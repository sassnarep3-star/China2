#!/usr/bin/env python3
"""Independent structural/arithmetic checks for the tax workbook.

These checks do not prove substantive legal accuracy or live external link
health. Official-source meaning was reviewed separately in research notes.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SITE = ROOT / "site"
OFFICIAL_HOSTS = {
    "www.irs.gov",
    "irs.gov",
    "www.govinfo.gov",
    "govinfo.gov",
    "fiscaldata.treasury.gov",
    "fiscal.treasury.gov",
    "www.fiscal.treasury.gov",
}


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def official(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname in OFFICIAL_HOSTS


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.main_count = 0
        self.in_tbody = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "main":
            self.main_count += 1
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row = []
        if "href" in attrs:
            self.links.append(attrs["href"])
            if self.row is not None:
                self.row.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def main() -> None:
    sources = {s["id"]: s for s in load("sources.json")}
    rules = load("rules.json")
    flags = load("flags.json")
    formulas = load("formulas.json")
    decisions = load("decisions.json")
    inputs = load("inputs.json")
    workbook = load("workbook.json")

    assert sources, "no sources"
    for source in sources.values():
        assert official(source["url"]), source
        assert source["status"] == "read", source
        assert source["verified_text"], source

    for rule in rules:
        assert rule["sources"], rule
        for sid in rule["sources"]:
            assert sid in sources and official(sources[sid]["url"]), rule
        if rule["status"] == "unverified":
            assert rule["value"] == "", rule

    for flag in flags:
        assert flag["sources"], flag
        for sid in flag["sources"]:
            assert sid in sources and official(sources[sid]["url"]), flag

    for formula in formulas:
        assert formula["sources"], formula
        for sid in formula["sources"]:
            assert sid in sources and official(sources[sid]["url"]), formula
        if formula["status"] == "unverified":
            assert formula["result"] == "", formula

    for decision in decisions:
        assert decision["sources"], decision
        for sid in decision["sources"]:
            assert sid in sources and official(sources[sid]["url"]), decision

    with (DATA / "basis-input-template.csv").open(newline="", encoding="utf-8") as handle:
        template_rows = list(csv.reader(handle))
    assert len(template_rows) == 1 and template_rows[0], "basis template must contain headers only"
    assert "acquisition_basis_usd" in template_rows[0]
    assert "source_ids" in template_rows[0]

    rate = Decimal(inputs["reference_rate"]["value"])
    expected_targets = list(
        range(inputs["target_usd_start"], inputs["target_usd_end"] + 1, inputs["target_usd_step"])
    )
    rows = workbook["rows"]
    assert [r["target_usd"] for r in rows] == expected_targets
    assert len(rows) == 40
    for row in rows:
        assert Decimal(row["cny_reference"]) == (Decimal(row["target_usd"]) * rate).quantize(Decimal("0.01"))
        for field in [
            "total_cost_usd",
            "federal_tax_usd",
            "execution_fees_usd",
            "acquisition_basis_usd",
            "realized_gain_usd",
            "taxable_gain_usd",
        ]:
            assert row[field] == "", (row["row_id"], field)
        for sid in row["source_ids"]:
            assert sid in sources and official(sources[sid]["url"]), row

    with (DATA / "workbook.csv").open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == len(rows)
    for csv_row, json_row in zip(csv_rows, rows):
        assert int(csv_row["target_usd"]) == json_row["target_usd"]
        assert csv_row["cny_reference"] == json_row["cny_reference"]
        for field in ["total_cost_usd", "federal_tax_usd", "execution_fees_usd", "acquisition_basis_usd", "realized_gain_usd", "taxable_gain_usd"]:
            assert csv_row[field] == ""
        assert csv_row["source_ids"].split(";") == json_row["source_ids"]

    assert (SITE / "workbook.csv").read_bytes() == (DATA / "workbook.csv").read_bytes()
    assert (SITE / "workbook.json").read_bytes() == (DATA / "workbook.json").read_bytes()
    assert (SITE / "basis-input-template.csv").read_bytes() == (DATA / "basis-input-template.csv").read_bytes()

    pages = {}
    for path in SITE.rglob("*.html"):
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        pages[path.resolve()] = parser

    expected_pages = {
        "index.html", "workbook.html", "rules.html", "sources.html", "review.html", "methodology.html"
    }
    assert {p.name for p in pages} == expected_pages

    for path, parser in pages.items():
        assert parser.main_count == 1, path
        for href in parser.links:
            parts = urlsplit(href)
            if parts.scheme or parts.netloc:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            assert target.is_file(), (path, href)
            if parts.fragment and target.suffix == ".html":
                assert unquote(parts.fragment) in pages[target].ids, (path, href)
        for row in parser.rows:
            assert any(official(href) for href in row), (path, row)

    print(
        f"PASS: {len(pages)} pages, {len(rows)} workbook rows, {len(sources)} official sources, "
        f"{len(rules)} rules, {len(flags)} flags, {len(formulas)} formulas, {len(decisions)} decision paths; "
        "blank unverified values, arithmetic parity, row source links, local links/anchors and blank input template."
    )


if __name__ == "__main__":
    main()
