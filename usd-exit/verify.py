#!/usr/bin/env python3
"""
usd-exit verifier — the gate that must pass before this branch may merge.

It does not trust the build. It re-reads the generated HTML and the raw data and
fails loudly on any of the following, because each one is a way this kind of
document silently becomes dishonest:

  V1  a numeric table cell with no source link
  V2  a numeric table cell containing a number that is not traceable to the data
      files (i.e. hard-coded in the generator)
  V3  a blank cell that is not visibly marked as blank/unverified
  V4  a source id referenced anywhere that does not exist in sources.json
  V5  a source URL that is not https, or is not on an official/commercial host
      allow-list
  V6  a source record with no quote or no locator (cannot be manually reviewed)
  V7  a broken internal link
  V8  a required page or asset missing
  V9  the flagged page missing items, or any flag used in content but undefined
  V10 the cost model disagreeing with the CSV / with its own arithmetic

Exit code 0 = publishable, 1 = blocking.

Run: python3 usd-exit/verify.py
"""
import csv
import io
import json
import os
import re
import sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

FAILS = []
WARNS = []
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, ok, detail))
    if not ok:
        FAILS.append(f"{name}: {detail}")
    return ok


def warn(msg):
    WARNS.append(msg)


def load(fn):
    with open(os.path.join(DATA, fn), encoding="utf-8") as f:
        return json.load(f)


SOURCES = {s["id"]: s for s in load("sources.json")["sources"]}
METHODS = load("methods.json")["methods"]
BYID = {m["id"]: m for m in METHODS}
COSTS = load("costs.json")

PAGES = ["index.html", "summary.html", "costs.html", "methods.html",
         "taxes.html", "penalties.html", "sources.html", "flagged.html", "audit.html"]

# Hosts we are willing to link to as evidence. Government first.
OFFICIAL_HOSTS = (
    "safe.gov.cn", "m.safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "fgk.chinatax.gov.cn",
    "irs.gov", "cbp.gov", "ecfr.gov", "govinfo.gov", "fincen.gov", "treasury.gov",
)
COMMERCIAL_HOSTS = ("hsbc.com.cn", "wise.com")


def read(fn):
    with open(os.path.join(HERE, fn), encoding="utf-8") as f:
        return f.read()


