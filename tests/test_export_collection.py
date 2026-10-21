import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect_docs import collect
from export_collection import export
BASE='https://developer.apple.com/documentation/swiftui'

class ExportTests(unittest.TestCase):
    def test_exports_body_and_index_and_checks_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            body=json.dumps({'metadata':{'title':'Synthetic'},'identifier':{'url':BASE},'abstract':[{'type':'text','text':'Example source text.'}],'references':{}}).encode()
            collect(root/'in',lambda u:body,workers=1)
            report=export(root/'in',root/'out',require_complete=True)
            self.assertEqual(report['exported'],1)
            docs=json.loads((root/'out/catalog.json').read_text())['documents']
            self.assertTrue((root/'out'/docs[0]['content_path']).is_file())
            self.assertIn('Synthetic',(root/'out/lookup.md').read_text())
            raw=next((root/'in/snapshots').glob('*/*/raw.json'))
            raw.write_bytes(b'changed')
            with self.assertRaises(ValueError):export(root/'in',root/'out',require_complete=True)
    def test_rejects_unfinished_collection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'in').mkdir()
            (root/'in/collection.json').write_text(json.dumps(dict(pages={},pending=[BASE],external_dependencies=[])))
            with self.assertRaises(ValueError):export(root/'in',root/'out',require_complete=True)

    def test_fake_empty_frontier_does_not_pass_complete_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            body=json.dumps({'metadata':{'title':'Root'},'identifier':{'url':BASE},'abstract':[],
                'references':{'child':{'url':BASE+'/view','type':'topic'}}}).encode()
            collect(root/'in',lambda u:body,workers=1,max_pages=1)
            p=root/'in/collection.json'; state=json.loads(p.read_text()); state['pending']=[];p.write_text(json.dumps(state))
            with self.assertRaises(ValueError):export(root/'in',root/'out',require_complete=True)
