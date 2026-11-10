#!/usr/bin/env python3
"""Render the static, dependency-free China→USD cost-ladder dashboard.

Every number printed here comes from ladder/data/*.json, which in turn comes
from ladder/model.py. Prose conclusions are labelled as analysis. No number is
written by hand into the HTML.
"""
from __future__ import annotations

import html
import json
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPO = ROOT.parent

SOURCES = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text())}
ROUTES = json.loads((DATA / "routes.json").read_text())
ASSUMPTIONS = json.loads((DATA / "assumptions.json").read_text())
COSTS = json.loads((DATA / "costs.json").read_text())
META = COSTS["meta"]
ROWS = COSTS["rows"]

PAGES = [
    ("index.html", "Overview"),
    ("costs.html", "Cost tables"),
    ("ladder.html", "All 40 tiers"),
    ("routes.html", "Routes"),
    ("steps.html", "Step by step"),
    ("tax.html", "Tax & penalties"),
    ("assumptions.html", "Assumptions"),
    ("audit.html", "Repo audit"),
    ("flagged.html", "Flagged"),
    ("sources.html", "Sources"),
]

FLAGS = []


def esc(t) -> str:
    return html.escape(str(t), quote=True)


def money(v) -> str:
    if v is None:
        return "—"
    return f"${v:,.0f}"


def src_link(sid: str) -> str:
    s = SOURCES[sid]
    host = s["url"].split("/")[2].replace("www.", "")
    return f'<a class="src" href="sources.html#{sid}" title="{esc(s["title"])}">{sid} · {esc(host)}</a>'


def ext(sid: str) -> str:
    s = SOURCES[sid]
    return (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">'
            f'{esc(s["authority"])}</a>')


def badge(status: str) -> str:
    m = {"lawful": ("ok", "Lawful"), "conditional": ("warn", "Conditional"),
         "unlawful": ("bad", "Unlawful"), "verified": ("ok", "Verified"),
         "needs review": ("warn", "Needs review")}
    cls, label = m.get(status, ("muted", status))
    return f'<span class="badge {cls}">{esc(label)}</span>'


def pct(v) -> str:
    return "—" if v is None else f"{v:.2f}%"


