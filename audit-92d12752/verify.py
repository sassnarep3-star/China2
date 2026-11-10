#!/usr/bin/env python3
"""Test parser boundary conditions and snapshot reproducibility, not factual truth."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
from html.parser import HTMLParser
import sys
sys.dont_write_bytecode = True
from scan import Rows, direct_primary, scan

here=Path(__file__).resolve().parent
assert direct_primary('https://www.irs.gov/test')
assert not direct_primary('https://irs.gov.example.com/test')
assert not direct_primary('javascript:https://irs.gov')
assert not direct_primary('sources.html#S01')
p=Rows(); p.feed('<table><tr><th>Header</th></tr><tr><td>x <a href="https://www.irs.gov/a">IRS</a></td></tr><tr><td>blank</td></tr></table>')
assert len(p.rows)==2 and direct_primary(p.rows[0]['links'][0]) and not p.rows[1]['links']
old=json.loads((here/'results.json').read_text())
assert scan()==old, 'snapshot differs: rerun build.py after inspecting repository changes'
class Links(HTMLParser):
 def __init__(self): super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a': self.links.append(dict(attrs).get('href',''))
p=Links();p.feed((here/'index.html').read_text())
for href in p.links:
 u=urlsplit(href)
 if not u.scheme and u.path: assert (here / unquote(u.path)).is_file(), href
print('PASS: parser/domain boundaries, snapshot parity, local report links. Does not verify source substance.')
