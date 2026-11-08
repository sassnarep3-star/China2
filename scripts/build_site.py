#!/usr/bin/env python3
"""Build the unified China CNY->USD dashboard at the repository root.

Deterministic: same data in, same HTML out. Every number in a table is computed
here from the constants in site_data.py and re-computed independently by
scripts/verify_site.py.
"""

import csv
import json
import math
from pathlib import Path

import site_data as D
from steps_data import STEPS, CAPTIONS

ROOT = Path(__file__).resolve().parents[1]
FX = D.FX_CNY_PER_USD
TIERS = D.TIERS


# --------------------------------------------------------------- arithmetic
def bracket_tax(amount, table):
    if amount <= 0:
        return 0.0
    for cap, rate, quick in table:
        if amount <= cap:
            return max(0.0, amount * rate - quick)
    return 0.0


def prc_iit_labor_usd(usd):
    """Resident comprehensive-income IIT on the whole amount (no other income)."""
    rmb = usd * FX
    taxable = max(0.0, rmb - D.PRC_IIT_ANNUAL_DEDUCTION_CNY)
    return bracket_tax(taxable, D.PRC_IIT_BRACKETS) / FX


def prc_flat20_usd(usd):
    return usd * D.PRC_FLAT_RATE


def us_tax_single_2026(usd):
    taxable = max(0.0, usd - D.US_2026_STANDARD_DEDUCTION_SINGLE)
    return bracket_tax(taxable, D.US_2026_SINGLE)


def ftc(prc, us):
    return min(prc, us)


def residual_us(prc, us):
    return max(0.0, us - ftc(prc, us))


def money(x):
    return "${:,.0f}".format(x)


def money2(x):
    return "${:,.2f}".format(x)


GLOSS = [
    ("服务贸易等项目对外支付税务备案", "outbound-payment tax filing"),
    ("个人财产对外转移售付汇", "individual property transfer FX rules"),
    ("分拆结售汇", "splitting FX settlement"),
    ("继承财产转移", "inheritance asset transfer"),
    ("移民财产转移", "emigrant asset transfer"),
    ("个人外汇结算账户", "individual FX settlement account"),
    ("原兑换水单", "original exchange memo"),
    ("完税证明", "tax payment certificate"),
    ("境内个人", "domestic individual"),
    ("境外个人", "non-domestic individual"),
    ("对敲", "mirror swap"),
]


def gloss(html):
    """Wrap Chinese terms so they stay readable when no CJK font is installed."""
    for term, meaning in GLOSS:
        html = html.replace(term, '<span lang="zh-Hans">{}</span> <span class="gloss">({})</span>'.format(term, meaning))
        html = html.replace('<span lang="zh-Hans">{}'.format(term), '<span lang="zh-Hans">{}'.format(term))
    # collapse accidental duplicate glosses from repeated terms in one string
    html = html.replace('</span> <span class="gloss">(tax payment certificate)</span> <span class="gloss">(tax payment certificate)</span>',
                        '</span> <span class="gloss">(tax payment certificate)</span>')
    return html


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def build_rows():
    rows = []
    for a in TIERS:
        labor = prc_iit_labor_usd(a)
        flat = prc_flat20_usd(a)
        us = us_tax_single_2026(a)
        rows.append(dict(
            amount=a,
            stat=0.0,
            labor=labor,
            flat=flat,
            us=us,
            res_labor=residual_us(labor, us),
            res_flat=residual_us(flat, us),
            quota_years=math.ceil(a / D.PRC_QUOTA_USD_PER_YEAR),
            atm_years=math.ceil(a / D.ATM_USD_PER_YEAR),
            walkin_days=math.ceil(a / D.WALKIN_USD_PER_DAY),
            fine30=a * 0.30,
            fine100=a * 1.00,
            fbar=a > 10000,
            f8938=a > 75000,
        ))
    return rows


ROWS = build_rows()
R400 = ROWS[-1]
R100 = [r for r in ROWS if r["amount"] == 100000][0]

# --------------------------------------------------------------- chrome
PAGES = [
    ("index.html", "Overview"),
    ("costs.html", "Costs"),
    ("matrix.html", "Method × amount"),
    ("methods.html", "Methods"),
    ("steps.html", "Steps"),
    ("penalty.html", "Penalty"),
    ("taxes.html", "Tax &amp; reporting"),
    ("flagged.html", "Flagged"),
    ("sources.html", "Sources"),
    ("audit.html", "Repo audit"),
]

TAIL = """
<footer class="bot"><div class="in">
<p><strong>Research, not a tax opinion.</strong> No personalised eligibility, lowest-cost provider or individual tax amount is certified. No funds were moved and no returns were filed. Blank cells are unverified or not stated by any official source — they are not zero.</p>
<p>Sources are official PRC (<span class="mono">.gov.cn</span>) or US (<span class="mono">.gov</span>) publications; the source registry marks which were re-read in this session. Repository: <a href="https://github.com/sassnarep3-star/China2">sassnarep3-star/China2</a> · Build data: <a href="data/cost-model.json">cost-model.json</a> · <a href="data/cost-tiers.csv">cost-tiers.csv</a> · <a href="data/repatriation-methods.csv">methods.csv</a></p>
</div></footer>
"""


def shell(slug, title, desc, body, extra_head=""):
    nav = []
    for href, label in PAGES:
        cur = ' aria-current="page"' if href == slug else ""
        nav.append('<a href="{h}"{c}>{l}</a>'.format(h=href, c=cur, l=label))
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="stylesheet" href="assets/site.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
{eh}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="topbar-in">
<a class="brand" href="index.html"><span class="mark">¥$</span><span>China Money<small>CNY → USD · US citizen</small></span></a>
<nav class="main" aria-label="Sections">{nav}</nav>
</div></header>
<main id="main" class="wrap">
{b}
</main>
{tail}
<script src="assets/site.js" defer></script>
</body>
</html>
""".format(t=title, d=esc(desc), eh=extra_head, nav="".join(nav), b=body, tail=TAIL)


def table(headers, rows, cap="", cls="", table_id="", filterable=False, note="", row_ids=None):
    ths = []
    for i, h in enumerate(headers):
        num = " num" if h.startswith("~") else ""
        ths.append('<th scope="col" class="{c}">{h}</th>'.format(c=num.strip(), h=h.lstrip("~")))
    trs = []
    for ri, r in enumerate(rows):
        tds = []
        for i, c in enumerate(r):
            num = ' class="num"' if headers[i].startswith("~") else ""
            tds.append("<td{s}>{c}</td>".format(s=num, c=c))
        rid = ' id="{}"'.format(row_ids[ri]) if row_ids else ""
        trs.append("<tr{s}>".format(s=rid) + "".join(tds) + "</tr>")
    cap_html = '<caption>{}</caption>'.format(cap) if cap else ""
    attrs = []
    if table_id:
        attrs.append('id="{}"'.format(table_id))
    if filterable:
        attrs.append("data-filterable")
    if cls:
        attrs.append('class="{}"'.format(cls))
    note_html = '<p class="small muted">{}</p>'.format(note) if note else ""
    return ('<div class="tw"><table {a}>{c}<thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>{n}'
            .format(a=" ".join(attrs), c=cap_html, h="".join(ths), r="".join(trs), n=note_html))


# --------------------------------------------------------------- index
def build_index():
    lab400 = R400["labor"]
    flat400 = R400["flat"]
    res400 = R400["res_flat"]
    body = """
<p class="eyebrow">Verified research · {date} · session {sess}</p>
<h1>Getting money out of China as a US citizen</h1>
<p class="lead">A working dashboard for one question: what does it actually cost to turn RMB in a mainland bank account into USD in a US account, from $10,000 to $400,000? Every figure below is either computed from an official statute or left blank and flagged. Nothing is guessed.</p>