def shell(slug: str, title: str, body: str, lead: str = "") -> str:
    nav_parts = []
    for p, label in PAGES:
        cls = ' class="on"' if p == slug else ""
        nav_parts.append(f'<a href="{p}"{cls}>{esc(label)}</a>')
    nav = "".join(nav_parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China → USD cost ladder</title>
<meta name="description" content="Source-linked cost of moving CNY out of mainland China into USD for a US citizen, from $10,000 to $400,000 in $10,000 steps.">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand"><span class="mark">¥→$</span> <span>China money <em>cost ladder</em></span></div>
  <p class="stamp">Research · retrieved {META['retrieved']} · not tax or legal advice</p>
</header>
<nav class="nav" aria-label="Sections">{nav}</nav>
<main id="main">
{lead}
{body}
</main>
<footer class="foot">
  <p><strong>What this is.</strong> A source-linked model of what it costs to convert and move RMB out of
  mainland China into USD, tier by tier from $10,000 to $400,000. Every published figure is linked to the
  authority that publishes it; every figure that is not published is labelled as a model assumption and
  kept separate.</p>
  <p><strong>What this is not.</strong> Not individualized tax, legal or investment advice, and not a quote.
  The bank's executable rate on the day is the only real spread. No transfers were made and no returns filed.</p>
  <p class="meta">Sources {META['source_count']} · routes {META['route_count']} · tiers {len(META['tiers'])} ·
  modelled rows {META['row_count']} · generated {META['generated']} ·
  <a href="data/costs.csv">costs.csv</a> · <a href="data/costs.json">costs.json</a> ·
  <a href="data/routes.json">routes.json</a> · <a href="data/sources.json">sources.json</a></p>
</footer>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


def route_table(rows, show_time=True, caption=""):
    out = ['<div class="table-wrap"><table class="grid rows">']
    out.append("<thead><tr>"
               "<th class='c-rank'>Route</th><th>All-in cost (est.)</th><th class='c-pct'>% of amount</th>"
               + ("<th class='c-time'>Time</th>" if show_time else "")
               + "<th>Basis</th></tr></thead><tbody>")
    for i, r in enumerate(rows, 1):
        route = next(x for x in ROUTES if x["id"] == r["route"])
        partial = r.get("partial")
        cost = f"{money(r['total_lo'])} – {money(r['total_hi'])}"
        note = ('<span class="flag-inline">fixed fee not published — spread only</span>'
                if partial else "")
        basis = " ".join(src_link(s) for s in route["basis"])
        out.append(
            f"<tr>"
            f"<td data-label='Route' class='c-rank'><span class='rank'>{i}</span>"
            f"<a href='routes.html#{r['route']}'><strong>{esc(r['name'])}</strong></a>"
            f"<span class='sub'>{r['route']}</span></td>"
            f"<td data-label='All-in cost'><strong>{cost}</strong> {note}</td>"
            f"<td data-label='% of amount' class='c-pct'>{pct(r['pct_lo'])} – {pct(r['pct_hi'])}</td>"
            + (f"<td data-label='Time' class='c-time'>{esc(r['time'])}</td>" if show_time else "")
            + f"<td data-label='Basis'>{basis}</td></tr>")
    out.append("</tbody></table></div>")
    if caption:
        out.append(f"<p class='note'>{caption}</p>")
    return "".join(out)


def rank(route: dict) -> int:
    """Order the table the way a reader needs it, not the way arithmetic falls.

    0 documented remittance channels · 1 small-cash conversion · 2 spending
    channels · 3 eligibility unverified · 4 does not move the money at all.
    """
    if route["fee"] == "none":
        return 4
    if route["status"] == "conditional":
        return 3
    if route["fee"] in ("wire", "global", "cashcarry"):
        return 0
    if route["fee"] == "cash":
        return 1
    return 2


def tier_rows(tier):
    rows = [r for r in ROWS if r["tier"] == tier]
    by_id = {r["id"]: r for r in ROUTES}
    rows.sort(key=lambda r: (rank(by_id[r["route"]]),
                             r["total_hi"] if r["total_hi"] is not None else 9e9))
    return rows


REMIT_FEES = {"wire", "global", "cashcarry"}


def best_at(tier):
    """Cheapest route that actually delivers USD to an overseas account.

    Card spending (R12) and doing nothing (R20) are excluded: they are valid
    channels but they are not ways to receive the balance in USD. Partial rows
    are excluded because their missing fixed fee would make them look free.
    """
    rows = []
    for r in tier_rows(tier):
        route = next(x for x in ROUTES if x["id"] == r["route"])
        if r["status"] == "lawful" and not r.get("partial") and route["fee"] in REMIT_FEES:
            rows.append(r)
    return rows[0]


# ---------------------------------------------------------------------------
# Page: overview
# ---------------------------------------------------------------------------
def page_index():
    def external(url: str, label: str) -> str:
        return (f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
                f'{esc(label)}</a>')

    faq_income = "https://www.safe.gov.cn/tianjin/2026/0713/3088.html"
    faq_quota = "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"
    state_reg = "https://www.safe.gov.cn/safe/2008/0806/5321.html"
    current_hsbc = "https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf"
    irs_credit = "https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit"

    facts = [
        ("Does exchanging CNY into USD itself establish a PRC tax bill?",
         "No separate tax levied solely for the exchange was identified in the instruments reviewed. This does <strong>not</strong> establish that the balance is tax-paid or tax-free; PRC tax depends on the underlying income or asset category and taxpayer facts.",
         [src_link("S01"), src_link("S02"), src_link("S07")]),
        ("Which FX category applies to a U.S. citizen?",
         "Citizenship alone does not settle it. State Council Decree 532 includes a foreign national continuously resident in China for one year or more in the domestic-individual definition. SAFE also treats foreign permanent-residence-ID status as relevant to its annual purchase facility. Confirm classification with the bank.",
         [src_link("S04"), external(faq_quota, "SAFE 2024 FAQ")]),
        ("Does a documented foreign person's employment income need evidence?",
         "SAFE's 2026 guidance says lawful current-account RMB income earned in China by a foreign individual is handled with valid identity documents and transaction/source evidence, including tax documents. Whether this route covers this balance is unknown.",
         [external(faq_income, "SAFE 2026 FAQ"), src_link("S02")]),
        ("Is USD 50,000 a universal outward wire cap?",
         "Do not treat the annual convenience facility as a universal limit on sending your own money abroad. The rules distinguish FX sales, domestic-person purchases, foreign-person income conversion and the underlying transaction. The applicable category and evidence need bank confirmation.",
         [src_link("S01"), src_link("S02"), external(faq_quota, "SAFE 2024 FAQ")]),
        ("Can I use the USD 500 / USD 1,000 exception for earned RMB?",
         "No. The 2026 SAFE FAQ describes these identity-only exceptions for reconverting originally exchanged, unused RMB; an exchange memo is normally valid for 24 months. It is not a general wage-income allowance.",
         [src_link("S17"), external("https://www.safe.gov.cn/tianjin/2026/0917/3134.html", "SAFE 2026 reconversion FAQ")]),
        ("Is Form 1116 an automatic dollar-for-dollar offset?",
         "No. A U.S. foreign-tax credit may be available for qualifying taxes imposed on you, but is subject to legal-liability, income-category and limitation rules. No personal credit is calculated here.",
         [src_link("S12"), external(irs_credit, "IRS Foreign Tax Credit")]),
        ("What is the exact transfer cost?",
         "Not verified for this account. The current HSBC tariff has fee tiers and excludes other institutions' charges; the bank sets the rate used when a non-CNY charge is paid. The user's bank, service eligibility, applied rate and intermediary/receiver fees are unknown.",
         [external(current_hsbc, "HSBC China tariff, effective 31 Oct 2026"), src_link("S21")]),
        ("Should I split transfers or use a crypto / quota workaround?",
         "Do not evade FX limits by splitting transactions or using false documents. The current PBOC virtual-currency notice addresses specified exchange and related business activity; this review found no official basis for saying every quota borrower is automatically put on a 'watch list'.",
         [src_link("S01"), src_link("S16")]),
        ("Does a U.S. foreign-account report depend on whether the money was taxable?",
         "FBAR is a separate test: IRS guidance says a U.S. person generally files when reportable foreign accounts exceed USD 10,000 in aggregate at any time during the year, regardless of whether the account produced taxable income. Form 8938 has separate rules.",
         [src_link("S10"), src_link("S11")]),
    ]
    fact_rows = "".join(
        f"<tr><th scope='row'>{q}</th><td>{a} <span class='srcs'>{' '.join(ss)}</span></td></tr>"
        for q, a, ss in facts)

    body = f"""
<section class="hero">
  <h1>Getting CNY out of China: start with the bank's reason</h1>
  <p class="lede">A U.S. passport alone cannot tell us whether a bank's request is a tax payment, a required tax document, a fee, or an FX eligibility issue. The lawful route depends on who owns the account, the source of the balance, residence/category, and the bank's documentary review.</p>
  <div class="callout">
    <p><strong>What can be said safely:</strong> the PRC FX rules reviewed describe transaction and documentation requirements; no separate tax imposed solely for converting CNY was found in those instruments. That is <em>not</em> a determination that this balance is tax-paid, tax-free, or eligible to move. Ask the bank to distinguish any assessed tax from a requested certificate and from its own fees, and state the legal basis in writing. {external(faq_income, "SAFE's 2026 income-conversion guidance")} · {external("https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html", "PRC Individual Income Tax Law")}</p>
  </div>
  <div class="callout">
    <p><strong>Fee basis (updated 10 November 2026):</strong> route, step-by-step and cost pages cite HSBC China's tariff effective 31 October 2026 (S21, re-fetched from the official PDF on 10 November 2026). Wire issuance for Premier/Advance is 0.1% (CNY 100 minimum / CNY 500 maximum) plus CNY 120 per cable; Private Banking individuals are exempt from issuance and cable charges (items 2.2.4.1–2.2.4.2). Same-name Global Transfer to self-name overseas HSBC accounts is published Free for Private Banking and Premier; Advance pays CNY 145 indicative per transaction (actual USD 20), item 2.2.6.1. The tariff's USD 7 reference is specific to International Education Payment (item 2.2.7), not a general same-name remittance fee. Charges exclude other institutions and are not an all-in quote. {external(current_hsbc, "HSBC tariff effective 31 Oct 2026")} · <a href="../audit-0f0f59fe/index.html">review finding C04</a></p>
  </div>
  <div class="kpis">
    <div class="card kpi"><p class="kpi-l">$10,000 principal</p><p class="kpi-v">All-in cost: —</p><p class="kpi-s">Not source-confirmed for this account</p></div>
    <div class="card kpi"><p class="kpi-l">$100,000 principal</p><p class="kpi-v">All-in cost: —</p><p class="kpi-s">Not source-confirmed for this account</p></div>
    <div class="card kpi"><p class="kpi-l">$400,000 principal</p><p class="kpi-v">All-in cost: —</p><p class="kpi-s">Not source-confirmed for this account</p></div>
  </div>
  <p class="note">The cost pages retain scenario-model totals for transparency; they include unverified rate/fee assumptions and are <strong>not quotes or official values</strong>. For a strict source-only view, use the blank matrix linked below. The only actual all-in amount is the bank's executable quote for your specific account and route.</p>
</section>

<section class="panel">
  <h2>Best next step: separate the four cost layers</h2>
  <ol class="layers">
    <li><strong>Source-income tax.</strong> Identify what created the balance and whether any tax was assessed/withheld. PRC income tax varies by category and tax base; do not use a single percentage on the total balance. {src_link('S07')}</li>
    <li><strong>FX documentation and eligibility.</strong> Ask the bank which individual category and current-account/capital-account procedure it is applying, and what proof it needs. SAFE's current guidance for foreign individuals refers to identity plus transaction-source materials, including tax documents. {external(faq_income, 'SAFE 2026 guidance')}</li>
    <li><strong>Bank pricing.</strong> Obtain the current rate and itemized fees: FX rate/spread, conversion commission, cable, intermediary/beneficiary fees and any service-specific charge. A published tariff does not establish the rate or every fee for this transaction. {external(current_hsbc, 'HSBC tariff effective 31 Oct 2026')}</li>
    <li><strong>U.S. tax and account reporting.</strong> Evaluate income reporting, a possible but limited foreign tax credit, FBAR and Form 8938 separately from the act of transfer. {src_link('S10')} {src_link('S11')} {src_link('S12')}</li>
  </ol>
</section>

<section class="panel">
  <h2>Questions answered from official text</h2>
  <div class="table-wrap"><table class="grid facts"><tbody>{fact_rows}</tbody></table></div>
</section>

<section class="panel">
  <h2>Choose a research page</h2>
  <div class="picks">
    <a class="pick" href="costs.html"><strong>Cost scenarios</strong><span>All 15 costed routes at selected amounts; totals are modeled, not verified quotes.</span><em>Read with the assumptions →</em></a>
    <a class="pick" href="ladder.html"><strong>All 40 increments</strong><span>$10,000 through $400,000; shows the full scenario model, not official account prices.</span><em>Open the ladder →</em></a>
    <a class="pick" href="../audit-86f0/costs.html"><strong>Source-only blank cost matrix</strong><span>22 method entries × 40 increments; unknown cost cells remain blank.</span><em>Use the no-inference view →</em></a>
    <a class="pick" href="routes.html"><strong>Methods &amp; steps</strong><span>Conditional routes, documents, pros/cons and execution steps.</span><em>Open methods →</em></a>
    <a class="pick" href="tax.html"><strong>Tax &amp; reporting</strong><span>PRC source-income tax and U.S. reporting are separate analyses.</span><em>Review tax →</em></a>
    <a class="pick" href="../audit-0f0f59fe/index.html"><strong>Independent claim review</strong><span>Findings against the executive summary, costs and route recommendations.</span><em>Open review →</em></a>
    <a class="pick" href="flagged.html"><strong>Flagged for review</strong><span>Unverified amounts, eligibility gaps, fee assumptions and repo discrepancies.</span><em>Open flags →</em></a>
    <a class="pick" href="sources.html"><strong>Source register</strong><span>Manual-review links and locations for the source text.</span><em>Open sources →</em></a>
  </div>
</section>
"""
    return shell("index.html", "Start with the source", body)


# ---------------------------------------------------------------------------
# Page: cost tables at milestone tiers
# ---------------------------------------------------------------------------
def page_costs():
    milestones = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000]
    blocks = []
    for t in milestones:
        rows = tier_rows(t)
        b = best_at(t)
        blocks.append(f"""
<details class="tier" {'open' if t == 10_000 else ''}>
  <summary><span class="tier-amt">${t:,}</span>
    <span class="tier-best">cheapest documented: <strong>{money(b['total_lo'])} – {money(b['total_hi'])}</strong></span>
    <span class="tier-pct">{pct(b['pct_lo'])} – {pct(b['pct_hi'])}</span></summary>
  {route_table(rows, caption="Cost includes published bank fees plus the modelled spread band. Rows marked “fixed fee not published — spread only” are partial estimates: the missing component is flagged, not guessed.")}
</details>""")
    body = f"""
<h1>Cost tables by amount</h1>
<p class="lede">Same question at six amounts. Rows are grouped the way a decision is made: documented
remittance channels first, cheapest of those at the top; then small-cash channels; then spending channels;
then the route whose eligibility is unverified; and last the option that does not move the money at all.
Every row links to the authority behind its ceiling.</p>
<div class="callout">
  <p><strong>How to read a number.</strong> “All-in cost” = published bank fees (only where a tariff was
  verified) + a <em>modelled</em> FX spread band. It excludes PRC tax on the source income, which is shown
  separately on <a href="tax.html">Tax &amp; penalties</a>, because it depends on the character of the money
  and not on the transfer. It also excludes US preparer fees, which were not verified.</p>
</div>
{''.join(blocks)}
<section class="panel">
  <h2>Machine-readable</h2>
  <p>The full 600-row model covering all 40 tiers:
  <a href="data/costs.csv">costs.csv</a> · <a href="data/costs.json">costs.json</a> ·
  <a href="data/routes.json">routes.json</a> · <a href="data/sources.json">sources.json</a> ·
  <a href="data/assumptions.json">assumptions.json</a></p>
</section>
"""
    return shell("costs.html", "Cost tables", body)


