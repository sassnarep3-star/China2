#!/usr/bin/env python3
"""Independent checks for cny-usd-6869721b. Does not import build.py.

    PYTHONDONTWRITEBYTECODE=1 python3 cny-usd-6869721b/verify.py

What this proves: every input number is anchored in the quoted source text, the ladder
arithmetic reproduces from those inputs, every table row links to a registered official
source, and local links resolve. It does NOT prove that a quoted page still says the same
thing today, or that a rule applies to any one person.
"""
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
from html.parser import HTMLParser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = ["index.html", "costs.html", "methods.html", "tax.html", "review.html", "flagged.html", "sources.html"]
OFFICIAL = ("gov.cn", "boc.cn", "bankofchina.com", "icbc.com.cn", "abchina.com", "cmbchina.com", "ccb.com", "bankcomm.com", "psbc.com",
            "hsbc.com.cn", "wise.com", "chase.com", "bankofamerica.com", "schwab.com", "fidelity.com", "irs.gov", "govinfo.gov", "ecfr.gov", "cbp.gov")
checks = 0
fails = []


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def load(name):
    with open(os.path.join(HERE, "data", name), encoding="utf-8") as f:
        return json.load(f)


SRC, INP, CON, LAD = load("sources.json"), load("inputs.json"), load("content.json"), load("ladder.json")
S = {s["id"]: s for s in SRC["sources"]}
URLS = {s["url"] for s in SRC["sources"]}


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


# 1. source registry
ok(len(S) == len(SRC["sources"]), "duplicate source id")
for s in SRC["sources"]:
    ok(s["access"] in ("fetched", "excerpt"), f"{s['id']}: bad access")
    ok(urlparse(s["url"]).scheme in ("http", "https") and official(s["url"]), f"{s['id']}: not an official host: {s['url']}")
    ok(len(s["quote"].strip()) >= 15, f"{s['id']}: quote missing")
    ok(all(s.get(k) for k in ("publisher", "title", "as_of", "group")), f"{s['id']}: field missing")

# 2. every input number is anchored in the verbatim quote of its source
def anchored(src_id, anchor, value, label):
    ok(src_id in S and anchor in S[src_id]["quote"], f"{label}: anchor not in {src_id} quote: {anchor!r}")
    ok(str(value) in anchor, f"{label}: value {value!r} not in anchor {anchor!r}")


for k, r in INP["rates"].items():
    anchored(r["source"], r["anchor_buy"], r["buy"], f"rate {k} buy")
    anchored(r["source"], r["anchor_sell"], r["sell"], f"rate {k} sell")
    ok(F(r["buy"]) < F(r["sell"]), f"rate {k}: buy >= sell")
anchored(INP["parity"]["source"], INP["parity"]["anchor"], INP["parity"]["value"], "parity")
for y, v in INP["irs_avg"]["years"].items():
    anchored(INP["irs_avg"]["source"], v["anchor"], v["value"], f"IRS {y}")
for k, f in INP["wire_fees"].items():
    for fld, anc in (("permille", "anchor_rate"), ("min", "anchor_min"), ("max", "anchor_max"), ("cable", "anchor_cable")):
        val = f[fld]
        if fld == "permille":
            ok(f[anc] in S[f["source"]]["quote"], f"fee {k}: rate anchor missing")
            ok(any(t in f[anc] for t in ("1‰", "千分之一", "0.1%")), f"fee {k}: rate anchor is not 0.1%")
        else:
            anchored(f["source"], f[anc], val, f"fee {k} {fld}")
anchored("F1", INP["wire_fees"]["BOC"]["anchor_full"], INP["wire_fees"]["BOC"]["full_amount_usd"], "BOC full amount")
anchored("F4", INP["wire_fees"]["HSBC"]["anchor_pay_exact"], INP["wire_fees"]["HSBC"]["pay_exact_cny"], "HSBC pay exact")
a = INP["atm"]
for v in (a["per_wd_fixed"], a["per_wd_pct"], a["per_wd_max"]):
    anchored(a["source"], a["anchor"], v, "ATM fee")
