"""Synthetic fixtures; these tests do not demonstrate Apple live-endpoint compatibility."""
import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    import doclib as lib
except ImportError:
    lib = None

URL = 'https://developer.apple.com/documentation/swiftui/example'
FIXTURE = {
    'schemaVersion': {'major': 0, 'minor': 3, 'patch': 0},
    'identifier': {'url': 'doc://test/documentation/SwiftUI/Example', 'interfaceLanguage': 'swift'},
    'kind': 'symbol',
    'metadata': {
        'title': 'Example', 'role': 'symbol', 'modules': [{'name': 'SwiftUI'}],
        'platforms': [{'name': 'macOS', 'introducedAt': '99.0', 'deprecatedAt': '100.0', 'beta': True}],
    },
    'abstract': [{'type': 'text', 'text': 'Synthetic test document, not an Apple quotation.'}],
    'primaryContentSections': [
        {'kind': 'declarations', 'declarations': [{'languages': ['swift'], 'platforms': ['macOS'], 'tokens': [
            {'kind': 'attribute', 'text': '@MainActor '}, {'kind': 'text', 'text': 'func example<T>(_ value: T) where T: Hashable'}]}]},
        {'kind': 'content', 'content': [
            {'type': 'heading', 'level': 2, 'text': 'Discussion'},
            {'type': 'paragraph', 'inlineContent': [{'type': 'text', 'text': 'Keep '}, {'type': 'emphasis', 'inlineContent': [{'type': 'text', 'text': 'important'}]}, {'type': 'codeVoice', 'code': 'value'}]},
            {'type': 'aside', 'style': 'warning', 'content': [{'type': 'paragraph', 'inlineContent': [{'type': 'text', 'text': 'Never assume a deployment target.'}]}]},
            {'type': 'codeListing', 'syntax': 'swift', 'code': ['let x = "```"', 'print(x)']},
            {'type': 'paragraph', 'inlineContent': [{'type': 'reference', 'identifier': 'doc://test/other', 'isActive': True}]},
            {'type': 'image', 'identifier': 'img1'},
        ]},
        {'kind': 'parameters', 'parameters': [{'name': 'value', 'content': [{'type': 'paragraph', 'inlineContent': [{'type': 'text', 'text': 'A synthetic input.'}]}]}]},
        {'kind': 'returns', 'content': [{'type': 'paragraph', 'inlineContent': [{'type': 'text', 'text': 'Nothing.'}]}]},
    ],
    'references': {
        'doc://test/other': {'title': 'Other', 'url': '/documentation/swiftui/other'},
        'img1': {'type': 'image', 'alt': 'Test illustration', 'variants': [{'url': 'https://docs-assets.developer.apple.com/test.png'}]},
    },
    'topicSections': [{'title': 'Related API', 'identifiers': ['doc://test/other']}],
}