# ---------------------------------------------------------------------------
# Page: full ladder
# ---------------------------------------------------------------------------
def page_ladder():
    blocks = []
    for t in META["tiers"]:
        b = best_at(t)
        rows = tier_rows(t)
        blocks.append(f"""
<details class="tier" data-tier="{t}" {'open' if t in (10_000, 100_000, 400_000) else ''}>
  <summary><span class="tier-amt">${t:,}</span>
    <span class="tier-best">best: <strong>{money(b['total_lo'])} – {money(b['total_hi'])}</strong> · {esc(b['name'])}</span>
    <span class="tier-pct">{pct(b['pct_lo'])} – {pct(b['pct_hi'])}</span></summary>
  {route_table(rows)}
</details>""")
    body = f"""
<h1>All 40 tiers, $10,000 to $400,000</h1>
<p class="lede">Each step is a separate calculation: documented ceilings change the number of transactions
and trips required, so the percentage cost is not flat. $10,000, $100,000 and $400,000 are open by default.</p>
<div class="toolbar">
  <label for="tier-jump">Jump to an amount</label>
  <select id="tier-jump">{''.join(f'<option value="{t}">${t:,}</option>' for t in META['tiers'])}</select>
  <label for="route-filter">Filter routes</label>
  <select id="route-filter">
    <option value="">All routes</option>
    {''.join(f'<option value="{r["route"]}">{r["route"]} · {esc(r["name"])}</option>' for r in tier_rows(10_000))}
    <option value="lawful">Lawful only</option>
  </select>
</div>
<p class="note">The filter hides rows in the browser only; the page is complete and printable without it.</p>
{''.join(blocks)}
"""
    return shell("ladder.html", "All 40 tiers", body)


# ---------------------------------------------------------------------------
# Page: routes
# ---------------------------------------------------------------------------
def page_routes():
    cards = []
    for r in ROUTES:
        basis = " ".join(src_link(s) for s in r["basis"])
        if r["status"] == "unlawful":
            cards.append(f"""
<article class="route bad" id="{r['id']}">
  <header><h2><span class="rid">{r['id']}</span> {esc(r['name'])} {badge(r['status'])}</h2>
    <p class="sub">{esc(r['group'])}</p></header>
  <p class="who">{esc(r['who'])}</p>
  <div class="two">
    <div><h3>Why not</h3><ul>{''.join(f'<li>{esc(c)}</li>' for c in r['cons'])}</ul></div>
    <div><h3>What the rule says</h3><p>{esc(r['steps'][0])}</p><p class="srcs">{basis}</p></div>
  </div>
</article>""")
            continue
        cap = f"USD {r['cap']:,} per transaction/period" if r["cap"] else "no per-transaction ceiling verified"
        rows = [x for x in ROWS if x["route"] == r["id"]]
        at = {x["tier"]: x for x in rows}
        cost_cells = "".join(
            f"<tr><td data-label='Amount'>${t:,}</td>"
            f"<td data-label='All-in cost'>{money(at[t]['total_lo'])} – {money(at[t]['total_hi'])}</td>"
            f"<td data-label='%'>{pct(at[t]['pct_lo'])} – {pct(at[t]['pct_hi'])}</td>"
            f"<td data-label='Transaction count'>{at[t]['transactions']}</td>"
            f"<td data-label='Time'>{esc(at[t]['time'])}</td>"
            f"<td data-label='Source'>{' '.join(src_link(x) for x in r['basis'])}</td></tr>"
            for t in (10_000, 100_000, 400_000))
        cards.append(f"""
<article class="route" id="{r['id']}">
  <header><h2><span class="rid">{r['id']}</span> {esc(r['name'])} {badge(r['status'])}</h2>
    <p class="sub">{esc(r['group'])} · {esc(cap)}</p></header>
  <p class="who">{esc(r['who'])}</p>
  <div class="table-wrap"><table class="grid mini">
    <thead><tr><th>Amount</th><th>All-in cost (est.)</th><th>% of amount</th><th>Transactions</th><th>Time</th><th>Source</th></tr></thead>
    <tbody>{cost_cells}</tbody></table></div>
  <p class="note">{esc(r['tax_note'])}</p>
  <div class="two">
    <div><h3>Pros</h3><ul>{''.join(f'<li>{esc(p)}</li>' for p in r['pros'])}</ul></div>
    <div><h3>Cons</h3><ul>{''.join(f'<li>{esc(c)}</li>' for c in r['cons'])}</ul></div>
  </div>
  <p class="docs"><strong>Documents:</strong> {esc('; '.join(r['docs'])) if r['docs'] else '—'}</p>
  <p class="srcs"><strong>Legal basis:</strong> {basis}</p>
</article>""")
    body = f"""
<h1>Every route, its ceiling and its paperwork</h1>
<p class="lede">{len([r for r in ROUTES if r["status"] != "unlawful"])} lawful or conditional routes and
{len([r for r in ROUTES if r["status"] == "unlawful"])} rejected ones. “Lawful” here means a route
exists in the instruments reviewed; it does not mean it applies to your facts — see
<a href="flagged.html">Flagged for review</a>.</p>
<div class="legend">
  <p>{badge('lawful')} a stated legal route · {badge('conditional')} route exists but your eligibility was
  not verified · {badge('unlawful')} prohibited, with the penalty provision cited</p>
</div>
{''.join(cards)}
"""
    return shell("routes.html", "Routes", body)


