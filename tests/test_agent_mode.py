"""Assistant use applies to every reasoning entry point and expires locally."""
from datetime import timedelta

from day_attendant.agent_mode import current, set_mode
from day_attendant.conversation import Conversation
from day_attendant.errors import AssistantError
from test_daily_domain import DailyBase
from test_connected import NOW


class AgentModeTests(DailyBase):
    def test_pause_blocks_model_and_leaves_local_work_available(self):
        set_mode(self.app, 'paused', '1h')
        with self.assertRaises(AssistantError) as error:
            self.board.request_suggestion('paused-order')
        self.assertEqual(error.exception.code, 'agent_paused')
        uid = self.add('Synthetic responsibility')
        self.assertTrue(uid)
        self.board.review_changes()
        self.assertEqual(self.board.bridge.turns, 0)
        chat = Conversation(self.board)
        chat.submit('Synthetic message', 'paused-chat')
        chat.run('paused-chat')
        self.assertEqual(self.board.bridge.turns, 0)
        self.assertEqual(current(self.app.store, NOW + timedelta(hours=1))['mode'], 'active')
        set_mode(self.app, 'off')
        with self.assertRaises(AssistantError) as error:
            self.board.require_agent()
        self.assertEqual(error.exception.code, 'agent_off')
        set_mode(self.app, 'active')
        self.assertIs(self.board.require_agent(), self.board.bridge)

    def test_today_ends_at_profile_midnight_and_invalid_mode_is_rejected(self):
        value = set_mode(self.app, 'paused', 'today')
        self.assertEqual(value['until'], '2026-10-29T06:00:00Z')
        with self.assertRaises(AssistantError):
            set_mode(self.app, 'paused', 'tomorrow')
