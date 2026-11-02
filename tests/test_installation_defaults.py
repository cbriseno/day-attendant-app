"""Public-installation defaults with synthetic configuration; no live model calls."""
import json
import os
import unittest
from unittest.mock import patch
from day_attendant.instructions import PERSONAL_ASSISTANT, personal_instructions
from day_attendant.codexbridge import CodexBridge
from day_attendant.claudebridge import ClaudeBridge
from day_attendant.profiles import new_profile

class InstallationDefaults(unittest.TestCase):
    def test_neutral_default_and_english_profile(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(personal_instructions(), PERSONAL_ASSISTANT)
            self.assertEqual(new_profile('/tmp/synthetic-profile', 'personal', 'UTC')['locale'], 'en')

    def test_private_recipient_reaches_both_adapters_as_data(self):
        name = '[SYNTHETIC] Example Stargazer'
        with patch.dict(os.environ, {'DAY_ATTENDANT_RECIPIENT': name}):
            expected = personal_instructions()
            self.assertEqual(json.loads(expected.splitlines()[-1]), {'recipient': name})
            codex = CodexBridge.__new__(CodexBridge)
            codex.workspace = '/tmp/synthetic-workspace'; codex.model = 'synthetic-model'
            calls = []
            def call(method, options, timeout):
                calls.append(options)
                return {'thread': {'cwd': codex.workspace, 'id': 'synthetic-thread'}}
            codex.call = call
            self.assertEqual(codex.thread(), 'synthetic-thread')
            self.assertEqual(calls[0]['baseInstructions'], expected)
            claude = ClaudeBridge.__new__(ClaudeBridge)
            claude.binary = 'claude'; claude.model = None; claude.effort = 'medium'
            args = claude.command({})
            self.assertEqual(args[args.index('--system-prompt') + 1], expected)

    def test_invalid_recipient_uses_neutral_default(self):
        for name in ('', 'x' * 101, 'Synthetic\nInjected instruction', '\nSynthetic', 'Synthetic\x7f'):
            with self.subTest(name_length=len(name)), patch.dict(os.environ, {'DAY_ATTENDANT_RECIPIENT': name}):
                self.assertEqual(personal_instructions(), PERSONAL_ASSISTANT)

if __name__ == '__main__':
    unittest.main()
