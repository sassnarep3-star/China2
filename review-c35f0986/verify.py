#!/usr/bin/env python3
"""Offline structural checks, not substantive legal verification."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
FILE = Path(__file__).resolve().parent / 'index.html'

class Check(HTMLParser):
    def __init__(self):
        super().__init__(); self.row = None; self.rows = []; self.links = []; self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, 'duplicate id: ' + a['id']
            self.ids.add(a['id'])
        if tag == 'tr': self.row = {'td': False, 'official': False}
        if tag == 'td' and self.row is not None: self.row['td'] = True
        if tag == 'a':
            href = a.get('href', ''); self.links.append(href)
            host = urlsplit(href).hostname or ''
            if self.row is not None and host in {'www.safe.gov.cn', 'www.irs.gov', 'www.boc.cn', 'www.abchina.com', 'fgk.chinatax.gov.cn'}:
                self.row['official'] = True
    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            if self.row['td']: self.rows.append(self.row)
            self.row = None

p = Check(); p.feed(FILE.read_text(encoding='utf-8'))
assert len(p.rows) >= 19 and all(r['official'] for r in p.rows), 'a data row is missing an official link'
for link in p.links:
    parts = urlsplit(link)
    if parts.scheme: assert parts.scheme == 'https', link; continue
    target = (FILE.parent / parts.path).resolve() if parts.path else FILE
    assert ROOT == target or ROOT in target.parents, link
    assert target.is_file(), f'broken local link: {link}'
    if parts.fragment and target == FILE: assert parts.fragment in p.ids, link
print(f'PASS: {len(p.rows)} cited rows; {len(p.links)} links; {len(p.ids)} anchors (offline structural check only)')
