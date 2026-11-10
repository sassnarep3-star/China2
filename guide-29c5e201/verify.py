#!/usr/bin/env python3
"""Structural/citation integrity checks for guide-29c5e201 (not legal verification)."""
from pathlib import Path
from urllib.parse import urlparse, unquote
from html.parser import HTMLParser
import csv, json, re, sys
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
class Links(HTMLParser):
 def __init__(self): super().__init__(); self.links=[]; self.ids=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'href' in a:self.links.append(a['href'])
  if 'id' in a:self.ids.add(a['id'])
errors=[]
def fail(msg): errors.append(msg)
sources=json.loads((ROOT/'data/sources.json').read_text())['sources']; srcmap={s['id']:s for s in sources}
methods=json.loads((ROOT/'data/methods.json').read_text())['methods']; methodmap={m['id']:m for m in methods}
rows=json.loads((ROOT/'data/costs.json').read_text())
expected_amounts=list(range(10000,400001,10000))
if len(methods)!=17: fail(f'expected 17 methods; found {len(methods)}')
if len(rows)!=680: fail(f'expected 680 cost rows; found {len(rows)}')
if len(sources)!=31: fail(f'expected 31 source records; found {len(sources)}')
for sid,s in srcmap.items():
 if not s.get('url','').startswith('https://'):fail(f'{sid} has no HTTPS source URL')
for mid,m in methodmap.items():
 group=[r for r in rows if r['method']==mid]
 amounts=[int(r['amount_usd']) for r in group]
 if amounts!=expected_amounts:fail(f'{mid} does not have ordered exact $10k-$400k tiers')
 if not m.get('sources'):fail(f'{mid} has no source IDs')
 for sid in m['sources']:
  if sid not in srcmap:fail(f'{mid} refers to missing source {sid}')
 for collection in ('pros','cons','steps'):
  for text in m.get(collection,[]):
   for sid in re.findall(r'\bS\d{2}\b',text):
    if sid not in srcmap:fail(f'{mid} has unknown citation {sid}')
for r in rows:
 if r['method'] not in methodmap:fail(f'unknown method in cost row {r}')
 if not r.get('sources'):fail(f'{r["method"]} ${r["amount_usd"]} row has no source')
 for sid in r['sources'].split(';'):
  if sid not in srcmap:fail(f'{r["method"]} row points to unknown source {sid}')
 for field in ('published_fee_usd','published_fee_cny','fine_standard_max_usd','fine_serious_min_usd','fine_serious_max_usd'):
  value=r.get(field,'')
  if value and not re.fullmatch(r'\d+(\.\d+)?',value):fail(f'non-numeric model value in {field}: {value}')
# Every generated page's local link/fragments must resolve within guide or repo.
htmlfiles=list(ROOT.glob('*.html'))+[REPO/'index.html']
parsed={}
for page in htmlfiles:
 parser=Links()
 try:parser.feed(page.read_text())
 except Exception as e:fail(f'cannot parse {page}: {e}')
 parsed[page.resolve()]=parser
for page,parser in parsed.items():
 for href in parser.links:
  if not href or href.startswith(('https://','http://','mailto:','tel:','javascript:')):continue
  url=urlparse(href); target=(page.parent/unquote(url.path)).resolve() if url.path else page
  if not target.exists():fail(f'broken local URL {page.relative_to(REPO)} -> {href}')
  if url.fragment and target.suffix.lower()=='.html' and target.resolve() in parsed:
   fragment=unquote(url.fragment)
   if fragment not in parsed[target.resolve()].ids:fail(f'broken fragment {page.relative_to(REPO)} -> {href}')
# Confirm landing page advertises the guide and guide has expected navigation/pages.
root_html=(REPO/'index.html').read_text()
if 'guide-29c5e201/index.html' not in root_html:fail('root dashboard does not link to the new guide')
for name in ['index.html','methods.html','costs.html','penalties.html','taxes.html','sources.html','flagged.html','verification.html']:
 if not (ROOT/name).exists():fail(f'missing dashboard page {name}')
if errors:
 print('\n'.join('FAIL '+x for x in errors));sys.exit(1)
print(f'PASS: {len(methods)} routes, {len(rows)} sourced cost rows ({len(expected_amounts)} tiers each), {len(sources)} HTTPS sources, local links/fragments across {len(htmlfiles)} pages; structural checks only, not factual/legal verification.')
