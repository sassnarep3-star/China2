#!/usr/bin/env python3
"""Independent verifier for the unified dashboard.

Deliberately does NOT import build_site. It re-derives every figure from bracket
tables transcribed in the form an official source publishes them, then checks the
rendered HTML, the JSON and the CSV against those figures, checks that every
external link points at an official domain, and that every local link and
fragment resolves.
"""

import csv
import json
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FAIL = []
CHECKS = [0]


def ok(cond, msg):
    CHECKS[0] += 1
    if not cond:
        FAIL.append(msg)


# ---------------------------------------------------------------- constants
FX = 6.7168  # PBOC central parity 2026-11-06

# US 2026 single, transcribed as (bracket ceiling, rate, tax at bracket floor)
# exactly as Rev. Proc. 2025-32 Table 3 prints it.
US_CUM = [
    (12400, 0.10, 0.0),
    (50400, 0.12, 1240.0),
    (105700, 0.22, 5800.0),
    (201775, 0.24, 17966.0),
    (256225, 0.32, 41024.0),
    (640600, 0.35, 58448.0),
    (float("inf"), 0.37, 192979.25),
]
US_FLOORS = [0, 12400, 50400, 105700, 201775, 256225, 640600]
US_STD = 16100.0

# PRC comprehensive-income schedule: (annual ceiling CNY, rate)
PRC_CUM = [(36000, 0.03), (144000, 0.10), (300000, 0.20), (420000, 0.25),
           (660000, 0.30), (960000, 0.35), (float("inf"), 0.45)]
PRC_FLOORS = [0, 36000, 144000, 300000, 420000, 660000, 960000]
PRC_DEDUCTION = 60000.0

TIERS = list(range(10000, 400001, 10000))
PAGES = ["index.html", "costs.html", "matrix.html", "methods.html", "steps.html",
         "penalty.html", "taxes.html", "flagged.html", "sources.html", "audit.html",
         "summary.html"]

OFFICIAL = ("gov.cn", "govinfo.gov", "irs.gov", "cbp.gov", "fincen.gov", "treasury.gov",
            "pbc.gov.cn", "safe.gov.cn", "chinatax.gov.cn", "customs.gov.cn", "chinamoney.com.cn")
ALLOWED_NON_OFFICIAL = ("github.com",)


def us_tax_from_cumulative(taxable):
    """tax = tax_at_floor + rate * (taxable - floor)"""
    if taxable <= 0:
        return 0.0
    for (ceiling, rate, at_floor), floor in zip(US_CUM, US_FLOORS):
        if taxable <= ceiling:
            return at_floor + rate * (taxable - floor)
    return 0.0


def us_tax_walk(taxable):
    """Second implementation: add band by band."""
    if taxable <= 0:
        return 0.0
    tax = 0.0
    prev = 0.0
    for ceiling, rate in [(c, r) for c, r, _ in US_CUM]:
        if taxable > prev:
            tax += (min(taxable, ceiling) - prev) * rate
        prev = ceiling
    return tax


def prc_tax_walk(taxable):
    if taxable <= 0:
        return 0.0
    tax = 0.0
    prev = 0.0
    for ceiling, rate in PRC_CUM:
        if taxable > prev:
            tax += (min(taxable, ceiling) - prev) * rate
        prev = ceiling
    return tax


def expected(amount):
    us = us_tax_from_cumulative(max(0.0, amount - US_STD))
    labor = prc_tax_walk(max(0.0, amount * FX - PRC_DEDUCTION)) / FX
    flat = amount * 0.20
    return {
        "stat": 0.0, "labor": labor, "flat": flat, "us": us,
        "res_labor": max(0.0, us - min(min(labor, us), us)),
        "res_flat": max(0.0, us - min(flat, us)),
        "quota_years": math.ceil(amount / 50000),
        "atm_years": math.ceil(amount / (100000 / FX)),
    }