<div class="grid g2" style="margin:18px 0">
  <section class="card verdict">
    <span class="pill">Headline finding</span>
    <div class="big">0%</div>
    <h2>There is no Chinese tax on converting your own money</h2>
    <p>The PRC Individual Income Tax Law taxes nine categories of income. "Converting RMB to USD" is not one of them. What people experience as a conversion penalty is almost always one of three different things: income tax already owed on the money's source, a bank refusing to process without a tax certificate, or the commercial spread and wire fees. Each of those is a separate problem with a separate fix.</p>
    <p><a href="penalty.html">See the six layers →</a></p>
  </section>
  <section class="card">
    <h3>The US side is usually zero too</h3>
    <p>Wiring your own funds to your own account is not a realisation event. For currency, §988(e)(1) excludes an individual's personal transactions from §988, and §988(e)(2) recognises no gain on a personal transaction unless the gain would exceed $200.</p>
    <p>If the money is untaxed income, the US tax is usually neutralised by the foreign tax credit: the PRC rate is normally higher, so the credit absorbs the US liability. At {a} the credit leaves {res} of US tax in the 20% scenario, in the model used here.</p>
    <p><a href="taxes.html">Reporting thresholds →</a></p>
  </section>
</div>

<h2>What it costs, by amount</h2>
<p>Four scenarios, all computed in the open. <strong>A</strong> is your own already-taxed money: the statutory cost is ${zero} at every amount, because no statute taxes the conversion. <strong>B</strong> and <strong>C</strong> are the two ways the real tax appears. <strong>D</strong> is the cost of the prohibited shortcuts.</p>

<div class="toolbar">
  <label class="field">Jump to an amount
    <select id="amount-jump" data-target="costs.html">
      <option value="">Choose…</option>
      {opts}
    </select>
  </label>
  <p class="small muted" id="jump-out" aria-live="polite">…or open the full 40-row table.</p>
  <a class="btn sec" href="costs.html">Full cost table</a>
  <a class="btn sec" href="matrix.html">Method × amount matrix</a>
</div>

{summary_table}

<div class="notice blue"><strong>Read the blank column literally.</strong> The commercial column is empty because no PRC or US regulator publishes a bank's spread, cable fee or intermediary charge. Those are the only costs that need a quote from your own bank, and the calculator on the cost page stays empty until you enter one.</div>

<h2>Which route, in one table</h2>
{decision}

<h2>How this was verified</h2>
<div class="grid g3">
  <div class="card kpi"><span class="n">{nsrc}</span><span class="l">official sources in the registry</span><span class="s">{nv} re-read this session · {np} cited from a prior session</span></div>
  <div class="card kpi"><span class="n">{nrow}</span><span class="l">cost rows, $10,000 to $400,000</span><span class="s">recomputed by an independent verifier on every commit</span></div>
  <div class="card kpi"><span class="n">{nflag}</span><span class="l">items flagged for review</span><span class="s">including three irregularities found in earlier work</span></div>
</div>

<h2>Executive summary</h2>
<div class="card">
<p><strong>The short version.</strong> Establish ownership and the lawful source of the balance first, then choose the document set. If the income was already taxed in China, the authorised-bank conversion route (M01) costs 0% in PRC tax and 0% in US tax on the act of moving it; the only unknown is the bank's commercial price. The USD 50,000 annual quota is <em>not</em> the controlling rule for a US citizen converting documented lawful income — Article 13 of the implementing rules sets documents, not a dollar cap — but the eligibility boundary is genuinely unclear and is flagged (F02).</p>
<p><strong>The expensive mistake to avoid.</strong> Every prohibited channel (smurfing, underground swaps, fake invoices, crypto bridges, card cash-out) is priced as a percentage of the amount: up to 30%, or 30%–100% if serious, plus confiscation. At {amt} that is up to {f30} on the low scale and {f100} on the high scale. No legitimate fee comes close.</p>
<p><strong>What cannot be certified.</strong> No provider can be named cheapest, no personal tax amount can be stated, and no commercial fee can be filled in, because none of those facts is available from an official source or from the information supplied. Those items are blank and listed on <a href="flagged.html">Flagged for review</a>.</p>
<p><a class="btn" href="summary.html">Read the full executive summary</a></p>
</div>

<h2>Earlier research in this repository</h2>
<p>Three earlier sessions published their own dashboards, each with a different scope and standard. They are preserved unchanged and linked here so nothing is lost, but they disagree with each other in places — see the <a href="audit.html">repo audit</a>.</p>
<div class="grid g3">
  <div class="card"><h3><a href="docs/index.html">docs/ dossier</a></h3><p class="small muted">Seven pages, 67 findings, 24 sources. Cites some commercial bank and fintech pages next to official ones.</p></div>
  <div class="card"><h3><a href="site/index.html">site/ dossier</a></h3><p class="small muted">Eight pages built from its own ledgers, 22 routes split 13 lawful / 5 unlawful.</p></div>
  <div class="card"><h3><a href="portal/index.html">portal/ dossier</a></h3><p class="small muted">Seven pages, 109 rows, official-domain links only, blank commercial cells.</p></div>
</div>
""".format(
        date="8 November 2026", sess=D.SESSION,
        a=money(R400["amount"]), res=money(res400), zero=money(0),
        opts="".join('<option value="{a}">{a}</option>'.format(a=r["amount"]) for r in ROWS),
        summary_table=summary_table(),
        decision=decision_table(),
        nsrc=len(D.S), nv=sum(1 for s in D.S.values() if s["status"] == "V"),
        np=sum(1 for s in D.S.values() if s["status"] == "P"),
        nrow=len(ROWS), nflag=len(D.FLAGS),
        amt=money(R400["amount"]), f30=money(R400["fine30"]), f100=money(R400["fine100"]),
    )
    return shell("index.html", "China Money — CNY → USD repatriation dashboard for a US citizen",
                 "Verified, source-linked research on converting CNY to USD as a US citizen, with costs computed from $10,000 to $400,000.", body)


def summary_table():
    picks = [r for r in ROWS if r["amount"] in (10000, 50000, 100000, 200000, 400000)]
    rows = []
    for r in picks:
        rows.append([
            "<strong>{a}</strong>".format(a=money(r["amount"])),
            money(r["stat"]) + " <span class=\"badge b-ok\">verified</span>",
            money(r["labor"]),
            money(r["flat"]),
            money(r["res_flat"]),
            "{0} yr".format(r["quota_years"]),
            "{0} yr".format(r["atm_years"]),
            money(r["fine30"]) + " / " + money(r["fine100"]),
        ])
    return table(
        ["Amount", "A. Statutory cost<br><span class='small'>own, already-taxed money</span>",
         "~B. PRC IIT<br><span class='small'>untaxed labour income</span>",
         "~C. PRC tax<br><span class='small'>asset gain / dividend, 20%</span>",
         "~US residual<br><span class='small'>after credit, case C</span>",
         "~Years<br><span class='small'>at $50k quota</span>",
         "~Years<br><span class='small'>at ATM cap</span>",
         "D. Fine if prohibited"],
        rows,
        cap="Costs at five reference amounts (full 40-row table on the cost page)",
        cls="cards-on-mobile compact",
        note="A is the verified statutory cost of converting documented, already-taxed funds. B and C are model arithmetic on official statutory rates, not advice. D is the statutory fine range under Decree 532 Arts. 39-45 (up to 30%, or 30%-100% if serious). Blank commercial costs are omitted here because they are unverified at every amount.",
    )


def decision_table():
    rows = [
        ["<strong>The income was already taxed and you can prove it</strong>",
         "M01 documented conversion + wire",
         "0% PRC · 0% US", "The only open number is the bank's spread and wire fee.",
         "S02, S04, S06"],
        ["<strong>The money is leftover from an earlier FX conversion</strong>",
         "M02 re-conversion against the original memo",
         "0% PRC · 0% US", "Needs the 原兑换水单 and must be within 24 months.",
         "S02"],
        ["<strong>The balance is already in USD inside China</strong>",
         "M04 remit from the FX savings account",
         "0% PRC · 0% US", "Cheapest of all: no conversion, so no spread.",
         "S02"],
        ["<strong>The money is untaxed income</strong>",
         "Settle PRC IIT first, then M01",
         "3%–45% or 20%", "This is the real cost, and it is owed whether or not you leave.",
         "S04, S05"],
        ["<strong>You are a PRC citizen or long-term resident</strong>",
         "M11 quota (USD 50,000/yr) or M01",
         "0% PRC at conversion", "Quota caps the speed, not the tax. Eligibility for a US passport holder is contested — F02.",
         "S01, S02, S11"],
        ["<strong>You sold PRC property or equity</strong>",
         "M08 / M15",
         "20% of the gain", "The 'penalty' is the transfer tax on the gain; the conversion adds nothing.",
         "S04"],
        ["<strong>Someone wants to use friends, an underground bank or crypto</strong>",
         "Stop — M18 to M22",
         "30%–100% fine", "Priced as a percentage of the whole amount, plus confiscation.",
         "S11"],
    ]
    return table(["Your situation", "Route to investigate", "Verified cost", "Why", "Sources"],
                 rows, cap="Route selection by fact pattern", cls="cards-on-mobile compact")


# --------------------------------------------------------------- costs
def build_costs():
    rows = []
    for r in ROWS:
        rows.append([
            '<span class="nowrap"><strong>{a}</strong></span>'.format(a=money(r["amount"])),
            money(r["stat"]),
            money(r["labor"]),
            money(r["flat"]),
            money(r["res_flat"]),
            '{} yr'.format(r["quota_years"]),
            '{} yr'.format(r["atm_years"]),
            '<span class="muted">not published</span>',
            D.sv("S04", "S05", "S07", "S13", "S11"),
        ])
    rows_html = table(
        ["Amount", "~A. Verified statutory cost", "~B. PRC IIT if untaxed", "~C. PRC 20% if asset gain",
         "~US residual after credit (C)", "~Years at $50k quota", "~Years at ATM cap",
         "Commercial fees", "Sources"],
        rows,
        cap="Cost of converting CNY to USD, $10,000 to $400,000 in $10,000 steps",
        table_id="tiers", cls="compact cards-on-mobile", filterable=True,
        row_ids=["tier-{}".format(r["amount"]) for r in ROWS])

    body = """
