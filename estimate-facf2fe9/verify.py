#!/usr/bin/env python3
"""Independent checks for estimate-facf2fe9. Does not import model.py or build.py.

1. Ledger: every source is on an official host and carries the words relied on.
2. Arithmetic: every cost cell is recomputed here from data/inputs.json with a
   separate float implementation and compared with data/costs.json.
3. Blank rule: a cell whose inputs were not read is blank, and its row is flagged.
4. Pages: every table row carries a direct link to an official host; every
   local link and fragment resolves; every page is mobile-ready.
These are structural and arithmetic checks. They do not certify the law.
"""
import csv
import json
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OFFICIAL = ("boc.cn", "icbc.com.cn", "ccb.com", "abchina.com", "cmbchina.com", "hsbc.com.cn", "bankcomm.com",
            "safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn", "irs.gov", "govinfo.gov", "ecfr.gov",
            "cbp.gov", "wise.com", "westernunion.com")
PAGES = ["index.html", "costs.html", "methods.html", "tax.html", "sources.html", "flagged.html", "repo-review.html"]
checks = 0
fails = []


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def load(n):
    with open(DATA / n, encoding="utf-8") as fh:
        return json.load(fh)


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in OFFICIAL)


sources = load("sources.json")["sources"]
inputs = load("inputs.json")
methods = load("methods.json")["methods"]
flags = load("flags.json")["flags"]
tax = load("tax.json")
costs = load("costs.json")
review = load("repo_review.json")["findings"]
scan = load("repo_scan.json")
SRC = {s["id"]: s for s in sources}
FL = {f["id"] for f in flags}

# ---- 1. ledger -------------------------------------------------------------
ok(len(SRC) == len(sources), "duplicate source id")
for s in sources:
    ok(urlparse(s["url"]).scheme in ("http", "https") and official(s["url"]), f"{s['id']}: not an official host: {s['url']}")
    if s["method"].startswith("not read"):
        ok(not s["quotes"], f"{s['id']}: unread source must carry no quote")
    else:
        ok(len(s["quotes"]) >= 1 and all(len(qt.strip()) >= 8 for qt in s["quotes"]), f"{s['id']}: missing words relied on")
        ok(bool(s["retrieved"]), f"{s['id']}: missing retrieval time")
for f in flags:
    ok(f["source"] in SRC, f"flag {f['id']}: unknown source")
    ok(len(f["detail"]) > 30, f"flag {f['id']}: no explanation")
for m in methods:
    ok(len(m["steps"]) >= 1 and len(m["pros"]) >= 1 and len(m["cons"]) >= 1, f"{m['id']}: steps/pros/cons missing")
    ok(all(i in SRC for i in m["sources"]) and m["sources"], f"{m['id']}: unknown or missing source")
    ok(all(i in FL for i in m["flags"]), f"{m['id']}: unknown flag")
for group in ("headline", "prc_by_source", "prc_procedure", "us_rules"):
    for row in tax[group]:
        ok(row["sources"] and all(i in SRC for i in row["sources"]), f"tax/{group}: row without source")
        ok(not row.get("flag") or row["flag"] in FL, f"tax/{group}: unknown flag")
        if row["status"] == "unverified":
            ok(row.get("tax", "") == "" and row.get("flag"), f"tax/{group}: unverified row must be blank and flagged")
for r in review:
    ok(r["sources"] and all(i in SRC for i in r["sources"]), f"{r['id']}: review finding without source")

# ---- 2. arithmetic, recomputed independently --------------------------------
boards = {}
for b in inputs["boards"]:
    if b["key"] == "HSBC":
        raw = b["raw_usd_per_cny"]
        boards["HSBC"] = (1 / raw["transfer_buying"], 1 / raw["transfer_selling"], 1 / raw["notes_selling"])
    else:
        boards[b["key"]] = (b["buy"], b["sell"], b.get("notes_sell"))
    if b["status"] == "verified":
        ok(b["buy"] < b["sell"], f"board {b['key']}: buy must be below sell")
        ok(6.0 < b["sell"] < 7.5, f"board {b['key']}: implausible rate")
    if b["status"] == "unverified":
        ok(b["buy"] is None and b["sell"] is None, f"board {b['key']}: unverified board must be blank")
