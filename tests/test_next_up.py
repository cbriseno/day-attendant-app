"""Persist and undo the next-up marker using the real SQLite coordinator."""
from day_attendant.errors import AssistantError
from test_daily_domain import DailyBase


class NextUpTests(DailyBase):
    def test_marker_survives_reads_and_start_clears_it_with_undo(self):
        uid = self.apply('task_add', {'title': 'Next', 'priority': 'low'})['result']['uuid']
        self.apply('task_update', {'uuid': uid, 'nextUp': True})
        task = next(t for t in self.board.snapshot()['tasks'] if t['id'] == uid)
        self.assertTrue(task['nextUp'])
        self.assertEqual(task['priority'], 'low')
        self.apply('front_activate', {'uuid': uid})
        self.assertFalse(next(t for t in self.board.snapshot()['tasks'] if t['id'] == uid)['nextUp'])
        self.board.undo(self.board.snapshot()['lastFact']['id'], 'undo-start-next')
        self.assertTrue(next(t for t in self.board.snapshot()['tasks'] if t['id'] == uid)['nextUp'])

    def test_started_tasks_and_non_boolean_values_are_rejected(self):
        uid = self.apply('task_add', {'title': 'Started'})['result']['uuid']
        with self.assertRaises(AssistantError):
            self.request('task_update', {'uuid': uid, 'nextUp': 'yes'})
        self.apply('front_activate', {'uuid': uid})
        self.apply('front_todo', {'uuid': uid})
        with self.assertRaises(AssistantError):
            self.request('task_update', {'uuid': uid, 'nextUp': True})
