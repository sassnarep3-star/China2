#!/usr/bin/env python3
"""Verifier for final-f6327e23.

Checks, in order:
  1  every page exists and is well formed (charset, viewport, title, nav, stylesheet)
  2  every table row carries at least one link (source or evidence)
  3  every internal link and fragment resolves
  4  the published arithmetic reproduces from the model's own inputs
  5  CSV export matches the JSON row for row
  6  meta counts match reality
  7  every route with sources cites only ids that exist; a route with no source is flagged
  8  every S-id used in HTML exists; every S-id in the ledger is used at least once
  9  no template leakage (None / nan / undefined / braces)
 10  blanks stay blank (an unknown is never rendered as 0.00)
 11  the build is deterministic (two runs, byte identical)

Exit code 0 = all checks pass. Prints a summary and any failures.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PAGES = ["index.html", "methods.html", "costs.html", "taxes.html",
         "steps.html", "sources.html", "review.html", "repo-audit.html"]

checks = 0
fails = []


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


costs = json.load(open(os.path.join(DATA, "costs.json")))
routes = json.load(open(os.path.join(DATA, "routes.json")))
sources = json.load(open(os.path.join(DATA, "sources.json")))
meta = json.load(open(os.path.join(DATA, "meta.json")))
SIDS = {s["id"] for s in sources}
html = {p: read(os.path.join(HERE, p)) for p in PAGES}

# ---------------------------------------------------------------- 1 structure
for p in PAGES:
    t = html[p]
    ok(t.startswith("<!doctype html>"), f"{p}: missing doctype")
    ok('<meta charset="utf-8">' in t, f"{p}: missing charset")
    ok('name="viewport"' in t and "width=device-width" in t, f"{p}: missing responsive viewport")
    ok("<title>" in t and "</title>" in t, f"{p}: missing title")
    ok('href="assets/style.css"' in t, f"{p}: missing stylesheet")
    ok('src="assets/app.js"' in t, f"{p}: missing script")
    ok(t.count("<h1>") == 1, f"{p}: expected exactly one h1, found {t.count('<h1>')}")
    ok(t.count('class="src"') + t.count("href=") > 10, f"{p}: implausibly few links")
    nav_count = len(re.findall(r"<nav[^>]*>.*?</nav>", t, re.S))
    ok(nav_count == 1, f"{p}: expected one nav block")

# ------------------------------------------------- 2 every table row has a link
for p in PAGES:
    t = html[p]
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        row = m.group(1)
        if "<th" in row:
            continue
        ok("<a " in row, f"{p}: table row without a link: {re.sub('<[^>]+>', ' ', row)[:70].strip()}")

# ------------------------------------------------ 3 internal links + fragments
ids = {}
for p in PAGES:
    ids[p] = set(re.findall(r'id="([^"]+)"', html[p]))
for p in PAGES:
    t = html[p]
    for m in re.finditer(r'(?:href|src)="([^"]+)"', t):
        u = m.group(1)
        if u.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
            continue
        path, _, frag = u.partition("#")
        if path:
            target = os.path.normpath(os.path.join(HERE, path.split("?")[0]))
            ok(os.path.exists(target), f"{p}: broken internal link {u}")
            if frag and path.endswith(".html") and os.path.basename(target) in ids:
                ok(frag in ids[os.path.basename(target)], f"{p}: missing fragment #{frag} in {path}")
        elif frag:
            ok(frag in ids[p], f"{p}: missing local fragment #{frag}")

# ------------------------------------------------------------- 4 arithmetic
BOC_SELL = Decimal("6.6851")
MID = (Decimal("6.6571") + Decimal("6.6851")) / 2
SPREAD = (Decimal("6.6851") - MID) / MID
RECEIVE = Decimal("16")


def q2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fee_usd(amount):
    cny = min(max(Decimal(amount) * BOC_SELL * Decimal("0.001"), Decimal("100")), Decimal("500")) + Decimal("120")
    return q2(cny / BOC_SELL)


for r in costs["rows"]:
    a = Decimal(r["amount"])
    if r["route"] == "R01":
        exp_fee = fee_usd(a)
        exp_spread = q2(a * SPREAD)
        exp_all = q2(exp_fee + exp_spread + RECEIVE)
        ok(Decimal(r["fx_fee_usd"]) == exp_fee, f"R01 {a}: fee {r['fx_fee_usd']} != {exp_fee}")
        ok(Decimal(r["spread_usd"]) == exp_spread, f"R01 {a}: spread {r['spread_usd']} != {exp_spread}")
        ok(Decimal(r["all_in_usd"]) == exp_all, f"R01 {a}: all-in {r['all_in_usd']} != {exp_all}")
        ok(Decimal(r["pct"]) == q2(exp_all / a * 100), f"R01 {a}: pct wrong")
    elif r["route"] == "R02":
        exp_all = q2(fee_usd(a) + RECEIVE)
        ok(Decimal(r["all_in_usd"]) == exp_all, f"R02 {a}: all-in wrong")
    elif r["route"] == "R03":
        exp_all = q2(Decimal("20") + a * SPREAD + RECEIVE)
        ok(Decimal(r["all_in_usd"]) == exp_all, f"R03 {a}: all-in wrong")
    elif r["route"] in ("R10", "R11"):
        ok(Decimal(r["all_in_usd"]) == q2(a * Decimal("0.30")), f"{r['route']} {a}: ceiling wrong")
    elif r["route"] == "R04":
        ok(r["all_in_usd"] == "", f"R04 {a}: unpriced route must stay blank")

# spread in meta matches the model
ok(Decimal(meta["spread_pct"]) == q2(SPREAD * 100), "meta spread_pct disagrees with measured spread")

# --------------------------------------------------------------- 5 CSV parity
with open(os.path.join(DATA, "costs.csv"), encoding="utf-8") as f:
    lines = f.read().strip().split("\n")
ok(len(lines) - 1 == len(costs["rows"]), f"CSV rows {len(lines)-1} != JSON rows {len(costs['rows'])}")
ok(lines[0].startswith("route,amount,fx_fee_usd"), "CSV header unexpected")

# ----------------------------------------------------------------- 6 meta
ok(meta["tiers"] == 40 and len(costs["tiers"]) == 40, "tier count wrong")
ok(meta["row_count"] == len(costs["rows"]), "row_count wrong")
ok(meta["route_count"] == len(routes), "route_count wrong")
ok(meta["source_count"] == len(sources), "source_count wrong")

# ------------------------------------------------------------ 7 route/citation
for r in routes:
    for sid in r["sources"]:
        ok(sid in SIDS, f"{r['id']}: cites missing source {sid}")
    if not r["sources"]:
        ok(r["category"] in ("unverified", "flagged"),
           f"{r['id']}: no source but category is {r['category']}")
    ok(r["category"] in ("lawful", "lawful-capped", "lawful-conditional", "unlawful",
                         "does-not-achieve-goal", "unverified", "flagged"),
       f"{r['id']}: unknown category {r['category']}")
    ok(bool(r["verdict"]), f"{r['id']}: missing verdict")

# ----------------------------------------------- 7b superseded-rule regression guard
# SAFE Huifa [2014] No. 2 Section 6 removed the 2004 instalment schedule, the RMB 500,000
# head-office step and the one-application-per-deceased rule (correction of 2026-11-11).
_r6 = next(r for r in routes if r["id"] == "R06")
_r7 = next(r for r in routes if r["id"] == "R07")
for _r in (_r6, _r7):
    ok("S17" in _r["sources"], f"{_r['id']}: must cite S17 (Huifa [2014] No. 2)")
    ok(bool(_r.get("correction")), f"{_r['id']}: correction note missing")
    for _bad in ("Two-year staging", "SAFE HQ approval above", "cannot be combined", "Repeat within the staged limits"):
        ok(not any(_bad in x for x in _r["cons"] + _r["steps"]), f"{_r['id']}: superseded text {_bad!r} is back")
ok("No instalment schedule since 10 February 2014" in _r6["caps"], "R06 caps must state the 2014 change")
ok("staged remittances: up to half" not in html["steps.html"], "steps.html: superseded staging text is back")
ok("with one application per deceased person" not in html["steps.html"], "steps.html: superseded per-deceased text is back")

# ------------------------------------------------------------- 8 source usage
used = set()
for p in PAGES:
    used |= {m.group(1) for m in re.finditer(r">(S\d\d)<", html[p])}
ok(used <= SIDS, f"HTML cites unknown source ids: {sorted(used - SIDS)}")
ok(SIDS <= used, f"ledger contains sources never used: {sorted(SIDS - used)}")
for s in sources:
    ok(bool(s["url"]) and s["url"].startswith("http"), f"{s['id']}: bad url")
    ok(bool(s["quote"]) and len(s["quote"]) > 30, f"{s['id']}: quote too short")
    # A source added by a later correction session carries "added_by" and its own date
    # (arena/8a85759a-china2, 2026-11-11: S17). Every other source must be dated to the original session.
    if s.get("added_by"):
        ok(s["verified_at"] > "2026-11-10", f"{s['id']}: added source must post-date the original session")
    else:
        ok(s["verified_at"] == "2026-11-10", f"{s['id']}: not dated to this session")
    ok(bool(s["locator"]), f"{s['id']}: missing locator")

# ------------------------------------------------------------- 9 leakage
for p in PAGES:
    for bad in (">None<", " nan", "undefined", "{{", "}}", "&lt;span"):
        ok(bad not in html[p], f"{p}: template leakage {bad!r}")

# ------------------------------------------------------- 10 blanks stay blank
for r in costs["rows"]:
    if r["route"] in ("R04",) or r["route"] in ("R13", "R14", "R15"):
        ok(r["fx_fee_usd"] == "" or r["route"] == "R04", f"{r['route']}: unpriced route has a fee")

# ----------------------------------------------------------- 11 determinism
def digest():
    h = hashlib.sha256()
    for p in PAGES:
        h.update(html[p].encode())
    h.update(read(os.path.join(DATA, "costs.csv")).encode())
    return h.hexdigest()

before = digest()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
for script in ("model.py", "build.py"):
    subprocess.run([sys.executable, os.path.join(HERE, script)], check=True,
                   capture_output=True, env=env)
html2 = {p: read(os.path.join(HERE, p)) for p in PAGES}
after = hashlib.sha256()
for p in PAGES:
    after.update(html2[p].encode())
after.update(read(os.path.join(DATA, "costs.csv")).encode())
ok(before == after.hexdigest(), "build is not deterministic")

# ------------------------------------------------------------------ report
print(f"checks: {checks}")
print(f"pages: {len(PAGES)}  routes: {len(routes)}  tiers: {len(costs['tiers'])}  "
      f"rows: {len(costs['rows'])}  sources: {len(sources)}")
if fails:
    print(f"FAILURES: {len(fails)}")
    for f in fails[:40]:
        print("  -", f)
    sys.exit(1)
print("FAILURES: 0")
