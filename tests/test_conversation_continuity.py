"""Continuity uses existing live receipts and completed interpretations, in isolated HTTP instances."""
import json
import tempfile
import threading
import unittest

from day_attendant.connected import Connected
from day_attendant.conversation import FIELDS, portable_context
from day_attendant.errors import AssistantError
from day_attendant.service import Assistant
from day_attendant.web import LocalServer
from test_conversation import ChatFixture


class RecordingChat(ChatFixture):
    def turn(self,thread,prompt,schema,**kwargs):
        self.prompt=prompt
        self.context=json.loads(prompt.split('Selected state and portable continuity:\n')[1])
        return super().turn(thread,prompt,schema,**kwargs)


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='synthetic-continuity-')
        app=Assistant(self.temp.name);Connected(app).initialize(kind='personal')
        self.fixture=RecordingChat({'message':'The service will check.','uncertainties':[],'intent':None})
        self.server=LocalServer(app,self.fixture);self.server.schedule=lambda result=None:None
        self.board=self.server.board;self.chat=self.server.chat
        self.thread=threading.Thread(target=self.server.serve_forever);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.thread.join(5);self.server.server_close();self.server.pool.shutdown(wait=True)
        self.assertFalse(self.thread.is_alive());self.temp.cleanup()

    def intent(self,text,action,**values):
        intent=dict.fromkeys(FIELDS)
        intent.update(action=action,userAuthorized=True,requestEvidence=text,clearDue=False,**values)
        return intent

    def say(self,text,key,questions=None,intents=None,unprocessed=None):
        intents=intents or []
        self.fixture.output.update(uncertainties=questions or [],intent=intents[0] if intents else None,
                                   additionalIntents=intents[1:],unprocessed=unprocessed or [])
        self.chat.submit(text,key);self.chat.run(key)
        return self.fixture.context['continuity']

    def test_partial_failure_and_pending_receipts_refresh_after_retry_without_duplicate(self):
        text='Add Synthetic launch and Synthetic support'
        original=self.board._admit_direct
        def fail_second(identity,*args,**kwargs):
            if self.board.proposal(identity)['intent']['payload'].get('title')=='Synthetic support':
                raise AssistantError('controlled_failure','Synthetic temporary failure')
            return original(identity,*args,**kwargs)
        self.board._admit_direct=fail_second
        try:self.say(text,'two',intents=[self.intent(text,'task_add',title=t) for t in ('Synthetic launch','Synthetic support')],unprocessed=['Choose a due date'])
        finally:self.board._admit_direct=original
        receipt=self.say('What remains?','query')['requestResults'][0]
        saved,failed=receipt['proposals']
        self.assertEqual((saved['phase'],failed['phase']),('applied','invalid'))
        self.assertEqual(failed['error_code'],'controlled_failure')
        self.assertTrue(saved['result']['uuid']);self.assertEqual(receipt['unprocessed'],['Choose a due date'])
        text='Retry the failed proposal'
        retry=self.intent(text,'proposal_retry',operationPayload={'id':failed['id']})
        self.say(text,'retry',intents=[retry]);self.say(text,'retry-again',intents=[retry])
        results=self.say('What saved?','after')['requestResults']
        self.assertEqual([p['phase'] for p in results[0]['proposals']],['applied','applied'])
        self.assertEqual(len(self.board.snapshot()['tasks']),2)
        self.assertEqual(results[2]['operationResults'][0]['result']['id'],failed['id'])
        uid=saved['result']['uuid'];text='Retire Synthetic launch'
        self.say(text,'retire',intents=[self.intent(text,'front_retire',taskId=uid)])
        pending=self.say('What needs confirmation?','pending')['requestResults'][-1]['proposals'][0]
        self.assertEqual(pending['phase'],'review')
        self.board.undo_message('two','undo-two')
        self.assertTrue(all(t['state']=='retired' for t in self.board.snapshot()['tasks']))

    def test_completed_question_set_removes_answered_and_keeps_unrelated_questions(self):
        self.say('Organize the launch','ask',questions=['Which team?','Which date?'])
        prior=self.say('The team is Launch','answer',questions=['Which date?'])
        self.assertEqual([q['text'] for q in prior['openQuestions']],['Which team?','Which date?'])
        self.say('Invalid availability','interrupted',intents=[self.intent('Invalid availability','context_update',availableMinutes=30)])
        remaining=self.say('Explain the date question','explain',questions=['Which date?'])
        self.assertEqual([q['text'] for q in remaining['openQuestions']],['Which date?'])
        self.say('No date is needed','close')
        self.assertEqual(self.say('Anything open?','closed')['openQuestions'],[])
        self.assertIn('Keep unrelated unanswered questions',self.fixture.prompt)

    def test_incomplete_messages_and_failed_app_operations_are_structured(self):
        self.say('Set availability','invalid',intents=[self.intent('Set availability','context_update',availableMinutes=30)])
        text='Inspect synthetic missing operation'
        self.say(text,'inspect',intents=[self.intent(text,'recovery_inspect',operationPayload={'operation_key':'synthetic-missing'})])
        results=self.say('What failed?','errors')['requestResults']
        self.assertEqual(results[0]['status'],'incomplete')
        self.assertEqual(results[0]['error']['code'],'invalid_context')
        self.assertFalse(results[1]['operationResults'][0]['ok'])
        self.assertTrue(results[1]['operationResults'][0]['code'])

    def test_clear_excludes_conversation_results_and_questions_but_keeps_saved_state_and_undo(self):
        text='Add Synthetic launch'
        self.say(text,'save',questions=['Which date?'],intents=[self.intent(text,'task_add',title='Synthetic launch')])
        uid=self.board.snapshot()['tasks'][0]['id'];text='Retire Synthetic launch'
        self.say(text,'pending-retirement',questions=['Which date?'],intents=[self.intent(text,'front_retire',taskId=uid)])
        before=self.board.snapshot();self.chat.clear('clear')
        context=portable_context(self.board.snapshot())
        self.assertEqual(context['requestResults'],[]);self.assertEqual(context['openQuestions'],[])
        after=self.board.snapshot()
        for field in ('tasks','proposals','undoStack'):self.assertEqual(after[field],before[field])
        self.board.undo_message('save','undo-after-clear')
        self.assertEqual(self.board.snapshot()['tasks'][0]['state'],'retired')
