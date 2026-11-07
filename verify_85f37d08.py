#!/usr/bin/env python3
"""Automated line-by-line verifier for portal/, reports/, official source domains, blank unverified cells, and local link integrity."""

from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json

ROOT = Path(__file__).resolve().parent
PORTAL = ROOT / "portal"
LEDGER = ROOT / "reports" / "CNY_TO_USD_RESEARCH_LEDGER.json"

OFFICIAL_SUFFIXES = (".gov", ".gov.cn")


def is_official_gov_url(url: str) -> bool:
    u = urlsplit(url)
    if u.scheme not in ("https", "http") or not u.hostname:
        return False
    host = u.hostname.lower()
    return any(host == s.lstrip(".") or host.endswith(s) for s in OFFICIAL_SUFFIXES)


class PortalPageParser(HTMLParser):
    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = set()
        self.links = []
        self.tbody_rows = []
        self._in_tbody = False
        self._cur_row_links = None
        self._cur_row_cells = None
        self._in_td = False
        self._td_buf = []
        self.h1_count = 0
        self.nav_current = 0
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            assert a["id"] not in self.ids, f"Duplicate id {a['id']} in {self.path}"
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1_count += 1
        if a.get("aria-current") == "page":
            self.nav_current += 1
        if tag == "tbody":
            self._in_tbody = True
        elif tag == "tr" and self._in_tbody:
            self._cur_row_links = []
            self._cur_row_cells = []
        elif tag == "td" and self._cur_row_cells is not None:
            self._in_td = True
            self._td_buf = []

        for key in ("href", "src"):
            if key in a:
                self.links.append(a[key])
                if self._cur_row_links is not None and key == "href":
                    self._cur_row_links.append(a[key])

    def handle_data(self, data):
        if self._in_td:
            self._td_buf.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self._in_td:
            self._cur_row_cells.append("".join(self._td_buf).strip())
            self._in_td = False
        elif tag == "tr" and self._cur_row_links is not None:
            self.tbody_rows.append((self._cur_row_links, self._cur_row_cells))
            self._cur_row_links = None
            self._cur_row_cells = None
        elif tag == "tbody":
            self._in_tbody = False


def main() -> None:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))

    # 1. Ledger checks
    src_ids = [s["id"] for s in data["sources"]]
    assert len(src_ids) == len(set(src_ids)) >= 24, "Duplicate or missing sources"
    for s in data["sources"]:
        assert is_official_gov_url(s["url"]), f"Non-official source URL: {s['url']}"
        if s.get("secondary_url"):
            assert is_official_gov_url(s["secondary_url"]), f"Non-official secondary URL: {s['secondary_url']}"

    for m in data["methods"]:
        assert is_official_gov_url(m["source_url"]), f"Non-official method URL: {m['source_url']}"
        if m.get("extra_source_url"):
            assert is_official_gov_url(m["extra_source_url"]), f"Non-official extra URL: {m['extra_source_url']}"
        assert m["commercial_spread_wire_fee"] == "", f"Unverified commercial fee must be blank in {m['id']}"

    unverified_layers = 0
    for cp in data["conversion_penalty_layers"]:
        assert is_official_gov_url(cp["source_url"]), f"Non-official penalty URL: {cp['source_url']}"
        if cp["layer"].startswith("4."):
            assert cp["verified_rate_or_rule"] == "", f"Commercial layer must be blank in {cp['id']}"
            unverified_layers += 1
    assert unverified_layers == 3

    for tc in data["us_prc_compliance"]:
        assert is_official_gov_url(tc["source_url"]), f"Non-official compliance URL: {tc['source_url']}"

    for flg in data["flagged_items"]:
        assert is_official_gov_url(flg["source_url"]), f"Non-official flag URL: {flg['source_url']}"

    # 2. HTML page & link/anchor checks
    expected_pages = {
        "index.html",
        "methods.html",
        "conversion-penalties.html",
        "tax-compliance.html",
        "repo-audit.html",
        "flagged-for-review.html",
        "sources.html",
    }
    html_files = {p.name: PortalPageParser(p) for p in PORTAL.glob("*.html")}
    assert set(html_files.keys()) == expected_pages, f"Unexpected portal pages: {set(html_files.keys())}"

    total_rows = 0
    for name, parser in html_files.items():
        assert parser.h1_count == 1, f"{name} must have exactly 1 h1"
        assert parser.nav_current == 1, f"{name} must have 1 active nav tab"
        assert len(parser.tbody_rows) > 0, f"{name} has no table rows"
        for idx, (row_links, row_cells) in enumerate(parser.tbody_rows, start=1):
            total_rows += 1
            gov_links = [u for u in row_links if is_official_gov_url(u)]
            assert len(gov_links) >= 1, f"Row {idx} in {name} lacks official .gov / .gov.cn source link"
            if name == "methods.html":
                assert row_cells[5] == "", f"Commercial fee cell in methods.html row {idx} must be strictly blank"

        for link in parser.links:
            u = urlsplit(link)
            if u.scheme in ("https", "http"):
                assert is_official_gov_url(link), f"External link in {name} is not an official .gov/.gov.cn site: {link}"
                continue
            if u.scheme in ("mailto", "tel", "data"):
                continue
            target = ((PORTAL / unquote(u.path)).resolve() if u.path else (PORTAL / name).resolve())
            assert target.is_relative_to(ROOT.resolve()), f"Link escapes repo root: {link}"
            assert target.is_file(), f"Broken local link in {name}: {link} -> {target}"
            if u.fragment and target.parent == PORTAL and target.suffix == ".html":
                target_parser = html_files[target.name]
                assert unquote(u.fragment) in target_parser.ids, f"Broken fragment {link} in {name}"

    print(
        f"PASS verify_85f37d08: {len(html_files)} portal pages, {total_rows} table rows verified, "
        f"100% official .gov/.gov.cn external links, blank unverified cells enforced, 0 broken local links."
    )


if __name__ == "__main__":
    main()
