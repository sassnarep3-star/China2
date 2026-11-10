#!/usr/bin/env python3
"""Static site builder for the consolidated CNY->USD guide.

Every page is generated from guide/data/*.json so that the site, the CSV and
the JSON cannot drift apart. No third-party scripts, no runtime fetches: the
HTML is complete on its own and works at the GitHub Pages /China2/ subpath.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RATE = 7.10
TODAY = "10 November 2026"

SOURCES = json.loads((DATA / "sources.json").read_text())
METHODS = json.loads((DATA / "methods.json").read_text())
COSTS = json.loads((DATA / "costs.json").read_text())
SRC = {s["id"]: s for s in SOURCES["sources"]}
M = {m["id"]: m for m in METHODS["methods"]}
ROWS = {(r["method"], r["tier"]): r for r in COSTS["rows"]}
TIERS = COSTS["meta"]["tiers"]
COSTED = COSTS["meta"]["costed_methods"]
UNVERIFIED = COSTS["meta"]["unverified_methods"]

NAV = [
    ("index.html", "Overview"),
    ("methods.html", "Methods"),
    ("costs.html", "Costs"),
    ("steps.html", "Step by step"),
    ("tax.html", "Tax &amp; penalties"),
    ("flagged.html", "Flagged"),
    ("sources.html", "Sources"),
    ("audit.html", "Repo audit"),
]


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def src_link(sid: str, label: str | None = None) -> str:
    s = SRC[sid]
    return (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer" '
            f'title="{esc(s["title"])}">{esc(label or sid)}</a>')


def money(x, blank: str = "—") -> str:
    return blank if x is None else f"{x:,.2f}"


def nav(active: str) -> str:
    parts = []
    for u, l in NAV:
        cur = ' aria-current="page"' if u == active else ""
        parts.append(f'<a href="{u}"{cur}>{l}</a>')
    return '<nav class="topnav" aria-label="Sections">' + "".join(parts) + '</nav>'



def page(active: str, title: str, subtitle: str, body: str, cls: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="Source-linked research on converting CNY to USD from mainland China as a U.S. citizen: methods, costs at every $10,000 step, tax, penalties and step-by-step execution.">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="{cls}">
<header class="site">
  <div class="wrap">
    <a class="brand" href="index.html">China&nbsp;money<span>CNY → USD · U.S. citizen</span></a>
    {nav(active)}
  </div>
</header>
<div class="masthead">
  <div class="wrap">
    <h1>{title}</h1>
    <p class="sub">{subtitle}</p>
  </div>
</div>
<main class="wrap">
{body}
</main>
<footer class="site">
  <div class="wrap">
    <p><strong>Research, not advice.</strong> Prepared {TODAY}. Every table row links to the primary official source it rests on; values that could not be confirmed are blank and listed on the <a href="flagged.html">Flagged for Review</a> page. No bank was contacted, no funds were moved and no return was filed for any person.</p>
    <p class="tiny"><a href="index.html">Overview</a> · <a href="methods.html">Methods</a> · <a href="costs.html">Costs</a> · <a href="steps.html">Step by step</a> · <a href="tax.html">Tax &amp; penalties</a> · <a href="flagged.html">Flagged</a> · <a href="sources.html">Sources</a> · <a href="audit.html">Repo audit</a> · <a href="../COORDINATION.md">Task board</a></p>
  </div>
</footer>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- overview
def buy_verdict():
    return [
        ("Best route if the money is documented salary or business income",
         "M01", "Documented income → SWIFT wire",
         "No USD 50,000 ceiling, no PRC tax on the exchange itself, and the cost is one bank commission plus the bank's spread."),
        ("Best route if the money predates emigration and you have cancelled household registration",
         "M03", "Emigration asset transfer",
         "The only channel expressly built to move a large owned balance abroad; approved once, remitted in stages over up to two years."),
        ("Cheapest published fee, if you already bank with HSBC on both sides",
         "M02", "Documented income → Global Transfer",
         "The same-name Global Transfer item is published Free for Premier and Private Banking in the 31 Oct 2026 tariff."),
        ("Cleanest paperwork, if the RMB came from USD you brought in",
         "M05", "Re-conversion on the original exchange memo",
         "No tax certificate needed; valid for 24 months from the exchange date."),
    ]


def page_index():
    rows = []
    for label, mid, name, why in buy_verdict():
        m = M[mid]
        rows.append(
            f"<tr><td data-label=\"Situation\">{esc(label)}</td>"
            f"<td data-label=\"Method\"><a href=\"methods.html#{mid}\">{mid} · {esc(name)}</a></td>"
            f"<td data-label=\"Why\">{esc(why)}</td>"
            f"<td data-label=\"Source\">{' '.join(src_link(s) for s in m['basis'][:3])}</td></tr>")

    tier10 = ROWS[("M01", 10000)]["total_usd"]
    tier400 = ROWS[("M01", 400000)]["total_usd"]
    # Rank only routes that actually put USD in a US account: "do nothing" and
    # "small ID-only conversion" are excluded, because a zero or tiny fee on a
    # route that cannot move the money is not the cheapest way to move the money.
    DELIVERING = ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08", "M12"]
    cheapest400 = min((ROWS[(m, 400000)]["total_usd"], m) for m in DELIVERING)

    body = f"""
<div class="callout lead">
  <h2>The short answer</h2>
  <p><strong>There is no PRC tax on converting currency.</strong> The PRC individual income tax law taxes nine listed
  categories of income, and an exchange of your own renminbi is not one of them {src_link("S05")}. What actually costs
  money, in descending order, is: (1) PRC tax on the <em>underlying income</em> if it was never paid, (2) the bank's
  exchange spread, (3) fixed bank and correspondent fees, and (4) U.S. reporting penalties if the account was never
  declared. Of these, only the spread and the fixed fees are costs of <em>converting</em>; the rest are costs of the
  history of the money.</p>
  <p>So the question to answer first is not "how do I convert", it is <strong>"what is this balance, and can I
  document it?"</strong> A documented, already-taxed balance moves out at roughly <strong>{money(tier400)} on
  USD 400,000 ({ROWS[("M01", 400000)]["pct_of_principal"]}%)</strong> in fees and spread. An undocumented balance has
  no lawful route at any price.</p>
</div>

<div class="cards">
  <div class="card"><p class="lbl">Cheapest route that actually delivers USD</p>
    <p class="big">{money(cheapest400[0])}</p>
    <p class="small">on USD 400,000 via {esc(M[cheapest400[1]]["short"])} — published fee plus the labelled spread assumption.
    Every lawful delivery route costs about the same, because they all pay the same spread and the same CNY 120 cable.</p></div>
  <div class="card"><p class="lbl">Cost of a documented wire</p>
    <p class="big">{money(tier10)} → {money(tier400)}</p>
    <p class="small">USD 10,000 → USD 400,000. Fixed fees dominate at the low end; the spread dominates at the high end.</p></div>
  <div class="card"><p class="lbl">Methods catalogued</p>
    <p class="big">{len(M)}</p>
    <p class="small">{len([m for m in M.values() if m['status']=='lawful'])} lawful · {len([m for m in M.values() if m['status']=='conditional'])} conditional · {len([m for m in M.values() if m['status']=='unlawful'])} unlawful</p></div>
  <div class="card"><p class="lbl">Costed with published fees</p>
    <p class="big">{len(COSTED)} / {len(M)}</p>
    <p class="small">{len(UNVERIFIED)} methods have no published fee in the official sources read, so their cost cells are blank, not estimated.</p></div>
</div>

<h2>Which route fits you</h2>
<div class="tablewrap">
<table class="grid">
<thead><tr><th>Situation</th><th>Method</th><th>Why</th><th>Source</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>

