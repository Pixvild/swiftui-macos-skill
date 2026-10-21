#!/usr/bin/env python3
"""Bounded, resumable discovery of SwiftUI topic navigation. Not a completeness claim."""
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin
from doclib import BASE, canonical_url, cached_fetch, doc_key, endpoint_candidates, parse_payload, utc_now, write_json


def children(document):
    refs = document.get('references', {})
    found, external = set(), set()
    for section in document.get('topicSections', []):
        for identifier in section.get('identifiers', []):
            ref = refs.get(identifier, {})
            if not isinstance(ref, dict):
                raise ValueError('Malformed topic reference: ' + str(identifier))
            url = ref.get('url')
            if not url:
                continue
            absolute = urljoin(BASE, url)
            try:
                found.add(canonical_url(absolute))
            except ValueError:
                external.add(absolute)
    return sorted(found), sorted(external)


def crawl(state, fetch, limit):
    processed = 0
    while state['pending'] and processed < limit:
        url = state['pending'][0]
        previous = state['pages'].get(url, {})
        try:
            response = fetch(url)
            parsed = parse_payload(response['body'], 'application/json', url)
            raw = json.loads(response['body'])
            links, external = children(raw)
            state['pages'][url] = dict(parsed['metadata'], url=url, status='fetched',
                sha256=response['sha256'], warnings=parsed['warnings'],
                access_status=response.get('status','unknown'),
                macos_status=macos_status(parsed['metadata'].get('platforms')),
                read_status='not_reviewed', build_status='not_run')
            state['external_dependencies'] = sorted(set(state['external_dependencies']) | set(external))
            for link in links:
                if link not in state['pages'] and link not in state['pending']:
                    state['pending'].append(link)
        except (OSError, ValueError, KeyError, TypeError) as error:
            state['pages'][url] = dict(previous, url=url, status='failed', error=str(error))
        state['pending'].pop(0)
        processed += 1
        state['updated_at'] = utc_now()
        yield state


def macos_status(platforms):
    if not platforms:
        return 'unknown'
    for platform in platforms:
        if platform.get('name') == 'macOS':
            return 'unavailable' if platform.get('unavailable') else 'listed'
    return 'not_listed'


def coverage(state):
    documents = list(state['pages'].values())
    good = sum(p['status'] == 'fetched' for p in documents)
    return dict(visited=len(documents), fetched=good, failed=len(documents)-good,
        pending=len(state['pending']), discovered=len(set(state['pages']) | set(state['pending'])),
        scope='SwiftUI root topicSections traversal; not all references or language variants',
        complete=False, read=0, compiled=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('references/local/discovery'))
    parser.add_argument('--cache', type=Path, default=Path('.cache/discovery'))
    parser.add_argument('--limit', type=int, default=10, help='Maximum additional requests this run')
    parser.add_argument('--retry-failed', action='store_true')
    parser.add_argument('--mode', choices=['online','offline'], default='online')
    args = parser.parse_args()
    if args.limit < 1: parser.error('--limit must be positive')
    path = args.output/'discovery.json'
    state = json.loads(path.read_text()) if path.exists() else dict(schema_version=1,
        root=BASE+'/documentation/swiftui', pending=[BASE+'/documentation/swiftui'], pages={}, external_dependencies=[])
    if args.retry_failed:
        for url, page in state['pages'].items():
            if page['status'] == 'failed' and url not in state['pending']: state['pending'].append(url)
    def fetch(url):
        return cached_fetch(endpoint_candidates(url)[0], args.cache, mode=args.mode, timeout=15)
    for state in crawl(state, fetch, args.limit):
        write_json(path, state)
    documents = sorted(state['pages'].values(), key=lambda p:p['url'])
    write_json(args.output/'catalog.json', dict(schema_version=1, documents=documents))
    sources = [dict(id='D'+doc_key(p['url']), url=p['url'], document_key=doc_key(p['url'])) for p in documents]
    write_json(args.output/'sources.json', dict(schema_version=1, sources=sources))
    report = coverage(state)
    write_json(args.output/'coverage.json', report)
    print(json.dumps(report, ensure_ascii=False))
    return 1 if report['failed'] else 0

if __name__ == '__main__': raise SystemExit(main())
