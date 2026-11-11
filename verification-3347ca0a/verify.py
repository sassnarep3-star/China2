#!/usr/bin/env python3
"""
Independent checker for the final-integration pages.

Deliberately re-derives the money from the tariff text instead of trusting
build.py, and re-checks every rule the brief imposes:
  * every data row carries a direct official (https) source link;
  * anything not confirmed from an official source is blank or flagged;
  * every internal link and fragment resolves;
  * no personal tax conclusion, no "cheapest route" claim, no invented fee.

Run: python3 verification-3347ca0a/verify.py
Exit code 0 = all checks passed.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

failures = []
checks_run = 0


def check(cond, label):
    global checks_run
    checks_run += 1
    if not cond:
        failures.append(label)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# 1. Files exist and are well-formed enough for a browser
# ---------------------------------------------------------------------------
PAGES = {
    "root": os.path.join(ROOT, "index.html"),
    "verification": os.path.join(HERE, "index.html"),
    "irregularities": os.path.join(HERE, "irregularities.html"),
}
for name, path in PAGES.items():
    check(os.path.exists(path), f"{name}: file missing")
    if not os.path.exists(path):
        continue
    html = read(path)
    check(html.lstrip().lower().startswith("<!doctype html>"), f"{name}: missing doctype")
    check('<html lang="en">' in html, f"{name}: missing lang attribute")
    check('<meta name="viewport"' in html, f"{name}: missing viewport (mobile)")
    check("<title>" in html and "</title>" in html, f"{name}: missing title")
    check(html.count("<main") == 1, f"{name}: expected exactly one <main>")
    check(html.count("</html>") == 1, f"{name}: unbalanced </html>")

root = read(PAGES["root"])

# ---------------------------------------------------------------------------
# 2. Every data row has a direct official source link
#    Exception: tables explicitly marked class="nav-index" (navigational only).
# ---------------------------------------------------------------------------
OFFICIAL = ("https://")
ROW_WITH_TD = re.compile(r"<tr[^>]*>(?:(?!</tr>).)*?<td", re.S)


def tables(html):
    return re.findall(r"<table([^>]*)>(.*?)</table>", html, re.S)


for name, path in PAGES.items():
    html = read(path)
    rows_checked = 0
    exempt = 0
    for attrs, body in tables(html):
        nav = "nav-index" in attrs
        for row in re.findall(r"<tr[^>]*>.*?</tr>", body, re.S):
            if "<td" not in row and "<th" not in row:
                continue  # header row
            if "<thead" in body.split(row)[0][-200:] and "<td" not in row:
                continue
            if nav:
                exempt += 1
                continue
            has_official = any(u.startswith(OFFICIAL) for u in re.findall(r'href="([^"]+)"', row))
            rows_checked += 1
            check(has_official, f"{name}: row without an official https source -> {row[:120]}")
    check(rows_checked > 0, f"{name}: no data rows found (parser broke?)")
    print(f"  {name}: {rows_checked} data rows carry an official link, {exempt} navigational rows exempt")

# ---------------------------------------------------------------------------
# 3. No unverified value may be filled in
# ---------------------------------------------------------------------------
# The pages must never publish a number for these because no official document gives one.
FORBIDDEN_NUMBERS = [
    (r"intermediary[^<]{0,80}\$\s?[\d,]", "an intermediary/correspondent fee with a dollar figure"),
    (r"receiving bank[^<]{0,80}\$\s?[\d,]", "a receiving-bank fee with a dollar figure"),
    (r"all-in (cost|total)[^<]{0,40}\$\s?[\d,]", "an 'all-in' figure presented as exact"),
    (r"cheapest route is", "a 'cheapest route' claim"),
    (r"you will owe\s+\$", "a personal tax amount"),
    (r"guaranteed", "a guarantee claim"),
]
for name, path in PAGES.items():
    html = read(path)
    text = re.sub(r"<[^>]+>", " ", html)
    for pattern, label in FORBIDDEN_NUMBERS:
        hit = re.search(pattern, text, re.I)
        check(hit is None, f"{name}: contains {label} -> {hit.group(0)[:80] if hit else ''}")

# explicit blanks must exist where the value is unpublished
check("—" in read(PAGES["root"]) or "blank" in read(PAGES["root"]).lower(),
      "root: no blank marker anywhere (expected for unpublished fees)")
check("Not published" in read(PAGES["root"]) or "not published" in read(PAGES["root"]).lower(),
      "root: unpublished-fee statement missing")

# ---------------------------------------------------------------------------
# 4. Re-derive the money independently of build.py
# ---------------------------------------------------------------------------
RATE_BOC = 669.11 / 100.0
RATE_IRS = 7.129
BOARD_GAP = (669.11 - 666.30) / 669.11


def tt_fee_cny(cny):
    return min(max(cny * 0.001, 100.0), 500.0) + 120.0


ladder = json.loads(read(os.path.join(HERE, "data", "computed_ladder.json")))
check(len(ladder["tiers"]) == 5, "ladder: expected 5 milestone tiers")
for t in ladder["tiers"]:
    amount = t["amount"]
    cny = amount * RATE_BOC
    check(abs(t["cny"] - cny) < 0.51, f"ladder {amount}: CNY figure {t['cny']} != {cny:.2f}")
    fee = tt_fee_cny(cny) / RATE_BOC
    check(abs(t["fee_std"] - fee) < 0.005, f"ladder {amount}: fee {t['fee_std']} != {fee:.2f}")
    margin = amount * BOARD_GAP
    check(abs(t["margin"] - margin) < 0.005, f"ladder {amount}: margin {t['margin']} != {margin:.2f}")
    check(abs(t["total_std"] - (fee + margin)) < 0.01, f"ladder {amount}: total mismatch")
    check(t["atm_years"] == math.ceil(cny / 100000.0), f"ladder {amount}: ATM years mismatch")
    check(t["min_batches_50k"] == math.ceil(amount / 50000.0), f"ladder {amount}: 50k batches mismatch")

# the three published anchor values the tariff text implies
check(abs(tt_fee_cny(10000 * RATE_IRS) / RATE_IRS - 30.86) < 0.005, "tariff: CNY 220 at 7.129 != $30.86")
check(abs(tt_fee_cny(50000 * RATE_IRS) / RATE_IRS - 66.83) < 0.005, "tariff: 0.1% of 356,450 + 120 != $66.83")
check(abs(tt_fee_cny(400000 * RATE_IRS) / RATE_IRS - 86.97) < 0.005, "tariff: CNY 620 cap at 7.129 != $86.97")
check(abs(620 / RATE_BOC - 92.66) < 0.01, "tariff: CNY 620 at the BOC board != $92.66")
check(abs(220 / RATE_BOC - 32.88) < 0.01, "tariff: CNY 220 at the BOC board != $32.88")

# The page must state both rate bases, not silently mix them.
check(f"{RATE_BOC:.4f}" in root, "root: BOC board rate not stated")
check(str(RATE_IRS) in root, "root: IRS 2025 rate not stated")

# ---------------------------------------------------------------------------
# 5. Evidence ledger integrity
# ---------------------------------------------------------------------------
checks = json.loads(read(os.path.join(HERE, "data", "checks.json")))["checks"]
check(len(checks) >= 20, f"ledger: only {len(checks)} checks")
ids = [c["id"] for c in checks]
check(len(ids) == len(set(ids)), "ledger: duplicate ids")
for c in checks:
    check(c["url"].startswith("https://"), f"ledger {c['id']}: non-https source")
    check(c["status"] in ("VERIFIED", "NOT RE-CHECKED"), f"ledger {c['id']}: unknown status")
    if c["status"] == "VERIFIED":
        check(c["quote"] and c["quote"] != "—", f"ledger {c['id']}: VERIFIED without a quote")
        check(len(c["quote"]) > 40, f"ledger {c['id']}: quote too short to identify the sentence")
    else:
        check(c["quote"] in ("", "—") or len(c["quote"]) < 200,
              f"ledger {c['id']}: NOT RE-CHECKED should not carry a full quote")
    check(bool(c["limit"]), f"ledger {c['id']}: no stated limitation")

verification_html = read(PAGES["verification"])
for c in checks:
    check(f'id="{c["id"]}"' in verification_html, f"verification page: {c['id']} row missing")
    check(c["url"] in verification_html, f"verification page: {c['id']} source url missing")

# ---------------------------------------------------------------------------
# 6. Irregularities ledger
# ---------------------------------------------------------------------------
irr = json.loads(read(os.path.join(HERE, "data", "irregularities.json")))["findings"]
check(len(irr) >= 10, f"audit: only {len(irr)} findings")
irr_html = read(PAGES["irregularities"])
for f in irr:
    check(f'id="{f["id"]}"' in irr_html, f"audit page: {f['id']} missing")
    check(f["source"].startswith("https://"), f"audit {f['id']}: non-https source")
    check(f["severity"] in ("structure", "conflict", "stale", "gap", "resolved"),
          f"audit {f['id']}: unknown severity")

# ---------------------------------------------------------------------------
# 7. Internal links and fragments resolve
# ---------------------------------------------------------------------------
def resolve(base_dir, href):
    path = href.split("#")[0].split("?")[0]
    frag = href.split("#")[1] if "#" in href else None
    if not path:
        return os.path.abspath(os.path.join(base_dir, os.path.basename(base_dir) + ".html")) if frag else None, frag
    target = os.path.normpath(os.path.join(base_dir, path))
    return target, frag


for name, path in PAGES.items():
    html = read(path)
    base = os.path.dirname(path)
    for href in re.findall(r'(?:href|src)="([^"]+)"', html):
        if href.startswith(("http://", "https://", "mailto:", "data:", "javascript:", "#")):
            continue
        target, frag = resolve(base, href)
        if target is None:
            continue
        check(os.path.exists(target), f"{name}: broken link {href}")
        if frag and os.path.exists(target) and target.endswith(".html"):
            body = read(target)
            check(f'id="{frag}"' in body or f'name="{frag}"' in body,
                  f"{name}: missing fragment #{frag} in {href}")

# no plain-http external links anywhere on these pages
for name, path in PAGES.items():
    html = read(path)
    check('href="http://' not in html, f"{name}: contains an insecure external link")

# ---------------------------------------------------------------------------
# 8. Content requirements from the brief
# ---------------------------------------------------------------------------
must_have = [
    (r"\$10,000", "a $10,000 tier"),
    (r"\$400,000", "a $400,000 tier"),
    (r"Step by step|ol class=\"steps\"", "a step-by-step section"),
    (r"Flagged for review|flagged\.html", "a flagged-for-review route"),
    (r"transfer-guide/methods\.html", "the methods catalogue"),
    (r"transfer-guide/questions\.html", "the questions checklist"),
    (r"transfer-guide/sources\.html", "the source register"),
]
for pattern, label in must_have:
    check(re.search(pattern, root) is not None, f"root: missing {label}")

# every milestone tier appears as a headline row
for amount in (10000, 50000, 100000, 200000, 400000):
    check(f"${amount:,}.00" in root, f"root: tier ${amount:,} missing from the cost table")

# the 23 methods must all be listed
for mid in [f"M{i:02d}" for i in range(1, 24)]:
    check(f">{mid}<" in root, f"root: method {mid} missing")

print()
if failures:
    print(f"FAILED {len(failures)} of {checks_run} checks:")
    for f in failures[:40]:
        print("  -", f)
    sys.exit(1)
print(f"PASSED {checks_run} checks with 0 failures.")