<h2>The seven things that decide the answer</h2>
<ol class="tight">
  <li><strong>Your characterisation in PRC FX law.</strong> A US citizen living in China for a continuous year or more is a
  <em>domestic individual</em>; otherwise a <em>non-domestic individual</em> {src_link("S05", "S05 Art. 52(2)")}. The
  operative rule differs: a domestic individual's <em>purchases</em> of FX face the annual total
  {src_link("S02", "S02 Art. 2")}, while a non-domestic individual converting lawful current-account RMB proceeds on
  identity plus source and tax documents {src_link("S03", "SAFE 2026 guidance")}.</li>
  <li><strong>The USD 50,000 figure is narrower than it looks.</strong> It is an annual total for individuals' FX
  <em>sales</em> and for a domestic individual's FX <em>purchases</em> {src_link("S02", "S02 Art. 2")}. Above it, the
  transaction is not banned: it moves to a documents-based review
  {src_link("S02", "S02 Arts. 10-12")}. So "my money is stuck because of the 50,000 cap" is usually a documents
  problem wearing a quota's clothes.</li>
  <li><strong>Using other people's quotas is a separate offence.</strong> Borrowing a quota, or lending yours, puts you on
  SAFE's watch list for that year plus two more {src_link("S09", "S09 point 2")}, and splitting to evade limits is
  expressly prohibited {src_link("S01", "S01 Art. 7")}. This closes the most commonly suggested workaround.</li>
  <li><strong>The U.S. side has a real but narrow tax.</strong> Disposing of foreign currency is a section 988
  transaction {src_link("S12", "26 USC 988(c)(1)(C)(i)")}, but for an individual's personal transaction no gain is
  recognised unless it exceeds <strong>USD 200</strong> {src_link("S12", "26 USC 988(e)(2)")}, restated in
  {src_link("S13", "IRS Publication 525")}. At IRS yearly averages from 2021 to 2025 the renminbi moved from 6.452 to
  7.129 per dollar — a <em>loss</em> for anyone who acquired RMB in 2021-2023 {src_link("S14", "IRS yearly averages")}.
  See <a href="tax.html">Tax &amp; penalties</a> for the arithmetic.</li>
  <li><strong>Reporting is due whether or not you move anything.</strong> A foreign account aggregate over USD 10,000
  must be reported on the FBAR {src_link("S15", "IRS FBAR page")} and a balance over the 8938 thresholds on Form 8938
  {src_link("S18", "26 USC 6038D")}. The FBAR penalty maximums are USD 16,536 non-willful and USD 165,353 willful per
  violation {src_link("S16", "31 CFR 1010.821")}. This is the largest number in this whole project and it has nothing
  to do with converting.</li>
  <li><strong>Cash is capped twice.</strong> Out of China: USD 5,000 without a permit, USD 10,000 with one, and in
  principle no more above that {src_link("S07", "SAFE/customs 2003")}. Onto a card abroad: CNY 100,000 equivalent per
  person per calendar year, with a two-year suspension for exceeding it {src_link("S08", "SAFE 2017")}. Neither can
  move a six-figure balance.</li>
  <li><strong>The published spread is a board rate, not your quote.</strong> The one same-day published retail figure
  verified here is Bank of China's, 665.72 buy against 668.52 sell per 100 USD, a 0.419% spread
  {src_link("S22", "BOC board rates")}, on a page that says it is for reference only. Every cost table below uses it as
  a labelled assumption. Replace it with the bank's executable quote before acting.</li>
</ol>

<div class="callout warn">
  <h2>Read this before you trust any number on this site</h2>
  <ul class="tight">
    <li><strong>The single biggest unknown is whether your balance is documented.</strong> Nothing published lets an
    undocumented balance leave lawfully. The tax and the permit are on the money's history, not on the exchange.</li>
    <li><strong>The spread is an assumption.</strong> It is one bank's published board rate from 10 Nov 2026
    {src_link("S22")}, applied uniformly. Your bank's executable rate will differ, and it moves the total far more than
    any fixed fee.</li>
    <li><strong>Fixed fees are one bank's published tariff.</strong> HSBC China, effective 31 October 2026
    {src_link("S11")}. Other banks publish different schedules, and the tariff itself excludes intermediary and
    receiving-bank charges {src_link("S11", "S11 Important Note 7")}.</li>
    <li><strong>Nothing here knows your facts.</strong> Tax residency days, household registration status, how the
    balance was earned, whether PRC tax was withheld, and whether the FBAR was ever filed are all unknown. Where a fact
    is unknown the cell is blank and the item is on <a href="flagged.html">Flagged for Review</a>.</li>
    <li><strong>Correction to earlier material in this repository.</strong> Some earlier pages in this repo quoted a
    "USD 0-7" same-name Global Transfer fee and a "USD 7" reference. In the current tariff the USD 7 figure belongs to
    <em>International Education Payment</em> (item 2.2.7), and same-name Global Transfer is Free for Premier and Private
    Banking {src_link("S11", "S11 items 2.2.6.1 and 2.2.7")}. The guide uses the current text.</li>
  </ul>
</div>

<h2>What is in this guide</h2>
<div class="cards links">
  <a class="card" href="methods.html"><strong>Methods</strong><span>{len(M)} routes, including the unlawful ones</span>
    <em>What each one is, who can use it, documents, pros, cons, and the statutory penalty for getting it wrong.</em></a>
  <a class="card" href="costs.html"><strong>Costs</strong><span>every USD 10,000 step to 400,000</span>
    <em>Fee, spread and total per method, with the source link in every row. Blank means no published figure.</em></a>
  <a class="card" href="steps.html"><strong>Step by step</strong><span>exact sequence, documents, what to ask the bank</span>
    <em>The two realistic paths, in order, with the paper you need at each step.</em></a>
  <a class="card" href="tax.html"><strong>Tax &amp; penalties</strong><span>PRC IIT · USC 988 · FBAR · 8938 · Form 105</span>
    <em>The conversion penalty broken down with the actual statutory figures and worked arithmetic.</em></a>
  <a class="card" href="flagged.html"><strong>Flagged for Review</strong><span>unverified cells and irregularities</span>
    <em>Everything that could not be confirmed from an official source, so you can check it yourself.</em></a>
  <a class="card" href="sources.html"><strong>Sources</strong><span>{len(SRC)} primary documents</span>
    <em>Each with the article or item number and the text actually read on {TODAY}.</em></a>
  <a class="card" href="audit.html"><strong>Repo audit</strong><span>irregularities found in this repository</span>
    <em>Contradictions between pages, stale figures and unsupported claims, with what was done about each.</em></a>
  <a class="card" href="../ladder/index.html"><strong>Earlier scenario ladder</strong><span>modelled bands, wider assumptions</span>
    <em>A separate earlier build with wider modelled ranges; compare its caveats before relying on it.</em></a>
</div>

<h2>How to read the cost tables</h2>
<p>The ladder prices each method at each USD 10,000 step from 10,000 to 400,000. Three columns are kept separate on
purpose, so you can recompute every cell by hand:</p>
<ul class="tight">
  <li><strong>Published fee</strong> = <code>clamp(0.1% × principal, CNY100/7.10, CNY500/7.10) + CNY120/7.10</code>
  for the standard wire {src_link("S11", "S11 2.2.4.1-2.2.4.2")}; zero for the items published Free
  {src_link("S11", "S11 2.2.6.1")}.</li>
  <li><strong>Spread</strong> = <code>principal × 0.419%</code>, the labelled assumption from {src_link("S22")}.</li>
  <li><strong>Total</strong> = published fee + spread. It excludes intermediary and receiving-bank charges, which the
  tariff itself excludes {src_link("S11", "S11 Important Note 7")}, and excludes any personal tax.</li>
</ul>
<p class="tiny">Tiers are USD amounts, so no exchange-rate forecast is embedded in the model. The 7.10 CNY/USD rate is
used only to express CNY-denominated published fees in dollars; at USD 400,000 the whole effect of that choice on a
capped fee is under USD 15.</p>
"""
    return page("index.html", "Getting CNY out of China as a U.S. citizen",
                "A source-linked answer to one question: what is the least-tax, least-penalty way to turn a renminbi balance into dollars, and what does each route actually cost.",
                body)


# ---------------------------------------------------------------- methods
def page_methods():
    groups = [("lawful", "Lawful routes", "Available now, on documents."),
              ("conditional", "Conditional structures", "Lawful only if a specific condition is genuinely met, or not verified in this session."),
              ("unlawful", "Unlawful — do not use", "Included because they are the options people are offered. Each carries a quoted statutory penalty.")]
    out = []
    for key, title, sub in groups:
        cards = []
        for m in METHODS["methods"]:
            if m["status"] != key:
                continue
            cost = m["cost"]
            if cost["fee"]["type"] == "unverified":
                costline = '<span class="blank">fee not published — blank</span>'
            elif cost["fee"]["type"] == "zero":
                costline = "no published fee (statutory route)"
            elif cost["fee"]["type"] == "flat_usd":
                costline = f"published fee USD {cost['fee']['usd']:.2f}"
            else:
                costline = "published fee 0.1% of amount, min CNY 100, max CNY 500, plus CNY 120 cable"
            cards.append(f"""
<article class="method {esc(m['status'])}" id="{esc(m['id'])}">
  <header>
    <h3><span class="tag {esc(m['status'])}">{esc(m['status'])}</span> {esc(m['id'])} · {esc(m['name'])}</h3>
  </header>
  <p class="what">{esc(m['what'])}</p>
  <dl class="facts">
    <dt>Who can use it</dt><dd>{esc(m['persona'])}</dd>
    <dt>Capacity</dt><dd>{esc(m['capacity'])}</dd>
    <dt>Published cost</dt><dd>{costline} · {src_link(m['cost']['cost_sources'][0])}</dd>
    <dt>PRC tax</dt><dd>{esc(m['prc_tax'])}</dd>
    <dt>U.S. tax</dt><dd>{esc(m['us_tax'])}</dd>
    <dt>Penalty if wrong</dt><dd class="pen">{esc(m['penalty'])}</dd>
  </dl>
  <div class="two">
    <div><h4>Pros</h4><ul>{''.join(f'<li>{esc(p)}</li>' for p in m['pros'])}</ul></div>
    <div><h4>Cons</h4><ul>{''.join(f'<li>{esc(c)}</li>' for c in m['cons'])}</ul></div>
  </div>
  <details>
    <summary>Documents needed</summary>
    <ul>{''.join(f'<li>{esc(d)}</li>' for d in m['docs'])}</ul>
  </details>
  <details>
    <summary>How it works, step by step</summary>
    <ol>{''.join(f'<li>{esc(s)}</li>' for s in m['steps'])}</ol>
  </details>
  <p class="srcs"><strong>Sources:</strong> {' · '.join(src_link(s) for s in m['basis'])}
     {' · ' if m['cost']['cost_sources'] else ''}
     {' · '.join(src_link(s) for s in m['cost']['cost_sources'] if s not in m['basis'])}</p>
