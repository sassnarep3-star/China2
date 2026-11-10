#!/usr/bin/env python3
"""Independent line-by-line verifier for study-8f529c94 (does NOT import build.py).

Verifies:
  1. Source ledger integrity: 40 unique sources, 100% HTTPS on official/primary
     allowlist, non-empty locators and verbatim excerpts.
  2. Method, penalty, tax, repo-audit, and flag ledgers: valid source_ids/flag_ids,
     complete pros/cons/steps.
  3. Independent arithmetic re-derivation of all 920 cost rows (40 tiers $10k->$400k
     in $10k steps x 23 methods) in both JSON and CSV exports, plus strict blank
     enforcement on fx_spread_usd, intermediary_receiving_fee_usd, and
     all_in_total_cost_usd across all 920 rows.
  4. HTML structural & row-level citation verification across all 8 pages:
     - <html lang="en">, viewport meta, skip-link, single <h1>, unique element IDs,
       zero localhost/127.0.0.1 strings.
     - EVERY <tr> containing a <td> MUST contain at least one direct HTTPS link
       to an official/primary domain on the allowlist.
     - Every local href/src resolves to an existing file and #fragment ID.
"""
import csv
import json
import math
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = HERE / "data"
EXPORTS = HERE / "exports"

ALLOWED_HOSTS = (
    "safe.gov.cn",
    "pbc.gov.cn",
    "chinatax.gov.cn",
    "gov.cn",
    "irs.gov",
    "govinfo.gov",
    "ecfr.gov",
    "cbp.gov",
    "hsbc.com.cn",
    "wise.com",
    "westernunion.com",
)

EXPECTED_PAGES = (
    "index.html",
    "costs.html",
    "methods.html",
    "penalties.html",
    "taxes.html",
    "audit.html",
    "flagged.html",
    "sources.html",
)

checks = 0
failures = []


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        failures.append(msg)
        print(f"FAIL: {msg}")


