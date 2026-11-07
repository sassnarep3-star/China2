#!/usr/bin/env python3
"""Check local site links/anchors, citation coverage, ledger integrity and artifact parity.
Does not claim continuous external URL health or individualized legal verification.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, csv, io

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'
ALLOWED={'www.pbc.gov.cn','www.safe.gov.cn','www.hsbc.com.cn','wise.com','czj.gz.gov.cn','www.irs.gov','www.govinfo.gov','www.cbp.gov'}
S=json.loads((ROOT/'research/sources.json').read_text())
R=json.loads((ROOT/'research/findings.json').read_text())
assert len({s['id'] for s in S})==len(S)
assert len({r['id'] for r in R})==len(R)
sources={s['id']:s for s in S}
urls={s['url'] for s in S}
for s in S:
    assert urlsplit(s['url']).scheme=='https'
    assert urlsplit(s['url']).hostname in ALLOWED
    assert all(s[k] for k in ['evidence','locator','accessed','method','limitation'])
for r in R:
    assert r['sources'] and all(i in sources for i in r['sources'])
    assert r['status'] in ['Source-backed','Analysis','Unverified','Needs review','Do not use']
    assert r['locator'] and r['finding'] and r['topic']
    assert isinstance(r['value'],str)
    if r['status']=='Unverified': assert r['value']==''
for name in ['sources','findings']:
    assert (ROOT/f'research/{name}.json').read_bytes()==(OUT/f'data/{name}.json').read_bytes()
assert (ROOT/'research/EXECUTIVE_SUMMARY.md').read_bytes()==(OUT/'executive-summary.md').read_bytes()
assert len(list(csv.DictReader(io.StringIO((OUT/'findings.csv').read_text()))))==len(R)

class Page(HTMLParser):
    def __init__(self,path):
        super().__init__(convert_charrefs=True)
        self.path=path; self.ids=set();self.links=[];self.rows=[];self.row=None;self.inbody=False;self.h1=0;self.lang='';self.navcurrent=0
        self.feed(path.read_text())
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, f'duplicate id {self.path}: {a["id"]}'
            self.ids.add(a['id'])
        if tag=='html': self.lang=a.get('lang')
        if tag=='h1':self.h1+=1
        if a.get('aria-current')=='page': self.navcurrent+=1
        if tag=='tbody':self.inbody=True
        if tag=='tr' and self.inbody:self.row=[]
        for key in ['href','src']:
            if key in a:
                self.links.append(a[key])
                if self.row is not None:self.row.append(a[key])
    def handle_endtag(self,tag):
        if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
        if tag=='tbody':self.inbody=False

pages={p.resolve():Page(p) for p in OUT.glob('*.html')}
for path,p in pages.items():
    assert p.h1==1 and p.lang=='en' and p.navcurrent==1, f'page structure {path}'
    for row in p.rows:
        assert any(link in urls for link in row), f'unsourced table row: {path}'
    for link in p.links:
        u=urlsplit(link)
        if u.scheme in ['https','http','tel','mailto','data']:continue
        target=(path.parent/unquote(u.path)).resolve() if u.path else path
        assert target.is_relative_to(OUT.resolve()), f'link escapes site: {link}'
        assert target.is_file(), f'broken local link {path}: {link}'
        if u.fragment and target.suffix=='.html':
            assert target in pages and unquote(u.fragment) in pages[target].ids, f'broken anchor {link}'
for r in R:
    assert r['id'] in pages[(OUT/f'{r["category"]}.html').resolve()].ids
assert len([r for r in R if r['category']=='review'])==9
assert len([r for r in R if r['category']=='routes'])==22
assert len(pages)==7
print(f'PASS: {len(pages)} pages; {len(R)} findings; {len(S)} sources; every table body row has an official link; all local links/anchors resolve; downloads match canonical data.')
print('External source bodies were reviewed during research; external URL availability and current law are not continuously tested by this script.')