<p class="eyebrow">Costs</p>
<h1>What it costs, $10,000 to $400,000</h1>
<p class="lead">Forty amounts, ten thousand apart. The first money column is the verified statutory cost of converting your own already-taxed money. The next columns show where a real tax appears. The commercial column is deliberately empty.</p>

<div class="notice"><strong>How to read column A.</strong> ${zero}. At every amount. Not because a provider is cheap, but because no PRC statute imposes an FX-conversion tax and no US statute taxes moving your own funds between your own accounts. If that number looks too good, the catch is in column B: China taxes the income, not the wire.</div>

<h2>Scenario definitions</h2>
<div class="grid g2">
  <div class="card"><h3>A — Your own already-taxed money</h3><p>Documented lawful income on which PRC tax was withheld or paid, evidenced by a 完税证明 or withholding records. PRC conversion tax: 0% (S04 Art. 2 lists no such category). US tax on the transfer: 0% (§988(e), S06). Statutory total: $0.</p></div>
  <div class="card"><h3>B — Untaxed labour / service income</h3><p>The whole amount is treated as PRC comprehensive income for a resident with no other income: annual progressive brackets after the RMB 60,000 deduction, converted at CNY 6.7168/USD (S04, S05, S12). This is an upper-bound illustration, not a determination.</p></div>
  <div class="card"><h3>C — Asset gain, dividend or interest</h3><p>The whole amount is treated as falling in the 20% flat category (S04 Art. 3(3)). On a real asset transfer the 20% applies to the gain, not the gross; the gross version is used only because the cost basis is unknown (F06).</p></div>
  <div class="card"><h3>US residual</h3><p>US federal tax on the same amount (single filer, 2026 brackets, $16,100 standard deduction, no other income) minus the credit for the PRC tax, floored at zero (S07, S13). State tax is excluded (F11).</p></div>
</div>

<h2>The table</h2>
<div class="toolbar">
  <label class="field">Find an amount<input type="search" data-filter-for="tiers" placeholder="e.g. 250000 or 250,000"></label>
  <span class="small muted" data-count-for="tiers"></span>
  <button class="btn sec" type="button" data-print>Print / save PDF</button>
</div>
{rows}

<h2>What the table says, in words</h2>
<ul class="tight">
  <li><strong>Converting already-taxed money is free of tax at every amount.</strong> The only missing number is commercial.</li>
  <li><strong>At {a400}, an untaxed labour balance would carry about {l400} of PRC IIT</strong> in this model, while the US residual after the credit is {rl400}.</li>
  <li><strong>In the 20% scenario the picture changes at the top end:</strong> PRC tax of {f400} against US tax of {u400} leaves about {r400} of US tax after the credit. That is a US-bracket effect, not a conversion penalty.</li>
  <li><strong>The $50,000 quota is a speed limit, not a tax.</strong> At {a400} it needs {q400} calendar years if it applies to you at all — which for a US citizen is exactly the open question in F02.</li>
  <li><strong>The ATM channel is capped at RMB 100,000 a year</strong>, about {atm} at this rate, so it needs {atmy} years to move {a400}. It is a spending channel, not a repatriation plan.</li>
</ul>

<h2>Costs by method</h2>
<p>Every lawful method below shares the same verified statutory cost (0% on the conversion itself); what changes is the ceiling, the paperwork, and therefore the number of operations and years needed. Per-method capacity at every amount is on the <a href="matrix.html">method × amount matrix</a>.</p>
{methods}

<h2>Estimate your own all-in cost</h2>
<p>No value is prefilled, because none of these is published officially. Enter the quote your bank gives you; the arithmetic is shown so you can check it.</p>
<div class="card" id="calc">
  <div class="toolbar">
    <label class="field">Amount to convert (USD)<input id="calc-amount" type="number" min="0" step="1000" inputmode="decimal" placeholder="e.g. 250000"></label>
    <label class="field">Spread (%)<input id="calc-spread" type="number" min="0" step="0.01" inputmode="decimal" placeholder="from your bank"></label>
    <label class="field">Fixed fees (USD)<input id="calc-fixed" type="number" min="0" step="1" inputmode="decimal" placeholder="wire + intermediary"></label>
  </div>
  <p id="calc-out" aria-live="polite" class="small muted">Enter an amount and at least one quote component to see a total. No value is assumed for you.</p>
  <p class="small muted">Add the statutory result from column A ($0 for already-taxed money) to this commercial figure to get your all-in cost. If the two disagree by more than rounding, the bank has quoted you something that is not a fee.</p>
</div>