ok(boards["HSBC"][0] < boards["HSBC"][1], "HSBC feed orientation: buy must be below sell after inversion")
ref = sum((boards[k][0] + boards[k][1]) / 2 for k in inputs["reference_banks"]) / len(inputs["reference_banks"])
ok(abs(ref - float(costs["meta"]["reference_mid"])) < 5e-7, "reference mid mismatch")
tariff = {t["key"]: t for t in inputs["tariffs"]}
for t in inputs["tariffs"]:
    filled = [t[k] is not None for k in ("pct", "min", "max", "cable")]
    ok(all(filled) if t["status"] == "verified" else not any(filled), f"tariff {t['key']}: status and figures disagree")
L = {k: v["value"] for k, v in inputs["limits"].items()}
for k, v in inputs["limits"].items():
    ok(v["source"] in SRC, f"limit {k}: unknown source")


def fee(tk, cny):
    t = tariff[tk]
    if t["pct"] is None:
        return None
    return min(t["max"], max(t["min"], cny * t["pct"])) + t["cable"]


def wires(bk, tk, parts):
    sell = boards[bk][1]
    if sell is None:
        return None
    spread = sum(p * (sell / ref - 1) for p in parts)
    fees = [fee(tk, p * sell) for p in parts]
    if any(f is None for f in fees):
        return {"spread": spread, "fee": None, "total": None, "cny": sum(p * sell for p in parts)}
    return {"spread": spread, "fee": sum(fees) / ref, "total": spread + sum(fees) / ref,
            "cny": sum(p * sell for p in parts) + sum(fees)}


def near(a, b, tol=0.011):
    return a is not None and b is not None and abs(float(a) - b) <= tol


rows = costs["rows"]
tiers = [10000 * i for i in range(1, 41)]
ok(costs["meta"]["tiers"] == tiers, "tiers must be 10,000 to 400,000 in steps of 10,000")
ok(len(rows) == len(methods) * 40, f"expected {len(methods) * 40} rows, found {len(rows)}")
BYM = {}
for r in rows:
    BYM.setdefault(r["method"], []).append(r)
