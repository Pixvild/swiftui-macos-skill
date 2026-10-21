import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect_docs import linked_pages, collect, collection_complete
BASE='https://developer.apple.com/documentation/swiftui'

def document(url,links=()):
    return dict(identifier={'url':url},metadata={'title':'Synthetic'},abstract=[],
        references={str(i):{'url':v,'type':'topic'} for i,v in enumerate(links)})

class CollectionTests(unittest.TestCase):
    def test_all_references_include_non_topic_members_and_keep_overloads(self):
        doc=document(BASE,[BASE+'/view/a(_:)-aaa',BASE+'/view/a(_:)-bbb','/documentation/appkit/nsview'])
        pages,external=linked_pages(doc)
        self.assertEqual(len(pages),2)
        self.assertEqual(external,['https://developer.apple.com/documentation/appkit/nsview'])
    def test_queue_exhaustion_cycle_and_snapshots(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            def fetch(url):
                doc=document(url,[BASE,BASE+'/view'])
                return json.dumps(doc).encode()
            state=collect(out,fetch,workers=2)
            self.assertTrue(collection_complete(state))
            self.assertEqual(len(state['pages']),2)
            self.assertEqual(len(list((out/'snapshots').glob('*/*/content.md'))),2)
            self.assertTrue(all(x['read_status']=='not_reviewed' for x in state['pages'].values()))
    def test_failure_prevents_completion_and_retry_resumes(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            def fail(url): raise OSError('temporary')
            state=collect(out,fail,workers=1)
            self.assertFalse(collection_complete(state))
            state=collect(out,lambda u:json.dumps(document(u)).encode(),workers=1,retry_failed=True)
            self.assertTrue(collection_complete(state))
    def test_bad_identity_is_not_followed(self):
        with tempfile.TemporaryDirectory() as folder:
            state=collect(Path(folder),lambda u:json.dumps(document(BASE+'/wrong',[BASE+'/other'])).encode(),workers=1)
            self.assertEqual(len(state['pages']),1)
            self.assertFalse(collection_complete(state))

    def test_truncated_frontier_is_rebuilt_from_saved_raw(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            def fetch(url):return json.dumps(document(url,[BASE+'/view'] if url==BASE else [])).encode()
            collect(out,fetch,workers=1,max_pages=1)
            state=json.loads((out/'collection.json').read_text())
            state['pending']=[]
            (out/'collection.json').write_text(json.dumps(state))
            final=collect(out,fetch,workers=1,retry_failed=True)
            self.assertIn(BASE+'/view',final['pages'])

    def test_missing_raw_snapshot_is_refetched_on_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            def fetch(url):return json.dumps(document(url)).encode()
            collect(out,fetch,workers=1)
            next((out/'snapshots').glob('*/*/raw.json')).unlink()
            calls=[]
            state=collect(out,lambda u:(calls.append(u) or fetch(u)),workers=1,retry_failed=True)
            self.assertEqual(calls,[BASE])
            self.assertTrue(collection_complete(state))

    def test_checkpoint_for_other_scope_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            collect(out,lambda u:json.dumps(document(u)).encode(),workers=1)
            p=out/'collection.json'; state=json.loads(p.read_text());state['scope']='different';p.write_text(json.dumps(state))
            with self.assertRaises(ValueError):collect(out,lambda u:b'',workers=1)

    def test_damaged_http_cache_is_quarantined_and_refetched(self):
        import collect_docs
        from doclib import cached_fetch, endpoint_candidates
        with tempfile.TemporaryDirectory() as folder:
            cache=Path(folder)
            endpoint=endpoint_candidates(BASE)[0]
            cached_fetch(endpoint,cache,transport=lambda *_:(200,{},b'OLD'))
            next(cache.glob('*.body')).write_bytes(b'CORRUPT')
            calls=[]
            body=collect_docs.fetch_document(BASE,cache,'online',1,transport=lambda *_:(calls.append(1) or (200,{},b'NEW')))
            self.assertEqual(body,b'NEW')
            self.assertEqual(len(calls),1)
            self.assertEqual(len(list((cache/'quarantine').glob('*/*.body'))),1)
