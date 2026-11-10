#!/usr/bin/env python3
"""Independent verifier for verify-88f5a1be/ (arena/88f5a1be-china2).

Recomputes every cost from the tariff formula, checks ledger schema,
citation coverage, blank-unverified policy, reconciliation parity, and
local links. Exits non-zero on any failure. Run:
  PYTHONDONTWRITEBYTECODE=1 python3 verify-88f5a1be/verify.py
"""
import csv
import json
import math
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RATE = 7.129
TIERS = list(range(10000, 400001, 10000))

failures = []
checks = 0


def ok(msg):
    global checks
    checks += 1
    print(f"  ok    {msg}")


def fail(msg):
    global checks
    checks += 1
    failures.append(msg)
    print(f"  FAIL  {msg}")


def hsbc_tt(amount_usd):
    cny = amount_usd * RATE
    return (min(max(0.001 * cny, 100.0), 500.0) + 120.0) / RATE


def quota_fee(amount_usd):
    n = math.ceil(amount_usd / 50000)
    total, remaining = 0.0, amount_usd
    for _ in range(n):
        t = min(50000, remaining)
        total += hsbc_tt(t)
        remaining -= t
    return total, n


print("[1] Ledger schema")
sources = json.loads((HERE / "sources.json").read_text())["sources"]
findings = json.loads((HERE / "findings.json").read_text())["findings"]
methods = json.loads((HERE / "methods.json").read_text())["methods"]
flags = json.loads((HERE / "flags.json").read_text())["flags"]
costs = json.loads((HERE / "costs.json").read_text())
SRC = {s["id"]: s for s in sources}
if len(sources) == 21:
    ok("21 sources")
else:
    fail(f"expected 21 sources, got {len(sources)}")
if len(findings) == 30:
    ok("30 findings")
else:
    fail(f"expected 30 findings, got {len(findings)}")
if len(methods) == 17:
    ok("17 methods")
else:
    fail(f"expected 17 methods, got {len(methods)}")
if len(flags) == 10:
    ok("10 flags")
else:
    fail(f"expected 10 flags, got {len(flags)}")
for s in sources:
    if not s.get("url", "").startswith("https://"):
        fail(f"source {s['id']} url not https")
    if s.get("status") not in ("fetched", "search-surfaced"):
        fail(f"source {s['id']} bad status {s.get('status')}")
ok("all source urls https + status valid")

print("[2] Citation coverage")
for f in findings:
    if f["status"] == "unverified-blank":
        if f["sources"]:
            fail(f"{f['id']} unverified-blank must have no sources")
        if f["value"]:
            fail(f"{f['id']} unverified-blank must have blank value")
    else:
        if not f["sources"]:
            fail(f"{f['id']} verified row has no sources")
        for sid in f["sources"]:
            if sid not in SRC:
                fail(f"{f['id']} cites unknown source {sid}")
ok("findings citation coverage checked")
for m in methods:
    if not m.get("sources"):
        fail(f"method {m['id']} has no sources")
ok("methods all sourced")

print("[3] Cost recomputation (independent)")
rows = costs["rows"]
if [r["amount_usd"] for r in rows] == TIERS:
    ok("40 tiers $10k-$400k in $10k steps")
else:
    fail("tier sequence wrong")
for r in rows:
    amt = r["amount_usd"]
    exp_m01 = round(hsbc_tt(amt), 2)
    if r["m01_fee_usd"] != exp_m01:
        fail(f"M01 fee {amt}: {r['m01_fee_usd']} != {exp_m01}")
    exp_m02, exp_n = quota_fee(amt)
    if r["m02_fee_usd"] != round(exp_m02, 2) or r["m02_wires"] != exp_n:
        fail(f"M02 fee {amt}: {r['m02_fee_usd']}/{r['m02_wires']} != {round(exp_m02,2)}/{exp_n}")
    if r["m06_years"] != math.ceil(amt * RATE / 100000):
        fail(f"M06 years {amt}")
    if r["m07_trips"] != math.ceil(amt / 5000):
        fail(f"M07 trips {amt}")
    if r["fine_standard_max_usd"] != round(0.30 * amt, 2):
        fail(f"fine std {amt}")
    if r["fine_serious_max_usd"] != round(1.00 * amt, 2):
        fail(f"fine serious {amt}")
    for k in ("m03_advance_fee_usd", "m04_fee_usd", "m05_fee_usd", "m06_fee_usd", "m08_fee_usd", "m09_fee_usd"):
        if r[k] is not None:
            fail(f"{k} must be blank (unpublished) at {amt}")
