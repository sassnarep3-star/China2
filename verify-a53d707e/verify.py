#!/usr/bin/env python3
"""Verifier for this session's verification record.

It checks that the published page is internally consistent and that every table
row carries a link to an official document. It does NOT re-fetch those documents
and cannot prove that a citation is accurate: that is asserted by the human-
readable locator in each row and was performed by opening the source. This tool
is a structure/consistency gate, not a factual oracle.
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "index.html"

OFFICIAL_HOSTS = {
    "www.safe.gov.cn",
    "www.chinatax.gov.cn",
    "www.irs.gov",
    "www.govinfo.gov",
    "www.ecfr.gov",
    "www.hsbc.com.cn",
}

EXPECTED = {"claims": 15, "blanks": 8, "irregularities": 2, "notes": 2, "sources": 12}
STATED = {"12": "official documents re-fetched", "15": "published values checked",
          "13": "confirmed exactly", "2": "confirmed with a wording note",
          "8": "values left blank", "2": "open irregularities",
          "2": "navigation notes"}

CHECKS = 0
FAILS: list[str] = []


def check(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(msg)


class Doc(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.rows: list[list[str]] = []
        self.in_body_table = False
        self._row: list[str] | None = None
        self._row_text: list[str] = []
        self.tables: list[dict] = []
        self._table: dict | None = None
        self.h1 = 0
        self.scripts = 0
        self.styles = 0
        self.has_viewport = False
        self.lang = ""
        self.text: list[str] = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "meta" and a.get("name") == "viewport":
            self.has_viewport = True
        if tag == "h1":
            self.h1 += 1
        if tag == "script":
            self.scripts += 1
        if tag == "style":
            self.styles += 1
        if tag == "table":
            self._table = {"rows": [], "caption": ""}
        if tag == "caption" and self._table is not None:
            self._in_caption = True
        if tag == "tbody" and self._table is not None:
            self.in_body_table = True
        if tag == "tr" and self.in_body_table:
            self._row = []
            self._row_text = []
        for key in ("href", "src"):
            if key in a:
                self.links.append(a[key])
                if self._row is not None:
                    self._row.append(a[key])

    def handle_endtag(self, tag):
        if tag == "caption":
            self._in_caption = False
        if tag == "tr" and self._row is not None:
            self._table["rows"].append(self._row)
            self.rows.append(self._row)
            self._row = None
        if tag == "tbody":
            self.in_body_table = False
        if tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    _in_caption = False

    def handle_data(self, data):
        if self._table is not None and self._in_caption:
            self._table["caption"] += data
        self.text.append(data)


def main() -> int:
    check(PAGE.exists(), "index.html missing")
    if not PAGE.exists():
        print("\n".join(FAILS))
        return 1
    html = PAGE.read_text(encoding="utf-8")
    doc = Doc(html)
    text = re.sub(r"\s+", " ", "".join(doc.text))

    # --- document basics -----------------------------------------------------
    check(doc.lang.startswith("en"), "html lang must be English")
    check(doc.has_viewport, "viewport meta missing (mobile layout)")
    check(doc.h1 == 1, f"expected exactly one h1, found {doc.h1}")
    check(doc.scripts == 0, "page must not need JavaScript")
    check("@media(max-width:760px)" in html.replace(" ", ""),
          "mobile stacking media query missing")
    check("data-label=" in html, "responsive data-label attributes missing")
    check("<title>" in html and "Verification record" in html, "title missing")
    check('name="description"' in html, "meta description missing")
    check("not tax or legal advice" in text, "disclaimer missing")
    check("unverified" in text.lower(), "blank/unverified wording missing")

    # --- row counts ----------------------------------------------------------
    claim_ids = re.findall(r'class="num">(C\d\d)<', html)
    blank_ids = re.findall(r'class="num">(B\d\d)<', html)
    irr_ids = re.findall(r'class="num">(I\d\d)<', html)
    note_ids = re.findall(r'class="num">(N\d\d)<', html)
    check(len(claim_ids) == EXPECTED["claims"],
          f"expected {EXPECTED['claims']} confirmed-claim rows, found {len(claim_ids)}")
    check(len(blank_ids) == EXPECTED["blanks"],
          f"expected {EXPECTED['blanks']} blank rows, found {len(blank_ids)}")
    check(len(irr_ids) == EXPECTED["irregularities"],
          f"expected {EXPECTED['irregularities']} irregularity rows, found {len(irr_ids)}")
    check(len(note_ids) == EXPECTED["notes"],
          f"expected {EXPECTED['notes']} navigation-note rows, found {len(note_ids)}")
    check(claim_ids == [f"C{i:02d}" for i in range(1, EXPECTED["claims"] + 1)],
          "confirmed-claim ids must run C01..C15 in order")
    check(blank_ids == [f"B{i:02d}" for i in range(1, EXPECTED["blanks"] + 1)],
          "blank ids must run B01..B08 in order")
    check(irr_ids == [f"I{i:02d}" for i in range(1, EXPECTED["irregularities"] + 1)],
          "irregularity ids must run I01..I02 in order")
    check(note_ids == [f"N{i:02d}" for i in range(1, EXPECTED["notes"] + 1)],
          "navigation-note ids must run N01..N02 in order")

    # --- every table body row carries an official link -----------------------
    check(len(doc.tables) >= 4, "expected at least four data tables")
    for t_i, table in enumerate(doc.tables):
        caption = " ".join(table["caption"].split())
        # The navigation-notes table is the one table that cannot carry an official
        # source by definition; it must say so in its caption instead.
        if caption.startswith("N01"):
            check("no official source" in table["caption"].lower(),
                  "navigation-notes table must state that no official source applies")
            continue
        for r_i, row in enumerate(table["rows"]):
            ext = [h for h in row if h.startswith(("http://", "https://"))]
            official = [h for h in ext if urlsplit(h).hostname in OFFICIAL_HOSTS]
            check(bool(official),
                  f"table {t_i + 1} row {r_i + 1} has no official-source link")
            for h in ext:
                check(urlsplit(h).hostname in OFFICIAL_HOSTS,
                      f"table {t_i + 1} row {r_i + 1}: non-official host {h}")
                check(h.startswith("https://"),
                      f"table {t_i + 1} row {r_i + 1}: non-HTTPS link {h}")

    # --- source count and host spread ---------------------------------------
    official_urls = {h for h in doc.links
                     if h.startswith("https://") and urlsplit(h).hostname in OFFICIAL_HOSTS}
    check(len(official_urls) == EXPECTED["sources"],
          f"expected {EXPECTED['sources']} distinct official documents, found {len(official_urls)}")
    hosts = {urlsplit(u).hostname for u in official_urls}
    check(hosts == OFFICIAL_HOSTS,
          f"host set mismatch: {sorted(hosts)}")

    # --- the numbers in the status strip match the rows ----------------------
    for n, label in STATED.items():
        pattern = rf"<b>{n}</b><span>{re.escape(label)}</span>"
        check(bool(re.search(pattern, html)), f"status strip lacks '{n} {label}'")

    # --- local links resolve -------------------------------------------------
    for href in doc.links:
        if href.startswith(("http://", "https://", "mailto:", "#")):
            if href.startswith("#"):
                check(unquote(href[1:]) in doc.ids, f"missing fragment {href}")
            continue
        path, _, frag = href.partition("#")
        target = (ROOT / unquote(path)).resolve()
        check(target.exists(), f"local link target missing: {href}")
        if frag and target.suffix == ".html" and target.exists():
            target_doc_ids = re.findall(r'id="([^"]+)"', target.read_text(encoding="utf-8"))
            check(frag in target_doc_ids, f"missing fragment {href}")

    # --- applied corrections are stated, not hidden -------------------------
    check("30–100%" in html or "30-100%" in html,
          "the briefing fine-band irregularity must be quoted")
    check("Decree 532" in html and "Art. 42" in html,
          "fine-band row must cite the statute and the 20% cash rule")
    check("ISO" not in html and "TODO" not in html and "lorem" not in html.lower(),
          "placeholder text left on the page")
    check("$16,536" in html and "$165,353" in html,
          "FBAR penalty maxima must be stated with their values")

    # --- workflow present ----------------------------------------------------
    wf = ROOT.parent / ".github" / "workflows" / "verify-a53d707e.yml"
    check(wf.exists(), "CI workflow missing")
    if wf.exists():
        check("verify.py" in wf.read_text(encoding="utf-8"),
              "CI workflow must run this verifier")

    print(f"{CHECKS} checks, {len(FAILS)} failures")
    for f in FAILS:
        print("FAIL:", f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
