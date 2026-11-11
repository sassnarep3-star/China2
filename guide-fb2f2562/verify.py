#!/usr/bin/env python3
"""Independent checks for guide-fb2f2562. Exits non-zero on any failure.

1. Source ledger: https, official/primary publisher domain, read date, finding present.
2. Cost arithmetic recomputed here with plain floats from the ledger figures (not by importing model.py).
3. Blank rule: every None in costs.json is rendered as an empty, flagged cell; no blank cell carries a value.
4. Every table body row on every page links at least one official source URL from the ledger.
5. Every number of 3+ digits written in content.py appears in the ledger or is a computed parameter/tier.
6. Every [Sxx] reference resolves; every flag id referenced in content exists on flagged.html.
7. Every local link and #anchor resolves.
8. Repo-review snapshot is well formed.
"""
import json
import math
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as C  # noqa: E402

FAIL = []
N = [0]


def check(cond, msg):
    N[0] += 1
    if not cond:
        FAIL.append(msg)


SOURCES = json.load(open(os.path.join(HERE, "data", "sources.json"), encoding="utf-8"))
SRC = {s["id"]: s for s in SOURCES}
COSTS = json.load(open(os.path.join(HERE, "data", "costs.json"), encoding="utf-8"))
REVIEW = json.load(open(os.path.join(HERE, "data", "review.json"), encoding="utf-8"))
OFFICIAL = ("safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn", "boc.cn", "hsbc.com.cn", "wise.com",
            "irs.gov", "ecfr.gov", "govinfo.gov", "cbp.gov", "federalreserve.gov")

# 1. ledger -----------------------------------------------------------------------------------
check(len(SOURCES) == len(SRC), "duplicate source ids")
for s in SOURCES:
    u = urlparse(s["url"])
    check(u.scheme == "https", f"{s['id']} not https")
    check(any(u.hostname == d or u.hostname.endswith("." + d) for d in OFFICIAL), f"{s['id']} host {u.hostname} not on the official/primary list")
    check(s.get("read") == C.TODAY, f"{s['id']} read date")
    for k in ("title", "publisher", "locator", "finding"):
        check(bool(s.get(k)), f"{s['id']} missing {k}")

# 2. arithmetic --------------------------------------------------------------------------------
F = lambda sid, k: float(SRC[sid]["figures"][k])  # noqa: E731
bs, bb = F("S01", "usd_sell_tt_per100") / 100, F("S01", "usd_buy_tt_per100") / 100
hs, hb = F("S02", "usd_sell_tt"), F("S02", "usd_buy_tt")
fed = F("S06", "nov6")


def wire(t, sell, buy, pct, lo, hi, cable):
    base = t * sell
    fee = min(max(base * pct, lo), hi) + cable
    margin = t * (sell - (sell + buy) / 2) / sell
    return fee, fee / sell + margin, margin


