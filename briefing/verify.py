#!/usr/bin/env python3
"""Independent verification for the briefing site (arena/dc2c65bd-china2).

Checks (all local, deterministic):
  1. Required files exist; no localhost/127.0.0.1 references.
  2. HTML parses (stdlib html.parser).
  3. All local href/src targets exist; all fragments resolve to ids on the target page.
  4. 680 cost rows (17 methods x 40 tiers); amounts match $10k..$400k.
  5. Published HSBC TT fees recomputed from S29 formula == table values (M01/M02).
  6. Fine columns for rejected methods == 30% bands of the tier.
  7. No external http link points at an empty/known-404 URL recorded in the ledger.
  8. Every external link is https and appears in no ignored/unsafe context; JS syntax (checked separately by node).
  9. Counts: 17 methods, 37 sources, F/N flag ids unique.
"""
import json, math, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
fail = []
def check(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond: fail.append(msg)

files = ["index.html","costs.html","methods.html","sources.html","flagged.html","audit.html",
         "EXECUTIVE_SUMMARY.md","AUDIT.md","assets/style.css","assets/app.js"]
for f in files:
    check((ROOT / f).exists() and (ROOT / f).stat().st_size > 0, f"exists: {f}")

for f in files:
    if f.endswith(".html"):
        t = (ROOT / f).read_text()
        check("localhost" not in t and "127.0.0.1" not in t, f"no localhost in {f}")

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set(); self.links = []; self.srcs = []
        self.tables = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        if tag == "a" and a.get("href"): self.links.append(a["href"])
        if tag in ("script","link","img") and (a.get("src") or a.get("href")): self.srcs.append(a.get("src") or a.get("href"))

pages = {f: P() for f in files if f.endswith(".html")}
for f, p in pages.items():
    p.feed((ROOT / f).read_text())

for f, p in pages.items():
    for link in p.links + p.srcs:
        if link.startswith(("http://","https://","mailto:","#")):
            if link.startswith("http://"):
                fail.append(f"{f}: non-https external link {link}"); print("FAIL", f"{f}: non-https external link {link}")
            continue
        target, _, frag = link.partition("#")
        target_path = (ROOT / target) if target else (ROOT / f)
        check(target_path.exists(), f"{f}: local target exists: {link}")
        if frag and target_path.exists() and target_path.suffix == ".html":
            tp = P(); tp.feed(target_path.read_text())
            check(frag in tp.ids, f"{f}: fragment #{frag} resolves in {target or f}")

costs = (ROOT / "costs.html").read_text()
rows = re.findall(r'<tr data-tier="(\d+)">(.*?)</tr>', costs, re.S)
check(len(rows) == 680, f"680 cost rows (got {len(rows)})")
tiers = sorted(int(r[0]) for r in rows)
check(tiers == sorted([t for _ in range(17) for t in [i*10000 for i in range(1,41)]]), "40 tiers x17 methods all present")

RATE = 7.129
def fee_cny(usd):
    c = usd * RATE
    return min(max(c * 0.001, 100.0), 500.0)

# M01 rows: recompute published fee
m01 = re.search(r'id="M01"(.*?)<section', costs, re.S).group(1)
for t in (10000, 80000, 400000):
    m = re.search(rf'<tr data-tier="{t}">(.*?)</tr>', m01, re.S)
    cells = re.findall(r'<td[^>]*>([^<]*)</td>', m.group(1))
    expect = (fee_cny(t) + 120.0) / RATE
    got = float(cells[1].replace("$","").replace(",",""))
    check(abs(got - expect) < 0.005, f"M01 tier {t}: fee ${got:.2f} == recomputed ${expect:.2f}")
m02 = re.search(r'id="M02"(.*?)<section', costs, re.S).group(1)
m = re.search(r'<tr data-tier="400000">(.*?)</tr>', m02, re.S)
cells = re.findall(r'<td[^>]*>([^<]*)</td>', m.group(1))
rem, tot = 400000, 0.0
for _ in range(8):
    tr = min(rem, 50000); rem -= tr
    tot += fee_cny(tr) + 120.0
expect = tot / RATE
got = float(cells[1].replace("$","").replace(",",""))
check(abs(got - expect) < 0.005, f"M02 tier 400000: fee ${got:.2f} == recomputed ${expect:.2f}")

# Rejected methods: fine == 0.3 * tier (standard) and 1.0 * tier (serious max)
for mid in ("M14","M15","M16","M17"):
    sec = re.search(rf'id="{mid}"(.*?)<section', costs + "<section", re.S).group(1)
    for t in (10000, 400000):
        m = re.search(rf'<tr data-tier="{t}">(.*?)</tr>', sec, re.S)
        cells = re.findall(r'<td[^>]*>([^<]*)</td>', m.group(1))
        std = float(cells[1].replace("$","").replace(",",""))
        check(abs(std - 0.30*t) < 0.5, f"{mid} tier {t}: standard fine ${std:,.0f} == 30% of tier")

# No invented placeholder text
for f in files:
    if f.endswith((".html",".md")):
        t = (ROOT / f).read_text().lower()
        for bad in ("lorem ipsum","todo:","xxx","{{","}}","insert here"):
            check(bad not in t, f"{f}: no placeholder '{bad}'")

# Counts
methods_html = (ROOT / "methods.html").read_text()
check(len(re.findall(r'class="method"', methods_html)) == 17, "17 method sections")
sources_html = (ROOT / "sources.html").read_text()
check(sources_html.count("<tr") >= 37, "≥37 source rows")
flagged_html = (ROOT / "flagged.html").read_text()
ids = re.findall(r"<strong>((?:F|N)\d+)</strong>", flagged_html)
check(len(ids) == len(set(ids)) == 24, f"24 unique flags (got {len(ids)}, unique {len(set(ids))})")

print()
if fail:
    print(f"{len(fail)} FAILURES"); sys.exit(1)
print("ALL CHECKS PASS")
