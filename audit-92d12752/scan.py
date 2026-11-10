#!/usr/bin/env python3
"""Static, direct-source-link inventory; counts are not legal verification."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json

ROOT = Path(__file__).resolve().parent.parent
# A deliberately finite list: government / primary providers present in the
# repository. Inclusion is domain classification only, not content validation.
HOSTS = ('safe.gov.cn','pbc.gov.cn','irs.gov','govinfo.gov','fincen.gov',
         'treasury.gov','ecfr.gov','hsbc.com.cn','chinatax.gov.cn','cbp.gov',
         'state.gov','wise.com','westernunion.com','boc.cn','bankofchina.com',
         'gov.cn','congress.gov','uscode.house.gov','federalregister.gov',
         'csrc.gov.cn','cftc.gov','justice.gov','federalreserve.gov',
         'consumerfinance.gov','finra.org','ustr.gov','imf.org','worldbank.org')
EXCLUDE = {'.git', 'node_modules', '.cache', 'audit-92d12752'}

def direct_primary(url):
    try:
        u = urlsplit(url)
        host = (u.hostname or '').lower().rstrip('.')
        return u.scheme in ('https','http') and any(host == x or host.endswith('.'+x) for x in HOSTS)
    except ValueError:
        return False

class Rows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = None
        self.rows = []
    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.active = {'td': False, 'links': [], 'text': []}
        elif self.active is not None:
            if tag == 'td': self.active['td'] = True
            if tag == 'a': self.active['links'].append(dict(attrs).get('href', ''))
    def handle_data(self, text):
        if self.active is not None: self.active['text'].append(text)
    def handle_endtag(self, tag):
        if tag == 'tr' and self.active is not None:
            if self.active['td']: self.rows.append(self.active)
            self.active = None

def scan():
    files = sorted(p for p in ROOT.rglob('*.html') if not EXCLUDE.intersection(p.relative_to(ROOT).parts))
    pages = []
    for path in files:
        parsed = Rows()
        parsed.feed(path.read_text(encoding='utf-8'))
        missing = [r for r in parsed.rows if not any(direct_primary(url) for url in r['links'])]
        pages.append({'path': path.relative_to(ROOT).as_posix(), 'rows': len(parsed.rows),
                      'without_direct_primary': len(missing),
                      'first_example': ' '.join(' '.join(missing[0]['text']).split())[:180] if missing else ''})
    return {'pages_scanned': len(pages), 'data_rows': sum(p['rows'] for p in pages),
            'without_direct_primary': sum(p['without_direct_primary'] for p in pages),
            'pages_with_candidates': sum(bool(p['without_direct_primary']) for p in pages),
            'pages': pages}

if __name__ == '__main__':
    result = scan()
    print(json.dumps(result, ensure_ascii=False, indent=2))