for m in methods:
    rs = BYM.get(m["id"], [])
    ok([r["tier"] for r in rs] == tiers, f"{m['id']}: must have the 40 tiers in order")
    kind = m["cost_model"].split(":")
    for r in rs:
        x = r["tier"]
        exp = None
        if kind[0] == "wire":
            exp = wires(kind[1], kind[2], [x])
            ok(r["count"] == 1, f"{m['id']} {x}: one wire expected")
        elif kind[0] == "quota":
            n = math.ceil(x / L["annual_quota_usd"])
            exp = wires(kind[1], kind[2], [x / n] * n)
            ok(r["count"] == n, f"{m['id']} {x}: years")
        elif kind[0] == "emigrant":
            single = x * boards[kind[1]][1] <= L["emigrant_single_cny"]
            exp = wires(kind[1], kind[2], [x] if single else [x / 2, x / 4, x / 4])
            ok(r["count"] == (1 if single else 3), f"{m['id']} {x}: tranche count")
        if kind[0] in ("wire", "quota", "emigrant"):
            if exp is None:
                ok(r["status"] == "unverified" and all(r[k] is None for k in ("total_usd", "pct", "cny_needed", "spread_usd", "fee_usd")),
                   f"{m['id']} {x}: rate not read, every cost cell must be blank")
            elif exp["total"] is None:
                ok(r["status"] == "partial" and r["total_usd"] is None and r["pct"] is None and r["fee_usd"] is None,
                   f"{m['id']} {x}: fee not read, all-in must be blank")
                ok(near(r["spread_usd"], exp["spread"]), f"{m['id']} {x}: rate margin")
            else:
                ok(r["status"] == "estimated", f"{m['id']} {x}: status")
                ok(near(r["total_usd"], exp["total"]), f"{m['id']} {x}: all-in {r['total_usd']} vs {exp['total']:.2f}")
                ok(near(r["spread_usd"], exp["spread"]), f"{m['id']} {x}: rate margin")
                ok(near(r["fee_usd"], exp["fee"]), f"{m['id']} {x}: fees")
                ok(near(r["cny_needed"], exp["cny"], 0.011), f"{m['id']} {x}: renminbi needed")
                ok(near(r["pct"], exp["total"] / x * 100, 0.0006), f"{m['id']} {x}: percentage")
        elif kind[0] == "atm":
            ok(r["count"] == math.ceil(x * ref / L["atm_year_cny"]), f"{m['id']} {x}: years")
            ok(near(r["fee_usd"], x * L["cmb_atm_fee_pct"]) and r["total_usd"] is None, f"{m['id']} {x}: issuer fee only")
        elif kind[0] == "cash_usd":
            ok(r["count"] == math.ceil(x / L["cash_bank_permit_usd"]), f"{m['id']} {x}: trips")
            ok(f"{math.ceil(x / L['cash_no_permit_usd'])} trips without a permit" in r["note"], f"{m['id']} {x}: no-permit trips")
            ok(near(r["spread_usd"], x * (boards["BOC"][2] / ref - 1)) and r["total_usd"] is None, f"{m['id']} {x}: notes margin only")
        elif kind[0] == "cash_rmb":
            ok(r["count"] == math.ceil(x * ref / L["rmb_cash_trip_cny"]) and r["total_usd"] is None, f"{m['id']} {x}: trips")
        elif kind[0] == "count_only":
            ok(r["count"] == math.ceil(x * ref / L["wise_transfer_cny"]) and r["total_usd"] is None, f"{m['id']} {x}: transfers")
        elif kind[0] == "fee_only":
            ok(r["total_usd"] is None and r["spread_usd"] is None and r["fee_usd"] == "0.00", f"{m['id']} {x}: fee only")
        elif kind[0] == "blank":
            ok(all(r[k] is None for k in ("total_usd", "pct", "cny_needed", "spread_usd", "fee_usd", "count")), f"{m['id']} {x}: must be blank")
        elif kind[0] == "none":
            ok(r["total_usd"] == "0.00" and r["status"] == "no transaction", f"{m['id']} {x}: no transaction")
        elif kind[0] == "penalty":
            ok(r["total_usd"] is None and f"USD {round(x * L['fine_band_ordinary'])} (30%)" in r["note"]
               and f"USD {round(x * L['fine_band_serious'])} (100%)" in r["note"], f"{m['id']} {x}: fine bands")
        else:
            ok(False, f"{m['id']}: unknown cost model")
        # blank rule
        if r["status"] in ("partial", "unverified"):
            ok(r["total_usd"] is None and r["pct"] is None, f"{m['id']} {x}: unverified all-in must be blank")
            ok(len(m["flags"]) >= 1, f"{m['id']}: blank rows need a flag")
        if r["status"] == "estimated":
            ok(all(r[k] is not None for k in ("total_usd", "pct", "cny_needed", "spread_usd", "fee_usd")), f"{m['id']} {x}: estimated row incomplete")
# figures quoted in the prose must equal the model
last = {m: BYM[m][-1] for m in BYM}
ok(last["M16"]["count"] == 27 and last["M17"]["count"] == 40 and last["M18"]["count"] == 134 and last["M10"]["count"] == 8,
   "prose figures (27 years, 40 trips, 134 trips, 8 years) no longer match the model")
ok(abs(L["atm_year_cny"] / ref - 15000) < 100 and abs(L["rmb_cash_trip_cny"] / ref - 3000) < 50, "prose figures (about USD 15,000 / 3,000) drifted")
# exchange-gain illustration
sell = boards["BOC"][1]
for f in costs["fx_gain"]:
    avg = inputs["irs_yearly_avg_cny_per_usd"][f["year"]]
    share = 1 - sell / avg
    ok(near(f["per_10k"], 10000 * share, 0.51) and near(f["per_400k"], 400000 * share, 0.51) and near(f["gain_pct"], share * 100, 0.006),
       f"exchange gain {f['year']}")
ok([f["year"] for f in costs["fx_gain"]] == ["2021", "2022", "2023", "2024", "2025"], "exchange-gain years")

# ---- 3. export --------------------------------------------------------------
with open(HERE / "exports" / "costs.csv", encoding="utf-8", newline="") as fh:
    recs = list(csv.DictReader(fh))
ok(len(recs) == len(rows), "CSV row count")
for rec, r in zip(recs, rows):
    ok(rec["method_id"] == r["method"] and int(rec["amount_usd"]) == r["tier"] and rec["all_in_cost_usd"] == (r["total_usd"] or ""),
       f"CSV row {rec['method_id']} {rec['amount_usd']}")
    ok(all(official(u) for u in rec["source_urls"].split()) and rec["source_urls"], f"CSV row {rec['method_id']}: source link")


