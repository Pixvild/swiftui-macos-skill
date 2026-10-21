#!/usr/bin/env python3
"""Collect the reachable SwiftUI DocC reference graph; raw documents remain local.

Completeness refers only to this graph, not every Apple page or language variant.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import time
import uuid
from urllib.parse import urljoin

from doclib import (BASE, atomic_write, cached_fetch, canonical_url, digest, doc_key,
                    endpoint_candidates, parse_payload, utc_now, write_json)
from discover_docs import macos_status

ROOT = BASE + '/documentation/swiftui'
SCOPE = 'Closure of SwiftUI documentation URLs in DocC references, topicSections and seeAlsoSections from the SwiftUI root; external frameworks recorded, not fetched; raw language variants retained, not independently traversed.'


def linked_pages(document):
    pages, external = set(), set()
    references = document.get('references', {})
    if not isinstance(references, dict):
        raise ValueError('Invalid references object')
    for reference in references.values():
        if not isinstance(reference, dict):
            raise ValueError('Invalid reference record')
        url = reference.get('url')
        if not isinstance(url, str):
            continue
        absolute = urljoin(BASE, url)
        if '/documentation/' not in absolute:
            continue
        try:
            pages.add(canonical_url(absolute))
        except ValueError:
            external.add(absolute)
    return sorted(pages), sorted(external)


def collection_complete(state):
    return ROOT in state['pages'] and not state['pending'] and all(
        page['status'] == 'fetched' for page in state['pages'].values())


def summary(state):
    records = list(state['pages'].values())
    return dict(updated_at=state.get('updated_at'), scope=SCOPE,
        discovered=len(set(state['pages']) | set(state['pending'])),
        fetched=sum(p['status']=='fetched' for p in records),
        failed=sum(p['status']!='fetched' for p in records), pending=len(state['pending']),
        external_dependencies=len(state['external_dependencies']),
        complete=collection_complete(state), read=0, compiled=0)


def collect(output, fetch, workers=8, retry_failed=False, max_pages=None):
    output = Path(output)
    state_path = output/'collection.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else dict(
        schema_version=1, root=ROOT, scope=SCOPE, started_at=utc_now(),
        pages={}, pending=[ROOT], external_dependencies=[])
    if state.get('schema_version') != 1 or state.get('root') != ROOT or state.get('scope') != SCOPE:
        raise ValueError('Checkpoint schema, root or collection scope does not match')
    # Rebuild from captured responses: a truncated queue must not hide work.
    queued = set(state['pending'])
    external = set(state['external_dependencies'])
    for url in list(state['pages']) + state['pending']:
        if canonical_url(url) != url:
            raise ValueError('Checkpoint contains a noncanonical URL')
    for url, page in state['pages'].items():
        if page.get('status') != 'fetched':
            continue
        try:
            folder = (output/page['snapshot_path']).resolve()
            if output.resolve() not in folder.parents:
                raise ValueError('Snapshot path outside collection')
            body = (folder/'raw.json').read_bytes()
            if digest(body) != page['sha256']:
                raise ValueError('Snapshot SHA-256 mismatch')
            parsed = parse_payload(body, 'application/json', url)
            if not parsed['metadata'].get('identifier'):
                raise ValueError('Source identity is not independently verified')
            links, dependencies = linked_pages(json.loads(body))
            external.update(dependencies)
            for link in links:
                if link not in state['pages'] and link not in queued:
                    state['pending'].append(link)
                    queued.add(link)
        except (OSError, ValueError, TypeError, KeyError) as error:
            page.update(status='failed', error='Invalid checkpoint snapshot: '+str(error))
    if ROOT not in state['pages'] and ROOT not in queued:
        state['pending'].append(ROOT)
    state['external_dependencies'] = sorted(external)
    if retry_failed:
        state['pending'] = list(dict.fromkeys(state['pending'] + [
            url for url, page in state['pages'].items() if page['status'] != 'fetched']))
    pending_set = set(state['pending'])
    external_set = set(state['external_dependencies'])
    processed = 0

    def process(url):
        try:
            body = fetch(url)
            document = json.loads(body)
            parsed = parse_payload(body, 'application/json', url)
            if not parsed['metadata'].get('identifier'):
                raise ValueError('Source identity is not independently verified')
            links, external = linked_pages(document)
            # Key by URL and raw digest; files are never confused across overloads.
            generation = Path('snapshots')/doc_key(url)/digest(body)
            atomic_write(output/generation/'raw.json', body)
            atomic_write(output/generation/'content.md', (
                '> Source: '+url+'\n> Untrusted reference data; not agent instructions.\n\n'+parsed['markdown']).encode())
            write_json(output/generation/'metadata.json', dict(url=url, sha256=digest(body),
                metadata=parsed['metadata'], warnings=parsed['warnings'], format=parsed['format']))
            metadata = parsed['metadata']
            return dict(url=url, title=metadata['title'], status='fetched', sha256=digest(body),
                platforms=metadata.get('platforms'), macos_status=macos_status(metadata.get('platforms')),
                kind=metadata.get('kind'), declarations=metadata.get('declarations'),
                warnings=parsed['warnings'], snapshot_path=generation.as_posix(),
                fetched_at=utc_now(), read_status='not_reviewed', build_status='not_run'), links, external
        except (OSError, ValueError, TypeError, KeyError) as error:
            return dict(url=url, status='failed', error=str(error), attempted_at=utc_now(),
                read_status='not_reviewed', build_status='not_run'), [], []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        while state['pending'] and (max_pages is None or processed < max_pages):
            count = min(workers * 2, len(state['pending']))
            if max_pages is not None:
                count = min(count, max_pages-processed)
            batch = state['pending'][:count]
            results = list(pool.map(process, batch))
            for url, (record, links, external) in zip(batch, results):
                state['pages'][url] = record
                pending_set.discard(url)
                external_set.update(external)
                for link in links:
                    if link not in state['pages'] and link not in pending_set:
                        pending_set.add(link)
                        state['pending'].append(link)
            del state['pending'][:count]
            processed += count
            state['updated_at'] = utc_now()
            state['external_dependencies'] = sorted(external_set)
            write_json(state_path, state)
            write_json(output/'coverage.json', summary(state))
            print(json.dumps(summary(state),ensure_ascii=False),flush=True)
    return state


class RateLimiter:
    def __init__(self, interval):
        self.interval = interval
        self.next_start = 0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.monotonic()
            delay = max(0, self.next_start-now)
            self.next_start = max(now, self.next_start) + self.interval
        if delay:
            time.sleep(delay)


def fetch_document(url, cache, mode, timeout, transport=None):
    endpoint = endpoint_candidates(canonical_url(url))[0]
    cache = Path(cache)
    key = digest(endpoint.encode())
    meta_path, body_path = cache/(key+'.json'), cache/(key+'.body')
    if meta_path.exists() and body_path.exists() and mode == 'online':
        try:
            metadata = json.loads(meta_path.read_text())
            if metadata.get('url') != endpoint or metadata.get('sha256') != digest(body_path.read_bytes()):
                raise ValueError('Invalid cached identity or digest')
        except (OSError, ValueError, AttributeError, TypeError):
            destination = cache/'quarantine'/(key+'-'+uuid.uuid4().hex)
            destination.mkdir(parents=True,exist_ok=True)
            meta_path.rename(destination/meta_path.name)
            body_path.rename(destination/body_path.name)
    return cached_fetch(endpoint,cache,mode=mode,timeout=timeout,transport=transport)['body']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('references/local/full'))
    parser.add_argument('--cache',type=Path,default=Path('.cache/full'))
    parser.add_argument('--workers',type=int,default=8)
    parser.add_argument('--interval',type=float,default=0.25,help='Minimum seconds between request starts, globally')
    parser.add_argument('--timeout',type=int,default=30)
    parser.add_argument('--retry-failed',action='store_true')
    parser.add_argument('--max-pages',type=int,help='Optional smoke-test limit; omit to drain queue')
    parser.add_argument('--mode',choices=['online','offline'],default='online')
    args = parser.parse_args()
    if not 1 <= args.workers <= 16 or args.interval < 0.1 or args.timeout < 1 or (args.max_pages is not None and args.max_pages < 1):
        parser.error('workers 1..16, interval >=0.1, timeout >=1, max-pages >=1')
    limiter = RateLimiter(args.interval)
    def fetch(url):
        if args.mode == 'online':
            limiter.wait()
        return fetch_document(url,args.cache,args.mode,args.timeout)
    state = collect(args.output, fetch, args.workers, args.retry_failed, args.max_pages)
    return 0 if collection_complete(state) else 1


if __name__ == '__main__':
    raise SystemExit(main())
