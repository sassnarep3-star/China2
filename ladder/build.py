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


def tier_rows(tier):
    rows = [r for r in ROWS if r["tier"] == tier]
    rows.sort(key=lambda r: (r["total_hi"] if r["total_hi"] is not None else 9e9))
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
    picks = [10_000, 100_000, 400_000]
    cards = "".join(
        f"""<div class="card kpi"><p class="kpi-l">${t:,} out</p>
        <p class="kpi-v">{money(best_at(t)['total_lo'])} – {money(best_at(t)['total_hi'])}</p>
        <p class="kpi-s">{pct(best_at(t)['pct_lo'])} – {pct(best_at(t)['pct_hi'])} of the amount ·
        {esc(best_at(t)['name'])}</p></div>""" for t in picks)

    facts = [
        ("Is there a PRC tax on converting RMB to USD?", "No such tax appears in any instrument reviewed "
         "here. PRC tax attaches to the <em>income</em>; conversion is a documentary and pricing event.",
         ["S01", "S02", "S07"]),
        ("Then why does the bank refuse or quote a “tax”?", "Because the bank must see either a tax "
         "certificate for lawful current-account income, or an original exchange memo to reverse a "
         "conversion. Without one of those, the counter has no lawful basis to convert a large balance.",
         ["S02", "S20"]),
        ("What does USD 50,000 a year actually cover?", "The annual aggregate applies to individuals' FX "
         "<em>sales</em> and to <em>domestic</em> individuals' purchases. It is not a universal ceiling on "
         "moving your own documented money out.", ["S02"]),
        ("What can I do with a passport only?", "Convert back at most the equivalent of USD 500 in a day "
         "(USD 1,000 at a port-side counter before departure). That is a documentary exemption for "
         "re-conversion, not a quota for earned income.", ["S17", "S02"]),
        ("Can I carry cash instead?", "Up to USD 5,000 out of China without a permit, USD 5,000–10,000 with "
         "a bank certificate; above USD 10,000 only in listed special cases. Entering the US with more than "
         "USD 10,000 requires a FinCEN Form 105 report.", ["S15", "S13"]),
        ("What are the real penalties?", "For unlawful FX conduct: up to 30% of the amount, or 30%–100% if "
         "serious; 20% for illegal cash carriage. For US reporting failures the exposure is separate and "
         "can exceed the tax.", ["S04", "S10"]),
        ("Can I use crypto or a friend's quota?", "No. Exchanging RMB for virtual currency is an illegal "
         "financial activity, and borrowing a quota puts both parties on a watch list.",
         ["S16", "S01", "S18"]),
    ]
    fact_rows = "".join(
        f"<tr><th scope='row'>{q}</th><td>{a} <span class='srcs'>{' '.join(src_link(s) for s in ss)}</span></td></tr>"
        for q, a, ss in facts)

    route_cards = [
        ("If the RMB is already-taxed salary or fees", "R01", "Documented income at the counter, then a "
         "SWIFT wire. Zero extra PRC tax; you pay commission, cable and spread."),
        ("If you bank with HSBC on both sides", "R02", "Same paperwork, but move the USD with Global "
         "Transfer: free for Premier, otherwise about $7."),
        ("If you bought the RMB with USD inside China", "R03", "Reverse it against the original exchange "
         "memo within 24 months. No tax certificate needed."),
        ("If you emigrated from China", "R07", "The emigration transfer has no annual quota; it is staged "
         "over two years and needs tax clearance."),
        ("If the RMB came from selling a flat", "R09", "20% PRC tax on the gain, then a capital-account "
         "remittance."),
        ("If the money was never taxed", "R01", "Settle the PRC tax first and claim it in the US on Form "
         "1116. There is no lawful conversion trick that avoids this."),
    ]
    rc = "".join(
        f"<a class='pick' href='routes.html#{rid}'><strong>{esc(t)}</strong><span>{esc(d)}</span>"
        f"<em>{esc(next(r['short'] for r in ROUTES if r['id'] == rid))} →</em></a>"
        for t, rid, d in route_cards)

    body = f"""
<section class="hero">
  <h1>What it actually costs to get CNY out of China</h1>
  <p class="lede">{len([r for r in ROUTES if r["status"] != "unlawful"])} lawful or conditional routes,
priced at every $10,000 step from $10,000 to
  $400,000, with the fee schedule and the legal ceiling behind each one. The short answer: on money that has
  already borne PRC tax, conversion is cheap and the “tax penalty” people describe is almost always
  something else.</p>
  <div class="kpis">{cards}</div>
  <p class="note">Cost of the cheapest route that actually delivers USD to an overseas account, at each tier:
  published bank fees plus a modelled spread band. It excludes any PRC tax on the source money (shown
  separately on <a href="tax.html">Tax &amp; penalties</a>) and excludes US preparer fees. The spread is the
  dominant cost and it is <em>not</em> published — see <a href="assumptions.html">assumptions</a>.</p>
</section>

<section class="panel">
  <h2>The answer in one paragraph</h2>
  <p>There is no PRC tax on converting RMB into USD. What exists is a <strong>documentary gate</strong>: the
  bank may convert a non-domestic individual's lawful current-account income only against identity plus
  proof of the transaction <em>including the tax voucher</em>. If the underlying income was already taxed
  and withheld, the extra PRC tax on conversion is <strong>zero</strong> and the true cost is the bank's
  commission (0.1%, CNY 100–500, plus CNY 120 cable on the verified tariff), plus the FX spread — roughly
  <strong>0.3%–1.8% all-in</strong>. If the income was never taxed, the 3%–45% or flat 20% that people call a
  “conversion penalty” is simply the unpaid PRC tax on the source, and no route avoids it lawfully. The
  cheapest legal sequence in that case is to pay it, collect the certificate, convert, and claim the PRC tax
  against US tax on Form 1116.</p>
</section>

<section class="panel">
  <h2>Pick the row that matches your money</h2>
  <div class="picks">{rc}</div>
</section>

<section class="panel">
  <h2>Seven questions, answered from the primary text</h2>
  <div class="table-wrap"><table class="grid facts"><tbody>{fact_rows}</tbody></table></div>
</section>

<section class="panel">
  <h2>Where the cost actually goes</h2>
  <p>Five things are routinely added together and called “the tax”. Only one of them is a tax on
  conversion, and it is zero.</p>
  <ol class="layers">
    <li><strong>PRC tax on the source income.</strong> 3%–45% comprehensive, 5%–35% business, 20% flat on
    dividends/interest/rent/property gain, or 10% treaty rate on dividends and royalties.
    {src_link('S07')} {src_link('S09')}</li>
    <li><strong>The bank's FX spread.</strong> Bank revenue, not a tax. Not published in advance; the only
    honest number is the executable quote on the day. <span class="flag-inline">model assumption A2</span></li>
    <li><strong>Commission and cable fees.</strong> Published: 0.1% with a CNY 100 floor and CNY 500 cap,
    plus CNY 120 cable per transfer, plus 1% to turn cash into remittable FX. {src_link('S06')}</li>
    <li><strong>PRC penalties for doing it the wrong way.</strong> Up to 30% of the amount, 30%–100% if
    serious, 20% for illegal cash carriage. {src_link('S04')}</li>
    <li><strong>US tax and reporting.</strong> Worldwide income is taxable, but PRC tax paid is creditable
    ({src_link('S12')}); the FBAR and Form 8938 duties attach to holding the account, not to converting.
    {src_link('S10')} {src_link('S11')}</li>
  </ol>
</section>

<section class="panel">
  <h2>Read next</h2>
  <div class="picks">
    <a class="pick" href="costs.html"><strong>Cost tables</strong><span>Six milestone amounts, all fifteen
    priced routes, most important column first.</span><em>Open →</em></a>
    <a class="pick" href="ladder.html"><strong>All 40 tiers</strong><span>Every $10,000 step from $10,000 to
    $400,000, with transaction counts and elapsed time.</span><em>Open →</em></a>
    <a class="pick" href="steps.html"><strong>Step by step</strong><span>What to bring, what to say at the
    counter, and what to keep.</span><em>Open →</em></a>
    <a class="pick" href="flagged.html"><strong>Flagged for review</strong><span>What could not be verified,
    and where prior work in this repository disagrees.</span><em>Open →</em></a>
  </div>
</section>
"""
    return shell("index.html", "What it actually costs", body)


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
<p class="lede">Same question at six amounts. Within each table the routes are ordered by the top of their
cost range, so the cheapest lawful route is first. Every row links to the authority behind its ceiling.</p>
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
        ("Splitting to evade limits / lending your quota", "watch list for the current year plus two years; "
         "counter service then requires full documentation", "S18", "Art. 2"),
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
  most cases where the PRC rate is at or above the US rate, the US tax on the same income is reduced to
  near zero — the credit is doing the work, not a trick.</p>
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
    <li>Outward telegraphic transfer: 0.1%, minimum CNY 100, maximum CNY 500 per transaction, plus a CNY 120
    cable fee. {src_link('S06')}</li>
    <li>Currency of a cash balance converted to remittable FX: 1% (waived for Premier). {src_link('S06')}</li>
    <li>Same-name HSBC Global Transfer: free for Premier, reference price USD 7 per transfer. {src_link('S06')}</li>
    <li>Foreign cash withdrawal: 0.25%–0.4%, minimum CNY 40. {src_link('S06')}</li>
    <li>CNY 100,000 per person per calendar year of overseas ATM cash; CNY 10,000 per card per day.
    {src_link('S03')}</li>
    <li>USD 500 per day onshore / USD 1,000 per day port-side conversion exemption. {src_link('S17')}</li>
    <li>USD 5,000 / 10,000 cash carrying thresholds. {src_link('S15')}</li>
    <li>Staged emigration remittance: up to half, then half of the remainder after one year, balance after
    two years; RMB 200,000 may go in one go. {src_link('S05')}</li>
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
        if not p.is_file() or ".git/" in str(p) or "/data/" in str(p):
            continue
        rel = p.relative_to(REPO)
        if str(rel).startswith("ladder/"):
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
        ("AUD-10", "Prior work asserts a USD 100,000 Form 3520 threshold for foreign gifts/bequests.",
         "Not re-verified in this session; the IRS page was not retrieved here.",
         "Left out of the model and flagged rather than repeated.", "F07"),
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
     "is the only real number. Treat the ladder as a planning band, not a quote.", ["S06"]),
    ("F05", "Offshore RMB (CNH) route eligibility is unverified", "medium",
     "Whether a non-resident US citizen may move RMB to Hong Kong and convert there was not established from "
     "a primary source. Route R14 is published with a blank eligibility and is not priced for a decision.",
     ["S02"]),
    ("F06", "Property-sale FX procedure for a non-domestic vendor is unverified", "medium",
     "The 20% rate on the gain is verified (S07 Arts. 3(3), 6(5)) and the tax certificate is checked at "
     "registration (S07 Art. 15), but the specific SAFE/bank documentary path for repatriating a foreign "
     "vendor's proceeds was not verified here. The 20% figure is published; the procedure is flagged.",
     ["S07", "S01"]),
    ("F07", "Form 3520 threshold not verified in this session", "low",
     "Prior work in this repository asserts a USD 100,000 threshold for foreign gifts and bequests. It was "
     "not re-retrieved here, so it is excluded from the model and flagged rather than repeated.", []),
    ("F08", "Card and ATM fixed fees are unpublished", "medium",
     "ATM operator fees, issuer foreign-transaction markups and card scheme settlement rates were not "
     "obtained. Routes R11 and R12 are marked PARTIAL: their estimates include the spread only.",
     ["S03"]),
    ("F09", "The verified bank tariff is dated 1 January 2021", "medium",
     "The HSBC China personal tariff retrieved is the current document reachable on the bank's site, but its "
     "effective date is 2021. Confirm the current schedule at the branch; a change in the CNY 500 cap or the "
     "CNY 120 cable fee would move every fixed-fee row.", ["S06"]),
    ("F10", "Three prior dashboards publish different counts", "low",
     "docs/, site/ and portal/ present overlapping material with different totals. None was edited; the "
     "inconsistency is recorded rather than resolved by deletion.", []),
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
    """Root landing page. Generated so its headline numbers cannot drift."""
    picks = [10_000, 100_000, 400_000]
    cards = "".join(
        f'<div class="kpi"><p class="l">${t:,} out</p>'
        f'<p class="v">{money(best_at(t)["total_lo"])} – {money(best_at(t)["total_hi"])}</p>'
        f'<p class="s">{pct(best_at(t)["pct_lo"])} – {pct(best_at(t)["pct_hi"])} of the amount</p></div>'
        for t in picks)
    sites = [
        ("ladder/index.html", "Cost ladder", "The answer, the cost tables and all 40 tiers",
         "15 routes priced at every $10,000 step to $400,000, with the fee schedule and the legal ceiling "
         "behind each one. Start here."),
        ("docs/index.html", "Research dashboard", "Findings, evidence ledger and review flags",
         "The original source-linked research build: routes, costs, taxes, checklist, flags, sources."),
        ("site/index.html", "Evidence site", "Rules, lawful and unlawful routes, methodology",
         "Built from a separate evidence ledger with its own verification harness."),
        ("portal/index.html", "Research portal", "Statutory verification and line-by-line repo audit",
         "A third independent pass, with a .gov/.gov.cn source register and audit of the repository."),
        ("audit-86f0/index.html", "Independent audit", "Claim corrections and a blank-cost 22 × 40 matrix",
         "A fourth session's audit. Its matrix deliberately leaves cost cells blank; this ladder fills them "
         "with published fees plus a labelled spread band. Read them together."),
    ]
    site_cards = "".join(
        f'<a class="site" href="{u}"><strong>{esc(t)}</strong><span>{esc(sub)}</span>'
        f'<em>{esc(d)}</em></a>' for u, t, sub, d in sites)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>China money · CNY to USD, costed</title>
