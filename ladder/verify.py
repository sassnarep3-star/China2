#!/usr/bin/env python3
"""Independent verifier for the ladder dashboard.

Checks structure, data integrity, citation coverage and local links. It does not
and cannot verify external URL health; see sources.html for retrieval mode.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FAILS: list[str] = []
CHECKS = 0


def check(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(msg)


SOURCES = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text())}
ROUTES = json.loads((DATA / "routes.json").read_text())
ASSUMPTIONS = json.loads((DATA / "assumptions.json").read_text())
COSTS = json.loads((DATA / "costs.json").read_text())
META = COSTS["meta"]
ROWS = COSTS["rows"]
PAGES = ["index.html", "costs.html", "ladder.html", "routes.html", "steps.html",
         "tax.html", "assumptions.html", "audit.html", "flagged.html", "sources.html"]


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
        self.text: list[str] = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "h1":
            self.h1 += 1
        if tag == "tbody":
            self._in_body = True
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

    def handle_data(self, data):
        self.text.append(data)


def main() -> int:
    docs = {}
    for name in PAGES:
        p = ROOT / name
        check(p.exists(), f"missing page {name}")
        if p.exists():
            docs[name] = Doc(p)

    # --- structure -------------------------------------------------------
    for name, d in docs.items():
        check(d.h1 == 1, f"{name}: expected exactly one h1, found {d.h1}")
        check(d.lang == "en", f"{name}: html lang must be 'en'")
        check(len(d.ids) == len(set(d.ids)), f"{name}: duplicate element ids")
        check("Skip to content" in "".join(d.text), f"{name}: missing skip link")

    # --- source registry -------------------------------------------------
    check(len(SOURCES) == META["source_count"], "source count mismatch with meta")
    for sid, s in SOURCES.items():
        for field in ("authority", "title", "url", "lang", "retrieval", "status", "locator",
                      "quote", "used_for"):
            check(bool(str(s.get(field, "")).strip()), f"{sid}: empty field {field}")
        check(s["url"].startswith("https://") or s["url"].startswith("http://"),
              f"{sid}: url must be absolute http(s)")
        host = urlsplit(s["url"]).hostname or ""
        check(host.endswith(".gov") or host.endswith(".gov.cn") or "hsbc.com.cn" in host,
              f"{sid}: source host {host} is neither .gov/.gov.cn nor the cited bank tariff")
        check(s["retrieval"] in ("direct", "search"), f"{sid}: bad retrieval mode")
        check(s["status"] in ("verified", "needs review"), f"{sid}: bad status")
    check(sum(1 for s in SOURCES.values() if s["retrieval"] == "direct") >= 12,
          "fewer than 12 sources retrieved directly")

    # --- assumptions -----------------------------------------------------
    check(len(ASSUMPTIONS) == META["assumption_count"], "assumption count mismatch")
    for a in ASSUMPTIONS:
        for field in ("id", "topic", "value", "status", "why"):
            check(bool(a[field].strip()), f"{a['id']}: empty {field}")
        check("assumption" in a["status"] or "unverified" in a["status"],
              f"{a['id']}: status must disclose that the value is not published")

    # --- routes ----------------------------------------------------------
    ids = [r["id"] for r in ROUTES]
    check(len(ids) == len(set(ids)), "duplicate route ids")
    check(len(ROUTES) == META["route_count"], "route count mismatch")
    for r in ROUTES:
        check(r["status"] in ("lawful", "conditional", "unlawful"), f"{r['id']}: bad status")
        check(bool(r["basis"]), f"{r['id']}: no legal basis cited")
        for sid in r["basis"]:
            check(sid in SOURCES, f"{r['id']}: cites unknown source {sid}")
        check(bool(r["steps"]), f"{r['id']}: no steps")
        check(r["pros"] and r["cons"], f"{r['id']}: missing pros/cons")
        if r["status"] != "unlawful":
            check(r["docs"] != [] or r["fee"] == "none", f"{r['id']}: lawful route with no documents")
    costed = [r for r in ROUTES if r["status"] != "unlawful"]
    check(len(costed) == META["costed_route_count"], "costed route count mismatch")

    # --- ladder ----------------------------------------------------------
    tiers = sorted({row["tier"] for row in ROWS})
    check(tiers == list(range(10_000, 400_001, 10_000)), "tier ladder is not 10k..400k step 10k")
    check(len(tiers) == 40, f"expected 40 tiers, found {len(tiers)}")
    check(len(ROWS) == 40 * len(costed), f"expected {40 * len(costed)} rows, found {len(ROWS)}")
    for row in ROWS:
        check(row["route"] in [r["id"] for r in costed], f"ladder row for unknown route {row['route']}")
        check(row["total_lo"] is not None and row["total_hi"] is not None,
              f"{row['route']}@{row['tier']}: missing estimate")
        check(row["total_lo"] <= row["total_hi"] + 1e-9,
              f"{row['route']}@{row['tier']}: low estimate exceeds high estimate")
        check(0 <= (row["pct_hi"] or 0) <= 100, f"{row['route']}@{row['tier']}: implausible percentage")
        if row["partial"]:
            check(row["fixed_fee"] is None, f"{row['route']}@{row['tier']}: partial row with a fixed fee")
        else:
            check(row["fixed_fee"] is not None, f"{row['route']}@{row['tier']}: non-partial row without a fee")

    # --- citation coverage in rendered tables ----------------------------
    for name in ("costs.html", "ladder.html", "routes.html", "tax.html"):
        d = docs[name]
        check(bool(d.rows), f"{name}: no table rows found")
        for i, row in enumerate(d.rows):
            has_anchor = any(("sources.html#S" in h) for h in row)
            check(has_anchor, f"{name}: table row {i + 1} has no official source link")

    for name in ("assumptions.html", "audit.html"):
        d = docs[name]
        check(bool(d.rows), f"{name}: no table rows found")

    # --- pages carry the entities they claim ----------------------------
    routes_html = (ROOT / "routes.html").read_text()
    steps_html = (ROOT / "steps.html").read_text()
    sources_html = (ROOT / "sources.html").read_text()
    flags_html = (ROOT / "flagged.html").read_text()
    for r in ROUTES:
        check(f'id="{r["id"]}"' in routes_html, f"routes.html missing route {r['id']}")
        if r["status"] != "unlawful":
            check(r["id"] in steps_html, f"steps.html missing route {r['id']}")
    for sid in SOURCES:
        check(f'id="{sid}"' in sources_html, f"sources.html missing source {sid}")

    # --- flags referenced across pages exist ----------------------------
    flags = set(re.findall(r'id="(F\d{2})"', flags_html))
    check(len(flags) >= 10, f"expected at least 10 flags, found {len(flags)}")
    for ref in set(re.findall(r"flagged\.html#(F\d{2})", (ROOT / "audit.html").read_text())):
        check(ref in flags, f"audit.html references missing flag {ref}")
    for sid, s in SOURCES.items():
        if s.get("flag"):
            check(s["flag"] in flags, f"{sid} points at missing flag {s['flag']}")

    # --- local links and fragments resolve -------------------------------
    for name, d in docs.items():
        for link in d.links:
            if link.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            target, _, frag = link.partition("#")
            target = unquote(target)
            path = (ROOT / target) if target else (ROOT / name)
            if target and not path.exists():
                check(False, f"{name}: broken local link {link}")
                continue
            check(True, f"{name}: local link {link}")
            if frag:
                tgt_doc = docs.get(path.name)
                if tgt_doc is not None:
                    check(frag in tgt_doc.ids, f"{name}: missing anchor #{frag} in {path.name}")

    # --- no leaked machinery --------------------------------------------
    for name, d in docs.items():
        text = "".join(d.text)
        for bad in ("None</td>", ">None<", "$None", "nan%", "TODO", "FIXME", "undefined", "&lt;", "{META"):
            check(bad not in text, f"{name}: leaked machinery token {bad!r}")

    # --- prose counts agree with ledgers --------------------------------
    check(f"{len(SOURCES)} documents" in sources_html, "sources.html count drifted from ledger")
    check(f"{len([r for r in ROUTES if r['status'] != 'unlawful'])} lawful or conditional routes"
          in (ROOT / "routes.html").read_text(), "routes.html count drifted from ledger")
    check(f"modelled rows {META['row_count']}" in (ROOT / "index.html").read_text(),
          "index.html footer row count does not match the ledger")

    # --- downloads exist and match the data -----------------------------
    for f in ("costs.csv", "costs.json", "routes.json", "sources.json", "assumptions.json"):
        check((DATA / f).exists(), f"missing download {f}")
    csv_lines = (DATA / "costs.csv").read_text().strip().splitlines()
    check(len(csv_lines) == len(ROWS) + 1, "costs.csv row count does not match costs.json")

    print(f"{CHECKS} checks, {len(FAILS)} failures")
    for f in FAILS:
        print("  FAIL:", f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