ok("all 40-tier recomputation matches (M01/M02/M06/M07/fines; unpublished blank)")

print("[4] Reconciliation parity")
rep = {}
with open(ROOT / "repatriate/exports/cost-ladders.csv", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["method"] == "M01":
            rep[int(r["amount_usd"])] = float(r["published_fee_usd"])
lad = {}
with open(ROOT / "ladder/data/costs.csv", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["route"] == "R01":
            lad[int(r["tier"])] = float(r["fixed_fee"])
for rec in costs["reconciliation"]:
    amt = rec["amount_usd"]
    if rec["repatriate"] != rep.get(amt):
        fail(f"recon repatriate {amt}")
    if abs(rec["ours"] - rep.get(amt, 0)) > 0.005:
        fail(f"ours vs repatriate {amt}: {rec['ours']} vs {rep.get(amt)}")
    # ladder differs only by reference rate: recompute at 7.1 directly
    if amt in lad:
        cny71 = amt * 7.1
        exp71 = (min(max(0.001 * cny71, 100.0), 500.0) + 120.0) / 7.1
        if abs(exp71 - lad[amt]) > 0.01:
            fail(f"ladder rate-explained {amt}: expected {exp71:.2f} vs {lad[amt]}")
ok("reconciliation: exact vs repatriate; rate-explained vs ladder")

print("[5] Exports parity")
csv_rows = list(csv.DictReader(open(HERE / "exports/costs.csv", newline="")))
json_rows = json.loads((HERE / "exports/costs.json").read_text())
if len(csv_rows) == 40 and len(json_rows) == 40:
    ok("exports 40 rows each")
else:
    fail(f"exports rows csv={len(csv_rows)} json={len(json_rows)}")
for a, b in zip(csv_rows, json_rows):
    if int(a["amount_usd"]) != b["amount_usd"] or float(a["m01_fee_usd"]) != b["m01_fee_usd"]:
        fail(f"export parity {a['amount_usd']}")
        break
else:
    ok("csv/json parity")

print("[6] HTML integrity")
PAGES = ["index.html", "findings.html", "costs.html", "methods.html", "penalties.html", "sources.html", "flagged.html"]


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if "id" in d:
            self.ids.add(d["id"])
        if tag == "a" and "href" in d:
            self.links.append(d["href"])


for name in PAGES:
    p = HERE / name
    if not p.exists():
        fail(f"missing page {name}")
        continue
    parser = P()
    parser.feed(p.read_text())
    if parser.h1 != 1:
        fail(f"{name} h1 count {parser.h1}")
    # every internal link resolves
    for href in parser.links:
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = href.split("#")[0]
        if target and not (HERE / target).exists() and not (ROOT / target).exists():
            # allow ../ links to repo files
            if not (HERE / target).resolve().exists():
                fail(f"{name} broken link {href}")
    ok(f"{name}: h1=1, links resolve")

# every findings row id has an anchor in findings.html
findings_html = (HERE / "findings.html").read_text()
for f in findings:
    if f'id="{f["id"]}"' not in findings_html and f'id={f["id"]}' not in findings_html:
        # ids are in table cells, not anchors; check id text present
        if f["id"] not in findings_html:
            fail(f"finding {f['id']} missing from findings.html")
ok("all finding ids present in findings.html")

print(f"\n{checks} checks, {len(failures)} failures")
sys.exit(1 if failures else 0)
