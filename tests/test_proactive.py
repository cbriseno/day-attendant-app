"""Check-ins use a controlled selected assistant and only run on explicit page requests."""
import json
from datetime import timedelta
from day_attendant import proactive
from day_attendant.agent_mode import set_mode
from day_attendant.errors import AssistantError
from test_connected import NOW
from test_daily_domain import DailyBase


class FakeAssistant:
    available = True
    model = 'controlled-fixture'
    def __init__(self):self.turns=0
    def thread(self):return 'fixture'
    def turn(self, thread, prompt, schema):
        self.turns+=1
        offered=json.loads(prompt.split('\n')[-1])
        return {'output':{'questions':[{'candidate':offered[0]['candidate'],'message':'Would you like to start?'}]}}


class ProactiveTests(DailyBase):
    def setUp(self):
        super().setUp()
        self.bridge=FakeAssistant();self.board.bridge=self.bridge
        proactive.configure(self.app.store,{'quietStart':'00:00','quietEnd':'00:00','maxPerDay':1})

    def test_real_model_contract_cadence_and_one_touch_action(self):
        uid=self.apply('task_add',{'title':'Synthetic','due':(NOW+timedelta(hours=2)).isoformat()})['result']['uuid']
        self.assertEqual(self.bridge.turns,0)  # State reads and scheduler do not start a turn.
        self.board.view();self.assertEqual(self.bridge.turns,0)
        result=proactive.run_pass(self.board)
        self.assertEqual(self.bridge.turns,1);self.assertEqual(result[0]['message'],'Would you like to start?')
        self.assertEqual(proactive.run_pass(self.board),[])
        self.assertTrue(proactive.limit_reached(self.board))
        proactive.answer(self.board,result[0]['id'],'start','answer','America/Edmonton')
        self.assertEqual(next(t for t in self.board.snapshot()['tasks'] if t['id']==uid)['state'],'active')
        self.assertEqual(proactive.view(self.board)['checkins'],[])
        self.board.undo(self.board.snapshot()['lastFact']['id'],'undo-answer')
        self.assertEqual(next(t for t in self.board.snapshot()['tasks'] if t['id']==uid)['state'],'todo')

    def test_rest_hours_and_pause_prevent_turns(self):
        self.apply('task_add',{'title':'Synthetic','due':(NOW+timedelta(hours=2)).isoformat()})
        proactive.configure(self.app.store,{'quietStart':'00:00','quietEnd':'23:59'})
        self.assertEqual(proactive.run_pass(self.board),[]);self.assertEqual(self.bridge.turns,0)
        proactive.configure(self.app.store,{'quietStart':'00:00','quietEnd':'00:00'})
        set_mode(self.app,'paused','forever')
        with self.assertRaises(AssistantError) as error:proactive.run_pass(self.board,manual=True)
        self.assertEqual(error.exception.code,'agent_paused');self.assertEqual(self.bridge.turns,0)
