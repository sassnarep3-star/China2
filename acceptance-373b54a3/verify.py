#!/usr/bin/env python3
"""Independent acceptance checks; does not mutate any prior-session output."""
from pathlib import Path
import csv, json, re, sys
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
checks = 0
failures = []

def check(ok, message):
    global checks
    checks += 1
    if not ok:
        failures.append(message)

# Published entry points and key review pages.
for rel in [
    "index.html", "ladder/index.html", "ladder/costs.html", "ladder/flagged.html",
    "repatriate/index.html", "repatriate/costs.html", "repatriate/flagged.html",
    "docs/index.html", "docs/review.html", "audit-86f0/index.html",
    "audit-0f0f59fe/index.html", "acceptance-373b54a3/index.html",
]:
    check((ROOT / rel).is_file(), f"missing required page: {rel}")

# Ladder completeness: exactly every USD 10,000 tier through USD 400,000 for every route.
ladder = json.loads((ROOT / "ladder/data/costs.json").read_text())
rows = ladder.get("rows", ladder.get("costs", []))
amount_key = "usd_amount" if rows and "usd_amount" in rows[0] else ("amount_usd" if rows and "amount_usd" in rows[0] else "tier")
route_key = "route_id" if rows and "route_id" in rows[0] else "route"
by_route = {}
for row in rows:
    by_route.setdefault(row[route_key], []).append(int(row[amount_key]))
expected = list(range(10_000, 400_001, 10_000))
check(len(rows) == 600, f"ladder row count is {len(rows)}, expected 600")
check(len(by_route) == 15, f"costed route count is {len(by_route)}, expected 15")
for route, amounts in by_route.items():
    check(sorted(amounts) == expected, f"incomplete increments for {route}")

# Repatriate export completeness: 17 methods x 40 tiers.
with (ROOT / "repatriate/exports/cost-ladders.csv").open(newline="", encoding="utf-8") as fh:
    rep = list(csv.DictReader(fh))
check(len(rep) == 680, f"repatriate row count is {len(rep)}, expected 680")

# Every local href in this acceptance page resolves; external links must be HTTPS.
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.hrefs=[]
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href: self.hrefs.append(href)
parser=Links(); parser.feed((ROOT/"acceptance-373b54a3/index.html").read_text())
for href in parser.hrefs:
    if href.startswith("http"):
        check(href.startswith("https://"), f"non-HTTPS external link: {href}")
    elif not href.startswith("#"):
        check((ROOT/"acceptance-373b54a3"/href.split("#")[0]).resolve().exists(), f"broken local link: {href}")

if failures:
    print(f"FAIL: {checks} checks, {len(failures)} failures")
    print("\n".join(f"- {x}" for x in failures))
    sys.exit(1)
print(f"PASS: {checks} independent acceptance checks; 600-row and 680-row ladders complete; required pages and report links resolve.")
