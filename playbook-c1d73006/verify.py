#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent checks for playbook-c1d73006.  Shares no code with model.py or build.py.

What it checks is structure and arithmetic: that every table row links an official
page, that blank cells are flagged, that links resolve, and that every cost equals
what the published numbers give when recomputed here from the quoted passages.
It cannot check that an official page still says today what it said when it was read,
or that a legal reading is right.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 playbook-c1d73006/verify.py
"""
import csv
import json
import re
import sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
PAGES = ["index.html", "summary.html", "route.html", "questions.html", "methods.html", "penalty.html", "costs.html",
         "review.html", "flagged.html", "sources.html"]
checks = 0
fails = []


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


SOURCES = json.loads((HERE / "data" / "sources.json").read_text(encoding="utf-8"))
SRC = {s["id"]: s for s in SOURCES}
QUOTE = {(s["id"], q["key"]): q["text"] for s in SOURCES for q in s["quotes"]}
OFFICIAL = {urlparse(s["url"]).netloc for s in SOURCES}

# ---------------------------------------------------------------- 1. the ledger
ok(len({s["id"] for s in SOURCES}) == len(SOURCES), "duplicate source id")
for s in SOURCES:
    ok(s["url"].startswith("https://"), "%s is not https" % s["id"])
    ok(re.fullmatch(r"\d{4}-\d{2}-\d{2}", s["retrieved"]) is not None, "%s has no retrieval date" % s["id"])
    ok(len(s["quotes"]) > 0, "%s has no passage" % s["id"])
    ok(len({q["key"] for q in s["quotes"]}) == len(s["quotes"]), "%s has duplicate passage keys" % s["id"])
    for q in s["quotes"]:
        ok(len(q["text"].strip()) >= 12 and q["locator"].strip() != "", "%s:%s is empty" % (s["id"], q["key"]))
        if s["lang"] == "zh":
            ok(bool(q.get("en")), "%s:%s has no English rendering" % (s["id"], q["key"]))

# every machine-readable input must be visible in the words of the passage it comes from
TIES = [("BANK-01", "usd_row", ["666.31", "669.12"]), ("BANK-04", "usd_row", ["6.7080734", "6.6413322"]),
        ("BANK-03", "tt", ["1‰", "50元", "260元", "150元"]), ("BANK-02", "tt_issuance", ["0.1%", "CNY100", "CNY500"]),
        ("BANK-02", "cable", ["CNY120"]), ("CN-FX-06", "art54", ["5万美元"]), ("CN-FX-06", "art89", ["5000美元", "1万美元"]),
        ("CN-FX-07", "annual_cap", ["RMB 100,000"]), ("CN-FX-07", "daily_cap", ["RMB 10,000"]), ("PROV-01", "per_transfer", ["300,000 CNY"]),
        ("CN-FX-01", "art45", ["30%"]), ("CN-FX-01", "art40", ["30%"]), ("CN-FX-01", "art42", ["20%"]),
        ("CN-TAX-05", "art32", ["万分之五"]), ("CN-TAX-05", "art64", ["百分之五十以上五倍以下"]),
        ("US-RPT-03", "nonwillful", ["16,536"]), ("US-RPT-03", "willful", ["165,353"]),
        ("US-FX-02", "china_row", ["6.6760"]), ("US-FX-01", "china_row", ["7.129"]), ("CN-TAX-01", "item2", ["15万元"])]
for sid, key, needles in TIES:
    for n in needles:
        ok(n in QUOTE[(sid, key)], "%s:%s does not contain %s" % (sid, key, n))


# ---------------------------------------------------------------- 2. recompute every cost from the passages
def nums(sid, key):
    return [F(x) for x in re.findall(r"\d+\.\d+", QUOTE[(sid, key)])]


b = nums("BANK-01", "usd_row")            # buy, cash buy, sell, cash sell, BOC conversion rate, per 100
BOC = {"buy": b[0] / 100, "sell": b[2] / 100, "pct": F(1, 1000), "min": F(50), "max": F(260), "cable": F(150)}
h = nums("BANK-04", "usd_row")            # sell cash, sell TT, buy TT, buy cash, per 1
HSBC = {"buy": h[2], "sell": h[1], "pct": F(1, 1000), "min": F(100), "max": F(500), "cable": F(120)}
for bank in (BOC, HSBC):
    bank["mid"] = (bank["buy"] + bank["sell"]) / 2
    bank["spread"] = (bank["sell"] - bank["mid"]) / bank["mid"]
REF = BOC["mid"]


def cents(x):
    q = x * 100
    n = int(q) if q == int(q) else int(q + F(1, 2)) if q - int(q) != F(1, 2) else int(q) + 1
    return "%d.%02d" % (n // 100, n % 100)


def wire(bank, amt):
    com = min(max(amt * bank["sell"] * bank["pct"], bank["min"]), bank["max"])
    return (com + bank["cable"]) / bank["sell"]


def ceil(x):
    return -(-x.numerator // x.denominator)


def expect(method, amt):
    r = {"boc_usd": None, "hsbc_usd": None, "count": None, "low_usd": None, "high_usd": None}
    a = F(amt)
    if method in ("L01", "L02", "L05", "L06", "L07"):
        r["boc_usd"], r["hsbc_usd"], r["count"] = cents(a * BOC["spread"] + wire(BOC, a)), cents(a * HSBC["spread"] + wire(HSBC, a)), 1
    elif method == "L03":
        r["boc_usd"], r["hsbc_usd"], r["count"] = cents(wire(BOC, a)), cents(wire(HSBC, a)), 1
    elif method == "L04":
        n = ceil(a / 50000)
        parts = [F(50000)] * (n - 1) + [a - 50000 * (n - 1)]
        r["boc_usd"] = cents(a * BOC["spread"] + sum(wire(BOC, p) for p in parts))
        r["hsbc_usd"] = cents(a * HSBC["spread"] + sum(wire(HSBC, p) for p in parts))
        r["count"] = n
    elif method == "L08":
        r["count"] = ceil(a * REF / 300000)
    elif method == "L09":
        r["count"] = 1
    elif method == "L10":
        r["count"] = ceil(a * REF / 100000)
    elif method == "L11":
        r["boc_usd"], r["hsbc_usd"], r["count"] = cents(a * BOC["spread"]), cents(a * HSBC["spread"]), ceil(a / 10000)
    elif method in ("U1", "U2"):
        r["low_usd"], r["high_usd"] = cents(a * F(30, 100)), cents(a)
    elif method == "U5":
        r["high_usd"] = cents(a * F(20, 100))
    return r


COSTS = json.loads((HERE / "data" / "costs.json").read_text(encoding="utf-8"))
METHODS = ["L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09", "L10", "L11", "L12", "U1", "U2", "U3", "U4", "U5"]
TIERS = [10000 * i for i in range(1, 41)]
ok([(r["method"], r["amount"]) for r in COSTS["rows"]] == [(m, a) for m in METHODS for a in TIERS], "cost rows are not 17 methods x 40 tiers in order")
for r in COSTS["rows"]:
    want = expect(r["method"], r["amount"])
    for k in want:
        ok(r[k] == want[k], "costs.json %s %d %s: %r, recomputed %r" % (r["method"], r["amount"], k, r[k], want[k]))
for key, bank in (("boc", BOC), ("hsbc", HSBC)):
    ok([x["amount"] for x in COSTS["breakdown"][key]] == TIERS, "breakdown tiers for %s" % key)
    for x in COSTS["breakdown"][key]:
        a = F(x["amount"])
        ok(x["total_usd"] == cents(a * bank["spread"] + wire(bank, a)), "breakdown total %s %d" % (key, x["amount"]))
        ok(x["spread_usd"] == cents(a * bank["spread"]), "breakdown margin %s %d" % (key, x["amount"]))
        ok(x["fees_usd"] == cents(wire(bank, a)), "breakdown fees %s %d" % (key, x["amount"]))
        ok(x["cny_needed"] == cents(a * bank["sell"]), "breakdown RMB %s %d" % (key, x["amount"]))
with open(HERE / "data" / "costs.csv", encoding="utf-8", newline="") as fh:
    rows = list(csv.DictReader(fh))
ok(len(rows) == 680, "costs.csv has %d rows" % len(rows))
for c, r in zip(rows, COSTS["rows"]):
    ok(c["method"] == r["method"] and int(c["amount_usd"]) == r["amount"] and c["bank_of_china_inputs_usd"] == (r["boc_usd"] or "")
       and c["hsbc_china_inputs_usd"] == (r["hsbc_usd"] or "") and c["fine_high_usd"] == (r["high_usd"] or ""), "costs.csv row %s %s" % (c["method"], c["amount_usd"]))
    ok(all(urlparse(u).netloc in OFFICIAL for u in c["source_urls"].split()) and c["source_urls"] != "", "costs.csv source %s %s" % (c["method"], c["amount_usd"]))


# ---------------------------------------------------------------- 3. the pages
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.rows, self.h1, self.meta, self.lang = set(), [], [], 0, False, None
        self.row, self.cell, self.text = None, None, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and a.get("name") == "viewport":
            self.meta = True
        if tag == "tr":
            self.row = {"cells": [], "links": [], "attrs": a}
        if tag == "td" and self.row is not None:
            self.cell = {"cls": a.get("class", ""), "label": a.get("data-label", ""), "links": [], "text": ""}
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
            if self.row is not None:
                self.row["links"].append(a["href"])
            if self.cell is not None:
                self.cell["links"].append(a["href"])

    def handle_data(self, data):
        self.text.append(data)
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.row["cells"].append(self.cell)
            self.cell = None
        if tag == "tr" and self.row is not None:
            if self.row["cells"]:
                self.rows.append(self.row)
            self.row = None


parsed = {}
for name in PAGES:
    p = Page()
    p.feed((HERE / name).read_text(encoding="utf-8"))
    parsed[name] = p
    ok(p.h1 == 1 and p.meta and p.lang == "en", "%s: needs one h1, a viewport and lang" % name)
    ok(not re.search(r"(?i)\b(todo|tbd|lorem|fixme)\b", " ".join(p.text)), "%s: placeholder text" % name)
total_rows = 0
for name, p in parsed.items():
    for i, row in enumerate(p.rows):
        total_rows += 1
        off = [u for u in row["links"] if u.startswith("https://") and urlparse(u).netloc in OFFICIAL]
        ok(len(off) > 0, "%s row %d has no link to an official page" % (name, i + 1))
        ok(row["cells"][-1]["cls"] == "src" and row["cells"][-1]["links"], "%s row %d: last cell is not a source cell" % (name, i + 1))
        for c in row["cells"]:
            if c["cls"] == "blank":
                ok(any(re.fullmatch(r"flagged\.html#FR-\d\d", u) for u in c["links"]), "%s row %d: blank cell without a flag" % (name, i + 1))
            elif c["cls"] != "src":
                ok(c["text"].strip() != "", "%s row %d: empty cell '%s' that is not marked blank" % (name, i + 1, c["label"]))
    for u in p.links:
        if u.startswith(("https://", "http://")):
            ok(u.startswith("https://"), "%s links %s over http" % (name, u))
            continue
        path, _, frag = u.partition("#")
        path = path.split("?")[0]
        target = name if path == "" else path
        ok((HERE / target).resolve().is_file(), "%s: link to missing file %s" % (name, u))
        if frag and target in parsed:
            ok(frag in parsed[target].ids, "%s: link to missing anchor %s" % (name, u))
flag_ids = {i for i in parsed["flagged.html"].ids if i.startswith("FR-")}
ok(len(flag_ids) == len(parsed["flagged.html"].rows) and len(flag_ids) >= 20, "flag rows and anchors differ")

# cost table on the page equals the model, cell by cell
ct = [r for r in parsed["costs.html"].rows if "data-m" in r["attrs"]]
ok(len(ct) == 680, "costs.html has %d method rows" % len(ct))


def money(text):
    m = re.findall(r"\$([\d,]+(?:\.\d\d)?)", text)
    return [x.replace(",", "") for x in m]


for row, r in zip(ct, COSTS["rows"]):
    ok(row["attrs"]["data-m"] == r["method"] and int(row["attrs"]["data-amt"]) == r["amount"], "costs.html row order")
    c1, c2 = row["cells"][1], row["cells"][2]
    if r["method"].startswith("U"):
        want = [x.split(".")[0] for x in (r["low_usd"], r["high_usd"]) if x]
        ok(money(c1["text"]) == want if want else c1["cls"] == "blank", "costs.html fine %s %d" % (r["method"], r["amount"]))
    else:
        ok(money(c1["text"]) == [r["boc_usd"]] if r["boc_usd"] else c1["cls"] == "blank", "costs.html BOC %s %d" % (r["method"], r["amount"]))
        ok(money(c2["text"]) == [r["hsbc_usd"]] if r["hsbc_usd"] else c2["cls"] == "blank", "costs.html HSBC %s %d" % (r["method"], r["amount"]))
bd = [r for r in parsed["costs.html"].rows if "data-bank" in r["attrs"]]
ok(len(bd) == 80, "costs.html has %d breakdown rows" % len(bd))

# passages on the sources page are the ledger, word for word
src_text = (HERE / "sources.html").read_text(encoding="utf-8")
import html as _h  # noqa: E402
for (sid, key), text in QUOTE.items():
    ok(("%s-%s" % (sid, key)) in parsed["sources.html"].ids, "sources.html lacks %s-%s" % (sid, key))
    ok(_h.escape(text) in src_text, "sources.html does not carry the words of %s:%s" % (sid, key))

# the headline numbers in the summary are the recomputed ones
for name in ("summary.html", "EXECUTIVE_SUMMARY.md", "index.html"):
    t = (HERE / name).read_text(encoding="utf-8")
    for amt, bank in ((100000, BOC), (100000, HSBC)):
        v = cents(F(amt) * bank["spread"] + wire(bank, F(amt)))
        ok("$" + format(float(v), ",.2f") in t, "%s lacks the recomputed figure $%s" % (name, v))

# unlawful routes carry no instructions
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402
for m in C.METHODS:
    ok((m["status"] == "unlawful") == (m["steps"] == []), "%s: steps and standing disagree" % m["id"])
    ok(all(tuple(p.split(":")) in QUOTE for p in m["src"]), "%s: unresolved source pointer" % m["id"])
ok([m["id"] for m in C.METHODS] == METHODS, "method list differs from the cost table")
ok(len(C.QUESTIONS) >= 20 and len(C.SITUATIONS) == 10 and len(C.LAYERS) == 12, "content counts changed")

print("verify playbook-c1d73006: %d checks, %d failures; %d table rows on %d pages, each with an official link; %d sources, %d passages"
      % (checks, len(fails), total_rows, len(PAGES), len(SOURCES), len(QUOTE)))
for f in fails[:40]:
    print("  FAIL", f)
sys.exit(1 if fails else 0)
