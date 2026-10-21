import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from search_catalog import search

class SearchTests(unittest.TestCase):
    def test_finds_specific_overload_without_merging(self):
        docs = [{'title':'badge(_:)', 'url':'/a', 'declarations':[{'text':'func badge(_ text: String)'}]},
                {'title':'badge(_:)', 'url':'/b', 'declarations':[{'text':'func badge(_ count: Int)'}]}]
        self.assertEqual([d['url'] for d in search(docs, 'badge')], ['/a','/b'])
        self.assertEqual([d['url'] for d in search(docs, 'String')], ['/a'])
    def test_platform_filter_retains_unknown_articles(self):
        docs = [{'title':'Unknown','platforms':None},
                {'title':'Mac','platforms':[{'name':'macOS','introducedAt':'14.0'}]},
                {'title':'Phone','platforms':[{'name':'iOS'}]}]
        self.assertEqual([d['title'] for d in search(docs, '', 'macOS')], ['Unknown','Mac'])
        self.assertIsNone(docs[0]['platforms'])
    def test_failed_pages_are_not_search_results(self):
        self.assertEqual(search([{'title':'Broken', 'status':'failed'}], ''), [])