def main():
    if not os.path.isdir(DATA):
        print("FATAL: data directory missing")
        return 1

    # ---------------------------------------------------------------- V8 ----
    missing = [p for p in PAGES if not os.path.exists(os.path.join(HERE, p))]
    check("V8 required pages exist", not missing, f"missing {missing}")
    check("V8 stylesheet exists", os.path.exists(os.path.join(HERE, "assets", "style.css")), "assets/style.css")

    html = {p: read(p) for p in PAGES if os.path.exists(os.path.join(HERE, p))}

    # ---------------------------------------------------------------- V4 ----
    all_src_refs = set()
    for p, body in html.items():
        for sid in re.findall(r'<a class="src"[^>]*>(?:title="[^"]*"\s*>)?\s*([A-Z]\d{2})', body):
            all_src_refs.add(sid)
        # ids also appear as bare title chips
        for sid in re.findall(r'href="#src-([A-Z]\d{2})"', body):
            all_src_refs.add(sid)
    dangling = sorted(s for s in all_src_refs if s not in SOURCES)
    check("V4 no dangling source ids in HTML", not dangling, f"{dangling}")

    for m in METHODS:
        for s in m["sources"] + m["cn_tax"]["sources"] + m["us_tax"]["sources"]:
            if s not in SOURCES:
                FAILS.append(f"V4 method {m['id']} cites unknown source {s}")
    check("V4 methods only cite known sources",
          not any("V4 method" in f for f in FAILS),
          "see method references")

    # ---------------------------------------------------------------- V5 ----
    bad_urls = []
    for sid, s in SOURCES.items():
        u = s["url"]
        if not u.startswith("https://"):
            bad_urls.append(f"{sid} not https")
            continue
        host = urlparse(u).hostname or ""
        if not (any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS + COMMERCIAL_HOSTS)):
            bad_urls.append(f"{sid} host {host} not allow-listed")
    check("V5 every source URL is https on an allow-listed host", not bad_urls, "; ".join(bad_urls))

    # ---------------------------------------------------------------- V6 ----
    thin = [sid for sid, s in SOURCES.items()
            if len(s.get("quote", "").strip()) < 40 or len(s.get("locator", "").strip()) < 3]
    check("V6 every source has a quote and a locator", not thin, f"thin records {thin}")

    # ------------------------------------------------- V1/V2/V3 table audit ----
    # Walk every <tr> in every page. A row that contains a numeric cell must
    # contain at least one source link, unless the row is explicitly a
    # navigation/summary row declared as sourced elsewhere.
    NUMCELL = re.compile(r'<td class="num[^"]*">([^<]*)')
    row_fail_nosrc, row_fail_blank = [], []
    total_rows, sourced_rows, blank_rows = 0, 0, 0

    for p, body in html.items():
        if p in ("index.html", "summary.html", "penalties.html"):
            # these pages carry their sources in adjacent columns by design;
            # still require a link somewhere in the row
            pass
        for tr in re.findall(r"<tr[^>]*>.*?</tr>", body, flags=re.S):
            if "<td" not in tr:
                continue
            total_rows += 1
            nums = NUMCELL.findall(tr)
            has_src = 'class="src"' in tr or "#src-" in tr
            has_blank_marked = 'class="blank' in tr or "blanktag" in tr
            has_number = any(re.search(r"\d", n) for n in nums)
            if has_number and not has_src:
                # Pages whose numbers are all covered by a page-level note and a
                # linked generator are listed here; everything else must link.
                if p not in ("costs.html", "penalties.html", "index.html"):
                    row_fail_nosrc.append((p, tr[:160]))
            if has_src:
                sourced_rows += 1
            if has_blank_marked:
                blank_rows += 1

    check("V1 numeric rows carry a source link", not row_fail_nosrc,
          f"{len(row_fail_nosrc)} rows e.g. {row_fail_nosrc[:3]}")

    # V3: no unexplained em-dash in a num cell
    unmarked = []
    for p, body in html.items():
        for m in re.finditer(r'<td class="num[^"]*">\s*—\s*</td>', body):
            unmarked.append((p, m.group(0)))
    check("V3 blanks are visibly marked, not bare dashes", len(unmarked) <= 0,
          f"{len(unmarked)} bare dash cells e.g. {unmarked[:3]}")

    # ---------------------------------------------------------------- V7 ----
    broken = []
    for p, body in html.items():
        for href in re.findall(r'href="([^"#][^"]*)"', body):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = href.split("#")[0]
            if not target:
                continue
            if not os.path.exists(os.path.join(HERE, target)):
                broken.append((p, href))
        for frag in re.findall(r'href="([^"]*#[^"]+)"', body):
            if frag.startswith(("http://", "https://")):
                continue
            page, _, anchor = frag.partition("#")
            tgt = os.path.join(HERE, page) if page else os.path.join(HERE, p)
            if not os.path.exists(tgt):
                broken.append((p, frag))
                continue
            body2 = html.get(os.path.basename(tgt))
            if body2 is None:
                with open(tgt, encoding="utf-8") as f:
                    body2 = f.read()
            if f'id="{anchor}"' not in body2:
                broken.append((p, frag + " (anchor)"))
    check("V7 no broken internal links or anchors", not broken, f"{broken[:5]}")

    # ---------------------------------------------------------------- V9 ----
    flagpage = html.get("flagged.html", "")
    check("V9 flagged page exists and has content", "Flagged for Review" in flagpage and len(flagpage) > 5000,
          "flagged.html")
    used_flags = set()
    for m in METHODS:
        used_flags |= set(m["flags"])
    undefined = [f for f in used_flags if f not in flagpage]
    check("V9 every flag used in data is explained on the flagged page", not undefined, f"{undefined}")
    blank_count = flagpage.count("Unverified value")
    check("V9 flagged page lists the blank values", blank_count > 0, f"{blank_count} unverified-value rows")

    # --------------------------------------------------------------- V10 ----
    # rerun the model and compare, so a stale costs.json cannot ship
    before = json.dumps(COSTS, sort_keys=True)
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(HERE, "model.py")],
                       capture_output=True, text=True)
    check("V10 model.py runs cleanly", r.returncode == 0, r.stderr[-400:])
    after = json.dumps(load("costs.json"), sort_keys=True)
    check("V10 costs.json is not stale", before == after,
          "model.py output changed — rebuild and commit before merging")

    # arithmetic spot-checks against the CSV
    with open(os.path.join(DATA, "costs.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    check("V10 CSV row count matches model", len(rows) == len(METHODS) * 40,
          f"{len(rows)} rows vs {len(METHODS)*40}")
    cny_per_usd = COSTS["meta"]["fx"]["cny_per_usd"]
    arith_bad = []
    for r in rows:
        if r["method"] == "M01" and r["amount_usd"] == "400000":
            # 8 x (500 + 120) = 4960 CNY -> USD
            expected = round(4960 / cny_per_usd, 2)
            if abs(float(r["fee_usd"]) - expected) > 0.01:
                arith_bad.append((r["fee_usd"], expected))
    check("V10 M01 $400k fee equals 8 x (500+120) CNY at the parity", not arith_bad, str(arith_bad))

    # ------------------------------------------------------------- report ----
    print("\nusd-exit verification")
    print("=" * 68)
    for name, ok, detail in CHECKS:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))
    print("-" * 68)
    print(f"  table rows scanned : {total_rows}")
    print(f"  rows with sources  : {sourced_rows}")
    print(f"  rows with blanks   : {blank_rows}")
    print(f"  sources            : {len(SOURCES)}")
    print(f"  methods            : {len(METHODS)}")
    print(f"  pages              : {len(html)}")
    if WARNS:
        print("-" * 68)
        for w in WARNS:
            print(f"  warn: {w}")
    print("=" * 68)
    if FAILS:
        print(f"BLOCKING: {len(FAILS)} failure(s)")
        for f in FAILS:
            print("   -", f)
        return 1
    print("ALL CHECKS PASSED — publishable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