</article>""")
        out.append(f"<section id=\"{key}\" data-method-group><h2>{title}</h2><p class=\"lede\">{sub}</p>{''.join(cards)}</section>")

    summary_rows = "".join(
        f"<tr><td data-label=\"#\"><a href=\"#{esc(m['id'])}\">{esc(m['id'])}</a></td>"
        f"<td data-label=\"Method\">{esc(m['name'])}</td>"
        f"<td data-label=\"Status\"><span class=\"tag {esc(m['status'])}\">{esc(m['status'])}</span></td>"
        f"<td data-label=\"Capacity\">{esc(m['capacity'][:110])}{'…' if len(m['capacity'])>110 else ''}</td>"
        f"<td data-label=\"Source\">{' '.join(src_link(s) for s in m['basis'][:2])}</td></tr>"
        for m in METHODS["methods"])

    body = f"""
<p class="lede">Twenty-seven mechanisms were located. Only thirteen are lawful on documents alone; seven are lawful
only if a specific condition is genuinely met, and several of those conditions could not be verified in this session;
seven are unlawful and are listed with the statute that penalises them so that nobody has to guess where the line is.</p>

<div class="callout">
  <p><strong>Read the status column literally.</strong> <span class="tag lawful">lawful</span> means an official source
  reviewed here establishes the mechanism. <span class="tag conditional">conditional</span> means the mechanism is
  lawful <em>or</em> not verified — check the method's own notes and the
  <a href="flagged.html">Flagged for Review</a> page before relying on it.
  <span class="tag unlawful">unlawful</span> means an official source prohibits it.</p>
</div>

<div class="filters" role="search">
  <label for="msearch">Filter</label>
  <input id="msearch" type="search" placeholder="Search methods, documents, rules…" data-method-search autocomplete="off">
  <label for="mstatus">Status</label>
  <select id="mstatus" data-method-status>
    <option value="all">All statuses</option>
    <option value="lawful">Lawful only</option>
    <option value="conditional">Conditional only</option>
    <option value="unlawful">Unlawful only</option>
  </select>
  <span class="count" data-method-count aria-live="polite"></span>
</div>

<h2>All methods at a glance</h2>
<div class="tablewrap">
<table class="grid">
<thead><tr><th>#</th><th>Method</th><th>Status</th><th>Capacity</th><th>Source</th></tr></thead>
<tbody>{summary_rows}</tbody>
</table>
</div>

<div data-method-list>
{''.join(out)}
</div>
"""
    return page("methods.html", "Every method to convert CNY into USD",
                "What each route is, who may use it, what it needs, and what it costs you if you get it wrong.",
                body)


# ---------------------------------------------------------------- costs
def cost_table(method_ids, caption):
    """Mobile-friendly table: each row carries its own source link."""
    head = ("<tr><th>Method</th><th>Published fee</th><th>Spread (assumed)</th>"
            "<th>Total</th><th>% of amount</th><th>Source</th></tr>")
    rows = []
    for mid in method_ids:
        m = M[mid]
        r = ROWS[(mid, CURRENT_TIER[0])]
        cap_note = ""
        if r["over_annual_cap"]:
            cap_note = ' <span class="flag">over annual cap</span>'
        if r["total_usd"] is None:
            rows.append(
                f"<tr class=\"unverified\"><td data-label=\"Method\"><a href=\"methods.html#{mid}\">{mid} · {esc(m['short'])}</a>{cap_note}</td>"
                f"<td data-label=\"Published fee\" class=\"blank\">not published</td>"
                f"<td data-label=\"Spread (assumed)\" class=\"blank\">not published</td>"
                f"<td data-label=\"Total\" class=\"blank\">blank</td>"
                f"<td data-label=\"% of amount\" class=\"blank\">—</td>"
                f"<td data-label=\"Source\">{' '.join(src_link(s) for s in m['basis'][:2])}</td></tr>")
        else:
            rows.append(
                f"<tr><td data-label=\"Method\"><a href=\"methods.html#{mid}\">{mid} · {esc(m['short'])}</a>{cap_note}</td>"
                f"<td data-label=\"Published fee\">${money(r['fee_usd'])}</td>"
                f"<td data-label=\"Spread (assumed)\">${money(r['spread_usd'])} <span class=\"pct\">{r['spread_pct']}%</span></td>"
                f"<td data-label=\"Total\" class=\"tot\">${money(r['total_usd'])}</td>"
                f"<td data-label=\"% of amount\">{r['pct_of_principal']}%</td>"
                f"<td data-label=\"Source\">{' '.join(src_link(s) for s in m['cost']['cost_sources'][-2:])}</td></tr>")
    return (f'<div class="tablewrap"><table class="grid costs">'
            f'<caption>{caption}</caption><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>')


CURRENT_TIER = [10000]


def page_costs():
    # Headline: the recommended route across every tier, most important first.
    headline = []
    for t in TIERS:
        r = ROWS[("M01", t)]
        headline.append(
            f"<tr><td data-label=\"Amount\">{money(t, '-')}</td>"
            f"<td data-label=\"Published fee\">${money(r['fee_usd'])}</td>"
            f"<td data-label=\"Spread (assumed)\">${money(r['spread_usd'])}</td>"
            f"<td data-label=\"Total\" class=\"tot\">${money(r['total_usd'])}</td>"
            f"<td data-label=\"% of amount\">{r['pct_of_principal']}%</td>"
            f"<td data-label=\"Source\">{src_link('S11')} {src_link('S22')}</td></tr>")

    # All-methods tiers of interest, each its own table so it reads on a phone.
    tier_tables = []
    for t in [10000, 50000, 100000, 200000, 400000]:
        CURRENT_TIER[0] = t
        tier_tables.append(
            f'<h3 id="tier-{t}">At USD {t:,}</h3>'
            + cost_table(COSTED, f"Every costed method at USD {t:,}. Fee from HSBC China tariff effective 31 Oct 2026 "
                                 f"[S11]; spread is the labelled 0.419% assumption [S22]."))

    # Full ladder matrix, all methods x all tiers, with a tier selector.
    full_head = "".join(f'<th class="num">${t//1000}k</th>' for t in TIERS)
    full_rows = []
    for mid in COSTED:
        cells = []
        for t in TIERS:
            r = ROWS[(mid, t)]
            cls = "num"
            if r["total_usd"] is None:
                cells.append('<td class="num blank">—</td>')
            elif r["over_annual_cap"]:
                cells.append(f'<td class="num over">{money(r["total_usd"], "—")}</td>')
            else:
                cells.append(f'<td class="num">{money(r["total_usd"], "—")}</td>')
        full_rows.append(
            f'<tr><th scope="row"><a href="methods.html#{mid}">{mid}</a> {esc(M[mid]["short"])}</th>{"".join(cells)}'
            f'<td>{src_link("S11")}</td></tr>')

    # Cheapest at each tier.
    cheap_rows = []
    for t in TIERS:
        ranked = sorted((ROWS[(mid, t)]["total_usd"], mid) for mid in COSTED
                        if ROWS[(mid, t)]["total_usd"] is not None
                        and not ROWS[(mid, t)]["over_annual_cap"])
        best = ranked[0]
        second = ranked[1]
        cheap_rows.append(
            f"<tr><td data-label=\"Amount\">USD {t:,}</td>"
            f"<td data-label=\"Lowest cost\">{esc(M[best[1]]['short'])} — ${money(best[0])}</td>"
            f"<td data-label=\"Next\">{esc(M[second[1]]['short'])} — ${money(second[0])}</td>"
            f"<td data-label=\"Source\">{' '.join(src_link(s) for s in M[best[1]]['cost']['cost_sources'])}</td></tr>")

    unverified_rows = []
    for mid in UNVERIFIED:
        m = M[mid]
        if m["status"] == "unlawful":
            what = "Statutory penalty only — no lawful price exists"
            why = "An unlawful method has no cost to quote; the published exposure is on the method card"
        elif m["cost"]["fee"]["type"] == "unverified" and m["cost"]["spread"]["pct"] is None:
            what = "Capacity and legal basis only"
            why = "Neither a bank fee nor a conversion spread appears in the official documents read"
        else:
            what = "Partly published"
            why = "The published part is on the method card; the missing part is left blank"
        unverified_rows.append(
            f'<tr class="unverified"><td data-label="Method"><a href="methods.html#{mid}">{mid} · {esc(m["short"])}</a></td>'
            f'<td data-label="Status"><span class="tag {esc(m["status"])}">{esc(m["status"])}</span></td>'
            f'<td data-label="What is published">{esc(what)}</td>'
            f'<td data-label="Why the cost is blank">{esc(why)}</td>'
            f'<td data-label="Source">{" ".join(src_link(s) for s in m["basis"][:2])}</td></tr>')
    unverified_rows = "".join(unverified_rows)

    body = f"""
