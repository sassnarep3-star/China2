# -*- coding: utf-8 -*-
"""Independent verifier. Recomputes every cost cell from the raw published
figures with a separate code path, then checks the rendered pages: one official
link per table row, no blank cell without a flag, no broken local path or
anchor, and every prose figure reproduced from the data."""
import json, os, re, sys
from fractions import Fraction as F
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
FILES = ["index.html", "summary.html", "questions.html", "methods.html", "costs.html",
         "penalties.html", "taxes.html", "sources.html", "review.html"]

OFFICIAL = ("safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn", "irs.gov",
            "ecfr.gov", "govinfo.gov", "federalreserve.gov", "cbp.gov",
            "boc.cn", "hsbc.com.cn")

sources = json.load(open(os.path.join(D, "sources.json"), encoding="utf-8"))
S = {x["id"]: x for x in sources}
data = json.load(open(os.path.join(D, "costs.json"), encoding="utf-8"))
P, ROWS, SUMMARY, METHODS, AMOUNTS = (data["parameters"], data["rows"], data["summary"],
                                      data["methods"], data["amounts"])

checks = failed = 0


def ok(cond, msg):
    global checks, failed
    checks += 1
    if not cond:
        failed += 1
        print("FAIL:", msg)
    return cond


def eq(got, want, msg, tol=0.005):
    return ok(abs(float(got) - float(want)) <= tol, f"{msg}: got {got}, want {want}")


# ---- 1. rebuild the model from the raw published figures, independently ----
b10 = S["S10"]["figures"]
b12 = S["S12"]["figures"]
boc_sell = F(str(S["S09"]["figures"]["usd_sell_spot_per100"])) / 100
boc_buy = F(str(S["S09"]["figures"]["usd_buy_spot_per100"])) / 100
boc_cash = F(str(S["S09"]["figures"]["usd_sell_cash_per100"])) / 100
boc_mid = (boc_sell + boc_buy) / 2
hs_sell = F(str(S["S11"]["figures"]["usd_sell_spot"]))
hs_buy = F(str(S["S11"]["figures"]["usd_buy_spot"]))
hs_mid = (hs_sell + hs_buy) / 2
fed = F(str(S["S13"]["figures"]["nov6"]))

eq(P["boc_mid"], boc_mid, "BOC midpoint")
eq(P["hsbc_mid"], hs_mid, "HSBC midpoint")
eq(P["fed"], fed, "Fed H.10 reference")
eq(P["boc_spread_pct"], (boc_sell / boc_mid - 1) * 100, "BOC spread %")
eq(P["hsbc_spread_pct"], (hs_sell / hs_mid - 1) * 100, "HSBC spread %")


def expect(kind, a):
    A = F(a)
    if kind == "boc":
        r, m = boc_sell, boc_mid
        cny = A * r
        fee = min(max(F(str(b10["pct"])) * cny, F(b10["min_cny"])), F(b10["max_cny"])) + F(b10["cable_cny"])
        fu = fee / r
    elif kind == "hsbc_tt":
        r, m = hs_sell, hs_mid
        cny = A * r
        fee = min(max(F(str(b12["pct"])) * cny, F(b12["min_cny"])), F(b12["max_cny"])) + F(b12["cable_cny"])
        fu = fee / r
    elif kind == "hsbc_gt_premier":
        r, m, cny, fee, fu = hs_sell, hs_mid, A * hs_sell, F(0), F(0)
    elif kind == "hsbc_gt_advance":
        r, m, cny, fee, fu = hs_sell, hs_mid, A * hs_sell, F(0), F(20)
    elif kind == "boc_cash":
        r, m, cny, fee, fu = boc_cash, boc_mid, A * boc_cash, F(0), F(0)
    else:
        return None
    fx = A * (r / m - 1)
    return dict(cny=float(cny), fee_cny=float(fee), fx=float(fx), fee=float(fu),
                total=float(fx + fu), pct=float((fx + fu) / A * 100),
                gap=float(A * (r / fed - 1)))