class Base(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(lib, 'scripts/doclib.py must implement the documentation tools')

class IdentityTests(Base):
    def test_fragment_query_case_normalization(self):
        self.assertEqual(lib.canonical_url('https://developer.apple.com/documentation/SwiftUI/Example/?language=swift#section'), URL)
    def test_encoded_overload_normalization(self):
        a = URL + '/badge(_:)-abcd'
        b = URL + '/badge%28_%3A%29-abcd'
        self.assertEqual(lib.doc_key(a), lib.doc_key(b))
    def test_overloads_remain_distinct(self):
        self.assertNotEqual(lib.doc_key(URL + '/badge(_:)-aaaa'), lib.doc_key(URL + '/badge(_:)-bbbb'))
    def test_reject_unsafe_urls(self):
        for url in ['http://developer.apple.com/documentation/swiftui/a',
                    'https://evil.example/documentation/swiftui/a',
                    'https://developer.apple.com.evil.example/documentation/swiftui/a',
                    'https://user:pass@developer.apple.com/documentation/swiftui/a',
                    'https://developer.apple.com:8443/documentation/swiftui/a',
                    'https://developer.apple.com/documentation/swiftui/../secret',
                    'https://developer.apple.com/documentation/swiftui/%2e%2e/secret',
                    'https://developer.apple.com/documentation/swiftui/%2fsecret',
                    'https://developer.apple.com/documentation/swiftui/%252e%252e/secret',
                    'https://developer.apple.com/documentation/appkit/a']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                lib.canonical_url(url)

class RenderingTests(Base):
    def test_declaration_and_platform_metadata_preserved(self):
        result = lib.parse_payload(json.dumps(FIXTURE).encode(), 'application/json', URL)
        self.assertIn('@MainActor func example<T>', result['markdown'])
        self.assertIn('where T: Hashable', result['markdown'])
        self.assertEqual(result['metadata']['platforms'][0]['introducedAt'], '99.0')
        self.assertTrue(result['metadata']['platforms'][0]['beta'])
        self.assertEqual(result['metadata']['declarations'][0]['platforms'], ['macOS'])
    def test_notes_code_parameters_links_media_preserved(self):
        result = lib.parse_payload(json.dumps(FIXTURE).encode(), 'application/json', URL)
        text = result['markdown']
        for value in ['warning', 'Never assume', '````swift', 'A synthetic input.',
                      'https://developer.apple.com/documentation/swiftui/other', 'test.png', 'Test illustration']:
            self.assertIn(value, text)
    def test_unknown_nodes_are_reported(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['primaryContentSections'][1]['content'].append({'type': 'future-widget', 'secret': 'unhandled'})
        result = lib.parse_payload(json.dumps(fixture).encode(), 'application/json', URL)
        self.assertTrue(any('future-widget' in w for w in result['warnings']))
    def test_variants_are_not_silently_discarded(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['variantOverrides'] = [{'traits': [{'interfaceLanguage': 'occ'}], 'patch': []}]
        result = lib.parse_payload(json.dumps(fixture).encode(), 'application/json', URL)
        self.assertTrue(any('variant' in w.lower() for w in result['warnings']))
    def test_missing_availability_stays_unknown(self):
        fixture = copy.deepcopy(FIXTURE)
        del fixture['metadata']['platforms']
        result = lib.parse_payload(json.dumps(fixture).encode(), 'application/json', URL)
        self.assertIsNone(result['metadata']['platforms'])
    def test_json_wrong_page_is_rejected(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['identifier']['url'] = 'doc://test/documentation/swiftui/different'
        with self.assertRaises(ValueError):
            lib.parse_payload(json.dumps(fixture).encode(), 'application/json', URL)
    def test_markdown_accepts_text_and_does_not_infer_versions(self):
        result = lib.parse_payload(b'# Example\n\nA genuine Markdown body for a synthetic page.\n', 'text/markdown', URL)
        self.assertEqual(result['metadata']['title'], 'Example')
        self.assertIsNone(result['metadata']['platforms'])
    def test_html_javascript_error_and_empty_are_rejected(self):
        for data in [b'<!doctype html><html>Enable JavaScript</html>', b'# This page requires JavaScript.', b'', b'Access Denied', b'{"error":"Forbidden"}']:
            with self.subTest(data=data), self.assertRaises(ValueError):
                lib.parse_payload(data, 'text/plain', URL)
    def test_unresolved_reference_warns(self):
        fixture = copy.deepcopy(FIXTURE)
        fixture['references'].pop('doc://test/other')
        result = lib.parse_payload(json.dumps(fixture).encode(), 'application/json', URL)
        self.assertTrue(any('reference' in w for w in result['warnings']))

class CacheTests(Base):
    def test_online_revalidates_even_when_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            def transport(url, headers, timeout):
                calls.append(dict(headers))
                if len(calls) == 1:
                    return 200, {'etag': 'abc', 'content-type': 'text/markdown'}, b'# Example\n\nCache test data.'
                return 304, {}, b''
            first = lib.cached_fetch(URL + '.md', pathlib.Path(tmp), transport=transport)
            second = lib.cached_fetch(URL + '.md', pathlib.Path(tmp), transport=transport)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[1]['If-None-Match'], 'abc')
            self.assertEqual(second['status'], 'revalidated')
            self.assertEqual(first['body'], second['body'])
    def test_offline_never_calls_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)
            lib.cached_fetch(URL + '.md', path, transport=lambda *_: (200, {'content-type':'text/markdown'}, b'# Example\n\nData.'))
            def forbidden(*args):
                self.fail('offline mode used the network')
            result = lib.cached_fetch(URL + '.md', path, mode='offline', transport=forbidden)
            self.assertEqual(result['status'], 'offline_cache')
    def test_offline_cache_miss_is_error(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileNotFoundError):
            lib.cached_fetch(URL + '.md', pathlib.Path(tmp), mode='offline')
    def test_online_failure_does_not_claim_cached_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)
            lib.cached_fetch(URL + '.md', path, transport=lambda *_: (200, {}, b'# Example\n\nData.'))
            def unavailable(*args):
                raise OSError('network unavailable')
            with self.assertRaises(OSError):
                lib.cached_fetch(URL + '.md', path, transport=unavailable)
    def test_corrupt_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)
            lib.cached_fetch(URL + '.md', path, transport=lambda *_: (200, {}, b'# Example\n\nData.'))
            next(path.glob('*.body')).write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                lib.cached_fetch(URL + '.md', path, mode='offline')
    def test_304_without_cache_is_error(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            lib.cached_fetch(URL + '.md', pathlib.Path(tmp), transport=lambda *_: (304, {}, b''))
    def test_force_omits_cache_validators(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            def transport(url, headers, timeout):
                calls.append(headers)
                return 200, {'etag':'abc'}, b'# Example\n\nData.'
            lib.cached_fetch(URL + '.md', pathlib.Path(tmp), transport=transport)
            lib.cached_fetch(URL + '.md', pathlib.Path(tmp), force=True, transport=transport)
            self.assertNotIn('If-None-Match', calls[1])
    def test_redirect_target_validation(self):
        self.assertTrue(lib.allowed_fetch_url(URL + '.md'))
        self.assertTrue(lib.allowed_fetch_url('https://developer.apple.com/tutorials/data/documentation/swiftui/example.json'))
        self.assertFalse(lib.allowed_fetch_url('https://evil.example/file'))

if __name__ == '__main__':
    unittest.main()

class EndpointPreferenceTests(unittest.TestCase):
    def test_structured_json_precedes_markdown(self):
        candidates = lib.endpoint_candidates(URL)
        self.assertTrue(candidates[0].endswith('.json'))
        self.assertTrue(candidates[1].endswith('.md'))