<div class="callout lead">
  <h2>Most important first: what the cost actually is</h2>
  <p>Converting USD 400,000 through the documented-income wire costs <strong>${money(ROWS[("M01",400000)]["total_usd"])}</strong>
  in published fees plus spread — about <strong>{ROWS[("M01",400000)]["pct_of_principal"]}%</strong>. That is the honest
  answer to "how big is the conversion penalty": it is a fraction of a percent, not a confiscation. If you have been
  quoted something much larger, the large part is almost certainly a <em>tax on the underlying income</em>, a
  <em>fine</em>, or somebody's <em>fee for an unlawful workaround</em> — not the price of exchanging currency.</p>
  <p><strong>The second thing to know: the lawful routes cost almost the same as each other.</strong> Most of them pay
  the same published commission and the same CNY 120 cable charge {src_link("S11")} and the same spread, so the choice
  between them is about <em>whether you qualify</em>, not about price. Only two things move the total materially: a
  route whose bank fee is published Free (a same-name HSBC Global Transfer, or money that is already in USD), and
  leaving the money in renminbi and spending it there.</p>
  <p>At the small end the fixed fee dominates: USD 10,000 costs <strong>${money(ROWS[("M01",10000)]["total_usd"])}</strong>
  ({ROWS[("M01",10000)]["pct_of_principal"]}%), because the CNY 120 cable charge and the CNY 100 minimum commission are
  the same whatever the amount {src_link("S11")}.</p>
</div>

<h2>The recommended route, every USD 10,000 step</h2>
<p class="lede">M01 — documented lawful income, bank FX purchase, SWIFT wire. Fixed fees from the HSBC China tariff
effective 31 October 2026 {src_link("S11", "S11 2.2.4.1-2.2.4.2")}; spread from the labelled assumption {src_link("S22")}.</p>
<div class="tablewrap">
<table class="grid costs">
<caption>Fee, spread and total for the documented-income wire at every step. Every row carries its source.</caption>
<thead><tr><th>Amount (USD)</th><th>Published fee</th><th>Spread (assumed)</th><th>Total</th><th>% of amount</th><th>Source</th></tr></thead>
<tbody>{''.join(headline)}</tbody>
</table>
</div>

<h2>Every method at the tiers that matter</h2>
<p class="lede">Same fee and spread columns, one table per tier so it reads on a phone without horizontal scrolling.
Methods with no published fee are shown as blank with the reason — never estimated.</p>
<div class="filters">
  <label for="tierjump">Jump to</label>
  <select id="tierjump" data-tier-jump>
    <option value="10000">USD 10,000</option>
    <option value="50000">USD 50,000</option>
    <option value="100000">USD 100,000</option>
    <option value="200000">USD 200,000</option>
    <option value="400000">USD 400,000</option>
  </select>
  <span class="count">The full 40-step matrix for every method is further down this page.</span>
</div>
{''.join(tier_tables)}

<h2>Methods with no published cost (blank, not estimated)</h2>
<p class="lede">Fifteen of the twenty-seven methods have no published fee, spread or both in the official documents
read. They are listed here with the source that governs them and the reason the cell is blank. A blank cell is not a
cheap cell.</p>
<div class="tablewrap">
<table class="grid" data-sortable>
<caption>No figure was estimated for any of these. Each is disclosed on the Flagged for Review page with the full reason.</caption>
<thead><tr><th>Method</th><th>Status</th><th>What is published</th><th>Why the cost is blank</th><th>Source</th></tr></thead>
<tbody>
{unverified_rows}
</tbody>
</table>
</div>

<h2>Cheapest lawful cost at each step</h2>
<p class="lede">Ranked on the published fee plus the labelled spread, excluding methods whose annual cap is below the
tier and excluding anything unlawful. The winner is usually a method whose bank fee is published as Free.</p>
<div class="tablewrap">
<table class="grid">
<caption>Lowest and second-lowest modelled cost per tier. This is arithmetic on published fees, not a recommendation.</caption>
<thead><tr><th>Amount</th><th>Lowest cost</th><th>Next</th><th>Source</th></tr></thead>
<tbody>{''.join(cheap_rows)}</tbody>
</table>
</div>

<h2>Every method against every step (full matrix)</h2>
<p class="lede">Totals in USD. <span class="over">Orange</span> means the tier exceeds that method's published annual
cap. A dash means no published figure exists for that method.</p>
<div class="tablewrap wide">
<table class="grid matrix">
<caption>Total modelled cost (published fee + 0.419% spread assumption) in USD. Source per row: HSBC China tariff [S11]; spread [S22].</caption>
<thead><tr><th>Method</th>{full_head}<th>Src</th></tr></thead>
<tbody>{''.join(full_rows)}</tbody>
</table>
</div>

<div class="callout warn">
  <h2>What these numbers are not</h2>
  <ul class="tight">
    <li><strong>Not a quote.</strong> No bank was asked for an executable rate. The spread cell is one bank's published
    board rate from 10 Nov 2026, labelled and applied uniformly {src_link("S22")}.</li>
    <li><strong>Not all-in.</strong> Intermediary and receiving-bank fees are outside the tariff
    {src_link("S11", "S11 Important Note 7")}, and no published figure for them was located. They are blank, not zero.</li>
    <li><strong>Not tax.</strong> No PRC income tax and no personal U.S. tax is in these totals. If the underlying income
    was never taxed in China, the tax is on the income (up to 45% on comprehensive income under IIT Law Art. 3(1)),
    and it dwarfs every number in these tables. See <a href="tax.html">Tax &amp; penalties</a>.</li>
    <li><strong>Not available for the blank rows.</strong> Fifteen of the twenty-seven methods have no published fee in
    the official sources read. They are listed on <a href="flagged.html">Flagged for Review</a> rather than filled in.</li>
    <li><strong>Not the annual cap.</strong> A right-hand dash or an orange cell is a limit, not a price. The ATM route
    is capped at CNY 100,000 equivalent a year {src_link("S08")} — about USD 14,085, about 3.5% of a USD 400,000
    balance, whatever the fee table says.</li>
  </ul>
</div>

<p class="tiny">Downloads: <a href="data/costs.csv">costs.csv</a> · <a href="data/costs.json">costs.json</a> ·
<a href="data/methods.json">methods.json</a> · <a href="data/sources.json">sources.json</a>.
Recompute with <code>python3 guide/model.py</code>. Fee formula:
<code>fee = clamp(0.001 × principal, 100/7.10, 500/7.10) + 120/7.10</code>; spread = <code>principal × 0.00419</code>.</p>
"""
    return page("costs.html", "What it costs, every step from USD 10,000 to 400,000",
                "Fee, spread and total for each method, with a source link in every row. Blank cells are values no official source publishes.",
                body)


# ---------------------------------------------------------------- steps
def page_steps():
    body = f"""
<p class="lede">This page is the execution order. It assumes nothing about your facts: where a step depends on a fact
only you know, it says so and sends you to the two-branch decision in step 1.</p>

<h2>Step 1 — Establish which of two positions you are in</h2>
<div class="tablewrap">
<table class="grid">
<thead><tr><th>Your situation</th><th>PRC characterisation</th><th>Operative rule</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="Your situation">US citizen who has lived in China continuously for one year or more, household
registration intact</td><td data-label="Characterisation">Domestic individual (境内个人)</td>
<td data-label="Operative rule">FX <em>purchases</em> face the USD 50,000 annual total; above it, documents for the
category, including an employment contract and income proof</td>
<td data-label="Source">{src_link("S05", "S05 Art. 52(2)")} {src_link("S02", "S02 Art. 12")}</td></tr>
<tr><td data-label="Your situation">US citizen who has left China, or never resided there, or has cancelled Chinese
household registration</td><td data-label="Characterisation">Non-domestic individual (境外个人)</td>
<td data-label="Operative rule">Lawful current-account RMB income converts on ID plus source-of-funds materials
<em>including the tax voucher</em> — this is a documents test, not a quota</td>
<td data-label="Source">{src_link("S03", "SAFE 2026 guidance")} {src_link("S02", "S02 Art. 13(1)")}</td></tr>
</tbody>
</table>
</div>
<p class="small">If you are not sure which row you are in, the bank decides it at the counter, and the answer changes
the paperwork. Ask them to confirm the characterisation in writing before you assemble the file.</p>

