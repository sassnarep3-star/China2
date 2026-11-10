#!/usr/bin/env python3
"""Structural checks for the targeted review; not a legal or live-link audit."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent

class Check(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []
        self.in_body = False
        self.row = None
        self.rows = []
        self.h1 = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'tbody':
            self.in_body = True
        if tag == 'tr' and self.in_body:
            self.row = []
        if tag == 'a' and 'href' in attrs:
            href = attrs['href']
            self.hrefs.append(href)
            if self.row is not None:
                self.row.append(href)
    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == 'tbody':
            self.in_body = False

p = Check()
p.feed((HERE / 'index.html').read_text())
assert p.h1 == 1
assert len(p.rows) == 9
for row in p.rows:
    assert any(urlsplit(h).hostname and (urlsplit(h).hostname.endswith('.gov') or urlsplit(h).hostname.endswith('.gov.cn') or urlsplit(h).hostname == 'www.hsbc.com.cn') for h in row), row
for href in p.hrefs:
    u = urlsplit(href)
    if u.scheme:
        assert u.scheme == 'https'
    elif u.path:
        assert (HERE / u.path).resolve().is_file(), href
    elif u.fragment:
        assert u.fragment in p.ids, href
print('PASS: 9 source-linked rows and local links; external availability and factual accuracy not automatically checked')
