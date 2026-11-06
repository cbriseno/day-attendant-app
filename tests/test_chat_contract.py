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
        with patch.dict(os.environ,{'CODEX_HOME':str(folder/'codex-home')}):
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