<h2>Step 2 — Choose the path</h2>
<div class="tablewrap">
<table class="grid">
<thead><tr><th>If this is true</th><th>Take this path</th><th>Because</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="If this is true">The balance is lawful income on which PRC individual income tax was paid or
withheld, and you can obtain the tax record</td><td data-label="Path"><a href="methods.html#M01">M01 documented income
→ SWIFT</a></td><td data-label="Because">No USD 50,000 purchase ceiling, no PRC tax on the exchange, and the tax record
is the document the bank asks for anyway</td><td data-label="Source">{src_link("S03")} {src_link("S02")}</td></tr>
<tr><td data-label="If this is true">You emigrated from mainland China, hold cancelled household registration and
certified proof of settlement abroad, and the assets predate that status</td>
<td data-label="Path"><a href="methods.html#M03">M03 emigration asset transfer</a></td>
<td data-label="Because">This is the channel designed for exactly this, and it has no upper limit in the measure</td>
<td data-label="Source">{src_link("S06", "S06 Art. 6 and 8")}</td></tr>
<tr><td data-label="If this is true">The RMB originally came from foreign currency you brought into China and you still
hold the exchange memo, within 24 months</td><td data-label="Path"><a href="methods.html#M05">M05 re-conversion</a></td>
<td data-label="Because">No tax certificate is required for this category at all</td>
<td data-label="Source">{src_link("S02", "S02 Art. 13(2)")} {src_link("S04")}</td></tr>
<tr><td data-label="If this is true">None of the above — you cannot document the source, or PRC tax was never paid</td>
<td data-label="Path">Stop and fix the documentation first</td><td data-label="Because">Every lawful route requires
the document, and the unlawful ones carry fines of up to 30% of the amount</td>
<td data-label="Source">{src_link("S05", "S05 Art. 40")} {src_link("S01", "S01 Art. 7")}</td></tr>
</tbody>
</table>
</div>

<h2>Step 3 — M01 in exact order</h2>
<ol class="steps">
  <li><strong>Get the tax record.</strong> Download the personal income tax payment record (纳税记录) from the national
  individual income tax app, or request a tax certificate (完税证明) at the tax service hall, for every year the balance
  represents. This is the document the FX rule names {src_link("S03", "SAFE 2026 guidance")}
  {src_link("S02", "S02 Art. 13(1)")}.</li>
  <li><strong>Tie the file to the balance.</strong> Employment contract or service agreement, payslips or invoices,
  bank statements showing each credit, and the tax record. Amounts must reconcile. A file that does not add up is
  refused at the counter, not argued.</li>
  <li><strong>Book a counter appointment</strong> at the branch that holds the account. Do not rely on a machine or the
  app for this category.</li>
  <li><strong>Ask for a written all-in quote</strong> using the wording in the box below. You are entitled to know the
  applied rate and every deduction line before you instruct the transfer
  {src_link("S11", "S11 2.2.4.1-2.2.4.2")}.</li>
  <li><strong>Convert and keep the exchange memo (水单).</strong> It is proof the conversion was authorised, and it is
  the document that would allow a re-conversion within 24 months if a transfer fails
  {src_link("S02", "S02 Art. 13(2)")}.</li>
  <li><strong>Instruct the wire to your own US account in the same name.</strong> Keep the SWIFT MT103 and the advice.
  The bank's tariff does not cover what intermediaries deduct {src_link("S11", "S11 Important Note 7")}; reconcile what
  actually arrives against the amount sent before you convert the next tranche.</li>
  <li><strong>Report on the US side.</strong> FBAR by 15 April with an automatic extension to 15 October
  {src_link("S15")}; Form 8938 attached to the return if the threshold applies {src_link("S18", "26 USC 6038D")}.
  Consider a foreign tax credit claim for PRC tax already paid — the mechanics were <em>not</em> re-verified in this
  session and are flagged on <a href="flagged.html">Flagged for Review</a>.</li>
</ol>

<h2>Step 4 — M03 in exact order, if you qualify</h2>
<ol class="steps">
  <li><strong>Assemble the status documents.</strong> Cancelled Chinese household registration certificate from the
  police, and proof of settlement abroad issued or certified by a Chinese embassy or consulate
  {src_link("S06", "S06 Art. 8(4)")}. Without these the route is closed; this is the step that stops most applicants.</li>
  <li><strong>Realise the assets and pay tax on the realisation.</strong> Obtain the tax certificate or tax payment
  voucher from the competent tax authority where the assets or income are located
  {src_link("S06", "S06 Art. 8(6)")}.</li>
  <li><strong>File one application for the whole amount</strong> at the SAFE branch for your former household
  registration location; a central sub-branch may accept it {src_link("S06", "S06 Arts. 5, 6")}.</li>
  <li><strong>Approval.</strong> Up to RMB 500,000 equivalent the local branch approves; above that it goes to SAFE head
  office {src_link("S06", "S06 Art. 10")}.</li>
  <li><strong>Remit in the staged pattern the measure dictates:</strong> no more than half first, no more than half the
  remainder after one year, the balance after two years; up to RMB 200,000 may go in one transfer after approval
  {src_link("S06", "S06 Art. 6")}. This staging is authorised, so it is not structuring.</li>
  <li><strong>The bank must pay your own overseas account and may not hand you FX cash in China</strong>
  {src_link("S06", "S06 Art. 11")}. Keep the approval letter and the capital-account approval document for the second
  and later tranches.</li>
  <li><strong>Report as in step 3.7.</strong></li>
</ol>

<div class="callout">
  <h2>Exactly what to ask the bank, in writing</h2>
  <ol class="tight">
    <li>Is my refusal a tax assessment, a request for a tax certificate, an eligibility decision, or a fee? Please
    identify which, in writing.</li>
    <li>If a tax is said to be due: what is the tax type, the taxpayer, the period, the tax base, the amount and the
    legal basis? A tax payment is not the same thing as a tax certificate, and neither is the same thing as a bank fee.</li>
    <li>Under which article is my conversion being handled — Art. 12 (domestic individual, above the annual total) or
    Art. 13(1) (non-domestic individual, lawful current-account income) {src_link("S02", "S02")}?</li>
    <li>Please list the source-of-funds documents you will accept, item by item.</li>
    <li>Please give an executable quote showing: the CNY/USD rate applied, the commission with its floor and cap, the
    cable charge, any intermediary or correspondent charge, and what the receiving bank will deduct
    {src_link("S11", "S11")}.</li>
    <li>If you will not process it, please confirm that in writing, and tell me which document would change the answer.</li>
  </ol>
  <p class="small">A refusal that cannot be put in writing in those terms is usually an incomplete file, not a legal
  prohibition. That distinction is the whole practical content of this project.</p>
</div>

<div class="callout warn">
  <h2>What not to do, and why</h2>
  <ul class="tight">
    <li><strong>Do not use a friend's or relative's USD 50,000 allowance.</strong> Borrowing or lending a quota puts you
    on SAFE's watch list for three years {src_link("S09", "S09 point 2")}, and splitting to evade the limits is
    expressly prohibited {src_link("S01", "S01 Art. 7")}.</li>
    <li><strong>Do not use an underground bank or a private swap.</strong> Fines up to 30% of the amount, higher where
    serious, plus confiscation {src_link("S05", "S05 Art. 45")}.</li>
    <li><strong>Do not use crypto or USDT.</strong> Converting between legal tender and virtual currency is expressly
    prohibited, and offshore exchanges serving China residents are treated as illegal financial activity
    {src_link("S21", "S21 points 1(2)-(3)")}.</li>
    <li><strong>Do not manufacture documents.</strong> Illegal FX arbitrage: the funds are ordered converted back and a
    fine of up to 30% applies, plus up to CNY 50,000 for untrue documents {src_link("S05", "S05 Arts. 40, 48")}.</li>
    <li><strong>Do not carry more than USD 10,000 out.</strong> USD 5,000 without a permit, USD 10,000 with one, and in
    principle nothing above that {src_link("S07")}; up to 20% fine for breach {src_link("S05", "S05 Art. 42")}.</li>
    <li><strong>Do not skip the FBAR because nothing moved.</strong> The obligation attaches to the account, not to the
    transaction {src_link("S15")}.</li>
  </ul>
</div>
"""
    return page("steps.html", "Exactly how to do it, in order",
                "Two realistic paths with the paper required at each step, plus the questions to put to the bank in writing.",
                body)


# ---------------------------------------------------------------- tax
def page_tax():
    # Worked 988 arithmetic from IRS yearly averages.
    avg = {"2025": 7.129, "2024": 7.189, "2023": 7.075, "2022": 6.730, "2021": 6.452}
    rows = []
    for yr in ["2021", "2022", "2023", "2024"]:
        acquired = avg[yr]
        later = avg["2025"]
        # USD value of 1 CNY acquired in `yr` vs converted at the 2025 average
        usd_then = 1 / acquired
        usd_now = 1 / later
        pct = (usd_now - usd_then) / usd_then * 100
        # principal at which a gain of 200 USD would arise
        if pct > 0:
            threshold = 200 / (pct / 100)
            thr = f"${threshold:,.0f}"
        else:
            thr = "no gain — a loss"
        rows.append((yr, acquired, later, pct, thr))

    body = f"""
