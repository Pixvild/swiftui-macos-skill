import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DiscoveryCLITests(unittest.TestCase):
    def test_failed_offline_discovery_has_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            result = subprocess.run([sys.executable, str(ROOT/'scripts/discover_docs.py'),
                '--mode', 'offline', '--limit', '1', '--output', str(base/'out'),
                '--cache', str(base/'cache')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads((base/'out/coverage.json').read_text())
            self.assertEqual(report['failed'], 1)
            self.assertEqual(report['fetched'], 0)