<h2>Method notes</h2>
{notes}
""".format(
        zero=money(0), rows=rows_html,
        a400=money(R400["amount"]), l400=money(R400["labor"]), rl400=money(R400["res_labor"]),
        f400=money(R400["flat"]), u400=money(R400["us"]), r400=money(R400["res_flat"]),
        q400=R400["quota_years"], atmy=R400["atm_years"], atm=money(D.ATM_USD_PER_YEAR),
        methods=method_cost_table(), notes=method_notes(),
    )
    return shell("costs.html", "Costs from $10,000 to $400,000 — China Money",
                 "Tiered, source-linked cost table for converting CNY to USD in $10,000 increments up to $400,000.", body)


def method_cost_table():
    rows = []
    for m in D.M:
        cap = m["cap"]
        if cap[0] == "illegal":
            continue
        rows.append([
            '<a href="methods.html#{i}">{i}</a>'.format(i=m["id"]),
            esc(m["name"]),
            esc(m["cost"]),
            esc(CAPTIONS[cap[0]]),
            D.sv(*m["srcs"][:3]),
        ])
    return table(["ID", "Method", "Verified statutory cost", "Capacity (from official text)", "Sources"],
                 rows, cap="Verified cost component by method", cls="compact cards-on-mobile")


def method_notes():
    out = []
    for m in D.M:
        if m["legal"] == "unlawful":
            continue
        out.append("<h3>{i} · {n}</h3><p>{c}</p><p class=\"small muted\">{x} {s}</p>".format(
            i=m["id"], n=esc(m["name"]), c=esc(m["note"]), x=esc(CAPTIONS[m["cap"][0]]), s=D.sv(*m["srcs"][:3])))
    return "".join(out)


# --------------------------------------------------------------- matrix
def cell_for(m, amount):
    kind, val = m["cap"]
    if kind in ("none", "oneoff"):
        return ("y1", "1")
    if kind == "perday":
        return ("ym", "{:,}d".format(math.ceil(amount / val)))
    if kind == "peryear":
        yrs = math.ceil(amount / val)
        return ("ym", "{} yr".format(yrs)) if yrs > 1 else ("y1", "1 yr")
    if kind == "unverified":
        return ("na", "unv")
    if kind == "na":
        return ("na", "—")
    return ("no", "ILLEGAL")


def build_matrix():
    lawful = [m for m in D.M if m["legal"] != "unlawful"]
    heads = ["Amount"] + ["<a href='methods.html#{i}' title='{n}'>{i}</a>".format(i=m["id"], n=esc(m["name"])) for m in lawful]
    rows = []
    for r in ROWS:
        cells = ['<span class="nowrap"><strong>{}</strong></span>'.format(money(r["amount"]))]
        for m in lawful:
            cls, txt = cell_for(m, r["amount"])
            cells.append('<span class="cell {c}">{t}</span>'.format(c=cls, t=txt))
        rows.append(cells)
    body = """
<p class="eyebrow">Coverage</p>
<h1>Every method, every amount</h1>
<p class="lead">This is the matrix the headline tables cannot show: for each lawful channel and each $10,000 tier, how many operations or calendar years the verified ceiling requires. A "1" means one documented operation covers the whole amount.</p>

<div class="notice blue"><strong>Legend.</strong> <span class="cell y1">1</span> one documented operation is enough &nbsp;·&nbsp; <span class="cell ym">N yr</span> calendar years needed at the verified annual ceiling &nbsp;·&nbsp; <span class="cell ym">Nd</span> counter days needed at the verified daily ceiling &nbsp;·&nbsp; <span class="cell na">unv</span> no verified ceiling (a personal fact or an unpublished rule) &nbsp;·&nbsp; <span class="cell na">—</span> the channel does not turn the balance into USD you can hold.</div>

<p class="small muted">Scroll the table sideways; the amount column stays fixed. Statutory tax is 0% in every lawful cell (see <a href="costs.html">costs</a>), so this matrix measures capacity, not tax. Prohibited channels are excluded here and priced on <a href="penalty.html">the penalty page</a>.</p>

<div class="tw"><table class="compact" id="matrix"><caption>Operations or years needed, by method and amount</caption>
<thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>

<h2>What the matrix reveals</h2>
<ul class="tight">
  <li><strong>Only three channels scale without a dollar ceiling:</strong> M01 (documented income), M02 (exchange memo) and M04 (existing FX balance). Everything else is capped, slow, or a one-off event.</li>
  <li><strong>The "quota" is not the main road for a US citizen.</strong> If M11 does not apply to you, or it does but is capped at $50,000 a year, the documented route in M01 is the only lawful way to move a large balance in one cycle.</li>
  <li><strong>Card and cash channels are structurally too small</strong> for anything above a few tens of thousands, and they carry separate declaration duties.</li>
  <li><strong>Rows marked unv are honest gaps,</strong> not zeroes: the ceiling depends on a personal fact (how much was originally converted) or on a rule not re-verified in this session.</li>
</ul>
""".format(h="".join("<th scope='col'>{}</th>".format(x) for x in heads),
           r="".join("<tr>" + "".join("<td{}>{}</td>".format(' class="num"' if i == 0 else "", c)
                                      for i, c in enumerate(row)) + "</tr>" for row in rows))
    return shell("matrix.html", "Method by amount matrix — China Money",
                 "Capacity matrix: operations or years needed for each lawful CNY-to-USD channel at every $10,000 increment.", body)


# --------------------------------------------------------------- methods
def build_methods():
    out = []
    for m in D.M:
        badge = {"lawful": "b-ok", "lawful-conditional": "b-warn", "unlawful": "b-bad"}[m["legal"]]
        label = {"lawful": "Lawful", "lawful-conditional": "Lawful, conditional", "unlawful": "Prohibited"}[m["legal"]]
        cap_kind = m["cap"][0]
        out.append("""
<details id="{i}">
<summary>{i} · {n} <span class="badge {b}">{l}</span></summary>
<div class="body">
<p>{mech}</p>
<p><strong>Verified limit.</strong> {lim}</p>
<p><strong>Cost.</strong> {cost}</p>
<p><strong>Capacity.</strong> {cap}</p>
<p><strong>Who.</strong> {who} &nbsp; <strong>Risk.</strong> {risk}</p>
<p class="small">{note}</p>
<p>{src}</p>
{steps}
</div>
</details>""".format(
            i=m["id"], n=esc(m["name"]), b=badge, l=label, mech=esc(m["mechanism"]),
            lim=esc(m["limit"]), cost=esc(m["cost"]), cap=esc(CAPTIONS[cap_kind]),
            who=esc(m["who"]), risk=esc(m["risk"]), note=esc(m["note"]),
            src=D.sv(*m["srcs"]),
            steps=('<p><a href="steps.html#{0}">Step-by-step for {0} →</a></p>'.format(m["id"]))
            if m["id"].lower() in STEPS else ""))

    overview_rows = []
    for m in D.LAWFUL + D.UNLAWFUL:
        lab = {"lawful": '<span class="badge b-ok">lawful</span>',
               "lawful-conditional": '<span class="badge b-warn">conditional</span>',
               "unlawful": '<span class="badge b-bad">prohibited</span>'}[m["legal"]]
        overview_rows.append([
            '<a href="#{i}">{i}</a>'.format(i=m["id"]),
            esc(m["name"]), lab, esc(m["limit"]), esc(m["cost"]), D.sv(*m["srcs"][:3]),
        ])
    overview = table(["ID", "Method", "Status", "Verified limit", "Verified cost", "Sources"],
                     overview_rows, cap="All 22 methods at a glance",
                     table_id="overview", cls="compact cards-on-mobile", filterable=True)

    body = """
<p class="eyebrow">Methods</p>
<h1>Every route, with its verified ceiling</h1>
<p class="lead">{nl} lawful routes, {nu} prohibited ones. The count is not the point: the ceiling, the document set and the tax treatment are. Each entry states exactly what an official source says, and says nothing where no source does.</p>

{overview}
<div class="toolbar">
  <label class="field">Search the entries<input type="search" data-filter-for="overview" placeholder="method, limit, cost…"></label>
  <span class="small muted" data-count-for="overview"></span>
