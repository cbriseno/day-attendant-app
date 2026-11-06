"""All public coordinator actions round trip through both controlled native adapters."""
import unittest
from test_chat_contract import controlled_board,turn
from day_attendant.action_contract import ALLOWED, FIELDS, SCHEMAS, DESCRIPTIONS, action_contract


class ChatParity(unittest.TestCase):
    def test_shared_definition_covers_every_action_and_field(self):
        self.assertEqual(set(DESCRIPTIONS),set(ALLOWED))
        self.assertTrue(set().union(*ALLOWED.values()) <= SCHEMAS.keys())
        for action,names in ALLOWED.items():
            self.assertEqual(set(action_contract()[action]['fields']),{('taskId' if n=='uuid' else n) for n in names})
            self.assertTrue((names-{'uuid'}) <= FIELDS.keys())

    def test_every_coordinator_action_uses_existing_receipts_in_both_harnesses(self):
        for provider in ('codex','claude'):
            with self.subTest(provider=provider),controlled_board(provider) as (board,folder):
              seen=[]
              def apply(action,text,**values):
               ctx,schema,prompt=turn(board,folder,text,'parity-'+str(len(seen)),action,**values)
               proposal=board.snapshot()['proposals'][-1]
               assert proposal['phase'] in ('applied','unchanged','review'),proposal
               seen.append(action)
               return proposal
              uid=apply('task_add','Create Synthetic A in Launch and Shared',title='Synthetic A',groups=['Launch','Shared'])['result']['uuid']
              other=apply('task_add','Create Synthetic B',title='Synthetic B')['result']['uuid']
              apply('task_update','Rename to Synthetic revised and set high priority',taskId=uid,title='Synthetic revised',priority='high',nextUp=True)
              apply('continuity_update','Block for supplier; save checklist Inspect',taskId=uid,blockReason='Supplier',notes='Human supplied note',original='Synthetic original',assistantNotes='Requested summary',checklist=[{'id':'inspect','text':'Inspect','done':False}])
              apply('continuity_update','Unblock the task',taskId=uid,blockReason='')
              apply('dependency_update','A depends on B',taskId=uid,dependsOn=[other])
              apply('related_update','Also relate A and B without blocking',taskId=uid,relatedTo=[other])
              apply('dependency_update','Remove the dependency',taskId=uid,dependsOn=[])
              apply('front_activate','Start A now',taskId=uid)
              apply('front_todo','Return A to todo',taskId=uid)
              apply('task_snooze','Snooze A until December 9',taskId=uid,until='2026-12-09T16:00:00Z',zone='America/Edmonton',fold=0)
              apply('front_todo','Wake A',taskId=uid)
              apply('task_done','Complete A',taskId=uid)
              apply('task_reopen','Reopen A',taskId=uid)
              apply('task_cancel','Cancel A because redundant',taskId=uid,reason='Redundant')
              apply('task_reopen','Reactivate A',taskId=uid)
              apply('group_rename','Rename Launch to Rollout',group='Launch',to='Rollout')
              apply('group_color_update','Color Rollout teal',group='Rollout',color='teal')
              apply('group_color_update','Use automatic color for Rollout',group='Rollout',clearFields=['color'])
              apply('order_update','Put B before A',order=[other,uid])
              apply('provenance_update','Record source chat, person Synthetic Jo',taskId=uid,source='chat',person='Synthetic Jo',reference='Human supplied reference')
              apply('attachments_update','Remove all attachment links from A',taskId=uid,attachmentIds=[])
              apply('schedule_update','Repeat weekdays with a 30 minute alert',taskId=uid,repeat={'every':'weekday','days':None,'n':None},reminders=[{'kind':'before','minutes':30}])
              apply('context_update','I am resting',rest=True)
              eid=apply('event_add','Create Synthetic meeting on December 9',title='Synthetic meeting',start='2026-12-09T18:00:00Z',end='2026-12-09T19:00:00Z')['result']['uuid']
              apply('event_update','Move Synthetic meeting to 20:00 UTC',taskId=eid,start='2026-12-09T20:00:00Z',end='2026-12-09T21:00:00Z')
              apply('event_cancel','Cancel Synthetic meeting',taskId=eid)
              raw=apply('task_add','Capture Synthetic raw in Support',title='Synthetic raw',groups=['Support'])['result']['uuid']
              apply('organize_capture','Organize Synthetic raw',taskId=raw,original='Synthetic raw',expectedTitle='Synthetic raw',tasks=[{'title':'Synthetic organized','notes':'Synthetic notes','groups':['Support'],'after':[]}])
              apply('front_retire','Delete Synthetic B',taskId=other)
              assert set(seen)==set(ALLOWED),(set(ALLOWED)-set(seen))
              assert next(t for t in board.snapshot()['tasks'] if t['id']==uid)['groups']==['Rollout','Shared']
