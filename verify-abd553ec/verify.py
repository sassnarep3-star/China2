#!/usr/bin/env python3
"""Structural checks for verify-abd553ec/index.html.

Checks: required sections present; every local href/src resolves on disk;
fragments resolve; external links use HTTPS; no placeholder markers; tables
are wrapped for horizontal scroll on small screens; every data row in the two
results tables links somewhere (local or https). Does not verify external
availability or legal substance.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser
import re, sys
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
html_text = (HERE / "index.html").read_text(encoding="utf-8")
failures = []

def check(cond, msg):
    if cond:
        print(f"PASS  {msg}")
    else:
        failures.append(msg)
        print(f"FAIL  {msg}")

for marker in ["Most important, first", "Requirement coverage map", "re-fetched live on 2026-11-11",
               "Test suites re-run", "landing-hub integration", "Still unresolved", "Method &amp; limitations"]:
    check(marker in html_text, f"section present: {marker!r}")

check("TODO" not in html_text and "PLACEHOLDER" not in html_text and "__" not in html_text, "no placeholder markers")
check(html_text.count("<table") == html_text.count("</table>"), "table tags balanced")
check(html_text.count('class="table-wrap"') == html_text.count("<table"), "every table wrapped in .table-wrap")

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids = [], set()
        self.row_links, self.row_text, self.rows_done = 0, [], []
        self.cur_td_text, self.in_td, self.first_cell, self.row_has_td = "", False, "", False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        if tag == "tr": self.row_links, self.first_cell, self.row_has_td = 0, "", False
        if tag == "td":
            self.in_td, self.cur_td_text, self.row_has_td = True, "", True
        if tag == "a" and a.get("href"):
            self.links.append(a["href"]); self.row_links += 1
    def handle_data(self, data):
        if self.in_td: self.cur_td_text += data
    def handle_endtag(self, tag):
        if tag == "td":
            if not self.first_cell.strip(): self.first_cell = self.cur_td_text
            self.in_td = False
        if tag == "tr":
            self.rows_done.append((self.first_cell.strip(), self.row_links, self.row_has_td))

p = P(); p.feed(html_text)

local_ok = 0
for href in p.links:
    u = urlsplit(href)
    if u.scheme in ("http", "https"):
        check(u.scheme == "https", f"https external link: {href[:80]}")
        local_ok += 1
        continue
    if href.startswith("mailto:") or href.startswith("#"):
        if href.startswith("#"):
            check(href[1:] in p.ids, f"fragment resolves: {href}")
        continue
    target, _, frag = href.partition("#")
    path = (ROOT / unquote(target)) if target.startswith("/") else (HERE / unquote(target))
    check(path.exists(), f"local link resolves: {href}")
    if path.exists() and frag:
        body = path.read_text(encoding="utf-8", errors="ignore") if path.suffix in (".html", ".md", ".csv", ".json") else ""
        ids = set(re.findall(r'id="([^"]+)"', body)) | set(re.findall(r'name="([^"]+)"', body))
        if path.suffix != ".md":
            check(frag in ids, f"fragment {frag!r} found in {path.name}")
    local_ok += 1
print(f"INFO  {len(p.links)} links checked")

key_rows = [(first, n) for first, n, has_td in p.rows_done if has_td and re.match(r"^(S|U)-\d", first)]
linked_key = sum(1 for _, n in key_rows if n > 0)
check(linked_key == len(key_rows), f"every source/open-item row links out ({linked_key}/{len(key_rows)})")
print(f"INFO  {sum(1 for _, _, has_td in p.rows_done if has_td)} data rows total")

print()
if failures:
    print(f"FAILURES: {len(failures)}")
    sys.exit(1)
print(f"ALL CHECKS PASS ({len(p.links)} links)")