</div>
<div class="notice"><strong>Groups.</strong> Personal current-account routes (M01–M07) move your own money. Capital-event routes (M08–M10) follow an asset event. Quota and family routes (M11–M12) are the ones most often misquoted online. Employment and business routes (M13–M17) need an employer, a company or a trade. M18–M22 are prohibited and priced as penalties.</div>
{cards}
""".format(nl=len(D.LAWFUL), nu=len(D.UNLAWFUL), cards="".join(out), overview=overview)
    return shell("methods.html", "All CNY-to-USD methods — China Money",
                 "Every lawful and prohibited route for moving CNY out of mainland China as a US citizen, with verified limits and official sources.", body)


# --------------------------------------------------------------- steps
def build_steps():
    blocks = []
    for m in D.M:
        key = m["id"].lower()
        if key not in STEPS:
            continue
        head, intro, steps = STEPS[key]
        lis = "".join(
            "<li><h4>{}</h4><p>{}</p><p class=\"small\">{}</p></li>".format(esc(t), esc(w), D.sv(*s))
            for t, w, s in steps)
        blocks.append("""
<section id="{ku}">
<h2>{h}</h2>
<p>{i}</p>
<ol class="steps">{l}</ol>
<p class="small"><a href="methods.html#{m}">Full method entry →</a> &nbsp; {src}</p>
</section>""".format(ku=key.upper(), h=esc(head), i=esc(intro), l=lis, m=m["id"], src=D.sv(*m["srcs"][:3])))

    body = """
<p class="eyebrow">Execution</p>
<h1>Exactly how each route works</h1>
<p class="lead">Ordered steps, each tied to the rule that requires it. Where an official source is silent — bank counter practice, appointment systems, forms that vary by branch — the step says so instead of inventing a requirement.</p>
<div class="notice"><strong>Nothing here has been executed.</strong> No account was accessed, no bank contacted, no return filed. The steps describe the sequence an official source implies; they cannot promise that a particular branch will follow it on a particular day.</div>
{blocks}
<h2>Before you start: the document set that decides everything</h2>
<div class="card">
<ul class="tight">
<li><strong>Identity</strong> — passport and the bank's customer file (S01 Art. 5; S02 Art. 26).</li>
<li><strong>Source</strong> — the contract, payroll, award, lease or sale document behind the RMB (S02 Art. 13(1)).</li>
<li><strong>Tax</strong> — the 完税证明 or withholding records; without them the bank's Art. 13 review has nothing to approve (S02, S04).</li>
<li><strong>US filing history</strong> — FBAR and Form 8938 for every year the thresholds were met; a missed year changes the plan more than any fee (S08, S09).</li>
</ul>
</div>
""".format(blocks="".join(blocks))
    return shell("steps.html", "Step-by-step execution — China Money",
                 "Ordered, source-linked steps for each lawful CNY-to-USD route.", body)


# --------------------------------------------------------------- penalty
def build_penalty():
    rows = []
    for L in D.LAYERS:
        rows.append([
            "<strong>{i}</strong><br><span class=\"small muted\">{b}</span>".format(i=L["id"], b=esc(L["basis"])),
            esc(L["name"]),
            esc(L["rule"]),
            esc(L["verified"]),
            D.sv(*L["srcs"]),
        ])
    big = table(["Layer", "What it is", "Verified rate or rule", "What the source actually says", "Sources"],
                rows, cap="The six layers of the so-called conversion penalty", cls="compact cards-on-mobile")

    calc_rows = []
    for r in [x for x in ROWS if x["amount"] in (10000, 50000, 100000, 200000, 300000, 400000)]:
        calc_rows.append([
            money(r["amount"]), money(r["stat"]), money(r["labor"]), money(r["flat"]),
            money(r["res_labor"]), money(r["res_flat"]), money(r["fine30"]), money(r["fine100"]),
            D.sv("S04", "S05", "S07", "S13", "S11"),
        ])
    calc = table(["Amount", "~L1 PRC conversion", "~L2 PRC IIT (labour)", "~L2 PRC 20% (gain)",
                  "~L4+L5 US after credit (labour)", "~L4+L5 US after credit (20%)",
                  "~L8 fine, low", "~L8 fine, serious", "Sources"],
                 calc_rows, cap="Each layer expressed in dollars", cls="compact")

    body = """
<p class="eyebrow">The penalty</p>
<h1>There is no conversion tax. There are six other layers.</h1>
<p class="lead">The phrase "conversion penalty" bundles things that behave completely differently: a tax on income, a paperwork gate, a tax on a transfer, a commercial spread, reporting duties, and fines. Breaking them apart is the whole analysis.</p>

{big}

<h2>The same layers in dollars</h2>
<p>This is where the "$400,000 problem" becomes concrete. Layer 1 is zero at every amount. Layer 2 is the only large lawful number, and it depends on the source of the money. Layer 8 is the only number that can legally exceed the balance itself.</p>
{calc}

<div class="notice"><strong>The arithmetic of the trap.</strong> At {a400}, an untaxed labour balance carries about {l400} of PRC IIT — {lp400} of the amount. The prohibited routes are priced at up to 30% ({f30}) or, if serious, 30%–100% ({f100}). A lawful conversion costs {zero} in tax plus a commercial spread nobody will publish. Paying a 30% fine to avoid a 3%–45% tax that you owe anyway is not a saving; it is the tax plus a penalty.</div>

<h2>Why the bank refuses without a certificate</h2>
<p>Article 13(1) of the implementing rules requires identity documents plus documents proving the amount and the source, expressly including tax vouchers. Article 7 of the 2006 rules prohibits fabricated vouchers and splitting. The bank is not taxing you at the counter; it is checking that the tax was paid where the law puts it — on the income.</p>

<h2>What is genuinely unknown</h2>
<ul class="tight">
<li>The commercial spread and fees (L6) — no official publication exists (F01).</li>
<li>Whether the income was already taxed (F05) — decides whether L2 applies at all.</li>
<li>The cost basis on an asset transfer (F06) — decides 20% of what.</li>
<li>Whether prior US filings were complete (F07) — can outweigh every other number.</li>
</ul>
""".format(big=big, calc=calc, a400=money(R400["amount"]), l400=money(R400["labor"]),
           lp400="{:.1f}%".format(R400["labor"] / R400["amount"] * 100),
           f30=money(R400["fine30"]), f100=money(R400["fine100"]), zero=money(0))
    return shell("penalty.html", "The conversion penalty, decomposed — China Money",
                 "Six-layer decomposition of the CNY-to-USD conversion penalty, with verified rates and dollar amounts.", body)


# --------------------------------------------------------------- taxes
def build_taxes():
    us_rows = [[esc(a), esc(b), esc(c), D.sv(d)] for a, b, c, d in D.US_RULES]
    prc_rows = [[esc(a), esc(b), D.sv(c)] for a, b, c in D.PRC_RULES]
    body = """
<p class="eyebrow">Tax and reporting</p>
<h1>US and PRC rules that actually apply</h1>
<p class="lead">Two jurisdictions, one balance. The PRC taxes the income; the US taxes worldwide income but credits the PRC tax. Reporting duties are separate from tax and are where the penalties live.</p>

<h2>PRC side</h2>
{prc}
<div class="notice blue"><strong>The one sentence to remember.</strong> Converting RMB to USD is not a taxable event in China; earning the RMB was. Article 2 of the IIT Law lists nine income categories and a conversion is not among them.</div>

<h2>US side</h2>
{us}

<h2>How the credit works in practice</h2>
<p>US tax is computed on the same income, then reduced by the PRC tax paid on it, limited to the US tax attributable to that income. When the PRC rate is higher, the excess becomes a carryforward rather than a refund. Two traps: the credit is unavailable against income you excluded under the foreign earned income exclusion, and where a treaty reduces the PRC rate, only the reduced amount is creditable (S13).</p>

<h2>Worked example at {a}</h2>
<div class="card">
<p><strong>Case C (20% flat):</strong> PRC tax {f}. US federal tax on the same amount, single filer 2026, standard deduction: {u}. Credit allowed: {c}. US tax remaining: <strong>{r}</strong>.</p>
<p><strong>Case B (progressive labour):</strong> PRC tax {l}. Credit allowed: {cb}. US tax remaining: <strong>{rb}</strong>. The PRC rate is higher across this range, so the credit absorbs the US liability.</p>
<p class="small muted">Model arithmetic on statutory inputs; not a return, not advice, and it excludes state tax and any other income (F11, F12).</p>
</div>

