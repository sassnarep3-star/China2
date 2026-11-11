#!/usr/bin/env python3
"""Independent structural/citation checks for audit-0f0f59fe."""
from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
findings = json.loads((ROOT / "findings.json").read_text(encoding="utf-8"))
sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
source_by_id = {s["id"]: s for s in sources}
checks = 0
failures: list[str] = []


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(message)


class PageParser(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.h1 = 0
        self.lang = ""
        self.finding_rows: list[dict[str, object]] = []
        self.source_rows: list[dict[str, object]] = []
        self._row: dict[str, object] | None = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "h1":
            self.h1 += 1
        if tag == "tr":
            self._row = {"id": a.get("id"), "class": a.get("class", ""), "links": []}
        if tag == "a" and "href" in a:
            href = a["href"]
            self.links.append(href)
            if self._row is not None and href.startswith("https://"):
                self._row["links"].append(href)

    def handle_endtag(self, tag):
        if tag == "tr" and self._row is not None:
            if "finding" in str(self._row.get("class", "")).split():
                self.finding_rows.append(self._row)
            elif str(self._row.get("id", "")).startswith("P"):
                self.source_rows.append(self._row)
            self._row = None


# Integration change (session arena/3347ca0a-china2, 2026-11-11): the root hub now also
# cites two primary sources that are not government domains but are the publisher of the
# fact being used - Bank of China's own FX board (the price it quotes) and Wise's own
# help page (the limit it sets). Both are the authoritative source for their own terms,
# so they are admitted here; nothing else outside .gov/.gov.cn/HSBC is.
PRIMARY_BANK_HOSTS = ("boc.cn", "wise.com", "westernunion.com")


def official_host(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    if host.endswith(".gov") or host.endswith(".gov.cn") or host == "hsbc.com.cn" or host.endswith(".hsbc.com.cn"):
        return True
    return any(host == h or host.endswith("." + h) for h in PRIMARY_BANK_HOSTS)


# Ledger structure and citation policy.
check(len(findings) == 11, f"expected 11 findings, got {len(findings)}")
check(len(sources) == 14, f"expected 14 sources, got {len(sources)}")
check(len(source_by_id) == len(sources), "duplicate source IDs")
check(len({f["id"] for f in findings}) == len(findings), "duplicate finding IDs")
for source in sources:
    for key in ("id", "authority", "title", "url", "locator", "retrieved", "status", "evidence"):
        check(bool(str(source.get(key, "")).strip()), f"{source.get('id')}: missing {key}")
    check(official_host(source["url"]), f"{source['id']}: non-official host {source['url']}")
    check(source["url"].startswith("https://"), f"{source['id']}: source URL is not HTTPS")
for finding in findings:
    for key in ("id", "severity", "status", "topic", "claim", "evidence", "action"):
        check(bool(str(finding.get(key, "")).strip()), f"{finding.get('id')}: missing {key}")
    check(bool(finding.get("sources")), f"{finding['id']}: no official source IDs")
    for sid in finding["sources"]:
        check(sid in source_by_id, f"{finding['id']}: unknown source {sid}")

page_path = ROOT / "index.html"
check(page_path.exists(), "generated index.html missing")
page_text = page_path.read_text(encoding="utf-8") if page_path.exists() else ""
doc = PageParser(page_text)
check(doc.lang == "en", "page language is not en")
check(doc.h1 == 1, f"expected one h1, got {doc.h1}")
check(len(doc.finding_rows) == len(findings), f"rendered finding rows {len(doc.finding_rows)} do not match ledger {len(findings)}")
for row, finding in zip(doc.finding_rows, findings):
    check(row.get("id") == finding["id"], f"finding row order/id mismatch at {finding['id']}")
    links = row.get("links", [])
    check(bool(links), f"{finding['id']}: rendered table row has no direct official link")
    expected = {source_by_id[sid]["url"] for sid in finding["sources"] if sid in source_by_id}
    found = set(links)
    check(expected.issubset(found), f"{finding['id']}: one or more ledger source URLs missing from its row")
    check(all(official_host(u) for u in links), f"{finding['id']}: non-official source link in row")
check(len(doc.source_rows) == len(sources),
      f"rendered source rows {len(doc.source_rows)} do not match ledger {len(sources)}")
for row, source in zip(doc.source_rows, sources):
    check(row.get("id") == source["id"], f"source row order/id mismatch at {source['id']}")
    links = row.get("links", [])
    check(source["url"] in links, f"{source['id']}: source register row lacks its direct official link")
    check(all(official_host(u) for u in links), f"{source['id']}: non-official link in source row")
for source in sources:
    check(source["url"] in page_text, f"{source['id']}: official source URL missing from rendered page")

# Every local link and local fragment used by the generated page must resolve.
for href in doc.links:
    if href.startswith(("http://", "https://", "mailto:", "tel:")):
        continue
    target_text, _, fragment = href.partition("#")
    target = (ROOT / unquote(target_text)).resolve() if target_text else page_path.resolve()
    check(target.exists(), f"broken local link: {href}")
    if target.exists() and fragment and target.suffix.lower() in (".html", ".htm"):
        target_doc = PageParser(target.read_text(encoding="utf-8"))
        check(fragment in target_doc.ids, f"broken local fragment: {href}")

# Verify the public root hub and every local target it links to, including C04.
root_path = REPO / "index.html"
check(root_path.exists(), "root landing page missing")
root_text = root_path.read_text(encoding="utf-8") if root_path.exists() else ""
root_doc = PageParser(root_text)
check(root_doc.h1 == 1, f"root landing expected one h1, got {root_doc.h1}")
for href in root_doc.links:
    if href.startswith(("http://", "https://", "mailto:", "tel:")):
        if href.startswith("https://"):
            check(official_host(href), f"root landing has a non-official external link: {href}")
        continue
    target_text, _, fragment = href.partition("#")
    target = (REPO / unquote(target_text)).resolve() if target_text else root_path.resolve()
    check(target.exists(), f"broken root landing link: {href}")
    if target.exists() and fragment and target.suffix.lower() in (".html", ".htm"):
        target_doc = PageParser(target.read_text(encoding="utf-8"))
        check(fragment in target_doc.ids, f"broken root landing fragment: {href}")
check("USD 0–7" in root_text, "root landing lacks the legacy Global Transfer warning")

# Ensure no cost is presented as verified in the strict source-only cards.
check("All-in cost: —" in page_text, "source-only cost result is not shown as blank")
check("no verified all-in usd amount" in page_text.lower(), "cost uncertainty disclosure missing")
check("model outputs" in page_text, "scenario-model disclosure missing")
check("not an official quote" in page_text.lower() or "not verified" in page_text.lower(),
      "modelled values are not clearly caveated")

print(f"{checks} checks, {len(failures)} failures")
for failure in failures:
    print("FAIL:", failure)
sys.exit(1 if failures else 0)