anchored(a["limit_source"], a["anchor_day"], a["per_card_day_cny"] + "万元", "ATM day")
anchored(a["limit_source"], a["anchor_year"], a["per_person_year_cny"] + "万元", "ATM year")
c = INP["cash"]
anchored(c["source"], c["anchor_no_permit"], c["no_permit_usd"], "cash no permit")
anchored(c["source"], c["anchor_bank_permit"], c["bank_permit_usd"], "cash permit")
anchored(c["permit_fee_source"], c["anchor_permit_fee"], c["permit_fee_cny"], "permit fee")
anchored(c["us_source"], c["anchor_us"], c["us_report_usd"], "FinCEN 105")
anchored(INP["quota"]["source"], INP["quota"]["anchor"], INP["quota"]["usd_per_year"] + "万美元", "quota")
anchored(INP["emigrant"]["source"], INP["emigrant"]["anchor"], INP["emigrant"]["single_cap_cny"] + "万元", "emigrant cap")
r = INP["reconversion"]
anchored(r["source"], r["anchor"], r["id_only_usd_per_day"], "reconversion")
anchored(r["source"], r["anchor_airside"], r["airside_usd_per_day"], "reconversion airside")
anchored(r["source"], r["anchor_memo"], r["memo_months"], "memo months")
anchored(INP["wise"]["source"], INP["wise"]["anchor"], INP["wise"]["bank_app_cny"], "wise")
anchored(INP["wise"]["source"], INP["wise"]["anchor_alipay"], INP["wise"]["alipay_cny"], "wise alipay")
anchored(INP["wu"]["source"], INP["wu"]["anchor"], INP["wu"]["counter_usd"] + "万美元", "WU counter")
anchored(INP["wu"]["source"], INP["wu"]["anchor_online"], INP["wu"]["online_usd"], "WU online")
anchored(INP["rmb_cash"]["source"], INP["rmb_cash"]["anchor"], INP["rmb_cash"]["per_trip_cny"], "RMB cash")
u = INP["us"]
anchored(u["source"], u["anchor"], u["gain_threshold_usd"], "gain threshold")
for v in (u["fbar_nonwillful"], u["fbar_willful"]):
    ok(v in S[u["fbar_source"]]["quote"], f"FBAR {v} not in quote")
for v in (u["f8938_penalty"], u["f8938_more"]):
    ok("$" + v in S[u["f8938_source"]]["quote"], f"8938 {v} not in quote")
ok("$" + u["f3520_threshold"] in S[u["f3520_source"]]["quote"], "3520 threshold not in quote")

# 3. recompute the ladder with exact fractions
def _r2(x):
    # exact rounding of a Fraction to two decimals, halves away from zero
    neg = x < 0
    n = abs(x) * 100
    fl = n.numerator // n.denominator
    if n - fl >= F(1, 2):
        fl += 1
    return ("-" if neg and fl else "") + f"{fl // 100}.{fl % 100:02d}"