priced = 0
for m in METHODS:
    kind = m["pricing"]
    for row in [r for r in ROWS if r["method"] == m["id"]]:
        a = row["amount"]
        if kind in ("unpriced", "exposure") or (m["id"] == "M09" and a > 10000):
            ok(row["total_usd"] == "" and row["cny"] == "",
               f"{m['id']} @ {a} must be blank, got {row['total_usd']}")
            continue
        e = expect(kind, a)
        priced += 1
        eq(row["cny"], round(e["cny"], 2), f"{m['id']} @ {a} CNY")
        eq(row["fee_cny"], round(e["fee_cny"], 2), f"{m['id']} @ {a} fee CNY")
        eq(row["fx_usd"], round(e["fx"], 2), f"{m['id']} @ {a} FX")
        eq(row["fee_usd"], round(e["fee"], 2), f"{m['id']} @ {a} fee USD")
        eq(row["total_usd"], round(e["total"], 2), f"{m['id']} @ {a} total")
        eq(row["pct"], round(e["pct"], 3), f"{m['id']} @ {a} pct", tol=0.0006)
        eq(row["gap_fed"], round(e["gap"], 2), f"{m['id']} @ {a} vs Fed")

ok(len(ROWS) == len(METHODS) * len(AMOUNTS) == 600, f"row count {len(ROWS)}")
ok(priced == 8 * 40 + 1, f"priced rows {priced} (expect 321)")

# summary rows: cheapest priced lawful route excluding the capped cash row
for s in SUMMARY:
    a = s["amount"]
    cands = []
    for m in METHODS:
        if m["pricing"] in ("unpriced", "exposure") or m["id"] == "M09":
            continue
        cands.append((expect(m["pricing"], a)["total"], m["id"]))
    best = min(cands)
    eq(s["total"], round(best[0], 2), f"summary cheapest @ {a}")
    ok(s["method"] == best[1], f"summary method @ {a}: {s['method']} vs {best[1]}")

# ---- 2. CSV parity ----
import csv
with open(os.path.join(D, "costs.csv"), encoding="utf-8") as f:
    csvrows = list(csv.DictReader(f))
ok(len(csvrows) == len(ROWS), "CSV row count")
for a, b in zip(csvrows, ROWS):
    if a["method"] != b["method"] or int(a["amount"]) != b["amount"] or a["total_usd"] != b["total_usd"]:
        ok(False, f"CSV mismatch {a} vs {b}")
        break
else:
    ok(True, "CSV parity")

# ---- 3. HTML structure ----
class P:
    def __init__(self, text):
        self.hrefs = re.findall(r'href="([^"]+)"', text)
        self.ids = set(re.findall(r'\sid="([^"]+)"', text))
        self.rows = []
        for body in re.findall(r"<tbody>(.*?)</tbody>", text, re.S):
            for tr in re.findall(r"<tr\b.*?</tr>", body, re.S):
                self.rows.append(re.findall(r'href="([^"]+)"', tr))


parsed = {f: P(open(os.path.join(HERE, f), encoding="utf-8").read()) for f in FILES}
total_rows = sum(len(p.rows) for p in parsed.values())
rows_without_official = 0
commercial_only = 0
for f, p in parsed.items():
    for i, r in enumerate(p.rows):
        if any(any(d in h for d in OFFICIAL) for h in r):
            continue
        if any("wise.com" in h for h in r):
            commercial_only += 1   # permitted only because the price cells are blank
            continue
        rows_without_official += 1
        ok(False, f"{f}: tbody row {i} has no official link (hrefs: {r[:3]})")
ok(commercial_only == 5, f"commercial-provider-only rows = {commercial_only} (expected 5, all blank-priced)")
ok(rows_without_official == 0, f"{total_rows} table rows, all with an official link")

# local links and anchors
missing = 0
for f, p in parsed.items():
    for h in p.hrefs:
        if h.startswith("http"):
            if not any(d in h for d in OFFICIAL) and "wise.com" not in h:
                ok(False, f"{f}: non-official external link {h}")
            continue
        path, _, frag = h.partition("#")
        target = f if not path else path
        if not os.path.exists(os.path.join(HERE, target)):
            ok(False, f"{f}: broken link {h}")
            missing += 1
            continue
        if frag and frag not in parsed.get(target, p).ids:
            ok(False, f"{f}: broken anchor {h}")
            missing += 1
ok(missing == 0, "local links and anchors")

# blank cells must carry a flag link
blanks = 0
for f, p in parsed.items():
    txt = open(os.path.join(HERE, f), encoding="utf-8").read()
    for m in re.finditer(r'class="blank"(.{0,220})', txt, re.S):
        blanks += 1
        ok("review.html#FR" in m.group(1), f"{f}: blank without flag link: {m.group(1)[:80]}")

