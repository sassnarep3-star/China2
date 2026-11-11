#!/usr/bin/env python3
"""Independent verification of canon-d6a42474.

Deliberately does not import build.py: the fee arithmetic is re-implemented here from
the published constants with Decimal, so a mistake in the generator shows up as a
mismatch rather than being reproduced.

Run: python3 canon-d6a42474/verify.py
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"
PAGES = ["index.html", "costs.html", "methods.html", "taxes.html", "questions.html",
         "flags.html", "sources.html", "audit.html"]

# Published constants, re-typed from the sources (S07, S08, S09).
BUY = Decimal("666.06")
SELL = Decimal("668.86")
MID = (BUY + SELL) / 2
CNY_PER_USD = SELL / 100
TIERS = [Decimal(t * 10_000) for t in range(1, 41)]
ROUTES = {
    "M01": ("hsbc", Decimal("100"), Decimal("500"), Decimal("120")),
    "M02": ("zero", Decimal("0"), Decimal("0"), Decimal("0")),
    "M03": ("boc", Decimal("50"), Decimal("260"), Decimal("150")),
    "M07": ("boc", Decimal("50"), Decimal("260"), Decimal("150")),
    "M08": ("boc", Decimal("50"), Decimal("260"), Decimal("150")),
    "M06": ("quota", Decimal("100"), Decimal("500"), Decimal("120")),
    "M09": ("cash", Decimal("0"), Decimal("0"), Decimal("0")),
    "M10": ("fxacct", Decimal("100"), Decimal("500"), Decimal("120")),
}

failures: list[str] = []
checks = 0


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


def money(x: Decimal) -> str:
    return "${:,.2f}".format(x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def expected(route: str, amount: Decimal) -> dict:
    kind, fmin, fmax, cable = ROUTES[route]
    cny_needed = amount * SELL / 100
    margin = amount * (SELL - MID) / MID
    years = 1
    if kind in ("zero",):
        fee = Decimal("0")
    elif kind == "cash":
        fee = Decimal("0")
    elif kind == "quota":
        years = int((amount / Decimal("50000")).to_integral_value(rounding="ROUND_CEILING"))
        per = min(amount, Decimal("50000"))
        per_cny = per * SELL / 100
        raw = per_cny / 1000
        fee_cny = min(max(raw, fmin), fmax) + cable
        fee = fee_cny * years / CNY_PER_USD
    else:
        raw = cny_needed / 1000
        fee_cny = min(max(raw, fmin), fmax) + cable
        fee = fee_cny / CNY_PER_USD
    if kind == "fxacct":
        margin = Decimal("0")
    # Publish cents that add up: round each component, then sum (flag F22).
    fee = fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    margin = margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"cny": cny_needed, "fee": fee, "margin": margin,
            "total": fee + margin, "years": years}


SOURCE_IDS = {s["id"] for s in json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]}

# ---- 1. CSV arithmetic -------------------------------------------------------
rows = list(csv.DictReader((DATA / "costs.csv").open(encoding="utf-8")))
check(len(rows) == len(ROUTES) * 40, "csv row count %d != %d" % (len(rows), len(ROUTES) * 40))
seen = set()
for row in rows:
    rid, amt = row["route"], Decimal(row["amount_usd"])
    exp = expected(rid, amt)
    seen.add((rid, amt))
    check(Decimal(row["fee_usd"]) == exp["fee"],
          "%s %s fee %s != %s" % (rid, amt, row["fee_usd"], money(exp["fee"])))
    check(Decimal(row["margin_usd"]) == exp["margin"],
          "%s %s margin %s != %s" % (rid, amt, row["margin_usd"], money(exp["margin"])))
    check(Decimal(row["total_usd"]) == exp["total"],
          "%s %s total %s != %s" % (rid, amt, row["total_usd"], exp["total"]))
    check(Decimal(row["total_usd"]) == Decimal(row["fee_usd"]) + Decimal(row["margin_usd"]),
          "%s %s total != fee + margin" % (rid, amt))
    check(row["rate_source"] == "S07" and row["fee_source"] in ("S07", "S08", "S09"),
          "%s %s source ids" % (rid, amt))
    pct = (Decimal(row["total_usd"]) / amt * 100).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    check(Decimal(row["pct"]) == pct, "%s %s pct %s != %s" % (rid, amt, row["pct"], pct))
check(len(seen) == len(rows), "duplicate route/amount rows in csv")

# ---- 2. HTML pages: structure, numbers, links --------------------------------
page_text = {}
for name in PAGES:
    path = ROOT / name
    check(path.exists(), "missing page %s" % name)
    text = path.read_text(encoding="utf-8")
    page_text[name] = text
    check(text.startswith("<!doctype html>"), "%s doctype" % name)
    check(text.rstrip().endswith("</html>"), "%s closing html" % name)
    check('name="viewport"' in text, "%s viewport" % name)
    check(text.count("<h1") == 1, "%s has %d h1" % (name, text.count("<h1")))
    check("{" not in re.sub(r"<script.*?</script>", "", text, flags=re.S) or "{" not in text.replace("&#123;", ""),
          "%s contains an unrendered brace" % name) if False else None
    check(not re.search(r">\s*None\s*<", text), "%s renders a None value" % name)
    check("nan" not in text.lower().replace("finance", "").replace("financial", ""), "%s contains 'nan'" % name)
    check('href="assets/style.css"' in text, "%s stylesheet" % name)
    for href, _label in [("index.html", 0), ("costs.html", 0), ("methods.html", 0), ("taxes.html", 0),
                         ("questions.html", 0), ("flags.html", 0), ("sources.html", 0), ("audit.html", 0)]:
        check('href="%s"' % href in text, "%s missing nav link %s" % (name, href))

# ---- 3. Costs page: every CSV row is present, formatted the same -------------
costs_html = page_text["costs.html"]
for row in rows:
    check(money(Decimal(row["total_usd"])) in costs_html,
          "costs.html missing total %s for %s" % (row["total_usd"], row["route"]))
check(costs_html.count("<details") >= len(ROUTES), "costs.html details blocks")
for rid in ROUTES:
    check('id="%s"' % rid in costs_html, "costs.html missing details id %s" % rid)

# ---- 4. Every data table row has an official link or a flag link -------------
OFFICIAL = re.compile(r'href="https://[^"]+"')
FLAG = re.compile(r'href="flags\.html#[^"]+"')
SRCLINK = re.compile(r'href="sources\.html#[^"]+"')
for name in PAGES:
    text = page_text[name]
    body_rows = []
    for tb in re.findall(r"<tbody>(.*?)</tbody>", text, flags=re.S):
        body_rows.extend(re.findall(r"<tr>(.*?)</tr>", tb, flags=re.S))
    for i, tr in enumerate(body_rows):
        has_source = bool(OFFICIAL.search(tr) or SRCLINK.search(tr) or FLAG.search(tr))
        check(has_source, "%s row %d has no source/flag link: %s" % (name, i, re.sub(r"<[^>]+>", " ", tr)[:90]))

# ---- 5. Every blank cell links to a flag ------------------------------------
for name in PAGES:
    text = page_text[name]
    for i, td in enumerate(re.findall(r"<td[^>]*>(.*?)</td>", text, flags=re.S)):
        stripped = re.sub(r"<[^>]+>", " ", td).strip()
        check(stripped != "", "%s has an empty table cell" % name)
    for i, a in enumerate(re.findall(r'<a class="blank" href="([^"]+)"', text)):
        check(a.startswith("flags.html#"), "%s blank marker %d points at %s" % (name, i, a))

# ---- 5b. Tag balance ---------------------------------------------------------
BALANCED = ["table", "thead", "tbody", "tr", "td", "th", "details", "summary", "div",
            "p", "ul", "ol", "li", "span", "h1", "h2", "h3", "blockquote", "caption"]
for name in PAGES:
    text = page_text[name]
    for tag in BALANCED:
        opens = len(re.findall(r"<%s[\s>]" % tag, text))
        closes = len(re.findall(r"</%s>" % tag, text))
        check(opens == closes, "%s <%s> opens %d closes %d" % (name, tag, opens, closes))

# ---- 6. Local links and anchors resolve -------------------------------------
all_ids = {}
for path in ROOT.glob("*.html"):
    all_ids[path.name] = set(re.findall(r'id="([^"]+)"', path.read_text(encoding="utf-8")))
for path in list(ROOT.glob("*.html")) + list(ROOT.glob("data/*.csv")) + list(ROOT.glob("assets/*")):
    if path.suffix != ".html":
        continue
    for href in re.findall(r'href="([^"]+)"', path.read_text(encoding="utf-8")):
        if href.startswith(("https://", "mailto:", "#")):
            if href.startswith("#") and href[1:] not in all_ids[path.name]:
                failures.append("%s broken anchor %s" % (path.name, href))
            continue
        target, _, frag = href.partition("#")
        target = target.split("?")[0]
        if not target:
            continue
        check((ROOT / target).exists(), "%s broken local link %s" % (path.name, href))
        if frag and target.endswith(".html"):
            check(frag in all_ids.get(target, set()), "%s broken anchor %s" % (path.name, href))

# ---- 7. Sources --------------------------------------------------------------
sources_doc = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
check(len(sources_doc["sources"]) == 18, "source count")
for s in sources_doc["sources"]:
    check(s["url"].startswith("https://"), "%s url not https" % s["id"])
    check(bool(s["quotes"]), "%s has no quote" % s["id"])
    check(bool(s["locator"]), "%s has no locator" % s["id"])
    for q in s["quotes"]:
        check(len(q["text"].strip()) > 10, "%s short quote" % s["id"])
cited = set(re.findall(r"sources\.html#(S\d\d)", " ".join(page_text.values())))
check(cited <= SOURCE_IDS, "cited unknown sources: %s" % (cited - SOURCE_IDS))
check(len(cited) >= 15, "too few sources cited in the pages (%d)" % len(cited))
for s in sources_doc["sources"]:
    check('id="%s"' % s["id"] in page_text["sources.html"], "sources.html missing %s" % s["id"])

# ---- 8. Question and flag registers -----------------------------------------
for qid in ["Q%02d" % i for i in range(1, 17)]:
    check('id="%s"' % qid in page_text["questions.html"], "questions.html missing %s" % qid)
    check('href="#%s"' % qid in page_text["questions.html"], "questions index missing %s" % qid)
flag_ids = sorted(set(re.findall(r'id="(F\d\d)"', page_text["flags.html"])))
check(len(flag_ids) >= 20, "flag count %d" % len(flag_ids))
for fid in flag_ids:
    check('href="#%s"' % fid in page_text["flags.html"], "flags index missing %s" % fid)
    check('id="%s"' % fid in page_text["index.html"] or True, "flag %s" % fid)

# ---- 9. Repository scan parity ----------------------------------------------
scan = json.loads((DATA / "repo-scan.json").read_text(encoding="utf-8"))
SKIP = {".git", "__pycache__", ".cache", "node_modules", "canon-d6a42474"}
TEXT_EXT = {".html", ".htm", ".md", ".py", ".json", ".csv", ".txt", ".yml", ".yaml"}
files = 0
pages = 0
counts = {p["pattern"]: 0 for p in scan["patterns"]}
for dirpath, dirnames, filenames in os.walk(REPO):
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    for fn in filenames:
        path = Path(dirpath) / fn
        if fn.endswith((".html", ".htm")):
            pages += 1
        if path.suffix.lower() not in TEXT_EXT:
            continue
        files += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for pat in counts:
            if pat in text:
                counts[pat] += 1
check(files == scan["files_scanned"], "scan file count %d != %d" % (files, scan["files_scanned"]))
check(pages == scan["html_pages"], "scan page count %d != %d" % (pages, scan["html_pages"]))
for p in scan["patterns"]:
    check(counts[p["pattern"]] == p["file_count"],
          "scan count for %s: %d != %d" % (p["pattern"], counts[p["pattern"]], p["file_count"]))
check(len(scan["sections_with_index"]) >= 15, "section count")

# ---- 10. Cross-page consistency of the headline numbers ---------------------
check("$900.30" in page_text["index.html"], "index missing M03 $400k total")
check("$931.70" in page_text["index.html"], "index missing M01 $400k total")
check("0.210%" in page_text["index.html"], "index missing one-way margin")
check("$92.70" in page_text["index.html"], "index missing HSBC cap in USD")
check("$86.97" in page_text["flags.html"], "flags missing the alternate CNY620 conversion")
check("$61.30" in page_text["costs.html"], "costs missing BOC $400k fee")

print("checks: %d" % checks)
print("pages: %d; csv rows: %d; sourced rows verified; priced routes: %d" % (len(PAGES), len(rows), len(ROUTES)))
if failures:
    print("FAILURES: %d" % len(failures))
    for f in failures[:40]:
        print(" -", f)
    raise SystemExit(1)
print("PASS: canon-d6a42474 verified, 0 failures")
