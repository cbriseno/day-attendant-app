"""#41: repetition, several reminders per task and notification kinds, with real SQLite stores."""
from datetime import datetime, timedelta, timezone
import tempfile
import unittest

from day_attendant import schedules
from day_attendant.connected import Connected
from day_attendant.errors import AssistantError
from day_attendant.service import Assistant
from test_connected import NOW, ReviewFixture
from test_daily_domain import DailyBase


class ScheduleRules(unittest.TestCase):
    def test_next_occurrence_keeps_local_wall_time(self):
        now = datetime(2026, 11, 5, 18, tzinfo=timezone.utc)
        due = '2026-11-05T16:00:00Z'  # 09:00 in Edmonton (MST)
        zone = 'America/Edmonton'
        self.assertEqual(schedules.next_due(due, {'every': 'day'}, zone, now), '2026-11-06T16:00:00Z')
        # Thursday → weekdays skips the weekend after Friday
        self.assertEqual(schedules.next_due('2026-11-06T16:00:00Z', {'every': 'weekday'}, zone, now), '2026-11-09T16:00:00Z')
        self.assertEqual(schedules.next_due(due, {'every': 'week', 'days': [0, 2]}, zone, now), '2026-11-09T16:00:00Z')
        self.assertEqual(schedules.next_due(due, {'every': 'days', 'n': 3}, zone, now), '2026-11-08T16:00:00Z')
        self.assertEqual(schedules.next_due('2026-01-31T16:00:00Z', {'every': 'month'}, zone, datetime(2026, 1, 31, 20, tzinfo=timezone.utc)), '2026-02-28T16:00:00Z')
        # An occurrence long past jumps to the first one after now.
        self.assertEqual(schedules.next_due('2026-10-01T16:00:00Z', {'every': 'day'}, zone, now), '2026-11-06T16:00:00Z')

    def test_validation(self):
        self.assertIsNone(schedules.validate({'repeat': None, 'reminders': []}))
        for bad in ({'repeat': {'every': 'hourly'}}, {'repeat': {'every': 'week', 'days': []}},
                    {'reminders': [{'kind': 'before', 'minutes': 0}]}, {'reminders': [{'kind': 'day_before', 'time': '9:00'}]}):
            with self.assertRaises(AssistantError):
                schedules.validate(bad)


class ScheduleTests(DailyBase):
    def due_task(self, title, due):
        return self.apply('task_add', {'title': title, 'due': due})['result']['uuid']

    def test_schedule_is_saved_shown_and_undone(self):
        uid = self.due_task('Pagar la luz', '2026-10-29T16:00:00Z')
        value = {'repeat': {'every': 'month'}, 'reminders': [{'kind': 'before', 'minutes': 30}, {'kind': 'day_before', 'time': '09:00'}]}
        self.apply('schedule_update', dict(value, uuid=uid))
        self.assertEqual(self.board.snapshot()['schedules'][uid], value)
        self.board.undo(self.board.snapshot()['lastFact']['id'], 'undo-schedule')
        self.assertNotIn(uid, self.board.snapshot()['schedules'])

    def test_completing_a_repeating_task_moves_it_to_the_next_occurrence_and_undo_restores(self):
        uid = self.due_task('Regar las plantas', '2026-10-28T15:00:00Z')
        self.apply('schedule_update', {'uuid': uid, 'repeat': {'every': 'day'}})
        done = self.apply('task_done', {'uuid': uid})
        task = next(t for t in self.board.snapshot()['tasks'] if t['id'] == uid)
        self.assertNotEqual(task['state'], 'done')
        self.assertEqual(task['due'], '2026-10-29T15:00:00Z')
        self.assertEqual(done['result']['repeated'], '2026-10-29T15:00:00Z')
        self.board.undo(self.board.snapshot()['lastFact']['id'], 'undo-repeat')
        task = next(t for t in self.board.snapshot()['tasks'] if t['id'] == uid)
        self.assertEqual(task['due'], '2026-10-28T15:00:00Z')

    def test_notices_for_reminders_soon_and_overdue_respect_switches(self):
        soon = self.due_task('Vence pronto', (NOW + timedelta(minutes=20)).isoformat())
        late = self.due_task('Ya venció', (NOW - timedelta(hours=2)).isoformat())
        later = self.due_task('Más tarde', (NOW + timedelta(days=2)).isoformat())
        self.apply('schedule_update', {'uuid': later, 'reminders': [{'kind': 'at', 'at': (NOW - timedelta(minutes=5)).isoformat()}]})
        kinds = {n['entity']: n['kind'] for n in self.app.pulse()['notices']}
        self.assertEqual(kinds[soon], 'due')
        self.assertEqual(kinds[late], 'overdue')
        self.assertEqual(kinds[later], 'reminder')
        from day_attendant.profiles import configure
        configure(self.app, {'notification_policy': {'kinds': {'reminder': False, 'overdue': False}}}, 'kinds-off')
        kinds = {n['entity']: n['kind'] for n in self.app.pulse()['notices']}
        self.assertEqual(set(kinds), {soon})

    def test_notifier_text_names_the_kind(self):
        sent = []
        temp = tempfile.TemporaryDirectory(prefix='day-schedule-notify-'); self.addCleanup(temp.cleanup)
        app = Assistant(temp.name, clock=lambda: NOW, notifier=lambda title, body: sent.append(body) or {'accepted': True})
        board = Connected(app, ReviewFixture()); board.initialize(kind='personal', zone='UTC')
        from day_attendant.profiles import configure
        configure(app, {'locale': 'es', 'notification_policy': {'weekdays': [0, 1, 2, 3, 4, 5, 6], 'start': '00:00', 'end': '23:59', 'quietStart': '00:00', 'quietEnd': '00:00'}}, 'policy-open')
        board.request('task_add', {'title': 'Llamar al banco', 'due': (NOW - timedelta(hours=1)).isoformat()}, 'n1')
        app.notify()
        self.assertEqual(sent, ['Venció · Llamar al banco'])


