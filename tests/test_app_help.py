"""App expertise contract; controlled models verify inputs, not model reasoning quality."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from day_attendant.app_help import DOCUMENTS, ROOT, app_help
from test_chat_contract import controlled_board, turn


class AppHelpTests(unittest.TestCase):
    def test_shipped_guides_views_and_real_shortcuts_reach_both_adapters(self):
        for provider in ('codex', 'claude'):
            with self.subTest(provider=provider), controlled_board(provider) as (board, folder):
                before = board.snapshot()['revision']
                context, _, prompt = turn(board, folder, 'Guíame por las vistas y los atajos.', 'guide')
                help_data = context['appHelp']
                for name in DOCUMENTS:
                    self.assertEqual(help_data['documents'][name], (ROOT / name).read_text())
                for view in ('list', 'board', 'focus', 'chains', 'group'):
                    self.assertIn(f'id="{view}-view"', help_data['uiDefinitions']['index.html'])
                self.assertIn("typing||document.querySelector('dialog[open]')", help_data['uiDefinitions']['daily.js'])
                self.assertIn("e.key.toLowerCase()==='n'", help_data['uiDefinitions']['daily.js'])
                self.assertIn("e.key==='F2'", help_data['uiDefinitions']['interface.js'])
                self.assertIn('"Enfoque"', help_data['captions']['focus_view'])
                self.assertIn('"Configuración"', help_data['captions']['daily_c7f73bb54d'])
                self.assertIn('Guide the human step by step', prompt)
                self.assertIn('Explain shortcut focus/modifier conditions', prompt)
                self.assertEqual(board.snapshot()['revision'], before)

    def test_source_edits_are_visible_on_the_next_read(self):
        with tempfile.TemporaryDirectory(prefix='day-help-source-') as temp:
            root = Path(temp)
            for name in DOCUMENTS:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            shutil.copytree(ROOT / 'day_attendant/ui', root / 'day_attendant/ui')
            with patch('day_attendant.app_help.ROOT', root):
                first = app_help()
                (root / 'README.md').write_text(first['documents']['README.md'] + '\nSynthetic new help.\n')
                script = root / 'day_attendant/ui/daily.js'
                script.write_text(script.read_text().replace("e.key.toLowerCase()==='n'", "e.key.toLowerCase()==='j'"))
                current = app_help()
                self.assertIn('Synthetic new help.', current['documents']['README.md'])
                self.assertIn("e.key.toLowerCase()==='j'", current['uiDefinitions']['daily.js'])
                self.assertNotIn("e.key.toLowerCase()==='n'", current['uiDefinitions']['daily.js'])

    def test_problem_triage_receives_evidence_and_uncertainty_rules(self):
        for provider in ('codex', 'claude'):
            with self.subTest(provider=provider), controlled_board(provider) as (board, folder):
                uid = board.request('task_add', {'title': 'Synthetic review'}, 'task')['result']['uuid']
                board.request('schedule_update', {'uuid': uid, 'repeat': {'every': 'weekday'}}, 'repeat')
                for i, question in enumerate(('¿Ya puedo repetir de lunes a viernes?',
                        'Guardé una repetición pero desaparece al recargar.', 'Quiero sincronización automática entre dispositivos.')):
                    context, _, prompt = turn(board, folder, question, f'triage-{i}')
                    self.assertEqual(context['schedules'][uid]['repeat'], {'every': 'weekday'})
                    for policy in ('already exists (give the exact steps)', 'probable bug', 'feature gap',
                                   'insufficient evidence', 'not a verified diagnosis', 'UI-only control'):
                        self.assertIn(policy, prompt)
                    self.assertIn('automatic device sync', context['appHelp']['documents']['README.md'])
                self.assertEqual(len(board.snapshot()['tasks']), 1)

    def test_report_reply_is_selected_markdown_without_writes(self):
        report = '# Fallo probable: recordatorio no conservado\n\n## Contexto\nCaso ficticio.\n\n## Pasos\n1. Guardar un aviso.\n2. Recargar.\n\n## Resultado actual\nEl usuario informa que falta.\n\n## Resultado esperado\nConservar el aviso.\n\n## Datos pendientes\nVersión no proporcionada.'
        for provider in ('codex', 'claude'):
            with self.subTest(provider=provider), controlled_board(provider) as (board, folder):
                before = board.snapshot()['revision']
                _, _, prompt = turn(board, folder, 'Redacta ese reporte en Markdown.', 'report', reply=report)
                saved = next(m for m in board.snapshot()['messages'] if m['key'] == 'report:assistant')
                self.assertEqual(saved['text'], report)
                self.assertEqual(board.snapshot()['revision'], before)
                self.assertFalse(board.snapshot()['proposals'])
                for rule in ('Download record', 'Do not invent steps', 'no unrelated tasks',
                             'Never submit, upload', 'Do not add a confirmation step before drafting'):
                    self.assertIn(rule, prompt)

    def test_visibility_distinguishes_supplied_context_from_browser_access(self):
        for provider in ('codex', 'claude'):
            with self.subTest(provider=provider), controlled_board(provider) as (board, folder):
                turn(board, folder, 'Guarda esta duda en la conversación.', 'earlier')
                context, _, prompt = turn(board, folder, '¿Qué puedes ver de mi app?', 'visibility')
                self.assertTrue(context['continuity']['messages'])
                self.assertIn('do not deny seeing those', prompt)
                self.assertIn('cannot inspect the live browser', prompt)
                self.assertIn('not a live browser inspection', context['appHelp']['scope'])
                self.assertIn('supplied app help', context['capabilities']['limits'][0])