# ---------------------------------------------------------------- HTML helpers
class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []          # (href, attrs dict)
        self.ids = set()
        self.tables = 0
        self.captions = 0
        self.details = 0
        self.summaries = 0
        self.text = []
        self.tags = []
        self.stack = []
        self.unbalanced = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "table":
            self.tables += 1
        if tag == "caption":
            self.captions += 1
        if tag == "details":
            self.details += 1
        if tag == "summary":
            self.summaries += 1
        if tag not in ("meta", "link", "br", "img", "hr", "input", "source", "col", "area", "base", "wbr", "track", "param", "embed"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            # tolerate implicit closes in tables
            while self.stack and self.stack[-1] != tag:
                if self.stack[-1] not in ("p", "li", "td", "th", "tr", "thead", "tbody"):
                    self.unbalanced.append((tag, self.stack[-1]))
                self.stack.pop()
            if self.stack:
                self.stack.pop()

    def handle_data(self, data):
        self.text.append(data)


def parse(path):
    c = Collector()
    c.feed(path.read_text(encoding="utf-8"))
    c.plain = re.sub(r"\s+", " ", " ".join(c.text))
    return c


# ---------------------------------------------------------------- run
def main():
    for page in PAGES:
        p = ROOT / page
        ok(p.exists(), "missing page {}".format(page))
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        ok(len(html) > 3000, "{} looks empty".format(page))
        ok('name="viewport"' in html, "{} has no viewport meta".format(page))
        ok('charset="utf-8"' in html, "{} has no charset".format(page))
        ok("assets/site.css" in html, "{} does not link the stylesheet".format(page))
        ok('name="description"' in html, "{} has no meta description".format(page))
        ok("<h1" in html, "{} has no h1".format(page))
        ok(html.count("<title>") == 1, "{} title count".format(page))
        for bad in ("None</td>", ">nan<", "NaN", "TODO", "FIXME", "&lt;script", "undefined<"):
            ok(bad not in html, "{} contains suspicious token {!r}".format(page, bad))

        c = parse(p)
        ok(not c.unbalanced, "{} has unbalanced tags near {}".format(page, c.unbalanced[:3]))
        ok(c.tables >= 1 or page in ("steps.html", "summary.html"), "{} has no table".format(page))

        # every table must carry a caption for screen readers
        ok(c.captions >= c.tables or c.tables == 0,
           "{}: {} tables but {} captions".format(page, c.tables, c.captions))
        # details/summary pairing
        ok(c.details == c.summaries, "{}: {} details vs {} summaries".format(page, c.details, c.summaries))

        # external links must be official
        for href in c.links:
            if href.startswith(("http://", "https://")):
                host = (urlsplit(href).hostname or "").lower()
                official = any(host == d or host.endswith("." + d) for d in OFFICIAL)
                allowed = any(host == d or host.endswith("." + d) for d in ALLOWED_NON_OFFICIAL)
                ok(official or allowed,
                   "{}: non-official external link {}".format(page, href))
                ok(not href.startswith("http://") or "customs.gov.cn" in host,
                   "{}: insecure http link {}".format(page, href))

    # ------------------------------------------------ local links and fragments
    for page in PAGES:
        p = ROOT / page
        if not p.exists():
            continue
        c = parse(p)
        for href in c.links:
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if href.startswith("#"):
                ok(href[1:] in c.ids, "{}: missing anchor {}".format(page, href))
                continue
            target, _, frag = href.partition("#")
            tpath = (p.parent / target).resolve()
            ok(tpath.exists(), "{}: broken local link {}".format(page, href))
            if frag and tpath.exists() and tpath.suffix == ".html":
                tc = parse(tpath)
                ok(frag in tc.ids, "{}: broken fragment {} in {}".format(page, href, target))

    # ------------------------------------------------ cost table vs recomputation
    model = json.loads((ROOT / "data" / "cost-model.json").read_text())
    tiers = model["tiers"]
    ok(len(tiers) == 40, "cost-model tiers != 40")
    ok([t["amount_usd"] for t in tiers] == TIERS, "tier amounts wrong")
    for t in tiers:
        e = expected(t["amount_usd"])
        pairs = (("statutory_cost_usd", "stat", 0.01), ("prc_iit_labor_usd", "labor", 0.02),
                 ("prc_flat20_usd", "flat", 0.02), ("us_federal_tax_usd", "us", 0.02),
                 ("us_residual_labor_usd", "res_labor", 0.02),
                 ("us_residual_flat_usd", "res_flat", 0.02))
        for json_key, ek, tol in pairs:
            ok(abs(t[json_key] - e[ek]) <= tol,
               "tier {} {} = {} but recomputed {}".format(
                   t["amount_usd"], json_key, t[json_key], round(e[ek], 2)))
        ok(t["years_at_quota"] == e["quota_years"], "quota years {}".format(t["amount_usd"]))
        ok(t["years_at_atm_cap"] == e["atm_years"], "atm years {}".format(t["amount_usd"]))
        ok(t["commercial_cost_usd"] is None, "commercial cost must stay blank")

    # the two US implementations must agree
    for x in (0, 12400, 50400, 83900, 105700, 201775, 256225, 383900, 640600, 900000):
        ok(abs(us_tax_from_cumulative(x) - us_tax_walk(x)) < 0.02,
           "US bracket implementations disagree at {}".format(x))

    # rendered rows must carry the same figures
    costs_html = (ROOT / "costs.html").read_text()
    for t in tiers:
        a = t["amount_usd"]
        ok('<strong>${:,}</strong>'.format(a) in costs_html, "costs.html missing amount row ${:,}".format(a))
    for probe in ("$148,896", "$23,134", "$103,134", "$80,000"):
        ok(probe in costs_html or probe in (ROOT / "summary.html").read_text()
           or probe in (ROOT / "penalty.html").read_text(),
           "expected computed figure {} not rendered".format(probe))

    # ------------------------------------------------ CSV parity
    with (ROOT / "data" / "cost-tiers.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    ok(len(rows) == 40, "csv rows != 40")
    for row in rows:
        e = expected(int(row["amount_usd"]))
        ok(abs(float(row["B_prc_iit_labor_usd"]) - e["labor"]) < 0.02, "csv labor mismatch")
        ok(abs(float(row["us_federal_tax_usd"]) - e["us"]) < 0.02, "csv us mismatch")
        ok(row["commercial_cost_usd"] == "", "csv commercial cell must be blank")

    # ------------------------------------------------ matrix cells
    matrix = (ROOT / "matrix.html").read_text()
    for a in (10000, 100000, 400000):
        ok("${:,}".format(a) in matrix, "matrix missing ${:,}".format(a))
    ok(matrix.count('class="cell ym"') + matrix.count('class="cell y1"') > 100, "matrix cells missing")
    ok("unv" in matrix and "—" in matrix, "matrix legend values missing")

    # ------------------------------------------------ sources, methods, flags
    srcs = model["sources"]
    ok(len(srcs) == 22, "source count {}".format(len(srcs)))
    for s in srcs:
        host = (urlsplit(s["url"]).hostname or "").lower()
        ok(any(host == d or host.endswith("." + d) for d in OFFICIAL),
           "source {} not on an official domain: {}".format(s["id"], host))
        ok(s["status"] in ("V", "P"), "source status {}".format(s["id"]))
        ok(len(s["evidence"]) > 40, "source {} evidence too thin".format(s["id"]))

    methods = model["methods"]
    ok(len(methods) == 22, "method count {}".format(len(methods)))
    for m in methods:
        ok(bool(m["sources"]), "method {} has no source".format(m["id"]))
        for sid in m["sources"]:
            ok(sid in [s["id"] for s in srcs], "method {} cites unknown source {}".format(m["id"], sid))
        ok(m["legal_status"] in ("lawful", "lawful-conditional", "unlawful"),
           "method {} bad legal status".format(m["id"]))
    ok(sum(1 for m in methods if m["legal_status"] == "unlawful") == 5, "unlawful count")

    flags = model["flagged"]
    ok(len(flags) == 16, "flag count {}".format(len(flags)))
    for f in flags:
        ok(bool(f["sources"]), "flag {} has no source".format(f["id"]))
        ok(len(f["detail"]) > 80, "flag {} detail too thin".format(f["id"]))

    # ------------------------------------------------ prose counts match data
    idx = parse(ROOT / "index.html").plain
    ok("{:d} official sources".format(len(srcs)) in idx, "index source count prose drifts")
    ok("{:d} cost rows".format(len(tiers)) in idx, "index tier count prose drifts")
    ok("{:d} items flagged".format(len(flags)) in idx, "index flag count prose drifts")
    ok("{:d} lawful routes".format(sum(1 for m in methods if m["legal_status"] != "unlawful")) in
       parse(ROOT / "methods.html").plain, "methods page lawful count drifts")

    # ------------------------------------------------ citation coverage per table row
    for page in ("costs.html", "methods.html", "sources.html", "flagged.html", "audit.html",
                 "taxes.html", "penalty.html", "matrix.html"):
        html = (ROOT / page).read_text()
        rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
        data_rows = [r for r in rows if "<td" in r]
        ok(len(data_rows) > 0, "{} has no data rows".format(page))
        if page in ("costs.html", "methods.html", "penalty.html", "sources.html", "flagged.html", "audit.html"):
            uncited = 0
            for r in data_rows:
                if not re.search(r'href="https?://[^"]*(gov\.cn|govinfo\.gov|irs\.gov|cbp\.gov|fincen\.gov)', r):
                    uncited += 1
            ok(uncited == 0, "{}: {} rows without an official source link".format(page, uncited))

    # ------------------------------------------------ no commercial domains anywhere
    for page in PAGES:
        html = (ROOT / page).read_text()
        for bad in ("wise.com", "hsbc.com", "icbc.com"):
            ok(not re.search(r'href="https?://[^"]*' + re.escape(bad), html),
               "{} links to commercial domain {}".format(page, bad))

    print("checks: {}  failures: {}".format(CHECKS[0], len(FAIL)))
    for f in FAIL[:40]:
        print("  FAIL:", f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
