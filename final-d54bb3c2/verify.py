#!/usr/bin/env python3
"""Verification for the final-d54bb3c2 section.

Fails loudly if a page, a value or a source link does not hold up:
  * every referenced source id exists in the ledger, and every ledger entry is used
  * every cost row recomputes exactly from the raw board rates and fee schedules
  * every priced method states a formula and at least one source
  * every blank in the cost table has a matching entry on the flagged page
  * every internal link on every page resolves, and every cost row links to a source
  * no template placeholders leaked into the HTML

Run: python3 verify.py [--quiet]
"""

import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
failures = []
checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def main():
    sources = load("sources.json")["sources"]
    src_ids = {s["id"] for s in sources}
    methods = load("methods.json")["methods"]
    costs = load("costs.json")
    penalties = load("penalties.json")
    questions = load("questions.json")["questions"]
    flagged = load("flagged.json")["items"]
    review = load("review.json")

    # --- 1. ledger integrity -------------------------------------------------
    ok(len(src_ids) == len(sources), "duplicate source ids in the ledger")
    ok(len(src_ids) >= 30, f"ledger looks thin: {len(src_ids)} sources")
    for s in sources:
        ok(bool(re.match(r"^https?://", s["url"])), f"{s['id']} has no absolute http url")
        ok(s["status"] in ("verified", "referenced_only"), f"{s['id']} has unknown status")
        ok(len(s["facts"]) >= 1, f"{s['id']} has no facts")
        ok(bool(s["title"].strip()), f"{s['id']} has no title")

    used = set()

    def note(ids, where):
        for i in ids:
            used.add(i)
            ok(i in src_ids, f"{where} references missing source {i}")

    for m in methods:
        note(m["sources"], f"method {m['id']}")
    for q in questions:
        note(q["sources"], f"question {q['id']}")
        ok(len(q["known"]) > 20, f"{q['id']} has no 'known' content")
        ok(len(q["how"]) > 15, f"{q['id']} has no discovery suggestion")
    for f in flagged:
        note(f["sources"], f"flagged {f['id']}")
        ok(f["status"] in ("blank", "assumption"), f"{f['id']} has an unknown status")
    for layer in penalties["layers"]:
        note(layer["sources"], f"penalty {layer['id']}")
    note(penalties["worked_example"]["sources"], "worked example")
    for i in review["irregularities"]:
        note(i["sources"], f"review {i['id']}")
    for i in costs["rates"]["sources"]:
        note([i], "cost rates")

    unused = src_ids - used
    ok(not unused, f"sources in the ledger never used: {sorted(unused)}")

    # --- 2. arithmetic -------------------------------------------------------
    r = costs["rates"]
    boc_buy, boc_sell = r["boc_buy"], r["boc_sell"]
    hsbc_buy, hsbc_sell = r["hsbc_buy"], r["hsbc_sell"]
    ok(abs(boc_buy - 6.6591) < 1e-9, "BOC buy does not match the board (665.91 per 100)")
    ok(abs(boc_sell - 6.6871) < 1e-9, "BOC sell does not match the board (668.71 per 100)")
    ok(abs(hsbc_sell - 6.7030239) < 1e-9, "HSBC sell does not match the board")

    def expected(usd, buy, sell, rate, fmin, fmax, cable, flat=0.0):
        mid = (buy + sell) / 2.0
        spread = usd * (sell - mid) / sell
        fee_cny = min(max(rate * usd * sell, fmin), fmax) + cable
        return round(spread + fee_cny / sell + flat, 2)

    ok(len(costs["rows"]) == 40, f"expected 40 cost rows, found {len(costs['rows'])}")
    ok([x["usd"] for x in costs["rows"]] == list(range(10000, 400001, 10000)),
       "cost rows are not USD 10,000 steps from 10,000 to 400,000")
    for row in costs["rows"]:
        usd = row["usd"]
        ok(abs(row["M01"]["total_usd"] - expected(usd, boc_buy, boc_sell, 0.001, 50, 260, 150)) <= 0.02,
           f"M01 arithmetic wrong at {usd}: {row['M01']['total_usd']}")
        ok(abs(row["M02"]["total_usd"] - expected(usd, hsbc_buy, hsbc_sell, 0.001, 100, 500, 120)) <= 0.02,
           f"M02 arithmetic wrong at {usd}: {row['M02']['total_usd']}")
        ok(abs(row["M03"]["total_usd"] - expected(usd, hsbc_buy, hsbc_sell, 0.0, 0, 0, 0)) <= 0.02,
           f"M03 arithmetic wrong at {usd}: {row['M03']['total_usd']}")
        ok(abs(row["M04"]["total_usd"] - expected(usd, hsbc_buy, hsbc_sell, 0.0, 0, 0, 0, 20.0)) <= 0.02,
           f"M04 arithmetic wrong at {usd}: {row['M04']['total_usd']}")
        cheapest = min(("M01", "M02", "M03", "M04"), key=lambda k: row[k]["total_usd"])
        ok(row["cheapest"] == cheapest, f"cheapest label wrong at {usd}")
        ok(row["M06"] is None and row["M07"] is None,
           f"M06/M07 must stay blank at {usd} because no fee is published")
        ok(row["M10"]["total_usd"] == 0.0, f"M10 must cost zero at {usd}")

    # --- 3. methods ----------------------------------------------------------
    ok(len(methods) >= 16, f"method catalogue is short: {len(methods)}")
    for m in methods:
        ok(bool(m["name"]) and bool(m["legality"]) and bool(m["limit"]), f"{m['id']} missing required fields")
        ok(len(m["cons"]) >= 1, f"{m['id']} has no cons")
        if m["priced"]:
            ok(bool(m["formula"]), f"priced method {m['id']} has no formula")
        else:
            ok(len(m["pros"]) + len(m["cons"]) >= 1, f"{m['id']} has no analysis")
        if m["category"].startswith("Prohibited"):
            ok(not m["pros"], f"prohibited method {m['id']} should not list pros")
            ok(m["steps"] == [], f"prohibited method {m['id']} should not give steps")

    # --- 4. blanks are flagged ----------------------------------------------
    flagged_text = " ".join(f["item"] + " " + f["reason"] for f in flagged).lower()
    for token in ("correspondent", "wise", "unionpay"):
        ok(token in flagged_text, f"blank for {token} is not on the flagged page")
    for m in methods:
        if not m["priced"] and m["category"].startswith(("Card", "Payment provider", "Unverified")):
            key = m["short"].lower()
            ok(key in flagged_text, f"unpriced method {m['id']} is not mentioned on the flagged page")

    # --- 5. penalty consistency ---------------------------------------------
    for s in penalties["scenarios"]:
        ok(abs(s["evasion_fine_low_usd"] - s["usd"] * 0.30) < 0.01, "30% evasion figure wrong")
        ok(abs(s["evasion_fine_high_usd"] - s["usd"] * 1.00) < 0.01, "100% evasion figure wrong")
        ok(s["fbar_willful_usd"] > s["lawful_boc_cost_usd"], "willful FBAR should exceed the lawful cost")
    ok(abs(penalties["fx_gain_pct"] - round((7.129 / boc_sell - 1) * 100, 4)) < 1e-6,
       "FX gain percentage does not follow from 7.129 and the BOC sell rate")

    # --- 6. pages ------------------------------------------------------------
    nav_targets = re.findall(r'<a class="[^"]*" href="([^"]+)"', open(os.path.join(HERE, "index.html"), encoding="utf-8").read())
    pages = sorted(f for f in os.listdir(HERE) if f.endswith(".html"))
    ok(len(pages) == 9, f"expected 9 pages, found {len(pages)}")
    for t in nav_targets:
        ok(t in pages, f"nav target {t} missing")

    for f in pages:
        path = os.path.join(HERE, f)
        text = open(path, encoding="utf-8").read()
        ok(">None<" not in text, f"{f} contains a leaked None")
        ok(not re.search(r"\bnan\b", text), f"{f} contains a leaked nan")
        for bad in ("TODO", "{r[", "undefined"):
            ok(bad not in text, f"{f} contains {bad!r}")
        for m in re.finditer(r'href="([^"]+)"', text):
            u = html.unescape(m.group(1))
            if u.startswith(("http", "#", "mailto:")):
                continue
            ok(os.path.exists(os.path.join(HERE, u.split("#")[0])), f"{f} links to missing {u}")
        if f == "sources.html":
            for sid in src_ids:
                ok(f'id="{sid}"' in text, f"sources page missing anchor {sid}")

    # every cost row on the cost page must link to a source
    cost_page = open(os.path.join(HERE, "costs.html"), encoding="utf-8").read()
    body = cost_page.split("<h2>Full ladder</h2>")[1].split("</thead>")[1].split("</table>")[0]
    rows = [x for x in body.split("<tr>") if x.strip() and "<td" in x]
    ok(len(rows) == 40, f"cost page should render 40 data rows, found {len(rows)}")
    for row in rows:
        ok("sources.html#S01" in row or "sources.html#S02" in row, "a cost row has no source link")
    ok("sources.html#S01" in cost_page and "sources.html#S04" in cost_page,
       "cost page does not cite the rate and fee sources")

    for f in ("methods.html", "penalty.html", "questions.html", "flagged.html", "review.html"):
        text = open(os.path.join(HERE, f), encoding="utf-8").read()
        ok("sources.html#S" in text, f"{f} has no source links")

    # --- 7. review reproducibility -----------------------------------------
    ok(review["totals"]["files_scanned"] > 250, "review scanned suspiciously few files")
    ok(len(review["irregularities"]) >= 5, "review lists too few irregularities")

    _ = questions  # counts above already validated

    print(f"checks run: {checks}")
    if failures:
        print(f"FAILED: {len(failures)}")
        for f in failures[:40]:
            print(" -", f)
        return 1
    print("all checks passed")
    print(f"sources={len(src_ids)} methods={len(methods)} rows={len(costs['rows'])} "
          f"questions={len(questions)} flagged={len(flagged)} irregularities={len(review['irregularities'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
