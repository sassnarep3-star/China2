#!/usr/bin/env python3
"""Independent verifier for verify-9fe02cf5.

Deliberately re-implements the cost arithmetic instead of importing build.py,
so a mistake in one file cannot hide itself in the other. Exits non-zero on any
failure. Structural and arithmetic checks only: they do not certify the law.
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.dont_write_bytecode = True

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
PAGES = ["index.html", "questions.html", "methods.html", "costs.html", "taxes.html",
         "verification.html", "flagged.html", "sources.html", "audit.html"]

OFFICIAL = ("safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "gov.cn", "irs.gov",
            "govinfo.gov", "ecfr.gov", "cbp.gov")
COMMERCIAL = ("hsbc.com.cn", "boc.cn")
REPO_EVIDENCE = ("github.com",)

checks = 0
failures = []


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


def load(name):
    return json.load(open(DATA / name, encoding="utf-8"))


sources = load("sources.json")
claims = load("claims.json")
methods = load("methods.json")
questions = load("questions.json")
flags = load("flags.json")
costs = load("costs.json")
repo = load("repo_audit.json")

SRC = {s["id"]: s for s in sources["sources"]}
CLAIM = {c["id"]: c for c in claims["claims"]}

P = costs["parameters"]
RATE = P["boc_sell_cny_per_usd"]
BUY = P["boc_buy_cny_per_usd"]
SPREAD = (RATE - BUY) / RATE * 100.0
BLANK = "\u2014"

# --------------------------------------------------------------- page structure
texts = {}
for name in PAGES:
    path = BASE / name
    check(path.exists(), f"{name} missing")
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    texts[name] = text
    check('name="viewport"' in text, f"{name} has no viewport meta")
    check("assets/style.css" in text, f"{name} does not link the stylesheet")
    check("<title>" in text and "</title>" in text, f"{name} has no title")
    check('href="../index.html"' in text, f"{name} has no link back to the hub")
    check("Flagged for Review" in text or name == "flagged.html",
          f"{name} does not point at the flagged page")
    for href, _label in [("index.html", ""), ("questions.html", ""), ("methods.html", ""),
                         ("costs.html", ""), ("taxes.html", ""), ("verification.html", ""),
                         ("flagged.html", ""), ("sources.html", ""), ("audit.html", "")]:
        check(f'href="{href}"' in text, f"{name} nav is missing {href}")
    for asset in ("assets/style.css", "assets/app.js"):
        check((BASE / asset).exists(), f"{asset} missing")

# --------------------------------------------------------------- local links
ids = {}
for name, text in texts.items():
    ids[name] = set(re.findall(r'id="([^"]+)"', text))
for name, text in texts.items():
    for ref in re.findall(r'(?:href|src)="([^"]+)"', text):
        if ref.startswith(("http://", "https://", "mailto:")):
            continue
        if ref.startswith("#"):
            check(ref[1:] in ids[name], f"{name}: dangling anchor {ref}")
            continue
        target, _, frag = ref.partition("#")
        target_path = (BASE / target).resolve()
        check(target_path.exists(), f"{name}: broken local link {ref}")
        if frag and target.endswith(".html") and target in ids:
            check(frag in ids[target], f"{name}: dangling anchor {ref}")
        if target in ids and not frag:
            continue

# --------------------------------------------------------------- external links
def allowed(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d)
               for d in OFFICIAL + COMMERCIAL + REPO_EVIDENCE)


for name, text in texts.items():
    for url in re.findall(r'href="(https?://[^"]+)"', text):
        check(url.startswith("https://"), f"{name}: non-HTTPS external link {url}")
        check(allowed(url), f"{name}: external link outside the allowlist {url}")

# --------------------------------------------------------------- table rows cited
def table_rows(text):
    """Yield the raw <tr> inner HTML for rows inside <tbody>."""
    body = text.split("<tbody>")
    rows = []
    for chunk in body[1:]:
        chunk = chunk.split("</tbody>")[0]
        rows.extend(re.findall(r"<tr>(.*?)</tr>", chunk, flags=re.S))
    return rows


row_counts = {}
for name, text in texts.items():
    rows = table_rows(text)
    row_counts[name] = len(rows)
    for row in rows:
        links = re.findall(r'href="(https?://[^"]+)"', row)
        check(bool(links), f"{name}: table row without an external source link: {row[:120]}")
        if links:
            check(all(allowed(u) for u in links),
                  f"{name}: table row cites a non-allowlisted link: {links}")
            check(all(u.startswith("https://") for u in links),
                  f"{name}: table row cites a non-HTTPS link: {links}")

# --------------------------------------------------------------- source register
check(len(sources["sources"]) == 21, "expected 21 sources")
for s in sources["sources"]:
    check(bool(s.get("url")), f"{s['id']} has no URL")
    check(s["url"].startswith("https://"), f"{s['id']} URL is not HTTPS")
    check(allowed(s["url"]), f"{s['id']} URL is outside the allowlist")
    check(bool(s.get("excerpt")), f"{s['id']} has no verbatim excerpt")
    check(bool(s.get("locator")), f"{s['id']} has no locator")
    check(bool(s.get("retrieved")), f"{s['id']} has no retrieval date")
    check(s["retrieved"] == "2026-11-11", f"{s['id']} was not re-fetched on 2026-11-11")
    check(f'id="{s["id"]}"' in texts["sources.html"], f"sources.html omits {s['id']}")

# --------------------------------------------------------------- claims
check(len(claims["claims"]) == 27, "expected 27 claims")
for c in claims["claims"]:
    check(c["status"] in {"VERIFIED", "PARTIAL", "UNVERIFIED"}, f"{c['id']} bad status")
    check(bool(c["evidence"]), f"{c['id']} has no quoted evidence")
    check(bool(c["statement"]), f"{c['id']} has no statement")
    check(bool(c["source_ids"]), f"{c['id']} cites no source")
    for sid in c["source_ids"]:
        check(sid in SRC, f"{c['id']} cites unknown source {sid}")
    check(f'id="{c["id"]}"' in texts["verification.html"],
          f"verification.html omits {c['id']}")
    head = html.escape(c["statement"][:40], quote=True)
    check(head in texts["verification.html"],
          f"verification.html does not carry the statement for {c['id']}")

# --------------------------------------------------------------- methods
check(len(methods["methods"]) == 12, "expected 12 methods")
for m in methods["methods"]:
    check(m["status"] in {"LAWFUL", "CONDITIONAL", "REJECTED"}, f"{m['id']} bad status")
    check(bool(m["steps"]), f"{m['id']} has no steps")
    check(bool(m["pros"]) and bool(m["cons"]), f"{m['id']} lacks pros or cons")
    check(bool(m["cap"]), f"{m['id']} has no stated limit")
    for cid in m["basis_claims"]:
        check(cid in CLAIM, f"{m['id']} cites unknown claim {cid}")
    if m["fee_model"]:
        check(m["fee_model"] in costs["fee_models"], f"{m['id']} unknown fee model")
    if m["status"] == "REJECTED":
        check(m["fee_model"] is None, f"{m['id']} is rejected but carries a fee model")
    check(m["id"] in texts["methods.html"], f"methods.html omits {m['id']}")

# --------------------------------------------------------------- questions / flags
for q in questions["questions"]:
    check(bool(q["how"]), f"{q['id']} has no discovery steps")
    check(bool(q["we_do_not_know"]), f"{q['id']} asserts knowledge it does not have")
    for sid in q["source_ids"]:
        check(sid in SRC, f"{q['id']} cites unknown source {sid}")
    for fid in q["flags"]:
        check(any(f["id"] == fid for f in flags["flags"]), f"{q['id']} cites unknown flag {fid}")
    check(f'id="{q["id"]}"' in texts["questions.html"], f"questions.html omits {q['id']}")

for f in flags["flags"]:
    check(f["status"] in {"UNVERIFIED", "REVIEW", "PARTIAL", "VERIFIED-WITH-DATE"},
          f"{f['id']} bad status")
    check(bool(f["detail"]), f"{f['id']} has no detail")
    for sid in f["source_ids"]:
        check(sid in SRC, f"{f['id']} cites unknown source {sid}")
    check(f'id="{f["id"]}"' in texts["flagged.html"], f"flagged.html omits {f['id']}")

# --------------------------------------------------------------- repo audit
check(len(repo["findings"]) >= 6, "repo audit has too few findings")
for f in repo["findings"]:
    check(f["status"] in {"REVIEW", "VERIFIED", "PARTIAL"}, "repo audit bad status")

# --------------------------------------------------------------- cost arithmetic
ladder = json.load(open(BASE / "exports" / "cost-ladder.json", encoding="utf-8"))
rows = ladder["rows"]
tier_list = list(range(P["tier_start_usd"], P["tier_end_usd"] + 1, P["tier_step_usd"]))
check(len(tier_list) == 40, "tier list is not 40 entries")
check(tier_list[0] == 10000 and tier_list[-1] == 400000, "tier range is wrong")
method_ids = [r["method"] for r in costs["rows"]]
check(len(rows) == 40 * len(method_ids), f"ladder has {len(rows)} rows, expected 400")
check(abs(ladder["benchmark_spread_pct"] - round(SPREAD, 6)) < 1e-9,
      "exported benchmark spread does not match the published rates")
check(abs(ladder["reference_rate_cny_per_usd"] - RATE) < 1e-12, "exported rate is wrong")

for r in rows:
    mid = r["method"]
    conf = next(x for x in costs["rows"] if x["method"] == mid)
    model = conf["fee_model"]
    amount = r["amount_usd"]
    check(amount in tier_list, f"{mid}: amount {amount} is not a $10k tier")
    check(abs(r["cny_needed"] - amount * RATE) < 1e-6, f"{mid}/{amount}: CNY total wrong")
    check(abs(r["spread_usd"] - amount * SPREAD / 100.0) < 1e-6,
          f"{mid}/{amount}: benchmark spread wrong")
    if model is None:
        check(r["fee_usd"] is None, f"{mid}/{amount}: fee must be blank")
        check(r["all_in_usd"] is None, f"{mid}/{amount}: all-in must be blank")
    else:
        fm = costs["fee_models"][model]
        raw = amount * RATE * fm["commission_pct"]
        comm = min(max(raw, fm["commission_min_cny"]), fm["commission_max_cny"]) \
            if fm["commission_pct"] > 0 else 0.0
        expect = (comm + fm["cable_cny"] + fm["pay_exact_cny"]) / RATE
        check(r["fee_usd"] is not None, f"{mid}/{amount}: fee must be present")
        check(abs(r["fee_usd"] - expect) < 1e-6,
              f"{mid}/{amount}: fee {r['fee_usd']} != recomputed {expect}")
        check(abs(r["all_in_usd"] - (expect + r["spread_usd"])) < 1e-6,
              f"{mid}/{amount}: all-in wrong")
    if mid == "M06":
        check(r["timing"] and r["timing"].endswith("annual tranche") or "annual tranches" in r["timing"],
              f"M06/{amount}: quota tranche count missing")
        n = -(-amount // P["annual_quota_usd"])
        check(str(n) in r["timing"], f"M06/{amount}: expected {n} tranches")
    if mid == "M07":
        years = -(-int(round(amount * RATE)) // P["atm_annual_rmb_cap"])
        check(str(years) in r["timing"], f"M07/{amount}: expected {years} years")

# the cap must actually bind at the top tier: M01 fee equals (500 + 120) / rate
cap_cny = costs["fee_models"]["hsbc_premier_sha"]["commission_max_cny"] + \
    costs["fee_models"]["hsbc_premier_sha"]["cable_cny"]
top_m01 = next(r for r in rows if r["method"] == "M01" and r["amount_usd"] == 400000)
check(abs(top_m01["fee_usd"] - cap_cny / RATE) < 1e-9,
      "M01 top-tier fee does not equal the published capped amount")

# --------------------------------------------------------------- rendered blanks
cost_rows = table_rows(texts["costs.html"])
check(len(cost_rows) == len(rows) + 2 + 5 * 4,
      f"costs.html renders {len(cost_rows)} rows, expected {len(rows) + 22}")
for row in cost_rows:
    cells = re.findall(r'data-label="([^"]+)">(.*?)</td>', row, flags=re.S)
    d = {k: v for k, v in cells}
    mid = re.sub(r"<[^>]+>", "", d.get("Method", "")).strip()
    fee = d.get("Published sender fee", "")
    if mid in {"M05", "M06", "M07", "M08", "M09", "M10"}:
        check(BLANK in fee, f"costs.html: {mid} row must show a blank fee")
        check("$0.00" not in fee, f"costs.html: {mid} row shows $0.00 instead of blank")
    elif mid:
        check("$" in fee and BLANK not in fee, f"costs.html: {mid} row lost its fee")

# --------------------------------------------------------------- stated numbers
check("0.420%" in texts["index.html"], "index.html does not state the benchmark spread")
check("0.420%" in texts["costs.html"], "costs.html does not state the benchmark spread")
check(f"{SPREAD:.6f}" in texts["costs.html"], "costs.html omits the spread formula")
check("6.6911" in texts["costs.html"], "costs.html omits the rate used")
check("2026-11-11 10:25:02" in texts["costs.html"], "costs.html omits the rate timestamp")
for bad in ("Capital Gain (Schedule D)", "5%/mo up to 25%", "$132,900"):
    for name in ("index.html", "costs.html", "taxes.html", "methods.html"):
        check(bad not in texts[name], f"{name} still asserts an unverified value: {bad}")
check("$16,536" in texts["taxes.html"], "taxes.html omits the FBAR non-willful maximum")
check("$165,353" in texts["taxes.html"], "taxes.html omits the FBAR willful maximum")
check("$200" in texts["taxes.html"], "taxes.html omits the section 988 threshold")

# --------------------------------------------------------------- exports
check(len(ladder["rows"]) == 400, "cost-ladder.json is incomplete")
csv_text = (BASE / "exports" / "cost-ladder.csv").read_text(encoding="utf-8")
check(csv_text.count("\n") == 401, "cost-ladder.csv does not have 400 data rows")
check(csv_text.splitlines()[0].startswith("amount_usd,method"), "CSV header changed")
claims_csv = (BASE / "exports" / "claims.csv").read_text(encoding="utf-8")
check(claims_csv.count("\n") == 28, "claims.csv does not have 27 data rows")

# --------------------------------------------------------------- headline arithmetic
m01_400 = next(r for r in rows if r["method"] == "M01" and r["amount_usd"] == 400000)
check(abs(m01_400["all_in_usd"] -
          (m01_400["fee_usd"] + m01_400["spread_usd"])) < 1e-6, "M01 400k all-in wrong")
check(f"{m01_400['all_in_usd']:,.2f}" in texts["index.html"],
      "index.html headline does not match the recomputed 400k all-in")
prime_10 = next(r for r in rows if r["method"] == "M01" and r["amount_usd"] == 10000)
check(f"{prime_10['all_in_usd']:,.2f}" in texts["index.html"],
      "index.html headline does not match the recomputed 10k all-in")

# --------------------------------------------------------------- markdown summary
summary_path = BASE / "EXECUTIVE_SUMMARY.md"
check(summary_path.exists(), "EXECUTIVE_SUMMARY.md is missing")
if summary_path.exists():
    md = summary_path.read_text(encoding="utf-8")
    check("2026-11-11" in md, "summary has no verification date")
    check("Not advice" in md or "not advice" in md, "summary lacks the not-advice statement")
    for amount in (10000, 50000, 100000, 200000, 400000):
        r = next(x for x in rows if x["method"] == "M01" and x["amount_usd"] == amount)
        check(f"{r['all_in_usd']:,.2f}" in md,
              f"summary headline for {amount} does not match the recomputed all-in")
    check("Flagged for review" in md or "flagged.html" in md, "summary omits the flags")

# --------------------------------------------------------------- summary
if failures:
    print(f"FAIL: {len(failures)} of {checks} checks failed")
    for f in failures[:40]:
        print("  -", f)
    sys.exit(1)
print(f"PASS: {checks:,} independent checks, 0 failures across {len(PAGES)} pages, "
      f"{len(rows)} ladder rows, {len(claims['claims'])} claims, "
      f"{len(sources['sources'])} sources, {len(flags['flags'])} flags.")