# ---- 4. pages ----------------------------------------------------------------
class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.hrefs, self.rows, self.meta, self.lang = set(), [], [], {}, ""
        self.in_tbody = self.in_tr = False
        self.cur = None
        self.h1 = self.title = 0
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "meta" and "name" in a:
            self.meta[a["name"]] = a.get("content", "")
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.title += 1
        if tag == "script":
            self.scripts.append(a.get("src", ""))
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.cur = {"links": [], "cells": 0, "blank": 0, "flag": 0, "text": ""}
        if tag in ("td", "th") and self.in_tr:
            self.cur["cells"] += 1
            if "blank" in a.get("class", "").split():
                self.cur["blank"] += 1
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
            if self.in_tr:
                self.cur["links"].append(a["href"])
                if "flag" in a.get("class", "").split():
                    self.cur["flag"] += 1

    def handle_data(self, data):
        if self.in_tr:
            self.cur["text"] += data

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_tr:
            self.rows.append(self.cur)
            self.in_tr = False
        if tag == "tbody":
            self.in_tbody = False


parsed = {}
for name in PAGES:
    text = (HERE / name).read_text(encoding="utf-8")
    p = P()
    p.feed(text)
    parsed[name] = p
    ok(p.lang == "en" and "width=device-width" in p.meta.get("viewport", "") and p.h1 == 1 and p.title == 1, f"{name}: page shell")
    ok(len(p.meta.get("description", "")) > 40, f"{name}: description")
    visible = re.sub(r"<[^>]+>", " ", re.sub(r"<code>.*?</code>", " ", text, flags=re.S))
    ok("{" not in visible and "}" not in visible, f"{name}: stray template brace")
    ok(re.search(r"\bNone\b", visible) is None, f"{name}: literal None on page")
    ok(len(p.rows) > 0, f"{name}: no table rows")
    for i, row in enumerate(p.rows):
        direct = any(h.startswith("http") and official(h) for h in row["links"])
        # rows about the repository itself (housekeeping) cite the file or pull request on GitHub
        house = name == "repo-review.html" and row["text"].lstrip().startswith("RH") and any(
            (urlparse(h).hostname or "") == "github.com" for h in row["links"])
        ok(direct or house, f"{name}: table row {i + 1} has no direct official source link")
total_rows = sum(len(p.rows) for p in parsed.values())
for name, p in parsed.items():
    for h in p.hrefs:
        if h.startswith(("http://", "https://")):
            host = (urlparse(h).hostname or "").lower()
            ok(official(h) or host == "github.com", f"{name}: external link to an unlisted host {h}")
            continue
        path, _, frag = h.partition("#")
        target = name if path == "" else path
        tp = (HERE / target).resolve()
        ok(tp.exists(), f"{name}: broken local link {h}")
        if frag and target in parsed:
            ok(frag in parsed[target].ids, f"{name}: missing anchor {h}")
    for s in p.scripts:
        ok((HERE / s).exists(), f"{name}: missing script {s}")
ok((HERE / "assets" / "style.css").exists(), "stylesheet missing")
# ladder rows on the costs page: 40 per method, blanks flagged
cp = parsed["costs.html"]
ok(sum(1 for r in cp.rows if r["cells"] == 9) == len(rows), "costs.html: one 9-cell row per method and tier expected")
for i, r in enumerate(cp.rows):
    if r["cells"] == 9 and ("Part published" in r["text"] or "Unverified" in r["text"]):
        ok(r["blank"] >= 2 and r["flag"] >= 1, f"costs.html row {i + 1}: blank cells must be marked and flagged")
    if r["cells"] == 9 and "Estimated" in r["text"]:
        ok(r["blank"] == 0, f"costs.html row {i + 1}: estimated row shows a blank")
flagged_page = parsed["flagged.html"]
ok(all(f in flagged_page.ids for f in FL), "flagged.html: every flag needs an anchor")
ok(all(s in parsed["sources.html"].ids for s in SRC), "sources.html: every source needs an anchor")
ok(all(m["id"] in parsed["methods.html"].ids and m["id"] in cp.ids for m in methods), "method anchors")

print(f"estimate-facf2fe9 verify: {checks} checks, {len(fails)} failures; {len(sources)} sources, "
      f"{len(methods)} methods, {len(rows)} cost rows, {total_rows} table rows on {len(PAGES)} pages")
for f in fails[:60]:
    print("FAIL:", f)
sys.exit(1 if fails else 0)