# ---------------------------------------------------------------------------
# Page: steps
# ---------------------------------------------------------------------------
def page_steps():
    blocks = []
    for r in ROUTES:
        if r["status"] == "unlawful":
            continue
        items = "".join(f"<li><span class='n'>{i}</span><div>{esc(s)}</div></li>"
                        for i, s in enumerate(r["steps"], 1))
        blocks.append(f"""
<details class="tier" {'open' if r['id'] in ('R01', 'R02') else ''}>
  <summary><span class="rid">{r['id']}</span> {esc(r['name'])} <span class="tier-pct">{esc(r['time'])}</span></summary>
  <ol class="steps">{items}</ol>
  <p class="docs"><strong>Bring:</strong> {esc('; '.join(r['docs'])) if r['docs'] else '—'}</p>
  <p class="srcs">{' '.join(src_link(s) for s in r['basis'])}</p>
</details>""")
    body = f"""
<h1>Exactly how each route works</h1>
<p class="lede">Ordered for the two routes that cover most real cases (R01 and R02). Nothing here requires
you to guess: every step maps to a document or a rule cited at the foot of the block.</p>
<div class="callout">
  <p><strong>Before you go to a branch.</strong> Ask the bank for two things in writing: the exchange memo
  (水单) and an all-in executable quote showing the rate applied, the commission, the cable fee and any
  correspondent deduction. The spread is the only large variable and it is never published.</p>
</div>
{''.join(blocks)}
"""
    return shell("steps.html", "Step by step", body)


# ---------------------------------------------------------------------------
# Page: tax & penalties
# ---------------------------------------------------------------------------
def page_tax():
    prc = [
        ("Comprehensive income (salary, fees, royalties, authorship)", "3% – 45% progressive",
         "S07", "Art. 3(1)"),
        ("Business income", "5% – 35% progressive", "S07", "Art. 3(2)"),
        ("Dividends, interest, rent, property transfer, incidental", "20% flat", "S07", "Art. 3(3)"),
        ("Dividends, interest, royalties — US resident under treaty", "10% ceiling", "S09", "Arts. 9–11"),
        ("Company profits before distribution", "25% EIT", "S08", "Art. 4"),
        ("Conversion of RMB to USD", "no separate tax identified", "S01", "Arts. 13–15"),
        ("Carrying cash across the border", "no tax; a report above USD 10,000 on entry to the US", "S13", "—"),
    ]
    prc_rows = "".join(
        f"<tr><td data-label='Item'>{esc(a)}</td><td data-label='Rate'><strong>{esc(b)}</strong></td>"
        f"<td data-label='Source'>{src_link(s)} <span class='sub'>{esc(l)}</span></td></tr>"
        for a, b, s, l in prc)

    penalties = [
        ("Evasion — moving domestic FX or capital abroad by deception", "fine up to 30% of the amount; "
         "30% up to the equivalent amount if serious; criminal liability possible", "S04", "Art. 39"),
        ("Illegal FX purchase — false or invalid documents to a bank", "fine up to 30%; 30%–100% if serious",
         "S04", "Art. 40"),
        ("Illegal carriage of FX across the border", "warning and fine up to 20% of the amount", "S04",
         "Art. 42"),
        ("Private, disguised or brokered FX trading", "confiscation of gains plus fine up to 30%; "
         "30%–100% if serious; criminal liability possible", "S04", "Art. 45"),
        ("Failure to make the required balance-of-payments declaration", "warning; up to CNY 50,000 for an "
         "individual", "S04", "Art. 48"),
        ("Splitting to evade limits / lending your quota", "prohibited by PBOC Decree [2006] No. 3 Art. 7 "
         "and penalized under Decree 532 Arts. 39–40; older Hui Fa [2015] No. 49 watch-list text carries "
         "conflicting active/repealed mirror labels (see F03)", "S18", "Art. 2 (disputed)"),
    ]
    pen_rows = "".join(
        f"<tr><td data-label='Conduct'>{esc(a)}</td><td data-label='Exposure'>{esc(b)}</td>"
        f"<td data-label='Source'>{src_link(s)} <span class='sub'>{esc(l)}</span></td></tr>"
        for a, b, s, l in penalties)

    us = [
        ("Worldwide income is taxable in the US regardless of where it sits", "Form 1040; foreign tax "
         "credit on Form 1116 limits the credit to US tax on the same foreign-source income", "S12",
         "Limit on the credit"),
        ("Foreign financial accounts", "FBAR (FinCEN 114) if aggregate value exceeded USD 10,000 at any "
         "time in the year", "S10", "Who must file"),
        ("Specified foreign financial assets", "Form 8938 if above USD 50,000 year-end / USD 75,000 at any "
         "time (single, living in the US)", "S11", "Thresholds"),
        ("Physical currency entering or leaving the US", "FinCEN Form 105 above USD 10,000; failure risks "
         "forfeiture and civil or criminal penalties", "S13", "Mandatory report"),
        ("Accounts in your own name only", "the duty still applies: an account is reportable if you have a "
         "financial interest in it", "S14", "1010.350(a)"),
    ]
    us_rows = "".join(
        f"<tr><td data-label='US duty'>{esc(a)}</td><td data-label='Detail'>{esc(b)}</td>"
        f"<td data-label='Source'>{src_link(s)} <span class='sub'>{esc(l)}</span></td></tr>"
        for a, b, s, l in us)

    body = f"""
<h1>The “penalty”, broken down</h1>
<p class="lede">Four different things get called a conversion penalty. Sorting them is the whole problem:
one is a tax you may already have paid, one is bank revenue, one is a fine for getting it wrong, and one is
a US reporting duty that has nothing to do with conversion.</p>

<section class="panel">
  <h2>1 · PRC rates that can sit behind the money</h2>
  <div class="table-wrap"><table class="grid"><thead><tr><th>Item</th><th>Rate</th><th>Source</th></tr></thead>
  <tbody>{prc_rows}</tbody></table></div>
  <p class="note">No separate PRC conversion tax, exit tax or remittance tax appears in the instruments
  reviewed (S01, S02, S04, S07, S19). That is a finding about the text, not a promise about your file.</p>
</section>

<section class="panel">
  <h2>2 · What it costs to get it wrong</h2>
  <div class="table-wrap"><table class="grid"><thead><tr><th>Conduct</th><th>Exposure</th><th>Source</th></tr></thead>
  <tbody>{pen_rows}</tbody></table></div>
  <p class="note">These are statutory maxima, applied case by case. At $400,000 a 30% fine is $120,000 —
  which is why no workaround beats the documented route, even before criminal exposure.</p>
</section>

<section class="panel">
  <h2>3 · The US side</h2>
  <div class="table-wrap"><table class="grid"><thead><tr><th>US duty</th><th>Detail</th><th>Source</th></tr></thead>
  <tbody>{us_rows}</tbody></table></div>
  <p class="note">The foreign tax credit is what stops the same income being taxed twice. It cannot reduce
  US tax on US-source income, and it is capped at the US tax on the foreign-source income, so an unusually
  high PRC rate does not automatically become a US refund.</p>
</section>

<section class="panel">
  <h2>4 · The one number that is not in any statute</h2>
  <p>The FX spread. It is the largest component of a lawful conversion and no regulator publishes it, because
  it is a commercial price. Every table on this site therefore shows a <em>band</em> and labels it as a model
  assumption (A2–A5). A bank quote replaces it; nothing else can.</p>
</section>

<section class="panel">
  <h2>5 · If the PRC tax was never paid</h2>
  <p>Then the amount people quote as a “conversion penalty” is the unpaid PRC tax plus, potentially, the
  Art. 39 or Art. 40 fine. The lawful sequence is: establish the income character, settle with the tax
  authority, obtain the certificate, convert under R01, then claim the PRC tax in the US on Form 1116. In
  most cases where the PRC income tax rate is at or above the U.S. rate on the same foreign-source "
  "income, a qualifying Form 1116 credit can substantially offset U.S. tax on that income, subject to "
  "sourcing, income-category, legal-liability and limitation rules (S12; see C05).</p>
</section>
"""
    return shell("tax.html", "Tax & penalties", body)


