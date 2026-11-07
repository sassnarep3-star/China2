from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

class Check(HTMLParser):
 def __init__(self):
  super().__init__(); self.links=[]; self.in_body=False; self.in_row=False; self.rows=[]; self.row=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='tbody': self.in_body=True
  if tag=='tr' and self.in_body: self.in_row=True; self.row=[]
  if tag=='a' and 'href' in a:
   self.links.append(a['href'])
   if self.in_row: self.row.append(a['href'])
 def handle_endtag(self,tag):
  if tag=='tr' and self.in_row: self.rows.append(self.row); self.in_row=False
  if tag=='tbody': self.in_body=False
for path in Path('.').glob('*.html'):
 c=Check(); c.feed(path.read_text())
 for link in c.links:
  if not urlparse(link).scheme and not link.startswith('#'): assert (path.parent / link.split('#')[0]).exists(), (path,link)
 for row in c.rows:
  assert any(urlparse(x).hostname and (urlparse(x).hostname.endswith('.gov.cn') or urlparse(x).hostname.endswith('.irs.gov') or urlparse(x).hostname in ('www.irs.gov','www.cbp.gov','english.www.gov.cn')) for x in row), (path,row)
 print(path, len(c.rows), 'rows checked')