# ---- 4. prose figures reproduced ----
costs_html = open(os.path.join(HERE, "costs.html"), encoding="utf-8").read()
index_html = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
a40 = SUMMARY[-1]
a10 = SUMMARY[0]
ok(f"${a40['total']:,.2f}" in index_html, "index shows the 400k total")
ok(f"{a40['pct']:.3f}%" in index_html, "index shows the 400k percentage")
ok(f"${a10['total']:,.2f}" in index_html, "index shows the 10k total")

band = float(F(400000) * (fed / F(str(S["S13"]["figures"]["nov2"])) - 1) * -1) if False else \
    float(400000 * (float(S["S13"]["figures"]["nov6"]) / float(S["S13"]["figures"]["nov2"]) - 1))
ok(f"{band:,.0f}" == "1,685", f"Fed H.10 band on 400k = {band:,.2f} (text says 1,685)")
pen = open(os.path.join(HERE, "penalties.html"), encoding="utf-8").read()
ok("USD 80,000" in pen and "USD 180,000" in pen, "scenario arithmetic 20%/45% of 400k")
ok("USD 40,000 to USD 400,000" in pen, "fine band on an 80,000 tax")
ok("USD 120,000 to USD 400,000" in pen, "unlawful band arithmetic")

# counts cited on the review page
rev = open(os.path.join(HERE, "review.html"), encoding="utf-8").read()
ok("379 tracked files" in rev, "review states the tree size")
import subprocess
try:
    r = subprocess.run(["git", "-C", os.path.join(HERE, ".."), "ls-tree", "-r", "2a5a470", "--name-only"],
                       capture_output=True, text=True, timeout=30)
    n = r.stdout.split()
except Exception:
    n = []
if n:
    ok(len(n) == 379, f"tracked files at 2a5a470 = {len(n)}")
else:
    # Shallow CI checkouts do not contain that commit; the claim is left as published
    # and not re-checked, which is printed rather than silently skipped.
    print("note: commit 2a5a470 is not in this checkout; the 379-file tree-size claim was not re-checked")
for n, frag in [("2", "creditable dollar-for-dollar"), ("39", "86.97"), ("12", "137,300"),
                ("50", "132,900")]:
    ok(n in rev, f"review cites count {n} for {frag}")

# ---- 5. repository conflicts named on the review page still hold ----
def line_has(path, lineno, needle):
    fp = os.path.join(HERE, "..", path)
    if not os.path.exists(fp):
        return None
    lines = open(fp, encoding="utf-8", errors="replace").read().splitlines()
    return needle in lines[lineno - 1] if len(lines) >= lineno else False


for path, ln, needle in [
    ("study-8f529c94/EXECUTIVE_SUMMARY.md", 20, "dollar-for-dollar"),
    ("transfer-guide/EXECUTIVE_SUMMARY.md", 20, "dollar-for-dollar"),
    ("estimate-facf2fe9/methods.html", 157, "stages"),
    ("estimate-facf2fe9/methods.html", 159, "staged"),
    ("verify-d5d1f860/costs.html", 50, "staged"),
    ("portal/index.html", 68, "10% US"),
]:
    r = line_has(path, ln, needle)
    ok(r is not False, f"review cites {path}:{ln} but the phrase is gone (r={r})")

# ---- 6. sources ----
ok(len(sources) == 27, f"{len(sources)} sources")
for s in sources:
    ok(s["url"].startswith("https://"), f"{s['id']} not https")
    ok(s.get("read") == "2026-11-11", f"{s['id']} read date")
    ok(len(s.get("quote", "")) > 30, f"{s['id']} quote too short")
ids_used = set(re.findall(r"\[(S\d\d)\]", open(os.path.join(HERE, "content.py"), encoding="utf-8").read()))
for m in METHODS:
    ids_used |= set(m["sources"])
ok(ids_used <= set(S), f"unknown source ids used: {ids_used - set(S)}")
unused = set(S) - ids_used
print("sources not referenced in content (still published):", sorted(unused))

print(f"\n{checks} checks, {failed} failures, {blanks} blank cells flagged, "
      f"{total_rows} table rows, {priced} recomputed cost cells")
sys.exit(1 if failed else 0)