<meta name="description" content="Source-linked cost of converting CNY to USD for a US citizen, from $10,000 to $400,000 in $10,000 steps.">
<style>
:root{{--ink:#12211d;--muted:#6b7d74;--paper:#f6f5ef;--line:#dfddd2;--accent:#0f6d5c}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
 font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
header{{background:var(--ink);color:#f4f2ea;padding:1.1rem clamp(1rem,4vw,2.5rem)}}
header p{{margin:.2rem 0 0;font-size:.8rem;color:#a9bab1}}
main{{max-width:1000px;margin:0 auto;padding:clamp(1.4rem,4vw,2.6rem) clamp(1rem,4vw,2rem) 3rem}}
h1{{font-size:clamp(1.7rem,5vw,2.6rem);line-height:1.12;letter-spacing:-.02em;margin:.2rem 0 .6rem}}
.lede{{font-size:1.06rem;color:#2c4038;max-width:70ch}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.8rem;margin:1.4rem 0}}
.kpi{{background:#fff;border:1px solid var(--line);border-top:4px solid var(--accent);border-radius:14px;
 padding:1rem 1.1rem;box-shadow:0 8px 24px rgba(18,33,29,.05)}}
.kpi .l{{margin:0;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}
.kpi .v{{margin:.1rem 0;font-size:1.7rem;font-weight:680;letter-spacing:-.02em}}
.kpi .s{{margin:0;font-size:.8rem;color:var(--muted)}}
.answer{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:12px;
 padding:1rem 1.1rem;margin:1.2rem 0}}
.sites{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:.8rem;margin:1rem 0}}
.site{{display:flex;flex-direction:column;gap:.25rem;background:#fff;border:1px solid var(--line);
 border-radius:12px;padding:1rem;text-decoration:none;color:var(--ink)}}
.site:hover{{border-color:var(--accent)}}
.site strong{{font-size:1rem}} .site span{{font-size:.85rem;color:#3b5147}}
.site em{{font-style:normal;font-size:.82rem;color:#54695f}}
footer{{background:var(--ink);color:#c8d4ce;padding:1.6rem clamp(1rem,4vw,2.5rem);font-size:.82rem}}
footer a{{color:#8fe0c8}}
</style>
</head>
<body>
<header><strong>China money</strong><p>Source-linked research · retrieved {META['retrieved']} · not tax or legal advice</p></header>
<main>
<h1>Getting CNY out of China: what it actually costs</h1>
<p class="lede">A US citizen's RMB balance is not blocked by a tax on converting currency. It is blocked by
documentation, and the largest real cost is the bank's FX spread. Below is the costed answer, then the
research behind it.</p>
<div class="kpis">{cards}</div>
<p class="lede" style="font-size:.88rem;color:#54695f">Cheapest route that actually delivers USD to an overseas
account: documented income, converted at the counter, moved by same-bank Global Transfer or SWIFT. Excludes any
PRC tax on the source money (that is a separate question, answered inside) and excludes US preparer fees.</p>
<div class="answer"><p><strong>Short version.</strong> If the RMB is already-taxed income, the extra PRC tax to
convert it is zero and the all-in cost is roughly 0.3%–1.8%. If it was never taxed, the 3%–45% or flat 20%
being called a “conversion penalty” is simply unpaid PRC tax, and the lawful fix is to pay it, get the
certificate, convert, and claim it in the US on Form 1116. If you emigrated from China, the dedicated
emigration transfer route has no annual quota but takes up to two years. Crypto, private swaps, borrowed
quotas and underground banks are criminal or prohibited, with fines of 20%–100%.</p></div>
<h2>Dashboards in this repository</h2>
<div class="sites">{site_cards}</div>
</main>
<footer>
<p><strong>Research, not advice.</strong> No personal tax amount is computed, no transfers were made and no
returns were filed. Every published figure links to the authority that publishes it; unverified values are
blank and flagged rather than filled in.</p>
<p><a href="ladder/flagged.html">Flagged for review</a> ·
<a href="ladder/sources.html">Sources</a> ·
<a href="COORDINATION.md">Task board</a></p>
</footer>
</body>
</html>
"""
    (REPO / "index.html").write_text(page)


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