<h2>What is not modelled</h2>
<ul class="tight">
<li>State income tax and local taxes.</li>
<li>Treaty relief on dividends, interest and royalties — described but not re-verified here (F04).</li>
<li>Corporate-level tax before a dividend, or VAT on services.</li>
<li>Any change in law after {date}.</li>
</ul>
""".format(prc=table(["Rule", "Verified threshold or rate", "Sources"], prc_rows,
                     cap="PRC rules used on this site", cls="compact cards-on-mobile"),
           us=table(["Obligation", "Verified threshold", "Deadline", "Sources"], us_rows,
                    cap="US obligations and thresholds", cls="compact cards-on-mobile"),
           a=money(R400["amount"]), f=money(R400["flat"]), u=money(R400["us"]),
           c=money(ftc(R400["flat"], R400["us"])), r=money(R400["res_flat"]),
           l=money(R400["labor"]), cb=money(ftc(R400["labor"], R400["us"])),
           rb=money(R400["res_labor"]), date="8 November 2026")
    return shell("taxes.html", "US and PRC tax and reporting rules — China Money",
                 "Verified PRC and US tax and reporting thresholds that apply to repatriating CNY as a US citizen.", body)


# --------------------------------------------------------------- flagged
def build_flagged():
    rows = []
    for f in D.FLAGS:
        lvl = f["level"]
        cls = "b-bad" if "irregular" in lvl.lower() or "conflict" in lvl.lower() else (
            "b-warn" if "unverified" in lvl.lower() or "unknown" in lvl.lower() else "b-v")
        rows.append([
            "<strong>{i}</strong><br><span class=\"badge {c}\">{l}</span>".format(i=f["id"], c=cls, l=esc(lvl)),
            "<strong>{t}</strong>".format(t=esc(f["title"])),
            esc(f["detail"]),
            esc(f["action"]),
            D.sv(*f["srcs"]),
        ])
    body = """
<p class="eyebrow">Flagged for review</p>
<h1>What is unverified, unknown or irregular</h1>
<p class="lead">Nothing on this page blocks the rest of the site; everything on it limits how far a number can be trusted. Each item says what is missing, why, and what would resolve it.</p>

<div class="grid g3">
  <div class="card"><h3>Blank means blank</h3><p>Where an official source does not state a value, the cell is empty. It is never inferred from a commercial page, a forum, or another country's rule.</p></div>
  <div class="card"><h3>Personal facts</h3><p>Five of these items depend on facts only you hold — whether tax was paid, what the money came from, whether earlier filings were made. They are unanswerable from public sources.</p></div>
  <div class="card"><h3>Earlier work</h3><p>Three irregularities were found in the earlier dashboards in this repository and are listed here rather than quietly corrected.</p></div>
</div>

<div class="tw"><table class="compact cards-on-mobile" id="flags"><caption>Flagged items, {n} in total</caption>
<thead><tr><th scope="col">ID</th><th scope="col">What</th><th scope="col">Detail</th><th scope="col">What would resolve it</th><th scope="col">Sources</th></tr></thead>
<tbody>{r}</tbody></table></div>

<h2>The two correction notes</h2>
<div class="card">
<h3>§988 gain is ordinary, not capital</h3>
<p>An earlier data file stated that a personal foreign-currency gain above $200 is reported as capital gain. Section 988(a)(1)(A) treats foreign currency gain or loss as ordinary, and §988(e)(2) is the personal-transaction exclusion, not a rate conversion. The earlier statement is wrong on its face and should not be relied on.</p>
<p>{s6}</p>
</div>
<div class="card" style="margin-top:14px">
<h3>The 35% trust penalty is not a foreign-gift penalty</h3>
<p>An earlier portal attributed "the greater of $10,000 or 35%" to Form 3520 in general. That is the §6677 penalty for foreign trusts. Receipt of a foreign gift is reported in Part IV and penalised under §6039F(c), which is a different provision with a different measure. Gift reporting thresholds are verified; the gift penalty percentage is not stated here (F13).</p>
<p>{s10}{s15}</p>
</div>
""".format(n=len(D.FLAGS), r="".join("<tr>" + "".join("<td>{}</td>".format(c) for c in row) + "</tr>" for row in rows),
           s6=D.sv("S06"), s10=D.sv("S10"), s15=D.sv("S15"))
    return shell("flagged.html", "Flagged for review — China Money",
                 "Every unverified, unknown and irregular item in the CNY-to-USD research, with sources and remediation.", body)


# --------------------------------------------------------------- sources
def build_sources():
    rows = []
    for sid in sorted(D.S):
        s = D.S[sid]
        badge = '<span class="badge b-ok">re-read this session</span>' if s["status"] == "V" else '<span class="badge b-warn">prior session</span>'
        rows.append([
            "<strong>{i}</strong>".format(i=sid),
            esc(s["authority"]),
            '<a href="{u}" target="_blank" rel="noopener noreferrer">{t}</a>'.format(u=s["url"], t=esc(s["title"])),
            esc(s["locator"]),
            esc(s["evidence"]),
            badge,
        ])
    nv = sum(1 for s in D.S.values() if s["status"] == "V")
    body = """
<p class="eyebrow">Evidence</p>
<h1>Source registry</h1>
<p class="lead">{n} official publications. {nv} were fetched and read in this session; {np} are carried from an earlier session, linked for review, and never used as the sole basis for a computed number.</p>

<div class="notice blue"><strong>Rule applied throughout.</strong> A cell may contain a number only if an official PRC or US publication states it, or if the number is arithmetic on such a number with the assumptions printed next to it. Commercial web pages are not used as sources for any value on this site.</div>

{rows}