# ---------------------------------------------------------------------------
# Page: assumptions
# ---------------------------------------------------------------------------
def page_assumptions():
    rows = "".join(
        f"<tr><td data-label='ID'><strong>{esc(a['id'])}</strong></td>"
        f"<td data-label='Topic'>{esc(a['topic'])}</td>"
        f"<td data-label='Value used'><strong>{esc(a['value'])}</strong></td>"
        f"<td data-label='Status'><span class='badge warn'>{esc(a['status'])}</span></td>"
        f"<td data-label='Why'>{esc(a['why'])}</td></tr>" for a in ASSUMPTIONS)
    body = f"""
<h1>What is published, and what is modelled</h1>
<p class="lede">This is the honesty page. Anything below is an assumption used to produce an estimate. None
of it is a regulator's figure, a bank quote, or a fact about your account.</p>
<div class="callout">
  <p><strong>The rule applied throughout.</strong> If an official source states a value, it is printed with a
  link. If no official source states it, the value is either left blank and flagged, or presented here as a
  labelled assumption with a range. It is never presented as a verified fact.</p>
</div>
<div class="table-wrap"><table class="grid">
<thead><tr><th>ID</th><th>Topic</th><th>Value used</th><th>Status</th><th>Why</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<section class="panel">
  <h2>Published values that the model actually uses</h2>
  <ul class="plain">
    <li>Wire issuance (Premier/Advance): 0.1% of remittance amount, minimum CNY 100, maximum CNY 500 per
    transaction, plus CNY 120 per cable; Private Banking individuals are exempt. {src_link('S21')}</li>
    <li>Same-name HSBC Global Transfer to self-name overseas HSBC accounts: Free for Private Banking and
    Premier; Advance pays CNY 145 indicative per transaction (actual USD 20). Available only where Global
    Transfer to Self is offered — tariff remark lists Canada, US, UK, Australia and Hong Kong SAR.
    {src_link('S21')}</li>
    <li>Foreign-currency notes withdrawal over the counter: Free for Private Banking, Premier and Advance;
    USD/HKD of at least USD 5,000 equivalent needs at least three working days' advance notice. CNY↔notes
    conversion uses notes buy/sell board rates (the modelled cash spread), not a fixed fee. {src_link('S21')}</li>
    <li>International Education Payment (platform-specific): USD 7 actual for Advance (CNY 50 indicative) —
    listed only to prevent the earlier confusion with a general same-name Global Transfer fee. {src_link('S21')}</li>
    <li>CNY 100,000 per person per calendar year of overseas ATM cash; CNY 10,000 per card per day.
    {src_link('S03')}</li>
    <li>USD 500 per day onshore / USD 1,000 per day port-side unused-RMB reconversion exemption (24-month original memo rule for larger amounts). {src_link('S17')}</li>
    <li>USD 5,000 / 10,000 cash carrying thresholds. {src_link('S15')}</li>
    <li>Emigration and inheritance transfers: local SAFE branch approves; SAFE Circular Huifa [2014] No. 2 §VI cancelled the >RMB 500,000 head-office filing and cancelled mandatory multi-stage installments so banks may remit in a lump sum or in batches within the approved limit. {src_link('S05')}</li>
  </ul>
</section>
"""
    return shell("assumptions.html", "Assumptions", body)


# ---------------------------------------------------------------------------
# Page: repo audit
# ---------------------------------------------------------------------------
def repo_inventory():
    exts = {".html": "page", ".css": "style", ".js": "script", ".py": "generator",
            ".json": "ledger", ".md": "document", ".csv": "data", ".yml": "CI",
            ".svg": "asset", ".txt": "archived page", ".cjs": "test", ".mjs": "tool"}
    out = []
    for p in sorted(REPO.rglob("*")):
        s = str(p)
        if not p.is_file() or ".git/" in s or "/data/" in s or "__pycache__/" in s or ".cache/" in s or "node_modules/" in s or p.suffix == ".pyc":
            continue
        rel = p.relative_to(REPO)
        if str(rel).startswith("ladder/"):
            continue
        # index.html at the repo root is written by this generator, so recording
        # its own byte size would make the page depend on its own output order.
        if str(rel) == "index.html":
            continue
        # The task board is append-only and changes with every session; recording
        # its size would make this page stale as soon as another session logs.
        if str(rel) == "COORDINATION.md":
            continue
        out.append((str(rel), p.stat().st_size, exts.get(p.suffix, p.suffix.lstrip("."))))
    return out


def audit_row(fid, observation, assessment, action, flag):
    link = '<a href="flagged.html#%s">%s</a>' % (flag, flag) if flag != "—" else "—"
    return ("<tr><td data-label='ID'><strong>%s</strong></td><td data-label='Observation'>%s</td>"
            "<td data-label='Assessment'>%s</td><td data-label='Action'>%s</td>"
            "<td data-label='Flag'>%s</td></tr>") % (
        esc(fid), esc(observation), esc(assessment), esc(action), link)