tiers = COSTS["tiers"]
check(tiers == list(range(10000, 400001, 10000)), "tiers are not 10,000..400,000 step 10,000")
for i, t in enumerate(tiers):
    for mid, sell, buy, fee in (("M01", bs, bb, (F("S03", "pct"), F("S03", "min_cny"), F("S03", "max_cny"), F("S03", "cable_other_cny"))),
                                ("M02", hs, hb, (F("S04", "pct"), F("S04", "min_cny"), F("S04", "max_cny"), F("S04", "cable_cny")))):
        r = COSTS["rows"][mid][i]
        fcny, total, margin = wire(t, sell, buy, *fee)
        check(r["usd"] == t, f"{mid} tier order")
        check(abs(r["fee_cny"] - fcny) < 0.006, f"{mid} {t} fee {r['fee_cny']} vs {fcny:.4f}")
        check(abs(r["total_known_usd"] - total) < 0.011, f"{mid} {t} total {r['total_known_usd']} vs {total:.4f}")
        check(abs(r["margin_usd"] - margin) < 0.006, f"{mid} {t} margin")
        check(abs(r["gap_to_fed_usd"] - t * (sell - fed) / sell) < 0.006, f"{mid} {t} fed gap")
        check(r["intermediary_fee"] is None and r["receiving_fee"] is None, f"{mid} {t} unpublished fee not blank")
    r = COSTS["rows"]["M03"][i]
    check(abs(r["total_known_usd"] - t * (hs - (hs + hb) / 2) / hs) < 0.006 and r["fee_usd"] == 0, f"M03 {t}")
    r = COSTS["rows"]["M04"][i]
    check(r["transfers_bank_app"] == math.ceil(round(t * fed, 6) / F("S05", "per_transfer_bank_cny")), f"M04 {t} transfers")
    check(r["fee"] is None and r["rate"] is None, f"M04 {t} Wise fee must be blank")
    r = COSTS["rows"]["M06"][i]
    check(r["calendar_years"] == math.ceil(round(t * fed, 6) / F("S16", "annual_cny")), f"M06 {t} years")
    r = COSTS["rows"]["M07"][i]
    check(r["trips_no_permit"] == math.ceil(t / F("S17", "free_usd")), f"M07 {t} trips")
    check(COSTS["rows"]["U04"][i]["fine_serious_usd"] == round(t * F("S09", "fine_serious_max"), 2), f"U04 {t}")
    check(COSTS["rows"]["U02"][i]["fine_serious_usd"] is None, f"U02 {t} serious fine must be blank")
    g = COSTS["rows"]["USTAX"][i]
    check(abs(g["gain_if_basis_2025"] - (t - t * bs / F("S07", "y2025"))) < 0.006, f"USTAX {t}")
    check(g["tax_on_gain"] is None, f"USTAX {t} tax must be blank")
check(abs(COSTS["rows"]["M01"][-1]["fee_cny"] - 410) < 1e-9, "BOC cap CNY 410")
check(abs(COSTS["rows"]["M02"][-1]["fee_cny"] - 620) < 1e-9, "HSBC cap CNY 620")

# 3–4, 7. pages ----------------------------------------------------------------------------------
PAGES = ["index.html", "summary.html", "questions.html", "methods.html", "penalty.html", "costs.html",
         "review.html", "flagged.html", "sources.html"]
SRC_URLS = {s["url"] for s in SOURCES}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.rows = set(), [], []
        self.in_tbody = 0
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
            if self.row is not None:
                self.row["hrefs"].append(a["href"])
        if tag == "tbody":
            self.in_tbody += 1
        if tag == "tr" and self.in_tbody:
            self.row = {"hrefs": [], "cells": []}
        if tag in ("td", "th") and self.row is not None:
            self.cell = {"cls": a.get("class") or "", "text": ""}

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row["cells"].append(self.cell)
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.in_tbody -= 1

    def handle_data(self, d):
        if self.cell is not None:
            self.cell["text"] += d


parsed = {}
for p in PAGES:
    path = os.path.join(HERE, p)
    check(os.path.isfile(path), f"missing page {p}")
    pp = Page()
    pp.feed(open(path, encoding="utf-8").read())
    parsed[p] = pp
    check('name="viewport"' in open(path, encoding="utf-8").read(), f"{p} lacks viewport meta")
    for r in pp.rows:
        check(any(h in SRC_URLS for h in r["hrefs"]), f"{p}: table row without an official source link: {[c['text'][:40] for c in r['cells'][:2]]}")
        for c in r["cells"]:
            if "blank" in c["cls"].split():
                check(c["text"].strip() == "", f"{p}: blank cell carries a value")
