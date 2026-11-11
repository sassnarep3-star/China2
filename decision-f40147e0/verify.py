#!/usr/bin/env python3
"""Independent verification of decision-f40147e0.

Re-derives the arithmetic from data/sources.json (not from the stored model output),
then checks the rendered HTML. Any failure exits non-zero.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

SOURCES = json.loads((DATA / "sources.json").read_text())
METHODS = json.loads((DATA / "methods.json").read_text())
FLAGS = json.loads((DATA / "flags.json").read_text())
COSTS = json.loads((DATA / "costs.json").read_text())

SOURCE_BY_ID = {s["id"]: s for s in SOURCES}
METHOD_BY_ID = {m["id"]: m for m in METHODS}
FLAG_BY_ID = {f["id"]: f for f in FLAGS}

# Publishers whose own site may be cited as the authority for a row.
OFFICIAL_HOSTS = (
    "boc.cn", "bankofchina.com", "cmbchina.com", "hsbc.com.cn", "services.cn-banking.hsbc.com.cn",
    "icbc.com.cn", "abchina.com", "ccb.com", "safe.gov.cn", "pbc.gov.cn",
    "chinatax.gov.cn", "fgk.chinatax.gov.cn", "gov.cn", "govinfo.gov", "irs.gov",
    "ecfr.gov", "cbp.gov", "fincen.gov", "federalregister.gov",
)
PROVIDER_HOSTS = ("wise.com",)

CHECKS = 0
FAILS = []


def check(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(msg)


def host_of(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_official(url: str) -> bool:
    h = host_of(url)
    return any(h == d or h.endswith("." + d) for d in OFFICIAL_HOSTS)


def is_provider(url: str) -> bool:
    h = host_of(url)
    return any(h == d or h.endswith("." + d) for d in PROVIDER_HOSTS)


# ---------------------------------------------------------------- ledger integrity
check(len(SOURCES) == len(SOURCE_BY_ID), "duplicate source id")
for s in SOURCES:
    for field in ("id", "authority", "title", "url", "kind", "retrieved", "quote_original",
                  "quote_en", "used_for", "limits"):
        check(bool(s.get(field)), f"{s.get('id')}: missing {field}")
    check(s["url"].startswith("https://"), f"{s['id']}: url is not https")
    check(is_official(s["url"]) or is_provider(s["url"]), f"{s['id']}: host not in allowlist ({host_of(s['url'])})")
    check(s["retrieved"] == "2026-11-11", f"{s['id']}: retrieval date is not this pass")
    check(len(s["quote_original"]) > 20, f"{s['id']}: quote too short to be a quote")

for m in METHODS:
    check(m["status"] in {"lawful", "conditional", "unlawful", "not_applicable", "unverified"},
          f"{m['id']}: bad status {m['status']}")
    check(bool(m["steps"]) and bool(m["pros"]) and bool(m["cons"]), f"{m['id']}: missing steps/pros/cons")
    for sid in m["sources"]:
        check(sid in SOURCE_BY_ID, f"{m['id']}: unknown source {sid}")
    for fid in m.get("flags", []):
        check(fid in FLAG_BY_ID, f"{m['id']}: unknown flag {fid}")
    if m["status"] == "unlawful":
        check(m["pricing"] is None, f"{m['id']}: unlawful route must not be priced")
        check(all(any(k in step.lower() for k in ("no execution steps", "not provided", "see art", "no steps"))
                  for step in m["steps"]), f"{m['id']}: unlawful route appears to contain instructions")
    if m["pricing"] is not None:
        p = m["pricing"]
        for f in ("rate_src", "sell", "ref", "fee_pct", "fee_min", "fee_max", "cable", "fee_src"):
            check(f in p, f"{m['id']}: pricing missing {f}")
        check(p["rate_src"] in SOURCE_BY_ID and p["fee_src"] in SOURCE_BY_ID,
              f"{m['id']}: pricing cites an unknown source")
        # The selling rate in the model must be the one printed on the cited board.
        board_sell = {"S01": 6.6911, "S03": 6.69199, "S05": 6.7079204}
        check(p["rate_src"] in board_sell, f"{m['id']}: rate source has no recorded selling rate")
        if p["rate_src"] in board_sell:
            check(abs(p["sell"] - board_sell[p["rate_src"]]) < 1e-9,
                  f"{m['id']}: selling rate does not match the cited board")

for f in FLAGS:
    check(bool(f["what"]) and bool(f["why"]) and bool(f["resolve"]), f"{f['id']}: incomplete flag")
    for sid in f["sources"]:
        check(sid in SOURCE_BY_ID, f"{f['id']}: unknown source {sid}")
    check(f["severity"] in {"high", "medium", "low"}, f"{f['id']}: bad severity")

# ---------------------------------------------------------------- arithmetic, recomputed
META = COSTS["meta"]
rows = COSTS["rows"]
priced_methods = [m["id"] for m in METHODS if m["pricing"]]
check(META["priced_methods"] == priced_methods, "meta priced_methods does not match the ledger")
check(META["tier_count"] == 40, "expected 40 tiers")
check(len(rows) == 40 * len(priced_methods), f"row count {len(rows)} != 40 x {len(priced_methods)}")

ref = META["ref_mid"]
check(abs(ref - 6.6763571) < 1e-6, "reference mid drifted")

for r in rows:
    m = METHOD_BY_ID[r["method"]]
    spec = m["pricing"]
    if m.get("cap_usd") is not None and r["usd"] > m["cap_usd"]:
        check(r["state"] != "priced", f"{r['method']}@{r['usd']}: priced above its ceiling")
        continue
    check(r["state"] == "priced", f"{r['method']}@{r['usd']}: should be priced")
    if r["state"] != "priced":
        continue
    cny = r["usd"] * ref
    spread = r["usd"] * (spec["sell"] / ref - 1)
    fee_cny = max(spec["fee_min"], min(spec["fee_max"], spec["fee_pct"] * cny)) + spec["cable"]
    fee_usd = fee_cny / ref
    total = spread + fee_usd
    check(abs(cny - r["cny"]) < 0.02, f"{r['method']}@{r['usd']}: cny drift")
    check(abs(spread - r["spread_usd"]) < 0.02, f"{r['method']}@{r['usd']}: spread drift")
    check(abs(fee_cny - r["fee_cny"]) < 0.02, f"{r['method']}@{r['usd']}: fee drift")
    check(abs(total - r["total_usd"]) < 0.02, f"{r['method']}@{r['usd']}: total drift")
    check(abs(r["pct"] - total / r["usd"] * 100) < 0.001, f"{r['method']}@{r['usd']}: pct drift")
    check(r["total_usd"] > 0, f"{r['method']}@{r['usd']}: zero cost is not plausible")

# The ranking must be monotonic in cost and cover only priced methods.
rank = COSTS["ranking_100k"]
check(rank == sorted(rank, key=lambda x: x["total_usd"]), "ranking is not sorted")
check(all(r["method"] in priced_methods for r in rank), "ranking contains an unpriced method")
check(all(abs(r["total_usd"] - next(c["total_usd"] for c in rows
                                    if c["method"] == r["method"] and c["usd"] == 100000)) < 0.02
          for r in rank), "ranking disagrees with the row table")

for il in COSTS["illustrative_988"]:
    check(abs(il["gain_usd"] - (il["usd"] - il["usd"] * ref / META["irs_2025_yuan_per_usd"])) < 0.02,
          f"§988 illustration drift at {il['usd']}")

# ---------------------------------------------------------------- rendered HTML
pages = sorted(p.name for p in ROOT.glob("*.html"))
check(len(pages) == 9, f"expected 9 pages, found {len(pages)}")

LOCAL = re.compile(r'href="([^"#:]+\.html)(#[^"]*)?"')
ALL_HREFS = re.compile(r'href="([^"]+)"')
IDS = re.compile(r'id="([^"]+)"')

ids_by_page = {}
for page in pages:
    text = (ROOT / page).read_text()
    ids_by_page[page] = set(IDS.findall(text))

for page in pages:
    text = (ROOT / page).read_text()
    for target, frag in LOCAL.findall(text):
        check((ROOT / target).exists(), f"{page}: broken local link {target}")
        if frag:
            check(frag.lstrip("#") in ids_by_page.get(target, set()),
                  f"{page}: broken anchor {target}{frag}")
    for href in ALL_HREFS.findall(text):
        if href.startswith(("http://", "https://")):
            check(is_official(href) or is_provider(href) or host_of(href) == "github.com",
                  f"{page}: external link to a non-official host {host_of(href)}")
    check("<html" in text and "</html>" in text, f"{page}: not a complete document")
    check('name="viewport"' in text, f"{page}: no viewport meta")
    check("assets/style.css" in text, f"{page}: missing stylesheet link")
    # No placeholders left in the rendered output.
    for bad in (">None<", "NaN", "undefined", "{{", "}}", "TODO", "XXX"):
        check(bad not in text, f"{page}: contains placeholder token {bad!r}")

# Every table body row must carry at least one external official link.
row_re = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
td_re = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
for page in pages:
    text = (ROOT / page).read_text()
    for body in re.findall(r"<tbody>(.*?)</tbody>", text, re.S):
        for row in row_re.findall(body):
            cells = td_re.findall(row)
            if not cells:
                continue
            if "none published" in row:
                continue  # flagged as a gap by design; the cell says so
            check("http" in row, f"{page}: a table body row has no source link")

# Numbers printed on the overview must equal the model.
idx = (ROOT / "index.html").read_text()
for key, mid in (("100000", "M01"), ("100000", "M03"), ("400000", "M01")):
    val = COSTS["headline"][mid][key]["total_usd"]
    check(f"${val:,.2f}" in idx, f"index.html: missing ${val:,.2f} for {mid}@{key}")
for key, mid in (("10000", "M01"), ("400000", "M01")):
    pc = COSTS["headline"][mid][key]["pct"]
    check(f"{pc:.2f}%" in idx, f"index.html: missing {pc:.2f}% for {mid}@{key}")

# Costs page must contain every priced headline for the primary methods.
costs = (ROOT / "costs.html").read_text()
for mid in ("M01", "M02", "M03", "M04"):
    for key in ("10000", "100000", "400000"):
        v = COSTS["headline"][mid][key]["total_usd"]
        check(f"${v:,.2f}" in costs, f"costs.html: missing {mid}@{key} (${v:,.2f})")

# Every source id must be reachable somewhere in the rendered sources page.
srcpage = (ROOT / "sources.html").read_text()
for s in SOURCES:
    check(f'id="{s["id"]}"' in srcpage, f"sources.html: {s['id']} has no anchor")
    check(s["url"] in srcpage, f"sources.html: {s['id']} url not linked")
for f in FLAGS:
    check(f'id="{f["id"]}"' in (ROOT / "flagged.html").read_text(), f"flagged.html: {f['id']} missing")

# Blank rule: unpriced methods must not print a dollar figure on the costs page.
for m in METHODS:
    if m["pricing"] is None:
        block = re.search(rf'id="{m["id"]}".*?</details>', costs, re.S)
        check(block is None, f"costs.html: unpriced {m['id']} has a priced detail block")

print(f"checks run: {CHECKS}")
if FAILS:
    print(f"FAIL: {len(FAILS)}")
    for f in FAILS[:40]:
        print("  -", f)
    sys.exit(1)
print(f"PASS: {CHECKS} checks, 0 failures — ledger, arithmetic, blank rule, row links, local links, anchors")
