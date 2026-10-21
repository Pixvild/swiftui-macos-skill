import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import doclib

class SyncCLITests(unittest.TestCase):
    def test_offline_sync_writes_snapshot_without_marking_read(self):
        self.assertTrue((ROOT/'scripts/sync_docs.py').exists(), 'Sync CLI is required')
        with tempfile.TemporaryDirectory() as folder:
            base = pathlib.Path(folder)
            url = 'https://developer.apple.com/documentation/swiftui/example'
            manifest = base/'sources.json'
            manifest.write_text(json.dumps({'schema_version':1,'sources':[{'id':'T1','url':url,'title':'Example'}]}))
            doclib.cached_fetch(url+'.md', base/'cache', transport=lambda *_:(200,{'content-type':'text/markdown'},b'# Example\n\nSynthetic fixture content.'))
            result = subprocess.run([sys.executable,str(ROOT/'scripts/sync_docs.py'),'--manifest',str(manifest),'--output',str(base/'out'),'--cache',str(base/'cache'),'--mode','offline'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            state=json.loads((base/'out/sync-state.json').read_text())
            row=state['sources']['T1']
            self.assertEqual(row['status'],'offline_cache')
            self.assertEqual(row['read_status'],'not_reviewed')
            self.assertEqual(row['build_status'],'not_run')
            self.assertTrue((base/'out'/row['content_path']).exists())

    def test_offline_failure_keeps_existing_snapshot(self):
        self.assertTrue((ROOT/'scripts/sync_docs.py').exists(), 'Sync CLI is required')
        with tempfile.TemporaryDirectory() as folder:
            base=pathlib.Path(folder); out=base/'out'; out.mkdir()
            (out/'old.md').write_text('KEEP ME')
            (out/'sync-state.json').write_text(json.dumps({'sources':{'T1':{'url':'https://developer.apple.com/documentation/swiftui/example','content_path':'old.md','status':'fetched','read_status':'not_reviewed'}}}))
            manifest=base/'sources.json'
            manifest.write_text(json.dumps({'schema_version':1,'sources':[{'id':'T1','title':'Example','url':'https://developer.apple.com/documentation/swiftui/example'}]}))
            result=subprocess.run([sys.executable,str(ROOT/'scripts/sync_docs.py'),'--manifest',str(manifest),'--output',str(out),'--cache',str(base/'cache'),'--mode','offline'],capture_output=True,text=True)
            self.assertEqual(result.returncode,1,result.stderr)
            row=json.loads((out/'sync-state.json').read_text())['sources']['T1']
            self.assertEqual(row['status'],'failed')
            self.assertTrue(row['stale_snapshot_retained'])
            self.assertEqual((out/'old.md').read_text(),'KEEP ME')

if __name__=='__main__': unittest.main()
