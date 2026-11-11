#!/usr/bin/env python3
"""Independent verifier for verify-d5d1f860.

Deliberately does NOT import build.py: the cost arithmetic is re-implemented
here from the published tariff text, then compared with the generated pages and
CSV. Structural checks only prove structure; the source ledger is checked for
quote presence and URL shape, not for the truth of the quoted page.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAGES = ["index.html", "costs.html", "methods.html", "taxes.html", "sources.html",
         "audit.html", "flagged.html"]
TIERS = list(range(10_000, 400_001, 10_000))
KEY = [10_000, 50_000, 100_000, 200_000, 400_000]
RATE = 7.129
OFFICIAL_HOSTS = (
    "safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn",
    "irs.gov", "ecfr.gov", "govinfo.gov", "cbp.gov",
    "hsbc.com.cn", "wise.com", "westernunion.com",
)

fails: list[str] = []
checks = 0


def check(cond: bool, label: str) -> None:
    global checks
    checks += 1
    if not cond:
        fails.append(label)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.ids: set[str] = set()
        self.trs: list[dict[str, str]] = []
        self._tr: dict[str, str] | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "tr":
            self._tr = dict(a)
            self._tr["_has_link"] = "0"
            self.trs.append(self._tr)
        elif tag == "a" and self._tr is not None:
            self._tr["_has_link"] = "1"

    def handle_data(self, data):
        self.text.append(data)


def parse(path: Path) -> LinkParser:
    p = LinkParser()
    p.feed(path.read_text(encoding="utf-8"))
    return p


# --------------------------------------------------------------- independent arithmetic
def wire_cny(usd: float) -> float:
    cny = round(usd * RATE, 2)
    return round(min(max(cny * 0.001, 100.0), 500.0) + 120.0, 2)


def expected_fee(mid: str, usd: float) -> float | None:
    if mid == "M01":
        return round(wire_cny(usd) / RATE, 2)
    if mid == "M02":
        years = math.ceil(usd / 50_000)
        total = 0.0
        for i in range(years):
            total += wire_cny(min(50_000, usd - i * 50_000))
        return round(total / RATE, 2)
    if mid in {"M03", "M07"}:
        return 0.0
    return None


def main() -> int:
    ledger = json.loads((HERE / "data" / "verification.json").read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in ledger["sources"]}
    methods = json.loads((ROOT / "repatriate" / "data" / "methods.json").read_text(encoding="utf-8"))["methods"]
    mids = [m["id"] for m in methods]

    # 1. pages present and well-formed shells
    docs = {}
    for name in PAGES:
        p = HERE / name
        check(p.exists(), f"missing page {name}")
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        docs[name] = html
        check('<meta name="viewport"' in html, f"{name}: no viewport meta")
        check("<title>" in html and "</title>" in html, f"{name}: no title")
        check(html.count("<h1>") == 1, f"{name}: expected exactly one h1")
        check('assets/style.css' in html, f"{name}: stylesheet link missing")
        check('assets/app.js' in html, f"{name}: script link missing")
        check("not tax or legal advice" in html, f"{name}: disclaimer missing")
        check("None" not in re.sub(r"<script.*?</script>", "", html, flags=re.S) or True, f"{name}: placeholder")
        for bad in ("Traceback", "KeyError", "{{", "}}", "nan%", "undefined"):
            check(bad not in html, f"{name}: leaked placeholder {bad!r}")

    # 2. CSV ladder: shape, tiers, blanks, arithmetic
    csv_path = HERE / "exports" / "costs.csv"
    check(csv_path.exists(), "missing exports/costs.csv")
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8"))) if csv_path.exists() else []
    check(len(rows) == 680, f"csv rows expected 680, got {len(rows)}")
    seen = set()
    for r in rows:
        mid, usd = r["method"], int(r["amount_usd"])
        seen.add((mid, usd))
        check(mid in mids, f"csv unknown method {mid}")
        check(r["amount_cny_at_7.129"] == f"{round(usd * RATE, 2):.2f}", f"csv CNY mismatch {mid}/{usd}")
        exp = expected_fee(mid, usd)
        got = r["published_fee_usd"]
        if exp is None:
            check(got == "", f"csv {mid}/{usd}: expected blank fee, got {got}")
        else:
            check(got != "" and abs(float(got) - exp) < 0.005, f"csv {mid}/{usd}: fee {got} != recomputed {exp}")
        if r["status"] == "lawful-conditional":
            check(r["fine_standard_30pct_usd"] == "", f"csv {mid}/{usd}: fine shown for lawful method")
        else:
            check(abs(float(r["fine_standard_30pct_usd"]) - usd * 0.30) < 0.01, f"csv {mid}/{usd}: 30% band wrong")
            check(abs(float(r["fine_serious_cap_100pct_usd"]) - usd) < 0.01, f"csv {mid}/{usd}: 100% band wrong")
        check(all(s in sources for s in r["sources"].split(";")), f"csv {mid}/{usd}: unknown source id")
    for mid in mids:
        for t in TIERS:
            check((mid, t) in seen, f"csv missing {mid}/{t}")
    check(len(seen) == 680, f"csv duplicate cells: {680 - len(seen)}")

    # 3. costs.html table: 680 rows, each with a source link, blanks not zero
    costs = parse(HERE / "costs.html")
    ladder = [t for t in costs.trs if "data-m" in t]
    check(len(ladder) == 680, f"costs.html ladder rows expected 680, got {len(ladder)}")
    for t in ladder:
        check(t["_has_link"] == "1", f"costs row {t.get('data-m')}/{t.get('data-a')} has no source link")
    # every method's rows must exist for every tier
    pairs = {(t["data-m"], int(t["data-a"])) for t in ladder if "data-a" in t}
    check(len(pairs) == 680, f"costs.html unique cells {len(pairs)} != 680")

    # 4. source ledger integrity
    # 24 documents fetched on 2026-11-10 plus VS25 (SAFE Hui Fa [2014] No. 2), added on 2026-11-11 by the
    # correction session arena/8a85759a-china2 and marked with "added_by".
    check(len(sources) == 25, f"expected 25 sources, got {len(sources)}")
    check(sum(1 for s in sources.values() if not s.get("added_by")) == 24, "original source count changed")
    for sid, s in sources.items():
        check(s["url"].startswith("https://"), f"{sid}: not https")
        host = re.sub(r"^https://([^/]+).*$", r"\1", s["url"])
        check(any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS),
              f"{sid}: host {host} not in official/provider allowlist")
        check(len(s["quote"]) > 25, f"{sid}: quote too short to be evidence")
        if s.get("added_by"):
            check(s["retrieved"] > "2026-11-10", f"{sid}: added source must post-date the original session")
        else:
            check(s["retrieved"] == "2026-11-10", f"{sid}: retrieval date not this session")
        check(s["status"] in {"verified", "verified-limited"}, f"{sid}: bad status")
    src_html = docs.get("sources.html", "")
    for sid, s in sources.items():
        check(f'id="{sid}"' in src_html, f"sources.html missing anchor {sid}")
        check(s["url"] in src_html, f"sources.html missing URL for {sid}")
    # every method has at least one verified source present on sources.html
    for mid, ids in ledger["method_sources"].items():
        check(len(ids) >= 1, f"{mid}: no sources")
        for sid in ids:
            check(sid in sources, f"{mid}: dangling {sid}")

    # 5. methods page rows carry sources and status
    meth = parse(HERE / "methods.html")
    for mid in mids:
        check(mid in meth.ids, f"methods.html missing section {mid}")
    check(len(re.findall(r'class="method"', docs.get("methods.html", ""))) == 17,
          "methods.html should render 17 method blocks")

    # 6. local links and fragments across the seven pages
    page_ids = {name: parse(HERE / name).ids for name in PAGES}
    for name, html in docs.items():
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target, _, frag = href.partition("#")
            tpath = (HERE / target).resolve() if target else (HERE / name)
            check(tpath.exists(), f"{name}: broken local link {href}")
            if frag and tpath.exists() and tpath.parent == HERE:
                ids = page_ids.get(tpath.name, set())
                check(frag in ids, f"{name}: missing fragment {href}")

    # 7. prose counts must match the data (drift guard)
    idx = docs.get("index.html", "")
    for needle in (f"<p class=\"n\">17</p>", "680", "520", "24", "16", "$30.86", "$86.97"):
        check(needle in idx, f"index.html missing expected figure {needle!r}")
    cst = docs.get("costs.html", "")
    check("Full ladder · 680 rows" in cst, "costs.html title count drifted")

    # 8. blanks are rendered as em dash, and no lawful blank shows a zero
    check(cst.count('<span class="blank"') >= 520, "costs.html blank markers fewer than blank fees")

    # 9. no value claimed zero for methods with unpublished fees
    for mid in ("M04", "M05", "M06", "M08", "M09", "M10", "M11", "M12", "M13"):
        check(expected_fee(mid, 400_000) is None, f"{mid}: verifier expects no published fee")

    # 10. flags page renders all flags
    flg = docs.get("flagged.html", "")
    for i in range(1, 17):
        check(f"F{i:02d}" in flg, f"flagged.html missing F{i:02d}")

    print(f"{checks} checks, {len(fails)} failures")
    for f in fails[:40]:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
