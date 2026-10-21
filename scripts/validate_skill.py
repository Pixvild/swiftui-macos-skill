#!/usr/bin/env python3
"""Static package checks; this is not a Codex-host or behavior certification."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from doclib import doc_key, validate_manifest

ROOT=Path(__file__).resolve().parents[1]


def validate(root):
    errors=[]
    required=['SKILL.md','README.md','agents/openai.yaml','references/sources.json',
              'references/catalog.json','references/coverage.md','references/swiftui-lookup.md',
              'references/source-notes.md','references/verification.md','references/sync-workflow.md',
              'scripts/sync_docs.py','scripts/probe_environment.py','tests/scenarios.md']
    errors += ['Missing '+name for name in required if not (root/name).is_file()]
    if errors:return errors
    skill=(root/'SKILL.md').read_text('utf-8')
    front=re.match(r'\A---\n(.*?)\n---\n',skill,re.S)
    if not front: errors.append('SKILL.md requires YAML frontmatter')
    else:
        if not re.search(r'^name: swiftui-macos$',front.group(1),re.M): errors.append('Unexpected skill name')
        if not re.search(r'^description: .+',front.group(1),re.M): errors.append('Missing description')
    try:
        manifest=json.loads((root/'references/sources.json').read_text('utf-8'))
        sources=validate_manifest(manifest)
        for source in sources:
            if source.get('document_key')!=doc_key(source['url']): errors.append('Document key mismatch: '+source['id'])
        ids={s['id'] for s in sources}
        catalog=json.loads((root/'references/catalog.json').read_text('utf-8'))
        if {s['id'] for s in catalog['documents']}!=ids: errors.append('Catalog/source IDs differ')
        for topic in catalog['topics']:
            if not (root/'references'/topic['guide']).is_file():errors.append('Missing topic guide: '+topic['guide'])
            if set(topic['source_ids'])-ids:errors.append('Unknown source ID in topic')
        for path in (root/'references/guides').glob('*.md'):
            for identifier in re.findall(r'\bSW\d{2}\b',path.read_text('utf-8')):
                if identifier not in ids:errors.append('Unknown source '+identifier+' in '+str(path))
    except (OSError,ValueError,KeyError,TypeError) as error:errors.append(str(error))
    for path in root.rglob('*.json'):
        if any(p in {'.cache','__pycache__','local'} for p in path.parts):continue
        try:json.loads(path.read_text('utf-8'))
        except (OSError,ValueError) as error:errors.append('Invalid JSON '+str(path)+': '+str(error))
    for path in root.rglob('*.md'):
        if any(p in {'.cache','local'} for p in path.parts):continue
        text=path.read_text('utf-8')
        # Check local file links only; no network and no claim to check anchors.
        for link in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)',text):
            if '://' in link or link.startswith(('#','mailto:')):continue
            target=(path.parent/link.split('#',1)[0]).resolve()
            if not target.exists():errors.append('Broken local link in '+str(path.relative_to(root))+': '+link)
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    errors=validate(args.root)
    for error in errors:print('ERROR: '+error)
    if not errors:print('PASS: skill frontmatter, required files, source identities, catalog, JSON and local file links. Host/behavior checks not included.')
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