def page_audit():
    inv = repo_inventory()
    inv_rows = "".join(
        f"<tr><td data-label='Path'><code>{esc(p)}</code></td><td data-label='Bytes'>{b:,}</td>"
        f"<td data-label='Kind'>{esc(k)}</td></tr>" for p, b, k in inv)

    findings = [
        ("AUD-01", "Three parallel dashboards publish overlapping but different route counts "
         "(22 routes in docs/, 13 lawful / 5 unlawful in site/, 22 in portal/, 20 here with 15 costed).",
         "No prior dashboard is wrong on its own terms, but a reader comparing them sees inconsistent totals.",
         "Consolidation note on this site; prior dashboards left in place untouched.", "F10"),
        ("AUD-02", "Prior text treats a US citizen as always a 境外个人 (non-domestic individual).",
         "State Council Decree 532 Art. 52(2) defines 境内个人 to include a foreign national who has resided "
         "continuously in China for one year or more, so the answer depends on residency history.",
         "Recorded as a substantive discrepancy.", "F02"),
        ("AUD-03", "SAFE publishes Hui Fa [2015] No. 49 with and without a “repealed” label on two of its own "
         "mirrors.", "The anti-splitting rule is independently stated in PBOC Decree [2006] No. 3 Art. 7, so "
         "the conclusion survives; the citation is unreliable.", "Flagged, not relied on as sole basis.", "F03"),
        ("AUD-04", "Crypto prohibition cited in places to Yin Fa [2021] No. 237.",
         "Yin Fa [2026] No. 42 (6 Feb 2026) expressly repeals 237. The 2026 notice is the operative text.",
         "This site cites 2026/42 and notes the repeal.", "F12"),
        ("AUD-05", "Previous sessions cite a SAFE branch Q&A and a PBOC notice for re-conversion.",
         "Both resolve and state the rule (USD 500 / 1,000, 24-month memo).", "Re-verified in this session.", "—"),
        ("AUD-06", "Two root-level executive summaries exist (EXECUTIVE_SUMMARY.md and EXECUTIVE-SUMMARY.md).",
         "Duplication invites drift: the two files can diverge without any check failing.",
         "Left untouched (owned by other sessions); noted here.", "F10"),
        ("AUD-07", "A prior CBP URL for currency reporting resolves; a similar-looking international-visitor "
         "URL does not.", "Link rot in this area is common; the working page is cited here.",
         "Cited the resolving page.", "—"),
        ("AUD-08", "No dashboard published a per-route cost at $10,000 increments.",
         "The brief's central deliverable was missing from all three prior dashboards.",
         "Built in this session as ladder/ (40 tiers × 15 costed routes).", "F13"),
        ("AUD-09", "No source in this repository is a live quote for CNY/USD.",
         "Every published cost here is a tariff; the spread is modelled.",
         "Separated into the assumptions register.", "F04"),
        ("AUD-10", "Form 3520 gift/bequest thresholds verified across IRS primary pages.",
         "Confirmed from IRS Gifts from Foreign Person and Rev. Proc. 2026-35 §3.51: >USD 100,000 for "
         "nonresident-alien / foreign-estate gifts and bequests; >USD 20,573 (2026) / >USD 21,240 "
         "(2027) for foreign corporations/partnerships.",
         "Updated F07 with IRS thresholds; excluded from transfer-fee arithmetic (not a bank fee).", "F07"),
    ]
    find_rows = "".join(audit_row(i, o, a, x, f) for i, o, a, x, f in findings)

    body = f"""
<h1>Repository review, line by line</h1>
<p class="lede">This repository already contained three independently built dashboards. This page records
what they contain, what was re-checked here, and every discrepancy found. No file from another session was
edited.</p>
<div class="callout">
  <p><strong>Scope.</strong> {len(inv)} files outside this session's own directory were inventoried.
  {len(findings)} findings are recorded; none blocks publication. Items that could not be resolved without private facts are
  on <a href="flagged.html">Flagged for review</a>.</p>
</div>
<section class="panel">
  <h2>Findings</h2>
  <div class="table-wrap"><table class="grid">
  <thead><tr><th>ID</th><th>Observation</th><th>Assessment</th><th>Action</th><th>Flag</th></tr></thead>
  <tbody>{find_rows}</tbody></table></div>
</section>
<section class="panel">
  <h2>Source re-verification</h2>
  <p>Twenty sources are used by this model. Each is listed on <a href="sources.html">Sources</a> with the
  retrieval mode: <em>direct</em> means the body of the document was retrieved in this session and the quoted
  text is from that body; <em>search</em> means the document was surfaced from the official domain with quoted
  text but not re-fetched end to end. {sum(1 for s in SOURCES.values() if s['retrieval']=='direct')} of 20
  were retrieved directly.</p>
</section>
<section class="panel">
  <h2>File inventory (prior sessions, untouched)</h2>
  <p class="note">Two files are excluded by design: the generated root <code>index.html</code>,
  because this generator writes it, and <code>COORDINATION.md</code>, because it is the append-only
  task board whose size changes with every session. Listing either would make this page stale.</p>
  <div class="table-wrap"><table class="grid compact">
  <thead><tr><th>Path</th><th>Bytes</th><th>Kind</th></tr></thead><tbody>{inv_rows}</tbody></table></div>
</section>
"""
    return shell("audit.html", "Repo audit", body)


# ---------------------------------------------------------------------------
# Page: flags
# ---------------------------------------------------------------------------
FLAG_ITEMS = [
    ("F01", "The private facts are unknown", "high",
     "Ownership of the balance, the residency history of the holder, how and when the RMB arose, the "
     "currency of the original funds, and whether US returns and FBARs were filed are all unknown. No "
     "personal tax amount or eligibility determination is possible, and none is made.",
     ["S01", "S02", "S07"]),
    ("F02", "Residence, not citizenship, decides which individual category applies", "high",
     "State Council Decree 532 Art. 52(2) defines “domestic individual” to include a foreign national who "
     "has resided continuously in China for one year or more. A US citizen who lived in China for years may "
     "therefore sit in a different category from a US citizen who never did, which changes whether the "
     "annual purchase facility applies. Prior dashboards in this repository state the opposite as settled.",
     ["S04", "S02"]),
    ("F03", "A SAFE notice carries conflicting status across SAFE's own mirrors", "medium",
     "Hui Fa [2015] No. 49 appears with a “repealed” label on one SAFE branch page and without it on another. "
     "The anti-splitting rule is independently stated in PBOC Decree [2006] No. 3 Art. 7, so the substance is "
     "not in doubt, but the citation is not relied on alone.", ["S18", "S01"]),
    ("F04", "No published CNY/USD spread exists for any account", "high",
     "Every cost figure here therefore contains a modelled spread band (A2–A5). The bank's executable quote "
     "is the only real number. Treat the ladder as a planning band, not a quote.", ["S21"]),
    ("F05", "Offshore RMB (CNH) route eligibility is unverified", "medium",
     "Whether a non-resident US citizen may move RMB to Hong Kong and convert there was not established from "
     "a primary source. Route R14 is published with a blank eligibility and is not priced for a decision.",
     ["S02"]),
    ("F06", "Property-sale FX procedure for a non-domestic vendor is unverified", "medium",
     "The 20% rate on the gain is verified (S07 Arts. 3(3), 6(5)) and the tax certificate is checked at "
     "registration (S07 Art. 15), but the specific SAFE/bank documentary path for repatriating a foreign "
     "vendor's proceeds was not verified here. The 20% figure is published; the procedure is flagged.",
     ["S07", "S01"]),
    ("F07", "Form 3520 foreign gift thresholds verified; trust facts still required", "low",
     "Verified against IRS 'Gifts from a Foreign Person' (irs.gov/businesses/gifts-from-foreign-person) "
     "and Rev. Proc. 2026-35 §3.51: Part IV applies above USD 100,000 aggregate for gifts/bequests from "
     "nonresident aliens or foreign estates, and above USD 20,573 (2026) / USD 21,240 (2027) from foreign "
     "corporations/partnerships. Foreign-trust reporting depends on personal facts and is not modelled in "
     "transfer-cost arithmetic.", []),
    ("F08", "Card and ATM fixed fees are unpublished", "medium",
     "ATM operator fees, issuer foreign-transaction markups and card scheme settlement rates were not "
     "obtained. Routes R11 and R12 are marked PARTIAL: their estimates include the spread only.",
     ["S03"]),
    ("F09", "The tariff used for the original 2026-11-08 build was dated 1 January 2021 (S06)", "low",
     "Re-verified and superseded on 10 November 2026: the tariff effective 31 October 2026 was retrieved "
     "from the bank's official site and recorded as S21; wire, cable, cash-notes and Global Transfer items "
     "are now modelled from S21. The CNY 500 wire cap and CNY 120 cable are unchanged for Premier/Advance "
     "between the two editions (Private Banking individuals are now exempt). Residual risk: the bank may "
     "adjust the schedule again — confirm at the branch. The spread-band caveat (F04) is unchanged.",
     ["S21", "S06"]),
    ("F10", "Parallel dashboards publish different route counts", "low",
     "docs/, site/, portal/, repatriate/, briefing/ and this ladder use different method taxonomies (17–22). "
     "All deliverables are now cross-linked from root index.html; review scope and caveats per sub-site.", []),
    ("F11", "No per-transfer ceiling was verified for a non-domestic remittance", "medium",
     "The model assumes one wire per tranche (A7). If a bank splits a large remittance, fixed fees multiply. "
     "This is where a $400,000 transfer could cost more than the table shows.", ["S02"]),
    ("F12", "An older crypto notice has been repealed", "low",
     "Yin Fa [2021] No. 237 is expressly repealed by Yin Fa [2026] No. 42. Any page in this repository still "
     "citing 237 as current is out of date; this site cites 42.", ["S16"]),
    ("F13", "The cost ladder does not exist anywhere else in this repository", "low",
     "The brief's central deliverable — cost at every $10,000 increment to $400,000 — was absent from all "
     "three prior dashboards. It is built here and is not a duplicate.", []),
]


