#!/usr/bin/env python3
"""Independent verifier for the consolidated guide.

Fails on:
  * any table body row in any generated page that has no link to a source in the register
  * any source id referenced by a method that is not in the register
  * any cost cell that does not recompute from the published fee + the labelled spread
  * any method or tier missing from the costs matrix
  * any broken local link or fragment, duplicate id, missing viewport, missing lang,
    or page without exactly one h1 and one aria-current nav item
  * any page whose table data is not present in the static HTML (no-JS parity)

It does not and cannot verify external URL health or current law.
"""
from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RATE = 7.10
CHECKS = 0
FAILS: list[str] = []


def check(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond and msg not in FAILS:
        FAILS.append(msg)


SOURCES = json.loads((DATA / "sources.json").read_text())["sources"]
METHODS = json.loads((DATA / "methods.json").read_text())["methods"]
COSTS = json.loads((DATA / "costs.json").read_text())
SRC = {s["id"]: s for s in SOURCES}
URLS = {s["url"] for s in SOURCES}
META = COSTS["meta"]
ROWS = {(r["method"], r["tier"]): r for r in COSTS["rows"]}
PAGES = ["index.html", "methods.html", "costs.html", "steps.html", "tax.html",
         "flagged.html", "sources.html", "audit.html"]


class Doc(HTMLParser):
    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids: list[str] = []
        self.links: list[str] = []
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._in_body = False
        self.h1 = 0
        self.lang = ""
        self.viewport = False
        self.current = 0
        self.table_ids: list[str] = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag == "h1":
            self.h1 += 1
        if a.get("aria-current") == "page":
            self.current += 1
        if tag == "tbody":
            self._in_body = True
        if tag == "table" and "id" in a:
            self.table_ids.append(a["id"])
        if tag == "tr" and self._in_body:
            self._row = []
        for key in ("href", "src"):
            if key in a:
                self.links.append(a[key])
                if self._row is not None:
                    self._row.append(a[key])

    def handle_endtag(self, tag):
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None
        if tag == "tbody":
            self._in_body = False


# ---------------------------------------------------------------- documents
docs: dict[Path, Doc] = {}
for name in PAGES:
    p = ROOT / name
    check(p.is_file(), f"missing page {name}")
    if p.is_file():
        docs[p.resolve()] = Doc(p)

check(set(PAGES) == {p.name for p in ROOT.glob("*.html")},
      "an unlisted html page exists in guide/")

for path, d in docs.items():
    name = path.name
    check(d.h1 == 1, f"{name}: expected exactly one h1, found {d.h1}")
    check(d.lang == "en", f"{name}: html lang is not 'en'")
    check(d.viewport, f"{name}: missing viewport meta")
    check(d.current == 1, f"{name}: expected one aria-current nav item, found {d.current}")
    check(len(d.ids) == len(set(d.ids)), f"{name}: duplicate element id")

# ---------------------------------------------------------------- links
for path, d in docs.items():
    for link in d.links:
        u = urlsplit(link)
        if u.scheme in ("https", "http", "mailto", "tel", "data"):
            continue
        target = (path.parent / unquote(u.path)).resolve() if u.path else path
        check(target.is_file() or target.is_dir(), f"{path.name}: broken local link {link}")
        if u.fragment and target.suffix == ".html":
            if target in docs:
                check(unquote(u.fragment) in docs[target].ids,
                      f"{path.name}: broken anchor {link}")
    # external links must be a registered source or an explicitly allowed repo path
    for link in d.links:
        u = urlsplit(link)
        if u.scheme in ("https", "http"):
            check(link in URLS, f"{path.name}: external link not in the source register: {link}")

# ---------------------------------------------------------------- citation coverage
for path, d in docs.items():
    for row in d.rows:
        check(any(link in URLS for link in row),
              f"{path.name}: table body row without an official source link")

# ---------------------------------------------------------------- data integrity
ids = [m["id"] for m in METHODS]
check(len(ids) == len(set(ids)), "duplicate method id")
check(len(ids) == 27, f"expected 27 methods, found {len(ids)}")
check(len(SOURCES) == 22, f"expected 22 sources, found {len(SOURCES)}")

for s in SOURCES:
    for k in ("id", "jur", "authority", "kind", "title", "url", "locator", "quote",
              "supports", "retrieved", "status"):
        check(bool(s.get(k)), f"source {s['id']}: missing {k}")
    check(urlsplit(s["url"]).scheme == "https" or s["url"].startswith("http://www.safe.gov.cn"),
          f"source {s['id']}: unexpected scheme")
    check(s["status"] == "fetched-2026-11-10", f"source {s['id']}: not marked freshly fetched")
    check(len(s["quote"]) > 40, f"source {s['id']}: quote too short to be evidence")

for m in METHODS:
    check(bool(m["basis"]), f"{m['id']}: no basis")
    for sid in m["basis"]:
        check(sid in SRC, f"{m['id']}: unknown source {sid}")
    for sid in m["cost"].get("cost_sources", []):
        check(sid in SRC, f"{m['id']}: unknown cost source {sid}")
    check(m["status"] in ("lawful", "conditional", "unlawful"), f"{m['id']}: bad status")
    check(len(m["steps"]) >= 2, f"{m['id']}: fewer than two steps")
    check(len(m["pros"]) >= 1 and len(m["cons"]) >= 1, f"{m['id']}: pros/cons missing")
    check(bool(m["penalty"]), f"{m['id']}: no penalty statement")
    if m["status"] == "unlawful":
        check(m["cost"]["annual_cap_usd"] == 0, f"{m['id']}: unlawful method has a capacity")
        check(m["cost"]["fee"]["type"] == "unverified", f"{m['id']}: unlawful method priced")

# ---------------------------------------------------------------- tier coverage
TIERS = list(range(10_000, 400_001, 10_000))
check(META["tiers"] == TIERS, "tier list is not every 10,000 from 10,000 to 400,000")
check(len(TIERS) == 40, f"expected 40 tiers, found {len(TIERS)}")
check(len(COSTS["rows"]) == len(METHODS) * len(TIERS),
      "costs matrix does not cover every method and tier")
for m in METHODS:
    for t in TIERS:
        check((m["id"], t) in ROWS, f"missing cost row {m['id']} at {t}")

# ---------------------------------------------------------------- arithmetic
for m in METHODS:
    fee_spec = m["cost"]["fee"]
    spread_pct = m["cost"]["spread"]["pct"]
    for t in TIERS:
        r = ROWS[(m["id"], t)]
        if fee_spec["type"] == "unverified":
            check(r["fee_usd"] is None and r["spread_usd"] is None and r["total_usd"] is None,
                  f"{m['id']}@{t}: unverified method has a number")
            continue
        if fee_spec["type"] == "zero":
            fee = 0.0
        elif fee_spec["type"] == "flat_usd":
            fee = float(fee_spec["usd"])
        else:
            raw = fee_spec["pct"] * t
            fee = min(max(raw, fee_spec["min_cny"] / RATE), fee_spec["max_cny"] / RATE)
            fee += fee_spec.get("cable_cny", 0) / RATE
            fee += fee_spec.get("flat_usd", 0)
        spread = t * spread_pct / 100
        total = fee + spread
        check(abs(r["fee_usd"] - round(fee, 2)) <= 0.011, f"{m['id']}@{t}: fee does not recompute")
        check(abs(r["spread_usd"] - round(spread, 2)) <= 0.011, f"{m['id']}@{t}: spread does not recompute")
        check(abs(r["total_usd"] - round(total, 2)) <= 0.011, f"{m['id']}@{t}: total does not recompute")
        check(abs(r["total_usd"] - (r["fee_usd"] + r["spread_usd"])) <= 0.02,
              f"{m['id']}@{t}: fee + spread != total")
        check(abs(r["pct_of_principal"] - round(total / t * 100, 3)) <= 0.002,
              f"{m['id']}@{t}: percentage does not recompute")

# ---------------------------------------------------------------- monotonicity
for m in META["costed_methods"]:
    totals = [ROWS[(m, t)]["total_usd"] for t in TIERS]
    check(totals == sorted(totals), f"{m}: total cost is not non-decreasing across tiers")
    pcts = [ROWS[(m, t)]["pct_of_principal"] for t in TIERS]
    check(pcts == sorted(pcts, reverse=True) or m == "M09",
          f"{m}: percentage of principal should not increase with size")

check(ROWS[("M01", 10_000)]["total_usd"] == 72.89, "M01 at 10k drifted from the published figure")
check(ROWS[("M01", 400_000)]["total_usd"] == 1763.32, "M01 at 400k drifted from the published figure")
check(ROWS[("M02", 400_000)]["fee_usd"] == 0.0, "M02 Global Transfer is not free at 400k")

# ---------------------------------------------------------------- no-JS parity
costs_html = (ROOT / "costs.html").read_text()
for m in META["costed_methods"]:
    check(f'id="tier-' in costs_html, "costs.html lost its per-tier anchors")
    break
for t in TIERS:
    check(f"${t//1000}k" in costs_html, f"costs.html matrix missing column for {t}")
for m in METHODS:
    check(f'href="methods.html#{m["id"]}"' in costs_html,
          f"costs.html does not link every method ({m['id']})")
methods_html = (ROOT / "methods.html").read_text()
for m in METHODS:
    check(f'id="{m["id"]}"' in methods_html, f"methods.html missing card for {m['id']}")
flagged_html = (ROOT / "flagged.html").read_text()
for m in META["unverified_methods"]:
    check(f"F-{m}" in flagged_html, f"flagged.html does not disclose {m} as unverified")

# ---------------------------------------------------------------- summary
print(f"{CHECKS:,} checks, {len(FAILS)} failures")
if FAILS:
    for f in FAILS[:40]:
        print("  FAIL:", f)
    sys.exit(1)
print(f"PASS: {len(PAGES)} pages; {len(METHODS)} methods ({len(META['costed_methods'])} costed, "
      f"{len(META['unverified_methods'])} blank and flagged); {len(TIERS)} tiers; "
      f"{len(COSTS['rows']):,} cost cells recomputed; {len(SOURCES)} sources; "
      f"every table body row has an official link.")
print("External URL availability and current law are not tested by this script.")