def is_allowed_https(url: str) -> bool:
    try:
        u = urlsplit(url)
        host = (u.hostname or "").lower().rstrip(".")
        return u.scheme == "https" and any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS)
    except ValueError:
        return False


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang_en = False
        self.viewport = False
        self.skip_link = False
        self.h1_count = 0
        self.ids: list[str] = []
        self.links: list[str] = []
        self.assets: list[str] = []
        self.cur_tr = None
        self.data_rows: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "html" and a.get("lang", "").lower().startswith("en"):
            self.lang_en = True
        if tag == "meta" and a.get("name", "").lower() == "viewport" and "width=device-width" in a.get("content", ""):
            self.viewport = True
        if tag == "h1":
            self.h1_count += 1
        if "id" in a and a["id"]:
            self.ids.append(a["id"])
        if tag == "a" and a.get("href"):
            href = a["href"]
            self.links.append(href)
            if "skip-link" in a.get("class", "") and href.startswith("#"):
                self.skip_link = True
        if tag in ("link", "script", "img"):
            target = a.get("href") or a.get("src")
            if target:
                self.assets.append(target)
        if tag == "tr":
            self.cur_tr = {"has_td": False, "hrefs": [], "text": []}
        elif self.cur_tr is not None:
            if tag == "td":
                self.cur_tr["has_td"] = True
            if tag == "a" and a.get("href"):
                self.cur_tr["hrefs"].append(a["href"])

    def handle_data(self, data: str) -> None:
        if self.cur_tr is not None:
            self.cur_tr["text"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.cur_tr is not None:
            if self.cur_tr["has_td"]:
                self.data_rows.append(self.cur_tr)
            self.cur_tr = None


def expected_hsbc_personal_tt_usd(cny: float, rate: float) -> float:
    return round((min(max(cny * 0.001, 100.0), 500.0) + 120.0) / rate, 2)


def expected_hsbc_entity_tt_usd(cny: float, rate: float) -> float:
    return round((min(max(cny * 0.001, 100.0), 1000.0) + 140.0) / rate, 2)


def main() -> None:
    # 1. Sources ledger
    src_doc = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    rate = float(src_doc["meta"]["reference_fx_rate"]["cny_per_usd"])
    check(rate == 7.129, f"reference FX rate == 7.129 (got {rate})")
    sources = src_doc["sources"]
    check(len(sources) == 40, f"40 primary sources present (got {len(sources)})")
    src_ids = [s["id"] for s in sources]
    check(src_ids == [f"SRC-{i:02d}" for i in range(1, 41)], "source IDs sequential SRC-01..SRC-40")
    src_map = {s["id"]: s for s in sources}

    for s in sources:
        sid = s["id"]
        check(is_allowed_https(s["url"]), f"{sid}: HTTPS official/primary allowlist URL ({s['url']})")
        check(s["status"] in ("verified", "verified-limited"), f"{sid}: valid status")
        check(len(s["locator"].strip()) >= 3, f"{sid}: non-empty locator")
        check(len(s["verbatim_excerpt"].strip()) >= 30, f"{sid}: non-empty verbatim excerpt")

    # 2. Methods, penalties/taxes, audit/flags ledgers
    m_doc = json.loads((DATA / "methods.json").read_text(encoding="utf-8"))
    methods = m_doc["methods"]
    check(len(methods) == 23, f"23 methods present (got {len(methods)})")
    m_ids = [m["id"] for m in methods]
    check(m_ids == [f"M{i:02d}" for i in range(1, 24)], "method IDs sequential M01..M23")

    af_doc = json.loads((DATA / "audit_and_flags.json").read_text(encoding="utf-8"))
    audit_rows = af_doc["repo_audit"]
    flags = af_doc["flags"]
    check(len(audit_rows) == 14, f"14 repo audit findings (got {len(audit_rows)})")
    check(len(flags) == 18, f"18 flags (got {len(flags)})")
    flag_ids = {f["id"] for f in flags}

    for m in methods:
        mid = m["id"]
        check(len(m["pros"]) >= 1 and len(m["cons"]) >= 1 and len(m["steps"]) >= 1, f"{mid}: pros/cons/steps populated")
        check(len(m["source_ids"]) >= 1 and all(sid in src_map for sid in m["source_ids"]), f"{mid}: valid source_ids")
        check(len(m["flag_ids"]) >= 1 and all(fid in flag_ids for fid in m["flag_ids"]), f"{mid}: valid flag_ids")

    pt_doc = json.loads((DATA / "penalties_and_taxes.json").read_text(encoding="utf-8"))
    check(len(pt_doc["penalty_layers"]) == 7, "7 conversion penalty layers")
    check(len(pt_doc["tax_compliance_rows"]) == 12, "12 tax/reporting rows")
    for row in pt_doc["penalty_layers"] + pt_doc["tax_compliance_rows"] + audit_rows + flags:
        check(len(row["source_ids"]) >= 1 and all(sid in src_map for sid in row["source_ids"]), "ledger row has valid source_ids")

    # 3. Independent re-derivation of all 920 cost-ladder rows (JSON + CSV parity)
    ladder_json = json.loads((EXPORTS / "cost-ladder-920.json").read_text(encoding="utf-8"))
    j_rows = ladder_json["rows"]
    with (EXPORTS / "cost-ladder-920.csv").open("r", encoding="utf-8", newline="") as fh:
        c_rows = list(csv.DictReader(fh))

    check(len(j_rows) == 920, f"JSON export has 920 rows (got {len(j_rows)})")
    check(len(c_rows) == 920, f"CSV export has 920 rows (got {len(c_rows)})")

    expected_tiers = [step * 10000 for step in range(1, 41)]
    seen_tiers = sorted(set(r["usd_amount"] for r in j_rows))
    check(seen_tiers == expected_tiers, "tiers cover $10,000..$400,000 in $10,000 steps")

    m_by_id = {m["id"]: m for m in methods}
    for idx, (jr, cr) in enumerate(zip(j_rows, c_rows)):
        usd = jr["usd_amount"]
        mid = jr["method_id"]
        m = m_by_id[mid]
        exp_cny = round(usd * rate, 2)
        check(jr["cny_reference_amount"] == exp_cny, f"row {idx} ({mid} ${usd}): CNY amount")
        check(int(cr["usd_amount"]) == usd and cr["method_id"] == mid, f"row {idx}: CSV/JSON key parity")

        # Strict blank enforcement on unconfirmed commercial/all-in columns
        check(
            jr["fx_spread_usd"] is None
            and jr["intermediary_receiving_fee_usd"] is None
            and jr["all_in_total_cost_usd"] is None,
            f"row {idx} ({mid} ${usd}): JSON unverified columns strictly null",
        )
        check(
            cr["fx_spread_usd"] == ""
            and cr["intermediary_receiving_fee_usd"] == ""
            and cr["all_in_total_cost_usd"] == "",
            f"row {idx} ({mid} ${usd}): CSV unverified columns strictly blank",
        )
        check(
            any(is_allowed_https(u.strip()) for u in cr["source_urls"].split("|")),
            f"row {idx} ({mid} ${usd}): CSV row carries official HTTPS URL",
        )

        # Independent fee & batch verification
        fmode = m["fee_mode"]
        if fmode == "hsbc_personal_tt":
            exp_std = expected_hsbc_personal_tt_usd(exp_cny, rate)
            check(jr["published_fee_standard_usd"] == exp_std and jr["published_fee_pb_usd"] == 0.0, f"{mid} ${usd}: HSBC personal TT fee")
        elif fmode == "hsbc_global_transfer":
            check(jr["published_fee_standard_usd"] == 0.0 and jr["published_fee_alt_usd"] == 20.0, f"{mid} ${usd}: HSBC Global Transfer fee")
        elif fmode == "hsbc_quota_annual_tt":
            n_full = usd // 50000
            rem = usd % 50000
            cny_fee = n_full * (min(max(50000.0 * rate * 0.001, 100.0), 500.0) + 120.0)
            if rem > 0:
                cny_fee += min(max(rem * rate * 0.001, 100.0), 500.0) + 120.0
            check(jr["published_fee_standard_usd"] == round(cny_fee / rate, 2), f"{mid} ${usd}: quota multi-year TT fee")
            check(jr["min_calendar_years"] == math.ceil(usd / 50000.0), f"{mid} ${usd}: quota years")
        elif fmode == "hsbc_entity_dividend_wht10":
            exp_ent = expected_hsbc_entity_tt_usd(exp_cny, rate)
            check(jr["published_fee_standard_usd"] == exp_ent, f"{mid} ${usd}: HSBC entity TT fee")
            check(jr["treaty_dividend_wht_10pct_usd"] == round(usd * 0.10, 2), f"{mid} ${usd}: 10% treaty WHT")
        elif fmode == "unverified_live_quote":
            check(jr["published_fee_standard_usd"] is None and cr["published_fee_standard_usd"] == "", f"{mid} ${usd}: unconfirmed fee left blank")
        elif fmode == "prc_fine_30_to_100_pct":
            check(
                jr["published_fee_standard_usd"] is None
                and jr["prc_statutory_fine_30pct_usd"] == round(usd * 0.30, 2)
                and jr["prc_statutory_fine_100pct_usd"] == round(usd * 1.00, 2),
                f"{mid} ${usd}: PRC 30%-100% statutory fine math",
            )

        if mid == "M15" and usd == 400000:
            check(jr["min_calendar_years"] == 29 and jr["min_batches"] == 286, "M15 $400k ATM cap == 29 years / 286 withdrawals")

    # Spot-check headline M01 figures
    by_key = {(r["method_id"], r["usd_amount"]): r for r in j_rows}
    check(by_key[("M01", 10000)]["published_fee_standard_usd"] == 30.86, "M01 $10k == $30.86")
    check(by_key[("M01", 50000)]["published_fee_standard_usd"] == 66.83, "M01 $50k == $66.83")
    check(by_key[("M01", 400000)]["published_fee_standard_usd"] == 86.97, "M01 $400k == $86.97")
    check(by_key[("M06", 400000)]["published_fee_standard_usd"] == 534.66, "M06 $400k == $534.66")

    # 4. HTML pages structural + row-level official-link + local link/anchor verification
    check((HERE / "EXECUTIVE_SUMMARY.md").is_file(), "EXECUTIVE_SUMMARY.md exists")
    parsed_pages: dict[Path, PageInspector] = {}
    for pname in EXPECTED_PAGES:
        p = HERE / pname
        check(p.is_file(), f"{pname}: exists")
        raw = p.read_text(encoding="utf-8")
        check("localhost" not in raw.lower() and "127.0.0.1" not in raw, f"{pname}: no localhost/127.0.0.1")
        ins = PageInspector()
        ins.feed(raw)
        parsed_pages[p.resolve()] = ins
        check(ins.lang_en, f"{pname}: <html lang='en'>")
        check(ins.viewport, f"{pname}: viewport meta present")
        check(ins.skip_link, f"{pname}: skip-link present")
        check(ins.h1_count == 1, f"{pname}: single <h1> (got {ins.h1_count})")
        check(len(ins.ids) == len(set(ins.ids)), f"{pname}: unique element IDs ({len(ins.ids)})")
        check(len(ins.data_rows) >= 1, f"{pname}: contains data table rows ({len(ins.data_rows)})")
        for r_idx, tr in enumerate(ins.data_rows, 1):
            has_official = any(is_allowed_https(h) for h in tr["hrefs"])
            snippet = " ".join("".join(tr["text"]).split())[:80]
            check(has_official, f"{pname} row {r_idx}: has direct HTTPS official source link ({snippet})")

    # Resolve all local href/src targets and #fragments
    id_cache: dict[Path, set[str]] = {p: set(ins.ids) for p, ins in parsed_pages.items()}
    for p, ins in parsed_pages.items():
        for ref in ins.links + ins.assets:
            if ref.startswith(("https://", "http://", "mailto:", "tel:")):
                check(ref.startswith("https://"), f"{p.name}: external link uses HTTPS ({ref})")
                continue
            u = urlsplit(ref)
            target_file = (p.parent / unquote(u.path)).resolve() if u.path else p
            check(target_file.is_file(), f"{p.name}: local target exists ({ref})")
            if u.fragment and target_file.suffix == ".html":
                if target_file not in id_cache and target_file.is_file():
                    tmp = PageInspector()
                    tmp.feed(target_file.read_text(encoding="utf-8", errors="replace"))
                    id_cache[target_file] = set(tmp.ids)
                check(u.fragment in id_cache.get(target_file, set()), f"{p.name}: fragment #{u.fragment} resolves in {target_file.name}")

    if failures:
        print(f"\nFAILED: {len(failures)} of {checks} checks failed.")
        sys.exit(1)
    print(f"PASS: {checks:,} independent checks, 0 failures across 8 pages, 920 cost rows, 23 methods, and 40 HTTPS official sources.")


if __name__ == "__main__":
    main()
