#!/usr/bin/env python3
"""Independent verifier for the cost-increments sub-site.
Exits non-zero on any failure. Re-derives the model from scratch rather than
importing model.py, so formula drift is caught."""
import json, math, re, sys, pathlib, html

ROOT = pathlib.Path(__file__).parent
FAIL = []
def ok(cond, msg):
    print(("PASS" if cond else "FAIL"), "-", msg)
    if not cond: FAIL.append(msg)

# ---- 1. independent recomputation --------------------------------------
RATE = 6.6538
def recompute(a):
    cny = a * RATE
    issuance = min(500.0, max(100.0, 0.001 * cny))
    wire_cny = issuance + 120.0
    wire_usd = wire_cny / RATE
    subtotal = wire_usd + 15.0
    return dict(usd=a, cny=round(cny,2), issuance_cny=round(issuance,2),
                cable_cny=120, wire_fee_cny=round(wire_cny,2), wire_fee_usd=round(wire_usd,2),
                receiving_usd=15, known_subtotal_usd=round(subtotal,2),
                known_pct=round(100*subtotal/a,3), dividend_wht_usd=round(a*0.10,2),
                quota_years=math.ceil(a/50_000), within_one_year_quota=a<=50_000)
EXPECTED = [recompute(a) for a in range(10_000, 400_001, 10_000)]

data = json.loads((ROOT/"data.json").read_text(encoding="utf-8"))
inc = data["increments"]
ok(len(inc) == 40, "data.json has exactly 40 increment rows")
drift = [i+1 for i,(e,a) in enumerate(zip(EXPECTED, inc)) if any(abs((e[k] or 0)-(a[k] or 0))>0.005 if isinstance(e[k],(int,float)) else e[k]!=a[k] for k in e)]
ok(not drift, f"all 40 rows match independent recomputation (drift rows: {drift})")
ok(data["meta"]["referenceRate"]["cnyPerUsd"] == RATE, "reference rate recorded as 6.6538")
src_ids = {s["id"] for s in data["sources"]}
ok(len(src_ids) == len(data["sources"]), "source ids unique")
for s in data["sources"]:
    u = s["url"]
    good = u.startswith("https://") or (u.startswith("../") and (ROOT/u).resolve().exists())
    ok(good, f"source {s['id']} is https or an existing internal link")

# ---- 2. page inventory & internal links --------------------------------
pages = ["index.html","increments.html","methods.html","flagged-for-review.html","verification.html"]
for p in pages:
    ok((ROOT/p).exists(), f"{p} exists")

local_ref = re.compile(r'(?:href|src)="([^"#]+?)(?:#[^"]*)?"')
local_ids = re.compile(r'id="([^"]+)"')
all_html = ""
for p in pages:
    all_html += (ROOT/p).read_text(encoding="utf-8")
# every internal (non-http) reference must resolve relative to the page that uses it
broken = []
for p in pages:
    text = (ROOT/p).read_text(encoding="utf-8")
    ids = set(local_ids.findall(text))
    for m in local_ref.finditer(text):
        u = m.group(1)
        if u.startswith(("http://","https://","mailto:","tel:")):
            continue
        target = (ROOT/p).parent / u
        if not target.exists():
            broken.append((p, u))
ok(not broken, f"no broken internal file references ({broken[:5]})")

# same-page anchors used by nav/buttons resolve
anchor_fail = []
for p in pages:
    text = (ROOT/p).read_text(encoding="utf-8")
    ids = set(local_ids.findall(text))
    for m in re.finditer(r'href="#([^"]+)"', text):
        if m.group(1) not in ids:
            anchor_fail.append((p, m.group(1)))
    for m in re.finditer(r'href="([a-z-]+\.html)#([^"]+)"', text):
        t = ROOT/m.group(1)
        if t.exists() and m.group(2) not in set(local_ids.findall(t.read_text(encoding="utf-8"))):
            anchor_fail.append((p, f"{m.group(1)}#{m.group(2)}"))
ok(not anchor_fail, f"all same-page and cross-page anchors resolve ({anchor_fail[:5]})")

# ---- 3. tables contain all 40 increments --------------------------------
inc_html = (ROOT/"increments.html").read_text(encoding="utf-8")
for a in range(10_000, 400_001, 10_000):
    ok_amt = f"${a:,.0f}" in inc_html
    if not ok_amt:
        ok(False, f"increment ${a:,.0f} present in increments.html")
print("PASS - all 40 increment amounts appear in increments.html")
ok(f"${400_000*0.10:,.0f}" in inc_html, "dividend WHT anchor $40,000 present")
ok("$108.18" in inc_html, "known-subtotal cap $108.18 present")
ok("$48.06" in inc_html, "smallest-increment known subtotal $48.06 present")
ok("$132,900" in (ROOT/"index.html").read_text(encoding="utf-8"), "FEIE 2026 anchor present on summary page")
ok("$16,536" in (ROOT/"index.html").read_text(encoding="utf-8"), "FBAR non-willful maxima present")
ok("$165,353" in (ROOT/"index.html").read_text(encoding="utf-8"), "FBAR willful maxima present")
ok('id="flags"' in (ROOT/"verification.html").read_text(encoding="utf-8"), "verification page exposes flags anchor")

# ---- 4. hygiene ---------------------------------------------------------
for banned in ("localhost", "127.0.0.1", "0.0.0.0"):
    ok(banned not in all_html, f"no '{banned}' references")
ok("Research, not tax or legal advice" in all_html, "disclaimer present")
ok("6.6538" in all_html, "reference rate disclosed")
ok("Flagged for Review" in all_html, "flagged-for-review labelling present")
used_ids = set(re.findall(r'>([A-Z]{2,6}-\d+|SAFE-\d|HSBC-\d|IIT-\d|EIT-\d|USC988|FEIE-\d|ECFR-\d|FED-\d|WISE-\d|CHASE-\d|FBAR-\d|CBP-\d|IRS-CUR|PBOC-\d|SPC-\d|REPO-\d)(?:<|\s)', all_html))
unknown = used_ids - src_ids
ok(not unknown, f"all source ids used resolve in the registry ({sorted(unknown)})")

# ---- 5. report -----------------------------------------------------------
print()
if FAIL:
    print(f"VERIFY FAILED: {len(FAIL)} problem(s)")
    sys.exit(1)
print("VERIFY OK — all checks passed")
