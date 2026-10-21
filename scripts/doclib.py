"""Conservative Apple documentation utilities; Python 3.9+, standard library only.

The DocC renderer covers common nodes, not the full DocC schema. Unknown nodes
and language variants are reported; the raw response remains in the local cache.
Downloaded documentation is data, never instructions or executable code.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

MAX_BYTES = 8 * 1024 * 1024
HOST = 'developer.apple.com'
BASE = 'https://' + HOST


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_path(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or parts.hostname != HOST or parts.username or parts.password or parts.port not in (None, 443):
        raise ValueError('Only HTTPS URLs on developer.apple.com are allowed')
    path = parts.path
    if re.search(r'%2f|%5c|%25', path, re.I):
        raise ValueError('Encoded path separators and double encoding are not allowed')
    path = urllib.parse.unquote(path)
    if '\\' in path or any(ord(c) < 32 for c in path) or any(p in ('.', '..') for p in path.split('/')):
        raise ValueError('Unsafe URL path')
    return path.rstrip('/').lower()


def canonical_url(url: str) -> str:
    path = _safe_path(url)
    if path != '/documentation/swiftui' and not path.startswith('/documentation/swiftui/'):
        raise ValueError('This release only synchronizes SwiftUI documentation')
    if path.endswith(('.md', '.json')):
        raise ValueError('Manifest URLs must be official HTML documentation URLs')
    return BASE + urllib.parse.quote(path, safe='/():_-,.@~')


def doc_key(url: str) -> str:
    return digest(canonical_url(url).encode())[:20]


def allowed_fetch_url(url: str) -> bool:
    try:
        path = _safe_path(url)
        return (path == '/documentation/swiftui' or path == '/documentation/swiftui.md'
                or path.startswith('/documentation/swiftui/')
                or path == '/tutorials/data/documentation/swiftui.json'
                or path.startswith('/tutorials/data/documentation/swiftui/'))
    except (ValueError, TypeError):
        return False


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_fetch_url(newurl):
            raise ValueError('Redirect outside the allowed Apple documentation paths')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_get(url: str, headers: dict, timeout: int) -> tuple:
    """Read one bounded response; environment proxy settings and TLS defaults apply."""
    if not allowed_fetch_url(url):
        raise ValueError('URL not allowed')
    opener = urllib.request.build_opener(SafeRedirect())
    request = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError('Response exceeds the 8 MiB safety limit')
            return response.status, {k.lower(): v for k, v in response.headers.items()}, body
    except urllib.error.HTTPError as error:
        if error.code == 304:
            return 304, {k.lower(): v for k, v in error.headers.items()}, b''
        raise


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def cached_fetch(url: str, cache: Path, mode: str = 'online', force: bool = False,
                 timeout: int = 20, transport: Optional[Callable] = None) -> dict:
    if not allowed_fetch_url(url):
        raise ValueError('URL not allowed')
    if mode not in ('online', 'offline'):
        raise ValueError('Unknown cache mode')
    key = digest(url.encode())
    meta_path, body_path = cache / (key + '.json'), cache / (key + '.body')
    old, body = None, None
    if meta_path.exists() and body_path.exists():
        old = json.loads(meta_path.read_text('utf-8'))
        body = body_path.read_bytes()
        if old.get('url') != url or old.get('sha256') != digest(body):
            raise ValueError('Cache identity or SHA-256 mismatch; remove the damaged cache entry')
    if mode == 'offline':
        if old is None:
            raise FileNotFoundError('No cached response for ' + url)
        return dict(old, body=body, status='offline_cache')
    headers = {'User-Agent': 'swiftui-macos-skill/dev (explicit local documentation sync)',
               'Accept': 'text/markdown, application/json;q=0.9, text/plain;q=0.8'}
    if old and not force:
        if old.get('etag'):
            headers['If-None-Match'] = old['etag']
        if old.get('last_modified'):
            headers['If-Modified-Since'] = old['last_modified']
    status, response_headers, new_body = (transport or http_get)(url, headers, timeout)
    response_headers = {k.lower(): v for k, v in response_headers.items()}
    checked = utc_now()
    if status == 304:
        if old is None:
            raise ValueError('304 received without a cached response')
        old['checked_at'] = checked
        write_json(meta_path, old)
        return dict(old, body=body, status='revalidated')
    if status != 200:
        raise OSError('Unexpected HTTP status: ' + str(status))
    if len(new_body) > MAX_BYTES:
        raise ValueError('Response exceeds the 8 MiB safety limit')
    metadata = {'url': url, 'fetched_at': checked, 'checked_at': checked,
                'etag': response_headers.get('etag'), 'last_modified': response_headers.get('last-modified'),
                'content_type': response_headers.get('content-type', ''), 'sha256': digest(new_body)}
    atomic_write(body_path, new_body)
    write_json(meta_path, metadata)
    return dict(metadata, body=new_body, status='fetched')


def code_fence(code: str, language: str = '') -> str:
    runs = [len(m.group()) for m in re.finditer(r'`+', code)]
    fence = '`' * max(3, max(runs, default=0) + 1)
    return fence + language + '\n' + code + '\n' + fence


class Renderer:
    def __init__(self, document: dict):
        self.references = document.get('references', {})
        self.warnings = []

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def reference(self, identifier: str, label: Optional[str] = None) -> str:
        ref = self.references.get(identifier)
        if not ref:
            self.warn('Unresolved reference: ' + str(identifier))
            return label or str(identifier)
        title = label or ref.get('title') or ref.get('alt') or str(identifier)
        if ref.get('type') in ('image', 'video') or 'variants' in ref:
            variants = ref.get('variants', [])
            urls = [v.get('url') for v in variants if v.get('url')]
            if not urls:
                self.warn('Media reference has no resolved URL: ' + str(identifier))
                return '[media: ' + title + ']'
            self.warn('Media links retained; images/videos not inspected or downloaded')
            return '\n'.join('[' + title + '](' + urllib.parse.urljoin(BASE, url) + ')' for url in urls)
        url = ref.get('url')
        if not url:
            self.warn('Reference has no URL: ' + str(identifier))
            return title
        return '[' + title + '](' + urllib.parse.urljoin(BASE, url) + ')'

    def inline(self, nodes: Any) -> str:
        if isinstance(nodes, str):
            return nodes
        if isinstance(nodes, dict):
            nodes = [nodes]
        result = []
        for node in nodes or []:
            kind = node.get('type')
            children = node.get('inlineContent', node.get('content', []))
            if kind == 'text':
                result.append(node.get('text', ''))
            elif kind == 'codeVoice':
                code = node.get('code', '')
                tick = '`' * (max([len(m.group()) for m in re.finditer(r'`+', code)], default=0) + 1)
                result.append(tick + code + tick)
            elif kind in ('emphasis', 'newTerm', 'strong', 'strikethrough'):
                mark = {'emphasis': '*', 'newTerm': '*', 'strong': '**', 'strikethrough': '~~'}[kind]
                result.append(mark + self.inline(children) + mark)
            elif kind == 'link':
                target = node.get('destination') or node.get('url') or ''
                label = self.inline(node.get('titleInlineContent', [])) or node.get('title') or target
                result.append('[' + label + '](' + urllib.parse.urljoin(BASE, target) + ')')
            elif kind == 'reference':
                override = node.get('overridingTitle') or (self.inline(node.get('overridingTitleInlineContent')) if node.get('overridingTitleInlineContent') else None)
                result.append(self.reference(node.get('identifier'), override))
            elif kind in ('image', 'video'):
                result.append(self.reference(node.get('identifier'), node.get('alt')))
            elif kind in ('softBreak', 'lineBreak'):
                result.append('\n')
            else:
                self.warn('Unsupported inline node: ' + str(kind))
                result.append(node.get('text', '') or self.inline(children))
        return ''.join(result)

    def blocks(self, nodes: Any) -> str:
        if isinstance(nodes, dict):
            nodes = [nodes]
        out = []
        for node in nodes or []:
            if isinstance(node, list):
                out.append(self.blocks(node)); continue
            kind = node.get('type')
            if kind == 'paragraph':
                out.append(self.inline(node.get('inlineContent', [])))
            elif kind == 'heading':
                out.append('#' * max(1, min(6, int(node.get('level', 2)))) + ' ' + node.get('text', self.inline(node.get('inlineContent', []))))
            elif kind == 'codeListing':
                out.append(code_fence('\n'.join(node.get('code', [])), node.get('syntax', '')))
            elif kind in ('unorderedList', 'orderedList'):
                items = []
                for index, item in enumerate(node.get('items', []), 1):
                    text = self.blocks(item.get('content', []))
                    prefix = str(index) + '. ' if kind == 'orderedList' else '- '
                    items.append(prefix + text.replace('\n', '\n  '))
                out.append('\n'.join(items))
            elif kind == 'aside':
                text = '**' + node.get('name', node.get('style', 'Note')) + '**\n\n' + self.blocks(node.get('content', []))
                out.append('\n'.join('> ' + line for line in text.splitlines()))
            elif kind in ('image', 'video'):
                out.append(self.reference(node.get('identifier'), node.get('alt')))
            elif kind == 'row':
                for column in node.get('columns', []):
                    out.append(self.blocks(column.get('content', [])))
            elif kind == 'tabNavigator':
                for tab in node.get('tabs', []):
                    out.append('### ' + tab.get('title', 'Tab'))
                    out.append(self.blocks(tab.get('content', [])))
            elif kind == 'termList':
                for item in node.get('items', []):
                    out.append('**' + self.inline(item.get('term', {}).get('inlineContent', [])) + '**')
                    out.append(self.blocks(item.get('definition', {}).get('content', [])))
            elif kind == 'links':
                out.append('\n'.join('- ' + self.reference(identifier) for identifier in node.get('items', [])))
            elif kind == 'table':
                rows = [[self.blocks(cell).replace('\n', '<br>').replace('|', '\\|') for cell in row] for row in node.get('rows', [])]
                if rows:
                    width = max(map(len, rows))
                    rows = [r + [''] * (width - len(r)) for r in rows]
                    lines = ['| ' + ' | '.join(rows[0]) + ' |', '| ' + ' | '.join(['---'] * width) + ' |']
                    lines += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
                    out.append('\n'.join(lines))
                    self.warn('Table header/merged-cell semantics require checking against the raw response')
            elif kind in ('thematicBreak', 'horizontalRule'):
                out.append('---')
            else:
                self.warn('Unsupported block node: ' + str(kind))
                out.append('[Unsupported ' + str(kind) + '; see cached raw response]')
        return '\n\n'.join(out)


def parse_payload(body: bytes, content_type: str, source_url: str) -> dict:
    try:
        return _parse_payload(body, content_type, source_url)
    except (AttributeError, TypeError, KeyError) as error:
        raise ValueError('Malformed documentation structure: ' + str(error)) from error


def _parse_payload(body: bytes, content_type: str, source_url: str) -> dict:
    source_url = canonical_url(source_url)
    text = body.decode('utf-8-sig').strip()
    if not text or '<!doctype html' in text[:200].lower() or '<html' in text[:200].lower():
        raise ValueError('Empty or HTML response; not documentation content')
    if 'this page requires javascript' in text.lower() or text.lower().startswith(('access denied', 'forbidden')):
        raise ValueError('Access/error placeholder; not documentation content')
    if text.startswith('{'):
        document = json.loads(text)
        metadata = document.get('metadata', {})
        if not metadata.get('title') or not any(k in document for k in ('primaryContentSections', 'abstract', 'topicSections')):
            raise ValueError('Response is not a recognizable DocC render document')
        platforms = metadata.get('platforms')
        if platforms is not None and (not isinstance(platforms, list) or
                any(not isinstance(platform, dict) for platform in platforms)):
            raise ValueError('Malformed platform metadata; expected a list of objects')
        identifier = document.get('identifier', {}).get('url', '')
        if identifier and '/documentation/' not in identifier:
            raise ValueError('Unrecognized document identifier; cannot verify source identity')
        if '/documentation/' in identifier:
            actual = canonical_url(BASE + '/documentation/' + identifier.split('/documentation/', 1)[1])
            if actual != source_url:
                raise ValueError('Document identifier does not match requested source')
        renderer = Renderer(document)
        if not identifier:
            renderer.warn('Missing document identifier; source identity not independently confirmed')
        out = ['# ' + metadata['title']]
        if document.get('abstract'):
            out.append(renderer.inline(document['abstract']))
        declarations = []
        for section in document.get('primaryContentSections', []):
            kind = section.get('kind')
            if kind == 'declarations':
                out.append('## Declarations')
                for declaration in section.get('declarations', []):
                    declaration_text = ''.join(t.get('text', '') for t in declaration.get('tokens', []))
                    declarations.append({'text': declaration_text, 'languages': declaration.get('languages'), 'platforms': declaration.get('platforms')})
                    out.append(code_fence(declaration_text, 'swift' if 'swift' in declaration.get('languages', ['swift']) else ''))
            elif kind == 'content':
                out.append(renderer.blocks(section.get('content', [])))
            elif kind == 'parameters':
                out.append('## Parameters')
                for parameter in section.get('parameters', []):
                    out.extend(['### ' + parameter.get('name', 'unnamed'), renderer.blocks(parameter.get('content', []))])
            elif kind in ('returns', 'throws'):
                out.extend(['## ' + kind.title(), renderer.blocks(section.get('content', []))])
            elif kind == 'mentions':
                out.extend(['## Mentions', '\n'.join('- ' + renderer.reference(item) for item in section.get('mentions', []))])
            else:
                renderer.warn('Unsupported primary section: ' + str(kind))
        for group in document.get('topicSections', []) + document.get('seeAlsoSections', []):
            out.append('## ' + group.get('title', 'Related'))
            out.extend('- ' + renderer.reference(identifier) for identifier in group.get('identifiers', []))
        for special in ('variantOverrides', 'variants', 'deprecationSummary'):
            if document.get(special):
                renderer.warn(special + ' retained in raw JSON; not fully interpreted')
                if special == 'deprecationSummary':
                    out.extend(['## Deprecation', renderer.blocks(document[special])])
        renderer.warn('DocC subset renderer: full-document and visual fidelity have not been established')
        return {'markdown': '\n\n'.join(x for x in out if x).strip() + '\n',
                'metadata': {'title': metadata['title'], 'identifier': identifier or None,
                             'kind': document.get('kind'), 'role': metadata.get('role'),
                             'modules': metadata.get('modules'), 'platforms': metadata.get('platforms'),
                             'declarations': declarations, 'raw_metadata': metadata},
                'warnings': renderer.warnings, 'format': 'docc_json_subset'}
    heading = re.search(r'^#\s+(.+)$', text, re.M)
    if not heading or len(text) < 20 or 'text/html' in content_type.lower():
        raise ValueError('Response is not recognizable Markdown')
    return {'markdown': text + '\n', 'metadata': {'title': heading.group(1).strip(), 'identifier': None,
                'kind': None, 'role': None, 'modules': None, 'platforms': None, 'declarations': None},
            'warnings': ['Markdown received: availability and declarations were not structurally extracted',
                         'Markdown title alone does not independently confirm source identity or full-page completeness'],
            'format': 'markdown'}


def endpoint_candidates(url: str) -> list:
    canonical = canonical_url(url)
    path = urllib.parse.urlsplit(canonical).path
    return [BASE + '/tutorials/data' + path + '.json', canonical + '.md']


def validate_manifest(data: dict) -> list:
    if data.get('schema_version') != 1 or not isinstance(data.get('sources'), list):
        raise ValueError('Unsupported manifest schema')
    ids, urls = set(), set()
    for source in data['sources']:
        identifier = source.get('id', '')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', identifier):
            raise ValueError('Source id must be a safe filename identifier')
        canonical = canonical_url(source['url'])
        if identifier in ids or canonical in urls:
            raise ValueError('Duplicate source id or canonical URL')
        ids.add(identifier); urls.add(canonical)
    return data['sources']
