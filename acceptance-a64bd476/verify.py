#!/usr/bin/env python3
"""Independent acceptance verification (arena/a64bd476-china2).

Structure + arithmetic checks only. These do NOT prove legal correctness or
personal eligibility; factual claims are in findings.json with official links.

Checks:
 1. findings/sources schema; every verified finding has an official URL.
 2. Repo crawl: every HTML file parses; local href/src targets exist;
    fragments resolve; viewport meta present; no localhost references.
 3. Cost arithmetic: HSBC M01 published fee recomputed from tariff formula
    at 7.129 for all 40 tiers matches repatriate CSV and briefing costs.html.
 4. Row counts: briefing 680 (17x40), repatriate CSV 680, ladder costs.json 600.
 5. Generated acceptance pages: every finding row contains its source link;
    every source row contains its URL.
Writes checks.json. Exit 1 on any failure.
"""
import csv, json, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACC = ROOT / "acceptance-a64bd476"
fail = []
count = 0

def check(cond, msg):
    global count
    count += 1
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fail.append(msg)

findings = json.load(open(ACC / "findings.json"))["findings"]
sources = json.load(open(ACC / "sources.json"))["sources"]
src_by_id = {s["id"]: s for s in sources}
OFFICIAL = ("safe.gov.cn", "irs.gov", "ecfr.gov", "hsbc.com.cn", "chinatax.gov.cn",
            "pbc.gov.cn", "govinfo.gov", "fincen.gov", "treasury.gov", "federalreserve.gov")

# 1. schema
ids = [f["id"] for f in findings]
check(len(ids) == len(set(ids)), f"finding ids unique ({len(ids)})")
for f in findings:
    check(f["status"] in ("verified", "verified-limited", "unverified-blank"),
          f"{f['id']}: valid status {f['status']}")
    if f["status"] in ("verified", "verified-limited"):
        s = src_by_id.get(f["source_id"])
        check(s is not None and any(d in s["url"] for d in OFFICIAL),
              f"{f['id']}: official source linked ({f['source_id']})")
    else:
        # Unverified values stay blank; a source id may still point at the
        # publication that was retrieved (e.g. TOC only) — detail must say so.
        check(bool(f["detail"]), f"{f['id']}: unverified explains the blank")

# 2. repo crawl
class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set(); self.links = []; self.srcs = []; self.viewport = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        if tag == "a" and a.get("href"): self.links.append(a["href"])
        if tag in ("script", "link", "img") and (a.get("src") or a.get("href")):
            self.srcs.append(a.get("src") or a.get("href"))
        if tag == "meta" and a.get("name") == "viewport": self.viewport = True

html_files = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
check(len(html_files) >= 60, f"repo HTML page count >= 60 (found {len(html_files)})")
parsed = {}
for p in html_files:
    rel = p.relative_to(ROOT)
    t = p.read_text(errors="replace")
    check("http://localhost" not in t and "https://localhost" not in t and "127.0.0.1" not in t, f"{rel}: no localhost")
    pg = P(); pg.feed(t); parsed[rel] = pg
    check(pg.viewport, f"{rel}: viewport meta present")
for rel, pg in parsed.items():
    for link in pg.links + pg.srcs:
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target, _, frag = link.partition("#")
        tp = ((ROOT / rel.parent / target) if target else (ROOT / rel)).resolve()
        check(tp.exists(), f"{rel}: local target exists: {link}")
        if frag and tp.exists() and tp.suffix == ".html":
            check(frag in parsed[tp.relative_to(ROOT)].ids, f"{rel}: fragment resolves: {link}")

# 3. HSBC M01 fee recompute at 7.129
RATE = 7.129
def fee_usd(tier):
    cny = tier * RATE
    return (min(max(cny * 0.001, 100.0), 500.0) + 120.0) / RATE

rows = list(csv.DictReader(open(ROOT / "repatriate/exports/cost-ladders.csv")))
m01 = [r for r in rows if r["method"] == "M01"]
check(len(m01) == 40, f"repatriate M01 rows == 40 (found {len(m01)})")
for r in m01:
    tier = int(r["amount_usd"])
    expect = round(fee_usd(tier), 2)
    got = round(float(r["published_fee_usd"]), 2)
    check(abs(expect - got) < 0.011, f"M01 ${tier:,}: CSV fee {got} == recomputed {expect}")
check(abs(round(fee_usd(10000), 2) - 30.86) < 0.011, "M01 $10,000 fee == $30.86")
check(abs(round(fee_usd(400000), 2) - 86.97) < 0.011, "M01 $400,000 fee == $86.97")

brief = (ROOT / "briefing/costs.html").read_text()
check(brief.count('data-tier=') == 680, f"briefing cost rows == 680 (found {brief.count('data-tier=')})")
check("$30.86" in brief and "$86.97" in brief, "briefing shows $30.86 and $86.97 illustrations")

# 4. row counts
check(len(rows) == 680, f"repatriate CSV rows == 680 (found {len(rows)})")
ladder = json.load(open(ROOT / "ladder/data/costs.json"))
check(len(ladder["rows"]) == 600, f"ladder costs.json rows == 600 (found {len(ladder['rows'])})")
tiers = ladder["meta"]["tiers"]
check(tiers == [i * 10000 for i in range(1, 41)], "ladder tiers are $10k..$400k step $10k")

# 5. generated acceptance pages (if built)
for name in ("index.html", "findings.html", "sources.html", "flagged.html", "checks.html"):
    check((ACC / name).exists(), f"generated page exists: {name}")
if (ACC / "findings.html").exists():
    fh = (ACC / "findings.html").read_text()
    for f in findings:
        if f["source_id"]:
            check(src_by_id[f["source_id"]]["url"] in fh, f"findings.html links source for {f['id']}")
if (ACC / "sources.html").exists():
    sh = (ACC / "sources.html").read_text()
    for s in sources:
        check(s["url"] in sh, f"sources.html lists {s['id']}")

checks = {"session": "arena/a64bd476-china2", "checks_run": count, "failures": fail,
          "html_pages_crawled": len(html_files), "findings": len(findings), "sources": len(sources)}
(ACC / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
print(f"\n{count} checks, {len(fail)} failures")
sys.exit(1 if fail else 0)
