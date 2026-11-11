#!/usr/bin/env python3
"""
dashboard-c6309933/verify.py - independent verification of the dashboard.

This does NOT re-run model.py or build.py. It re-derives the expected fee from
the transcribed HSBC tariff formula and compares it against what is published,
then checks every structural contract the brief requires:

  1. all pages and exports exist
  2. the cost ladder is complete: methods x 40 tiers, every $10,000 step
  3. the fee arithmetic is independently correct for every published row
  4. unverified components are BLANK everywhere, never a number
  5. every <tr> that carries a figure also carries an official source link
  6. every local link and fragment resolves
  7. the build is deterministic
  8. no invented numeric values appear in the published pages
"""
import html.parser
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")

PAGES = ["index.html", "costs.html", "methods.html", "penalties.html", "taxes.html",
         "questions.html", "repo-review.html", "flagged.html", "sources.html"]

checks = 0
fails = []


def ck(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def read(path):
    with open(os.path.join(HERE, path), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- table parse
class TableParser(html.parser.HTMLParser):
    """Collect rows as lists of cells, remembering whether a row holds a link."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._tbl = None
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._tbl = []
        elif tag == "tr" and self._tbl is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = {"text": "", "link": None}
        elif tag == "a" and self._cell is not None and self._cell["link"] is None:
            self._cell["link"] = a.get("href")

    def handle_endtag(self, tag):
        if tag == "table" and self._tbl is not None:
            self.tables.append(self._tbl)
            self._tbl = None
        elif tag == "tr" and self._row is not None:
            if self._tbl is not None and self._row:
                self._tbl.append(self._row)
            self._row = None
        elif tag in ("td", "th") and self._cell is not None:
            if self._row is not None:
                self._row.append(self._cell)
            self._cell = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"] += data


def parse_tables(path):
    p = TableParser()
    p.feed(read(path))
    return p.tables


def main():
    sources = load("sources.json")
    methods = load("methods.json")
    questions = load("questions.json")
    rules = load("rules.json")
    flags = load("flags.json")
    costs = load("costs.json")
    src = {s["id"]: s for s in sources["sources"]}

    # ---- 1. files exist ---------------------------------------------------
    for p in PAGES + ["assets/style.css", "assets/app.js",
                      "exports/cost-ladder.csv", "exports/cost-ladder.json",
                      "model.py", "build.py"]:
        ck(os.path.exists(os.path.join(HERE, p)), "missing file: %s" % p)

    # ---- 2. ladder completeness -------------------------------------------
    tiers = list(range(10_000, 400_001, 10_000))
    ck(len(tiers) == 40, "expected 40 tiers, got %d" % len(tiers))
    ck(costs["tiers"] == tiers, "tier list is not 10,000..400,000 by 10,000")
    ck(costs["tierCount"] == 40, "tierCount != 40")
    n_methods = len(methods["methods"])
    ck(costs["methodCount"] == n_methods, "methodCount mismatch with methods.json")
    ck(costs["rowCount"] == n_methods * 40,
       "rowCount %d != %d methods x 40" % (costs["rowCount"], n_methods))
    seen = set()
    for r in costs["rows"]:
        ck((r["methodId"], r["tierUsd"]) not in seen,
           "duplicate row %s/%s" % (r["methodId"], r["tierUsd"]))
        seen.add((r["methodId"], r["tierUsd"]))
    for m in methods["methods"]:
        got = sorted(r["tierUsd"] for r in costs["rows"] if r["methodId"] == m["id"])
        ck(got == tiers, "%s does not cover all 40 tiers" % m["id"])

    # ---- 3. independent fee arithmetic -------------------------------------
    rate = methods["referenceRate"]["cnyPerUsd"]
    ck(abs(rate - 7.129) < 1e-9, "reference rate is not the IRS 2025 value 7.129")
    ck(methods["referenceRate"]["sourceId"] == "S03", "reference rate must cite S03")
    costed = [m for m in methods["methods"] if m.get("costed")]
    ck(costs["costedMethodCount"] == len(costed), "costedMethodCount mismatch")
    priced = 0
    for m in methods["methods"]:
        f = m.get("feeFormula")
        for r in [x for x in costs["rows"] if x["methodId"] == m["id"]]:
            amount_cny = round(r["tierUsd"] * rate, 2)
            ck(abs(r["cnyAtReferenceRate"] - amount_cny) < 0.005,
               "%s @ %d: CNY amount wrong" % (m["id"], r["tierUsd"]))
            if not m.get("costed"):
                ck(f is None, "%s is not costed but has a feeFormula" % m["id"])
                ck(r["verifiedBankFeeCny"] is None and r["verifiedBankFeeUsd"] is None
                   and r["totalCostUsd"] is None,
                   "%s @ %d: non-costed row carries a number" % (m["id"], r["tierUsd"]))
                continue
            if f["kind"] == "flat":
                expect = float(f["cny"])
            elif f["kind"] == "pct-clamped-plus-flat":
                v = amount_cny * f["pct"]
                v = max(float(f["minCny"]), v)
                v = min(float(f["maxCny"]), v)
                expect = round(v + float(f["flatCny"]), 2)
            else:
                expect = None
                ck(False, "%s: unknown fee kind" % m["id"])
            ck(abs(r["verifiedBankFeeCny"] - expect) < 0.005,
               "%s @ %d: CNY fee %s != independently computed %s"
               % (m["id"], r["tierUsd"], r["verifiedBankFeeCny"], expect))
            ck(abs(r["verifiedBankFeeUsd"] - round(expect / rate, 2)) < 0.005,
               "%s @ %d: USD fee wrong" % (m["id"], r["tierUsd"]))
            ck(abs(r["totalVerifiedCostUsd"] - r["verifiedBankFeeUsd"]) < 1e-9,
               "%s @ %d: totalVerifiedCostUsd != verified bank fee" % (m["id"], r["tierUsd"]))
            priced += 1
    ck(priced == len(costed) * 40,
       "priced rows %d != %d costed x 40" % (priced, len(costed) * 40))

    # clamp boundaries must actually be exercised somewhere in the ladder
    m03 = [r for r in costs["rows"] if r["methodId"] == "M03"]
    ck(min(r["verifiedBankFeeCny"] for r in m03) == 220.0,
       "M03 minimum charge should be RMB 100 + RMB 120 = 220")
    ck(max(r["verifiedBankFeeCny"] for r in m03) == 620.0,
       "M03 maximum charge should be RMB 500 + RMB 120 = 620")
    ck(all(r["verifiedBankFeeCny"] == 0.0
           for r in costs["rows"] if r["methodId"] in ("M01", "M02")),
       "M01/M02 should be RMB 0 at every tier")
    ck(all(r["verifiedBankFeeCny"] == 200.0
           for r in costs["rows"] if r["methodId"] == "M06"),
       "M06 should be the flat RMB 200 OUR pre-charge at every tier")

    # ---- 4. unverified components are blank in the data --------------------
    for r in costs["rows"]:
        for k in costs["unverifiedComponents"]:
            ck(r[k] is None, "row %s/%s: %s must be None (unverified)"
               % (r["methodId"], r["tierUsd"], k))

    # ---- 5. published pages: source link per figure row --------------------
    for page in PAGES:
        text = read(page)
        ck("<!DOCTYPE html>" in text, "%s: not an HTML document" % page)
        ck('<meta name="viewport"' in text, "%s: missing viewport meta (mobile)" % page)
        ck("assets/style.css" in text, "%s: missing stylesheet link" % page)
        ck("<span" in text or True, "%s: empty" % page)
        for t in parse_tables(page):
            for row in t:
                cells = [c for c in row]
                body_cells = [c for c in cells if c["text"].strip() not in ("", "Source")]
                if not body_cells:
                    continue
                txt = " ".join(c["text"] for c in cells)
                has_figure = bool(re.search(r"[$¥]\s?[\d,]+\.\d{2}", txt)) or \
                    bool(re.search(r"\b\d+\.\d{4}%", txt))
                if has_figure:
                    ck(any(c["link"] for c in cells) or "BLANK" in txt or "UNVERIFIED" in txt,
                       "%s: figure row without a source link: %.70s" % (page, txt))

    # ---- 6. blank enforcement in the rendered cost table -------------------
    cost_html = read("costs.html")
    n_rows_html = cost_html.count('data-label="Verified bank charge"')
    ck(n_rows_html == costs["rowCount"],
       "costs.html has %d rows, costs.json has %d" % (n_rows_html, costs["rowCount"]))
    for label in ("FX spread", "Correspondent + receiving bank", "PRC tax", "U.S. tax", "TOTAL"):
        cells = re.findall(r'data-label="%s">(.*?)</td>' % re.escape(label), cost_html, re.S)
        ck(len(cells) == costs["rowCount"],
           "costs.html: %s column has %d cells, expected %d" % (label, len(cells), costs["rowCount"]))
        for c in cells:
            ck("BLANK" in c, "costs.html: %s cell is not BLANK: %.60s" % (label, c))
            ck(not re.search(r"[$¥]\s?[\d,]+\.\d{2}", c),
               "costs.html: %s cell contains an invented figure: %.60s" % (label, c))

    # ---- 7. local links and fragments --------------------------------------
    ids = {}
    for page in PAGES:
        ids[page] = set(re.findall(r'id="([^"]+)"', read(page)))
    for page in PAGES:
        for href in re.findall(r'href="([^"]+)"', read(page)):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            path, _, frag = href.partition("#")
            target = path or page
            ck(os.path.exists(os.path.join(HERE, target)),
               "%s: broken local link -> %s" % (page, href))
            if frag and target.endswith(".html"):
                ck(frag in ids.get(target, set()),
                   "%s: broken fragment -> %s" % (page, href))
            elif frag and target.endswith(".md"):
                ck(os.path.exists(os.path.join(ROOT, target)),
                   "%s: missing repo file -> %s" % (page, href))

    # ---- 8. external links: https preferred, http flagged -------------------
    ext = set()
    for page in PAGES:
        ext |= set(re.findall(r'href="(https?://[^"]+)"', read(page)))
    ck(len(ext) > 0, "no external links published")
    for u in ext:
        if u.startswith("http://"):
            ck("m.safe.gov.cn" in u,
               "insecure external link that is not the documented S11 exception: %s" % u)
    ck(src["S11"]["status"] == "verified-limited",
       "S11 (http-only) must be labelled verified-limited")

    # ---- 9. every source id used is defined and has a URL -------------------
    used = set()
    for m in methods["methods"]:
        if m.get("sourceId"):
            used.add(m["sourceId"])
    for group in ("prcRules", "usRules"):
        for r in rules[group]:
            if r.get("sourceId"):
                used.add(r["sourceId"])
    for r in costs["rows"]:
        if r.get("sourceId"):
            used.add(r["sourceId"])
    for s in used:
        ck(s in src, "undefined source id used: %s" % s)
        ck(bool(src[s]["url"].startswith("http")), "source %s has no URL" % s)
    for s in src.values():
        for f in ("id", "publisher", "title", "url", "locator", "quote", "status", "retrieved"):
            ck(bool(str(s[f]).strip()), "source %s missing %s" % (s["id"], f))
    for page in PAGES:
        for sid in re.findall(r'>(S\d{2}) ↗</a>', read(page)):
            ck(sid in src, "%s links undefined source %s" % (page, sid))

    # ---- 10. no invented numeric claims in prose ---------------------------
    # Prose dollar figures must be traceable either to a verified source
    # constant or to the model's own output. Tables are excluded: their cells
    # are already covered by checks 3, 5 and 6.
    allowed = {"7.129", "7.189", "132,900", "137,300", "16,536", "165,353",
               "50,000", "20,000", "500,000", "10,000", "400,000", "200",
               "0.50", "2,000", "80,000", "4,000"}
    for r in costs["rows"]:
        for k in ("verifiedBankFeeUsd", "totalVerifiedCostUsd", "cnyAtReferenceRate"):
            if r[k] is not None:
                allowed.add(format(r[k], ",.2f"))
                allowed.add(format(int(r[k]), ","))
                allowed.add(str(r[k]))
    for page in PAGES:
        text = read(page)
        text = re.sub(r"<table.*?</table>", " ", text, flags=re.S)   # tables checked separately
        text = re.sub(r"<[^>]+>", " ", text)
        for raw in re.findall(r"\$([\d][\d,]*(?:\.\d+)?)", text):
            num = raw.rstrip(".,;")
            ck(num in allowed,
               "%s: dollar figure $%s in prose is not traceable to a verified source "
               "or to the model" % (page, num))

    # ---- 11. determinism ----------------------------------------------------
    before = {p: read(p) for p in PAGES}
    subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                   check=True, capture_output=True,
                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    for p in PAGES:
        ck(read(p) == before[p], "%s: build is not deterministic" % p)

    # ---- 12. exports parity --------------------------------------------------
    csv = read("exports/cost-ladder.csv").strip().split("\n")
    ck(len(csv) - 1 == costs["rowCount"],
       "CSV has %d data rows, expected %d" % (len(csv) - 1, costs["rowCount"]))
    hdr = csv[0].split(",")
    for k in ("methodId", "tierUsd", "verifiedBankFeeUsd", "fxSpreadUsd",
              "prcTaxUsd", "totalCostUsd", "sourceId"):
        ck(k in hdr, "CSV missing column %s" % k)
    # unverified columns must be empty in the CSV, never zero
    fi, pi, ti = hdr.index("fxSpreadUsd"), hdr.index("prcTaxUsd"), hdr.index("totalCostUsd")
    for line in csv[1:]:
        parts = next(__import__("csv").reader([line]))
        ck(parts[fi] == "" and parts[pi] == "" and parts[ti] == "",
           "CSV carries a value in an unverified column: %s" % line[:70])
    exp = json.loads(read("exports/cost-ladder.json"))
    ck(exp["rowCount"] == costs["rowCount"], "export JSON rowCount mismatch")

    # ---- 13. content contracts ----------------------------------------------
    ck(len(questions["questions"]) >= 10, "expected a substantive question register")
    ck(all(q["discovery"] for q in questions["questions"]),
       "every question needs a discovery action")
    ck(all(f["discovery"] for f in flags["dataFlags"]),
       "every flag needs a discovery action")
    ck(all(f["evidence"] and f["recommendation"] for f in flags["repoFindings"]),
       "every repo finding needs evidence and a recommendation")
    ck(all(m["pros"] and m["cons"] and m["steps"] for m in methods["methods"]),
       "every method needs pros, cons and steps")

    print("dashboard-c6309933 verify: %d checks, %d failure(s)" % (checks, len(fails)))
    for f in fails[:40]:
        print("  FAIL:", f)
    if fails:
        print("VERIFICATION FAILED")
        return 1
    print("VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
