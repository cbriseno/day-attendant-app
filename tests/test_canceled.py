"""Cancellation remains separate from completion and can be undone or reopened."""
import tempfile
import unittest
from day_attendant.connected import Connected
from day_attendant.errors import AssistantError
from day_attendant.service import Assistant
from test_connected import ReviewFixture


class CanceledTests(unittest.TestCase):
    def test_cancel_dependency_checklist_undo_and_reopen(self):
        with tempfile.TemporaryDirectory(prefix='day-canceled-') as state:
            board = Connected(Assistant(state), ReviewFixture())
            board.initialize(kind='personal', zone='UTC')
            def change(action, payload, key):
                return board.request(action, payload, key, expected_revision=board.snapshot()['revision'])
            a = change('task_add', {'title': 'Prerequisite'}, 'add-a')['result']['uuid']
            b = change('task_add', {'title': 'Dependent'}, 'add-b')['result']['uuid']
            change('dependency_update', {'uuid': b, 'dependsOn': [a]}, 'depends')
            change('continuity_update', {'uuid': a, 'checklist': [{'id': 'one', 'text': 'Item', 'done': False}]}, 'checklist')
            change('task_cancel', {'uuid': a, 'reason': 'Changed plans'}, 'cancel')
            tasks = {t['id']: t for t in board.snapshot()['tasks']}
            self.assertEqual((tasks[a]['state'], tasks[a]['cancelReason']), ('canceled', 'Changed plans'))
            self.assertTrue(tasks[a]['closedAt'])
            self.assertEqual(tasks[b]['blockedBy'], [])
            self.assertNotIn(a, [t['uuid'] for t in board.app.list()['tasks']])
            self.assertNotIn(a, [n['entity'] for n in board.app.pulse()['notices']])
            board = Connected(Assistant(state), ReviewFixture())
            self.assertEqual(next(t for t in board.snapshot()['tasks'] if t['id'] == a)['state'], 'canceled')
            board.undo(board.snapshot()['lastFact']['id'], 'undo')
            self.assertEqual(next(t for t in board.snapshot()['tasks'] if t['id'] == b)['blockedBy'], [a])
            change('task_cancel', {'uuid': a}, 'cancel-again')
            change('task_reopen', {'uuid': a}, 'reopen')
            task = next(t for t in board.snapshot()['tasks'] if t['id'] == a)
            self.assertEqual((task['state'], len(task['checklist'])), ('todo', 1))
            board.undo(board.snapshot()['lastFact']['id'], 'undo-reopen')
            self.assertEqual(next(t for t in board.snapshot()['tasks'] if t['id'] == a)['state'], 'canceled')
            with self.assertRaises(AssistantError):
                change('task_done', {'uuid': a}, 'invalid-done')

    def test_schema_three_upgrades_without_reinterpreting_records(self):
        from pathlib import Path
        import sqlite3
        from day_attendant.archives import snapshot, upgrade_tasks
        with tempfile.TemporaryDirectory(prefix='day-cancel-upgrade-') as state, tempfile.TemporaryDirectory(prefix='day-cancel-backup-') as backups:
            board = Connected(Assistant(state), ReviewFixture())
            board.initialize(kind='personal', zone='UTC')
            uid = board.request('task_add', {'title': 'Existing'}, 'legacy-add')['result']['uuid']
            board.request('front_retire', {'uuid': uid}, 'legacy-retire')
            before = board.app.tasks.rows()
            with sqlite3.connect(Path(state) / 'tasks.sqlite3') as con:
                con.execute('PRAGMA user_version=3')
            upgrade_tasks(board.app, backup=snapshot(board.app, destination=backups, category="migration"))
            self.assertEqual(board.app.tasks.schema(), 4)
            self.assertEqual(board.app.tasks.rows(), before)
            self.assertEqual(board.snapshot()['tasks'][0]['state'], 'retired')

    def test_repeating_task_has_no_reminders_or_new_occurrence_while_canceled(self):
        from datetime import datetime, timezone
        now = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix='day-cancel-schedule-') as state:
            board = Connected(Assistant(state, clock=lambda: now), ReviewFixture())
            board.initialize(kind='personal', zone='UTC')
            uid = board.request('task_add', {'title': 'Scheduled', 'due': '2026-11-05T12:30:00Z'}, 'scheduled-add')['result']['uuid']
            board.request('schedule_update', {'uuid': uid, 'repeat': {'every': 'day'}, 'reminders': [{'kind': 'at', 'at': '2026-11-05T11:59:00Z'}]}, 'schedule')
            self.assertTrue(any(n['entity'] == uid and n['kind'] == 'reminder' for n in board.app.pulse()['notices']))
            board.request('task_cancel', {'uuid': uid}, 'cancel-scheduled')
            self.assertFalse(any(n['entity'] == uid for n in board.app.pulse()['notices']))
            with self.assertRaises(AssistantError):
                board.request('task_done', {'uuid': uid}, 'done-canceled')
            self.assertEqual(board.app.tasks.get(uid)['due'], '20261105T123000Z')
            board.request('task_reopen', {'uuid': uid}, 'reactivate-scheduled')
            self.assertEqual(board.snapshot()['schedules'][uid]['repeat'], {'every': 'day'})