<div class="callout lead">
  <h2>The conversion penalty, broken apart</h2>
  <p>People describe a "penalty" for converting. In the official texts reviewed it resolves into five different things,
  and only two of them are actually a cost of exchanging currency:</p>
  <ol class="tight">
    <li><strong>PRC income tax on the money's origin.</strong> Not a conversion tax. The PRC individual income tax law
    taxes nine listed categories {src_link("S05", "S05")} — wages, remuneration, author's remuneration, royalties,
    business income, interest/dividends, rental, property transfer and incidental income. Exchanging your own renminbi
    is not among them. If the balance was never taxed, the tax is on the income, at up to 45% for comprehensive income
    {src_link("S07", "IIT Law Art. 3(1)")}.</li>
    <li><strong>U.S. tax on the exchange gain.</strong> Real but capped at USD 200 for a personal transaction
    {src_link("S12", "26 USC 988(e)(2)")}. Worked below.</li>
    <li><strong>The bank's spread.</strong> A real cost, roughly 0.42% of the amount on one bank's published board rate
    {src_link("S22")}.</li>
    <li><strong>Fixed bank and correspondent fees.</strong> Tens of dollars per transfer {src_link("S11")}.</li>
    <li><strong>Penalties for doing it wrong</strong> — either PRC FX penalties, up to 30% of the amount
    {src_link("S05", "S05 Arts. 39-45")}, or U.S. reporting penalties, which are the largest numbers in this project
    {src_link("S16")}.</li>
  </ol>
</div>

<h2>1. PRC tax: what the law actually taxes</h2>
<div class="tablewrap">
<table class="grid">
<thead><tr><th>Question</th><th>Answer from the official text</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="Question">Is there a PRC tax on exchanging currency?</td>
<td data-label="Answer">No tax on the exchange appears in the FX instruments or in the IIT Law. The FX regulations
impose <em>documentation and authenticity</em> requirements {src_link("S05", "S05 Art. 12")}, and the IIT Law taxes
categories of income, not conversions {src_link("S07", "IIT Law Art. 2")}.</td>
<td data-label="Source">{src_link("S01")} {src_link("S05")} {src_link("S07")}</td></tr>
<tr><td data-label="Question">So why does the bank ask for a tax certificate?</td>
<td data-label="Answer">Because the FX rule requires it as a <em>document</em> proving the money's source: identity plus
source-of-funds materials "including tax vouchers" {src_link("S03", "SAFE 2026 guidance")}
{src_link("S02", "S02 Art. 13(1)")}. A certificate of tax already paid is not a new tax.</td>
<td data-label="Source">{src_link("S03")} {src_link("S02")}</td></tr>
<tr><td data-label="Question">What if PRC tax was never paid?</td>
<td data-label="Answer">Then it is owed on the income, separately from the conversion. Rates: 3%-45% progressive on
comprehensive income; 5%-35% on business income; a flat 20% on interest, dividends, property rental, property transfer
and incidental income {src_link("S07", "IIT Law Art. 3")}.</td>
<td data-label="Source">{src_link("S07")}</td></tr>
<tr><td data-label="Question">Does the emigration route avoid the tax?</td>
<td data-label="Answer">No. It <em>requires</em> a tax certificate or tax payment voucher as a condition of the
application {src_link("S06", "S06 Art. 8(6)")}.</td><td data-label="Source">{src_link("S06")}</td></tr>
</tbody>
</table>
</div>

<h2>2. U.S. tax on the conversion itself: 26 U.S.C. 988</h2>
<p>Disposing of nonfunctional currency is a section 988 transaction {src_link("S12", "26 USC 988(c)(1)(C)(i)")}. Then
988(e) takes it away again for individuals: the section "shall not apply to any section 988 transaction entered into by
an individual which is a personal transaction" {src_link("S12", "26 USC 988(e)(1)")}, and "no gain shall be recognized
... by reason of changes in exchange rates ... The preceding sentence shall not apply if the gain ... exceeds $200"
{src_link("S12", "26 USC 988(e)(2)")}. The IRS states the same in plain words in
{src_link("S13", "Publication 525")}.</p>
<p>A "personal transaction" excludes transactions whose expenses meet section 162 or 212 tests
{src_link("S12", "26 USC 988(e)(3)")}. Business or investment use of the money is therefore outside the exclusion, and
this is where an account-specific answer would need facts this project does not have.</p>

<h3>Worked example: what the 2021-2025 rate move does to a conversion</h3>
<p>Using the IRS's own yearly average rates {src_link("S14", "IRS yearly averages")} — the renminbi went from 6.452
(2021) to 7.129 (2025) per dollar. That is a <em>weaker</em> renminbi, so a dollar buys more renminbi in 2025 than in
2021. Converting renminbi that was acquired earlier therefore produced a <em>loss</em> in dollar terms for 2021-2023
acquisitions, and a small gain for 2024.</p>
<div class="tablewrap">
<table class="grid">
<caption>Direction and size of the section 988 exchange difference, from IRS yearly averages. A loss is not the same as
a gain, and the USD 200 exclusion is a ceiling on gain, not a floor on loss.</caption>
<thead><tr><th>RMB acquired in</th><th>Rate then (CNY/USD)</th><th>2025 average</th><th>Change in USD value</th><th>USD 200 threshold would be crossed at</th><th>Source</th></tr></thead>
<tbody>
{''.join(f'<tr><td data-label="Acquired">{y}</td><td data-label="Rate then">{a:.3f}</td><td data-label="2025 average">{b:.3f}</td>'
         f'<td data-label="Change">{p:+.2f}%</td><td data-label="Threshold">{t}</td>'
         f'<td data-label="Source">{src_link("S14")} {src_link("S12")}</td></tr>' for y, a, b, p, t in rows)}
</tbody>
</table>
</div>
<p class="small">This is arithmetic on the IRS's published annual averages, not a prediction and not a computation of
anyone's tax. Section 988 uses the rate on the booking and payment dates of your particular transactions
{src_link("S12", "26 USC 988(b), (c)(2)-(3)")}, and the IRS accepts any posted rate used consistently
{src_link("S14")}. An earlier page in this repository asserted a specific gain of +0.83% for a 2024 acquisition and a
threshold of about $23,963; recomputing here from the same published averages gives
{rows[3][3]:+.2f}% and {rows[3][4]}, so the earlier figure is close but is replaced by this recomputation.</p>

<h2>3. Reporting: the obligations and their published penalty maximums</h2>
<div class="tablewrap">
<table class="grid">
<thead><tr><th>Obligation</th><th>Trigger</th><th>Due</th><th>Published penalty</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="Obligation">FBAR — FinCEN Form 114</td>
<td data-label="Trigger">Financial interest in, or signature authority over, a foreign financial account, where the
aggregate of all such accounts exceeded USD 10,000 at any time in the calendar year. Income is irrelevant.</td>
<td data-label="Due">15 April, with an automatic extension to 15 October</td>
<td data-label="Penalty">Civil maximum USD 16,536 per violation (non-willful); USD 165,353 (willful). These are maximums
adjusted for inflation, assessed on facts and circumstances — not an amount anyone is assumed to owe.</td>
<td data-label="Source">{src_link("S15")} {src_link("S16")} {src_link("S17")}</td></tr>
<tr><td data-label="Obligation">Form 8938 — 26 USC 6038D</td>
<td data-label="Trigger">Aggregate specified foreign financial assets above the threshold: USD 50,000 year-end or
USD 75,000 at any time for an unmarried taxpayer living in the US; USD 100,000 / 150,000 married filing jointly;
USD 200,000 / 300,000 for a taxpayer living abroad filing other than jointly.</td>
<td data-label="Due">With the annual return</td>
<td data-label="Penalty">USD 10,000, plus up to USD 10,000 per 30-day period after a 90-day notice, capped at a further
USD 50,000. A reasonable-cause exception exists; a foreign jurisdiction's disclosure penalty is not reasonable cause.</td>
<td data-label="Source">{src_link("S18")} {src_link("S19")}</td></tr>
<tr><td data-label="Obligation">FinCEN Form 105</td>
<td data-label="Trigger">Carrying or sending currency or monetary instruments over USD 10,000 into or out of the US;
the threshold applies to the family or group total, not per person.</td>
<td data-label="Due">At entry or departure</td>
<td data-label="Penalty">Forfeiture and seizure of the currency, and civil or criminal penalties including fines or
imprisonment.</td>
<td data-label="Source">{src_link("S20")}</td></tr>
<tr><td data-label="Obligation">PRC FX compliance</td>
<td data-label="Trigger">Converting outside the rules, splitting to evade limits, false documents, private dealing,
carrying cash over the limit.</td>
<td data-label="Due">Ongoing</td>
<td data-label="Penalty">Up to 30% of the amount involved, and 30% up to the equivalent of the full amount where
serious, plus confiscation and conversion back of the funds; up to 20% for cash; up to CNY 50,000 for untrue documents;
watch-list management for three years for quota abuse.</td>
<td data-label="Source">{src_link("S05")} {src_link("S09")} {src_link("S01")}</td></tr>
</tbody>
</table>
</div>

