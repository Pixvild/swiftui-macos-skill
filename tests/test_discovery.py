import json
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from discover_docs import children, crawl
from doclib import digest
BASE='https://developer.apple.com/documentation/swiftui'

def response(url, links=()):
    doc={'identifier':{'url':url},'metadata':{'title':'Example'},'abstract':[],
         'topicSections':[{'identifiers':list(links)}],
         'references':{x:{'url':x} for x in links}}
    body=json.dumps(doc).encode()
    return {'body':body,'sha256':digest(body)}

class DiscoveryTests(unittest.TestCase):
    def test_only_topics_and_cross_framework_registration(self):
        d=json.loads(response(BASE,[BASE+'/view','/documentation/appkit/nsview'])['body'])
        d['references']['unrelated']={'url':BASE+'/text'}
        self.assertEqual(children(d),([BASE+'/view'],['https://developer.apple.com/documentation/appkit/nsview']))
    def test_bounded_resume_and_cycle(self):
        state=dict(pending=[BASE],pages={},external_dependencies=[])
        calls=[]
        def fetch(url):
            calls.append(url)
            return response(url,[BASE,BASE+'/view',BASE+'/view'])
        list(crawl(state,fetch,1))
        self.assertEqual(state['pending'],[BASE+'/view'])
        list(crawl(state,fetch,1))
        self.assertEqual(state['pending'],[])
        self.assertEqual(len(calls),2)
    def test_failure_does_not_hide_remaining_work(self):
        state=dict(pending=[BASE,BASE+'/view'],pages={},external_dependencies=[])
        def fail(url): raise OSError('unavailable')
        list(crawl(state,fail,1))
        self.assertEqual(state['pages'][BASE]['status'],'failed')
        self.assertEqual(state['pending'],[BASE+'/view'])