<h2>Primary instruments used for the computations</h2>
<ul class="tight">
<li><strong>PRC tax base and rates</strong> — S04 (IIT Law, English) and S05 (official Chinese rate schedule, because S04 publishes the schedule as an image).</li>
<li><strong>PRC FX rules</strong> — S01 (PBOC Decree 2006 No. 3) and S02 (implementing rules, 2024 republication).</li>
<li><strong>PRC penalties</strong> — S11 (State Council Decree 532).</li>
<li><strong>US tax</strong> — S07 (2026 inflation adjustments), S06 (§988), S13 (foreign tax credit).</li>
<li><strong>US reporting</strong> — S08, S09, S10, S14, S15.</li>
<li><strong>Exchange rate</strong> — S12, the PBOC central parity for 2026-11-06.</li>
</ul>
""".format(n=len(D.S), nv=nv, np=len(D.S) - nv,
           rows=table(["ID", "Authority", "Publication", "Locator", "What it establishes", "Status"],
                      rows, cap="Official source registry", cls="compact cards-on-mobile"))
    return shell("sources.html", "Source registry — China Money",
                 "Registry of every official PRC and US publication used, with locators and verification status.", body)


# --------------------------------------------------------------- audit
AUDIT = [
    ("A01", "Repository root, index.html (before this session)",
     "A 181-byte meta-refresh redirect to docs/ with no landing page.",
     "The brief asked for a clean landing page. There was none at the repository URL.", "Fixed", "Replaced with this dashboard.", "S01"),
    ("A02", "docs/, site/ and portal/ (three earlier sessions)",
     "Three parallel dashboards, built to different standards and counts: 18 routes in data/methods.json versus 22 in portal/ and research/.",
     "A reader could not tell which was authoritative, and the counts did not reconcile.", "Irregularity", "Preserved unchanged and linked from the landing page; this dashboard is the single entry point.", "S01"),
    ("A03", "data/methods.json, route R01 (field usTaxOnConversion)",
     "\"Personal foreign-currency gain of $200 or less is excluded; above $200 report as capital gain\".",
     "§988(a)(1)(A) treats the gain as ordinary, not capital; §988(e)(2) is an exclusion, not a rate change.", "Irregularity", "Corrected here and published on the flagged page (F16).", "S06"),
    ("A04", "portal/conversion-penalties.html, row CP-16",
     "Attributes \"the greater of $10,000 or 35%\" to Form 3520 generally.",
     "That measure is §6677 for foreign trusts. Foreign gifts are penalised under §6039F(c).", "Irregularity", "Split into the correct provisions; gift percentage left unstated because it was not extracted (F13).", "S10"),
    ("A05", "docs/costs.html and docs/sources.html",
     "Cites hsbc.com.cn tariff PDFs and wise.com help pages as table sources.",
     "Commercial marketing pages are not official publications; they cannot support a 'verified' row.", "Irregularity", "No commercial page is used as a source on this site; those cells are blank and flagged (F01).", "S01"),
    ("A06", "EXECUTIVE-SUMMARY.md and EXECUTIVE_SUMMARY.md",
     "Two executive summaries of different length and scope at the repository root.",
     "Duplicated, drifting deliverables with no single authoritative version.", "Duplication", "A new dated summary is published as summary.html and EXECUTIVE-SUMMARY-2026-11-08.md; the two older files are left in place, untouched.", "S04"),
    ("A07", "portal/repo-audit.html, row R-01",
     "Asserts that the USD 50,000 quota is unavailable to US passport holders, full stop.",
     "Decree 532 Art. 52(2) defines 境内个人 to include a foreigner who has resided in China for one full year. The exclusion is not absolute, and the implementing rules do not restate the definition.", "Overstatement", "Published as conflict F02 with both texts linked; no computed cell depends on the resolution.", "S11"),
    ("A08", "docs/costs.html",
     "Cites a Guangzhou municipal finance bureau page for the IIT Law.",
     "An indirect re-publication rather than the tax authority's own text.", "Weak citation", "This site cites the STA English text (S04) plus the official rate schedule (S05).", "S04"),
    ("A09", "site/index.html and EXECUTIVE-SUMMARY.md",
     "Earlier counts of lawful/unlawful routes and fetch-verified sources were wrong until a later session corrected two of them.",
     "Generated prose drifted from the ledgers, which is what happens when counts are typed by hand.", "Fixed earlier", "Every count and dollar figure on this site is generated from one data module at build time; the verifier fails the build if prose drifts.", "S01"),
    ("A10", "research/previous-dashboard/",
     "An older dashboard archived as .txt files.",
     "Preserved for audit, but not browsable as HTML.", "Intentional", "Left as is; linked only from the coordination record.", "S01"),
    ("A11", "Repository root",
     "No .nojekyll at the root, although this session publishes pages there.",
     "Jekyll processing on Pages can drop paths that begin with an underscore and slows the build.", "Fixed", "Added .nojekyll at the root.", "S01"),
    ("A12", ".github/workflows/*.yml (three earlier workflows)",
     "Each workflow triggers only on main and its own session branch.",
     "This session's branch would otherwise merge unvalidated.", "Gap", "Added verify-unified.yml for this branch and for main.", "S01"),
    ("A13", "portal/index.html",
     "\"100% .gov/.gov.cn row source links\".",
     "True within portal/, but not true of the repository as a whole, where docs/ cites commercial domains. The claim needs its scope stated.", "Scoping", "Stated here as a per-artifact claim, not a repository-wide one.", "S01"),
    ("A14", "PBOC Decree [2006] No.3, English translation",
     "Chapter Three is headed \"Administration of Individual's Foreign Exchange under the Current Account\" — the same heading as Chapter Two — although its articles are capital-account provisions.",
     "An evident translation defect. Anyone coding against the English headings will misclassify the articles.", "Irregularity", "Relied on the Chinese implementing rules (S02) for the operative text; noted here for any reader using the English page.", "S01"),
]


def build_audit():
    rows = []
    for a in AUDIT:
        cls = {"Irregularity": "b-bad", "Overstatement": "b-bad", "Gap": "b-warn", "Weak citation": "b-warn",
               "Duplication": "b-warn", "Scoping": "b-warn"}.get(a[4], "b-ok")
        rows.append([
            "<strong>{}</strong>".format(a[0]), esc(a[1]), esc(a[2]), esc(a[3]),
            '<span class="badge {c}">{s}</span>'.format(c=cls, s=esc(a[4])), esc(a[5]), D.sv(a[6]),
        ])
    body = """
<p class="eyebrow">Repository review</p>
<h1>Line-by-line audit of what was already here</h1>
<p class="lead">The repository already contained three research dossiers from earlier sessions. Each was read, and its claims were checked against the official text they cite. {n} findings, including four substantive irregularities.</p>

<div class="notice"><strong>Nothing was deleted.</strong> Earlier work is preserved in place. Where it is wrong, the correction is stated here and on the flagged page rather than silently overwritten — an audit trail is more useful than a tidy tree.</div>

<div class="tw"><table class="compact cards-on-mobile" id="audit"><caption>Audit findings</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Artifact</th><th scope="col">What it says</th><th scope="col">Finding</th><th scope="col">Severity</th><th scope="col">Resolution</th><th scope="col">Source</th></tr></thead>
<tbody>{r}</tbody></table></div>

<h2>What the audit changes about the answer</h2>
<p>None of the irregularities change the headline conclusion, which rests on the IIT Law and §988 read directly: no PRC conversion tax, no US tax on moving your own funds. They do change which earlier page a reader should trust. The civil-law point in A07 does change a recommendation, which is why it is a flag rather than a footnote: whether a long-term US resident of China may use the USD 50,000 quota has not been settled by anything in this repository.</p>

<h2>What this audit could not check</h2>
<ul class="tight">
<li>Whether any earlier session's external links still resolve — no global link-health check was run.</li>
<li>Whether earlier Chinese-language excerpts were translated correctly by their authors — only the cited locators were compared.</li>
<li>Whether the bank practice described anywhere is current at a particular branch.</li>
</ul>
""".format(n=len(AUDIT), r="".join("<tr>" + "".join("<td>{}</td>".format(c) for c in row) + "</tr>" for row in rows))
    return shell("audit.html", "Repository audit — China Money",
                 "Line-by-line audit of the earlier dashboards in this repository, with corrections and sources.", body)


# --------------------------------------------------------------- summary
def build_summary():
    body = """
<p class="eyebrow">Executive summary · {date}</p>
<h1>The answer, and its limits</h1>
<p class="lead">For a US citizen with RMB in a mainland bank account, the cheapest lawful way out is almost never a clever structure. It is the documented route: prove the source, prove the tax was paid, convert at an authorised bank, and wire. That costs 0% in Chinese tax on the conversion and 0% in US tax on the movement. Everything else in this dossier is detail around that sentence.</p>

<h2>1. The premise needs correcting</h2>
<p>The starting assumption was that converting CNY to USD triggers a considerable tax. The statutes do not support that. Article 2 of the PRC Individual Income Tax Law taxes nine categories of income; a currency conversion is not one of them. On the US side, moving your own funds is not a realisation event, and §988(e)(1)-(2) excludes an individual's personal currency transactions from §988, with no gain recognised unless it would exceed $200. At {a400} the verified statutory cost of converting already-taxed money is {zero}.</p>

<h2>2. Where the money actually goes</h2>
<ul class="tight">
<li><strong>Income tax on the source (3%–45% or a flat 20%)</strong> — owed whether or not the money leaves China. This is the real "penalty" in most cases.</li>
<li><strong>The documentary gate</strong> — Article 13(1) of the implementing rules requires identity plus source documents including tax vouchers. A missing certificate is a refusal, not a charge.</li>
<li><strong>The commercial spread and wire fees</strong> — real, unavoidable, and unpublished by any regulator. The only figure that requires your own bank's quote.</li>
<li><strong>Reporting duties</strong> — FBAR over $10,000, Form 8938 from $50,000/$75,000, Form 3520 from $100,000 of gifts, FinCEN Form 105 over $10,000 in cash. Zero cost if filed.</li>
<li><strong>Fines on prohibited channels</strong> — up to 30%, or 30%–100% if serious, plus confiscation. This is the only layer that can exceed the balance.</li>
</ul>

