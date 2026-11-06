"""Conversation contract through both real adapters with local controlled executables."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from day_attendant.claudebridge import ClaudeBridge
from day_attendant.codexbridge import CodexBridge
from day_attendant.connected import Connected
from day_attendant.conversation import Conversation, FIELDS, ACTIONS
from day_attendant.profiles import configure
from day_attendant.service import Assistant
from test_effort import FAKE_CLAUDE, FAKE_CODEX


@contextmanager
def controlled_board(provider):
    with tempfile.TemporaryDirectory(prefix='day-chat-contract-') as state:
        folder=Path(state)
        script=FAKE_CODEX if provider=='codex' else FAKE_CLAUDE
        script=script.replace("{'answer':'ok'}", "json.loads((Path(__file__).parent/'output.json').read_text())")
        if provider=='claude':
            script=script.replace("text=json.loads", "(Path(__file__).parent/'schema.json').write_text(sys.argv[sys.argv.index('--json-schema')+1])\ntext=json.loads")
            script=script.replace("if text=='hang':", "(Path(__file__).parent/'prompt.txt').write_text(text)\nif text=='hang':")
        binary=folder/provider;binary.write_text(script);binary.chmod(0o700)
        from day_attendant.fm_diagnostics import export as export_diagnostics
        def isolated_export(components,**kwargs):
            return export_diagnostics(components,downloads=folder/'downloads',**kwargs)
        with patch('day_attendant.fm_diagnostics.export',side_effect=isolated_export),patch.dict(os.environ,{'CODEX_HOME':str(folder/'codex-home'),'XDG_STATE_HOME':str(folder/'xdg-state'),'FM_DIAGNOSTICS_HOME':str(folder/'diagnostics')}):
            bridge=(CodexBridge if provider=='codex' else ClaudeBridge)(folder,binary=str(binary))
            try:
                board=Connected(Assistant(folder/'profile'),bridge);board.initialize(kind='personal',zone='America/Edmonton')
                configure(board.app,{'harness':provider},'selected-harness')
                yield board,folder
            finally:bridge.close()


def turn(board,folder,text,key,action=None,**values):
    intent=None
    if action:
        intent=dict.fromkeys(FIELDS);intent.update(action=action,clearDue=False,userAuthorized=True,requestEvidence=text,**values)
    output={'message':'Controlled response','uncertainties':[],'intent':intent,'additionalIntents':[],'unprocessed':[]}
    (folder/'output.json').write_text(json.dumps(output))
    chat=Conversation(board);chat.submit(text,key);chat.run(key)
    reply=next(m for m in board.snapshot()['messages'] if m['key']==key+':assistant')
    if reply['status']!='completed':raise AssertionError(reply)
    if board.bridge.provider=='codex':
        request=[r['params'] for r in map(json.loads,(folder/'requests.jsonl').read_text().splitlines()) if r.get('method')=='turn/start'][-1]
        prompt=request['input'][0]['text'];schema=request['outputSchema']
    else:prompt=(folder/'prompt.txt').read_text();schema=json.loads((folder/'schema.json').read_text())
    return json.loads(prompt.split('Selected state and portable continuity:\n')[1]),schema,prompt


class ChatContract(unittest.TestCase):
    def test_capabilities_and_saved_schedule_reach_both_harnesses(self):
        for provider in ('codex','claude'):
            with self.subTest(provider=provider),controlled_board(provider) as (board,folder):
                uid=board.request('task_add',{'title':'Synthetic rollout'},'task')['result']['uuid']
                schedule={'repeat':{'every':'weekday'},'reminders':[{'kind':'before','minutes':30},{'kind':'before','minutes':60}]}
                board.request('schedule_update',dict(schedule,uuid=uid),'schedule')
                before=board.snapshot()['revision']
                for i,text in enumerate(('What can you do?','Do you support recurrence and multiple alerts?','What reminders do I have?')):
                    ctx,schema,prompt=turn(board,folder,text,f'query-{i}')
                    contract=ctx['capabilities'];self.assertEqual(ctx['schedules'][uid],schedule)
                    self.assertEqual(set(contract['chatActions']),set(ACTIONS))
                    self.assertEqual(set(schema['properties']['intent']['anyOf'][1]['properties']['action']['enum']),set(ACTIONS))
                    self.assertEqual(contract['productSchedules']['maxReminders'],10)
                    self.assertEqual(contract['execution']['assistant']['provider'],provider)
                    self.assertTrue(contract['execution']['assistant']['connected'])
                    self.assertIn('No autonomous',contract['limits'][1]);self.assertIn('never proves',contract['limits'][2])
                    self.assertIn('Answer read questions',prompt)
                self.assertEqual(board.snapshot()['revision'],before)

    def test_existing_groups_classify_chat_and_organized_capture_without_losing_memberships(self):
        for provider in ('codex','claude'):
            with self.subTest(provider=provider),controlled_board(provider) as (board,folder):
                first=board.request('task_add',{'title':'Synthetic launch','groups':['Launch','Shared']},'launch')['result']['uuid']
                board.request('task_add',{'title':'Synthetic support','groups':['Support']},'support')
                before={t['id']:t for t in board.snapshot()['tasks']}
                ctx,_,_=turn(board,folder,'What categories exist?','groups')
                self.assertEqual(ctx['existingGroups'],['Launch','Shared','Support'])
                turn(board,folder,'Create and organize Review rollout','create','task_add',title='Review rollout',groups=['Launch'],classifyGroups=True)
                created=next(t for t in board.snapshot()['tasks'] if t['title']=='Review rollout')
                self.assertEqual(created['groups'],['Launch'])
                self.assertEqual({t['id']:t for t in board.snapshot()['tasks'] if t['id'] in before},before)
                turn(board,folder,'Classify the launch task for support too','classify','task_update',taskId=first,groups=['Support'],classifyGroups=True)
                self.assertEqual(next(t for t in board.snapshot()['tasks'] if t['id']==first)['groups'],['Launch','Shared','Support'])
                turn(board,folder,'Organize this when the category is unclear','ambiguous')
                uid=board.request('task_add',{'title':'Review synthetic support request','groups':['Shared']},'raw')['result']['uuid']
                (folder/'output.json').write_text(json.dumps({'tasks':[{'title':'Review synthetic support request','notes':'Synthetic request','groups':['Shared','Support'],'after':[]}]}))
                board.normalize_capture(uid,'Review synthetic support request',board.snapshot()['revision'])
                self.assertEqual(next(t for t in board.snapshot()['tasks'] if t['id']==uid)['groups'],['Shared','Support'])
                if provider=='claude':prompt=(folder/'prompt.txt').read_text()
                else:prompt=[r['params']['input'][0]['text'] for r in map(json.loads,(folder/'requests.jsonl').read_text().splitlines()) if r.get('method')=='turn/start'][-1]
                self.assertIn('Existing categories: ["Launch","Shared","Support"]',prompt)

    def test_schedule_round_trip_and_partial_updates_in_both_harnesses(self):
        for provider in ('codex','claude'):
            with self.subTest(provider=provider),controlled_board(provider) as (board,folder):
                turn(board,folder,'Create Synthetic rollout','create','task_add',title='Synthetic rollout',due='2026-12-09T16:00:00Z')
                uid=board.snapshot()['tasks'][0]['id']
                alerts=[{'kind':'before','minutes':30},{'kind':'before','minutes':60}]
                turn(board,folder,'Repeat Monday to Friday with alerts 30 and 60 minutes before due','configure','schedule_update',taskId=uid,repeat={'every':'weekday','days':None,'n':None},reminders=alerts)
                ctx,schema,prompt=turn(board,folder,'What reminders are saved?','query')
                self.assertEqual(ctx['schedules'][uid],{'repeat':{'every':'weekday'},'reminders':alerts})
                self.assertIn('milestone stop condition',prompt)
                self.assertIn('reminders',ctx['capabilities']['chatActions']['schedule_update'])
                self.assertIn('repeat',schema['properties']['intent']['anyOf'][1]['properties'])
                turn(board,folder,'Change only repetition to daily','repeat','schedule_update',taskId=uid,repeat={'every':'day','days':None,'n':None})
                self.assertEqual(board.snapshot()['schedules'][uid]['reminders'],alerts)
                alerts[0]['minutes']=15
                turn(board,folder,'Change only the first alert to 15 minutes','modify','schedule_update',taskId=uid,reminders=alerts)
                self.assertEqual(board.snapshot()['schedules'][uid],{'repeat':{'every':'day'},'reminders':alerts})
                turn(board,folder,'Remove repetition but keep the alerts','clear-repeat','schedule_update',taskId=uid,clearRepeat=True)
                self.assertEqual(board.snapshot()['schedules'][uid],{'repeat':None,'reminders':alerts})
                custom=[{'kind':'day_before','time':'09:00'},{'kind':'at','at':'2026-12-08T12:00:00-07:00'}]
                turn(board,folder,'Set the day before at 09:00 and December 8 at noon Edmonton','custom','schedule_update',taskId=uid,reminders=custom)
                self.assertEqual(board.snapshot()['schedules'][uid]['reminders'],[custom[0],{'kind':'at','at':'2026-12-08T19:00:00Z'}])
                turn(board,folder,'Cancel the entire schedule','cancel','schedule_update',taskId=uid,clearSchedule=True)
                self.assertNotIn(uid,board.snapshot()['schedules'])
