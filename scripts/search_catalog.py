#!/usr/bin/env python3
"""Search a local source or discovered catalog; no network or availability inference."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def search(documents, query, platform=None):
    result = []
    terms = query.casefold().split()
    for document in documents:
        if document.get('status') == 'failed':
            continue
        # Unknown platform metadata must retain conceptual articles for inspection.
        platforms = document.get('platforms')
        if platform and platforms and not any(p.get('name', '').casefold() == platform.casefold() for p in platforms):
            continue
        text = json.dumps(document, ensure_ascii=False).casefold()
        if all(term in text for term in terms):
            result.append(document)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='?', default='')
    parser.add_argument('--catalog', type=Path, default=ROOT/'references/catalog.json')
    parser.add_argument('--platform', help='Retain matching or unknown platform metadata')
    args = parser.parse_args()
    try:
        data = json.loads(args.catalog.read_text('utf-8'))
        documents = data['documents']
        if not isinstance(documents, list):
            raise ValueError('catalog.documents must be a list')
        print(json.dumps(search(documents, args.query, args.platform), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, str(error)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
