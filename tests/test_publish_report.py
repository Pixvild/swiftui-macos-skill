import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

class PublishReportTests(unittest.TestCase):
    def run_report(self, folder):
        env=dict(os.environ,CORPUS_URL='https://github.com/Pixvild/swiftui-macos-skill/actions/runs/1/artifacts/2',RUN_URL='https://github.com/Pixvild/swiftui-macos-skill/actions/runs/1')
        return subprocess.run([sys.executable,str(ROOT/'scripts/publish_collection_report.py')],cwd=folder,env=env,capture_output=True,text=True)
    def test_incomplete_corpus_cannot_publish(self):
        with tempfile.TemporaryDirectory() as f:
            root=Path(f); source=root/'references/local/full'; (source/'export').mkdir(parents=True)
            (source/'collection.json').write_text(json.dumps(dict(pages={},pending=['pending'],external_dependencies=[])))
            (source/'export/coverage.json').write_text(json.dumps(dict(complete=False)))
            result=self.run_report(root)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((root/'reports/full-coverage.json').exists())
    def test_complete_report_contains_artifact_location(self):
        with tempfile.TemporaryDirectory() as f:
            root=Path(f); source=root/'references/local/full'; (source/'export').mkdir(parents=True)
            (source/'collection.json').write_text(json.dumps(dict(pages={'https://developer.apple.com/documentation/swiftui':{'status':'fetched'}},pending=[],external_dependencies=[])))
            report=dict(complete=True,raw_hashes_verified=True,raw_graph_closure_verified=True,exported=1,fetched=1,discovered=1,failed=0,pending=0,scope='Test graph')
            (source/'export/coverage.json').write_text(json.dumps(report))
            (source/'export/catalog.json').write_text(json.dumps(dict(documents=[{'url':'url'}])))
            (source/'export/sources.json').write_text(json.dumps(dict(sources=[{'url':'url'}])))
            result=self.run_report(root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('artifacts/2',(root/'references/full-coverage.md').read_text())
