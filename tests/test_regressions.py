import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import doclib
import discover_docs
import sync_docs
from test_doclib import FIXTURE, URL

class RegressionTests(unittest.TestCase):
    def test_changed_source_identity_does_not_relabel_old_snapshot(self):
        source = {'id':'T1','url':URL+'/new'}
        previous = {'url':URL, 'content_path':'old.md', 'read_status':'read'}
        row = sync_docs.failed(source, previous, 'now', [])
        self.assertNotIn('content_path', row)
        self.assertEqual(row['read_status'], 'not_reviewed')
        self.assertFalse(row['stale_snapshot_retained'])

    def test_metadata_failure_leaves_old_snapshot_intact(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            old = out/doclib.doc_key(URL)/'content.md'
            old.parent.mkdir()
            old.write_text('OLD')
            source = {'id':'T1','url':URL}
            previous = {'url':URL,'content_path':str(old.relative_to(out))}
            body = json.dumps(FIXTURE).encode()
            response = dict(body=body,sha256=doclib.digest(body),fetched_at='now',checked_at='now',status='fetched',content_type='application/json')
            with patch.object(sync_docs,'cached_fetch',return_value=response), patch.object(sync_docs,'write_json',side_effect=OSError('disk failure')):
                row = sync_docs.sync_one(source,previous,out,out/'cache','online',False,1,0)
            self.assertEqual(row['status'],'failed')
            self.assertEqual(old.read_text(),'OLD')

    def test_unrecognized_nonempty_identifier_is_rejected(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['identifier']['url'] = 'doc://other/unrelated'
        with self.assertRaises(ValueError):
            doclib.parse_payload(json.dumps(fixture).encode(),'application/json',URL)

    def test_malformed_metadata_raises_controlled_error(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['metadata'] = []
        with self.assertRaises(ValueError):
            doclib.parse_payload(json.dumps(fixture).encode(),'application/json',URL)

    def test_unavailable_mac_is_not_supported(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['metadata']['platforms'] = [{'name':'macOS','unavailable':True}]
        body = json.dumps(fixture).encode()
        state = dict(pending=[URL],pages={},external_dependencies=[])
        list(discover_docs.crawl(state,lambda u:dict(body=body,sha256=doclib.digest(body)),1))
        self.assertEqual(state['pages'][URL]['macos_status'],'unavailable')

    def test_retry_pending_does_not_inflate_discovered_count(self):
        state = dict(pages={URL:{'status':'failed'}},pending=[URL,URL+'/next'])
        self.assertEqual(discover_docs.coverage(state)['discovered'],2)

    def test_bad_reference_records_failure_and_continues(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['references']['bad'] = 'not a reference object'
        fixture['topicSections'] = [{'identifiers':['bad']}]
        body = json.dumps(fixture).encode()
        state = dict(pending=[URL,URL+'/next'],pages={},external_dependencies=[])
        list(discover_docs.crawl(state,lambda u:dict(body=body,sha256=doclib.digest(body)),1))
        self.assertEqual(state['pages'][URL]['status'],'failed')
        self.assertEqual(state['pending'],[URL+'/next'])

    def test_bad_platform_record_marks_page_failed_without_aborting(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['metadata']['platforms'] = ['macOS']
        body = json.dumps(fixture).encode()
        state = dict(pending=[URL,URL+'/next'],pages={},external_dependencies=[])
        list(discover_docs.crawl(state,lambda u:dict(body=body,sha256=doclib.digest(body)),1))
        self.assertEqual(state['pages'][URL]['status'],'failed')
        self.assertEqual(state['pending'],[URL+'/next'])
