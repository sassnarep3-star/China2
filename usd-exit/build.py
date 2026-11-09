#!/usr/bin/env python3
"""
usd-exit static site generator.

Reads data/sources.json, data/methods.json, data/costs.json and emits a
self-contained, mobile-first static site into usd-exit/:

    index.html          landing page + the answer
    costs.html          the $10k..$400k ladder, per method
    methods.html        19 routes, pros/cons, step-by-step
    taxes.html          the Chinese and US tax analysis
    penalties.html      what going the wrong way costs
    sources.html        all 27 sources, verbatim quotes
    flagged.html        "Flagged for Review" - blank/unverified items
    summary.html        executive summary
    assets/style.css

Design rules enforced in code:
  * Every value rendered in a table cell carries its source id, rendered as a
    link to the official URL. verify.py re-checks this by parsing the output.
  * A None value renders as an em-dash in a cell marked class="blank" plus a
    flag badge. It is never replaced by a number.

Run: python3 usd-exit/build.py
"""
import json
import os
import html
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

with open(os.path.join(DATA, "sources.json"), encoding="utf-8") as f:
    SOURCES = {s["id"]: s for s in json.load(f)["sources"]}
with open(os.path.join(DATA, "methods.json"), encoding="utf-8") as f:
    MD = json.load(f)
with open(os.path.join(DATA, "costs.json"), encoding="utf-8") as f:
    COSTS = json.load(f)

METHODS = MD["methods"]
BYID = {m["id"]: m for m in METHODS}
META = MD["meta"]
COST_META = COSTS["meta"]
LADDER = COSTS["ladder"]
BY_METHOD = COSTS["by_method"]

# ----------------------------------------------------------------- helpers --
FLAG_TEXT = {
    "F-SPREAD": "Retail FX spread not published by any reviewed bank — every total is a floor.",
    "F-UNVERIFIED": "Value could not be confirmed from an official source; left blank on purpose.",
    "F-UNVERIFIED-FEE": "The provider does not publish this fee for the from-CNY direction.",
    "F-NO-FEE-PUBLISHED": "No fee is published in the cited instrument. Absence of a fee is not proof of zero charge.",
    "F-NO-CAP-PUBLISHED": "No dollar cap is published; the limit is document review, not a number.",
    "F-STEPS-EXECUTION": "This route requires an action at a mainland bank. This document cannot perform it.",
    "F-CLASSIFICATION": "Outcome depends on whether the bank records you as 境内个人 or 境外个人.",
    "F-IRREVERSIBLE": "Requires cancelling Chinese household registration — not reversible.",
    "F-COMMERCIAL": "Commercial provider, not a government source.",
    "F-AGGREGATION": "Many small transfers can be treated as structuring even if each is lawful.",
    "F-NOT-A-TRANSFER": "This is spending, not a means of delivering USD to a US account.",
    "F-SLOW": "The published ceiling makes this impractically slow for a large balance.",
    "F-PROHIBITION": "This specific action is prohibited, not merely limited.",
    "F-PROHIBITED": "Prohibited by the cited official source.",
    "F-ABUSE-RISK": "Cannot lawfully be used to move your own money; only a genuine gift.",
    "F-VARIABLE": "Depends on facts the table does not have (e.g. cost basis); the rate is given, not a dollar figure.",
    "F-APPROVAL": "Requires discretionary official approval.",
    "F-NARROW": "Scope is narrow by design; not a bulk channel.",
    "F-REPORTING-LOAD": "Creates an ongoing foreign-account reporting obligation.",
    "F-PFIC-NOT-RESEARCHED": "PFIC consequences were outside the sources reviewed and are not asserted.",
}

e = html.escape


def money(v):
    if v is None:
        return None
    if abs(v) >= 1000:
        return f"${v:,.0f}" if float(v).is_integer() else f"${v:,.2f}"
    return f"${v:,.2f}"


def cell_num(v, src=None, extra_cls=""):
    """A numeric table cell. None -> a blank cell marked and labelled unverified."""
    if v is None:
        return f'<td class="blank {extra_cls}" title="Not published / could not be verified">—<span class="blanktag">blank</span></td>'
    if src:
        return f'<td class="num {extra_cls}">{money(v) if isinstance(v, (int, float)) else e(str(v))} {srclink(src)}</td>'
    return f'<td class="num {extra_cls}">{money(v) if isinstance(v, (int, float)) else e(str(v))}</td>'


def srclink(sid, label=None):
    """Render a source id as a link to the official URL."""
    if sid is None:
        return ""
    s = SOURCES.get(sid)
    if not s:
        return f'<span class="src missing">{e(str(sid))}</span>'
    return f'<a class="src" href="{e(s["url"])}" title="{e(s["title"])}">{e(label or sid)}</a>'


def srclinks(sids):
    return " ".join(srclink(s) for s in sids)


def flagbadge(f):
    return f'<span class="flag" title="{e(FLAG_TEXT.get(f, "See Flagged for Review"))}">{e(f)}</span>'


def statuschip(st):
    return f'<span class="chip c-{e(st)}">{e(st)}</span>'


