"""Manual blocks: an outside reason with its start, separate from dependencies, with Undo."""
import tempfile
import unittest

from day_attendant.connected import Connected
from day_attendant.errors import AssistantError
from day_attendant.service import Assistant
from test_connected import NOW, ReviewFixture


class BlockTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='day-block-test-')
        self.app=Assistant(self.temp.name,clock=lambda:NOW)
        self.board=Connected(self.app,ReviewFixture())
        self.board.initialize(zone='America/Edmonton')
        self.n=0
        self.uid=self.apply('task_add',{'title':'Pagar la factura del proveedor'})['result']['uuid']

    def tearDown(self):self.temp.cleanup()

    def apply(self,action,payload):
        self.n+=1
        final=self.board.request(action,payload,f'block-{self.n}')
        self.assertIn(final['phase'],('applied','unchanged'))
        return final

    def task(self):return next(t for t in self.board.snapshot()['tasks'] if t['id']==self.uid)

    def test_block_reason_and_start_are_kept_and_editing_keeps_the_start(self):
        self.apply('continuity_update',{'uuid':self.uid,'blockReason':'  Esperando respuesta del proveedor '})
        t=self.task();self.assertEqual(t['blockReason'],'Esperando respuesta del proveedor');self.assertTrue(t['blockedSince'])
        self.assertFalse(t['blocked'],'A manual block is not a dependency block.')
        since=t['blockedSince']
        self.apply('continuity_update',{'uuid':self.uid,'blockReason':'Esperando la cotización'})
        self.assertEqual(self.task()['blockedSince'],since)
        self.apply('continuity_update',{'uuid':self.uid,'blockReason':''})
        t=self.task();self.assertEqual(t['blockReason'],'');self.assertIsNone(t['blockedSince'])

    def test_undo_restores_the_previous_block_exactly(self):
        self.apply('continuity_update',{'uuid':self.uid,'blockReason':'Esperando al contador'})
        since=self.task()['blockedSince']
        self.apply('continuity_update',{'uuid':self.uid,'blockReason':''})
        fact=self.board.snapshot()['events'][-1]['id']
        self.assertEqual(self.board.undo(fact,'undo-unblock')['phase'],'applied')
        t=self.task();self.assertEqual((t['blockReason'],t['blockedSince']),('Esperando al contador',since))

    def test_blocked_task_can_start_and_reason_is_validated(self):
        self.apply('continuity_update',{'uuid':self.uid,'blockReason':'Esperando la llave'})
        self.apply('front_activate',{'uuid':self.uid})
        self.assertEqual(self.task()['state'],'active')
        for bad in ('x'*201,'dos\nlíneas',5):
            with self.assertRaises(AssistantError):self.board.request('continuity_update',{'uuid':self.uid,'blockReason':bad},'bad-'+str(bad)[:3])


if __name__=='__main__':unittest.main()
