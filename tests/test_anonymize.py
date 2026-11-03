"""Screenshot privacy is exercised against disposable SQLite and the existing UI harness."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which('chrome-devtools-axi'), 'Chrome AXI is required for browser checks')
class AnonymizeUITests(unittest.TestCase):
    def test_canaries_layout_restoration_and_frame_budgets(self):
        with tempfile.TemporaryDirectory(prefix='day-anonymize-proof-') as scratch:
            out = os.environ.get('DAY_ATTENDANT_ANONYMIZE_PROOF', scratch)
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts/test_anonymize_ui.py'), '--out', out],
                cwd=ROOT, capture_output=True, text=True, timeout=240,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((Path(out) / 'report.json').read_text())
            self.assertTrue(report['passed'])
            self.assertEqual(len(report['checks']), 2)