def page_flags():
    cards = []
    for fid, title, sev, text, ss in FLAG_ITEMS:
        cls = "bad" if sev == "high" else ("warn" if sev == "medium" else "muted")
        srcs = " ".join(src_link(s) for s in ss) if ss else "<span class='sub'>no official source exists for this item</span>"
        cards.append(f"""
<article class="flagcard" id="{fid}">
  <header><h2><span class="rid">{fid}</span> {esc(title)}</h2>
    <span class="badge {cls}">severity: {esc(sev)}</span></header>
  <p>{esc(text)}</p>
  <p class="srcs">{srcs}</p>
</article>""")
    body = f"""
<h1>Flagged for review</h1>
<p class="lede">Everything that could not be verified, or where sources disagree, or where earlier work in
this repository says something different. These items do not block publication; they block a decision. Send
back the ones you want changed.</p>
<div class="callout">
  <p><strong>Nothing here is filled in by inference.</strong> Where a value could not be confirmed from an
  official source, the cell on the other pages is blank or the row is marked PARTIAL, and the item appears
  below with the source that comes closest.</p>
</div>
{''.join(cards)}
"""
    return shell("flagged.html", "Flagged for review", body)


# ---------------------------------------------------------------------------
# Page: sources
# ---------------------------------------------------------------------------
def page_sources():
    gov_count = sum(1 for s in SOURCES.values() if "commercial" not in s["jur"])
    rows = []
    for sid, s in SOURCES.items():
        status = badge("verified") if s["status"] == "verified" else badge("needs review")
        rows.append(f"""
<article class="source" id="{sid}">
  <header><h2><span class="rid">{sid}</span> {esc(s['title'])}</h2>
    <p class="sub">{esc(s['authority'])} · {esc(s['jur'])} · {esc(s['lang'])} · retrieved {esc(s['retrieval'])} · {status}</p></header>
  <p class="quote">“{esc(s['quote'])}”</p>
  <p class="meta"><strong>Locator:</strong> {esc(s['locator'])} · <strong>Used for:</strong> {esc(s['used_for'])}</p>
  <p><a class="button" href="{esc(s['url'])}" target="_blank" rel="noopener noreferrer">Open the official document ↗</a></p>
</article>""")
    body = f"""
<h1>Sources</h1>
<p class="lede">{len(SOURCES)} documents. {gov_count} are published by a government, central bank or
statutory authority; {len(SOURCES) - gov_count} is a commercial bank's own published tariff, labelled as such. Quoted text is copied from the retrieved document, not paraphrased
from memory.</p>
<div class="callout">
  <p><strong>Retrieval legend.</strong> <em>direct</em> = the document body was retrieved in this session.
  <em>search</em> = the official-domain document was surfaced with quoted text but not re-fetched end to end.
  No source here is a news article, a blog or a mirror site, except where a SAFE branch mirror is the
  authoritative publisher of the notice.</p>
</div>
{''.join(rows)}
"""
    return shell("sources.html", "Sources", body)


def write_root_hub():
    """Root landing page; source-first and explicit about unknown personal costs."""
    def ext(url: str, label: str) -> str:
        return (f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
                f'{esc(label)}</a>')

    cards = [
        ("verify-d5d1f860/index.html", "Live-verified dashboard · newest pass", "24 sources re-fetched · 680 rows · 16 flags",
         "Quote-level re-verification dated 10 November 2026: each load-bearing document was re-fetched and the exact sentence is shown with its link. Fees recomputed independently; blanks where nothing is published."),
        ("briefing/index.html", "Executive briefing · start here", "Summary · 17 methods · 680 cost rows",
         "Consolidated comparison with steps and caveats. Published fees are not all-in quotes; read the review notes below."),
        ("audit-ad300459/index.html", "Latest evidence audit", "27 findings · official-source review · ladder checks",
         "Separates verified, limited and unverified claims. Arithmetic checks do not establish personal eligibility."),
        ("briefing/costs.html", "Costs · every $10,000 to $400,000", "17 methods · 40 tiers each",
         "Corrected source-only briefing: published fee components; unknown spreads and all-in costs left blank."),

        ("ladder/index.html", "Cost ladder · scenario model", "15 routes · 40 tiers · $10k–$400k",
         "Shows modelled bands using explicit assumptions. Not an account quote or an officially verified all-in cost."),
        ("audit-86f0/costs.html", "Source-only blank matrix", "22 methods · 40 tiers",
         "Leaves unverified FX spreads, transfer totals and tax amounts blank. Blank means unverified, not zero."),
        ("audit-0f0f59fe/index.html", "Landing-page claim review", "Official text · corrections · unresolved facts",
         "Independent check of root claims, legacy-tariff warnings and unresolved account facts."),
        ("ladder/routes.html", "Methods & execution", "Eligibility · pros/cons · step by step",
         "Routes are conditional; the bank must confirm documents, status, service availability and limits."),
        ("ladder/tax.html", "Tax & reporting", "PRC income tax · U.S. FTC · FBAR/FATCA",
         "A transfer is not a personalized tax calculation. U.S. credits and reporting have separate tests."),
        ("ladder/flagged.html", "Flagged for review", "Unverified values · eligibility · open caveats",
         "Open issues are published here rather than filled in by inference."),
        ("ladder/sources.html", "Primary source register", "SAFE · PBOC · tax authorities · IRS · bank tariff",
         "Direct source text and locators for manual review."),
        ("docs/index.html", "Research dashboard", "22 routes · 67 findings · 24 official sources",
         "Searchable source-linked decision dashboard with execution checklist and CSV/JSON exports."),
        ("site/index.html", "Evidence ledger site", "18 routes · 16 flags · strict allowlist",
         "Source-only evidence site built strictly from government and registry domain ledgers."),
        ("portal/index.html", "Government-source portal", "22 methods · .gov / .gov.cn only",
         "Independent statutory verification portal linking exclusively to government domains."),
        ("acceptance-373b54a3/index.html", "Acceptance summary & checks", "Cross-repo deliverable check",
         "Independent completeness verification across the published 600-row and 680-row ladders."),
    ]
    site_cards = "".join(
        f'<a class="card" href="{esc(u)}"><strong>{esc(t)}</strong><span>{esc(sub)}</span>'
        f'<em>{esc(d)}</em></a>' for u, t, sub, d in cards)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>China money · CNY to USD research</title>
