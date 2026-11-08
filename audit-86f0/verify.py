from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import csv, subprocess
R=Path(__file__).resolve().parent
class P(HTMLParser):
 def __init__(self):
  super().__init__(); self.links=[];self.ids=set();self.rows=[];self.row=None;self.main=0
 def handle_starttag(self,t,a):
  d=dict(a)
  if 'id' in d:self.ids.add(d['id'])
  if t=='main':self.main+=1
  if t=='tr':self.row=[]
  if 'href' in d:
   self.links.append(d['href'])
   if self.row is not None:self.row.append(d['href'])
 def handle_endtag(self,t):
  if t=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
pages={}
for p in R.parent.rglob('*.html'):
 if '.git' in p.parts:continue
 x=P();x.feed(p.read_text());pages[p.resolve()]=x
for p,x in pages.items():
 if p.parent!=R:continue
 assert x.main==1
 for href in x.links:
  u=urlsplit(href)
  if u.scheme or u.netloc:continue
  target=(p.parent/unquote(u.path)).resolve() if u.path else p
  assert target.is_file(), (p,href)
  if u.fragment and target.suffix=='.html':assert unquote(u.fragment) in pages[target].ids,(p,href)
 for row in x.rows:
  if row:assert any(urlsplit(h).hostname for h in row),(p,row)
with (R/'cost-matrix.csv').open() as f:rows=list(csv.DictReader(f))
assert len(rows)==880
for k in {r['route_id'] for r in rows}:
 part=[r for r in rows if r['route_id']==k];assert [int(r['target_usd']) for r in part]==list(range(10000,400001,10000))
 for r in part:
  assert all(not r[f] for f in ['fx_spread_usd','transfer_fees_usd','tax_and_penalties_usd','total_cost_usd'])
  assert urlsplit(r['source_context_url']).scheme=='https'
print('PASS: 4 pages, 22 × 40 cost rows, blank unverified figures, row source context, all local links and anchors. Source context is not verification of costs.')
