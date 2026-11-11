#!/usr/bin/env python3
"""Deterministic static site & cost-ladder generator for transfer-guide.

Reads canonical JSON ledgers in transfer-guide/data/ and writes:
  - 8 responsive, mobile-first HTML dashboard pages
  - transfer-guide/EXECUTIVE_SUMMARY.md
  - transfer-guide/exports/cost-ladder-920.csv
  - transfer-guide/exports/cost-ladder-920.json

Policy:
  - Every table body row (<tr> with <td>) carries direct HTTPS links to official
    primary sources verified in this session plus local source-ledger anchors.
  - Only fee/tax/penalty components confirmed in official/primary sources are
    computed; unconfirmed FX spreads, third-party wire deductions, and private
    tax figures remain strictly blank ("" in CSV / null in JSON / "—" in HTML)
    and are linked to Flagged for Review.
"""
import csv
import html
import json
import math
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
EXPORTS = HERE / "exports"

SOURCES_DOC = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
METHODS_DOC = json.loads((DATA / "methods.json").read_text(encoding="utf-8"))
TAX_DOC = json.loads((DATA / "penalties_and_taxes.json").read_text(encoding="utf-8"))
AUDIT_DOC = json.loads((DATA / "audit_and_flags.json").read_text(encoding="utf-8"))
QUESTIONS_DOC = json.loads((DATA / "questions.json").read_text(encoding="utf-8"))

RATE = float(SOURCES_DOC["meta"]["reference_fx_rate"]["cny_per_usd"])  # 7.129
RETRIEVED = SOURCES_DOC["meta"]["retrieved_date"]

SOURCES = {s["id"]: s for s in SOURCES_DOC["sources"]}
METHODS = METHODS_DOC["methods"]
CATEGORIES = {c["code"]: c for c in METHODS_DOC["meta"]["categories"]}
PENALTY_LAYERS = TAX_DOC["penalty_layers"]
TAX_ROWS = TAX_DOC["tax_compliance_rows"]
REPO_AUDIT = AUDIT_DOC["repo_audit"]
FLAGS = AUDIT_DOC["flags"]
QUESTIONS = QUESTIONS_DOC["questions"]

TIERS = [step * 10000 for step in range(1, 41)]  # $10,000 .. $400,000

