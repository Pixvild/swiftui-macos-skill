#!/usr/bin/env python3
"""Publish metadata and a corpus location after a verified collection; no network."""
import json
import os
from pathlib import Path
from collect_docs import collection_complete
from doclib import atomic_write, write_json


def main():
    source=Path('references/local/full')
    state=json.loads((source/'collection.json').read_text())
    report=json.loads((source/'export/coverage.json').read_text())
    if not collection_complete(state) or not report.get('complete') or not report.get('raw_hashes_verified') or not report.get('raw_graph_closure_verified'):
        raise ValueError('Refusing to publish incomplete collection evidence')
    corpus=os.environ['CORPUS_URL']
    run=os.environ['RUN_URL']
    if not corpus.startswith('https://github.com/Pixvild/swiftui-macos-skill/actions/') or not run.startswith('https://github.com/Pixvild/swiftui-macos-skill/actions/'):
        raise ValueError('Corpus and workflow locations must belong to this repository')
    catalog=json.loads((source/'export/catalog.json').read_text())
    if len(catalog['documents']) != report['exported'] or report['exported'] != report['fetched']:
        raise ValueError('Catalog/coverage counts disagree')
    report.update(corpus_url=corpus,workflow_url=run)
    write_json(Path('references/full-catalog.json'),catalog)
    atomic_write(Path('references/full-sources.json'),(source/'export/sources.json').read_bytes())
    write_json(Path('reports/full-coverage.json'),report)
    atomic_write(Path('references/full-coverage.md'),(
        '# SwiftUI collection coverage\n\n'
        f"Scope: {report['scope']}\n\n"
        f"Discovered: {report['discovered']}; fetched/exported: {report['fetched']}; failed: {report['failed']}; pending: {report['pending']}.\n\n"
        f"[Download captured corpus]({corpus}) · [Verified collection run]({run})\n\n"
        'Extract the corpus into references/local/full; export/lookup.md and export/catalog.json route to the readable official bodies. '
        'The archive also retains raw JSON and per-page provenance. GitHub artifact retention applies; this is a captured snapshot, not a permanent mirror service.\n\n'
        'Raw response hashes verified. Downloaded is not read or compiled. Language variants are retained raw, not fully interpreted; images and videos remain references. '
        'Completion covers the reachable SwiftUI reference graph, not unlinked pages or every Apple framework.\n').encode())
    return 0


if __name__=='__main__':
    raise SystemExit(main())
