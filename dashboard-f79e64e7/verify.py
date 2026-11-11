#!/usr/bin/env python3
"""Independent checks for dashboard-f79e64e7. Structural and arithmetic only:
they show the pages are consistent with the recorded inputs, not that the law is right.

    PYTHONDONTWRITEBYTECODE=1 python3 dashboard-f79e64e7/verify.py
"""
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

HERE = Path(__file__).resolve().parent
PAGES = ["index.html", "questions.html", "methods.html", "costs.html", "taxes.html",
         "sources.html", "flagged.html", "repo-review.html"]
OFFICIAL = ("safe.gov.cn", "gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "irs.gov", "ecfr.gov", "cbp.gov",
            "govinfo.gov", "boc.cn", "hsbc.com.cn", "wise.com")
HTTP_OK = {"m.safe.gov.cn"}          # SAFE's mobile host is served over http only
checks, fails = 0, []


def check(ok, msg):
    global checks
    checks += 1
    if not ok:
        fails.append(msg)


def official(url):
    u = urlsplit(url)
    host = (u.hostname or "").lower()
    if u.scheme != "https" and host not in HTTP_OK:
        return False
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.rows, self.h1, self.viewport = set(), [], [], 0, False
        self._row, self.text = None, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag == "tr":
            self._row = {"td": 0, "links": [], "text": []}
        if tag == "td" and self._row is not None:
            self._row["td"] += 1
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self._row is not None:
                self._row["links"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self._row is not None:
            if self._row["td"]:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        self.text.append(data)
        if self._row is not None:
            self._row["text"].append(data)


# 1. build is deterministic and the committed output is current
def digest():
    h = hashlib.sha256()
    for p in sorted(HERE.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(p.relative_to(HERE).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


before = digest()
subprocess.run([sys.executable, str(HERE / "build.py")], check=True, capture_output=True,
               env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
check(before == digest(), "build output differs from committed files (run build.py and commit)")

sources = json.loads((HERE / "data/sources.json").read_text())
methods = json.loads((HERE / "data/methods.json").read_text())
inputs = json.loads((HERE / "data/inputs.json").read_text())
costs = json.loads((HERE / "exports/costs.json").read_text())
SRC = {s["id"]: s for s in sources}

# 2. source ledger
used = set()
for name in ("methods", "layers", "questions", "flags", "review"):
    for r in json.loads((HERE / f"data/{name}.json").read_text()):
        check(bool(r["src"]), f"{name} {r['id']}: no source")
        for i in r["src"]:
            check(i in SRC, f"{name} {r['id']}: unknown source {i}")
            used.add(i)
for s in sources:
    check(official(s["url"]), f"{s['id']}: not an official host: {s['url']}")
    check(len(s["quote"]) >= 20 and len(s["means"]) >= 20, f"{s['id']}: quote or meaning missing")
    check(s["how"] in ("fetched", "partial"), f"{s['id']}: bad read method")
    check(s["id"] in used, f"{s['id']}: never cited")
check(len({s["url"] for s in sources}) == len(sources), "duplicate source URL")

# 3. pages: one h1, viewport, every data row has an official link, local links resolve, no leaks
docs = {}
for name in PAGES:
    d = Doc()
    d.feed((HERE / name).read_text(encoding="utf-8"))
    docs[name] = d
total_rows = 0
for name, d in docs.items():
    check(d.h1 == 1, f"{name}: expected one h1")
    check(d.viewport, f"{name}: no viewport meta")
    for i, row in enumerate(d.rows):
        total_rows += 1
        check(any(official(h) for h in row["links"]), f"{name}: row {i} has no official source link")
        for h in row["links"]:
            if h.startswith("http"):
                check(official(h), f"{name}: row {i} links to a non-official host {h}")
    text = "".join(d.text)
    raw = (HERE / name).read_text(encoding="utf-8")
    for bad in ("TODO", "FIXME", "{", "}"):
        check(bad not in text, f"{name}: leaked token {bad!r}")
    for pat in (r">\s*None\s*<", r"\bnan\b", r"\bundefined\b", r"\$None", r"¥None"):
        check(not re.search(pat, raw), f"{name}: leaked token {pat!r}")
    for h in d.links:
        if h.startswith(("http://", "https://", "mailto:")):
            continue
        path, _, frag = h.partition("#")
        target = (HERE / unquote(path)).resolve() if path else (HERE / name)
        check(target.exists(), f"{name}: broken local link {h}")
        if frag and target.suffix == ".html" and target.parent == HERE:
            check(frag in docs[target.name].ids, f"{name}: broken fragment {h}")

# 4. cost rows recomputed independently with exact fractions
SELL, BUY = F(inputs["BOC_SELL"]), F(inputs["BOC_BUY"])
HALF = SELL - (SELL + BUY) / 2
check(HALF == F("0.01405"), "half-gap is not 0.01405")


def cents(x):
    return float(math.floor(x * 100 + F(1, 2)) / 100)          # round half up, x >= 0


def boc(usd):
    c = min(max(usd * SELL * F(inputs["BOC_PCT"]), F(inputs["BOC_MIN"])), F(inputs["BOC_MAX"]))
    return c + F(inputs["BOC_CABLE"])


def expect(model, usd):
    """Return (est_cost_usd, rmb_in) or (None, None) when the route has no published price."""
    def wired(parts):
        fee = sum(boc(p) for p in parts)
        return cents((usd * HALF + fee) / SELL), cents(usd * SELL + fee)
    if model in ("one_wire", "reconvert"):
        return wired([usd])
    if model == "quota_wires":
        n = math.ceil(usd / inputs["QUOTA_USD"])
        return wired([F(inputs["QUOTA_USD"])] * (n - 1) + [usd - inputs["QUOTA_USD"] * (n - 1)])
    if model == "cash":
        return cents(usd * HALF / SELL), cents(usd * SELL)
    if model == "dividend":
        return cents(usd / 9), cents(usd / F("0.9") * SELL)
    if model == "stay":
        return 0.0, None
    return None, None


by = {}
for r in costs:
    by.setdefault(r["method"], []).append(r)
check(len(costs) == len(methods) * 40, f"expected {len(methods) * 40} cost rows, got {len(costs)}")
for m in methods:
    rows = by.get(m["id"], [])
    check([r["usd"] for r in rows] == list(range(10000, 400001, 10000)), f"{m['id']}: tiers are not $10k..$400k")
    for r in rows:
        usd = F(r["usd"])
        est, rmb = expect(m["model"], usd)
        got = None if r["est_cost_usd"] is None else float(r["est_cost_usd"])
        check(got == est, f"{m['id']} ${r['usd']}: cost {got} != {est}")
        got_rmb = None if r["rmb_in"] is None else float(r["rmb_in"])
        check(got_rmb == rmb, f"{m['id']} ${r['usd']}: RMB {got_rmb} != {rmb}")
        if m["model"] == "fine":
            check(float(r["fine_ordinary_max_usd"]) == cents(usd * F(inputs["FINE_ORDINARY"]))
                  and float(r["fine_serious_max_usd"]) == cents(usd * F(inputs["FINE_SERIOUS"])),
                  f"{m['id']} ${r['usd']}: fine exposure wrong")
        if m["model"] in ("hsbc_fee", "wise", "atm", "blank", "fine"):
            check(r["est_cost_usd"] is None and r["pct"] is None, f"{m['id']}: unpublished total must be blank")
        check(bool(r["source_urls"]) and all(official(u) for u in r["source_urls"].split()),
              f"{m['id']} ${r['usd']}: export row lacks official sources")
        if m["model"] == "atm":
            check(r["time"].startswith(str(math.ceil(usd * SELL / inputs["ATM_YEAR_CNY"])) + " "), f"{m['id']}: ATM years")
        if m["model"] == "wise":
            check(r["count"].startswith(str(math.ceil(usd * SELL / inputs["WISE_PER_TRANSFER_CNY"])) + " "), f"{m['id']}: Wise count")

# 5. CSV matches JSON
with (HERE / "exports/costs.csv").open(newline="", encoding="utf-8") as fh:
    crow = list(csv.DictReader(fh))
check(len(crow) == len(costs), "CSV row count differs from JSON")
for a, b in zip(crow, costs):
    check(a["usd"] == str(b["usd"]) and a["method"] == b["method"]
          and a["est_cost_usd"] == ("" if b["est_cost_usd"] is None else str(b["est_cost_usd"])), "CSV/JSON mismatch")

# 6. headline figures on the pages come from the ledger
idx = (HERE / "index.html").read_text(encoding="utf-8")
m01 = by["M01"]
for r in (m01[0], m01[9], m01[39]):
    check(f"${float(r['est_cost_usd']):,.2f}" in idx, f"index.html lacks M01 ${r['usd']} figure")
check(f"¥{inputs['BOC_SELL']}" in idx, "index.html lacks the posted rate")
check(len(docs["flagged.html"].rows) == len(json.loads((HERE / "data/flags.json").read_text())), "flag rows differ from ledger")

print(f"{checks} checks, {len(fails)} failures; {total_rows} table rows on {len(PAGES)} pages")
for f in fails[:40]:
    print("FAIL:", f)
sys.exit(1 if fails else 0)
