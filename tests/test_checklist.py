"""Light per-task checklist (#45): stored with the task's continuity, one undo per change."""
import unittest

from day_attendant.errors import AssistantError
from test_daily_domain import DailyBase


class ChecklistTests(DailyBase):
    def items(self, uid):
        return next(t for t in self.board.snapshot()['tasks'] if t['id'] == uid)['checklist']

    def test_items_are_saved_in_order_and_each_change_undoes_alone(self):
        uid = self.add('Preparar viaje')
        self.assertEqual(self.items(uid), [])
        first = [{'id': 'a', 'text': 'Pasaporte', 'done': False}, {'id': 'b', 'text': ' Boletos ', 'done': False}]
        self.apply('continuity_update', {'uuid': uid, 'checklist': first})
        first_fact = self.board.snapshot()['lastFact']['id']
        self.assertEqual([i['text'] for i in self.items(uid)], ['Pasaporte', 'Boletos'])
        checked = [dict(first[1], text='Boletos', done=True), first[0]]
        self.apply('continuity_update', {'uuid': uid, 'checklist': checked})
        self.assertEqual([(i['id'], i['done']) for i in self.items(uid)], [('b', True), ('a', False)])
        self.board.undo(self.board.snapshot()['lastFact']['id'], 'undo-check')
        self.assertEqual([(i['id'], i['done']) for i in self.items(uid)], [('a', False), ('b', False)])
        self.board.undo(first_fact, 'undo-first')
        self.assertEqual(self.items(uid), [])

    def test_the_checklist_does_not_touch_other_continuity_fields(self):
        uid = self.add('Mudanza')
        self.apply('continuity_update', {'uuid': uid, 'context': 'Ya empaqué la cocina'})
        self.apply('continuity_update', {'uuid': uid, 'checklist': [{'id': 'x', 'text': 'Cajas', 'done': True}]})
        task = next(t for t in self.board.snapshot()['tasks'] if t['id'] == uid)
        self.assertEqual(task['context'], 'Ya empaqué la cocina')
        self.assertEqual(task['checklist'][0]['done'], True)

    def test_invalid_items_are_refused(self):
        uid = self.add('Revisar')
        for bad in ([{'id': 'a', 'text': ''}], [{'id': 'a', 'text': 'x'}, {'id': 'a', 'text': 'y'}],
                    [{'id': 'a', 'text': 'x', 'done': 'yes'}], [{'id': 'a', 'text': 'x', 'due': 'mañana'}],
                    [{'id': str(i), 'text': 'x'} for i in range(51)], 'not a list'):
            with self.assertRaises(AssistantError):
                self.board.request('continuity_update', {'uuid': uid, 'checklist': bad}, 'bad-' + str(id(bad)))
        self.assertEqual(self.items(uid), [])


if __name__ == '__main__':
    unittest.main()
