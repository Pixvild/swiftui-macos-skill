#!/usr/bin/env python3
"""Validate captured raw bytes and export readable bodies with an automatic index."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from doclib import atomic_write, digest, doc_key, parse_payload, write_json
from collect_docs import ROOT, collection_complete, linked_pages, summary


def export(source, output, require_complete=False):
    source, output = Path(source), Path(output)
    state = json.loads((source/'collection.json').read_text())
    if require_complete and not collection_complete(state):
        raise ValueError('Collection incomplete: pending pages or unresolved failures')
    documents, warning_counts = [], Counter()
    all_links = set()
    lines = ['# SwiftUI official document lookup', '',
        'Generated from captured Apple DocC responses. Downloaded does not mean read or compiled.', '',
        '| Document | Local body | macOS metadata |', '| --- | --- | --- |']
    for url, page in sorted(state['pages'].items()):
        if page['status'] != 'fetched':
            continue
        folder = (source/page['snapshot_path']).resolve()
        if source.resolve() not in folder.parents:
            raise ValueError('Snapshot path outside collection')
        body = (folder/'raw.json').read_bytes()
        if digest(body) != page['sha256']:
            raise ValueError('Raw SHA-256 mismatch: '+url)
        parsed = parse_payload(body,'application/json',url)
        if require_complete and not parsed['metadata'].get('identifier'):
            raise ValueError('Source identity not verified: '+url)
        links, _ = linked_pages(json.loads(body))
        all_links.update(links)
        title = parsed['metadata']['title']
        slug = re.sub('[^a-z0-9]+','-',title.lower()).strip('-')[:70] or 'document'
        path = 'official/'+slug+'-'+doc_key(url)+'.md'
        atomic_write(output/path, ('> Source: '+url+'\n> Converted reference; full visual and language-variant fidelity not established.\n\n'+parsed['markdown']).encode())
        metadata = parsed['metadata']
        documents.append(dict(id='D'+doc_key(url),url=url,title=title,content_path=path,
            sha256=page['sha256'],kind=metadata.get('kind'),platforms=metadata.get('platforms'),
            declarations=metadata.get('declarations'),warnings=parsed['warnings'],
            read_status='not_reviewed',build_status='not_run'))
        warning_counts.update(parsed['warnings'])
        mac = next((p for p in metadata.get('platforms') or [] if p.get('name')=='macOS'),None)
        text = json.dumps(mac,ensure_ascii=False) if mac else 'unknown / not listed; inspect source'
        lines.append('| ['+title.replace('|','\\|')+']('+url+') | ['+path.split('/')[-1]+']('+path+') | '+text.replace('|','\\|')+' |')
    if require_complete and (ROOT not in state['pages'] or all_links - set(state['pages'])):
        raise ValueError('Captured raw graph is not closed; missing referenced pages')
    report = dict(summary(state),exported=len(documents),
        warning_counts=dict(warning_counts),raw_hashes_verified=True,
        raw_graph_closure_verified=bool(require_complete),
        full_document_fidelity='not_established')
    write_json(output/'catalog.json',dict(schema_version=1,documents=documents))
    write_json(output/'sources.json',dict(schema_version=1,sources=[
        dict(id=d['id'],url=d['url'],document_key=doc_key(d['url'])) for d in documents]))
    write_json(output/'coverage.json',report)
    write_json(output/'external-dependencies.json',state['external_dependencies'])
    atomic_write(output/'lookup.md', ('\n'.join(lines)+'\n').encode())
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('references/local/full'))
    parser.add_argument('--output',type=Path,default=Path('references/local/full/export'))
    parser.add_argument('--require-complete',action='store_true')
    args=parser.parse_args()
    try:
        report=export(args.source,args.output,args.require_complete)
        print(json.dumps(report,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        parser.exit(1,str(error)+'\n')


if __name__=='__main__':
    raise SystemExit(main())