if __name__ == '__main__':
    unittest.main()

class ScheduleRecoveryTests(DailyBase):
    def test_repeat_resets_checklist_and_undo_restores_it(self):
        uid = self.add('Synthetic checklist')
        checklist = [{'id': 'one', 'text': 'Step', 'done': True}]
        self.apply('continuity_update', {'uuid': uid, 'checklist': checklist})
        self.apply('schedule_update', {'uuid': uid, 'repeat': {'every': 'day'}})
        self.apply('task_done', {'uuid': uid})
        state = self.board.snapshot()
        self.assertFalse(next(t for t in state['tasks'] if t['id'] == uid)['checklist'][0]['done'])
        self.board.undo(state['lastFact']['id'], 'undo-repeat-checklist')
        self.assertTrue(next(t for t in self.board.snapshot()['tasks'] if t['id'] == uid)['checklist'][0]['done'])

    def test_schedule_survives_backup_restore(self):
        from pathlib import Path
        from day_attendant import archives
        uid = self.add('Synthetic backup')
        self.apply('schedule_update', {'uuid': uid, 'repeat': {'every': 'day'}, 'reminders': [{'kind': 'before', 'minutes': 30}]})
        with tempfile.TemporaryDirectory(prefix='da-schedule-backup-') as folder:
            backup = archives.snapshot(self.app, folder)
            archives.restore(backup['path'], Path(folder) / 'restored')
            restored = Connected(Assistant(Path(folder) / 'restored', clock=lambda: NOW), ReviewFixture())
            self.assertEqual(restored.snapshot()['schedules'][uid], self.board.snapshot()['schedules'][uid])

    def test_custom_reminder_and_due_are_delivered_independently(self):
        sent = []
        self.app.notifier = lambda title, body: sent.append(body) or {'accepted': True}
        from day_attendant.profiles import configure
        configure(self.app, {'notification_policy': {'weekdays': list(range(7)), 'start': '00:00', 'end': '23:59', 'quietStart': '00:00', 'quietEnd': '00:00'}}, 'open-policy')
        uid = self.apply('task_add', {'title': 'Synthetic', 'due': (NOW + timedelta(minutes=20)).isoformat()})['result']['uuid']
        self.apply('schedule_update', {'uuid': uid, 'reminders': [{'kind': 'at', 'at': (NOW - timedelta(minutes=5)).isoformat()}]})
        self.app.notify()
        self.assertEqual(set(sent), {'Due soon · Synthetic', 'Reminder · Synthetic'})
