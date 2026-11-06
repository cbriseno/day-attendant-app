"""Optional real-browser coverage for the selected record download."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent

@unittest.skipUnless(shutil.which('chrome-devtools-axi'), 'Chrome AXI is required')
class RecordExportTests(unittest.TestCase):
    def test_selected_download_and_failure_paths(self):
        with tempfile.TemporaryDirectory(prefix='day-record-proof-') as out:
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/test_record_export_ui.py'), '--out', out],
                                    env=dict(os.environ, FM_LIVE='0'), text=True, capture_output=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