NAV_PAGES = [
    ("index.html", "Overview"),
    ("questions.html", "Decision Checklist"),
    ("costs.html", "Costs ($10k–$400k)"),
    ("methods.html", "23 Methods & Steps"),
    ("penalties.html", "Conversion Penalty"),
    ("taxes.html", "US & PRC Tax"),
    ("audit.html", "Repo Audit"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Official Sources"),
]


def esc(val) -> str:
    return html.escape(str(val), quote=True)


def host_label(url: str) -> str:
    h = (urlsplit(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def render_sources(src_ids: list[str], max_direct: int = 3) -> str:
    parts = []
    for i, sid in enumerate(src_ids):
        s = SOURCES[sid]
        if i < max_direct:
            parts.append(
                f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(sid)} ({esc(host_label(s["url"]))})</a>'
            )
        else:
            parts.append(f'<a href="sources.html#{esc(sid)}">{esc(sid)}</a>')
    return '<span class="src-links">' + " · ".join(parts) + "</span>"


def render_flags(flag_ids: list[str]) -> str:
    if not flag_ids:
        return "—"
    return " · ".join(f'<a href="flagged.html#{esc(fid)}">{esc(fid)}</a>' for fid in flag_ids)


def status_badge(st: str) -> str:
    mapping = {
        "lawful-documented": ("ok", "Lawful · Documented"),
        "lawful-conditional": ("cond", "Lawful · Conditional"),
        "closed-loop-non-exit": ("warn", "Closed-Loop · Non-Exit"),
        "rejected-unlawful": ("bad", "Rejected · Unlawful"),
        "verified": ("ok", "Verified"),
        "verified-limited": ("warn", "Verified · Limited"),
        "high": ("bad", "High"),
        "medium": ("warn", "Medium"),
        "low": ("cond", "Low"),
    }
    cls, label = mapping.get(st, ("cond", st))
    return f'<span class="badge {cls}">{esc(label)}</span>'


def hsbc_personal_tt_cny(cny_amt: float) -> float:
    return min(max(cny_amt * 0.001, 100.0), 500.0) + 120.0


def hsbc_entity_tt_cny(cny_amt: float) -> float:
    return min(max(cny_amt * 0.001, 100.0), 1000.0) + 140.0


def compute_cost_row(m: dict, usd: int) -> dict:
    cny = round(usd * RATE, 2)
    bmode = m["batch_mode"]
    fmode = m["fee_mode"]

    batches = None
    min_years = None
    if bmode == "single_wire_uncapped":
        batches = 1
        min_years = 1
        sched = "1 wire (uncapped with valid docs)"
    elif bmode == "wise_bank_300k":
        batches = math.ceil(cny / 300000.0)
        min_years = 1
        sched = f"{batches} bank-app transfer(s) (<=CNY 300k; <=3-yr tax records)"
    elif bmode == "wise_alipay_50k":
        batches = math.ceil(cny / 50000.0)
        min_years = 1
        sched = f"{batches} Alipay transfer(s) (<=CNY 50k; <=3-yr tax records)"
    elif bmode == "annual_50k_quota":
        batches = math.ceil(usd / 50000.0)
        min_years = batches
        sched = f"{batches} annual wire(s) over {min_years} yr(s) (PR-ID / PRC ID only)"
    elif bmode == "small_reconv_500_day":
        days = math.ceil(usd / 500.0)
        ports = math.ceil(usd / 1000.0)
        batches = days
        sched = f"{days} branch days (<=$500/d) or {ports} port departures (<=$1k) — unspent FX only"
    elif bmode == "atm_100k_cny_yr":
        atm_days = math.ceil(cny / 10000.0)
        min_years = math.ceil(cny / 100000.0)
        batches = atm_days
        sched = f"{atm_days} ATM withdrawals over {min_years} yr(s) (RMB 100k/yr hard cap)"
    elif bmode == "consumption_non_deposit":
        sched = "POS merchant spend only ($0 USD bank deposit)"
    elif bmode == "usd_cash_5k_trip":
        t5 = math.ceil(usd / 5000.0)
        t10 = math.ceil(usd / 10000.0)
        batches = t5
        sched = f"{t5} trips (<=$5k permit-free) or {t10} trips (<=$10k bank permit)"
    elif bmode == "rmb_cash_20k_trip":
        tr = math.ceil(cny / 20000.0)
        batches = tr
        sched = f"{tr} cross-border trips (<=RMB 20,000/trip)"
    elif bmode == "unverified_batches":
        sched = "— (WU bank payout unavailable; partner limits unconfirmed)"
    elif bmode == "closed_loop_no_exit":
        sched = "Closed-loop pipe only ($0 open USD exit)"
    elif bmode == "unlawful_prohibited":
        batches = 0
        sched = "PROHIBITED ($0 lawful limit)"
    else:
        raise ValueError(f"Unknown batch_mode: {bmode}")

    pub_pb_usd = None
    pub_std_usd = None
    pub_alt_usd = None
    pub_alt_label = ""
    treaty_wht_usd = None
    fine_ord_max_usd = None
    fine_ser_max_usd = None
    fee_note = ""

    if fmode == "hsbc_personal_tt":
        fee_cny = hsbc_personal_tt_cny(cny)
        pub_pb_usd = 0.00
        pub_std_usd = round(fee_cny / RATE, 2)
        pub_alt_usd = round((fee_cny + 200.0) / RATE, 2)
        pub_alt_label = f"Pay Exact OUR: ${pub_alt_usd:,.2f} (+CNY 200); PB/Premier Elite: $0.00"
        fee_note = f"HSBC Premier/Advance SHA (CNY {fee_cny:,.2f} @ {RATE})"
    elif fmode == "hsbc_global_transfer":
        pub_pb_usd = 0.00
        pub_std_usd = 0.00
        pub_alt_usd = 20.00
        pub_alt_label = "Advance segment: $20.00 actual/tx (CNY 145 indicative)"
        fee_note = "HSBC Global Transfer to Self: $0.00 (PB/Premier)"
    elif fmode == "hsbc_quota_annual_tt":
        n_full = usd // 50000
        rem = usd % 50000
        total_cny_fee = n_full * hsbc_personal_tt_cny(50000.0 * RATE)
        if rem > 0:
            total_cny_fee += hsbc_personal_tt_cny(rem * RATE)
        n_wires = n_full + (1 if rem > 0 else 0)
        pub_pb_usd = 0.00
        pub_std_usd = round(total_cny_fee / RATE, 2)
        pub_alt_usd = round((total_cny_fee + 200.0 * n_wires) / RATE, 2)
        pub_alt_label = f"Pay Exact OUR ({n_wires}x): ${pub_alt_usd:,.2f}; PB/Premier Elite: $0.00"
        fee_note = f"{n_wires} annual HSBC Premier/Advance wire(s)"
    elif fmode == "hsbc_cash_zero_fee":
        pub_pb_usd = 0.00
        pub_std_usd = 0.00
        pub_alt_label = "Excludes banknote FX spread & airfare (unverified)"
        fee_note = "HSBC counter banknote fee $0.00 (NOT zero all-in cost)"
    elif fmode == "hsbc_entity_dividend_wht10":
        ent_cny = hsbc_entity_tt_cny(cny)
        pub_std_usd = round(ent_cny / RATE, 2)
        treaty_wht_usd = round(usd * 0.10, 2)
        pub_alt_usd = round((ent_cny + 200.0) / RATE, 2)
        pub_alt_label = f"10% Treaty Art. 9(2) WHT: ${treaty_wht_usd:,.2f} (Form 1116 creditable)"
        fee_note = f"HSBC Entity TT (CNY {ent_cny:,.2f} @ {RATE}) + 10% Treaty WHT"
    elif fmode == "hsbc_gba_closed_loop":
        pub_std_usd = 0.00
        pub_alt_label = "Closed-loop only — cannot exit to U.S. USD bank account"
        fee_note = "HSBC GBA WMC fee $0.00 (Premier/Advance), non-exit"
    elif fmode == "unverified_live_quote":
        fee_note = "Blank — fee/spread not published in official static schedule"
    elif fmode == "prc_fine_30_to_100_pct":
        fine_ord_max_usd = round(usd * 0.30, 2)
        fine_ser_max_usd = round(usd * 1.00, 2)
        pub_alt_label = f"PRC fine exposure: <=${fine_ord_max_usd:,.0f} (30%) / ${fine_ord_max_usd:,.0f}–${fine_ser_max_usd:,.0f} (30%–100%)"
        fee_note = "Unlawful route — statutory penalty exposure, not a fee"
    else:
        raise ValueError(f"Unknown fee_mode: {fmode}")

    return {
        "usd_amount": usd,
        "cny_reference_amount": cny,
        "reference_fx_rate": RATE,
        "method_id": m["id"],
        "method_name": m["name"],
        "category": m["category"],
        "legal_status": m["legal_status"],
        "min_batches": batches,
        "min_calendar_years": min_years,
        "schedule_summary": sched,
        "published_fee_pb_usd": pub_pb_usd,
        "published_fee_standard_usd": pub_std_usd,
        "published_fee_alt_usd": pub_alt_usd,
        "published_fee_detail": fee_note,
        "secondary_published_detail": pub_alt_label,
        "treaty_dividend_wht_10pct_usd": treaty_wht_usd,
        "fx_spread_usd": None,
        "intermediary_receiving_fee_usd": None,
        "all_in_total_cost_usd": None,
        "prc_statutory_fine_30pct_usd": fine_ord_max_usd,
        "prc_statutory_fine_100pct_usd": fine_ser_max_usd,
        "source_ids": m["source_ids"],
        "flag_ids": m["flag_ids"],
    }


def shell(filename: str, title: str, description: str, body: str) -> str:
    nav_links = []
    for href, label in NAV_PAGES:
        cur = ' aria-current="page"' if href == filename else ""
        nav_links.append(f'<a href="{esc(href)}"{cur}>{esc(label)}</a>')
    nav_html = "\n        ".join(nav_links)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · China Money Transfer Guide (50f278d8)</title>
  <meta name="description" content="{esc(description)}">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <header class="site-header">
    <div class="header-inner">
      <div class="brand-row">
        <a class="brand" href="index.html">China Money · US Citizen CNY→USD Repatriation Study</a>
        <span class="brand-meta">40 official/primary HTTPS sources verified {esc(RETRIEVED)} · <a href="../index.html" style="color:#9be3cd">Repository Hub</a></span>
      </div>
      <nav class="nav-bar" aria-label="Study sections">
        {nav_html}
      </nav>
    </div>
  </header>
  <main id="main-content">
{body}
  </main>
  <footer class="site-footer">
    <div class="footer-inner">
      <p><strong>Regulatory research only — not personalized legal, tax, or investment advice.</strong> Every table row links directly to an official government or primary published bank/provider source verified on {esc(RETRIEVED)}. Unconfirmed FX spreads, intermediary fees, and account-specific tax liabilities are left strictly blank and published on <a href="flagged.html">Flagged for Review</a>.</p>
      <p><a href="index.html">Overview</a> · <a href="costs.html">$10k–$400k Cost Tables</a> · <a href="methods.html">23 Methods</a> · <a href="penalties.html">Conversion Penalty</a> · <a href="taxes.html">US &amp; PRC Tax</a> · <a href="audit.html">Repo Audit</a> · <a href="flagged.html">Flagged for Review</a> · <a href="sources.html">40 Official Sources</a> · <a href="../index.html">Main Repo Hub</a></p>
    </div>
  </footer>
  <script src="assets/app.js" defer></script>
</body>
</html>
"""


def fmt_usd_or_blank(val, suffix: str = "") -> str:
    if val is None:
        return '<span class="blank-cell">— (unverified)</span>'
    return f"${val:,.2f}{esc(suffix)}"


def build_index(ladder_rows: list[dict]) -> str:
    by_key = {(r["method_id"], r["usd_amount"]): r for r in ladder_rows}
    m01_10k = by_key[("M01", 10000)]["published_fee_standard_usd"]
    m01_50k = by_key[("M01", 50000)]["published_fee_standard_usd"]
    m01_400k = by_key[("M01", 400000)]["published_fee_standard_usd"]

    decision_rows = [
        (
            "1. Taxed PRC Salary / Wages / Consulting / Rent",
            "M01 Bank Counter Conversion + SWIFT Wire (or M02 HSBC Global Transfer / M05 Proxy if already in U.S.)",
            "0% conversion tax; 0% extra PRC tax (present STA 个人所得税纳税记录)",
            f"${m01_10k:,.2f} ($10k) → ${m01_400k:,.2f} cap ($400k) Premier/Advance; $0.00 PB/Premier Elite; FX spread — (blank)",
            "Uncapped 1 wire (even 10-yr-old salary qualifies at bank; Wise M03 capped at <=3-yr tax records)",
            ["SRC-03", "SRC-05", "SRC-08", "SRC-09", "SRC-38"],
        ),
        (
            "2. Unspent RMB Originally Converted from USD (<=24 Months)",
            "M07 Reconversion with Original FX Settlement Slip (原兑换水单)",
            "0% PRC tax (return of principal, not income)",
            f"${m01_10k:,.2f} → ${m01_400k:,.2f} wire fee (or $0.00 counter banknote fee); FX spread — (blank)",
            "Up to original FX settlement slip amount within 24 months",
            ["SRC-03", "SRC-06", "SRC-38"],
        ),
        (
            "3. Proceeds from Selling Self-Use PRC Apartment",
            "M09 Direct Bank Property-Sale Proceeds Conversion + Wire",
            "Clear statutory property transfer taxes (20% net-gain IIT unless exempt) + free STA Recordal if >$50k",
            f"${m01_10k:,.2f} → ${m01_400k:,.2f} wire fee; PRC tax creditable via U.S. Form 1116; FX spread — (blank)",
            "100% of net after-tax sale proceeds (original purchase FX slip NOT required per SAFE Q14)",
            ["SRC-02", "SRC-15", "SRC-17", "SRC-18", "SRC-28", "SRC-38"],
        ),
        (
            "4. Inherited Mainland PRC Estate",
            "M10 Foreign Citizen Inheritance SAFE One-Off Transfer",
            "0% PRC inheritance tax; 0% U.S. income tax on bequest (MUST file IRS Form 3520 if >$100,000!)",
            f"${m01_10k:,.2f} → ${m01_400k:,.2f} wire fee after free SAFE approval; FX spread — (blank)",
            "100% lump sum upon SAFE approval (2014 circular cancelled staging)",
            ["SRC-13", "SRC-14", "SRC-26", "SRC-33", "SRC-38"],
        ),
        (
            "5. Former Mainland Resident Who Cancelled Hukou & Emigrated",
            "M11 Emigrant Personal Asset One-Off Transfer",
            "0% conversion tax (requires historical tax proof on pre-emigration wealth)",
            f"${m01_10k:,.2f} → ${m01_400k:,.2f} wire fee after free SAFE approval; FX spread — (blank)",
            "100% lump sum of pre-emigration Mainland assets",
            ["SRC-13", "SRC-14", "SRC-38"],
        ),
        (
            "6. Retained Profits Inside Your Own PRC Company / WFOE",
            "M12 Audited Dividend Distribution Claiming 10% U.S.–China Treaty Cap",
            "10% gross dividend WHT under Treaty Art. 9(2) (vs. 20% domestic) after corporate EIT + free >$50k STA Recordal",
            "HSBC Entity TT $33.67 ($10k) → $159.91 cap ($400k) + 10% PRC WHT (Form 1116 creditable); FX spread — (blank)",
            "Uncapped single corporate wire after CPA audit",
            ["SRC-17", "SRC-18", "SRC-20", "SRC-23", "SRC-28", "SRC-38"],
        ),
        (
            "7. PRC Foreign Permanent Resident ID ('Chinese Green Card') Holder",
            "M06 Annual USD 50,000 Facilitated FX Purchase Quota",
            "0% conversion tax; ID-only up to USD 50,000/calendar year",
            f"${m01_50k:,.2f}/yr ($534.66 across 8 annual wires for $400k); $0.00 PB/Premier Elite; FX spread — (blank)",
            "USD 50,000/yr hard ceiling (8 calendar years for $400k; NOT open to standard U.S. passport!)",
            ["SRC-03", "SRC-07", "SRC-38"],
        ),
        (
            "8. Undocumented / Untaxed PRC Income Sitting in Account",
            "Voluntary PRC Tax Clearance + Treaty Relief → M01 Wire + U.S. Form 1116 FTC",
            "Settle statutory PRC IIT (claim 10% treaty caps where eligible) to obtain 完税证明",
            "PRC income tax paid offsets U.S. federal tax on Form 1116 (10-yr refund window); avoids 30%–100% evasion fines",
            "Unlocks 100% lawful M01 single-wire conversion",
            ["SRC-01", "SRC-05", "SRC-19", "SRC-23", "SRC-28"],
        ),
        (
            "9. Crypto / Quota-Splitting / Underground Swap / Fake Invoices",
            "M21–M23 REJECTED — DO NOT USE",
            "Illegal FX evasion / illegal financial activity (Decree 532 Arts. 39, 40, 45; Yin Fa [2026] No. 42)",
            "Statutory PRC fine exposure: up to 30% ($120k at $400k) or 30%–100% ($120k–$400k) + account freeze + criminal risk",
            "PROHIBITED ($0 lawful limit)",
            ["SRC-01", "SRC-02", "SRC-21"],
        ),
    ]

    dec_html = "".join(
        f"<tr>"
        f"<td data-label='Origin of Stuck CNY'><strong>{esc(orig)}</strong></td>"
        f"<td data-label='Best Lawful Route'>{esc(rt)}</td>"
        f"<td data-label='PRC &amp; US Tax Rule'>{esc(tx)}</td>"
        f"<td data-label='Published Fee / Exposure'>{esc(fee)}</td>"
        f"<td data-label='Cap &amp; Timeline'>{esc(cap)}</td>"
        f"<td data-label='Official Sources'>{render_sources(sids)}</td>"
        f"</tr>"
        for orig, rt, tx, fee, cap, sids in decision_rows
    )

    body = f"""
<h1>Executive Summary: Best Lawful Way for a U.S. Citizen to Convert Stuck CNY to USD With Minimum Tax Penalties</h1>
<p class="lede">Most important findings first — verified line by line from <strong>40 official government and primary commercial sources</strong> fetched over HTTPS on {esc(RETRIEVED)}. Unconfirmed FX spreads, third-party fees, and private tax amounts are never guessed or filled in.</p>

<div class="callout">
  <p><strong>1. Core Diagnosis — There is $0 standalone "conversion tax" in both China and the United States:</strong> Neither SAFE/STA nor the IRS taxes the act of converting CNY into USD. When a Chinese bank says you cannot convert RMB without "paying taxes," it is enforcing <strong>SAFE's tax-voucher compliance gate</strong> (<a href="https://www.safe.gov.cn/tianjin/2026/0713/3088.html" target="_blank" rel="noopener noreferrer">Hui Fa [2020] No. 14 Art. 59</a>): foreign individuals do <em>not</em> get China's $50,000/year ID-only FX purchase quota unless they hold a <strong>PRC Foreign Permanent Resident ID Card</strong> (<a href="https://www.safe.gov.cn/tianjin/2024/0621/2529.html" target="_blank" rel="noopener noreferrer">SAFE Tianjin 2024 Case 9</a>). Instead, banks require proof of lawful RMB origin <strong>plus official STA tax vouchers (<code>税收完税证明</code> / <code>个人所得税纳税记录</code>)</strong>.</p>
  <p><strong>2. If PRC tax was ALREADY withheld (e.g., payroll salary), your extra PRC tax to convert $10,000–$400,000+ is $0:</strong> Download your tax record from the PRC <code>个人所得税</code> App and wire the full documented balance in <strong>one uncapped bank wire (M01)</strong> — SAFE confirms <strong>no statutory age limit</strong> even on 10-year-old salary (<a href="https://www.safe.gov.cn/henan/2022/0718/1249.html" target="_blank" rel="noopener noreferrer">SAFE Henan Q&amp;A 5</a>), and you can legally authorize an agent in China if you already returned to the U.S. (<a href="https://www.safe.gov.cn/henan/2022/0718/1247.html" target="_blank" rel="noopener noreferrer">SAFE Henan Q&amp;A 3</a>).</p>
  <p><strong>3. If PRC tax was NOT yet paid on PRC-source income, U.S. Foreign Tax Credits prevent double taxation:</strong> Under <a href="https://www.irs.gov/pub/irs-trty/china.pdf" target="_blank" rel="noopener noreferrer">Article 22(2) of the U.S.–China Income Tax Treaty</a> and <a href="https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit" target="_blank" rel="noopener noreferrer">IRS Form 1116</a> (which has a <strong>10-year refund amendment window</strong>), creditable PRC income taxes paid offset U.S. federal tax on that same income dollar-for-dollar (and Treaty Arts. 9–11 cut PRC dividend/interest/royalty withholding from 20% to <strong>10%</strong>). By contrast, illegal "tax-saving" shortcuts (crypto, quota-splitting, underground <code>对敲</code> swaps) carry <strong>up to 30%–100% PRC fines</strong> (<a href="https://www.safe.gov.cn/beijing/2018/1221/1010.html" target="_blank" rel="noopener noreferrer">State Council Decree 532 Arts. 39–45</a>) and zero U.S. tax credit!</p>
</div>

<div class="callout warn">
  <p><strong>Strict Verification Boundary (What Cannot Be Certified Without Your Private Facts):</strong> Exact personal tax due, individual route eligibility, live bank CNY→USD exchange-rate spread, and intermediary/receiving bank deductions depend on your balance's origin, acquisition dates, filing history, and live bank quote. In every table on this site, unconfirmed values remain <strong>blank (<code>—</code>)</strong> and are cataloged on <a href="flagged.html">Flagged for Review (FL-01–FL-18)</a>. USD translations of RMB fee schedules use the latest published <a href="https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates" target="_blank" rel="noopener noreferrer">IRS yearly average rate (7.129 CNY/USD for 2025)</a> solely as a transparent reference.</p>
</div>

<div class="kpi-grid">
  <div class="kpi">
    <p class="label">PRC / US Conversion Excise Tax</p>
    <p class="val">$0.00 (0%)</p>
    <p class="sub">No tax on currency conversion itself; U.S. personal FX gain taxed only if &gt;$200 (<a href="sources.html#SRC-24">26 U.S.C. § 988(e)</a>; <a href="sources.html#SRC-26">Pub. 525</a>).</p>
  </div>
  <div class="kpi">
    <p class="label">M01 Published Sender Wire Fee</p>
    <p class="val">$0.00 or $30.86–$86.97</p>
    <p class="sub">HSBC China PB/Premier Elite: $0; Premier/Advance SHA capped at CNY 620 = $86.97 from ~$70.1k through $400k (<a href="sources.html#SRC-38">SRC-38</a>). Spread blank.</p>
  </div>
  <div class="kpi">
    <p class="label">US–China Treaty Passive Cap</p>
    <p class="val">10% Max WHT</p>
    <p class="sub">Halves PRC 20% rate on dividends, interest &amp; royalties (<a href="sources.html#SRC-23">Treaty Arts. 9–11</a>); creditable on Form 1116.</p>
  </div>
  <div class="kpi">
    <p class="label">Largest Real Penalty Trap</p>
    <p class="val">$16,536 – 50% / 100%</p>
    <p class="sub">U.S. FBAR non-willful $16,536 / willful max($165,353, 50%) (<a href="sources.html#SRC-31">31 CFR 1010.821</a>); PRC FX evasion 30%–100% (<a href="sources.html#SRC-01">Decree 532</a>).</p>
  </div>
</div>

<section class="panel">
  <h2>Decision Matrix: Best Lawful Route by Origin of Stuck CNY (Most Important Info First)</h2>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>Origin of Stuck CNY</th>
          <th>Best Lawful Route</th>
          <th>PRC &amp; US Tax Rule</th>
          <th>Published Fee / Exposure</th>
          <th>Cap &amp; Timeline</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {dec_html}
      </tbody>
    </table>
  </div>
</section>

<section class="panel">
  <h2>Explore All Category Subpages</h2>
  <div class="card-grid">
    <a class="nav-card" href="costs.html">
      <strong>$10,000 → $400,000 Cost Estimator</strong>
      <span class="meta">920 rows · 40 increments × 23 methods · CSV/JSON</span>
      <p>Mobile-friendly milestone comparison plus filterable $10k-increment table for every method, showing published fees, batch counts, and strictly blank unverified spreads.</p>
    </a>
    <a class="nav-card" href="methods.html">
      <strong>All 23 Conversion Methods &amp; Steps</strong>
      <span class="meta">18 lawful · 1 closed-loop · 4 unlawful rejected</span>
      <p>Pros, cons, legal basis, eligibility, and exact step-by-step execution instructions (including remote proxy M05 when already in the U.S.).</p>
    </a>
    <a class="nav-card" href="penalties.html">
      <strong>7-Layer Conversion Penalty Breakdown</strong>
      <span class="meta">Tax gate vs. spread vs. § 988(e) vs. fines</span>
      <p>Decomposes every hidden cost and legal penalty layer, including STA/SAFE &gt;$50k free online Tax Recordal.</p>
    </a>
    <a class="nav-card" href="taxes.html">
      <strong>U.S. Citizen Tax &amp; Reporting Matrix</strong>
      <span class="meta">FTC · FEIE ($132.9k) · Treaty · FBAR · 8938 · 3520</span>
      <p>How to avoid paying double tax legally and cure delinquent offshore filings (0% Foreign vs. 5% Domestic Streamlined).</p>
    </a>
    <a class="nav-card" href="audit.html">
      <strong>Line-by-Line Repository Review</strong>
      <span class="meta">14 source-verified audit findings (RA-01–RA-14)</span>
      <p>Independent verification of existing repo files, catching arithmetic, quota-eligibility, § 988(e), and repealed-citation discrepancies.</p>
    </a>
    <a class="nav-card" href="flagged.html">
      <strong>Flagged for Review</strong>
      <span class="meta">18 unverified / conditional items (FL-01–FL-18)</span>
      <p>Complete transparency register of every blank commercial value, private-fact boundary, and statutory nuance.</p>
    </a>
    <a class="nav-card" href="sources.html">
      <strong>40 Official Primary Sources</strong>
      <span class="meta">100% HTTPS · body-verified on {esc(RETRIEVED)}</span>
      <p>SAFE, PBOC, STA, State Council, IRS, GPO Title 26, eCFR Title 31, CBP, HSBC China Oct 2026 Tariff, Wise, and Western Union.</p>
    </a>
  </div>
</section>
"""
    return shell(
        "index.html",
        "Executive Summary & Decision Dashboard",
        "Source-verified executive summary and decision matrix for a U.S. citizen converting stuck CNY in China into USD with minimum lawful tax penalties.",
        body,
    )


def build_costs(ladder_rows: list[dict]) -> str:
    by_key = {(r["method_id"], r["usd_amount"]): r for r in ladder_rows}
    checkpoints = [10000, 50000, 100000, 200000, 400000]

    ms_rows = []
    for m in METHODS:
        mid = m["id"]
        cells = []
        for cp in checkpoints:
            r = by_key[(mid, cp)]
            if r["prc_statutory_fine_30pct_usd"] is not None:
                val = f"Fine <={r['prc_statutory_fine_30pct_usd']:,.0f}–${r['prc_statutory_fine_100pct_usd']:,.0f}"
            elif r["published_fee_standard_usd"] is not None:
                extra = ""
                if mid == "M12" and r["treaty_dividend_wht_10pct_usd"] is not None:
                    extra = f" + ${r['treaty_dividend_wht_10pct_usd']:,.0f} WHT"
                elif mid in ("M08", "M17", "M20"):
                    extra = "*"
                val = f"${r['published_fee_standard_usd']:,.2f}{extra}"
            else:
                val = "— (blank)"
            b = r["min_batches"]
            sub = f" ({b}x)" if b and b > 1 else ""
            cells.append(f"<td class='num' data-label='${cp:,} USD'>{esc(val)}{esc(sub)}</td>")

        ms_rows.append(
            f"<tr>"
            f"<td data-label='Method'><strong><a href='methods.html#{esc(mid)}'>{esc(mid)}</a></strong> · {esc(m['name'])}</td>"
            f"<td data-label='Status'>{status_badge(m['legal_status'])}</td>"
            + "".join(cells)
            + f"<td data-label='FX Spread &amp; All-In Total'><span class='blank-cell'>— (blank · {render_flags(m['flag_ids'][:2])})</span></td>"
            f"<td data-label='Official Sources'>{render_sources(m['source_ids'])}</td>"
            f"</tr>"
        )

    tier_opts = "".join(f'<option value="{t}">${t:,} USD (CNY {t*RATE:,.0f})</option>' for t in TIERS)
    method_opts = "".join(f'<option value="{esc(m["id"])}">{esc(m["id"])} — {esc(m["name"][:58])}</option>' for m in METHODS)

    full_rows = []
    for r in ladder_rows:
        std_cell = fmt_usd_or_blank(r["published_fee_standard_usd"], "*" if r["method_id"] in ("M08", "M17", "M20") else "")
        if r["prc_statutory_fine_30pct_usd"] is not None:
            alt_cell = f"<span class='badge bad'>Fine <=${r['prc_statutory_fine_30pct_usd']:,.0f} / <=${r['prc_statutory_fine_100pct_usd']:,.0f}</span>"
        elif r["published_fee_Detail_override"] if False else r["secondary_published_detail"]:
            alt_cell = esc(r["secondary_published_detail"])
        else:
            alt_cell = '<span class="blank-cell">— (unverified)</span>'

        full_rows.append(
            f"<tr data-tier='{r['usd_amount']}' data-method='{esc(r['method_id'])}' data-status='{esc(r['legal_status'])}'>"
            f"<td class='num' data-label='USD Tier'><strong>${r['usd_amount']:,}</strong></td>"
            f"<td class='num' data-label='CNY (@7.129)'>¥{r['cny_reference_amount']:,.2f}</td>"
            f"<td data-label='Method'><a href='methods.html#{esc(r['method_id'])}'><strong>{esc(r['method_id'])}</strong></a> · {esc(r['method_name'])}</td>"
            f"<td data-label='Status'>{status_badge(r['legal_status'])}</td>"
            f"<td data-label='Min Batches / Timeline'>{esc(r['schedule_summary'])}</td>"
            f"<td class='num' data-label='Published Primary Fee'>{std_cell}</td>"
            f"<td data-label='Other Published Tiers / Statutory Exposure'>{alt_cell}</td>"
            f"<td data-label='FX Spread &amp; All-In USD'><span class='blank-cell'>— ({render_flags(r['flag_ids'][:1])})</span></td>"
            f"<td data-label='Official Sources'>{render_sources(r['source_ids'])}</td>"
            f"</tr>"
        )

    body = f"""
<h1>CNY → USD Transfer &amp; Conversion Costs: $10,000 to $400,000 USD ($10,000 Increments)</h1>
<p class="lede">Most important comparison first, followed by all <strong>920 verified rows (40 increments × 23 methods)</strong>. Downloads: <a href="exports/cost-ladder-920.csv">CSV (920 rows)</a> · <a href="exports/cost-ladder-920.json">JSON (920 rows)</a>.</p>

<div class="callout">
  <p><strong>How every figure is calculated (zero guesswork):</strong></p>
  <p>1. <strong>Published Bank Fees (<a href="https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf" target="_blank" rel="noopener noreferrer">HSBC China Tariff eff. 2026-10-31</a>, translated at <a href="https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates" target="_blank" rel="noopener noreferrer">IRS 2025 average 7.129 CNY/USD</a>):</strong> Outward SWIFT wire (<code>M01/M05/M07/M09/M10/M11/M13</code>) = <strong>$0.00</strong> for Private Banking &amp; Premier Elite individuals; <strong>0.1% (min CNY 100, max CNY 500) + CNY 120 cable</strong> for Premier &amp; Advance = <strong>$30.86</strong> at $10k, <strong>$66.83</strong> at $50k, and <strong>capped at $86.97</strong> from $70k all the way to $400k! Optional <strong>Pay Exact (OUR)</strong> adds CNY 200 (<strong>+$28.05</strong>). Same-name Global Transfer (<code>M02</code>) = <strong>$0.00</strong> (PB/Premier) or <strong>$20.00</strong> (Advance). Corporate Dividend TT (<code>M12</code>) = <strong>0.1% (min CNY 100, max CNY 1,000) + CNY 140 cable</strong> = <strong>$33.67 → $159.91 cap</strong> plus <strong>10% U.S.–China Treaty dividend withholding</strong> (Form 1116 creditable).</p>
  <p>2. <strong>Why FX Spread &amp; All-In Total are Blank (<code>—</code>):</strong> No government authority or static bank tariff publishes an executable customer CNY/USD spread or third-party correspondent bank deduction. Per project verification rules, unconfirmed values are left strictly blank and flagged (<a href="flagged.html#FL-02">FL-02</a>, <a href="flagged.html#FL-03">FL-03</a>). An asterisk (<code>*</code>) on <code>$0.00*</code> cash/closed-loop rows warns that counter fee waiver does <em>not</em> mean zero FX spread or travel cost.</p>
</div>

<section class="panel">
  <h2>1. Executive Milestone Summary ($10k · $50k · $100k · $200k · $400k Across All 23 Methods)</h2>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>Method</th>
          <th>Status</th>
          <th class="num">$10,000 USD</th>
          <th class="num">$50,000 USD</th>
          <th class="num">$100,000 USD</th>
          <th class="num">$200,000 USD</th>
          <th class="num">$400,000 USD</th>
          <th>FX Spread &amp; All-In Total</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {"".join(ms_rows)}
      </tbody>
    </table>
  </div>
</section>

<section class="panel">
  <h2>2. Full 40-Increment Cost Table ($10,000 → $400,000 USD in $10,000 Steps · All 23 Methods)</h2>
  <div class="controls" role="region" aria-label="Filter 920 cost rows">
    <div class="control-group">
      <label for="filter-tier">USD Amount ($10k steps)</label>
      <select id="filter-tier">
        <option value="">All 40 increments ($10,000–$400,000)</option>
        {tier_opts}
      </select>
    </div>
    <div class="control-group">
      <label for="filter-method">Method (M01–M23)</label>
      <select id="filter-method">
        <option value="">All 23 methods</option>
        {method_opts}
      </select>
    </div>
    <div class="control-group">
      <label for="filter-status">Legal Classification</label>
      <select id="filter-status">
        <option value="">All classifications</option>
        <option value="lawful-documented">Lawful · Documented</option>
        <option value="lawful-conditional">Lawful · Conditional</option>
        <option value="closed-loop-non-exit">Closed-Loop · Non-Exit</option>
        <option value="rejected-unlawful">Rejected · Unlawful</option>
      </select>
    </div>
    <div class="control-group">
      <label for="filter-search">Keyword Search</label>
      <input id="filter-search" type="search" placeholder="e.g. Wise, ATM, property, Premier...">
    </div>
    <button id="filter-reset" class="btn secondary" type="button">Reset Filters</button>
  </div>
  <p id="filter-count" class="filter-count" aria-live="polite">Showing 920 of 920 verified rows ($10,000 to $400,000 USD across all 23 methods).</p>
  <div class="table-wrap stack-mobile">
    <table id="ladder-table" class="data-table stack-mobile">
      <thead>
        <tr>
          <th class="num">USD Tier</th>
          <th class="num">CNY (@7.129)</th>
          <th>Method</th>
          <th>Status</th>
          <th>Min Batches / Timeline</th>
          <th class="num">Published Primary Fee</th>
          <th>Other Published Tiers / Statutory Exposure</th>
          <th>FX Spread &amp; All-In USD</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {"".join(full_rows)}
      </tbody>
    </table>
  </div>
</section>
"""
    return shell(
        "costs.html",
        "$10,000 to $400,000 Cost Tables",
        "Mobile-friendly $10,000-increment CNY to USD conversion and transfer cost tables up to $400,000 across all 23 methods.",
        body,
    )


def build_methods() -> str:
    summary_rows = []
    detail_blocks = []

    for m in METHODS:
        mid = m["id"]
        cat = CATEGORIES[m["category"]]
        summary_rows.append(
            f"<tr data-filterable='1' data-category='{esc(m['category'])}' data-status='{esc(m['legal_status'])}'>"
            f"<td data-label='ID'><a href='#{esc(mid)}'><strong>{esc(mid)}</strong></a></td>"
            f"<td data-label='Category'>Cat {esc(m['category'])}</td>"
            f"<td data-label='Method'><strong>{esc(m['name'])}</strong></td>"
            f"<td data-label='Status'>{status_badge(m['legal_status'])}</td>"
            f"<td data-label='Statutory Cap / Gate'>{esc(m['statutory_cap'])}</td>"
            f"<td data-label='PRC Tax at Conversion'>{esc(m['prc_tax_at_conversion'])}</td>"
            f"<td data-label='Official Sources'>{render_sources(m['source_ids'])}</td>"
            f"</tr>"
        )

        pros_li = "".join(f"<li>{esc(p)}</li>" for p in m["pros"])
        cons_li = "".join(f"<li>{esc(c)}</li>" for c in m["cons"])
        steps_li = "".join(f"<li>{esc(st)}</li>" for st in m["steps"])

        detail_blocks.append(
            f"""
<article id="{esc(mid)}" class="method-card" data-filterable="1" data-category="{esc(m['category'])}" data-status="{esc(m['legal_status'])}">
  <div class="method-head">
    <h3>{esc(mid)} · {esc(m['name'])}</h3>
    <div>{status_badge(m['legal_status'])} · <span class="badge cond">Category {esc(m['category'])}: {esc(cat['title'])}</span></div>
  </div>
  <p><strong>Best for:</strong> {esc(m['best_for'])}</p>
  <p><strong>Statutory limit &amp; gate:</strong> {esc(m['statutory_cap'])}</p>
  <p><strong>PRC tax rule:</strong> {esc(m['prc_tax_at_conversion'])}<br>
     <strong>U.S. tax &amp; reporting impact:</strong> {esc(m['us_tax_impact'])}</p>
  <div class="two-col">
    <div>
      <strong>Pros (Verified)</strong>
      <ul>{pros_li}</ul>
    </div>
    <div>
      <strong>Cons &amp; Restrictions (Verified)</strong>
      <ul>{cons_li}</ul>
    </div>
  </div>
  <div>
    <strong>Exact Step-by-Step Execution</strong>
    <ol class="steps-list">{steps_li}</ol>
  </div>
  <p style="margin-top:0.7rem;font-size:0.84rem"><strong>Official Sources:</strong> {render_sources(m['source_ids'], max_direct=6)} · <strong>Flags:</strong> {render_flags(m['flag_ids'])} · <a href="costs.html">See $10k–$400k cost rows</a></p>
</article>"""
        )

    cat_opts = "".join(f'<option value="{ esc(c["code"]) }">Category {esc(c["code"])}: {esc(c["title"])}</option>' for c in METHODS_DOC["meta"]["categories"])

    body = f"""
<h1>All 23 CNY → USD Conversion &amp; Repatriation Methods: Pros, Cons &amp; Step-by-Step Guide</h1>
<p class="lede">Comprehensive catalog of <strong>18 lawful/conditional channels</strong>, <strong>1 closed-loop non-exit channel</strong>, and <strong>4 unlawful/rejected workarounds</strong> — with verified pros, cons, tax rules, and step-by-step execution.</p>

<div class="controls" role="region" aria-label="Filter methods">
  <div class="control-group">
    <label for="page-status">Filter by Category</label>
    <select id="page-status">
      <option value="">All 5 categories (23 methods)</option>
      {cat_opts}
    </select>
  </div>
  <div class="control-group">
    <label for="page-search">Search Methods, Pros, Cons, or Steps</label>
    <input id="page-search" type="search" placeholder="e.g. proxy, property, Wise, inheritance, Green Card...">
  </div>
  <button id="page-reset" class="btn secondary" type="button">Reset</button>
</div>
<p id="page-count" class="filter-count" aria-live="polite"></p>

<section class="panel">
  <h2>Quick Comparison Table (All 23 Methods)</h2>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>ID</th>
          <th>Category</th>
          <th>Method</th>
          <th>Status</th>
          <th>Statutory Cap / Gate</th>
          <th>PRC Tax at Conversion</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {"".join(summary_rows)}
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Detailed Pros, Cons &amp; Step-by-Step Playbooks (M01–M23)</h2>
  {"".join(detail_blocks)}
</section>
"""
    return shell(
        "methods.html",
        "All 23 CNY→USD Methods, Pros/Cons & Step-by-Step Guide",
        "Complete comparison of 23 CNY to USD conversion methods with pros, cons, statutory limits, and step-by-step execution.",
        body,
    )



def build_questions() -> str:
    rows = "".join(
        f"<tr id='{esc(q['id'])}' data-filterable='1' data-status='{esc(q['status'])}'>"
        f"<td data-label='ID'><strong>{esc(q['id'])}</strong><br>{status_badge(q['status'])}</td>"
        f"<td data-label='Question'><strong>{esc(q['question'])}</strong><p style='margin:0.4rem 0 0;font-size:0.85rem;color:#243831'><strong>Why it matters:</strong> {esc(q['why_it_matters'])}</p></td>"
        f"<td data-label='What We Already Know'>{esc(q['what_we_know'])}</td>"
        f"<td data-label='What We DO NOT Know (your private facts)'><span class='blank-cell'>{esc(q['what_we_dont_know'])}</span></td>"
        f"<td data-label='How to Discover / Next Step'>{esc(q['how_to_discover'])}</td>"
        f"<td data-label='Official Sources'>{render_sources(q['source_ids'], max_direct=3)}</td>"
        f"</tr>"
        for q in QUESTIONS
    )
    body = f"""
<h1>Decision Checklist: 12 Questions You Must Answer Before Moving Any Money</h1>
<p class="lede">No decision can be made on the facts provided. The table below lists <strong>what we know from official sources</strong>, <strong>what we do not know about your private account</strong>, and <strong>exact next steps to discover missing information</strong> — every row linked to a primary government or bank source.</p>

<div class="callout">
  <p><strong>How to use this checklist:</strong> Work top to bottom. Questions <strong>Q01–Q06</strong> are gating — answering them determines which of the 23 methods (M01–M23) is even lawful for you and what the true tax is. Questions <strong>Q07–Q12</strong> refine timing, cost, and reporting. Bring this table to both your China bank FX counter <em>and</em> your U.S. cross-border CPA/attorney. <strong>Never pay a tax or fee you cannot name — demand the bank's refusal in writing with article, taxpayer, period, and amount.</strong></p>
</div>

<div class="callout warn">
  <p><strong>What we cannot determine from the prompt:</strong> The origin of funds, whether PRC tax was already withheld, your SAFE classification (PR-ID holder or not), prior U.S. FBAR/8938 history, your bank and live quote, and whether you have been offered gray-market workarounds. Every <em>What We DO NOT Know</em> cell explains the private fact and <em>How to Discover</em> gives a concrete action.</p>
</div>

<section class="panel">
  <h2>The 12 Questions: Knowns, Unknowns & Discovery Steps (Q01–Q12)</h2>
  <div class="controls" role="region" aria-label="Filter questions">
    <div class="control-group">
      <label for="page-status">Priority</label>
      <select id="page-status">
        <option value="">All 12 questions</option>
        <option value="critical">Critical (gating)</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </div>
    <div class="control-group">
      <label for="page-search">Search Questions, Knowns & Steps</label>
      <input id="page-search" type="search" placeholder="e.g. salary, tax voucher, FBAR, proxy, ATM...">
    </div>
    <button id="page-reset" class="btn secondary" type="button">Reset</button>
  </div>
  <p id="page-count" class="filter-count" aria-live="polite"></p>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>ID</th>
          <th>Question & Why It Matters</th>
          <th>What We Already Know (Official Sources)</th>
          <th>What We DO NOT Know</th>
          <th>How to Discover / Next Step</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</section>

<section class="panel">
  <h2>What to Do Next (Suggested Order)</h2>
  <ol>
    <li><strong>Classify every tranche (Q01→Q02):</strong> Pull 5-year statements + IIT records; separate taxed salary from untaxed receipts, property/inheritance from business profit.</li>
    <li><strong>Confirm your SAFE category (Q03) and physical location (Q08):</strong> Are you PR-ID holder or standard foreign passport? In China or back in U.S. needing proxy (M05)?</li>
    <li><strong>Check U.S. reporting cure (Q05) BEFORE wiring:</strong> If prior FBAR/8938 were missed and non-willful, evaluate Streamlined Foreign 0% vs Domestic 5% — wiring first raises willfulness risk.</li>
    <li><strong>Get the bank's all-in written quote (Q06) and compare to the published HSBC Oct 2026 tariff:</strong> Demand separate lines for tax payment vs. tax certificate, and for commission/cable vs. spread.</li>
    <li><strong>Choose the cheapest lawful lump-sum route (M01, M09, M10, M11) and execute with records (Q12):</strong> Single documented wire is 6x cheaper in sender fees than 8 annual $50k quota wires.</li>
  </ol>
</section>
"""
    return shell(
        "questions.html",
        "Decision Checklist — 12 Questions Before Any Transfer",
        "12 gating questions separating what official sources confirm from what private facts remain unknown, with exact discovery steps for each.",
        body,
    )


def build_penalties() -> str:
    rows = "".join(
        f"<tr>"
        f"<td data-label='Layer'><strong>{esc(p['layer'])}</strong></td>"
        f"<td data-label='Cost / Penalty Component'><strong>{esc(p['component'])}</strong></td>"
        f"<td data-label='Verified Rate / Amount'>{esc(p['verified_rate_or_amount'])}</td>"
        f"<td data-label='When &amp; Why It Applies'>{esc(p['who_pays_and_when'])}</td>"
        f"<td data-label='How to Minimize Lawfully'>{esc(p['how_to_minimize_legally'])}</td>"
        f"<td data-label='Official Sources'>{render_sources(p['source_ids'], max_direct=4)}</td>"
        f"</tr>"
        for p in PENALTY_LAYERS
    )

    body = f"""
<h1>Deep Breakdown of the "Conversion Penalty" (All 7 Cost &amp; Risk Layers)</h1>
<p class="lede">Why banks in China tell U.S. citizens they "cannot convert CNY without paying taxes" — and how each of the seven distinct friction layers actually works under PRC and U.S. law.</p>

<div class="callout">
  <p><strong>Key Insight:</strong> People lump seven completely different things under the phrase "conversion penalty." Separating them reveals why <strong>settling/proving lawful PRC tax + claiming U.S. Form 1116 Foreign Tax Credits + wiring in one documented lump sum (M01)</strong> beats every gray-market workaround.</p>
</div>

<section class="panel">
  <h2>The 7 Layers of CNY → USD Conversion Friction &amp; Tax Exposure</h2>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>Layer</th>
          <th>Cost / Penalty Component</th>
          <th>Verified Rate / Amount</th>
          <th>When &amp; Why It Applies</th>
          <th>How to Minimize Lawfully</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</section>

<section class="panel">
  <h2>Why STA/SAFE Outbound Tax Recordal (&gt; USD 50,000) Is Frequently Misunderstood as a "Tax"</h2>
  <p>Under <a href="https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103016/c5250711/content.html" target="_blank" rel="noopener noreferrer">STA &amp; SAFE Announcement [2013] No. 40</a> and <a href="https://tianjin.chinatax.gov.cn/11200000000/0300/030004/03000418/20210705111145797.shtml" target="_blank" rel="noopener noreferrer">Supplementary Announcement [2021] No. 19</a>:</p>
  <ul>
    <li>When a <strong>domestic payer</strong> (such as a PRC company paying dividends/remuneration or a Chinese buyer paying &gt; USD 50,000 for your PRC apartment) remits &gt; USD 50,000 outbound, it must file a <strong>Tax Recordal Form (<code>服务贸易等项目对外支付税务备案表</code>)</strong>.</li>
    <li><strong>Filing fee = $0.00</strong>, processed online via the Electronic Tax Bureau or on the spot at the tax hall without on-the-spot tax audit, and required <strong>only once per contract</strong> under the 2021 supplement.</li>
    <li>When a <strong>foreign individual</strong> converts their own current-account lawful RMB income already sitting in their personal Mainland account, <strong>Article 4</strong> directs banks to apply SAFE's individual FX rule (<a href="https://www.safe.gov.cn/tianjin/2026/0713/3088.html" target="_blank" rel="noopener noreferrer">Hui Fa [2020] No. 14 Art. 59</a>): valid passport + contract/income proof + <strong>STA tax payment record (<code>个人所得税纳税记录</code>)</strong>.</li>
  </ul>
</section>
"""
    return shell(
        "penalties.html",
        "7-Layer Conversion Penalty Breakdown",
        "Line-by-line decomposition of all 7 CNY to USD conversion cost, tax, spread, and compliance penalty layers.",
        body,
    )


def build_taxes() -> str:
    rows = "".join(
        f"<tr id='{esc(t['id'])}' data-filterable='1' data-status='{esc(t['jurisdiction'])}'>"
        f"<td data-label='ID'><strong>{esc(t['id'])}</strong></td>"
        f"<td data-label='Jurisdiction'><span class='badge cond'>{esc(t['jurisdiction'])}</span></td>"
        f"<td data-label='Rule / Form'><strong>{esc(t['item'])}</strong></td>"
        f"<td data-label='Threshold / Scope'>{esc(t['threshold_or_scope'])}</td>"
        f"<td data-label='Verified Rate / Penalty'>{esc(t['verified_rate_or_penalty'])}</td>"
        f"<td data-label='Action for U.S. Citizen'>{esc(t['action_for_us_citizen'])}</td>"
        f"<td data-label='Official Sources'>{render_sources(t['source_ids'], max_direct=4)}</td>"
        f"</tr>"
        for t in TAX_ROWS
    )

    body = f"""
<h1>U.S. Citizen Tax Minimizer &amp; Offshore Reporting Compliance Matrix</h1>
<p class="lede">Exact statutory thresholds, treaty caps, Foreign Tax Credit vs. FEIE interactions, § 988(e) currency-gain rules, and FinCEN/IRS penalty exposures — every row backed by official government links.</p>

<div class="callout warn">
  <p><strong>Critical U.S. Citizen Trap — Treaty Saving Clause + Compulsory-Tax Rule:</strong> Under <a href="https://www.irs.gov/pub/irs-trty/china.pdf" target="_blank" rel="noopener noreferrer">Protocol 1 Paragraph 2 of the 1984 U.S.–China Income Tax Treaty</a>, the United States taxes its citizens on worldwide income regardless of residence. However, <strong>Article 22(2)</strong> is expressly excepted from the Saving Clause, guaranteeing U.S. citizens a Foreign Tax Credit for PRC income taxes paid — <strong>PROVIDED</strong> you claimed any treaty rate reduction you were entitled to (such as the <strong>10% cap</strong> on dividends, interest, and royalties under Arts. 9–11; <a href="https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit" target="_blank" rel="noopener noreferrer">IRS Foreign Tax Credit rules</a> disallow crediting voluntary excess foreign withholding!).</p>
</div>

<section class="panel">
  <h2>PRC &amp; U.S. Tax, Treaty &amp; Reporting Table (TX-01–TX-12)</h2>
  <div class="controls" role="region" aria-label="Search tax rules">
    <div class="control-group">
      <label for="page-search">Filter Tax &amp; Reporting Rules</label>
      <input id="page-search" type="search" placeholder="e.g. 1116, FBAR, 3520, 988, Streamlined, dividend...">
    </div>
    <button id="page-reset" class="btn secondary" type="button">Reset</button>
  </div>
  <p id="page-count" class="filter-count" aria-live="polite"></p>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>ID</th>
          <th>Jurisdiction</th>
          <th>Rule / Form</th>
          <th>Threshold / Scope</th>
          <th>Verified Rate / Penalty</th>
          <th>Action for U.S. Citizen</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</section>
"""
    return shell(
        "taxes.html",
        "U.S. & PRC Tax, Treaty & Reporting Matrix",
        "Official-source matrix of PRC IIT/EIT, U.S.–China Tax Treaty, Form 1116 FTC, Form 2555 FEIE, IRC § 988(e), FBAR, Form 8938, Form 3520, and Streamlined procedures.",
        body,
    )


def build_audit() -> str:
    rows = "".join(
        f"<tr id='{esc(a['id'])}' data-filterable='1' data-severity='{esc(a['severity'])}'>"
        f"<td data-label='Audit ID'><strong>{esc(a['id'])}</strong></td>"
        f"<td data-label='Severity'>{status_badge(a['severity'])}</td>"
        f"<td data-label='Repo File &amp; Lines'><code>{esc(a['file_and_lines'])}</code></td>"
        f"<td data-label='Irregularity Found'>{esc(a['finding'])}</td>"
        f"<td data-label='Verified Official Rule'>{esc(a['official_verification'])}</td>"
        f"<td data-label='Disposition'>{esc(a['disposition'])}</td>"
        f"<td data-label='Official Sources'>{render_sources(a['source_ids'], max_direct=4)}</td>"
        f"</tr>"
        for a in REPO_AUDIT
    )

    body = f"""
<h1>Line-by-Line Repository Review (RA-01 – RA-14)</h1>
<p class="lede">Independent audit of inherited files and prior session dashboards in <code>sassnarep3-star/China2</code> against primary official sources retrieved on {esc(RETRIEVED)}. Per parallel-session rules, other sessions' owned files were not unilaterally overwritten; findings are published here with official links for review.</p>

<section class="panel">
  <h2>Repository Audit Findings Table (14 Findings)</h2>
  <div class="controls" role="region" aria-label="Filter repo audit">
    <div class="control-group">
      <label for="page-status">Severity</label>
      <select id="page-status">
        <option value="">All severities (14)</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </div>
    <div class="control-group">
      <label for="page-search">Search Repo Audit</label>
      <input id="page-search" type="search" placeholder="e.g. ATM, 8+ years, 50,000, 988, 237...">
    </div>
    <button id="page-reset" class="btn secondary" type="button">Reset</button>
  </div>
  <p id="page-count" class="filter-count" aria-live="polite"></p>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>Audit ID</th>
          <th>Severity</th>
          <th>Repo File &amp; Lines</th>
          <th>Irregularity Found</th>
          <th>Verified Official Rule</th>
          <th>Disposition</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</section>
"""
    return shell(
        "audit.html",
        "Line-by-Line Repository Audit",
        "14 line-numbered repository audit findings verified against official PRC and U.S. primary sources.",
        body,
    )


def build_flagged() -> str:
    rows = "".join(
        f"<tr id='{esc(f['id'])}' data-filterable='1' data-severity='{esc(f['severity'])}'>"
        f"<td data-label='Flag ID'><strong>{esc(f['id'])}</strong></td>"
        f"<td data-label='Priority'>{status_badge(f['severity'])}</td>"
        f"<td data-label='Unverified / Conditional Item'><strong>{esc(f['title'])}</strong></td>"
        f"<td data-label='Blank Table Fields'>{esc(f['blank_fields'])}</td>"
        f"<td data-label='Why Left Blank / Needs Review'>{esc(f['explanation'])}</td>"
        f"<td data-label='Official Sources'>{render_sources(f['source_ids'], max_direct=4)}</td>"
        f"</tr>"
        for f in FLAGS
    )

    body = f"""
<h1>Flagged for Review (FL-01 – FL-18)</h1>
<p class="lede">Every value that cannot be confirmed from an official primary source is left strictly blank (never inferred or filled in) and documented below with direct official source links for manual review. Per project instructions, these <code>needs review</code> items do not block publication.</p>

<section class="panel">
  <h2>Unverified Values, Private-Fact Dependencies &amp; Statutory Caveats (18 Flags)</h2>
  <div class="controls" role="region" aria-label="Filter flags">
    <div class="control-group">
      <label for="page-status">Priority</label>
      <select id="page-status">
        <option value="">All priorities (18)</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </div>
    <div class="control-group">
      <label for="page-search">Search Flags</label>
      <input id="page-search" type="search" placeholder="e.g. spread, Wise, Western Union, PFIC, state tax...">
    </div>
    <button id="page-reset" class="btn secondary" type="button">Reset</button>
  </div>
  <p id="page-count" class="filter-count" aria-live="polite"></p>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>Flag ID</th>
          <th>Priority</th>
          <th>Unverified / Conditional Item</th>
          <th>Blank Table Fields</th>
          <th>Why Left Blank / Needs Review</th>
          <th>Official Sources</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</section>
"""
    return shell(
        "flagged.html",
        "Flagged for Review",
        "18 unverified commercial values, account-specific unknowns, and statutory caveats published with official links for manual review.",
        body,
    )


def build_sources() -> str:
    rows = []
    n_prc = sum(1 for s in SOURCES_DOC["sources"] if s["jurisdiction"] == "PRC")
    n_us = sum(1 for s in SOURCES_DOC["sources"] if s["jurisdiction"] in ("US", "US-PRC Treaty"))
    n_comm = sum(1 for s in SOURCES_DOC["sources"] if s["jurisdiction"] not in ("PRC", "US", "US-PRC Treaty"))
    n_ver = sum(1 for s in SOURCES_DOC["sources"] if s["status"] == "verified")
    n_lim = sum(1 for s in SOURCES_DOC["sources"] if s["status"] == "verified-limited")
    for s in SOURCES_DOC["sources"]:
        rows.append(
            f"<tr id='{esc(s['id'])}' data-filterable='1' data-status='{esc(s['status'])}'>"
            f"<td data-label='Source ID'><strong>{esc(s['id'])}</strong></td>"
            f"<td data-label='Jurisdiction'>{esc(s['jurisdiction'])}</td>"
            f"<td data-label='Authority'>{esc(s['authority'])}</td>"
            f"<td data-label='Document &amp; Locator'><strong><a href='{esc(s['url'])}' target='_blank' rel='noopener noreferrer'>{esc(s['title'])}</a></strong><br><small>Locator: {esc(s['locator'])} · Published/Eff: {esc(s['published_or_effective'])}</small>"
            f"<div class='quote-box'>{esc(s['verbatim_excerpt'])}</div></td>"
            f"<td data-label='Status'>{status_badge(s['status'])}<br><small>Fetched {esc(s['retrieved_date'])}</small></td>"
            f"<td data-label='Direct Official Link'><a href='{esc(s['url'])}' target='_blank' rel='noopener noreferrer'>{esc(host_label(s['url']))}</a></td>"
            f"</tr>"
        )

    body = f"""
<h1>Official Primary Source Registry (SRC-01 – SRC-{len(SOURCES_DOC['sources']):02d})</h1>
<p class="lede">All <strong>{len(SOURCES_DOC['sources'])} primary sources</strong> ({n_prc} PRC statutory/regulatory/tax/central-bank documents, {n_us} U.S. statutory/IRS/FinCEN/CBP/Treaty documents, and {n_comm} primary published commercial schedules) were retrieved over HTTPS on <strong>{esc(RETRIEVED)}</strong> with verbatim excerpts recorded below.</p>

<section class="panel">
  <h2>Verified Primary Sources Table ({len(SOURCES_DOC['sources'])} Sources)</h2>
  <div class="controls" role="region" aria-label="Filter sources">
    <div class="control-group">
      <label for="page-status">Verification Status</label>
      <select id="page-status">
        <option value="">All {len(SOURCES_DOC['sources'])} sources</option>
        <option value="verified">Verified ({n_ver})</option>
        <option value="verified-limited">Verified · Limited ({n_lim})</option>
      </select>
    </div>
    <div class="control-group">
      <label for="page-search">Search Title, Authority, or Verbatim Excerpt</label>
      <input id="page-search" type="search" placeholder="e.g. SAFE, 988, Pub 525, 3520, HSBC, Wise...">
    </div>
    <button id="page-reset" class="btn secondary" type="button">Reset</button>
  </div>
  <p id="page-count" class="filter-count" aria-live="polite"></p>
  <div class="table-wrap stack-mobile">
    <table class="data-table stack-mobile">
      <thead>
        <tr>
          <th>Source ID</th>
          <th>Jurisdiction</th>
          <th>Authority</th>
          <th>Document, Locator &amp; Verbatim Excerpt</th>
          <th>Status</th>
          <th>Direct Official Link</th>
        </tr>
      </thead>
      <tbody>
        {"".join(rows)}
      </tbody>
    </table>
  </div>
</section>
"""
    return shell(
        "sources.html",
        "40 Official Primary Sources",
        "Complete registry of 40 official government and primary provider sources fetched over HTTPS with verbatim excerpts.",
        body,
    )


def build_exec_summary_md(ladder_rows: list[dict]) -> str:
    by_key = {(r["method_id"], r["usd_amount"]): r for r in ladder_rows}
    n_prc = sum(1 for s in SOURCES_DOC["sources"] if s["jurisdiction"] == "PRC")
    n_us = sum(1 for s in SOURCES_DOC["sources"] if s["jurisdiction"] in ("US", "US-PRC Treaty"))
    n_comm = sum(1 for s in SOURCES_DOC["sources"] if s["jurisdiction"] not in ("PRC", "US", "US-PRC Treaty"))
    return f"""# Executive Summary: Best Lawful Way for a U.S. Citizen to Convert Stuck CNY to USD With Minimum Tax Penalties

**Session:** `arena/8f529c94-china2` · **Retrieved & Verified:** `{RETRIEVED}` · **Scope:** `transfer-guide/`  
**Evidence Base:** {len(SOURCES_DOC['sources'])} directly fetched HTTPS primary sources ({n_prc} PRC official `safe.gov.cn`/`pbc.gov.cn`/`chinatax.gov.cn`/`gov.cn`, {n_us} U.S. official `irs.gov`/`govinfo.gov`/`ecfr.gov`/`cbp.gov`, {n_comm} primary published commercial schedules `hsbc.com.cn`/`wise.com`/`westernunion.com`). *Research only; not individualized legal or tax advice.*

---

## 1. Direct Answer: Why Your Money Is "Stuck" — and How to Pay the Minimum Lawful Tax

1. **Neither China nor the U.S. levies a standalone "currency conversion tax" ($0 / 0%):**  
   China's FX regime ([State Council Decree No. 532 Art. 5](https://www.safe.gov.cn/beijing/2018/1221/1010.html)) guarantees free current-account international payments on authentic transactions. When a Mainland bank tells a U.S. citizen they cannot convert RMB into USD without "paying taxes," the bank is enforcing **SAFE's tax-voucher documentation gate** ([SAFE Tianjin 2026 FAQ 08 / Hui Fa [2020] No. 14 Art. 59](https://www.safe.gov.cn/tianjin/2026/0713/3088.html)), because a U.S. passport holder does **not** get the $50,000/year ID-only FX purchase quota unless they hold a **PRC Foreign Permanent Resident ID Card** ([SAFE Tianjin 2024 Case 9](https://www.safe.gov.cn/tianjin/2024/0621/2529.html)).

2. **If PRC tax was ALREADY withheld (e.g., payroll wages), your extra PRC tax to convert $10,000–$400,000+ is $0:**  
   Download your official `个人所得税纳税记录` from the PRC **Personal Income Tax App (`个人所得税` App)** (or print `税收完税证明` at the local tax hall) and use **Method M01 (Documented Bank Counter Conversion + SWIFT Wire)**.
   - **No $50,000/year cap:** You can convert and wire the entire documented balance in **1 wire** ([PBOC Decree [2006] No. 3 Art. 13](https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html)).
   - **No statutory age limit:** Even 10-year-old lawful RMB salary can be converted at a bank if original contracts + tax proofs are presented ([SAFE Henan Q&A 5](https://www.safe.gov.cn/henan/2022/0718/1249.html)) — whereas Wise (`M03`/`M04`) rejects tax records older than 3 years ([Wise CNY Guide](https://wise.com/help/articles/2955298/guide-to-cny-transfers)).
   - **Remote execution if already in the U.S.:** SAFE expressly permits entrusting employer finance staff or another agent (`M05`) to complete salary FX conversion and wire out ([SAFE Henan Q&A 3](https://www.safe.gov.cn/henan/2022/0718/1247.html)).

3. **If PRC tax was NOT yet paid, U.S. Foreign Tax Credits (`Form 1116`) + U.S.–China Tax Treaty caps prevent double taxation:**  
   As a U.S. citizen taxed on worldwide income, paying legitimate PRC income tax on China-source earnings is **creditable dollar-for-dollar against U.S. federal tax** on that same income ([1984 U.S.–China Tax Treaty Art. 22(2)](https://www.irs.gov/pub/irs-trty/china.pdf); [IRS Foreign Tax Credit](https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit), with a **10-year Form 1040-X refund window**). Always claim **Treaty Arts. 9(2), 10(2), and 11(2)** to cap PRC dividend, interest, and royalty withholding at **10%** (instead of 20% domestic), because the IRS disallows FTC for voluntary overpayment above a treaty rate!

4. **Check U.S. Personal FX Gain (`>$200`) and Offshore Reporting (`FBAR` / `8938` / `3520`) BEFORE wiring:**  
   - **Personal FX Gain:** Exempt if exchange gain is **<= $200** per personal transaction ([26 U.S.C. § 988(e)(2)](https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm)); if **> $200**, report as capital gain ([IRS Pub. 525 (2025)](https://www.irs.gov/publications/p525)).
   - **FBAR (`FinCEN 114`):** Mandatory if aggregate foreign accounts > **$10,000** at any time in the year ([IRS FBAR](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar)); civil penalty max **$16,536** non-willful / **max($165,353, 50%)** willful ([31 CFR § 1010.821](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821)). If delinquent due to non-willful error and not under IRS exam, evaluate **Streamlined Foreign Offshore (`0%` penalty)** or **Streamlined Domestic Offshore (`5%` penalty)** ([IRS Streamlined](https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures)).

---

## 2. Published Fee Checkpoints ($10,000 → $400,000 USD at IRS 2025 Reference Rate 7.129 CNY/USD)

| Method | $10,000 | $50,000 | $100,000 | $200,000 | $400,000 | FX Spread & All-In Total | Official Source |
|---|---:|---:|---:|---:|---:|---|---|
| **M01 / M05 / M07 / M09 / M10 / M11 / M13** (HSBC Premier/Advance `SHA` 1 wire) | ${by_key[("M01", 10000)]["published_fee_standard_usd"]:,.2f} | ${by_key[("M01", 50000)]["published_fee_standard_usd"]:,.2f} | ${by_key[("M01", 100000)]["published_fee_standard_usd"]:,.2f} | ${by_key[("M01", 200000)]["published_fee_standard_usd"]:,.2f} | ${by_key[("M01", 400000)]["published_fee_standard_usd"]:,.2f} | `—` (unverified; PB/Premier Elite = `$0.00`; `OUR` adds `$28.05`) | [HSBC Tariff](https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf) |
| **M02** (HSBC Global Transfer to Self after FX conversion) | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | `—` (unverified; Advance segment = `$20.00`/tx) | [HSBC Tariff](https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf) |
| **M06** (PR-ID `$50k`/yr Quota — 1 to 8 annual wires) | ${by_key[("M06", 10000)]["published_fee_standard_usd"]:,.2f} | ${by_key[("M06", 50000)]["published_fee_standard_usd"]:,.2f} | ${by_key[("M06", 100000)]["published_fee_standard_usd"]:,.2f} (2 yrs) | ${by_key[("M06", 200000)]["published_fee_standard_usd"]:,.2f} (4 yrs) | ${by_key[("M06", 400000)]["published_fee_standard_usd"]:,.2f} (8 yrs) | `—` (unverified; PR-ID / PRC ID holders only) | [SAFE Case 9](https://www.safe.gov.cn/tianjin/2024/0621/2529.html) |
| **M12** (WFOE Dividend: HSBC Entity TT + 10% Treaty WHT) | ${by_key[("M12", 10000)]["published_fee_standard_usd"]:,.2f} + $1,000 WHT | ${by_key[("M12", 50000)]["published_fee_standard_usd"]:,.2f} + $5,000 WHT | ${by_key[("M12", 100000)]["published_fee_standard_usd"]:,.2f} + $10,000 WHT | ${by_key[("M12", 200000)]["published_fee_standard_usd"]:,.2f} + $20,000 WHT | ${by_key[("M12", 400000)]["published_fee_standard_usd"]:,.2f} + $40,000 WHT | `—` (10% WHT creditable on Form 1116) | [Treaty Art. 9](https://www.irs.gov/pub/irs-trty/china.pdf) |
| **M03 / M04 / M14 / M15 / M16 / M18 / M19** (Wise / Trade / ATM / Card / Cash / WU) | `—` | `—` | `—` | `—` | `—` | `—` (live quote / issuer-specific; ATM takes **29 yrs** at $400k!) | [Wise](https://wise.com/help/articles/2955298/guide-to-cny-transfers) · [SAFE ATM](https://www.safe.gov.cn/en/2017/1230/1397.html) |
| **M21–M23** (REJECTED: Splitting / Crypto / Underground Swap) | Fine <=$3k–$10k | Fine <=$15k–$50k | Fine <=$30k–$100k | Fine <=$60k–$200k | Fine <=$120k–$400k | **PROHIBITED** (30% / 30%–100% PRC fines + criminal risk) | [Decree 532](https://www.safe.gov.cn/beijing/2018/1221/1010.html) · [Yin Fa [2026] 42](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html) |

Full 920-row ($10,000-increment) dataset, 23 method playbooks, 7-layer penalty analysis, 14 repo-audit findings, 18 flags, and 40 official sources are published in `transfer-guide/index.html`.
"""


def write_exports(ladder_rows: list[dict]) -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    json_path = EXPORTS / "cost-ladder-920.json"
    json_path.write_text(
        json.dumps(
            {
                "meta": {
                    "session": "arena/8f529c94-china2",
                    "retrieved_date": RETRIEVED,
                    "reference_fx_rate_cny_per_usd": RATE,
                    "method_count": len(METHODS),
                    "tier_count": len(TIERS),
                    "row_count": len(ladder_rows),
                    "blank_policy": "null in JSON and empty string in CSV indicate unconfirmed values left strictly blank per verification rules.",
                },
                "rows": ladder_rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    csv_fields = [
        "usd_amount",
        "cny_reference_amount",
        "reference_fx_rate",
        "method_id",
        "method_name",
        "category",
        "legal_status",
        "min_batches",
        "min_calendar_years",
        "schedule_summary",
        "published_fee_pb_usd",
        "published_fee_standard_usd",
        "published_fee_alt_usd",
        "published_fee_detail",
        "secondary_published_detail",
        "treaty_dividend_wht_10pct_usd",
        "fx_spread_usd",
        "intermediary_receiving_fee_usd",
        "all_in_total_cost_usd",
        "prc_statutory_fine_30pct_usd",
        "prc_statutory_fine_100pct_usd",
        "source_urls",
        "flag_ids",
    ]
    csv_path = EXPORTS / "cost-ladder-920.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fields)
        writer.writeheader()
        for r in ladder_rows:
            out = {}
            for k in csv_fields:
                if k == "source_urls":
                    out[k] = " | ".join(SOURCES[sid]["url"] for sid in r["source_ids"])
                elif k == "flag_ids":
                    out[k] = " | ".join(r["flag_ids"])
                else:
                    v = r[k]
                    out[k] = "" if v is None else f"{v:.2f}" if isinstance(v, float) else v
            writer.writerow(out)


def main() -> None:
    ladder_rows = []
    for usd in TIERS:
        for m in METHODS:
            ladder_rows.append(compute_cost_row(m, usd))

    write_exports(ladder_rows)
    (HERE / "EXECUTIVE_SUMMARY.md").write_text(build_exec_summary_md(ladder_rows), encoding="utf-8")

    pages = {
        "index.html": build_index(ladder_rows),
        "questions.html": build_questions(),
        "costs.html": build_costs(ladder_rows),
        "methods.html": build_methods(),
        "penalties.html": build_penalties(),
        "taxes.html": build_taxes(),
        "audit.html": build_audit(),
        "flagged.html": build_flagged(),
        "sources.html": build_sources(),
    }
    for name, content in pages.items():
        (HERE / name).write_text(content, encoding="utf-8")

    print(
        f"OK: built {len(pages)} HTML pages, EXECUTIVE_SUMMARY.md, and {len(ladder_rows)} cost rows "
        f"({len(METHODS)} methods x {len(TIERS)} tiers; {len(SOURCES)} sources; {len(REPO_AUDIT)} audit rows; {len(FLAGS)} flags)."
    )


if __name__ == "__main__":
    main()