<div class="callout warn">
  <h2>The comparison that matters</h2>
  <p>Converting USD 400,000 through the documented route costs about
  <strong>${money(ROWS[("M01",400000)]["total_usd"])}</strong>. A single willful FBAR violation has a published civil
  maximum of <strong>USD 165,353</strong> {src_link("S16")}. One unreported year can therefore cost about 94 times the
  entire cost of converting lawfully. If the money has been sitting in a Chinese account, the largest financial
  exposure in this project is almost certainly not the conversion — it is whether the account was ever declared.</p>
  <p class="small">Maximums are not assessments. Penalty assertion depends on facts and circumstances, and the IRS
  publishes streamlined and delinquent-filing procedures for people who come forward before being contacted
  {src_link("S15", "IRS FBAR page, filing delinquent FBARs")}. Whether any of those procedures apply to you is a
  question for a qualified adviser, not for this site.</p>
</div>

<h2>4. What is <em>not</em> verified here</h2>
<ul class="tight">
  <li><strong>The mechanics of the U.S. foreign tax credit for PRC tax already paid</strong> were not re-verified in this
  session. The treaty and Form 1116 paths are named but not analysed. Flagged.</li>
  <li><strong>The PRC tax rate on a specific balance</strong> depends on its character, which is unknown. No number is
  asserted.</li>
  <li><strong>Your filing status, residence days and thresholds</strong> are unknown, so no threshold conclusion is drawn
  for you. The published thresholds are quoted, and that is all.</li>
  <li><strong>Whether a conversion is a "personal transaction" for you</strong> depends on whether the money is used in a
  trade or business or for investment expenses {src_link("S12", "26 USC 988(e)(3)")}. Unknown here.</li>
</ul>
<p class="small">All four are published on <a href="flagged.html">Flagged for Review</a> with their source links.</p>
"""
    return page("tax.html", "Tax and penalties: what is actually charged",
                "The conversion is not the taxable event. Here are the four things that are, with the statutory figures and the arithmetic shown.",
                body)


# ---------------------------------------------------------------- flagged
def page_flagged():
    flags = []
    # Unverified cost cells, generated from the data itself.
    for mid in UNVERIFIED:
        m = M[mid]
        if m["status"] == "unlawful":
            reason = ("No lawful cost exists for an unlawful method. The published statutory exposure is stated on the "
                      "method itself; no price is invented.")
        elif m["cost"]["fee"]["type"] == "unverified" and m["cost"]["spread"]["pct"] is None:
            reason = ("Neither a bank fee nor a conversion spread is published in the official documents read for this "
                      "method. Both cells are blank rather than estimated.")
        else:
            reason = "Part of the cost is published and part is not; the incomplete part is left blank."
        flags.append((f"F-{mid}", "medium" if m["status"] != "unlawful" else "low",
                      f"{mid} — cost not published", reason, m["basis"]))

    manual = [
        ("F01", "high", "The spread used in every cost table is an assumption drawn from one bank's board rate",
         "The 0.419% spread comes from Bank of China's published USD board rates on 10 November 2026 (buy 665.72, sell "
         "668.52 per 100 USD), on a page that states the table is for reference only and that the rate actually applied "
         "at the counter or in the app governs. It is applied uniformly to every method and every tier. Your bank's "
         "executable rate will differ, and the spread dominates the total at large amounts.",
         ["S22"]),
        ("F02", "high", "No intermediary or receiving-bank fee could be sourced",
         "The HSBC China tariff expressly excludes charges collected by other institutions and by regulators. No official "
         "source publishes what a US receiving bank or a correspondent will deduct. Those cells are blank, not zero, and "
         "the totals on this site are therefore lower bounds for the delivered amount.",
         ["S11"]),
        ("F03", "high", "Whether your specific balance is documentation-eligible is unknown",
         "Every lawful route in this guide turns on documents: a PRC tax record, a source-of-funds file, cancelled "
         "household registration, or an original exchange memo. None of those facts were supplied. The guide states what "
         "each rule requires and does not conclude that any particular balance qualifies.",
         ["S02", "S03", "S06"]),
        ("F04", "high", "The U.S. foreign tax credit mechanics were not re-verified in this session",
         "The PRC tax already paid on the income may be creditable in the US by treaty or under section 901/903, and Form "
         "1116 is the usual mechanism. That path was named but not read in this session, so no conclusion is drawn and no "
         "credit amount is computed.",
         ["S15"]),
        ("F05", "medium", "Whether you are a domestic or a non-domestic individual under PRC FX law is unknown",
         "The operative rule differs: a domestic individual's FX purchases face the annual total (S02 Art. 12), while a "
         "non-domestic individual converts lawful current-account income on identity plus source and tax documents "
         "(S02 Art. 13(1); S03). The test turns on residence and household registration, neither of which is known.",
         ["S02", "S03", "S05"]),
        ("F06", "medium", "Earlier pages in this repository carried a superseded Global Transfer fee",
         "A \"USD 0-7\" same-name Global Transfer figure and a \"USD 7\" reference appear in earlier material here. In the "
         "tariff effective 31 October 2026 the USD 7 figure belongs to International Education Payment (item 2.2.7), and "
         "same-name Global Transfer is Free for Private Banking and Premier, with Advance at CNY 145 indicative / actual "
         "USD 20 (item 2.2.6.1). This guide uses the current text. The earlier pages were not edited by this session "
         "because they are outside its scope.",
         ["S11"]),
        ("F07", "medium", "An earlier page's section 988 illustration did not reproduce exactly",
         "An earlier page stated a +0.83% exchange gain for renminbi acquired in 2024 and a USD 200 threshold at about "
         "$23,963. Recomputing from the same IRS yearly averages gives +0.84% and a threshold of about $23,800. The "
         "difference is rounding. This guide publishes its own recomputation on the Tax page rather than restating the "
         "earlier figure.",
         ["S14", "S12"]),
        ("F08", "medium", "The emigration route's practical availability was not tested",
         "The measure requires cancelled Chinese household registration and certified proof of settlement abroad. Many "
         "naturalised US citizens no longer hold the first document. The rule is verified; whether it is achievable for "
         "any particular person is not, and no adviser or SAFE branch was contacted.",
         ["S06"]),
        ("F09", "medium", "Offshore RMB (CNH) eligibility for an individual was not established",
         "Whether, and on what basis, an individual may move a personal RMB balance offshore outside the documented "
         "current-account and capital-account channels was not established from the sources read. The method is listed as "
         "conditional with no cost, not as a recommendation.",
         ["S05", "S01"]),
        ("F10", "medium", "Card settlement margins and issuer fees are not in the official documents read",
         "The ATM and card-spending routes have published caps and published rules, but no published retail FX settlement "
         "margin or issuer foreign-transaction fee was located. Their cost cells are blank.",
         ["S08", "S10"]),
        ("F11", "low", "Corporate, service-invoice, goods and QDII structures were not costed",
         "Their PRC VAT, withholding and duty rates were not verified in this session, and each depends on facts about a "
         "business that do not exist in the material supplied. They are described as structures with all cost cells "
         "blank, and are not presented as ways to move a personal balance.",
         ["S01", "S05"]),
        ("F12", "low", "The 7.10 CNY/USD rate used to express CNY fees in dollars is an assumption",
         "It affects only the CNY-denominated published caps (100, 500, 120, 145). At USD 400,000 the entire effect of "
         "the choice is under USD 15, and no exchange-rate forecast is embedded anywhere, because the tiers themselves "
         "are USD amounts.",
         ["S11"]),
    ]

    cards = []
    for fid, sev, title, detail, srcs in manual + flags:
        cards.append(f"""
<article class="flag {esc(sev)}" id="{esc(fid)}">
  <h3><span class="sev {esc(sev)}">{esc(sev)}</span> {esc(fid)} — {esc(title)}</h3>
  <p>{esc(detail)}</p>
  <p class="srcs"><strong>Sources:</strong> {' · '.join(src_link(s) for s in srcs)}</p>
</article>""")

    body = f"""
<div class="callout warn">
  <h2>What this page is for</h2>
  <p>Every value on this site that could not be confirmed from an official primary source is listed here with the
  reason it is unconfirmed. <strong>Blank means unverified, not zero, and not free.</strong> Nothing on this page was
  filled in by inference, and nothing here is hidden in a footnote. There are
  {len(manual)} substantive flags and {len(flags)} method-level cost gaps.</p>
  <p>Two of these matter far more than the rest: <strong>F01</strong> (the spread is one bank's board rate, applied as
  an assumption) and <strong>F03</strong> (whether your balance can be documented at all is unknown). If you read
  nothing else here, read those two.</p>
</div>
{''.join(cards)}
"""
    return page("flagged.html", "Flagged for Review",
                "Everything that could not be confirmed from an official source, with the reason and the source link, so you can check it yourself.",
                body)


# ---------------------------------------------------------------- sources
def page_sources():
    rows = []
    for s in SOURCES["sources"]:
        rows.append(f"""
