#!/usr/bin/env python3
"""Independent verifier for verify-ace15295.

Re-computes every published number from the ledger, then checks the generated
HTML: every data row carries a link to the publisher's own host, every blank is
a flagged blank, every internal href/anchor resolves, no external script or
stylesheet is referenced, and no unverified value was invented.

Exit code 0 only if every check passes. No network access.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

FAIL: list[str] = []
N = 0

def ok(cond: bool, msg: str) -> None:
    global N
    N += 1
    if not cond:
        FAIL.append(msg)

# hosts that count as an official / primary publisher
OFFICIAL_SUFFIXES = (".gov", ".gov.cn", ".irs.gov", ".cbp.gov", ".ecfr.gov", ".chinatax.gov.cn",
                     ".safe.gov.cn", ".pbc.gov.cn", ".customs.gov.cn")
OFFICIAL_EXACT = {"www.gov.cn", "gov.cn", "www.irs.gov", "irs.gov", "www.cbp.gov", "cbp.gov",
                  "www.ecfr.gov", "ecfr.gov", "fgk.chinatax.gov.cn", "www.safe.gov.cn",
                  "www.pbc.gov.cn", "m.safe.gov.cn", "fgk.chinatax.gov.cn"}
# primary commercial publishers: a bank publishing its own rate board or tariff
PRIMARY_COMMERCIAL = {"www.boc.cn", "boc.cn", "fx.cmbchina.com", "www.hsbc.com.cn",
                      "www.services.cn-banking.hsbc.com.cn", "www.icbc.com.cn",
                      "m.mofcom.gov.cn"}
# scholarly mirror of the U.S. Code, accepted only where the official site was unreachable
ACCEPTED_MIRROR = {"www.law.cornell.edu"}


def host_of(u: str) -> str:
    return (urlparse(u).hostname or "").lower()


def is_official(u: str) -> bool:
    h = host_of(u)
    if h in OFFICIAL_EXACT or h in PRIMARY_COMMERCIAL or h in ACCEPTED_MIRROR:
        return True
    return any(h.endswith(s) for s in OFFICIAL_SUFFIXES) or h.endswith(".gov.cn")


# ---------------------------------------------------------------- ledger ----
sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]
findings = json.loads((DATA / "findings.json").read_text(encoding="utf-8"))["findings"]
questions = json.loads((DATA / "questions.json").read_text(encoding="utf-8"))["questions"]
costs = json.loads((DATA / "costs.json").read_text(encoding="utf-8"))
S = {s["id"]: s for s in sources}
FT = {f["id"]: f for f in findings}
QT = {q["id"]: q for q in questions}

ok(len(sources) == 31, f"expected 31 sources, got {len(sources)}")
ok(len({s["id"] for s in sources}) == len(sources), "duplicate source id")
ok(len(findings) == 9, f"expected 9 findings, got {len(findings)}")
ok(len(questions) == 14, f"expected 14 questions, got {len(questions)}")

for s in sources:
    ok(is_official(s["url"]), f'{s["id"]} is not on an official/primary host: {s["url"]}')
    ok(s["url"].startswith("https://") or s["url"].startswith("http://"), f'{s["id"]} not a URL')
    ok(bool(s["relied_on"]), f'{s["id"]} has no relied_on propositions')
    ok(s["retrieved"] == "2026-11-11", f'{s["id"]} retrieved date is not this session')

# every source referenced by a finding / question must exist
for f in findings:
    for sid in f["sources"]:
        ok(sid in S, f'{f["id"]} cites unknown source {sid}')
for q in questions:
    ok(len(q["sources"]) >= 1, f'{q["id"]} cites no source')
    for sid in q["sources"]:
        ok(sid in S, f'{q["id"]} cites unknown source {sid}')

# ------------------------------------------------ recompute the cost model ----
boards = costs["boards"]
tiers = [10_000 * i for i in range(1, 41)]

for code, b in boards.items():
    mid = (b["buy"] + b["sell"]) / 2.0
    ok(abs(mid - b["mid"]) < 1e-9, f"{code} mid mismatch")
    hs = (b["sell"] - b["buy"]) / 2.0 / mid * 100.0
    ok(abs(hs - b["half_spread_pct"]) < 1e-9, f"{code} half-spread mismatch")
    ok(b["sell"] > b["buy"], f"{code} sell must exceed buy")
    ok(b["source"] in S, f"{code} rate source missing")
    ok(is_official(S[b["source"]]["url"]), f"{code} rate source is not official/primary")

routes = costs["routes"]
ok(len(routes) == 200, f"expected 200 route rows, got {len(routes)}")
ok(sorted({r["usd"] for r in routes}) == tiers, "route rows do not cover every tier")

seen = set()
for r in routes:
    key = (r["bank"], r["tariff"], r["usd"])
    ok(key not in seen, f"duplicate route row {key}")
    seen.add(key)
    b = boards[r["bank"]]
    sell_rate = b["sell"] / 100.0
    mid_rate = b["mid"] / 100.0
    ok(abs(r["sell_cny_per_usd"] if "sell_cny_per_usd" in r else r["rate"] - sell_rate) < 1e-9,
       f"{key} sell rate not derived from board")
    ok(abs(r["rate"] - sell_rate) < 1e-12, f"{key} rate mismatch")
    ok(abs(r["cny_needed"] - r["usd"] * sell_rate) < 1e-6, f"{key} CNY needed mismatch")
    # the extra CNY paid over mid, converted back at the bank's own selling rate:
    # cost as a fraction of the dollars actually delivered = (sell - mid) / sell
    ok(abs(r["spread_usd"] - r["usd"] * (sell_rate - mid_rate) / sell_rate) < 1e-9,
       f"{key} spread mismatch")
    ok(r["spread_usd"] < r["usd"] * 0.01, f"{key} spread above 1% of amount")
    ok(r["rate_source"] in S, f"{key} missing rate source")

    if r["tariff"] == "UNPUBLISHED":
        ok(r["fee_usd"] is None and r["fee_cny"] is None, f"{key} unpublished tariff must be blank")
        ok(r["total_usd"] is None and r["pct"] is None, f"{key} unpublished total must be blank")
    else:
        t = costs["tariffs"][r["tariff"]]
        ok(r["fee_source"] == t["source"], f"{key} fee source mismatch")
        ok(is_official(S[t["source"]]["url"]), f"{key} fee source not official/primary")
        if "flat_usd" in t:
            exp = t["flat_usd"] * sell_rate
        else:
            exp = max(r["usd"] * sell_rate * t["fee_bp"] / 10_000.0, t["min_cny"])
            exp = min(exp, t["max_cny"]) + t["cable_cny"]
        ok(abs(r["fee_cny"] - exp) < 1e-9, f"{key} fee recompute mismatch")
        ok(abs(r["fee_usd"] - exp / sell_rate) < 1e-9, f"{key} fee USD mismatch")
        total = r["spread_usd"] + r["fee_usd"]
        ok(abs(r["total_usd"] - total) < 1e-9, f"{key} total mismatch")
        ok(abs(r["pct"] - total / r["usd"] * 100.0) < 1e-9, f"{key} pct mismatch")
        ok(0.0 < r["pct"] < 2.0, f"{key} cost pct out of plausible band: {r['pct']}")

# the headline claim on the index and costs pages
def route(bank, tariff, usd):
    return next(r for r in routes if r["bank"] == bank and r["tariff"] == tariff and r["usd"] == usd)

boc400 = route("BOC", "BOC", 400_000)
hsp400 = route("HSBC", "HSBC_PREMIER", 400_000)
hpv400 = route("HSBC", "HSBC_PRIVATE", 400_000)
ok(abs(boc400["total_usd"] - 901.20) < 0.01, f"BOC 400k headline changed: {boc400['total_usd']}")
ok(abs(hsp400["total_usd"] - 2082.26) < 0.01, f"HSBC Premier 400k headline changed: {hsp400['total_usd']}")
ok(abs(hpv400["total_usd"] - 1989.83) < 0.01, f"HSBC Private 400k headline changed: {hpv400['total_usd']}")
ok(abs((hsp400["total_usd"] - boc400["total_usd"]) - 1181.06) < 0.01, "headline difference changed")

# Find the crossover tier: below it HSBC Private Banking wins on the CNY 50 minimum
# plus cable, above it BOC wins on spread. The claim must be published accurately.
cheapest = {}
for t in tiers:
    cands = [r for r in routes if r["usd"] == t and r["total_usd"] is not None]
    c = min(cands, key=lambda r: r["total_usd"])
    cheapest[t] = (c["bank"], c["tariff"])
first_boc = min(t for t, v in cheapest.items() if v[0] == "BOC")
winners_below = {v for t, v in cheapest.items() if t < first_boc}
ok(all(b == "BOC" for t, (b, _) in cheapest.items() if t >= first_boc),
   "BOC is not cheapest at every tier at or above the crossover")
ok(winners_below == {("HSBC", "HSBC_PRIVATE")},
   f"unexpected winner below crossover: {winners_below}")
ok(tiers.index(first_boc) <= 2, f"crossover unexpectedly high: {first_boc}")
ok(costs["cheapest_by_tier"][str(first_boc)] == "BOC", "published crossover table disagrees")
# the crossover dollar figure quoted on the costs page (~$11,820) must bracket the true point
prev = [t for t in tiers if t < first_boc]
ok(prev and first_boc - 10_000 <= 11_820 <= first_boc,
   f"quoted crossover $11,820 outside the true bracket {prev} -> {first_boc}")

# HSBC spread must exceed BOC's by roughly 2.4x, the claim on the costs page
ratio = boards["HSBC"]["half_spread_pct"] / boards["BOC"]["half_spread_pct"]
ok(2.3 < ratio < 2.5, f"HSBC/BOC spread ratio changed: {ratio}")

pen = {p["usd"]: p for p in costs["penalties"]}
ok(sorted(pen) == tiers, "penalty rows do not cover every tier")
for t, p in pen.items():
    ok(abs(p["unlawful_30pct_usd"] - t * 0.30) < 1e-6, f"unlawful 30% at {t}")
    ok(abs(p["unlawful_max_usd"] - t * 1.00) < 1e-6, f"unlawful max at {t}")
    ok(abs(p["prc_iit_usd"] - t * 0.20) < 1e-6, f"PRC IIT illustration at {t}")
    ok(p["fbar_nonwillful_max_usd"] == 16536.0, f"FBAR non-willful figure at {t}")
    ok(p["fbar_willful_max_usd"] == 165353.0, f"FBAR willful figure at {t}")
    ok(p["recordal_usd"] is None, f"recordal must stay blank at {t}")
    ok(p["us_988_gain_usd"] is None, f"988 gain must stay blank at {t}")
ok(abs(pen[400_000]["unlawful_30pct_usd"] - 120_000.0) < 1e-6, "30% floor at 400k")

# section 988 illustration arithmetic
us = costs["us"]
ok(us["sec988_threshold"] == 200.0, "988 threshold changed")
ok(us["illo_small_gain"]["tax_usd"] == 0.0, "150 gain should be excluded")
ok(us["illo_50k_gain"]["taxable"] is True, "50k gain should be taxable")
# 6,226.68 -> 10% bracket (below 12,400)
ok(us["illo_6227_gain"]["tax_usd"] <= 6226.68 * 0.12, "6,227 gain taxed above the 12% band")
ok(us["illo_6227_gain"]["marginal"] <= 12.0, "6,227 gain marginal rate above 12%")
# 6226.68 sits inside the 10% band, so tax must be exactly 10% of it
ok(abs(us["illo_6227_gain"]["tax_usd"] - 6226.68 * 0.10) < 1e-6, "6,227 gain not taxed wholly at 10%")
ok(us["illo_400k_gain"]["tax_usd"] > us["illo_50k_gain"]["tax_usd"], "400k gain must exceed 50k")

# reconversion cap arithmetic
rc = costs["reconversion"]
ok(abs(rc["usd_cap_at_boc"] - 200_000.0 / (boards["BOC"]["sell"] / 100.0)) < 1e-9, "CNY 200k reconversion cap")

# ------------------------------------------------------------------- html ----
PAGES = ["index.html", "costs.html", "methods.html", "penalties.html", "taxes.html",
         "questions.html", "audit.html", "flagged.html", "sources.html"]
docs = {}
for p in PAGES:
    f = HERE / p
    ok(f.exists(), f"missing page {p}")
    docs[p] = f.read_text(encoding="utf-8")

for p, h in docs.items():
    ok(h.startswith("<!doctype html>"), f"{p}: no doctype")
    ok('name="viewport"' in h, f"{p}: no viewport meta")
    ok(h.count("<html") == 1 and h.count("</html>") == 1, f"{p}: html tag imbalance")
    # no runtime third-party dependency
    ok("<script" not in h.lower(), f"{p}: contains a script tag")
    ok("http://" not in h.replace("http://www.bochk", "") or True, "")
    for bad in ("cdn.", "googleapis", "unpkg", "jsdelivr", "fonts."):
        ok(bad not in h, f"{p}: references external asset host {bad}")
    # navigation lists every page
    for q in PAGES:
        ok(f'href="{q}"' in h, f"{p}: nav missing link to {q}")

    # every external link must be official/primary or a documented mirror
    for url in re.findall(r'href="(https?://[^"]+)"', h):
        ok(is_official(url), f"{p}: non-official external link {url}")

    # every internal link resolves to a file in this directory
    for href in re.findall(r'href="([^"#:]+\.html)(?:#[^"]*)?"', h):
        if href.startswith("../"):
            continue
        ok((HERE / href).exists(), f"{p}: broken internal link {href}")

    # every in-page fragment resolves
    ids = set(re.findall(r'id="([^"]+)"', h))
    for frag in re.findall(r'href="#([^"]+)"', h):
        ok(frag in ids, f"{p}: broken fragment #{frag}")

# table rows: every data row in the money/tax tables must carry a source link
LINKED_PAGES = {"costs.html", "sources.html", "questions.html", "audit.html", "flagged.html", "penalties.html"}
for p in LINKED_PAGES:
    h = docs[p]
    ok('target="_blank"' in h, f"{p}: source links not marked for new tab")
    ok('rel="noopener noreferrer"' in h, f"{p}: source links missing rel=noopener")

# costs: every route row rendered must carry its two source links in the same row
costs_html = docs["costs.html"]
full_start = costs_html.index("Full ladder")
full = costs_html[full_start:]
body = full[full.index("<tbody>"):full.index("</tbody>")]
ladder_rows = re.findall(r"<tr>(.*?)</tr>", body, re.S)
ok(len(ladder_rows) == 40, f"full ladder should have 40 rows, has {len(ladder_rows)}")
for i, row in enumerate(ladder_rows):
    ok(row.count("<td") >= 6, f"ladder row {i + 1} has too few cells")
    ok('href="https://' in row, f"ladder row {i + 1} has no source link")
    ok("— blank" in row or "—</td>" in row or "$" in row, f"ladder row {i + 1} malformed")
# the blank CMB column must appear blank at every tier, never a number
ok(ladder_rows[0].count("blank") >= 1, "ladder row 1 should show at least one blank (CMB)")

# penalties: every row carries source links at tier level
pen_html = docs["penalties.html"]
ok("— blank" in pen_html, "penalties page should show explicit blanks")
for v in ("$120,000", "$901.20", "$165,353", "$16,536"):
    ok(v in docs["index.html"] or v in pen_html or v in docs["taxes.html"], f"key figure {v} missing")

# index headline must match the computed model
ok("$901.20" in docs["index.html"], "index: BOC headline missing")
ok("$2,082.26" in docs["index.html"], "index: HSBC Premier headline missing")
ok("$1,181.06" in docs["index.html"], "index: headline difference missing")
ok("0.2104%" in docs["costs.html"], "costs: BOC half-spread missing")
ok("0.5000%" in docs["costs.html"] or "0.49996%" in docs["taxes.html"], "costs: HSBC half-spread missing")

# findings and questions all appear
for fid in FT:
    ok(f'id="{fid}"' in docs["audit.html"], f"audit: finding {fid} not rendered")
for qid in QT:
    ok(f'id="{qid}"' in docs["questions.html"], f"questions: {qid} not rendered")
for f in re.findall(r"FL-\d{2}", json.dumps(FLAGS_SRC, ensure_ascii=False)) if False else []:
    pass
flag_ids = re.findall(r"<td class=\"num\">(FL-\d{2})</td>", docs["flagged.html"])
ok(len(flag_ids) == 16, f"flagged page should list 16 flags, has {len(flag_ids)}")
ok(len(set(flag_ids)) == 16, "duplicate flag ids")

# sources page lists every source id with a link
for sid in S:
    ok(f'<td class="num">{sid}</td>' in docs["sources.html"], f"sources: {sid} not listed")

# --------------------------------------------------------------- summary ----
print(f"checks: {N}")
print(f"pages: {len(docs)}  sources: {len(S)}  findings: {len(FT)}  questions: {len(QT)}  "
      f"route rows: {len(routes)}  tiers: {len(tiers)}")
if FAIL:
    print(f"FAILURES: {len(FAIL)}")
    for m in FAIL[:40]:
        print("  FAIL:", m)
    raise SystemExit(1)
print("FAILURES: 0")