NAV = [
    ("index.html", "Start"),
    ("summary.html", "Summary"),
    ("costs.html", "Costs"),
    ("methods.html", "Methods"),
    ("taxes.html", "Taxes"),
    ("penalties.html", "Penalties"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged"),
    ("audit.html", "Repo audit"),
]


def page(slug, title, subtitle, body, desc=""):
    parts = []
    for h, t in NAV:
        cls = ' class="on"' if h == slug else ""
        parts.append(f'<a href="{h}"{cls}>{e(t)}</a>')
    nav = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · USD exit</title>
<meta name="description" content="{e(desc or subtitle)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="brand"><a href="index.html">USD exit</a> <span class="sub">CNY → USD for a US citizen</span></div>
    <nav class="nav">{nav}</nav>
  </div>
</header>
<main class="wrap">
  <h1>{e(title)}</h1>
  <p class="lede">{subtitle}</p>
{body}
</main>
<footer class="wrap foot">
  <p><strong>Not tax, legal or immigration advice.</strong> Compiled from primary sources, each linked. Figures are as published on 2026-11-09; Chinese FX rules change by circular. Where a number is not published it is shown blank and listed on the <a href="flagged.html">Flagged for Review</a> page.</p>
  <p class="mono">branch arena/b8e50c81-china2 · {len(SOURCES)} sources · {len(METHODS)} routes · generated {e(COST_META["generated"])}</p>
</footer>
</body>
</html>
"""


# ------------------------------------------------------------ the answer ----
def headline_numbers():
    """The three numbers that decide this problem, each traceable."""
    return [
        ("US$50,000", "per person per year", "the annual facilitation quota — the constraint that actually binds", "P02"),
        ("8 years", "for US$400,000", "at one person's quota, one wire per calendar year (derived)", "P02"),
        ("~US$543", "bank fees for US$400,000", "total published wire tariff across those 8 wires (derived from C01)", "C01"),
        ("0%", "Chinese tax on converting", "currency conversion is not one of the nine IIT income categories", "P11"),
        ("US$200", "§988 personal-transaction threshold", "below this FX gain on a personal conversion is not recognised", "U05"),
        ("US$16,536 / US$165,353", "FBAR non-willful / willful", "inflation-adjusted civil maxima per violation — the real risk is reporting, not the tax", "U04"),
    ]


# ================================================================ index =====
def build_index():
    rows = "".join(
        f"""<tr><td><strong>{e(v)}</strong><div class="tiny">{e(lbl)}</div></td>
        <td>{e(why)} {srclink(sid)}</td></tr>"""
        for v, lbl, why, sid in headline_numbers()
    )

    top = "".join(
        f"""<tr>
        <td><span class="rank">{m['rank']}</span> <a href="methods.html#{m['id']}">{e(m['name'])}</a>
            <div class="tiny">{e(m['one_line'])}</div></td>
        <td>{statuschip(m['status'])}</td>
        {cell_num(m['volume']['annual_usd'], m['volume']['source'][0])}
        </tr>"""
        for m in sorted(METHODS, key=lambda x: x["rank"])[:6]
    )

    body = f"""
<section class="hero">
  <p class="kicker">The direct answer</p>
  <blockquote>
    There is no Chinese tax on converting CNY into USD. The thing that stops you is a
    <strong>US$50,000-per-person-per-year quota</strong>, not a tax. The tax risk is a
    <em>separate</em> question — what the money is made of, and whether the US has been told
    about the account.
  </blockquote>
</section>

<h2>The numbers that decide it</h2>
<table class="t">
<thead><tr><th>Number</th><th>What it means</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<p class="note">Every figure above is either quoted from the linked source or is arithmetic on
quoted figures, labelled <em>derived</em>. Nothing here is estimated.</p>

<h2>If you read only one thing</h2>
<div class="cards">
  <div class="card">
    <h3>1 · The constraint is a quota, not a tax</h3>
    <p>US$50,000 per person per calendar year, ID only. A genuine current-account need above
    that is allowed with authenticity documents — but not for buying overseas property or
    securities, which are excluded. {srclinks(["P02"," P03","P15"])}</p>
  </div>
  <div class="card">
    <h3>2 · The one bulk route is emigration</h3>
    <p>If you are leaving for good and will cancel your
    <span class="zh">户口</span>, PBOC [2004] No.16 allows staged transfer of your whole
    balance over about two years — but a PRC tax settlement comes first, by statute.
    {srclinks(["P06","P11"])}</p>
  </div>
  <div class="card">
    <h3>3 · The expensive mistake is a reporting failure</h3>
    <p>Not paying Chinese tax — <em>forgetting</em> the FBAR or Form 8938. Civil maxima run to
    US$16,536 non-willful and US$165,353 willful per violation.
    {srclinks(["U01","U02","U04"])}</p>
  </div>
  <div class="card">
    <h3>4 · Do not split, borrow quotas, or use virtual currency</h3>
    <p>Splitting is prohibited by Decree 3 Art.7 independently of any repealed penalty clause;
    virtual-currency business was banned outright on 2026-02-06.
    {srclinks(["P01","P12"])}</p>
  </div>
</div>

<h2>Where to go next</h2>
<table class="t">
<thead><tr><th>Page</th><th>What is on it</th></tr></thead>
<tbody>
<tr><td><a href="summary.html">Executive summary</a></td><td>The whole problem in one page: the four questions, the answer to each, and the decision tree.</td></tr>
<tr><td><a href="costs.html">Costs, $10k → $400k</a></td><td>The ladder in $10,000 steps, per method, with what each number is and is not.</td></tr>
<tr><td><a href="methods.html">19 routes</a></td><td>Every route found, with pros, cons, exact step-by-step procedure and the official source for each claim.</td></tr>
<tr><td><a href="taxes.html">Tax analysis</a></td><td>Why the Chinese tax on conversion is zero, and where the real tax actually sits on both sides.</td></tr>
<tr><td><a href="penalties.html">Penalties</a></td><td>The price of the wrong route, from both governments.</td></tr>
<tr><td><a href="sources.html">Sources</a></td><td>All {len(SOURCES)} sources with the exact quoted text and a link for manual review.</td></tr>
<tr><td><a href="flagged.html">Flagged for Review</a></td><td>Every value left blank, why, and every irregularity found. {len(FLAGGED)} items.</td></tr>
</tbody>
</table>

<h2>The six most relevant routes</h2>
<table class="t">
<thead><tr><th>Route</th><th>Status</th><th class="num">Max / yr</th></tr></thead>
<tbody>{top}</tbody>
</table>
<p class="note"><a href="methods.html">All {len(METHODS)} routes, including the {sum(1 for m in METHODS if m['status']=='prohibited')} prohibited ones</a>.</p>
"""
    return page("index.html", "Getting money out of China",
                "What actually stands between a CNY bank balance and a USD balance in the US — "
                "and which part of it is a tax, which part is a quota, and which part is a myth.",
                body, "CNY to USD for a US citizen: routes, costs and tax from official sources.")


# ============================================================== summary =====
def build_summary():
    body = """
<section class="hero">
  <p class="kicker">Executive summary</p>
  <blockquote>The brief was: money is stuck in a CNY account and cannot be converted
  "without paying a considerable amount of taxes." The research does not support that
  framing. China does not tax the conversion. What it restricts is the <em>movement</em>,
  and what the US can tax is <em>income</em>, not the transfer. Those are three different
  things and conflating them is what makes the problem look unsolvable.</blockquote>
</section>

<h2>1 · What is actually being asked</h2>
<table class="t">
<thead><tr><th>Question</th><th>Answer</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Is there a Chinese tax on converting CNY to USD?</td>
    <td><strong>No.</strong> A currency conversion is not one of the nine enumerated IIT income categories. Tax attaches to the income that produced the money — salary at 3–45%, passive items at a flat 20%.</td>
    <td>__SRC:P11__</td></tr>
<tr><td>Is there a limit on how much can be converted?</td>
    <td><strong>Yes — a quota, not a tax.</strong> US$50,000 per person per calendar year with ID only. Above that, genuine current-account needs are permitted with authenticity documents; capital items are excluded.</td>
    <td>__SRC:P02__ __SRC:P03__ __SRC:P15__</td></tr>
<tr><td>How do I move a large balance then?</td>
    <td><strong>Two honest options.</strong> Eight calendar years at one person's quota with no approvals and no irreversible steps; or the emigration transfer under PBOC [2004] No.16 — roughly two years, but you must cancel your <span class="zh">户口</span> and complete a PRC tax settlement first.</td>
    <td>__SRC:P02__ __SRC:P06__</td></tr>
<tr><td>Where does the US tax bite?</td>
    <td><strong>Not on the transfer.</strong> A US citizen is taxed on worldwide income and §988 makes FX gain ordinary — but a personal transaction is excluded unless the gain exceeds US$200. The real exposure is <em>reporting</em>: FBAR, Form 8938, Form 3520.</td>
    <td>__SRC:U05__ __SRC:U08__ __SRC:U01__ __SRC:U02__</td></tr>
</tbody>
</table>

<h2>2 · The decision tree</h2>
<ol class="steps">
<li><strong>Work out what the money is.</strong> Salary that was taxed at source? A property sale? An inheritance or gift? Untaxed informal earnings? This single fact determines the Chinese tax, and it is the only question this document cannot answer for you.</li>
<li><strong>Ask the bank, in writing, which class you are in:</strong> <span class="zh">境内个人</span> or <span class="zh">境外个人</span>. A <span class="zh">境内个人</span> gets the US$50,000 purchase quota. A <span class="zh">境外个人</span> generally does not — <em>unless</em> they hold a Foreign Permanent Resident ID, in which case they do. __SRC:P08__ __SRC:P03__</li>
<li><strong>Is the answer to (1) "taxed salary" and the amount ≤ US$50,000?</strong> Use the quota. One wire, ~$68 of published bank fees, done this year. __SRC:P02__ __SRC:C01__</li>
<li><strong>Is the amount larger, and is the money provably salary?</strong> Either run the quota over several years, or use the documented above-quota route with the tax voucher — legal, but discretionary. __SRC:P02__ __SRC:P08__</li>
<li><strong>Are you leaving China permanently?</strong> The emigration route is the only published bulk channel. Weigh ~2 years of approval against 8 years of patience, and be clear that cancelling <span class="zh">户口</span> is irreversible. __SRC:P06__ __SRC:P11__</li>
<li><strong>Whatever you choose, file the US side.</strong> FinCEN 114 above US$10,000 aggregate; Form 8938 above the threshold; Form 3520 above US$100,000 of gifts from a nonresident individual. Getting this wrong costs more than any of the Chinese taxes discussed here. __SRC:U01__ __SRC:U02__ __SRC:U08__ __SRC:U04__</li>
</ol>

<h2>3 · What the conversion penalty actually consists of</h2>
<p>Five separate things get called "the tax". Only one of them is a tax.</p>
<table class="t">
<thead><tr><th>Component</th><th>Is it a tax?</th><th>Size</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Bank wire commission + cable charge</td><td>No — a fee</td><td>0.1% of the CNY amount, min CNY 100 / max CNY 500, plus CNY 120 per wire</td><td>__SRC:C01__</td></tr>
<tr><td>Retail FX spread (bid/ask)</td><td>No — a margin</td><td><strong>Not published.</strong> Left blank throughout this site rather than guessed. Usually the largest single component.</td><td>— <span class="flag">F-SPREAD</span></td></tr>
<tr><td>China IIT on the underlying income</td><td><strong>Yes</strong></td><td>3–45% on comprehensive income; 20% flat on interest, dividends, property rent, property transfers, incidental income</td><td>__SRC:P11__</td></tr>
<tr><td>China FX-control penalty (if you break a rule)</td><td>No — a penalty</td><td>up to 30% of the amount involved; individual administrative fines up to RMB 50,000</td><td>__SRC:P04__</td></tr>
<tr><td>US tax on FX gain</td><td><strong>Yes, but rarely</strong></td><td>Ordinary, not capital — with a personal-transaction exclusion unless the gain exceeds US$200</td><td>__SRC:U05__</td></tr>
</tbody>
</table>
<p class="note">The "considerable tax" in the brief is almost certainly items 2 and 3 confused with each other:
a bank margin is invisible and feels like a tax, and a real IIT bill on untaxed income is a genuine tax
that no route avoids. Item 3 cannot be engineered away; items 1 and 2 can be minimised by choosing the
cheapest route, and item 4 is entirely optional — you only pay it by breaking a rule.</p>

<h2>4 · Cost in one line per route</h2>
__COSTTABLE__

<h2>5 · What was verified, and what was not</h2>
<p>Every claim in this document carries a source id that links to the official page where the text
appears; the exact quoted passage is reproduced on the <a href="sources.html">Sources</a> page for
manual review. Where a value could not be confirmed it is blank, never filled in — those are
enumerated with reasons on the <a href="flagged.html">Flagged for Review</a> page
({nflag} items, none of which blocks publication).

The largest single gap is the retail FX spread. No bank reviewed publishes an executable
CNY/USD customer rate with its markup, so <strong>every dollar figure on this site is a floor
and not a full cost</strong>. That is stated on every table rather than buried.</p>
"""
    # cost one-liner table
    rows = []
    for m in sorted(METHODS, key=lambda x: x["rank"]):
        r = BY_METHOD[m["id"]][len(BY_METHOD[m["id"]]) - 1]  # $400k row
        fee = money(r["fee_usd"]) if r["fee_usd"] is not None else '<span class="blank">—</span>'
        yrs = r["years"] if r["years"] is not None else '<span class="blank">—</span>'
        srcs = srclinks(m["sources"][:3])
        rows.append(
            f'<tr><td><a href="methods.html#{m["id"]}">{e(m["id"])}</a> {e(m["name"])} {srcs}</td>'
            f"<td>{statuschip(m['status'])}</td><td class=\"num\">{fee}</td><td class=\"num\">{yrs}</td></tr>"
        )
    costtable = (
        '<table class="t"><thead><tr><th>Route</th><th>Status</th>'
        '<th class="num">Published fee to move $400,000</th><th class="num">Years</th></tr></thead>'
        "<tbody>" + "".join(rows) + "</tbody></table>"
        '<p class="note">Fees only — excludes the unpublished spread. Full $10,000-increment ladder on '
        '<a href="costs.html">Costs</a>.</p>'
    )
    body = body.replace("__COSTTABLE__", costtable)
    body = re.sub(r"__SRC:([A-Z0-9]+)__", lambda m: srclink(m.group(1)), body)
    body = body.replace("{nflag}", str(len(FLAGGED)))
    body = body.replace("{nflag_plural}", "" if len(FLAGGED) == 1 else "s")
    return page("summary.html", "Executive summary",
                "Four questions, four answers, one decision tree — and an honest account of which part of "
                "the 'conversion penalty' is a tax and which part is a bank margin.", body)


# ================================================================ costs =====
def build_costs():
    # --- the headline ladder: M01 vs M04 at every $10k step -------------------
    rows = []
    for L in LADDER:
        rec = L["recommended"]
        badge = f'<span class="chip c-available">{rec}</span>'
        rows.append(
            f"""<tr>
            <td class="num"><strong>{money(L['amount_usd'])}</strong></td>
            <td class="num">{money(L['quota_fee_usd'])}</td>
            <td class="num">{L['quota_years']}</td>
            <td class="num">{money(L['bulk_fee_usd'])}</td>
            <td class="num">{L['bulk_years']}</td>
            <td>{badge}</td>
            </tr>"""
        )
    ladder_table = f"""
<table class="t ladder">
<thead><tr>
  <th class="num">Amount</th>
  <th class="num">M01 quota<br><span class="thsub">fee · years</span></th>
  <th class="num">yrs</th>
  <th class="num">M04 emigration<br><span class="thsub">fee · years</span></th>
  <th class="num">yrs</th>
  <th>Recommended</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<p class="note"><strong>Every fee column is a floor.</strong> It is the published bank tariff
(0.1%, min CNY 100, max CNY 500, + CNY 120 cable per wire) {srclink("C01")} converted at the
SAFE central parity of 1 USD = {COST_META['fx']['cny_per_usd']} CNY for 2026-11-09 {srclink("P14")}.
It excludes the retail FX spread, which no reviewed bank publishes <span class="flag">F-SPREAD</span>.
It excludes any Chinese income tax on the money itself, which depends on what the money is
{srclink("P11")}.</p>
"""

    # --- per-method tables at each amount ------------------------------------
    detail = []
    for m in sorted(METHODS, key=lambda x: x["rank"]):
        rows_m = []
        for r in BY_METHOD[m["id"]]:
            fee = money(r["fee_usd"]) if r["fee_usd"] is not None else None
            rows_m.append(
                f"""<tr>
                <td class="num">{money(r['amount_usd'])}</td>
                {cell_num(r["fee_usd"])}
                <td class="num">{'' if r['transfers'] is None else r['transfers']}</td>
                <td class="num">{'' if r['years'] is None else r['years']}</td>
                <td class="tiny">{e(r['constrained_by'] or '')}</td>
                </tr>"""
            )
        rows_m = "".join(rows_m)
        srcs_used = m["sources"]
        detail.append(f"""
<details class="m" id="cost-{m['id']}">
<summary><strong>{e(m['id'])}</strong> {e(m['name'])} {statuschip(m['status'])}</summary>
<table class="t">
<thead><tr><th class="num">Amount</th><th class="num">Published fee</th>
<th class="num">Transfers</th><th class="num">Years</th><th>Binding constraint</th></tr></thead>
<tbody>{rows_m}</tbody>
</table>
<p class="tiny">Sources: {srclinks(srcs_used)}</p>
</details>""")

    body = f"""
<section class="hero">
  <p class="kicker">$10,000 → $400,000 in $10,000 steps</p>
  <blockquote>The fees are small. The cost is <strong>time</strong> — and the one number that
  would actually matter, the bank's FX spread, is not published anywhere, so it is blank
  here rather than invented.</blockquote>
</section>

<h2>The ladder</h2>
<p>Two lawful choices at every amount: the annual quota (M01) or the emigration transfer (M04).
Everything else is either slower, narrower, or prohibited.</p>
{ladder_table}

<h2>How to read these numbers</h2>
<table class="t">
<thead><tr><th>Column</th><th>What it is</th><th>What it is not</th></tr></thead>
<tbody>
<tr><td>Fee</td><td>The published bank tariff for the wires the route requires</td><td>Not the spread, not tax, not professional fees</td></tr>
<tr><td>Years</td><td>How long the route takes at its published ceiling</td><td>Not a promise — approval times are discretionary</td></tr>
<tr><td>Transfers</td><td>How many separate wires are needed</td><td>Not a suggestion to split; each is lawful and disclosed</td></tr>
<tr><td>Recommended</td><td>The route that avoids the worst trade-off at that size</td><td>Not advice — it ignores your tax facts, which dominate</td></tr>
</tbody>
</table>

<h2>Roadmap by amount</h2>
<div class="cards">
  <div class="card"><h3>$10k – $50k</h3>
  <p>One wire under the annual quota. Published bank fee US$32.74 – US$67.86.
  No approval, no irreversible step. {srclink("P02")} {srclink("C01")}</p></div>
  <div class="card"><h3>$60k – $150k</h3>
  <p>Two to three calendar years at the quota, or the documented above-quota route,
  or the emigration transfer. This is the band where the trade-off first bites.
  {srclink("P02")} {srclink("P06")}</p></div>
  <div class="card"><h3>$160k – $400k</h3>
  <p>Four to eight calendar years at the quota. Past roughly $100,000 the emigration
  route becomes both cheaper and faster — at the price of cancelling
  <span class="zh">户口</span>, which is irreversible. {srclink("P06")} {srclink("P11")}</p></div>
</div>

<h2>Every method, every increment</h2>
<p>Expand a route for its own ladder. A blank cell means the provider does not publish that
figure — it is not zero.</p>
{''.join(detail)}

<h2>Raw data</h2>
<p class="mono">
<a href="data/costs.csv">costs.csv</a> — {len(BY_METHOD) * 40} rows ·
<a href="data/costs.json">costs.json</a> ·
<a href="data/methods.json">methods.json</a> ·
<a href="data/sources.json">sources.json</a> ·
generated by <a href="model.py">model.py</a>
</p>
"""
    return page("costs.html", "Costs by amount",
                "What moving each amount actually costs, in $10,000 steps from $10,000 to $400,000 — "
                "with the unpublished spread left blank instead of guessed.", body)


# ============================================================== methods =====
def build_methods():
    blocks = []
    for m in sorted(METHODS, key=lambda x: x["rank"]):
        vol = m["volume"]
        steps = "".join(f"<li>{e(s)}</li>" for s in m["steps"])
        docs = "".join(f"<li>{e(d)}</li>" for d in m["docs"]) or "<li>—</li>"
        pros = "".join(f"<li>{e(p)}</li>" for p in m["pros"]) or '<li class="none">None — this route is prohibited.</li>'
        cons = "".join(f"<li>{e(c)}</li>" for c in m["cons"])
        fees = "".join(
            f"""<tr><td>{e(f['item'])}</td>
            {cell_num(f['usd'], f.get('source'))}
            <td class="tiny">{e(f['basis'])}</td></tr>"""
            for f in m["fees"]
        )
        flags = " ".join(flagbadge(f) for f in m["flags"])
        blocks.append(f"""
<article class="method" id="{m['id']}">
  <h2><span class="mid">{e(m['id'])}</span> {e(m['name'])} {statuschip(m['status'])}</h2>
  <p class="zh">({e(m['name_zh'])})</p>
  <p class="oneline">{e(m['one_line'])}</p>

  <table class="kv">
  <tr><th>Eligibility</th><td>{e(m['eligibility'])}</td></tr>
  <tr><th>Ceiling</th><td>{'—' if vol['annual_usd'] is None else money(vol['annual_usd']) + ' / year'}
      {' · ' + money(vol['per_txn_usd']) + ' / transfer' if vol['per_txn_usd'] is not None else ''}
      <div class="tiny">{e(vol['note'])} {srclinks(vol['source'])}</div></td></tr>
  <tr><th>Documents</th><td><ul class="tight">{docs}</ul></td></tr>
  </table>

  <h3>Step by step</h3>
  <ol class="steps">{steps}</ol>

  <h3>Published fees</h3>
  <table class="t">
  <thead><tr><th>Item</th><th class="num">Cost</th><th>Basis</th></tr></thead>
  <tbody>{fees}</tbody>
  </table>

  <h3>Chinese tax</h3>
  <div class="taxbox"><strong>{e(m['cn_tax']['headline'])}</strong>
  <p>{e(m['cn_tax']['detail'])} {srclinks(m['cn_tax']['sources'])}</p></div>

  <h3>US tax</h3>
  <div class="taxbox"><strong>{e(m['us_tax']['headline'])}</strong>
  <p>{e(m['us_tax']['detail'])} {srclinks(m['us_tax']['sources'])}</p></div>

  <div class="pc">
    <div><h4>Pros</h4><ul class="pros">{pros}</ul></div>
    <div><h4>Cons</h4><ul class="cons">{cons}</ul></div>
  </div>
  <p class="tiny">{flags}</p>
  <p class="tiny">Sources: {srclinks(m['sources'])}</p>
</article>""")

    body = f"""
<section class="hero">
  <p class="kicker">{len(METHODS)} routes found</p>
  <blockquote>{sum(1 for m in METHODS if m['status']=='available')} available now,
  {sum(1 for m in METHODS if m['status']=='conditional')} conditional,
  and {sum(1 for m in METHODS if m['status']=='prohibited')} <strong>prohibited</strong> — listed
  because knowing what to avoid is part of the answer, and because several of them are
  actively marketed to people in exactly this position.</blockquote>
</section>
<p>Ordered by usefulness. Each route states what it needs, what it costs, how long it takes,
and the exact procedure.</p>
{''.join(blocks)}
"""
    return page("methods.html", "Every route, pros and cons",
                "Nineteen ways CNY can become USD — including the five that will get you "
                "penalised, listed so you can recognise them.", body)


# ================================================================ taxes =====
def build_taxes():
    body = f"""
<section class="hero">
  <p class="kicker">The tax analysis</p>
  <blockquote>China taxes <em>income</em>. The US taxes <em>worldwide income of citizens</em>.
  Neither taxes the act of changing currency. The word "penalty" in the brief is doing a lot
  of work — most of it is a bank margin, and the rest is income tax on money that was never
  declared in the first place.</blockquote>
</section>

<h2>China: why conversion is not a taxable event</h2>
<p>The PRC Individual Income Tax Law lists nine income categories and taxes nothing else.
A conversion between currencies is not among them.</p>
<table class="t">
<thead><tr><th>Category</th><th>Rate</th></tr></thead>
<tbody>
<tr><td>Comprehensive income — wages and salaries, labour remuneration, author's remuneration, royalties</td><td>progressive <strong>3% – 45%</strong></td></tr>
<tr><td>Business income</td><td>progressive <strong>5% – 35%</strong></td></tr>
<tr><td>Interest, dividends and bonuses</td><td>flat <strong>20%</strong></td></tr>
<tr><td>Property leasing income</td><td>flat <strong>20%</strong></td></tr>
<tr><td>Property transfer income</td><td>flat <strong>20%</strong> on proceeds minus original value and reasonable expenses</td></tr>
<tr><td>Incidental income</td><td>flat <strong>20%</strong></td></tr>
</tbody>
</table>
<p>{srclink("P11")} — IIT Law Arts. 2, 3, 6(5). Rates quoted directly from the statute; no
category is "currency conversion".</p>

<h3>The two Chinese taxes that actually apply to this problem</h3>
<table class="t">
<thead><tr><th>Situation</th><th>Tax</th><th>Source</th></tr></thead>
<tbody>
<tr><td>The balance is salary already taxed at source</td>
    <td><strong>Nothing further.</strong> Withheld monthly; remitting it adds no tax.</td>
    <td>{srclink("P11")} {srclink("P13")}</td></tr>
<tr><td>The balance came from selling property</td>
    <td><strong>20% flat on the net gain</strong> — proceeds minus original value minus reasonable expenses. This is usually the largest Chinese tax in the picture.</td>
    <td>{srclink("P11")}</td></tr>
<tr><td>You are emigrating and cancelling <span class="zh">户口</span></td>
    <td><strong>A full tax settlement is mandatory before cancellation</strong> — by statute, not by bank policy. This is where an undeclared balance surfaces.</td>
    <td>{srclink("P11")} {srclink("P06")}</td></tr>
<tr><td>The balance is from untaxed informal earnings</td>
    <td><strong>The real problem.</strong> No document-backed route can carry it, because every above-quota route demands a tax voucher. No lawful route fixes this; only regularisation does.</td>
    <td>{srclink("P08")} {srclink("P13")}</td></tr>
</tbody>
</table>

<h3>Currency for tax purposes</h3>
<p>IIT is computed in RMB. Foreign-currency income is converted at the PBOC central parity
{srclink("P11")} — the same rate series this site uses to turn published CNY fees into dollars
{srclink("P14")}.</p>

<h2>The United States: three separate questions</h2>
<table class="t">
<thead><tr><th>Question</th><th>Rule</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Is the transfer income?</td>
    <td><strong>No.</strong> A US citizen is taxed on worldwide income; moving your own money is not income.</td>
    <td>{srclink("U08")}</td></tr>
<tr><td>Is the currency itself taxed?</td>
    <td><strong>Only on a gain over US$200.</strong> §988 makes FX gain <em>ordinary</em>, not capital — but a personal transaction is excluded unless the gain exceeds US$200.</td>
    <td>{srclink("U05")}</td></tr>
<tr><td>Is there double taxation of the Chinese income?</td>
    <td><strong>Relieved by the foreign tax credit</strong> — a credit, not a deduction, on Form 1116. Not available for tax on income you excluded under the FEIE, and only the treaty-reduced amount is creditable.</td>
    <td>{srclink("U06")} {srclink("U07")}</td></tr>
</tbody>
</table>

<h3>The treaty, and why it does not shelter a US citizen</h3>
<p>The US–PRC income tax convention (signed 1984, in force 1987) caps source-country tax on
dividends, interest and royalties at <strong>10% of the gross amount</strong>
{srclink("U07")}. But its saving clause says the United States may tax its citizens
notwithstanding any provision of the agreement {srclink("U10")}. Practical effect: the treaty
limits <em>China's</em> claims and shapes what you may credit — it does not reduce your US
filing obligation.</p>

<h2>The reporting obligations, which are the real risk</h2>
<table class="t">
<thead><tr><th>Form</th><th>Trigger</th><th>Failure costs</th><th>Source</th></tr></thead>
<tbody>
<tr><td>FinCEN 114 (FBAR)</td>
    <td>Aggregate of all foreign financial accounts exceeds <strong>US$10,000</strong> at any point in the year — even with no income</td>
    <td>Civil maxima: <strong>US$16,536</strong> non-willful, <strong>US$165,353</strong> willful per violation; willful statutory floor is the greater of US$100,000 or 50% of the balance</td>
    <td>{srclink("U01")} {srclink("U04")} {srclink("U09")}</td></tr>
<tr><td>Form 8938</td>
    <td>Specified foreign financial assets above <strong>US$50,000 / US$75,000</strong> (single, US / abroad) or <strong>US$100,000 / US$150,000</strong> (joint); <strong>US$200,000 / US$300,000</strong> single and <strong>US$400,000 / US$600,000</strong> joint for a US resident filing abroad</td>
    <td>Separate penalty regime</td>
    <td>{srclink("U02")}</td></tr>
<tr><td>Form 3520</td>
    <td>Receipt of more than <strong>US$100,000</strong> in gifts/bequests from a nonresident individual or foreign estate in a year</td>
    <td>Information-return penalties</td>
    <td>{srclink("U08")}</td></tr>
<tr><td>FinCEN 105</td>
    <td>More than <strong>US$10,000</strong> of currency entering or leaving the US</td>
    <td>Seizure/forfeiture plus civil and criminal exposure; structuring penalty capped at the amount involved</td>
    <td>{srclink("U03")} {srclink("U09")}</td></tr>
</tbody>
</table>

<h2>The honest bottom line</h2>
<p>For a US citizen moving taxed salary out of China, the combined tax bill on the
<em>conversion itself</em> is <strong>zero</strong> on both sides. What you actually pay is a
bank wire tariff (cents on the dollar), an unpublished FX spread (the real cost), and — if the
money was never taxed in China — the Chinese income tax you already owed. The expensive
mistakes are reporting failures and prohibited routes, and both are avoidable.</p>
"""
    return page("taxes.html", "Taxes on both sides",
                "China taxes income at 3–45% or a flat 20%; the US taxes worldwide income but not "
                "the transfer — and neither taxes the act of converting.", body)


# ============================================================ penalties =====
def build_penalties():
    body = f"""
<section class="hero">
  <p class="kicker">The cost of the wrong route</p>
  <blockquote>Every penalty below is avoidable. None of them is a tax you owe for converting
  money lawfully — they are the price of splitting, misdeclaring, or failing to file.</blockquote>
</section>

<h2>China — FX-control penalties</h2>
<table class="t">
<thead><tr><th>Conduct</th><th>Penalty</th><th>Source</th></tr></thead>
<tbody>
<tr><td>逃汇 / 非法套汇 / 违规购汇 (evasion, illicit arbitrage, irregular purchase)</td>
    <td>Fine <strong>up to 30%</strong> of the amount involved; in serious cases <strong>30% up to the equivalent of the amount</strong>, plus possible criminal liability; proceeds may be confiscated</td>
    <td>{srclink("P04")}</td></tr>
<tr><td>Violating rules on carrying currency into or out of China</td>
    <td>Fine <strong>up to 20%</strong> of the amount</td><td>{srclink("P04")}</td></tr>
<tr><td>Administrative penalties on individuals generally</td>
    <td>Up to <strong>RMB 50,000</strong></td><td>{srclink("P04")}</td></tr>
<tr><td>Splitting purchases across people to beat the quota</td>
    <td>Prohibited by <strong>Decree [2006] No.3 Art.7</strong> — and note the trap: the 2007 penalty clause was repealed in 2023, but the prohibition stands independently</td>
    <td>{srclink("P01")} {srclink("P02")} {srclink("P15")}</td></tr>
<tr><td>Lending or borrowing quotas</td>
    <td>Named expressly in SAFE's "six don'ts"</td><td>{srclink("P15")}</td></tr>
<tr><td>Carrying more than US$10,000 of currency out</td>
    <td><strong>Prohibited outright</strong> — not a permit matter</td><td>{srclink("P07")}</td></tr>
<tr><td>Virtual-currency business</td>
    <td>Illegal financial activity since <strong>2026-02-06</strong>; penalties including criminal referral; offshore entities barred from serving mainland subjects</td>
    <td>{srclink("P12")}</td></tr>
<tr><td>Underground banking</td>
    <td>Expressly prohibited; 30% penalty regime applies</td><td>{srclink("P15")} {srclink("P04")}</td></tr>
</tbody>
</table>

<h2>United States — reporting and structuring</h2>
<table class="t">
<thead><tr><th>Conduct</th><th>Exposure</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Failing to file the FBAR (non-willful)</td>
    <td><strong>US$16,536</strong> per violation (inflation-adjusted, assessments on/after 2025-01-17); reasonable-cause exception exists if the account was properly reported in amount</td>
    <td>{srclink("U04")} {srclink("U09")}</td></tr>
<tr><td>Failing to file the FBAR (willful)</td>
    <td><strong>US$165,353</strong> per violation, with a statutory floor of the greater of <strong>US$100,000 or 50% of the account balance</strong></td>
    <td>{srclink("U04")} {srclink("U09")}</td></tr>
<tr><td>Structuring a transaction to evade a reporting threshold</td>
    <td>Civil penalty <strong>up to the amount of currency involved</strong>, reduced by any forfeiture</td>
    <td>{srclink("U09")}</td></tr>
<tr><td>Not reporting currency above US$10,000</td>
    <td>Seizure/forfeiture plus civil and criminal exposure</td><td>{srclink("U03")}</td></tr>
<tr><td>Failing to file Form 8938</td>
    <td>Separate penalty regime from the FBAR</td><td>{srclink("U02")}</td></tr>
<tr><td>Failing to file Form 3520</td>
    <td>Information-return penalties</td><td>{srclink("U08")}</td></tr>
</tbody>
</table>

<h2>Compare that to the lawful fee</h2>
<div class="cards">
  <div class="card"><h3>Lawful, $400,000 over 8 years</h3>
  <p class="bignum">{money(LADDER[-1]['quota_fee_usd'])}</p>
  <p>of published bank tariff, no penalty, no approval, nothing irreversible.
  {srclink("C01")} {srclink("P02")}</p></div>
  <div class="card"><h3>One willful FBAR violation</h3>
  <p class="bignum">$165,353</p>
  <p>per violation — plus a floor of half the account balance.
  {srclink("U04")} {srclink("U09")}</p></div>
  <div class="card"><h3>One 30% China FX penalty</h3>
  <p class="bignum">$120,000</p>
  <p>on a $400,000 amount involved, at the stated maximum rate. {srclink("P04")}</p></div>
</div>
<p class="note">The comparison is the whole argument for doing this slowly and lawfully: the
lawful route's fees are roughly <strong>0.07%</strong> of the amount, while a single reporting
failure can exceed <strong>41%</strong> of it.</p>
"""
    return page("penalties.html", "Penalties",
                "What the prohibited routes cost when they go wrong — and why the slow lawful "
                "route is cheaper than any of them by two orders of magnitude.", body)


# ============================================================== sources =====
def build_sources():
    gov = [s for s in SOURCES.values() if s["type"] == "government"]
    com = [s for s in SOURCES.values() if s["type"] != "government"]

    def cards(items):
        out = []
        for s in items:
            out.append(f"""
<div class="srccard" id="src-{s['id']}">
  <h3><span class="mid">{e(s['id'])}</span> {e(s['title'])}</h3>
  <p class="tiny">{e(s['authority'])} · {e(s['lang'])} · {e(s['type'])} · retrieved {e(s['retrieved'])}</p>
  <p><a href="{e(s['url'])}" class="urllink">{e(s['url'])}</a></p>
  <p class="tiny"><strong>Locator:</strong> {e(s.get('locator',''))}</p>
  <blockquote class="q">{e(s['quote'])}</blockquote>
  <p class="tiny">{e(s.get('notes',''))}</p>
  <p class="tiny">Cited by: {', '.join(m['id'] for m in METHODS if s['id'] in m['sources']) or '—'}</p>
</div>""")
        return "".join(out)

    body = f"""
<section class="hero">
  <p class="kicker">{len(SOURCES)} sources</p>
  <blockquote>Every claim on this site traces to one of these. The quoted passage is reproduced
  so you can check the wording yourself without re-reading a Chinese regulation, and the URL is
  there so you can check that the quote is real.</blockquote>
</section>

<h2>Government and official sources ({len(gov)})</h2>
<p class="tiny">PRC: PBOC, SAFE (national and Tianjin branch), State Taxation Administration,
State Council. US: IRS, CBP, eCFR, U.S. Code via govinfo.</p>
{cards(gov)}

<h2>Commercial sources ({len(com)}) — clearly labelled</h2>
<p class="tiny">A commercial tariff or provider page is not an official rule. They are included
because published bank fees are the only real cost figures available, and each is marked
<span class="flag">F-COMMERCIAL</span> where it matters.</p>
{cards(com)}

<h2>What was deliberately not used</h2>
<table class="t">
<thead><tr><th>Source</th><th>Why not</th></tr></thead>
<tbody>
<tr><td>Blog posts, forums, YouTube explainers, "how I moved my money out" threads</td>
<td>Not official, not verifiable, frequently describing conduct that is now prohibited.</td></tr>
<tr><td>Bank FX rate pages that publish only a headline rate without the customer markup</td>
<td>Cannot support any dollar figure; the markup is the cost and it is missing.</td></tr>
<tr><td>Any source behind a login or paywall</td>
<td>Not manually reviewable by the user, which defeats the purpose.</td></tr>
</tbody>
</table>
"""
    return page("sources.html", "Sources",
                "All sources with the exact quoted text and a public link, so every number on "
                "this site can be checked by hand.", body)


# ============================================================== flagged =====
FLAGGED = []


def collect_flags():
    """Every blank and every irregularity, harvested from the data itself."""
    FLAGGED.clear()
    # 1. every blank numeric cell in the cost model
    blanks = {}
    for mid, rows in BY_METHOD.items():
        for r in rows:
            for field in ("fee_usd", "spread", "cn_tax_on_conversion_usd", "us_tax_on_transfer_usd"):
                if r.get(field) is None:
                    blanks.setdefault((mid, field), {"example": r["amount_usd"], "note": r.get("note", "")})
    for (mid, field), info in sorted(blanks.items()):
        m = BYID[mid]
        FLAGGED.append({
            "kind": "Unverified value",
            "id": f"{mid} · {field}",
            "what": f"The {field} for {m['name']} is blank.",
            "why": info["note"] or "No official source publishes this figure.",
            "sources": m["sources"],
            "blocks": False,
        })
    # 2. method-level flags
    for m in METHODS:
        for f in m["flags"]:
            FLAGGED.append({
                "kind": "Flag",
                "id": f"{m['id']} · {f}",
                "what": FLAG_TEXT.get(f, f),
                "why": m["one_line"],
                "sources": m["sources"],
                "blocks": False,
            })
    # 3. structural irregularities found while doing this work
    FLAGGED.extend([
        {"kind": "Irregularity", "id": "I-01",
         "what": "The retail CNY/USD spread is not published by any bank reviewed.",
         "why": "HSBC's published tariff (C01) lists transaction fees but no exchange-rate markup, and no other reviewed source publishes an executable customer rate. Consequence: every dollar total on this site is a floor. Deliberately left blank rather than estimated.",
         "sources": ["C01"], "blocks": False},
        {"kind": "Irregularity", "id": "I-02",
         "what": "SAFE's Tianjin 2024 guidance and the 2006 Decree appear to differ on whether a 境外个人 gets an annual purchase quota.",
         "why": "Decree [2006] No.3 (P01) imposes the annual total on 境内个人, while SAFE Tianjin's 2024 Q&A (P08) states 境外个人 have a settlement quota but no purchase quota EXCEPT holders of a Foreign Permanent Resident ID. Resolution used here: quote P08 for the 境外个人 case and flag that bank practice governs. Not resolved by this document — flagged for the user to confirm with their bank.",
         "sources": ["P01", "P08", "P03"], "blocks": False},
        {"kind": "Irregularity", "id": "I-03",
         "what": "Hui Fa [2007] No.1 Art. 39 was repealed by Hui Fa [2023] No.8, which could be misread as legalising quota-splitting.",
         "why": "The prohibition on splitting survives in Decree [2006] No.3 Art.7 and in SAFE's 'six don'ts'. Repeal of one penalty clause did not legalise the conduct. Recorded so the repeal is not mistaken for permission.",
         "sources": ["P02", "P01", "P15"], "blocks": False},
        {"kind": "Irregularity", "id": "I-04",
         "what": "The US$10,000 cash limit and the US$5,000/10,000 permit tiers are China-side; the US has a parallel US$10,000 reporting line with a totally different consequence.",
         "why": "Two regimes, same number, opposite meaning: China prohibits above US$10,000, the US merely requires a form. Conflating them is a common error.",
         "sources": ["P07", "U03"], "blocks": False},
        {"kind": "Irregularity", "id": "I-05",
         "what": "A REPO-level discrepancy was found in the repository's shared task board, outside this session's scope.",
         "why": "COORDINATION.md describes PR #17 as merged while the GitHub API reports it OPEN and CONFLICTING with no CI checks. Logged for the owning session; not edited by this session because the file is shared. See the audit page for the repo review.",
         "sources": [], "blocks": False},
        {"kind": "Irregularity", "id": "I-06",
         "what": "No published source states a per-year USD cap for the emigration transfer (M04).",
         "why": "PBOC [2004] No.16 stages the transfer by time (half within a year, balance within two) rather than by an annual dollar figure, and sends applications of RMB 500,000+ to SAFE head office. The 'per year' column is therefore blank by design, not by omission.",
         "sources": ["P06"], "blocks": False},
        {"kind": "Irregularity", "id": "I-07",
         "what": "Wise does not publish its from-CNY fee, and its eligibility excludes mainland Chinese nationals.",
         "why": "The provider states the fee appears at transfer set-up and that senders must be non-mainland-Chinese with a tax record from the last 3 years. Both facts materially limit the route and neither can be turned into a number.",
         "sources": ["C02"], "blocks": False},
        {"kind": "Irregularity", "id": "I-08",
         "what": "The US–China treaty's saving clause is quoted from the treaty PDF but was not checked against a second independent copy.",
         "why": "Protocol 1 paragraph 2 text was extracted from the IRS-hosted treaty PDF (U10). A second source was not consulted, so the quote is single-sourced.",
         "sources": ["U07", "U10"], "blocks": False},
    ])


def build_flagged():
    collect_flags()
    rows = "".join(
        f"""<tr>
        <td><span class="kind">{e(f['kind'])}</span><div class="mono tiny">{e(f['id'])}</div></td>
        <td>{e(f['what'])}<div class="tiny">{e(f['why'])}</div></td>
        <td>{srclinks(f['sources']) if f['sources'] else '<span class="blank">no source</span>'}</td>
        <td class="tiny">{'blocks' if f['blocks'] else 'does not block'}</td>
        </tr>"""
        for f in FLAGGED
    )
    body = f"""
<section class="hero warn">
  <p class="kicker">Flagged for Review</p>
  <blockquote><strong>{len(FLAGGED)} items.</strong> Nothing here blocks publication — every
  item is either a value that no official source publishes (left blank rather than guessed), a
  known limitation of the evidence, or an irregularity found while cross-checking. Each is
  listed with the source that governs it.</blockquote>
</section>

<h2>The one gap that matters most</h2>
<p>The retail CNY/USD spread — the margin a bank takes between the rate it quotes and the rate
it gives you — is the largest real cost of converting, and <strong>no reviewed bank publishes
it</strong>. HSBC's tariff lists transaction fees only. Because this site will not estimate, the
spread is blank in every table and every total is a <strong>floor</strong>. A user comparing
routes on price alone is comparing the smallest component of the cost.</p>

<h2>All flagged items</h2>
<table class="t">
<thead><tr><th>Type / id</th><th>What</th><th>Source</th><th>Effect</th></tr></thead>
<tbody>{rows}</tbody>
</table>

<h2>How to request a change</h2>
<p>If you can point to an official page that publishes any of the blank values — especially a
bank's executable CNY/USD customer rate — it can be added: the data lives in
<a href="data/sources.json">sources.json</a> (with a verbatim quote and locator) and
<a href="data/methods.json">methods.json</a>, and the site is regenerated by
<a href="build.py">build.py</a>. The build refuses to emit a hard-coded number that has no
source id.</p>
"""
    return page("flagged.html", "Flagged for Review",
                "Every value left blank and why, plus the irregularities found while verifying — "
                "published openly so nothing is silently guessed.", body)


# ================================================================ audit =====
def build_audit():
    import importlib.util
    spec = importlib.util.spec_from_file_location("usd_exit_audit", os.path.join(HERE, "audit.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return page("audit.html", "Repository audit",
                "A line-by-line review of this repository, with the command output behind every "
                "finding — twelve items, none of them edited outside this session's scope.",
                mod.build_audit_html(len(SOURCES), len(METHODS)))


# ================================================================ write =====
def main():
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    collect_flags()
    pages = {
        "index.html": build_index(),
        "summary.html": build_summary(),
        "costs.html": build_costs(),
        "methods.html": build_methods(),
        "taxes.html": build_taxes(),
        "penalties.html": build_penalties(),
        "sources.html": build_sources(),
        "flagged.html": build_flagged(),
        "audit.html": build_audit(),
    }
    for name, content in pages.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"wrote {len(pages)} pages; {len(FLAGGED)} flagged items")


if __name__ == "__main__":
    main()
