"""Category priorities are profile data, independent of task priority and browser order."""
from pathlib import Path
import tempfile

from day_attendant import archives
from day_attendant.connected import Connected
from day_attendant.errors import AssistantError
from day_attendant.service import Assistant
from test_connected import ReviewFixture
from test_daily_domain import DailyBase
from test_chat_contract import controlled_board, turn


class CategoryPriorityTests(DailyBase):
    def test_priority_persists_restarts_backups_and_undo_without_task_changes(self):
        self.apply('task_add', {'title':'Synthetic release', 'group':'Release', 'priority':'low'})
        before=self.board.snapshot()['tasks']
        self.apply('group_priority_update', {'group':'RELEASE', 'groupPriority':'high'})
        self.assertEqual(self.board.snapshot()['groupPriorities'], {'release':'high'})
        self.assertEqual(self.board.snapshot()['tasks'], before)
        self.assertTrue(self.board.snapshot()['lastFact']['undoable'])
        self.assertEqual(Connected(Assistant(self.temp.name), ReviewFixture()).snapshot()['groupPriorities'], {'release':'high'})
        with tempfile.TemporaryDirectory() as folder:
            backup=archives.snapshot(self.app, Path(folder)/'backups')
            restored=Path(folder)/'restored';archives.restore(backup['path'], restored)
            self.assertEqual(Connected(Assistant(restored), ReviewFixture()).snapshot()['groupPriorities'], {'release':'high'})
        self.board.undo(self.board.snapshot()['lastFact']['id'], 'undo-category-priority')
        self.assertEqual(self.board.snapshot()['groupPriorities'], {})
        for value in ('urgent', '', 5, None):
            with self.assertRaises(AssistantError):self.request('group_priority_update', {'group':'Release','groupPriority':value})
        self.apply('group_priority_update', {'group':'Release','groupPriority':'low'})
        self.apply('group_priority_update', {'group':'Release','groupPriority':'none'})
        self.assertEqual(self.board.snapshot()['groupPriorities'], {})

    def test_rename_merge_and_undo_preserve_category_priorities(self):
        self.apply('task_add', {'title':'Synthetic release', 'group':'Release'})
        self.apply('group_priority_update', {'group':'Release','groupPriority':'high'})
        self.apply('group_rename', {'group':'Release','to':'Launch'})
        self.assertEqual(self.board.snapshot()['groupPriorities'], {'launch':'high'})
        self.board.undo(self.board.snapshot()['lastFact']['id'], 'undo-priority-rename')
        self.assertEqual(self.board.snapshot()['groupPriorities'], {'release':'high'})
        self.apply('group_priority_update', {'group':'Launch','groupPriority':'low'})
        self.apply('group_rename', {'group':'Release','to':'Launch'})
        self.assertEqual(self.board.snapshot()['groupPriorities'], {'launch':'low'})

    def test_both_chat_adapters_share_category_priority_action_and_context(self):
        for provider in ('codex','claude'):
            with self.subTest(provider=provider),controlled_board(provider) as (board,folder):
                board.request('task_add', {'title':'Synthetic release','group':'Release'}, 'seed')
                turn(board,folder,'Set Release category priority high','category','group_priority_update',group='Release',groupPriority='high')
                context,_,_=turn(board,folder,'What category priorities are saved?','query')
                self.assertEqual(context['presentation']['groupPriorities'], {'release':'high'})
