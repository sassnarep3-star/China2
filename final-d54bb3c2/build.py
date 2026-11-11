#!/usr/bin/env python3
"""Static site generator for the final-d54bb3c2 section.

Reads only the JSON produced by model.py, penalties.py and the hand-checked
data files, and writes self-contained HTML pages (no external CSS or JS) so the
site works on GitHub Pages and on a phone.

Run: python3 build.py -> writes *.html in this folder.
"""

import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


SOURCES = load("sources.json")["sources"]
SRC_BY_ID = {s["id"]: s for s in SOURCES}
METHODS = load("methods.json")["methods"]
COSTS = load("costs.json")
PEN = load("penalties.json")
QUESTIONS = load("questions.json")
FLAGGED = load("flagged.json")
REVIEW = load("review.json")

NAV = [
    ("index.html", "Overview"),
    ("summary.html", "Executive summary"),
    ("costs.html", "Cost table"),
    ("methods.html", "Methods"),
    ("penalty.html", "Penalty breakdown"),
    ("questions.html", "Questions"),
    ("review.html", "Repo review"),
    ("flagged.html", "Flagged"),
    ("sources.html", "Sources"),
]

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#16181d;--muted:#5c6470;--line:#e3e6ea;
--accent:#0b5fff;--good:#0a7a45;--warn:#a85b00;--bad:#b3261e;--chip:#eef2f7}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{background:#0e1116;color:#fff;padding:14px 16px}
header .wrap{max-width:1080px;margin:0 auto}
header .t{font-weight:700;font-size:17px;letter-spacing:.2px}
header .s{color:#a9b1bd;font-size:13px;margin-top:2px}
nav{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5;
overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}
nav .wrap{max-width:1080px;margin:0 auto;padding:0 8px}
nav a{display:inline-block;padding:11px 10px;color:var(--muted);font-size:14px;font-weight:600}
nav a.on{color:var(--ink);box-shadow:inset 0 -2px 0 var(--accent)}
main{max-width:1080px;margin:0 auto;padding:18px 14px 60px}
h1{font-size:23px;line-height:1.25;margin:6px 0 6px}
h2{font-size:18px;margin:28px 0 8px}
h3{font-size:15px;margin:18px 0 6px}
p{margin:8px 0}
.lede{color:var(--muted);font-size:15px;margin:0 0 14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0}
.grid{display:grid;gap:12px}
@media(min-width:720px){.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}
.kpi .k{font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted)}
.kpi .v{font-size:22px;font-weight:700;margin:4px 0 0}
.kpi .n{font-size:12px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f0f2f5;font-size:12px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted)}
tbody tr:nth-child(even){background:#fafbfc}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:12px;background:#fff}
.chip{display:inline-block;background:var(--chip);border-radius:999px;padding:2px 9px;font-size:12px;
color:var(--muted);font-weight:600;margin:0 4px 4px 0}
.good{color:var(--good);font-weight:600}.warn{color:var(--warn);font-weight:600}.bad{color:var(--bad);font-weight:600}
.src{font-size:12px}
.src a{display:inline-block;background:#eef4ff;border:1px solid #dbe6ff;border-radius:6px;
padding:1px 6px;margin:2px 3px 2px 0;font-weight:600}
.blank{color:var(--muted);font-style:italic}
ul,ol{margin:6px 0 6px 18px;padding:0}
li{margin:3px 0}
.steps li{margin:6px 0}
details{border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:#fff;margin:8px 0}
summary{cursor:pointer;font-weight:600}
footer{max-width:1080px;margin:0 auto;padding:0 14px 40px;color:var(--muted);font-size:12px}
@media(max-width:640px){
  h1{font-size:20px}
  table.resp thead{display:none}
  table.resp,table.resp tbody,table.resp tr,table.resp td{display:block;width:100%}
  table.resp tr{border:1px solid var(--line);border-radius:10px;margin:8px 0;background:#fff;padding:6px 4px}
  table.resp td{border:0;padding:4px 10px;display:flex;justify-content:space-between;gap:10px;text-align:right}
  table.resp td::before{content:attr(data-label);color:var(--muted);font-size:12px;font-weight:600;
  text-transform:uppercase;letter-spacing:.3px;text-align:left}
  table.resp td.num{text-align:right}
}
"""


def page(slug, title, body, subtitle=""):
    nav = "".join(
        f'<a class="{"on" if f == slug else ""}" href="{f}">{html.escape(t)}</a>' for f, t in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · China money</title>
<style>{CSS}</style></head>
<body>
<header><div class="wrap"><div class="t">China money · final section d54bb3c2</div>
<div class="s">{html.escape(subtitle or "CNY to USD, verified against primary sources, 11 November 2026")}</div></div></header>
<nav><div class="wrap">{nav}</div></nav>
<main>
{body}
</main>
<footer>Every figure on this site is traceable to a page in the source ledger. Blank means unverified, not zero.
Built by session <code>arena/d54bb3c2-china2</code>. Not tax or legal advice.</footer>
</body></html>
"""


def srclinks(ids):
    out = []
    for i in ids:
        s = SRC_BY_ID.get(i)
        if s:
            out.append(f'<a href="sources.html#{i}" title="{html.escape(s["title"])}">{i}</a>')
        else:
            out.append(f'<span class="bad">{i}?</span>')
    return '<span class="src">' + "".join(out) + "</span>"


def money(x):
    return f"${x:,.2f}"


def pct(x):
    return f"{x:.4f}%".rstrip("0").rstrip(".") + ("" if "%" in f"{x:.4f}%" else "")


def pctf(x):
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return s + "%"


# ---------------------------------------------------------------- index
def build_index():
    r = COSTS["rates"]
    small = COSTS["rows"][0]
    mid = [x for x in COSTS["rows"] if x["usd"] == 100000][0]
    big = COSTS["rows"][-1]
    top = f"""
<h1>Getting money out of China: what it actually costs</h1>
<p class="lede">A verified, source-linked answer to one question: a US citizen has CNY stuck in a mainland bank account and needs USD.
What are the lawful routes, what does each cost at every USD 10,000 step up to USD 400,000, and what is the real penalty exposure?</p>

<div class="grid g3">
  <div class="kpi"><div class="k">Cheapest at USD 10,000</div><div class="v">{money(small['cheapest_total_usd'])}</div>
  <div class="n">{small['cheapest']} · {pctf(small[small['cheapest']]['pct'])} of the amount</div></div>
  <div class="kpi"><div class="k">Cheapest at USD 100,000</div><div class="v">{money(mid['cheapest_total_usd'])}</div>
  <div class="n">{mid['cheapest']} · {pctf(mid[mid['cheapest']]['pct'])} of the amount</div></div>
  <div class="kpi"><div class="k">Cheapest at USD 400,000</div><div class="v">{money(big['cheapest_total_usd'])}</div>
  <div class="n">{big['cheapest']} · {pctf(big[big['cheapest']]['pct'])} of the amount</div></div>
</div>

<div class="card">
<h2 style="margin-top:4px">The short answer</h2>
<ol>
<li><b>There is no tax on the conversion itself.</b> None of the 31 primary pages in the ledger imposes a tax on exchanging CNY for USD.
The "considerable tax" is almost always one of three things: the bank's FX spread, PRC income tax that was already due on the income, or US tax on the currency gain.</li>
<li><b>The real cost of a lawful conversion is small.</b> At the board rates read on 11 November 2026 the cheapest priced route costs
{money(small['cheapest_total_usd'])} on USD 10,000 and {money(big['cheapest_total_usd'])} on USD 400,000 — about {pctf(big[big['cheapest']]['pct'])}.</li>
<li><b>The expensive part is the paperwork ceiling, not the fee.</b> The USD 50,000 annual facilitation quota [S08] is the binding constraint for a domestic individual;
documented purchases and the emigrant transfer are the routes that go beyond it.</li>
<li><b>Penalties dwarf costs.</b> A single willful FBAR violation is USD 165,353 [S22]; an unlawful conversion treated as evasion is 30% of the amount,
up to 100% in serious cases [S09]. At USD 400,000 that is a USD 120,000 exposure against a USD 899 lawful cost.</li>
</ol>
<p><a href="summary.html">Read the executive summary →</a></p>
</div>

<div class="card">
<h2 style="margin-top:4px">Rates used in every calculation</h2>
<table class="resp"><thead><tr><th>Input</th><th>Value</th><th>Source</th></tr></thead><tbody>
<tr><td data-label="Input">BOC board, USD</td><td data-label="Value">buy {r['boc_buy']*100:.2f} / sell {r['boc_sell']*100:.2f} per 100 USD</td><td data-label="Source">{srclinks(['S01'])}</td></tr>
<tr><td data-label="Input">BOC spread to midpoint</td><td data-label="Value">{pctf(r['boc_spread_pct'])}</td><td data-label="Source">{srclinks(['S01'])}</td></tr>
<tr><td data-label="Input">HSBC board, USD</td><td data-label="Value">buy {r['hsbc_buy']:.7f} / sell {r['hsbc_sell']:.7f}</td><td data-label="Source">{srclinks(['S02'])}</td></tr>
<tr><td data-label="Input">HSBC spread to midpoint</td><td data-label="Value">{pctf(r['hsbc_spread_pct'])}</td><td data-label="Source">{srclinks(['S02'])}</td></tr>
<tr><td data-label="Input">BOC commission + cable</td><td data-label="Value">0.1%, min CNY 50, max CNY 260, + CNY 150</td><td data-label="Source">{srclinks(['S03'])}</td></tr>
<tr><td data-label="Input">HSBC commission + cable</td><td data-label="Value">0.1%, min CNY 100, max CNY 500, + CNY 120</td><td data-label="Source">{srclinks(['S04'])}</td></tr>
</tbody></table>
<p class="lede" style="margin-top:10px">Board timestamps: BOC {r['boc_board_timestamp']}, HSBC {r['hsbc_board_timestamp']}.
Rates move daily; the formulas on the cost page can be re-run with any board.</p>
</div>

<div class="card">
<h2 style="margin-top:4px">What is on each page</h2>
<table class="resp"><thead><tr><th>Page</th><th>Contents</th></tr></thead><tbody>
<tr><td data-label="Page"><a href="summary.html">Executive summary</a></td><td data-label="Contents">The recommendation, the numbers behind it, and the four things that actually cost money.</td></tr>
<tr><td data-label="Page"><a href="costs.html">Cost table</a></td><td data-label="Contents">USD 10,000 to USD 400,000 in USD 10,000 steps, every priced method, cheapest marked per row.</td></tr>
<tr><td data-label="Page"><a href="methods.html">Methods</a></td><td data-label="Contents">16 routes including the prohibited ones, each with pros, cons and step-by-step instructions.</td></tr>
<tr><td data-label="Page"><a href="penalty.html">Penalty breakdown</a></td><td data-label="Contents">Nine cost layers separated, with the lawful cost against the enforcement exposure at three sizes.</td></tr>
<tr><td data-label="Page"><a href="questions.html">Questions</a></td><td data-label="Contents">15 things that must be answered before a route can be chosen, with how to find each answer.</td></tr>
<tr><td data-label="Page"><a href="review.html">Repo review</a></td><td data-label="Contents">Line-by-line check of the rest of this repository, with irregularities flagged.</td></tr>
<tr><td data-label="Page"><a href="flagged.html">Flagged</a></td><td data-label="Contents">Every blank and every assumption, with the reason and the source link.</td></tr>
<tr><td data-label="Page"><a href="sources.html">Sources</a></td><td data-label="Contents">The full ledger of {len(SOURCES)} pages read, with the facts taken from each.</td></tr>
</tbody></table>
</div>
"""
    return page("index.html", "Overview", top)


# ---------------------------------------------------------------- summary
def build_summary():
    r = COSTS["rates"]
    rows = COSTS["rows"]
    small, big = rows[0], rows[-1]
    top5 = rows[:5]
    trs = "".join(
        f"<tr><td data-label='Amount' class='num'>${x['usd']:,}</td>"
        f"<td data-label='Cheapest route'>{x['cheapest']}</td>"
        f"<td data-label='Total cost' class='num'>{money(x['cheapest_total_usd'])}</td>"
        f"<td data-label='As % of amount' class='num'>{pctf(x[x['cheapest']]['pct'])}</td></tr>"
        for x in top5
    )
    body = f"""
<h1>Executive summary</h1>
<p class="lede">One conclusion, the evidence for it, and the limits of what the evidence supports.</p>

<div class="card">
<h2 style="margin-top:4px">Conclusion</h2>
<p><b>Move the money with a documented bank conversion and wire to your own US account, in the largest single transfer your documents support,
and stop treating the conversion as the taxable event.</b> On the rates read for this section that costs
{money(small['cheapest_total_usd'])} on USD 10,000 and {money(big['cheapest_total_usd'])} on USD 400,000 ({pctf(big[big['cheapest']]['pct'])}).
It is lawful, it uses only published prices, and it produces exactly the paper trail the US return needs.</p>
<p>Every alternative that looks cheap — a private swap, a quota split, a stablecoin leg — is priced in the penalty schedule, not in the fee schedule.
At USD 400,000 the enforcement exposure is {money(PEN['scenarios'][-1]['evasion_fine_low_usd'])} to
{money(PEN['scenarios'][-1]['evasion_fine_high_usd'])}, against {money(big['cheapest_total_usd'])} for doing it properly.</p>
</div>

<div class="grid g2">
<div class="card">
<h3 style="margin-top:0">Four things that actually cost money</h3>
<table class="resp"><thead><tr><th>#</th><th>Layer</th><th>Size</th><th>Source</th></tr></thead><tbody>
<tr><td data-label="#">1</td><td data-label="Layer">Bank FX spread, BOC</td><td data-label="Size">{pctf(r['boc_spread_pct'])} of the amount</td><td data-label="Source">{srclinks(['S01'])}</td></tr>
<tr><td data-label="#">2</td><td data-label="Layer">Bank FX spread, HSBC</td><td data-label="Size">{pctf(r['hsbc_spread_pct'])} of the amount</td><td data-label="Source">{srclinks(['S02'])}</td></tr>
<tr><td data-label="#">3</td><td data-label="Layer">Commission + cable</td><td data-label="Size">BOC max CNY 410 total; HSBC max CNY 620 total</td><td data-label="Source">{srclinks(['S03','S04'])}</td></tr>
<tr><td data-label="#">4</td><td data-label="Layer">US tax on the currency gain</td><td data-label="Size">{PEN['fx_gain_pct']}% gain in the worked example, ordinary rates, first USD 200 excluded</td><td data-label="Source">{srclinks(['S07','S27'])}</td></tr>
</tbody></table>
<p class="lede" style="margin-top:8px">PRC income tax on the source income is deliberately not in this list: it is due whether or not you convert [S20].</p>
</div>

<div class="card">
<h3 style="margin-top:0">Cost of the cheapest priced route</h3>
<table class="resp"><thead><tr><th>Amount</th><th>Route</th><th>Total</th><th>%</th></tr></thead><tbody>{trs}</tbody></table>
<p class="lede" style="margin-top:8px">Full 40-row ladder on the <a href="costs.html">cost page</a>.</p>
</div>
</div>

<div class="card">
<h2 style="margin-top:4px">Why the answer is not "pay the tax"</h2>
<p>No page in the ledger imposes a tax, surcharge or levy on an individual's purchase of USD with CNY.
The PRC rules that mention conversion are documentation and quota rules, and the enforcement provisions penalise evasion, arbitrage and
unlawful trading — not lawful conversion [S08, S09, S19]. The US side taxes the currency gain, and excludes only the first USD 200 of a
personal-transaction gain [S27]. So a lawful conversion is cheap, and the expensive outcomes in this problem come from how the money is moved,
not from the fact that it is converted.</p>
<p>What the rules do constrain is <b>volume and evidence</b>: a domestic individual gets USD 50,000 a year without prior approval [S08 Art.2];
beyond that you need a documented China-source income stream [S10, S11] or an approved emigrant property transfer [S13, S14].</p>
</div>

<div class="card">
<h2 style="margin-top:4px">Action order</h2>
<ol class="steps">
<li><b>Fix your US filing position first.</b> FBAR above USD 10,000 aggregate [S21], Form 8938 at its own thresholds [S23].
A clean history costs nothing; a missed willful year is USD 165,353 [S22]. If years are missing, the streamlined procedures exist for non-willful cases [S30].</li>
<li><b>Document the source of the balance.</b> Match every large credit to a contract, payslip, deed or dividend notice, and obtain the tax record for each year [S14, S20].</li>
<li><b>Pick the route by amount.</b> Under about USD 21,000 the HSBC Premier transfer is cheapest in the model because BOC's minimum-fee and cable floor dominate;
above that the BOC wire wins because its commission is capped [S03, S04].</li>
<li><b>Send a small test transfer first</b> and read the credited amount; correspondent charges are not published [S03, S04] and are flagged.</li>
<li><b>Record the USD basis of every conversion</b> at the rate used, so the section 988 gain is computed from evidence [S07, S27].</li>
</ol>
</div>

<div class="card">
<h2 style="margin-top:4px">What this section cannot tell you</h2>
<p>The model answers "what does a lawful conversion cost". It cannot answer "which route is available to you", because that depends on your
nationality, hukou status, income history and filing record. Those are the 15 questions on the <a href="questions.html">questions page</a>.
Items that could not be confirmed from an official page are on the <a href="flagged.html">flagged page</a> and are excluded from the arithmetic.</p>
</div>
"""
    return page("summary.html", "Executive summary", body)


# ---------------------------------------------------------------- costs
def build_costs():
    r = COSTS["rates"]
    head = """<tr><th>Amount (USD)</th><th>BOC wire<br><span class="lede">0.2094% + CNY 410 max</span></th>
<th>HSBC wire<br><span class="lede">0.4979% + CNY 620 max</span></th>
<th>HSBC Premier GT<br><span class="lede">0.4979%, fee 0</span></th>
<th>HSBC Advance GT<br><span class="lede">0.4979% + USD 20</span></th>
<th>Cheapest</th><th>Source</th></tr>"""
    trs = []
    for x in COSTS["rows"]:
        c = x["cheapest"]
        trs.append(
            f"<tr><td data-label='Amount' class='num'><b>${x['usd']:,}</b></td>"
            f"<td data-label='BOC wire' class='num'>{money(x['M01']['total_usd'])}<br><span class='lede'>{pctf(x['M01']['pct'])}</span></td>"
            f"<td data-label='HSBC wire' class='num'>{money(x['M02']['total_usd'])}<br><span class='lede'>{pctf(x['M02']['pct'])}</span></td>"
            f"<td data-label='HSBC Premier GT' class='num'>{money(x['M03']['total_usd'])}<br><span class='lede'>{pctf(x['M03']['pct'])}</span></td>"
            f"<td data-label='HSBC Advance GT' class='num'>{money(x['M04']['total_usd'])}<br><span class='lede'>{pctf(x['M04']['pct'])}</span></td>"
            f"<td data-label='Cheapest'><span class='good'>{c}</span> {money(x['cheapest_total_usd'])}</td>"
            f"<td data-label='Source' class='src'><a href='sources.html#S01'>S01</a><a href='sources.html#S03'>S03</a>"
            f"<a href='sources.html#S02'>S02</a><a href='sources.html#S04'>S04</a></td></tr>"
        )
    x10 = COSTS["rows"][0]
    x40 = COSTS["rows"][-1]
    body = f"""
<h1>Cost of converting and transferring, USD 10,000 to USD 400,000</h1>
<p class="lede">Bank spread plus published bank fees, per method, at the board rates read on 11 November 2026.
Rows are USD 10,000 steps; each cell shows the total cost and, underneath, the same cost as a percentage of the amount moved.</p>

<div class="grid g3">
<div class="kpi"><div class="k">USD 10,000 best</div><div class="v">{money(x10['cheapest_total_usd'])}</div><div class="n">{x10['cheapest']} · {pctf(x10[x10['cheapest']]['pct'])}</div></div>
<div class="kpi"><div class="k">USD 200,000 best</div><div class="v">{money([x for x in COSTS['rows'] if x['usd']==200000][0]['cheapest_total_usd'])}</div><div class="n">BOC wire · {pctf([x for x in COSTS['rows'] if x['usd']==200000][0]['M01']['pct'])}</div></div>
<div class="kpi"><div class="k">USD 400,000 best</div><div class="v">{money(x40['cheapest_total_usd'])}</div><div class="n">{x40['cheapest']} · {pctf(x40[x40['cheapest']]['pct'])}</div></div>
</div>

<div class="card">
<h2 style="margin-top:4px">How each cell is calculated</h2>
<p>Buying USD X at the bank's sell rate costs X × sell CNY. At the midpoint of the bank's buy and sell rates it would cost X × mid,
so the spread cost in USD is X × (sell − mid) ÷ sell. The commission is the published percentage with its published floor and cap,
plus the published cable charge, divided by the sell rate to express it in USD. Total = spread + fee. No correspondent charge is added,
because neither bank publishes one.</p>
<p>Inputs: BOC buy {r['boc_buy']*100:.2f}, sell {r['boc_sell']*100:.2f} per 100 USD [S01]; HSBC buy {r['hsbc_buy']:.7f}, sell {r['hsbc_sell']:.7f} [S02];
BOC 0.1% floor CNY 50 cap CNY 260 plus CNY 150 [S03]; HSBC 0.1% floor CNY 100 cap CNY 500 plus CNY 120 [S04];
Global Transfer to self free for Premier and USD 20 for Advance [S04].</p>
<p class="src">Sources for this table: {srclinks(['S01','S02','S03','S04'])}</p>
</div>

<h2>Full ladder</h2>
<div class="scroll"><table class="resp"><thead>{head}</thead><tbody>{''.join(trs)}</tbody></table></div>
<p class="lede" style="margin-top:8px">Every row is computed, not copied. To reproduce: <code>python3 model.py</code> in this folder.
Each row cites its four inputs: BOC board and fee schedule (S01, S03) and HSBC board and tariff (S02, S04).</p>
<div class="card"><p><b>For orientation only, not used in any calculation:</b> the Federal Reserve H.10 noon buying rate for
2026-11-06 was 6.6760 CNY per USD {srclinks(['S06'])}. The banks set their own buying and selling rates, so the Fed rate cannot
price a retail conversion; it is quoted here only so the spread can be seen against an independent published reference.
The BOC sell rate used above is 6.6871, which is 0.167% above the Fed noon rate.</p></div>

<div class="card">
<h2 style="margin-top:4px">Methods with no published price</h2>
<table class="resp"><thead><tr><th>Method</th><th>Cost</th><th>Why blank</th></tr></thead><tbody>
<tr><td data-label="Method">M06 UnionPay card abroad</td><td data-label="Cost" class="blank">blank</td><td data-label="Why blank">No official page read publishes the card FX fee or spread.</td></tr>
<tr><td data-label="Method">M07 Wise CNY→USD</td><td data-label="Cost" class="blank">blank</td><td data-label="Why blank">The Wise help page describes eligibility and limits but not the fee for this corridor.</td></tr>
<tr><td data-label="Method">M08 / M09 approval and documented routes</td><td data-label="Cost">bank layer only</td><td data-label="Why blank">SAFE charges no fee; the cost is the M01/M02 bank spread and wire fee, plus any professional help, which is not published.</td></tr>
<tr><td data-label="Method">M05 cash carry</td><td data-label="Cost">{money(x10['M05']['total_usd'])} per USD 10,000</td><td data-label="Why blank">Spread only, no wire fee, but capped at USD 10,000 per traveller per trip, so USD 400,000 needs 40 trips and travel cost is excluded.</td></tr>
</tbody></table>
</div>

<div class="card">
<h2 style="margin-top:4px">Reading the numbers</h2>
<ul>
<li><b>Under USD 21,000</b> the HSBC Premier transfer is cheapest, because BOC's CNY 50 floor plus CNY 150 cable is a bigger drag than the wider HSBC spread at small size.</li>
<li><b>Above USD 21,000</b> the BOC wire is cheapest at every single step, because its commission stops at CNY 260 while HSBC's spread never stops.</li>
<li><b>Percentages fall as the amount rises</b> for both banks: the capped fee is a smaller share, while the spread stays constant.</li>
<li><b>The Premier monthly fee of CNY 300 is excluded</b> from the M03 column; see flagged item F-07.</li>
</ul>
</div>
"""
    return page("costs.html", "Cost table", body)


# ---------------------------------------------------------------- methods
def build_methods():
    priced = [m for m in METHODS if m["priced"]]
    rest = [m for m in METHODS if not m["priced"]]
    lawful = [m for m in rest if not m["legality"].startswith("Prohibited")]
    bad = [m for m in rest if m["legality"].startswith("Prohibited")]

    def card(m):
        pros = "".join(f"<li>{html.escape(p)}</li>" for p in m["pros"]) or "<li class='blank'>none</li>"
        cons = "".join(f"<li>{html.escape(c)}</li>" for c in m["cons"]) or "<li class='blank'>none</li>"
        steps = "".join(f"<li>{html.escape(s)}</li>" for s in m["steps"])
        steps_html = f'<h4>Step by step</h4><ol class="steps">{steps}</ol>' if steps else ""
        formula = f"<p class='lede'><b>Formula:</b> <code>{html.escape(m['formula'])}</code></p>" if m["formula"] else ""
        return f"""
<details>
<summary>{html.escape(m['id'])} · {html.escape(m['name'])} <span class="chip">{html.escape(m['category'])}</span>
<span class="chip">{'priced' if m['priced'] else 'not priced'}</span></summary>
<p><b>Legality:</b> {html.escape(m['legality'])}<br>
<b>Who it is for:</b> {html.escape(m['who'])}<br>
<b>Limit:</b> {html.escape(m['limit'])}<br>
<b>Speed:</b> {html.escape(m['speed'])}<br>
<b>Cost basis:</b> {html.escape(m['cost_basis'])}</p>
{formula}
<div class="grid g2"><div><h4>Pros</h4><ul>{pros}</ul></div><div><h4>Cons</h4><ul>{cons}</ul></div></div>
{steps_html}
<p class="src">Sources: {srclinks(m['sources']) if m['sources'] else '<span class="blank">none — see flagged item</span>'}</p>
</details>"""

    body = f"""
<h1>Every route, with pros, cons and steps</h1>
<p class="lede">{len(METHODS)} routes were checked. {len(priced)} have a published price and appear in the cost ladder;
{len(lawful)} more are lawful but unpriced or structured differently; {len(bad)} are prohibited and are listed so the cost of using them is visible.</p>

<div class="card">
<h2 style="margin-top:4px">The three lawful shapes of a solution</h2>
<ol>
<li><b>Convert inside the annual quota.</b> Up to USD 50,000 per person per year without prior approval [S08 Art.2]. Cheapest, simplest, slowest to clear a large balance.</li>
<li><b>Convert against documented China-source income.</b> Identity document plus source materials and tax vouchers; not capped at USD 50,000, but each purchase is reviewed [S08 Art.13, S10, S11].</li>
<li><b>Emigrant property transfer.</b> A dedicated approval for a whole pre-emigration balance, no SAFE fee, no staging since 2014 [S12, S13, S14]. Requires emigrant status and a cancelled hukou.</li>
</ol>
</div>

<h2>Priced routes</h2>
{''.join(card(m) for m in priced)}

<h2>Lawful routes without a published price</h2>
{''.join(card(m) for m in lawful)}

<h2>Prohibited routes</h2>
<p class="lede">Listed for completeness. Each carries a statutory penalty on the amount moved, not a fee.</p>
{''.join(card(m) for m in bad)}
"""
    return page("methods.html", "Methods", body)


# ---------------------------------------------------------------- penalty
def build_penalty():
    layers = "".join(
        f"<tr><td data-label='Layer'><b>{l['id']}</b> {html.escape(l['layer'])}</td>"
        f"<td data-label='Who pays'>{html.escape(l['who'])}</td>"
        f"<td data-label='Size'>{html.escape(l['amount'])}</td>"
        f"<td data-label='Basis'>{html.escape(l['basis'])}</td>"
        f"<td data-label='Sources'>{srclinks(l['sources'])}</td></tr>"
        for l in PEN["layers"]
    )
    scen = "".join(
        f"<tr><td data-label='Amount' class='num'>${s['usd']:,}</td>"
        f"<td data-label='Lawful BOC cost' class='num good'>{money(s['lawful_boc_cost_usd'])}</td>"
        f"<td data-label='US FX gain' class='num'>{money(s['fx_gain_usd'])}</td>"
        f"<td data-label='Evasion fine 30%' class='num bad'>{money(s['evasion_fine_low_usd'])}</td>"
        f"<td data-label='Evasion fine up to 100%' class='num bad'>{money(s['evasion_fine_high_usd'])}</td>"
        f"<td data-label='One willful FBAR' class='num bad'>{money(s['fbar_willful_usd'])}</td></tr>"
        for s in PEN["scenarios"]
    )
    s4 = PEN["scenarios"][-1]
    body = f"""
<h1>The conversion penalty, broken into its actual parts</h1>
<p class="lede">"Penalty" in this problem means at least nine different things. They are separated here so each can be sized and, where possible, avoided.
Layers P1, P2 and P6 are unavoidable in any lawful conversion. P4 is not a conversion cost at all. P7 and P8 are the layers that can ruin the outcome.</p>

<div class="scroll"><table class="resp"><thead><tr><th>Layer</th><th>Who pays</th><th>Size</th><th>Basis</th><th>Source</th></tr></thead><tbody>{layers}</tbody></table></div>

<h2>Lawful cost against enforcement exposure</h2>
<div class="scroll"><table class="resp"><thead><tr><th>Amount</th><th>Lawful BOC cost</th><th>US FX gain at {PEN['fx_gain_pct']}%</th>
<th>Evasion fine at 30%</th><th>Evasion fine up to 100%</th><th>One willful FBAR year</th></tr></thead><tbody>{scen}</tbody></table></div>
<p class="src" style="margin-top:8px">Sources: {srclinks(['S01','S03','S07','S09','S22','S27'])}</p>

<div class="card">
<h2 style="margin-top:4px">What the table says</h2>
<ul>
<li>At USD 400,000 the lawful conversion costs <b>{money(s4['lawful_boc_cost_usd'])}</b>. The same amount treated as evasion carries a floor fine of
<b>{money(s4['evasion_fine_low_usd'])}</b> and a serious-case maximum of <b>{money(s4['evasion_fine_high_usd'])}</b> [S09 Art.39].</li>
<li>One willful FBAR year (<b>{money(s4['fbar_willful_usd'])}</b>) costs more than the lawful conversion of USD 400,000 by a factor of
{s4['fbar_willful_usd']/s4['lawful_boc_cost_usd']:.0f} [S22]. A single non-willful year is {money(s4['fbar_nonwillful_usd'])}.</li>
<li>The US currency gain of about {PEN['fx_gain_pct']}% is real but small next to either penalty layer; it is ordinary income, and only the first
USD 200 of a personal-transaction gain is excluded [S27].</li>
<li>PRC income tax (P4) is not caused by converting. It is due on the income whether or not the money moves, with a 0.05% per day surcharge if late [S20, S31].</li>
</ul>
</div>

<div class="card">
<h2 style="margin-top:4px">Worked example</h2>
<p>{html.escape(PEN['worked_example']['text'])}</p>
<p class="src">Sources: {srclinks(PEN['worked_example']['sources'])}</p>
</div>

<div class="card">
<h2 style="margin-top:4px">Three ways the penalty gets triggered by accident</h2>
<ol>
<li><b>Quota splitting.</b> Using relatives' USD 50,000 quotas to move a large balance is expressly prohibited; it puts you on a watch list for two years [S15].</li>
<li><b>Mislabeling.</b> Describing capital as a service payment does not survive the tax filing review that applies at USD 50,000 and above [S19], and is treated as evasion [S09].</li>
<li><b>Silence on the US side.</b> Not filing the FBAR or Form 8938 does not become cheaper by moving the money; the penalty attaches to the account years [S21, S23, S22].</li>
</ol>
</div>
"""
    return page("penalty.html", "Penalty breakdown", body)


# ---------------------------------------------------------------- questions
def build_questions():
    cards = []
    for q in QUESTIONS["questions"]:
        cards.append(f"""
<details>
<summary>Q{q['id'][1:]} · {html.escape(q['question'])} <span class="chip">{html.escape(q['group'])}</span></summary>
<p><b>Why it matters.</b> {html.escape(q['why'])}</p>
<p><b>What is already known.</b> {html.escape(q['known'])}</p>
<p><b>What is missing.</b> {html.escape(q['missing'])}</p>
<p><b>How to find it.</b> {html.escape(q['how'])}</p>
<p class="src">Sources: {srclinks(q['sources'])}</p>
</details>""")
    body = f"""
<h1>Questions that must be answered before choosing a route</h1>
<p class="lede">{html.escape(QUESTIONS['intro'])}</p>
<div class="card">
<h2 style="margin-top:4px">The decision tree in one table</h2>
<table class="resp"><thead><tr><th>If this is true</th><th>Then the route is</th><th>Source</th></tr></thead><tbody>
<tr><td data-label="If this is true">You are a mainland individual, moving under USD 50,000 a year</td><td data-label="Route">Bank conversion plus wire inside the annual quota</td><td data-label="Source">{srclinks(['S08'])}</td></tr>
<tr><td data-label="If this is true">You are a foreign national with taxed China-source salary in the account</td><td data-label="Route">Documented purchase against that income</td><td data-label="Source">{srclinks(['S08','S10','S11'])}</td></tr>
<tr><td data-label="If this is true">You hold foreign PR or citizenship and cancelled your hukou, and the assets predate it</td><td data-label="Route">Emigrant property transfer approval</td><td data-label="Source">{srclinks(['S13','S14'])}</td></tr>
<tr><td data-label="If this is true">None of the above, and the balance is large</td><td data-label="Route">Split across calendar years inside the quota, or resolve the status question first</td><td data-label="Source">{srclinks(['S08','S14'])}</td></tr>
</tbody></table>
</div>
<h2>All 15 questions</h2>
{''.join(cards)}
"""
    return page("questions.html", "Questions", body)


# ---------------------------------------------------------------- review
def build_review():
    sev = {"high": "bad", "medium": "warn", "low": ""}
    rows = "".join(
        f"<tr><td data-label='#'>{i['id']}</td>"
        f"<td data-label='Severity'><span class='{sev.get(i['severity'],'')}'>{html.escape(i['severity'])}</span></td>"
        f"<td data-label='File'><code>{html.escape(i['file'])}</code></td>"
        f"<td data-label='Finding'>{html.escape(i['finding'])}</td>"
        f"<td data-label='Effect'>{html.escape(i['effect'])}</td>"
        f"<td data-label='Sources'>{srclinks(i['sources'])}</td></tr>"
        for i in REVIEW["irregularities"]
    )
    stats = "".join(
        f"<tr><td data-label='Check'>{html.escape(c['check'])}</td>"
        f"<td data-label='Result' class='num'>{html.escape(str(c['result']))}</td>"
        f"<td data-label='Detail'>{html.escape(c['detail'])}</td></tr>"
        for c in REVIEW["checks"]
    )
    body = f"""
<h1>Repository review, line by line</h1>
<p class="lede">{html.escape(REVIEW['method'])}</p>

<div class="card">
<h2 style="margin-top:4px">Mechanical checks</h2>
<div class="scroll"><table class="resp"><thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead><tbody>{stats}</tbody></table></div>
</div>

<h2>Irregularities flagged</h2>
<p class="lede">Each item is a place where the repository states or implies something that a primary source does not support, or where two sections disagree.
None of them is silently corrected in another session's files; they are reported here and, where they affect the price, this section publishes the verified value instead.</p>
<div class="scroll"><table class="resp"><thead><tr><th>#</th><th>Severity</th><th>File</th><th>Finding</th><th>Effect</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="lede" style="margin-top:10px">Counts: {len(REVIEW['irregularities'])} irregularities, {REVIEW['totals']['files_scanned']} files scanned,
{REVIEW['totals']['checks_run']:,} mechanical checks. Generated by <code>review.py</code>; re-run to reproduce.</p>
"""
    return page("review.html", "Repo review", body)


# ---------------------------------------------------------------- flagged
def build_flagged():
    rows = "".join(
        f"<tr><td data-label='#'>{f['id']}</td>"
        f"<td data-label='Item'>{html.escape(f['item'])}</td>"
        f"<td data-label='Status'>{html.escape(f['status'])}</td>"
        f"<td data-label='Why it is blank or assumed'>{html.escape(f['reason'])}</td>"
        f"<td data-label='What would settle it'>{html.escape(f['action'])}</td>"
        f"<td data-label='Sources'>{srclinks(f['sources']) if f['sources'] else '<span class=blank>none</span>'}</td></tr>"
        for f in FLAGGED["items"]
    )
    body = f"""
<h1>Flagged for review</h1>
<p class="lede">Everything on this site that is blank, assumed, or ambiguous. Blank means unverified, never zero.
Nothing in this list blocks publication; it is the list to work through if you want the numbers tightened.</p>
<div class="card">
<p><b>{len(FLAGGED['items'])} items.</b> Two kinds: <span class="chip">blank</span> no official value was published on the pages read,
and <span class="chip">assumption</span> a reasoning step was needed and is stated openly.</p>
</div>
<div class="scroll"><table class="resp"><thead><tr><th>#</th><th>Item</th><th>Status</th><th>Why</th><th>What would settle it</th><th>Sources</th></tr></thead><tbody>{rows}</tbody></table></div>
"""
    return page("flagged.html", "Flagged for review", body)


# ---------------------------------------------------------------- sources
def build_sources():
    cards = []
    for s in SOURCES:
        facts = "".join(f"<li>{html.escape(f)}</li>" for f in s["facts"])
        badge = "good" if s["status"] == "verified" else "warn"
        cards.append(f"""
<div class="card" id="{s['id']}">
<h3 style="margin-top:0">{s['id']} · {html.escape(s['title'])} <span class="chip {badge}">{html.escape(s['status'])}</span></h3>
<p class="lede">{html.escape(s['issuer'])} · {html.escape(s['kind'])}</p>
<p><a href="{html.escape(s['url'])}" rel="noopener">{html.escape(s['url'])}</a></p>
<ul>{facts}</ul>
<p class="lede"><b>Excerpt:</b> {html.escape(s['quote'])}</p>
</div>""")
    body = f"""
<h1>Source ledger</h1>
<p class="lede">{len(SOURCES)} pages, all opened on 11 November 2026. Each entry lists the facts taken from that page and a short excerpt.
Facts are what the site relies on; anything not in this ledger is not used.</p>
<div class="card">
<p><b>Composition.</b> Banks and their tariffs: BOC and HSBC China boards and fee schedules. PRC regulators: SAFE (rules, Q&amp;As, a provincial
service guide), PBOC (property transfer, virtual currency), the tax administration (IIT law, collection law, outward-payment filing).
US authorities: IRS (FBAR, 8938, foreign tax credit, streamlined procedures, FEIE, yearly averages, Rev. Proc. 2026-35, Form 3520 guidance),
the Federal Reserve (H.10), CBP, the eCFR and the U.S. Code.
One provider page (Wise) is included because it is the only non-bank CNY corridor with an official description.</p>
</div>
{''.join(cards)}
"""
    return page("sources.html", "Sources", body)


def main():
    outputs = {
        "index.html": build_index(),
        "summary.html": build_summary(),
        "costs.html": build_costs(),
        "methods.html": build_methods(),
        "penalty.html": build_penalty(),
        "questions.html": build_questions(),
        "review.html": build_review(),
        "flagged.html": build_flagged(),
        "sources.html": build_sources(),
    }
    for name, content in outputs.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
            fh.write(content)
    print("wrote", ", ".join(outputs))


if __name__ == "__main__":
    main()
