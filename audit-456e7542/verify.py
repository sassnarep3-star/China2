#!/usr/bin/env python3
"""Structural checks only; passing does not verify legal interpretation or live links."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent
HOSTS = {'www.safe.gov.cn', 'www.gov.cn', 'www.govinfo.gov', 'www.irs.gov', 'www.hsbc.com.cn'}

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.local = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            assert attrs['id'] not in self.ids
            self.ids.add(attrs['id'])
        if tag == 'tr':
            self.row = []
        if tag == 'a':
            href = attrs.get('href', '')
            if self.row is not None:
                self.row.append(href)
            parsed = urlsplit(href)
            if href and not parsed.scheme and not parsed.netloc and parsed.path:
                self.local.append(unquote(parsed.path))
    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None

parser = Audit()
parser.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
rows = parser.rows[1:]
assert len(rows) == 8, f'Expected 8 findings, found {len(rows)}'
for i, links in enumerate(rows, 1):
    assert any(urlsplit(link).scheme == 'https' and urlsplit(link).hostname in HOSTS for link in links), f'Row {i} has no primary source'
for path in parser.local:
    assert (ROOT / path).is_file(), f'Broken local file link: {path}'
print('PASS: 8 source-linked review rows and local file links; no claim of factual or external link validation')