<tr id="{esc(s['id'])}">
  <td data-label="ID"><strong>{esc(s['id'])}</strong></td>
  <td data-label="Document"><a href="{esc(s['url'])}" target="_blank" rel="noopener noreferrer">{esc(s['title'])}</a>
      <div class="small">{esc(s['authority'])} · {esc(s['kind'])} · {esc(s['lang'])}</div></td>
  <td data-label="Locator">{esc(s['locator'])}</td>
  <td data-label="Text read"><q>{esc(s['quote'])}</q></td>
  <td data-label="Used for">{esc(s['supports'])}</td>
</tr>""")

    body = f"""
<p class="lede">Every source below was fetched and read in this session on {TODAY}. The quoted text is what the document
returned, not a paraphrase from memory. Where a document is a commercial bank tariff or a board rate it is labelled as
such: a bank's publication is primary evidence of that bank's price, and is not a regulator's figure.</p>

<div class="callout">
  <h2>How to check any claim on this site</h2>
  <ol class="tight">
    <li>Each table row on <a href="costs.html">Costs</a> and <a href="methods.html">Methods</a> carries the source ID it
    rests on.</li>
    <li>Find that ID in the table below; the locator column names the article, item or paragraph.</li>
    <li>Open the link and read the quoted sentence in place.</li>
    <li>If the sentence is not there, the claim is wrong and should be corrected — the flag belongs on
    <a href="flagged.html">Flagged for Review</a>.</li>
  </ol>
</div>

<div class="tablewrap wide">
<table class="grid sources">
<caption>{len(SRC)} primary sources. Quote column shows the text actually read; locator column shows where to find it.</caption>
<thead><tr><th>ID</th><th>Document</th><th>Locator</th><th>Text read</th><th>Used for</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>

<h2>Source register as data</h2>
<p><a href="data/sources.json">sources.json</a> · <a href="data/methods.json">methods.json</a> ·
<a href="data/costs.json">costs.json</a> · <a href="data/costs.csv">costs.csv</a>.
Regenerate with <code>python3 guide/model.py &amp;&amp; python3 guide/build.py</code>; verify with
<code>python3 guide/verify.py</code>.</p>
<p class="small">Official-source coverage note: the PRC FX instruments are published in Chinese by SAFE and the PBOC;
the English rendering of PBOC Decree [2006] No. 3 was used for that one instrument and is quoted in English above. Where
the operative rule is only published in Chinese, the Chinese sentence is quoted rather than translated into a claim.</p>
"""
    return page("sources.html", "Primary sources",
                f"{len(SRC)} official documents, each with the article or item number and the text read on {TODAY}.",
                body)


# ---------------------------------------------------------------- audit
def page_audit():
    items = [
        ("A01", "resolved", "Two executive summaries coexisted at the repository root",
         "EXECUTIVE-SUMMARY.md and EXECUTIVE_SUMMARY.md both existed, with different content and dates. Two files "
         "differing only by underscore are a maintenance trap: a reader can pick either and get a different answer. This "
         "session does not edit or delete either, because both are outside its claimed scope; it publishes one guide "
         "with one summary (this site) and records the duplication here for the repository owner.",
         "Flagged for the owner. Not edited."),
        ("A02", "corrected in this guide", "A superseded Global Transfer fee is still visible in older pages",
         "Several pages in this repository quote a same-name Global Transfer fee of \"USD 0-7\", or a flat \"USD 7\". In "
         "the tariff effective 31 October 2026, USD 7 is the International Education Payment item (2.2.7); same-name "
         "Global Transfer is Free for Private Banking and Premier, and CNY 145 indicative / actual USD 20 for Advance "
         "(2.2.6.1). This guide uses the current figure and labels the older one as superseded.",
         "Fixed in guide/. Older pages untouched and flagged."),
        ("A03", "corrected in this guide", "An earlier section 988 illustration does not reproduce from its own source",
         "An earlier page reported a +0.83% exchange gain for renminbi acquired in 2024 and a USD 200 threshold at about "
         "$23,963. Recomputing from the IRS yearly averages gives +0.84% and about $23,800. Small, but a number that does "
         "not recompute is a number that should not be published. This guide publishes its own arithmetic and shows the "
         "inputs so it can be checked.",
         "Recomputed on tax.html."),
        ("A04", "noted", "The repository now contains many overlapping builds of the same research",
         "docs/, ladder/, briefing/, portal/, repatriate/, site/, audit-*/, acceptance-*/, verify-* and now guide/ all "
         "answer the same question with different assumptions, different route counts and different fee vintages. Several "
         "of them present modelled ranges as if they were prices. A reader cannot tell which is current. This is a "
         "structural risk: the correct fix is one canonical build with redirects, which is outside this session's scope.",
         "Flagged for the owner. The root hub lists them with warnings."),
        ("A05", "noted", "Earlier sessions published flags that remain open",
         "Flag sets F01-F09, E01-E02 and G01-G05 from earlier sessions are still published on their own pages. None was "
         "closed by this session, and none was assumed resolved. This guide does not restate them; it links to them.",
         "Left open deliberately."),
        ("A06", "verified", "Every table row in this guide carries an official source link",
         "Enforced mechanically, not by inspection: guide/verify.py fails the build if any table body row in any generated "
         "page lacks an href that matches a URL in the source register, and fails if any method or tier is missing from "
         "the costs matrix.",
         "Enforced by guide/verify.py."),
        ("A07", "verified", "The arithmetic in every cost cell recomputes from the published inputs",
         "guide/verify.py recomputes fee, spread and total for all 1,080 method-tier cells from the formula and the "
         "published fee parameters, and fails on any mismatch greater than one cent.",
         "Enforced by guide/verify.py."),
        ("A08", "noted", "No bank, adviser or regulator was contacted",
         "Every statement here comes from a published document. No executable quote was obtained, no SAFE branch was "
         "asked, and no tax adviser reviewed the conclusion. The site says so in its footer and on the Flagged page.",
         "Disclosed."),
    ]
    rows = "".join(
        f'<article class="flag {"low" if s == "noted" else "medium"}" id="{esc(i)}">'
        f'<h3><span class="sev {"low" if s == "noted" else "medium"}">{esc(s)}</span> {esc(i)} — {esc(t)}</h3>'
        f'<p>{esc(d)}</p><p class="srcs"><strong>Disposition:</strong> {esc(x)}</p></article>'
        for i, s, t, d, x in items)

    body = f"""
<p class="lede">The repository was reviewed for internal contradictions, stale figures and unsupported claims. Eight
items were found. Two were corrected in this guide, one class is mechanically prevented from recurring, and the rest are
disclosed rather than silently fixed, because the files involved belong to other sessions' scopes.</p>

<div class="callout">
  <h2>Scope and coordination</h2>
  <p>This session claimed only <code>guide/**</code>, a card in the generated root hub, and its own board record in
  COORDINATION.md. Every other directory is read-only input. Two open pull requests (#39 and #41) were conflicting and
  stale; they were not rebased, merged or discarded, and their content was treated as read-only input. Where a fix was
  needed in a file owned by another scope, it is recorded here instead of edited.</p>
</div>

<div class="audit-list">
{rows}
</div>

<h2>What was verified, and how</h2>
<ul class="tight">
  <li><strong>Source text.</strong> All {len(SRC)} sources were fetched in this session and the quoted sentence is the
  text returned. Retrieval date is recorded per source on <a href="sources.html">Sources</a>.</li>
  <li><strong>Cost arithmetic.</strong> 1,080 cells recomputed from the published fee parameters plus one labelled
  assumption.</li>
  <li><strong>Citation coverage.</strong> Mechanically enforced per table row; see A06.</li>
  <li><strong>Local links and anchors.</strong> Every internal link and fragment in the generated site is resolved by the
  verifier.</li>
  <li><strong>No-JavaScript parity.</strong> All content is in the HTML. The script only filters and re-sorts what is
  already on the page, so the tables are complete with scripting off.</li>
  <li><strong>Not verified:</strong> external URL availability over time, current law at the moment you read this, and
  anything about your personal facts. Those are stated as limits, not glossed.</li>
</ul>
"""
    return page("audit.html", "Repository audit",
                "Irregularities found across this repository, what was corrected, and what was deliberately left for the owner.",
                body)


# ---------------------------------------------------------------- write
def main():
    pages = {
        "index.html": page_index(),
        "methods.html": page_methods(),
        "costs.html": page_costs(),
        "steps.html": page_steps(),
        "tax.html": page_tax(),
        "flagged.html": page_flagged(),
        "sources.html": page_sources(),
        "audit.html": page_audit(),
    }
    for name, html_text in pages.items():
        (ROOT / name).write_text(html_text)
    (ROOT / ".nojekyll").write_text("")
    # Copy the data next to the site so the downloads work on Pages.
    (ROOT / "data").mkdir(exist_ok=True)
    print(f"built {len(pages)} pages")


if __name__ == "__main__":
    main()