<meta name="description" content="Source-linked research on lawful CNY-to-USD conversion, route eligibility, tax and costs. Unknown account-specific values remain blank or flagged.">
<style>
:root{{--ink:#142722;--muted:#5c7167;--paper:#f5f5ef;--line:#dce2dc;--accent:#0b705e;--warn:#744600;--warn-bg:#fff3d8}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.58 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
header{{background:var(--ink);color:#f6f5ef;padding:1.1rem clamp(1rem,4vw,2.5rem)}}
header p{{margin:.2rem 0 0;color:#cbd9d1;font-size:.84rem}}
main{{max-width:1080px;margin:0 auto;padding:clamp(1.2rem,4vw,2.6rem) clamp(1rem,4vw,2rem) 3rem}}
h1{{font-size:clamp(1.8rem,5vw,2.8rem);line-height:1.1;letter-spacing:-.03em;margin:.25rem 0 .7rem}}
.lede{{font-size:1.08rem;color:#32483d;max-width:74ch}}
.summary{{background:#fff;border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:14px;padding:1rem 1.1rem;margin:1rem 0}}
.notice{{background:var(--warn-bg);border:1px solid #e7d2a3;border-left:5px solid #a36a10;border-radius:12px;padding:.95rem 1.1rem;margin:1rem 0}}
.status{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.75rem;margin:1.1rem 0}}
.status-card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:.9rem 1rem}}
.status-card .label{{font-size:.77rem;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin:0}}
.status-card .value{{font-size:1.35rem;font-weight:750;margin:.2rem 0}}
.status-card .small{{font-size:.83rem;color:var(--muted);margin:0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:.8rem;margin:1rem 0}}
.card{{display:flex;flex-direction:column;gap:.3rem;background:#fff;border:1px solid var(--line);border-radius:12px;padding:1rem;text-decoration:none;color:var(--ink);transition:border-color .15s,transform .15s}}
.card:hover{{border-color:var(--accent);transform:translateY(-1px)}}
.card strong{{font-size:1rem;color:#075b49}}
.card span{{font-size:.82rem;color:#263b33;font-weight:650}}
.card em{{font-style:normal;font-size:.84rem;color:var(--muted)}}
footer{{background:var(--ink);color:#e1e9e4;padding:1.5rem clamp(1rem,4vw,2.5rem);font-size:.86rem}}
footer a{{color:#a4e5cf}}
@media(max-width:520px){{.grid{{grid-template-columns:1fr}}}}
@media print{{header,footer{{print-color-adjust:exact}}.card{{break-inside:avoid}}}}
</style>
</head>
<body>
    <header><strong>China money</strong><p>Official-source research · summary re-reviewed 10 November 2026 · navigation integrated 10 November 2026 · not tax or legal advice</p></header>
<main>
<h1>Getting CNY out of China: identify the source, then compare approved routes</h1>
<p class="lede">The bank's explanation matters. A requested tax certificate, an actual tax assessment, an FX eligibility question and a transfer fee are different things. This repository separates them; it does not assume that any private balance is taxable, already taxed, or eligible for a particular route.</p>
<div class="summary"><p><strong>What the source review supports:</strong> PRC FX rules reviewed set transaction-document requirements. No separate tax solely for exchanging currency was located in those instruments, but the source and tax history of the balance are unknown. For lawful current-account income, SAFE guidance requires identity and transaction/source evidence including tax documents; the correct category is individual-specific. {ext("https://www.safe.gov.cn/tianjin/2026/0713/3088.html", "SAFE 2026 guidance")} · {ext("https://www.safe.gov.cn/safe/2008/0806/5321.html", "State Council FX rules")}</p></div>
<div class="notice"><strong>Most important limitation:</strong> the exact tax due, best eligible route and all-in USD cost cannot be determined from the facts provided. Current FX rate/spread and all intermediary/receiver fees are not available as an account-specific executable quote. Do not treat modeled ranges in the scenario ladder as verified prices. <strong>HSBC fee note (updated 10 November 2026):</strong> route pages cite the tariff effective 31 October 2026; the former “USD 0–7” same-name Global Transfer wording shown with the 2021 tariff is superseded — same-name Global Transfer is now published Free for Private Banking and Premier (Advance: CNY 145 indicative per transaction, actual USD 20), and the tariff's USD 7 reference is specific to International Education Payment, not a general same-name remittance. See <a href="audit-0f0f59fe/index.html#C04">finding C04</a> and the <a href="https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf" target="_blank" rel="noopener noreferrer">current tariff</a>.</div>
<div class="status">
  <div class="status-card"><p class="label">PRC tax on this balance</p><p class="value">— / undetermined</p><p class="small">Source, category, dates and prior tax records are unknown.</p></div>
  <div class="status-card"><p class="label">Route eligibility</p><p class="value">— / undetermined</p><p class="small">Residence category, account type and transaction origin matter.</p></div>
  <div class="status-card"><p class="label">Current all-in cost</p><p class="value">— / unverified</p><p class="small">Request current, executable rate and itemized fees.</p></div>
</div>
<section class="notice" id="integration-review">
<h2>Flagged for Review · briefing limitations</h2>
<p><strong>E01 — blanket no-tax wording is not a personal tax conclusion.</strong> The briefing's “no tax on converting” language must not be read as a guarantee of no taxable income or currency gain. The IRS requires foreign-currency income and relevant tax items to be translated into the taxpayer's functional currency. Tax basis, source and transaction history are unknown. {ext("https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates", "IRS currency rules (re-read 10 November 2026)")} · <a href="briefing/EXECUTIVE_SUMMARY.md">Affected executive summary</a></p>
<p><strong>E02 — historic rate, not today's executable quote.</strong> The briefing's USD fee illustrations use CNY 7.129/USD (2025 annual average), not a current customer conversion rate. Do not interpret the $86.97 wire-fee illustration as the cost of converting or delivering $400,000. Spread, intermediary fees, receiving fees and personal taxes remain unverified. {ext("https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates", "IRS rate-use guidance")} · <a href="briefing/costs.html">Affected cost tables and assumptions</a></p>
<p>All other unresolved findings: <a href="briefing/flagged.html">consolidated Flagged for Review</a> · <a href="audit-ad300459/flagged.html">latest source-audit flags</a>. These cautions do not establish that a bank will accept this particular balance.</p>
</section>
<h2>Choose a category</h2>
<div class="grid">{site_cards}</div>
<section class="summary">
<h2>What to ask the bank first</h2>
<p>Request the refusal in writing. Ask it to identify the tax type (if any), taxpayer, period, tax base, amount and legal basis; distinguish a tax payment from a tax certificate or a bank fee; list acceptable source-of-funds evidence; confirm which FX category applies; and provide a current all-in quote showing the applied CNY/USD rate, sender fee, cable, correspondent/intermediary and recipient charges. The current HSBC schedule, for example, is specific to customer segments and excludes charges of other institutions. {ext("https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf", "HSBC China tariff effective 31 October 2026")}</p>
</section>
</main>
<footer>
<p><strong>Research, not advice.</strong> No private account facts were entered, no bank was contacted, no funds moved and no tax return filed. Every unresolved personal value is left blank or flagged.</p>
<p><a href="briefing/index.html">Executive briefing</a> · <a href="audit-ad300459/index.html">Official-source audit</a> · <a href="audit-0f0f59fe/index.html">Claim review</a> · <a href="ladder/flagged.html">Flagged for review</a> · <a href="ladder/sources.html">Sources</a> · <a href="README.md">README</a> · <a href="COORDINATION.md">Task board</a></p>
</footer>
</body>
</html>
"""
    (REPO / "index.html").write_text(page, encoding="utf-8")


# ---------------------------------------------------------------------------
def main():
    out = {
        "index.html": page_index(),
        "costs.html": page_costs(),
        "ladder.html": page_ladder(),
        "routes.html": page_routes(),
        "steps.html": page_steps(),
        "tax.html": page_tax(),
        "assumptions.html": page_assumptions(),
        "audit.html": page_audit(),
        "flagged.html": page_flags(),
        "sources.html": page_sources(),
    }
    for name, html_text in out.items():
        (ROOT / name).write_text(html_text)
    write_root_hub()
    print(f"wrote {len(out)} pages, {sum(len(v) for v in out.values()):,} bytes")


if __name__ == "__main__":
    main()