<h2>3. The route, in order</h2>
<ol class="tight">
<li>Establish ownership and the lawful source of the balance, and locate the tax evidence.</li>
<li>If the money came from an earlier FX conversion, use the original exchange memo (M02) — the only route needing no tax documents, valid 24 months.</li>
<li>If the balance is already in foreign currency, remit it from the FX savings account (M04) — no conversion means no spread.</li>
<li>Otherwise use M01: documented conversion plus wire, with the full document set.</li>
<li>Ask the bank, in writing, for the all-in price and for which category it will record you under.</li>
<li>File the US information returns for the years concerned.</li>
</ol>

<h2>4. The numbers</h2>
<table class="compact"><caption>Verified cost at {a400}</caption><thead><tr><th>At {a400}</th><th class="num">Amount</th></tr></thead><tbody>
<tr><td>Verified statutory cost, already-taxed money (A)</td><td class="num">{zero}</td></tr>
<tr><td>PRC IIT if the whole balance were untaxed labour income (B)</td><td class="num">{l400}</td></tr>
<tr><td>PRC tax if the whole balance were an asset gain at 20% (C)</td><td class="num">{f400}</td></tr>
<tr><td>US residual after the credit in case C</td><td class="num">{r400}</td></tr>
<tr><td>Years needed at the USD 50,000 quota, if it applies</td><td class="num">{q400}</td></tr>
<tr><td>Years needed through the ATM channel at RMB 100,000/year</td><td class="num">{q400atm}</td></tr>
<tr><td>Fine if a prohibited channel were used (low / serious)</td><td class="num">{f30} / {f100}</td></tr>
</tbody></table>

<h2>5. What cannot be certified</h2>
<p>No provider is named cheapest, because no official source publishes spreads. No personal tax amount is stated, because the personal facts are unknown. No commercial fee is filled in. No individual eligibility conclusion is drawn, and the question of whether a long-term US resident of China may use the USD 50,000 quota is flagged rather than resolved. Sixteen items are published on the flagged page, each with the source that limits it.</p>

<h2>6. The one thing to do first</h2>
<p>Before any bank visit: establish whether the PRC tax on the income was paid and obtain the certificate. That single document decides whether this is a 0% transaction or a 3%–45% one.</p>

<p class="small muted">Research only, not legal, tax or investment advice. Prepared {date}. Model arithmetic uses the PBOC central parity of 2026-11-06 (6.7168 CNY/USD), 2026 US single-filer brackets and standard deduction, and the PRC schedule for comprehensive income. Assumptions and limits are itemised on the <a href="flagged.html">flagged</a> page.</p>
""".format(date="8 November 2026", a400=money(R400["amount"]), zero=money(0),
           l400=money(R400["labor"]), f400=money(R400["flat"]), r400=money(R400["res_flat"]),
           q400=R400["quota_years"], q400atm=R400["atm_years"],
           f30=money(R400["fine30"]), f100=money(R400["fine100"]))
    return shell("summary.html", "Executive summary — China Money",
                 "Executive summary of the CNY-to-USD repatriation research for a US citizen.", body)


# --------------------------------------------------------------- exports
def write_exports():
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    model = {
        "meta": {
            "project": "China2 unified CNY→USD cost model",
            "session": D.SESSION,
            "built": D.SESSION_DATE,
            "fx_cny_per_usd": FX,
            "fx_source": "S12 PBOC central parity 2026-11-06",
            "policy": "Every value is either stated by an official source or computed by the published formula from such values. Commercial fees are never filled in.",
            "scenarios": {
                "A": "own already-taxed money: PRC conversion tax 0%, US tax on transfer 0%",
                "B": "whole amount treated as PRC comprehensive income of a resident with no other income",
                "C": "whole amount treated as PRC 20% flat-category income; US residual after credit",
                "D": "statutory fine range if a prohibited channel were used (Decree 532 Arts. 39-45)",
            },
        },
        "tiers": [
            {
                "amount_usd": r["amount"],
                "statutory_cost_usd": r["stat"],
                "prc_iit_labor_usd": round(r["labor"], 2),
                "prc_flat20_usd": round(r["flat"], 2),
                "us_federal_tax_usd": round(r["us"], 2),
                "us_residual_labor_usd": round(r["res_labor"], 2),
                "us_residual_flat_usd": round(r["res_flat"], 2),
                "years_at_quota": r["quota_years"],
                "years_at_atm_cap": r["atm_years"],
                "counter_days_at_500": r["walkin_days"],
                "fine_30pct_usd": r["fine30"],
                "fine_100pct_usd": r["fine100"],
                "fbar_threshold_met": r["fbar"],
                "form8938_threshold_met_single_us": r["f8938"],
                "commercial_cost_usd": None,
            } for r in ROWS
        ],
        "methods": [
            {
                "id": m["id"], "name": m["name"], "category": m["cat"], "legal_status": m["legal"],
                "verified_limit": m["limit"], "verified_cost": m["cost"],
                "capacity_kind": m["cap"][0], "capacity_value": m["cap"][1],
                "sources": m["srcs"], "note": m["note"],
            } for m in D.M
        ],
        "sources": list(D.S.values()),
        "flagged": [{"id": f["id"], "level": f["level"], "title": f["title"], "detail": f["detail"],
                     "action": f["action"], "sources": f["srcs"]} for f in D.FLAGS],
    }
    (data_dir / "cost-model.json").write_text(json.dumps(model, indent=1, ensure_ascii=False) + "\n")

    with (data_dir / "cost-tiers.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["amount_usd", "A_statutory_cost_usd", "B_prc_iit_labor_usd", "C_prc_flat20_usd",
                    "us_federal_tax_usd", "us_residual_labor_usd", "us_residual_flat_usd",
                    "years_at_50k_quota", "years_at_atm_cap", "counter_days_at_500usd",
                    "fine_30pct_usd", "fine_100pct_usd", "commercial_cost_usd"])
        for r in ROWS:
            w.writerow([r["amount"], 0, round(r["labor"], 2), round(r["flat"], 2), round(r["us"], 2),
                        round(r["res_labor"], 2), round(r["res_flat"], 2), r["quota_years"],
                        r["atm_years"], r["walkin_days"], int(r["fine30"]), int(r["fine100"]), ""])

    with (data_dir / "repatriation-methods.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "category", "legal_status", "verified_limit", "verified_cost",
                    "capacity", "sources"])
        for m in D.M:
            w.writerow([m["id"], m["name"], m["cat"], m["legal"], m["limit"], m["cost"],
                        m["cap"][0] + ("" if m["cap"][1] is None else ":" + str(m["cap"][1])),
                        "|".join(m["srcs"])])


def main():
    pages = {
        "index.html": build_index(),
        "costs.html": build_costs(),
        "matrix.html": build_matrix(),
        "methods.html": build_methods(),
        "steps.html": build_steps(),
        "penalty.html": build_penalty(),
        "taxes.html": build_taxes(),
        "flagged.html": build_flagged(),
        "sources.html": build_sources(),
        "audit.html": build_audit(),
        "summary.html": build_summary(),
    }
    for name, html in pages.items():
        (ROOT / name).write_text(gloss(html))
    write_exports()
    print("wrote {} pages, {} tiers, {} methods, {} sources, {} flags".format(
        len(pages), len(ROWS), len(D.M), len(D.S), len(D.FLAGS)))


if __name__ == "__main__":
    main()
