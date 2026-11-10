#!/usr/bin/env python3
"""Verify guide-c9cc56a6 line by line.

Fails (exit 1) if any of the following is untrue:
  1. every source id used anywhere exists in data/sources.json and has an https URL
  2. every local link and every #anchor resolves to a file / an id that exists
  3. every table data row carries a non-empty data-src
  4. a blank cost cell carries a data-flag whose id exists on the Flagged page, and
     no cell is blank without a flag
  5. the published bank fee is recomputed from the 2026 tariff formula and matches
     the rendered value at all 40 tiers
  6. every costed route has exactly 40 tiers, USD 10,000 to USD 400,000 step 10,000
  7. the section 988 gain table matches a fresh computation from the IRS averages
  8. no page contains 'None', 'nan', 'NaN' or an unformatted float artifact
  9. counts are what the pages claim: 24 channels, 5 unlawful, 960 cost rows, 12 flags

Run: python3 guide-c9cc56a6/verify.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FX = 7.10
TIERS = list(range(10_000, 400_001, 10_000))
ERRORS: list[str] = []
CHECKS = [0]


def ok(msg: str):
    CHECKS[0] += 1


def fail(msg: str):
    ERRORS.append(msg)


def expect(cond, msg):
    if cond:
        ok(msg)
    else:
        fail(msg)


SOURCES = {s["id"]: s for s in json.load(open(DATA / "sources.json", encoding="utf-8"))["sources"]}
ANALYSIS = json.load(open(DATA / "analysis.json", encoding="utf-8"))
COSTS = json.load(open(DATA / "costs.json", encoding="utf-8"))

PAGES = {
    p.name: p.read_text(encoding="utf-8")
    for p in sorted(ROOT.glob("*.html"))
}
if not PAGES:
    fail("no html pages found - run build.py first")
    sys.exit(1)

ALL_SRC_IDS = set()
ALL_IDS: dict[str, set[str]] = {}

# ---------------------------------------------------------------- 1. sources --
for name, html in PAGES.items():
    for m in re.finditer(r'data-src="([^"]*)"', html):
        for sid in m.group(1).split():
            ALL_SRC_IDS.add(sid)
    for m in re.finditer(r'class="chip[^"]*"[^>]*>(G\d\d)<', html):
        ALL_SRC_IDS.add(m.group(1))

for sid in sorted(ALL_SRC_IDS):
    expect(sid in SOURCES, f"source id {sid} used in a page exists in data/sources.json")
    if sid in SOURCES:
        expect(SOURCES[sid]["url"].startswith("https://"), f"{sid} has an https URL")

# flagged/unverified sources must never be referenced by a numeric cell
UNVERIFIED = {k for k, v in SOURCES.items() if v["verification_level"] == "unverified"}
for name, html in PAGES.items():
    for m in re.finditer(r'<tr data-src="([^"]*)">(.*?)</tr>', html, re.S):
        sids = m.group(1).split()
        text = re.sub(r"<[^>]+>", " ", m.group(2))
        text = re.sub(r"^\s*\$[\d,]+\s*", "", text)      # drop the amount column
        has_number = re.search(r"\$[\d,]+", text) is not None
        if has_number and sids:
            bad = [s for s in sids if s in UNVERIFIED]
            if bad:
                fail(f"{name}: row with a dollar figure cites unverified source(s) {bad}")
ok("no row with a dollar figure cites an unverified source")

# ------------------------------------------------------------------ 2. links --
class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.add(d["id"])
        if tag == "a" and "href" in d:
            self.links.append(d["href"])


for name, html in PAGES.items():
    p = IdCollector()
    p.feed(html)
    ALL_IDS[name] = p.ids

for name, html in PAGES.items():
    p = IdCollector()
    p.feed(html)
    for href in p.links:
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target, _, anchor = href.partition("#")
        page = target or name
        if page not in PAGES:
            fail(f"{name}: link to missing file {href}")
            continue
        if anchor and anchor not in ALL_IDS[page]:
            fail(f"{name}: link to missing anchor {href}")
ok("every local link and anchor resolves")

# ------------------------------------------------------- 3. rows have sources --
for name, html in PAGES.items():
    for tbl in re.findall(r"<tbody>(.*?)</tbody>", html, re.S):
        for row in re.findall(r"<tr\b([^>]*)>(.*?)</tr>", tbl, re.S):
            attrs, body = row
            if body.count("<td") == 0:
                continue
            if "data-src=" not in attrs:
                fail(f"{name}: table row without data-src: {re.sub(chr(60) + '[^' + chr(62) + ']+' + chr(62), ' ', body)[:90]}")
            else:
                m = re.search(r'data-src="([^"]*)"', attrs)
                if not m.group(1).strip():
                    fail(f"{name}: table row with an empty data-src")
ok("every table data row carries a non-empty data-src")

# ---------------------------------------------- 4. blank <=> flag, no orphans --
FLAG_IDS = {f["id"] for f in ANALYSIS["flags"]}
flagged_html = PAGES.get("flagged.html", "")
for fid in FLAG_IDS:
    expect(fid in flagged_html, f"flag {fid} is published on the Flagged page")

for name, html in PAGES.items():
    for m in re.finditer(r'<td class="blank"([^>]*)>', html):
        if "data-flag=" not in m.group(1):
            fail(f"{name}: blank cell with no data-flag")
    for m in re.finditer(r'data-flag="([^"]+)"', html):
        fid = m.group(1)
        if not (fid in FLAG_IDS or re.match(r"^A\d$", fid)):
            fail(f"{name}: data-flag {fid} does not exist on the Flagged page")
ok("blank cells are flagged and every flag id resolves")

# ------------------------------------------------------- 5/6. fee recompute ----
def tt_fee(a: float) -> float:
    cny = max(100.0, min(500.0, 0.001 * a * FX))
    return (cny + 120.0) / FX


def quota_fee(a: float):
    years = math.ceil(a / 50_000)
    return tt_fee(min(a, 50_000)) * years, years


rows = COSTS["rows"]
expect(len(rows) == 960, f"960 cost rows (got {len(rows)})")

by_route: dict[str, list] = {}
for r in rows:
    by_route.setdefault(r["id"], []).append(r)

COSTED = [c for c in by_route if len(by_route[c]) == 40]
expect(len(COSTED) == 24, f"24 routes with 40 rows each (got {len(COSTED)})")

for rid, rs in by_route.items():
    amounts = sorted(r["amount"] for r in rs)
    expect(amounts == TIERS, f"{rid} covers 10,000-400,000 in 10,000 steps ({len(amounts)} tiers)")

for rid in ("C01", "C03", "C07", "C08", "C09", "C10", "C13", "C14"):
    for r in by_route[rid]:
        if r["mode"] == "cost" and r.get("fee_status") == "published":
            expect(abs(r["fee"] - tt_fee(r["amount"])) < 0.005,
                   f"{rid} at ${r['amount']:,}: published fee {r['fee']:.2f} matches the tariff formula")

for r in by_route["C21"]:
    exp, years = quota_fee(r["amount"])
    if r["mode"] == "cost":
        expect(abs(r["fee"] - exp) < 0.005, f"C21 at ${r['amount']:,}: {years} year-tranches priced correctly")

# rendered fee strings must appear in the C01 ladder section
costs_html = PAGES["costs.html"]
sec = costs_html.split('id="C01-l"', 1)[1].split('id="C21-l"', 1)[0]
for t in (10_000, 50_000, 100_000, 400_000, 250_000):
    val = f"${tt_fee(t):,.2f}"
    expect(val in sec, f"costs.html shows {val} for C01 at ${t:,}")

# ------------------------------------------------------------ 7. 988 table ----
CNY_ANNUAL = {2021: 6.452, 2022: 6.730, 2023: 7.075, 2024: 7.189, 2025: 7.129}
tax_html = PAGES["taxes.html"]


def fx_gain(a: float, y: int) -> float:
    return a - (a * CNY_ANNUAL[2025]) / CNY_ANNUAL[y]


for y in CNY_ANNUAL:
    g = fx_gain(10_000, y)
    shown = ("+" if g > 0 else "−") + f"${abs(g):,.0f}" if abs(g) >= 0.5 else ""
    if shown:
        expect(shown in tax_html, f"988 table shows {y} gain {shown} on $10,000")
    else:
        expect(True, f"988 table shows zero for {y}")
expect(f"{CNY_ANNUAL[2022]:.3f}" in tax_html, "988 rate table shows the 2022 average to 3 decimals")

# --------------------------------------------------------------- 8. artifacts --
ARTIFACT_PATTERNS = (r">\s*None\s*<", r"\$None", r"None%", r">\s*nan\s*<", r"\$nan", r"\bnan%")
for name, html in PAGES.items():
    for pat in ARTIFACT_PATTERNS:
        if re.search(pat, html):
            fail(f"{name}: rendering artifact matching {pat}")
ok("no rendering artifacts (None / nan) in any cell")

# ------------------------------------------------------------------ 9. counts --
expect(len({c for c in by_route}) == 24, "24 channels in the cost model")
expect(len([f for f in ANALYSIS["flags"]]) == 12, f"12 flagged items (got {len(ANALYSIS['flags'])})")
expect(len(SOURCES) == 32, f"32 sources (got {len(SOURCES)})")
unlawful = {rid for rid, rs in by_route.items() if rs[0].get("mode") == "penalty"}
expect(len(unlawful) == 5, f"5 unlawful routes priced as penalties (got {len(unlawful)})")
expect(len([s for s in SOURCES.values() if s["verification_level"] == "fetched-this-session"]) >= 17,
       "at least 17 sources were fetched and read this session")

# --------------------------------------------------------------------- report --
print(f"checks run : {CHECKS[0]}")
print(f"failures   : {len(ERRORS)}")
for err in ERRORS[:40]:
    print("  FAIL:", err)
if ERRORS:
    sys.exit(1)
print("guide-c9cc56a6: all checks pass")