blank_cells = sum(1 for r in parsed["costs.html"].rows for c in r["cells"] if "blank" in c["cls"].split())
nones = sum(1 for m in ("M01", "M02", "M03", "M04", "M05", "M06", "M07", "U01", "U02", "U03", "U04") for r in COSTS["rows"][m] for v in r.values() if v is None)
nones -= sum(1 for m in ("M01", "M02", "M03") for r in COSTS["rows"][m])  # intermediary + receiving share one cell
check(blank_cells == nones, f"costs.html blank cells {blank_cells} != None values {nones}")
for p, pp in parsed.items():
    for h in pp.links:
        if h.startswith(("http://", "https://", "mailto:")):
            check(not h.startswith("http://"), f"{p}: insecure link {h}")
            continue
        file, _, anchor = h.partition("#")
        target = os.path.normpath(os.path.join(HERE, file)) if file else os.path.join(HERE, p)
        check(os.path.exists(target), f"{p}: broken link {h}")
        check("?" not in h, f"{p}: query-string link {h}")
        if anchor and file.endswith(".html") or (anchor and not file):
            tp = os.path.basename(target)
            if tp in parsed:
                check(anchor in parsed[tp].ids, f"{p}: missing anchor {h}")

# 5. numbers in content come from the ledger or computed params ----------------------------------
allowed_text = json.dumps(SOURCES, ensure_ascii=False)
allowed = set(re.sub(",", "", x) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", allowed_text))
allowed |= {str(t) for t in tiers} | {"400000", "200", "2026", "2027", "2014", "2025", "2024", "1116", "114", "105", "3520", "8938", "2555", "988", "911", "6039"}
for v in COSTS["params"].values():
    allowed |= {str(v), f"{v:.2f}", f"{v:.0f}", f"{v:,.2f}".replace(",", "")}
ctext = open(os.path.join(HERE, "content.py"), encoding="utf-8").read()
for num in re.findall(r"(?<![\w.])\d[\d,]{2,}(?:\.\d+)?", ctext):
    n = num.replace(",", "").rstrip(".")
    check(n in allowed or n.rstrip("0").rstrip(".") in allowed, f"content.py number {num} not found in ledger or computed params")

# 6. references -----------------------------------------------------------------------------------
for m in C.METHODS + C.QUESTIONS + C.PENALTY + C.FLAGS:
    for sid in m["sources"]:
        check(sid in SRC, f"{m['id']} cites unknown {sid}")
for sid in re.findall(r"\b(S\d\d)\b", ctext):
    check(sid in SRC, f"content.py mentions unknown {sid}")
flag_ids = {f["id"] for f in C.FLAGS}
for fid in re.findall(r"flag (F-\d\d)", ctext):
    check(fid in flag_ids, f"content references missing flag {fid}")
for fid in flag_ids:
    check(fid in parsed["flagged.html"].ids, f"{fid} not on flagged.html")
check(len([m for m in C.METHODS if m["kind"] != "unlawful"]) >= 7, "lawful methods missing")
for m in C.METHODS:
    check(m["id"] in parsed["methods.html"].ids and f"c-{m['id']}" in parsed["costs.html"].ids, f"{m['id']} missing on pages")
    check(len(m["steps"]) >= 1 and len(m["cons"]) >= 1, f"{m['id']} lacks steps/cons")

# 8. review snapshot -------------------------------------------------------------------------------
rules = {r["id"] for r in REVIEW["rules"]}
check(len(rules) >= 9, "review rules")
for r in REVIEW["rules"]:
    for sid in r["sources"]:
        check(sid in SRC, f"rule {r['id']} cites unknown {sid}")
for x in REVIEW["findings"]:
    check(x["rule"] in rules and x["verdict"] in ("conflict", "check", "consistent", "corrected", "quoted"), "bad finding")
    check(not x["file"].startswith("guide-fb2f2562/"), "review scanned its own section")
    check(isinstance(x["line"], int) and x["line"] >= 1, "bad line number")
check(sum(REVIEW["totals"].values()) == len(REVIEW["findings"]), "review totals")
conf = sum(1 for x in REVIEW["findings"] if x["verdict"] == "conflict")
check(len([r for r in parsed["flagged.html"].rows if any("review.html#RA-" in h for h in r["hrefs"])]) == conf, "flagged.html must list every conflicting repo line")

# result -------------------------------------------------------------------------------------------
if FAIL:
    print(f"{len(FAIL)} of {N[0]} checks FAILED")
    for f in FAIL[:60]:
        print("  -", f)
    sys.exit(1)
print(f"guide-fb2f2562 verify: {N[0]} checks, 0 failures")
