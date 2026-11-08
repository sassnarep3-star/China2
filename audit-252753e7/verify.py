"""Structural checks only; citation relevance still requires human source review."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import re

root = Path(__file__).resolve().parent
class Check(HTMLParser):
    def __init__(self):
        super().__init__(); self.hrefs=[]; self.ids=set(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.add(a['id'])
        if tag=='a': self.hrefs.append(a.get('href',''))
        if tag=='tr': self.row={'sources': [], 'cells': []}
        if self.row is not None and tag=='td': self.cell=''; self.row['cells'].append('')
        if self.row is not None and tag=='a': self.row['sources'].append(a.get('href',''))
    def handle_data(self, data):
        if self.row is not None and self.cell is not None:
            self.row['cells'][-1]+=data
    def handle_endtag(self, tag):
        if tag=='td': self.cell=None
        if tag=='tr' and self.row is not None:
            if self.row['cells']: self.rows.append(self.row)
            self.row=None
p=Check(); p.feed((root/'index.html').read_text())
assert len(p.rows)==47, len(p.rows)
for row in p.rows:
    assert any(urlparse(x).hostname in {'www.pbc.gov.cn','www.safe.gov.cn','www.irs.gov','www.govinfo.gov'} for x in row['sources']), row
for i,row in enumerate(p.rows[-40:],1):
    assert row['cells'][0]==f'${i*10000:,}' and row['cells'][1:3]==['',''], row
for href in p.hrefs:
    u=urlparse(href)
    if u.scheme: continue
    if not u.path: assert u.fragment in p.ids, href; continue
    target=(root/unquote(u.path)).resolve()
    if target.is_dir(): target=target/'index.html'
    assert target.exists(), href
assert (root/'style.css').exists()
print('PASS: 47 rows, official reference in each, 40 blank cost rows, local links and anchors. Not a fact-check.')