def ceil(x):
    return -((-x.numerator) // x.denominator)


def rate(k):
    b, s = F(INP["rates"][k]["buy"]) / 100, F(INP["rates"][k]["sell"]) / 100
    m = (b + s) / 2
    return s, (s - m) / m


def wire(k, usd):
    s, half = rate(k)
    f = INP["wire_fees"][k]
    yuan = usd * s
    fee = min(max(yuan * F(f["permille"]) / 1000, F(f["min"])), F(f["max"])) + F(f["cable"])
    return yuan, usd * half, fee, fee / s, usd * half + fee / s


rows = LAD["rows"]
amounts = list(range(INP["amounts_usd"]["start"], INP["amounts_usd"]["end"] + 1, INP["amounts_usd"]["step"]))
ok([x["amount"] for x in rows] == amounts and len(rows) == 40, "ladder amounts are not 40 steps of $10,000")
bs, _ = rate("BOC")
par = F(INP["parity"]["value"]) / 100
fh = INP["wire_fees"]["HSBC"]
quota = F(INP["quota"]["usd_per_year"]) * 10000
for x in rows:
    A = F(x["amount"])
    y, sp, fee, feeu, tot = wire("BOC", A)
    exp = {"boc_cny": _r2(y), "boc_spread": _r2(sp), "boc_fee_cny": _r2(fee), "boc_fee_usd": _r2(feeu), "boc_total": _r2(tot), "boc_pct": _r2(tot / A * 100),
           "boc_full_total": _r2(tot + F(INP["wire_fees"]["BOC"]["full_amount_usd"])), "cash_spread": _r2(sp)}
    y2, sp2, fee2, feeu2, tot2 = wire("ABC", A)
    exp.update({"abc_cny": _r2(y2), "abc_spread": _r2(sp2), "abc_fee_cny": _r2(fee2), "abc_fee_usd": _r2(feeu2), "abc_total": _r2(tot2), "abc_pct": _r2(tot2 / A * 100)})
    hf = min(max(A * par * F(fh["permille"]) / 1000, F(fh["min"])), F(fh["max"])) + F(fh["cable"])
    exp.update({"hsbc_fee_cny": _r2(hf), "hsbc_fee_usd": _r2(hf / par)})
    parts = [A] if y <= F(INP["emigrant"]["single_cap_cny"]) * 10000 else [A / 2, A / 4, A / 4]
    ok(sum(parts) == A, f"{x['amount']}: emigrant stages do not add up")
    exp.update({"emigrant_total": _r2(sum(wire("BOC", p)[4] for p in parts)), "emigrant_first": _r2(parts[0])})
    nfull, rem = int(A // quota), A - (A // quota) * quota
    exp["quota_total"] = _r2(nfull * wire("BOC", quota)[4] + (wire("BOC", rem)[4] if rem else 0))
    day = F(a["per_card_day_cny"]) * 10000
    full, last = int(y // day), y - (y // day) * day
    af = full * F(a["per_wd_max"]) + (min(F(a["per_wd_fixed"]) + last * F(a["per_wd_pct"]) / 100, F(a["per_wd_max"])) if last else 0)
    exp.update({"atm_fee_cny": _r2(af), "atm_fee_usd": _r2(af / bs)})
    for yr, v in INP["irs_avg"]["years"].items():
        exp["gain_" + yr] = _r2(A * (1 - bs / F(v["value"])))
    ints = {"emigrant_wires": len(parts), "emigrant_years": 0 if len(parts) == 1 else 2, "quota_years": ceil(A / quota),
            "atm_years": ceil(y / (F(a["per_person_year_cny"]) * 10000)), "atm_withdrawals": full + (1 if last else 0),
            "cash_trips_5k": ceil(A / F(c["no_permit_usd"])), "cash_trips_10k": ceil(A / F(c["bank_permit_usd"])),
            "recon_days": ceil(A / F(r["id_only_usd_per_day"])), "wise_transfers": ceil(y / F(INP["wise"]["bank_app_cny"].replace(",", ""))),
            "wu_counter": ceil(A / (F(INP["wu"]["counter_usd"]) * 10000)), "wu_online": ceil(A / F(INP["wu"]["online_usd"]))}
    for k, v in exp.items():
        ok(x[k] == v, f"ladder {x['amount']} {k}: file {x[k]} != recomputed {v}")
    for k, v in ints.items():
        ok(x[k] == v, f"ladder {x['amount']} {k}: file {x[k]} != recomputed {v}")
    ok(set(x) == set(exp) | set(ints) | {"amount"}, f"ladder {x['amount']}: unexpected or missing columns")

# 4. content integrity
def has_sources(items, label):
    for it in items:
        ok(it.get("sources") and all(i in S for i in it["sources"]), f"{label} {it.get('id', it.get('bank'))}: missing or unknown source")


for key in ("scenarios", "methods", "penalty_layers", "other_banks", "claims", "flags"):
    has_sources(CON[key], key)
for key in ("scenarios", "methods", "penalty_layers", "claims", "flags"):
    ids = [it["id"] for it in CON[key]]
    ok(len(ids) == len(set(ids)), f"{key}: duplicate id")
for m in CON["methods"]:
    if m["status"] == "unlawful":
        ok(not m["steps"] and not m["pros"], f"{m['id']}: unlawful route must not carry steps or advantages")
    else:
        ok(len(m["steps"]) >= 2 and m["pros"] and m["cons"], f"{m['id']}: steps, pros and cons required")
ok(len(CON["methods"]) >= 15, "fewer than 15 methods")
last = {x["amount"]: x for x in rows}
m1 = next(m for m in CON["methods"] if m["id"] == "M1")["cost"]
ok(f"{Decimal(last[10000]['boc_fee_cny']):,.2f}" in m1 and f"{Decimal(last[10000]['abc_fee_cny']):,.2f}" in m1, "M1 cost text does not match the ladder")
c04 = next(x for x in CON["claims"] if x["id"] == "C04")["finding"]
ok(_r2((F(fh["max"]) + F(fh["cable"])) / bs) in c04, "C04 dollar figure does not match the Bank of China rate")
p6 = next(x for x in CON["penalty_layers"] if x["id"] == "P6")["amount"]
ok(_r2((1 - bs / F(INP["irs_avg"]["years"]["2024"]["value"])) * 100) + "%" in p6, "P6 percentage does not match")
n_exc = sum(1 for s in SRC["sources"] if s["access"] == "excerpt")
fl17 = next(x for x in CON["flags"] if x["id"] == "FL17")["why"]
ok(f"{n_exc} of {len(S)}" in fl17, f"FL17 count is stale: {n_exc} of {len(S)}")

# 5. pages
class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.rows, self.h1, self.viewport, self.tables = [], set(), [], 0, False, []
        self._row, self._tb, self._text = None, False, []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "a" and d.get("href"):
            self.links.append(d["href"])
            if self._row is not None:
                self._row.append(d["href"])
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and d.get("name") == "viewport":
            self.viewport = True
        if tag == "tbody":
            self._tb = True
            self.tables.append(0)
        if tag == "tr" and self._tb:
            self._row = []

    def handle_endtag(self, tag):
        if tag == "tbody":
            self._tb = False
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self.tables[-1] += 1
            self._row = None

    def handle_data(self, data):
        self._text.append(data)


parsed = {}
for name in PAGES:
    path = os.path.join(HERE, name)
    ok(os.path.exists(path), f"{name}: missing")
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    p = P()
    p.feed(raw)
    parsed[name] = p
    text = " ".join(p._text)
    ok(p.h1 == 1, f"{name}: needs exactly one h1")
    ok(p.viewport, f"{name}: no viewport meta")
    ok(len(p.rows) > 0, f"{name}: no table rows")
    for bad in ("TODO", "lorem", "undefined", " None", "NaN", "{", "}"):
        ok(bad not in text, f"{name}: stray text {bad!r}")
    for i, row in enumerate(p.rows):
        ext = [h for h in row if h.startswith("http")]
        ok(any(official(h) for h in ext), f"{name}: table row {i + 1} has no official source link")
    for h in p.links:
        if h.startswith("http"):
            ok(h in URLS, f"{name}: external link not in the source registry: {h}")
            ok(official(h), f"{name}: external link is not an official host: {h}")
for name, p in parsed.items():
    for h in p.links:
        if h.startswith("http") or h.startswith("mailto:"):
            continue
        target, _, frag = h.partition("#")
        tname = target or name
        tpath = os.path.normpath(os.path.join(HERE, tname))
        ok(os.path.exists(tpath), f"{name}: broken local link {h}")
        if frag and tname in parsed:
            ok(frag in parsed[tname].ids, f"{name}: missing anchor {h}")
ok(os.path.exists(os.path.join(HERE, "assets", "style.css")), "stylesheet missing")
costs = parsed["costs.html"]
ok(sum(1 for n in costs.tables if n == 40) == 10, f"costs.html: expected 10 ladders of 40 rows, got {costs.tables}")
ok(sum(1 for n in parsed["tax.html"].tables if n == 40) == 1, "tax.html: gain ladder is not 40 rows")
ok(max(parsed["methods.html"].tables) >= len(CON["methods"]), "methods.html: summary table incomplete")
ok(len(parsed["flagged.html"].rows) == len(CON["flags"]), "flagged.html: row count != flags")
ok(len(parsed["review.html"].rows) >= len(CON["claims"]), "review.html: claims missing")
ok(len(parsed["sources.html"].rows) == len(S), "sources.html: row count != sources")


def money(v):
    return f"${Decimal(v):,.2f}"


with open(os.path.join(HERE, "costs.html"), encoding="utf-8") as f:
    costs_raw = f.read()
with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
    index_raw = f.read()
for x in rows:
    for k in ("boc_total", "abc_total", "hsbc_fee_usd", "emigrant_total", "quota_total", "atm_fee_usd"):
        ok(money(x[k]) in costs_raw, f"costs.html: {k} for {x['amount']} not shown ({money(x[k])})")
for k in ("boc_total", "abc_total"):
    ok(money(last[400000][k]) in index_raw and money(last[10000][k]) in index_raw, f"index.html: headline {k} missing")
with open(os.path.join(HERE, "EXECUTIVE_SUMMARY.md"), encoding="utf-8") as f:
    md = f.read()
ok(money(last[400000]["abc_total"]) in md and money(last[400000]["boc_total"]) in md, "EXECUTIVE_SUMMARY.md: headline figures missing")
for url in re.findall(r"\]\((https?://[^)]+)\)", md):
    ok(url in URLS, f"EXECUTIVE_SUMMARY.md: link not in registry: {url}")
blank_pages = [n for n in PAGES if 'class="blank"' in open(os.path.join(HERE, n), encoding="utf-8").read()]
ok(len(CON["flags"]) >= 20 and blank_pages, "blank cells exist but are not flagged")

print(f"cny-usd-6869721b verify: {checks} checks, {len(fails)} failures")
for m in fails[:40]:
    print("  FAIL", m)
sys.exit(1 if fails else 0)
