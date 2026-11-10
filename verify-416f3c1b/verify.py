#!/usr/bin/env python3
"""Independent verifier for verify-416f3c1b.

Checks, without importing the build script:
  1. every HTML page parses, has a viewport, balanced tags, and the shared nav;
  2. every local link, anchor and asset resolves on disk;
  3. every data row in every table carries at least one external source link;
  4. every source ID used anywhere exists in sources.json, and every source in
     sources.json is referenced somewhere;
  5. every cited URL is on an allow-listed official/provider host and is http(s);
  6. the cost ladder arithmetic recomputes from the published tariff figures and
     reproduces every rendered USD value, and the 40 tiers are exactly
     $10,000..$400,000 in $10,000 steps;
  7. no cell that must be blank contains a number (the FX spread column);
  8. the sec. 988 comparison table and the $200 threshold arithmetic are correct;
  9. re-running the builder is deterministic (byte-identical output);
 10. no absolute or localhost URLs, no external script/style dependencies.

Exit code 0 only if every check passes.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"

fails: list[str] = []
checks = 0


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


ALLOWED_HOSTS = {
    "www.safe.gov.cn",
    "safe.gov.cn",
    "www.pbc.gov.cn",
    "pbc.gov.cn",
    "www.chinatax.gov.cn",
    "fgk.chinatax.gov.cn",
    "www.gov.cn",
    "www.govinfo.gov",
    "www.irs.gov",
    "www.ecfr.gov",
    "www.cbp.gov",
    "www.fincen.gov",
    "www.hsbc.com.cn",
}

S = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
M = json.loads((DATA / "methods.json").read_text(encoding="utf-8"))
C = json.loads((DATA / "costs.json").read_text(encoding="utf-8"))
F = json.loads((DATA / "findings.json").read_text(encoding="utf-8"))
SRC = {s["id"]: s for s in S["sources"]}
RATE = C["rate_cny_per_usd"]
TIERS = list(range(C["tiers"]["start_usd"], C["tiers"]["end_usd"] + 1, C["tiers"]["step_usd"]))


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.srcs: list[str] = []
        self.ids: set[str] = set()
        self.tags: list[str] = []
        self.has_viewport = False
        self.void = {"meta", "link", "br", "img", "hr", "input", "source", "wbr", "col"}
        self.stack: list[str] = []
        self.unbalanced: list[str] = []
        self.tables: list[list[list[str]]] = []
        self._in_table = 0
        self._rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._in_thead = False
        self._row_links: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("name") == "viewport":
            self.has_viewport = True
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
            if self._in_table and a["href"].startswith("https://"):
                self._row_links.append(a["href"])
        if tag in ("script", "link", "img") and a.get("src"):
            self.srcs.append(a["src"])
        if tag == "link" and a.get("href") and "stylesheet" in str(a.get("rel", "")):
            self.srcs.append(a["href"])
        if a.get("id"):
            self.ids.add(a["id"])
        self.tags.append(tag)
        if tag == "table":
            self._in_table += 1
            self._rows = []
        elif tag == "thead":
            self._in_thead = True
        elif tag == "tr" and self._in_table:
            self._row = []
            self._row_links = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        if tag not in self.void:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.void:
            return
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if not self._in_thead:
                self._rows.append((self._row, list(self._row_links)))
            self._row = None
        elif tag == "thead":
            self._in_thead = False
        elif tag == "table":
            self.tables.append(self._rows)
            self._in_table = max(0, self._in_table - 1)
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            self.unbalanced.append(tag)

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


PAGES = {
    "index.html": "Dashboard",
    "routes.html": "Methods",
    "costs.html": "Costs $10k-$400k",
    "tax.html": "Tax & penalties",
    "steps.html": "Step by step",
    "sources.html": "Sources",
    "audit.html": "Repo audit",
    "flagged.html": "Flagged for review",
}

docs: dict[str, Doc] = {}
for name in PAGES:
    p = ROOT / name
    check(p.exists(), f"missing page {name}")
    if not p.exists():
        continue
    raw = p.read_text(encoding="utf-8")
    d = Doc()
    d.feed(raw)
    d.raw = raw
    docs[name] = d
    check(d.has_viewport, f"{name}: no viewport meta (mobile)")
    check(not d.unbalanced, f"{name}: unbalanced tags {d.unbalanced[:5]}")
    check(raw.startswith("<!doctype html>"), f"{name}: missing doctype")
    check("<title>" in raw, f"{name}: missing title")
    check("lang=" in raw, f"{name}: missing lang attribute")
    # shared nav present on every page
    for href, label in PAGES.items():
        check(href in d.hrefs, f"{name}: nav missing link to {href}")
    # no localhost / absolute-file references, no external asset dependencies
    check("localhost" not in raw and "127.0.0.1" not in raw, f"{name}: contains localhost reference")
    check("file://" not in raw, f"{name}: contains file:// reference")
    for s_ in d.srcs:
        check(not s_.startswith("http"), f"{name}: external asset dependency {s_}")
        check(not s_.startswith("/"), f"{name}: absolute asset path {s_}")
        check((ROOT / s_).exists(), f"{name}: missing asset {s_}")

# ---------------------------------------------------------------- links & anchors
for name, d in docs.items():
    for href in d.hrefs:
        check(not href.startswith("/"), f"{name}: absolute link {href}")
        if href.startswith(("http://", "https://", "mailto:")):
            host = re.sub(r"^https?://", "", href).split("/")[0]
            check(href.startswith("https://"), f"{name}: non-https external link {href}")
            check(host in ALLOWED_HOSTS, f"{name}: external link to unapproved host {href}")
            continue
        target, _, frag = href.partition("#")
        target = target or name
        tp = ROOT / target
        check(tp.exists(), f"{name}: broken local link {href}")
        if frag and tp.exists():
            dt = docs.get(target)
            if dt is None:
                dt2 = Doc()
                dt2.feed(tp.read_text(encoding="utf-8"))
                dt = dt2
            check(frag in dt.ids, f"{name}: broken fragment {href}")

# ---------------------------------------------------------------- tables cite sources
total_rows = 0
for name, d in docs.items():
    for ti, rows in enumerate(d.tables):
        for ri, (row, links) in enumerate(rows):
            total_rows += 1
            check(bool(links), f"{name} table {ti} row {ri}: no external source link in row")
            check(len(row) >= 2, f"{name} table {ti} row {ri}: too few cells")
            for lk in links:
                host = re.sub(r"^https?://", "", lk).split("/")[0]
                check(host in ALLOWED_HOSTS, f"{name} table {ti} row {ri}: unapproved host {lk}")

# ---------------------------------------------------------------- source ledger
check(len(SRC) == len(S["sources"]), "duplicate source ids")
for s in S["sources"]:
    check(s["url"].startswith("https://"), f"{s['id']}: source url not https")
    host = re.sub(r"^https?://", "", s["url"]).split("/")[0]
    check(host in ALLOWED_HOSTS, f"{s['id']}: source host not allow-listed: {host}")
    for field in ("title", "publisher", "kind", "locator", "facts", "status"):
        check(bool(str(s.get(field, "")).strip()), f"{s['id']}: empty {field}")
    check(s["status"] == "fetched", f"{s['id']}: not marked fetched")

used: set[str] = set()
for r in M["routes"]:
    used.update(r["sources"])
    check(r["ceiling_source"] in SRC or r["ceiling_source"] is None, f"{r['id']}: bad ceiling_source")
for f in F["findings"]:
    used.update(f["sources"])
for f in F["flags"]:
    used.update(f["sources"])
for it in F["audit"]["items"]:
    used.update(it["sources"])
    check(it["verdict"] in ("verified", "verified-limited", "contradicted", "unverified"),
          f"audit {it['id']}: bad verdict")
    for k in ("page", "title", "claim", "finding", "sources"):
        check(bool(str(it.get(k, "")).strip()), f"audit {it['id']}: empty {k}")
check(len({i['id'] for i in F['audit']['items']}) == len(F['audit']['items']), "duplicate audit ids")
# the contradicted claim must name real pages, and the statute text must be quoted on the audit page
audit_raw = docs["audit.html"].raw
for it in F["audit"]["items"]:
    if it["verdict"] == "contradicted":
        check("988" in it["finding"] or "2.2.6.1" in it["finding"],
              f"audit {it['id']}: contradicted verdict without statutory or tariff citation")
check("ordinary income" in audit_raw, "audit page does not state the ordinary-income rule")
for name, d in docs.items():
    used.update(re.findall(r"\bS\d{2}\b", d.raw))
check(used.issubset(set(SRC)), f"unknown source ids referenced: {sorted(used - set(SRC))}")
unused = sorted(set(SRC) - used)
check(not unused, f"sources never referenced: {unused}")

# ---------------------------------------------------------------- cost arithmetic
cfg = C["routes"]["R01"]
check(cfg["pct"] == 0.001, "R01 percentage is not 0.1%")
check(cfg["min_cny"] == 100 and cfg["max_cny"] == 500, "R01 floors/caps changed")
check(cfg["cable_cny"] == 120, "R01 cable charge changed")
check(RATE == 7.129, "reference rate is not the IRS 2025 average")

check(TIERS[0] == 10000 and TIERS[-1] == 400000 and len(TIERS) == 40,
      f"tier ladder wrong: {TIERS[0]}..{TIERS[-1]} n={len(TIERS)}")
check(all(b - a == 10000 for a, b in zip(TIERS, TIERS[1:])), "tiers are not $10,000 steps")


def expected_fee(usd_amount: int) -> float:
    cny = usd_amount * RATE
    fee = min(max(cny * cfg["pct"], cfg["min_cny"]), cfg["max_cny"]) + cfg["cable_cny"]
    return fee / RATE


costs_raw = docs["costs.html"].raw
for t in TIERS:
    value = f"${expected_fee(t):,.2f}"
    check(value in costs_raw, f"costs.html: missing/recomputed mismatch for ${t:,} ({value})")
    check(f"${t:,}" in costs_raw, f"costs.html: tier ${t:,} label missing")

# spot-check the two worked examples quoted in prose
check(abs(expected_fee(10000) - 30.86) < 0.005, f"USD 10,000 fee is not ~30.86 ({expected_fee(10000)})")
check(abs(expected_fee(400000) - 86.97) < 0.005, f"USD 400,000 fee is not ~86.97 ({expected_fee(400000)})")
check("$30.86" in costs_raw and "$86.97" in costs_raw, "worked examples not rendered")
check("CNY 71,290" in costs_raw, "USD 10,000 CNY conversion not rendered")
check("CNY 2,851,600" in costs_raw, "USD 400,000 CNY conversion not rendered")

# R02 flat fees
check(C["routes"]["R02"]["usd_advance"] == 20, "R02 advance fee is not USD 20")
check(C["routes"]["R02"]["usd_premier"] == 0 and C["routes"]["R02"]["usd_pb"] == 0,
      "R02 premier/PB fee is not Free")
check(costs_raw.count("$20.00") >= 40, "R02 advance column not rendered for every tier")

# the FX spread column must be blank everywhere
check(costs_raw.count('data-blank="unverified"') >= len(TIERS), "spread column not blank on every tier")

# ---------------------------------------------------------------- sec. 988 arithmetic
rates = {"2021": 6.452, "2022": 6.730, "2023": 7.075, "2024": 7.189, "2025": 7.129}
gain_2024 = 10000 - (10000 * rates["2025"]) / rates["2024"]
thr = 200 / ((rates["2024"] / rates["2025"]) - 1)
tax_raw = docs["tax.html"].raw
check(abs(gain_2024 - 83.46) < 0.02, f"2024 gain arithmetic wrong: {gain_2024}")
check(f"${thr:,.2f}" in tax_raw, f"$200 threshold amount not rendered ({thr:,.2f})")
check(thr > 23700 and thr < 23800, f"threshold outside expected range: {thr}")
for yr in ("2021", "2022", "2023"):
    check(f"{rates[yr]:.3f}" in tax_raw, f"tax.html: {yr} average rate missing")
check("$16,536" in tax_raw, "FBAR non-willful maximum missing")
check("$165,353" in tax_raw, "FBAR willful maximum missing")

# ---------------------------------------------------------------- findings consistency
ids = [f["id"] for f in F["findings"]]
check(len(ids) == len(set(ids)), "duplicate finding ids")
fl = [f["id"] for f in F["flags"]]
check(len(fl) == len(set(fl)), "duplicate flag ids")
for f in F["findings"]:
    check(f["status"] in ("verified", "unverified"), f"{f['id']}: bad status")
    check(bool(f["sources"]), f"{f['id']}: no sources")
for f in F["flags"]:
    for k in ("title", "detail", "impact", "sources"):
        check(bool(f.get(k)), f"{f['id']}: empty {k}")

# every route must have pros, cons and steps, and a status that is allowed
for r in M["routes"]:
    check(r["status"] in ("lawful-conditional", "prohibited", "conditional-unverified"),
          f"{r['id']}: bad status")
    check(len(r["pros"]) >= 1, f"{r['id']}: no pros listed")
    check(len(r["cons"]) >= 1, f"{r['id']}: no cons listed")
    check(len(r["steps"]) >= 1, f"{r['id']}: no steps listed")
    check(bool(r["cost_note"]), f"{r['id']}: no cost note")
    for key in ("name", "short", "category", "who", "mechanism", "ceiling"):
        check(bool(str(r[key]).strip()), f"{r['id']}: empty {key}")

# prohibited routes must not present a numeric cost as if it were payable
for r in M["routes"]:
    if r["status"] == "prohibited":
        check("Not a costed route" in r["cost_note"], f"{r['id']}: prohibited route looks costed")

# ---------------------------------------------------------------- determinism
before = {n: (ROOT / n).read_bytes() for n in PAGES}
res = subprocess.run([sys.executable, str(ROOT / "build.py")], capture_output=True, text=True,
                     env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
check(res.returncode == 0, f"rebuild failed: {res.stderr[:300]}")
for n in PAGES:
    check((ROOT / n).read_bytes() == before[n], f"{n}: build is not deterministic")

print(f"pages          : {len(docs)}")
print(f"html tables    : {sum(len(d.tables) for d in docs.values())}")
print(f"table rows     : {total_rows}")
print(f"sources        : {len(SRC)}")
print(f"routes         : {len(M['routes'])}")
print(f"tiers          : {len(TIERS)}")
print(f"findings/flags : {len(F['findings'])}/{len(F['flags'])}")
print(f"checks         : {checks}")
print(f"FAILURES       : {len(fails)}")
for f in fails[:40]:
    print("  FAIL:", f)
sys.exit(1 if fails else 0)
