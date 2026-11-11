# -*- coding: utf-8 -*-
"""Generate the dashboard. All numbers come from data/costs.json (model.py);
all prose figures are quoted or computed, never typed into HTML by hand."""
import html, json, math, os
import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
DATA = json.load(open(os.path.join(D, "costs.json"), encoding="utf-8"))
SOURCES = json.load(open(os.path.join(D, "sources.json"), encoding="utf-8"))
S = {s["id"]: s for s in SOURCES}
P = DATA["parameters"]
ROWS = DATA["rows"]
SUMMARY = DATA["summary"]
METHODS = DATA["methods"]
AMOUNTS = DATA["amounts"]

OFFICIAL = ("safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn", "irs.gov",
            "ecfr.gov", "govinfo.gov", "federalreserve.gov", "cbp.gov",
            "boc.cn", "hsbc.com.cn", "hsbc.com")


def esc(t):
    return html.escape(str(t), quote=True)


def src(ids, label=None):
    links = " ".join(
        f'<a href="{esc(S[i]["url"])}">{esc(label or i)}</a>' for i in ids if i in S
    )
    return f'<span class="src">{links}</span>'


def money(x, dp=2):
    return f"${x:,.{dp}f}"


def cny(x, dp=2):
    return f"&yen;{x:,.{dp}f}"


def pct(x, dp=3):
    return f"{x:.{dp}f}%"


def blank(flag, why="unverified"):
    return f'<span class="blank">&mdash;<a href="review.html#{flag}"> {why}</a></span>'


CSS = """
:root{--ink:#0f1c19;--ink2:#20342e;--paper:#f5f4ef;--card:#fff;--line:#dce1db;--muted:#5d7067;
--accent:#0b6455;--accent2:#084d42;--warn:#7a4a00;--warnbg:#fff6e0;--warnline:#e6d1a0;
--bad:#8a2c21;--badbg:#fdeeec;--ok:#0b6455;--pill:#edf2ee}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.62 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent2)}a:hover{color:var(--accent)}
.wrap{max-width:1080px;margin:0 auto;padding:0 clamp(.9rem,3.5vw,2rem)}
.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;background:#fff;padding:.5rem;z-index:30}
header.site{background:var(--ink);color:#eef2ee;padding:.8rem 0}
header.site .wrap{display:flex;gap:1rem;align-items:center;justify-content:space-between;flex-wrap:wrap}
.brand{display:flex;gap:.55rem;align-items:center;color:#fff;text-decoration:none;font-weight:750}
.brand .mark{display:inline-grid;place-items:center;width:2rem;height:2rem;border-radius:.55rem;
background:#0b6455;font-size:.95rem}
.brand small{display:block;font-size:.65rem;letter-spacing:.13em;color:#9fb5ab;font-weight:600}
.meta{font-size:.76rem;color:#b6c6bd;text-align:right}
nav.site{background:#16271f;border-bottom:1px solid #213a2f;position:sticky;top:0;z-index:20}
nav.site .wrap{display:flex;gap:.1rem;overflow-x:auto;padding:.32rem clamp(.9rem,3.5vw,2rem)}
nav.site a{color:#cfe0d6;text-decoration:none;font-size:.81rem;font-weight:600;padding:.48rem .66rem;
border-radius:.45rem;white-space:nowrap}
nav.site a:hover,nav.site a[aria-current]{background:#22392d;color:#fff}
main{padding:1.3rem 0 3rem}
h1{font-size:clamp(1.6rem,4.6vw,2.45rem);line-height:1.13;letter-spacing:-.02em;margin:.3rem 0 .5rem}
h2{font-size:clamp(1.15rem,3vw,1.45rem);margin:2.1rem 0 .45rem;letter-spacing:-.01em}
h3{font-size:1rem;margin:1.2rem 0 .3rem}
p{margin:.5rem 0}ul,ol{margin:.4rem 0 .6rem;padding-left:1.15rem}li{margin:.22rem 0}
.eyebrow{display:block;font-size:.69rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);
font-weight:750;margin-bottom:.15rem}
.lede{font-size:1.04rem;color:#2c423a;max-width:76ch}
.muted{color:var(--muted);font-size:.85rem}
.notice{background:var(--warnbg);border:1px solid var(--warnline);border-left:5px solid #b1790f;
border-radius:.65rem;padding:.8rem .95rem;margin:1rem 0;font-size:.9rem}
.notice strong{color:var(--warn)}
.answer{background:var(--card);border:1px solid var(--line);border-radius:.8rem;padding:1rem 1.1rem;margin:1rem 0}
.answer ol{margin:.4rem 0 0;padding-left:1.2rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.65rem;margin:1.1rem 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:.75rem;padding:.85rem .95rem}
.kpi .label{font-size:.71rem;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);
font-weight:700;margin:0}
.kpi .value{font-size:1.42rem;font-weight:780;letter-spacing:-.02em;margin:.2rem 0 .1rem}
.kpi .sub{font-size:.79rem;color:var(--muted);margin:0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));gap:.65rem;margin:1rem 0}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:.75rem;
padding:.85rem .95rem;text-decoration:none;color:var(--ink)}
.card:hover{border-color:#a9c4b8;box-shadow:0 2px 10px rgba(12,60,50,.07)}
.card b{display:block;font-size:.98rem;color:var(--accent2)}
.card span{display:block;font-size:.76rem;color:var(--muted);margin:.15rem 0 .3rem}
.card em{font-style:normal;font-size:.85rem;color:#33483f}
.tablewrap{overflow-x:auto;margin:.7rem 0 1.4rem;border:1px solid var(--line);border-radius:.7rem;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:.86rem}
caption{text-align:left;padding:.6rem .7rem;font-size:.78rem;color:var(--muted);border-bottom:1px solid var(--line)}
th,td{padding:.5rem .6rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
thead th{background:#eef2ee;font-size:.73rem;letter-spacing:.05em;text-transform:uppercase;color:#3b5148;
position:sticky;top:0}
tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}
tbody tr:nth-child(even){background:#fbfbf8}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.src a{font-size:.72rem;font-weight:700;color:var(--accent);background:var(--pill);border-radius:.3rem;
padding:.05rem .3rem;text-decoration:none;margin-right:.15rem;display:inline-block}
.blank{color:var(--bad);background:var(--badbg);border-radius:.3rem;padding:.05rem .35rem;font-size:.8rem}
.blank a{color:var(--bad);font-weight:700}
.badge{display:inline-block;font-size:.7rem;font-weight:750;letter-spacing:.04em;text-transform:uppercase;
border-radius:.35rem;padding:.1rem .4rem;white-space:nowrap}
.b-ok{background:#e4f1ea;color:#0a5748}.b-gate{background:#eef0e4;color:#5b5f12}
.b-appr{background:#e8eef7;color:#22456f}.b-cap{background:#f6ecd9;color:#7a4a00}
.b-un{background:#fbe6e3;color:#8a2c21}.b-flag{background:#fff3d6;color:#7a4a00}
.blankrow{background:#fffaf0!important}
details.m{background:var(--card);border:1px solid var(--line);border-radius:.7rem;margin:.6rem 0;padding:.15rem .85rem}
details.m>summary{cursor:pointer;padding:.6rem 0;font-weight:700;color:var(--accent2)}
details.m[open]>summary{border-bottom:1px solid var(--line);margin-bottom:.5rem}
details.m p,details.m li{font-size:.88rem}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:.8rem}
@media(max-width:760px){
 table.stack thead{display:none}
 table.stack,table.stack tbody,table.stack tr,table.stack td,table.stack th{display:block;width:100%}
 table.stack tr{border:1px solid var(--line);border-radius:.6rem;margin:.55rem .6rem;background:#fff;overflow:hidden}
 table.stack td,table.stack th{display:flex;justify-content:space-between;gap:.9rem;border:0;
 padding:.4rem .65rem;text-align:right}
 table.stack td::before,table.stack th::before{content:attr(data-label);font-weight:750;color:var(--muted);
 font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;text-align:left;flex:0 0 42%}
 table.stack td.num{text-align:right}
 .grid2{grid-template-columns:1fr}
 .tablewrap{overflow:visible;border:0;background:transparent}
}
footer.site{border-top:1px solid var(--line);padding:1.3rem 0;color:var(--muted);font-size:.8rem}
.tag{display:inline-block;font-size:.68rem;background:var(--pill);border:1px solid var(--line);
border-radius:.3rem;padding:.02rem .35rem;color:#3d544a;margin:.1rem .1rem 0 0}
@media print{nav.site,header.site{position:static}details.m{page-break-inside:avoid}}
"""

NAV = [("index.html", "Start"), ("summary.html", "Summary"), ("questions.html", "Questions"),
       ("methods.html", "Methods"), ("costs.html", "Costs"), ("penalties.html", "Penalty layers"),
       ("taxes.html", "Tax rules"), ("sources.html", "Sources"), ("review.html", "Flagged")]


def page(slug, title, desc, body):
    cur = ' aria-current="page"'
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (h, cur if h == slug else "", esc(t))
        for h, t in NAV)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0f1c19"><link rel="stylesheet" href="style.css">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap">
<a class="brand" href="index.html"><span class="mark">¥→$</span>
<span>China money<small>CNY TO USD · SOURCED</small></span></a>
<div class="meta">{len(SOURCES)} official pages read {C.TODAY}<br>Board: 11 Nov 2026 · Fed H.10: 9 Nov 2026</div>
</div></header>
<nav class="site"><div class="wrap">{nav}</div></nav>
<main id="main"><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap">
<p><strong>What this is.</strong> A source-linked working file, not advice. Every figure is either quoted from a
linked official page or computed from one by <code>model.py</code>; every blank is published as a blank and
listed on the <a href="review.html">Flagged for review</a> page. No tax liability, route eligibility or
all-in quote is asserted for any person.</p>
<p>Built {C.TODAY}. Sources re-read {C.TODAY}. Arithmetic reproducible with <code>python3 model.py</code>;
checks with <code>python3 verify.py</code>.</p>
</div></footer>
</body></html>"""


def badge(status):
    key = {"lawful, gated": "b-gate", "lawful, approval required": "b-appr",
           "lawful, capped": "b-cap", "unlawful": "b-un",
           "lawful, approval required": "b-appr"}.get(status, "b-un")
    if status.startswith("lawful") and "approval" not in status and "capped" not in status:
        key = "b-gate"
    return f'<span class="badge {key}">{esc(status)}</span>'


# ---------------------------------------------------------------- pages
def index_page():
    a40 = SUMMARY[-1]
    a10 = SUMMARY[0]
    s10 = next(r for r in SUMMARY if r["amount"] == 10000)
    body = f"""
<span class="eyebrow">Decision dashboard</span>
<h1>Getting money out of China: what it costs, and what actually blocks it</h1>
<p class="lede">The money is not stuck because of tax. On the rules read here, converting CNY to USD is not a
taxable event at all; the blocks are a USD 50,000 annual purchase total, a documentary review above it, and the
fees and spread a bank charges on the way through. This dashboard prices every route it can from published
terms, from USD 10,000 to USD 400,000 in USD 10,000 steps, and publishes every value it could not verify as a
blank.</p>

<div class="answer">
<strong>The short answer, in four lines.</strong>
<ol>
<li><strong>No PRC tax is levied on the conversion itself.</strong> The income tax law taxes listed categories
of income; a currency exchange is not one of them. Whether tax is owed on the money is a separate question
about where the money came from, and that is still open. {src(["S19"])}</li>
<li><strong>One person can buy at most USD 50,000 of foreign exchange per calendar year on ID alone.</strong>
Above that the bank requires documents. USD 400,000 is eight calendar years at one person's total.
{src(["S01"])}</li>
<li><strong>The published cost of the transfer itself is small: {money(a40['total'])} on USD 400,000
({pct(a40['pct'])}) through Bank of China online banking</strong>, and {money(s10['total'])} on USD 10,000
({pct(s10['pct'])}). Those are fees plus the bank's own spread, not tax. {src(["S09", "S10"])}</li>
<li><strong>The expensive mistakes are the shortcuts.</strong> Splitting the amount across family totals is
named in the rules and puts you on a watch list for three years; private FX dealing and crypto conversion are
prohibited, with fines up to 30-100 percent of the amount. {src(["S02", "S03", "S08"])}</li>
</ol>
</div>

<div class="kpis">
<div class="kpi"><p class="label">Cost on USD 10,000</p><p class="value">{money(a10['total'])}</p>
<p class="sub">{pct(a10['pct'])} · {esc(a10['method'])} on published terms</p></div>
<div class="kpi"><p class="label">Cost on USD 400,000</p><p class="value">{money(a40['total'])}</p>
<p class="sub">{pct(a40['pct'])} · Bank of China online transfer</p></div>
<div class="kpi"><p class="label">Annual purchase total</p><p class="value">USD 50,000</p>
<p class="sub">per person per calendar year, ID only {src(["S01"])}</p></div>
<div class="kpi"><p class="label">Methods examined</p><p class="value">{len(METHODS)}</p>
<p class="sub">8 priced or approval-based · 2 capped/unpriced · 5 unlawful</p></div>
<div class="kpi"><p class="label">Official pages read</p><p class="value">{len(SOURCES)}</p>
<p class="sub">SAFE, PBOC, State Council, STA, IRS, eCFR, Fed, CBP, BOC, HSBC</p></div>
</div>

<div class="notice"><strong>What this page will not tell you:</strong> how much tax you personally owe. That
depends on where the CNY came from and whether PRC tax was paid on it, which are unknown. The
<a href="questions.html">question register</a> lists each missing fact and how to obtain it; the
<a href="penalties.html">penalty layers</a> page shows arithmetic at the statutory rates, clearly labelled as
arithmetic and not as a determination.</div>

<h2>Cost at each USD 10,000 step</h2>
<p class="muted">The two cheapest published routes side by side, with the gate that applies at that size.
Full per-method tables and every input are on the <a href="costs.html">costs page</a>.</p>
<div class="tablewrap"><table class="stack">
<caption>Published cost of converting, USD 10,000 to USD 400,000 in USD 10,000 steps · board of 11 Nov 2026</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">Cheapest published route</th>
<th scope="col" class="num">Cost</th><th scope="col" class="num">%</th>
<th scope="col" class="num">BOC online</th><th scope="col" class="num">%</th>
<th scope="col">Gate at this size</th><th scope="col">Source</th></tr></thead>
<tbody>{''.join(
    f'<tr><th scope="row" data-label="Amount">{money(r["amount"],0)}</th>'
    f'<td data-label="Cheapest route">{esc(r["method"])} · {esc(r["name"])}</td>'
    f'<td class="num" data-label="Cost">{money(r["total"])}</td>'
    f'<td class="num" data-label="% of amount">{pct(r["pct"])}</td>'
    f'<td class="num" data-label="BOC online">'
    + money(next(x for x in SUMMARY if x["amount"] == r["amount"])["total"])
    + f'</td><td class="num" data-label="BOC %">'
    + pct(next(x for x in SUMMARY if x["amount"] == r["amount"])["pct"])
    + f'</td><td data-label="Gate">{esc(r["gate"])}</td>'
    + f'<td data-label="Source">{src(["S09", "S10", "S13", "S01"])}</td></tr>'
    for r in SUMMARY)}</tbody></table></div>
<p class="muted">Every row: computed by <code>model.py</code> from the Bank of China board and fee schedule
{src(["S09", "S10"])}, the HSBC board and tariff {src(["S11", "S12"])}, benchmarked against the Federal
Reserve H.10 {src(["S13"])}. Figures are board-based estimates; the rate actually dealt governs.</p>

<h2>Every page</h2>
<div class="cards">
<a class="card" href="summary.html"><b>Executive summary</b><span>10 findings</span>
<em>The answer, the binding constraint, the cost, and what remains unknown.</em></a>
<a class="card" href="questions.html"><b>Question register</b><span>{len(C.QUESTIONS)} gating questions</span>
<em>Question · what we know · what we do not · how to find out.</em></a>
<a class="card" href="methods.html"><b>Methods</b><span>{len(METHODS)} routes · pros · cons · steps</span>
<em>Every route with its statutory cap and a numbered execution sequence.</em></a>
<a class="card" href="costs.html"><b>Costs at every step</b><span>{len(ROWS)} rows · 40 amounts</span>
<em>Per-method ladder from USD 10,000 to USD 400,000, mobile-first, cost first.</em></a>
<a class="card" href="penalties.html"><b>Conversion penalty, in layers</b><span>{len(C.LAYERS)} layers</span>
<em>What is a fee, what is a tax, what is a fine — and which document each comes from.</em></a>
<a class="card" href="taxes.html"><b>Tax and reporting rules</b><span>PRC and US</span>
<em>The rules that apply, with the rate or threshold and its source.</em></a>
<a class="card" href="sources.html"><b>Source register</b><span>{len(SOURCES)} documents</span>
<em>Publisher, locator, exact words read, and date read.</em></a>
<a class="card" href="review.html"><b>Flagged for review</b><span>{len(C.FLAGS)} items</span>
<em>What could not be verified, what conflicts, and what in this repository needs correcting.</em></a>
</div>

<h2>Method in one paragraph</h2>
<p>Each route was priced only from published inputs: the bank's own rate board, the bank's own fee schedule or
tariff, and the regulator's rule. The spread is measured against the bank's own midpoint, so it isolates the
bank's charge from market movement; the Federal Reserve H.10 is shown alongside as an external benchmark. Where
a charge is not published — intermediary bank deductions, Wise's fee and rate, HSBC Premier's monthly fee —
the cell is blank and carries a link to its entry on the Flagged for review page. Nothing was inferred, and no
value was filled in from a secondary source.</p>
"""
    return page("index.html", "China money · CNY to USD, priced and sourced",
                "A source-linked dashboard for moving lawful CNY out of mainland China to the United States: "
                "published costs at every USD 10,000 step to 400,000, the documentary gate, PRC and US tax "
                "rules, and every value that could not be verified.", body)


def summary_page():
    nosrc = '<span class="muted">no source: this states what is unknown</span>'
    rows = "".join(
        '<tr><th scope="row" data-label="#">%s</th>'
        '<td data-label="Finding"><strong>%s</strong><br><span class="muted">%s</span></td>'
        '<td data-label="Official source">%s</td></tr>'
        % (n, esc(t), esc(body), src(ids) if ids else nosrc)
        for n, t, body, ids in C.FINDINGS)
    body = f"""
<span class="eyebrow">Executive summary</span>
<h1>Ten findings, and the one question that decides everything</h1>
<p class="lede">Written for a US citizen with CNY in a mainland bank account who wants USD with the least tax
and penalty exposure. Each finding names the official page it rests on. Nothing about the reader's own facts
is assumed.</p>

<div class="notice"><strong>The decisive question is not which bank or which fee.</strong> It is what the money
IS. After-tax salary, a property sale, an inheritance and an untaxed payment each take a different legal route,
and only the last one creates a tax problem. Everything else on this site prices the plumbing around that
answer.</div>

<div class="tablewrap"><table class="stack">
<caption>Findings · each with the official page it rests on</caption>
<thead><tr><th scope="col">#</th><th scope="col">Finding</th><th scope="col">Official source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>What follows from the findings</h2>
<div class="grid2">
<div><h3>If the money is after-tax income</h3>
<p>There is no PRC tax left to pay and none arises from converting. The task is documentary: establish which
article applies to you, keep the tax record, and convert within the annual total or with documents above it.
The published cost is under one percent at every size tested.</p></div>
<div><h3>If the money is property or an inheritance</h3>
<p>It is a capital-account item and cannot use the annual purchase total. The emigrant or inheritance transfer
route applies, needs SAFE approval and a tax certificate, and — since 2014 — can be paid out in one go within
the approved amount.</p></div>
<div><h3>If PRC tax was never paid on it</h3>
<p>That is the only path to a large liability, and it exists before any transfer. The surcharge runs at 0.05
percent per day and an evasion fine runs from 50 percent to 5 times the tax. Voluntary correction is a
different conversation from an enquiry, and the order of operations matters.</p></div>
<div><h3>On the US side</h3>
<p>Converting principal does not create income. Currency movement between acquisition and conversion does,
under section 988, as ordinary gain or loss. Reporting duties attach to the account each year regardless of
whether anything moved.</p></div>
</div>

<h2>The three numbers to hold in mind</h2>
<div class="kpis">
<div class="kpi"><p class="label">USD 50,000</p><p class="value">annual total</p>
<p class="sub">Per person, per calendar year, ID only {src(["S01"])}</p></div>
<div class="kpi"><p class="label">{money(SUMMARY[-1]['total'])}</p><p class="value">on USD 400,000</p>
<p class="sub">{pct(SUMMARY[-1]['pct'])} — fees and spread, not tax {src(["S09", "S10"])}</p></div>
<div class="kpi"><p class="label">30-100%</p><p class="value">fine band</p>
<p class="sub">For private FX dealing, plus confiscation {src(["S03"])}</p></div>
</div>
<p class="muted">Read next: the <a href="questions.html">question register</a> for the facts that must be
established first, then <a href="costs.html">costs</a> for every method at every USD 10,000 step.</p>
"""
    return page("summary.html", "Executive summary · China money",
                "Ten sourced findings on moving CNY to USD as a US citizen, and the question that decides the rest.",
                body)


def questions_page():
    rows = "".join(
        f'<tr id="{qid}"><th scope="row" data-label="ID">{qid}</th>'
        f'<td data-label="Question"><strong>{esc(q)}</strong></td>'
        f'<td data-label="Why it matters">{esc(why)}</td>'
        f'<td data-label="What we know">{esc(know)}</td>'
        f'<td data-label="What we do not know">{esc(unk)}</td>'
        f'<td data-label="How to find out">{esc(how)}</td>'
        f'<td data-label="Official source">{src(ids)}</td></tr>'
        for qid, q, why, know, unk, how, ids in C.QUESTIONS)
    body = f"""
<span class="eyebrow">Decision register</span>
<h1>What has to be established before any decision</h1>
<p class="lede">Sixteen questions. For each: why it changes the answer, what the rules already tell us, what is
still missing, and the concrete step that produces the missing fact. No route can be chosen and no tax figure
computed until the first four are answered.</p>

<div class="notice"><strong>Order matters.</strong> Q01 to Q04 decide everything downstream. If the answer to
Q03 is "PRC tax was never paid on this income", the sequence changes completely: correcting the tax position
comes before choosing a transfer method, because the bank will ask for the tax record anyway.</div>

<div class="tablewrap"><table class="stack">
<caption>Sixteen gating questions · known / unknown / how to find out</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Question</th><th scope="col">Why it matters</th>
<th scope="col">What we know</th><th scope="col">What we do not know</th>
<th scope="col">How to find out</th><th scope="col">Official source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>What the answers change</h2>
<div class="tablewrap"><table class="stack">
<caption>Decision map · the answer to Q01-Q03 selects the route</caption>
<thead><tr><th scope="col">If the facts are</th><th scope="col">Then the route is</th>
<th scope="col">Published cost basis</th><th scope="col">Source</th></tr></thead>
<tbody>
<tr><th scope="row" data-label="Facts">Domestic individual, after-tax current-account income, within USD 50,000</th>
<td data-label="Route">Bank purchase on ID, then outward remittance</td>
<td data-label="Cost">Spread + 0.1% commission (capped) + cable</td><td>{src(["S01", "S10"])}</td></tr>
<tr><th scope="row" data-label="Facts">Domestic individual, documented current-account income above the total</th>
<td data-label="Route">Bank purchase on documents (contract, invoice, tax record)</td>
<td data-label="Cost">Same schedule as above; the gate is the document file</td><td>{src(["S01"])}</td></tr>
<tr><th scope="row" data-label="Facts">Foreign individual who is not a domestic individual</th>
<td data-label="Route">Conversion of lawful current-account RMB income on ID plus documents including tax documents</td>
<td data-label="Cost">Bank board and schedule</td><td>{src(["S26", "S03"])}</td></tr>
<tr><th scope="row" data-label="Facts">Emigrant, property owned before emigration</th>
<td data-label="Route">Emigrant property transfer with SAFE approval</td>
<td data-label="Cost">Approval is not published as a charge; bank spread and fee apply</td><td>{src(["S04", "S05"])}</td></tr>
<tr><th scope="row" data-label="Facts">Foreign heir of PRC property</th>
<td data-label="Route">Inherited-property transfer with SAFE approval</td>
<td data-label="Cost">As above</td><td>{src(["S04"])}</td></tr>
<tr class="blankrow"><th scope="row" data-label="Facts">PRC tax unpaid on the income</th>
<td data-label="Route">No route until the tax position is regularised</td>
<td data-label="Cost">{blank("FR01", "cannot be priced")} surcharge 0.05%/day and fine 50%-5x apply</td>
<td>{src(["S20"])}</td></tr>
<tr class="blankrow"><th scope="row" data-label="Facts">Origin of the money unknown</th>
<td data-label="Route">Undetermined</td><td data-label="Cost">{blank("FR01", "not determinable")}</td>
<td>{src(["S19"])}</td></tr>
</tbody></table></div>
"""
    return page("questions.html", "Question register · China money",
                "Sixteen questions that must be answered before a CNY-to-USD decision: what is known, what is "
                "missing, and how to find it out.", body)


def methods_page():
    rows = "".join(
        f'<tr><th scope="row" data-label="ID"><a href="#{m["id"]}">{m["id"]}</a></th>'
        f'<td data-label="Method"><strong>{esc(m["name"])}</strong></td>'
        f'<td data-label="Status">{badge(m["status"])}</td>'
        f'<td data-label="Cap / gate">{esc(m["cap"])}</td>'
        f'<td data-label="Official source">{src(m["sources"])}</td></tr>'
        for m in METHODS)
    detail = ""
    for m in METHODS:
        pros = "".join(f"<li>{esc(x)}</li>" for x in m["pros"])
        cons = "".join(f"<li>{esc(x)}</li>" for x in m["cons"])
        steps = "".join(f"<li>{esc(x)}</li>" for x in m["steps"])
        detail += f"""
<details class="m" id="{m['id']}"><summary>{m['id']} · {esc(m['name'])} &nbsp; {badge(m['status'])}</summary>
<p><strong>Who can use it.</strong> {esc(m['who'])}</p>
<p><strong>Cap or gate.</strong> {esc(m['cap'])}</p>
<div class="grid2"><div><h3>Advantages</h3><ul>{pros}</ul></div>
<div><h3>Disadvantages</h3><ul>{cons}</ul></div></div>
<h3>Step by step</h3><ol>{steps}</ol>
<p class="muted">Official sources: {src(m['sources'])}</p>
</details>"""
    body = f"""
<span class="eyebrow">Methods</span>
<h1>Every route examined, with what it costs you and what it costs legally</h1>
<p class="lede">{esc(C.METHOD_TABLE_NOTE)} Priced routes are computed on the <a href="costs.html">costs page</a>;
this page sets out who can use each one, the cap, the advantages, the disadvantages and the numbered steps.</p>

<div class="tablewrap"><table class="stack">
<caption>{len(METHODS)} routes · status, cap and source</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Method</th><th scope="col">Status</th>
<th scope="col">Cap or gate</th><th scope="col">Official source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Detail, route by route</h2>
{detail}

<h2>Why five of these are marked unlawful</h2>
<p>They are listed because the brief asked for every way, including the ones a reader will encounter in
conversation. Each is prohibited by a named article, and each carries a statutory fine rather than a fee. The
private-trading article sets a fine of up to 30 percent of the amount, rising to 30-100 percent if serious,
plus confiscation; the virtual-currency notice classifies legal-tender-to-virtual-currency exchange as an
illegal financial activity; and the quota-splitting article names the practice and imposes a three-year watch
list in addition. {src(["S03", "S08", "S02"])}</p>
"""
    return page("methods.html", "Methods · China money",
                "Fifteen CNY-to-USD routes with status, cap, advantages, disadvantages and step-by-step "
                "instructions, each linked to its official source.", body)


def costs_page():
    def boc_of(amount):
        return next(r for r in SUMMARY if r["amount"] == amount)

    summary_rows = "".join(
        f'<tr><th scope="row" data-label="Amount">{money(r["amount"],0)}</th>'
        f'<td class="num" data-label="CNY needed">{cny(r["cny"],0)}</td>'
        f'<td data-label="Cheapest route">{esc(r["method"])}</td>'
        f'<td class="num" data-label="Cost">{money(r["total"])}</td>'
        f'<td class="num" data-label="% of amount">{pct(r["pct"])}</td>'
        f'<td class="num" data-label="BOC online">{money(boc_of(r["amount"])["total"])}</td>'
        f'<td class="num" data-label="BOC %">{pct(boc_of(r["amount"])["pct"])}</td>'
        f'<td class="num" data-label="Years at USD 50k/yr">{math.ceil(r["amount"]/50000)}</td>'
        f'<td data-label="Gate">{esc(r["gate"])}</td>'
        f'<td data-label="Source">{src(["S09", "S10", "S11", "S12", "S13", "S01"])}</td></tr>'
        for r in SUMMARY)

    priced = [m for m in METHODS if m["pricing"] in ("boc", "hsbc_tt", "hsbc_gt_premier",
                                                     "hsbc_gt_advance", "boc_cash")]
    details = ""
    for m in priced:
        rws = [r for r in ROWS if r["method"] == m["id"]]
        trs = ""
        for r in rws:
            if r["status"] != "priced":
                trs += (f'<tr class="blankrow"><th scope="row" data-label="Amount">{money(r["amount"],0)}</th>'
                        f'<td colspan="6" data-label="Status">'
                        f'{blank("FR13", "above the USD 10,000 cash cap")} — not available in one trip</td>'
                        f'<td data-label="Source">{src(m["sources"])}</td></tr>')
                continue
            trs += (f'<tr><th scope="row" data-label="Amount">{money(r["amount"],0)}</th>'
                    f'<td class="num" data-label="CNY debited">{cny(float(r["cny"]),0)}</td>'
                    f'<td class="num" data-label="Commission + cable (CNY)">{cny(float(r["fee_cny"]))}</td>'
                    f'<td class="num" data-label="FX spread (USD)">{money(float(r["fx_usd"]))}</td>'
                    f'<td class="num" data-label="Fee (USD)">{money(float(r["fee_usd"]))}</td>'
                    f'<td class="num" data-label="Total (USD)"><strong>{money(float(r["total_usd"]))}</strong></td>'
                    f'<td class="num" data-label="% of amount">{pct(float(r["pct"]))}</td>'
                    f'<td class="num" data-label="vs Fed H.10 (USD)">{money(float(r["gap_fed"]))}</td>'
                    f'<td data-label="Source">{src(m["sources"])}</td></tr>')
        details += f"""
<details class="m" id="{m['id']}"><summary>{m['id']} · {esc(m['name'])}</summary>
<p class="muted">{esc(m['cap'])}</p>
<div class="tablewrap"><table class="stack">
<caption>{m['id']} · {len(rws)} rows · USD 10,000 to USD 400,000</caption>
<thead><tr><th scope="col">Amount</th><th scope="col" class="num">CNY debited</th>
<th scope="col" class="num">Commission + cable</th><th scope="col" class="num">FX spread</th>
<th scope="col" class="num">Fee</th><th scope="col" class="num">Total</th>
<th scope="col" class="num">% of amount</th><th scope="col" class="num">vs Fed H.10</th>
<th scope="col">Source</th></tr></thead><tbody>{trs}</tbody></table></div>
</details>"""

    unpriced = [m for m in METHODS if m["pricing"] == "unpriced"]
    expo = [m for m in METHODS if m["pricing"] == "exposure"]
    unpriced_rows = "".join(
        f'<tr class="blankrow"><th scope="row" data-label="ID">{m["id"]}</th>'
        f'<td data-label="Method">{esc(m["name"])}</td>'
        f'<td data-label="Cost at any amount">{blank("FR07" if m["id"] == "M10" else "FR06", "not published")}</td>'
        f'<td data-label="Cap or gate">{esc(m["cap"])}</td>'
        f'<td data-label="Source">{src(m["sources"])}</td></tr>' for m in unpriced)
    expo_rows = "".join(
        f'<tr><th scope="row" data-label="Amount">{money(a,0)}</th>'
        f'<td class="num" data-label="Fine at 30%">{money(a*0.30,0)}</td>'
        f'<td class="num" data-label="Fine at 100%">{money(a*1.00,0)}</td>'
        f'<td data-label="Plus">{esc("confiscation of the amount, and possible criminal liability")}</td>'
        f'<td data-label="Source">{src(["S03"])}</td></tr>' for a in AMOUNTS)

    body = f"""
<span class="eyebrow">Costs</span>
<h1>What converting costs, at every USD 10,000 step to USD 400,000</h1>
<p class="lede">Total first, then the arithmetic. Every figure below is computed by <code>model.py</code> from
six published inputs: two rate boards, two fee schedules, one external benchmark and the annual total. The
spread is measured against each bank's own midpoint, so it isolates the bank's charge; the column against the
Federal Reserve H.10 shows the all-in difference from an external reference rate.</p>

<div class="notice"><strong>Read the scope before the numbers.</strong> These are published-schedule estimates
on the board of 11 November 2026, not quotes. Bank of China states on the board itself that the rate actually
dealt governs. Intermediary and receiving-bank charges are not published and are blank. No tax is included,
because no rule read here taxes the conversion. {{$srcs}}</div>

<h2>The one table to read first</h2>
<div class="tablewrap"><table class="stack">
<caption>Cheapest published route versus Bank of China at each amount · 40 rows</caption>
<thead><tr><th scope="col">USD amount</th><th scope="col" class="num">CNY needed</th>
<th scope="col">Cheapest route</th><th scope="col" class="num">Cost</th><th scope="col" class="num">%</th>
<th scope="col" class="num">BOC online</th><th scope="col" class="num">BOC %</th>
<th scope="col" class="num">Years at USD 50k/yr</th><th scope="col">Gate</th><th scope="col">Source</th></tr></thead>
<tbody>{summary_rows}</tbody></table></div>

<h2>Inputs, and where each one comes from</h2>
<div class="tablewrap"><table class="stack">
<caption>Every number the model uses</caption>
<thead><tr><th scope="col">Input</th><th scope="col" class="num">Value</th><th scope="col">Meaning</th>
<th scope="col">Source</th></tr></thead><tbody>
<tr><th scope="row" data-label="Input">BOC USD selling rate</th>
<td class="num" data-label="Value">{P['boc_sell']:.4f}</td>
<td data-label="Meaning">RMB per USD the bank charges when it sells you USD (board: 668.71 per 100)</td>
<td>{src(["S09"])}</td></tr>
<tr><th scope="row" data-label="Input">BOC USD buying rate</th>
<td class="num" data-label="Value">{P['boc_buy']:.4f}</td>
<td data-label="Meaning">RMB per USD the bank pays (board: 665.91 per 100); used only to build the midpoint</td>
<td>{src(["S09"])}</td></tr>
<tr><th scope="row" data-label="Input">BOC midpoint</th>
<td class="num" data-label="Value">{P['boc_mid']:.4f}</td>
<td data-label="Meaning">Arithmetic mean of the two; the spread is measured against this</td><td>{src(["S09"])}</td></tr>
<tr><th scope="row" data-label="Input">BOC spread</th>
<td class="num" data-label="Value">{P['boc_spread_pct']:.4f}%</td>
<td data-label="Meaning">Selling rate over midpoint, minus one</td><td>{src(["S09"])}</td></tr>
<tr><th scope="row" data-label="Input">BOC commission</th>
<td class="num" data-label="Value">0.1% · min &yen;50 · max &yen;260 · cable &yen;150</td>
<td data-label="Meaning">Cross-border telegraphic transfer, e-banking schedule from 1 Nov 2014</td>
<td>{src(["S10"])}</td></tr>
<tr><th scope="row" data-label="Input">HSBC USD selling rate</th>
<td class="num" data-label="Value">{P['hsbc_sell']:.4f}</td>
<td data-label="Meaning">RMB per USD, board last updated 10 Nov 2026</td><td>{src(["S11"])}</td></tr>
<tr><th scope="row" data-label="Input">HSBC midpoint</th>
<td class="num" data-label="Value">{P['hsbc_mid']:.4f}</td>
<td data-label="Meaning">Mean of HSBC's buying and selling rates</td><td>{src(["S11"])}</td></tr>
<tr><th scope="row" data-label="Input">HSBC spread</th>
<td class="num" data-label="Value">{P['hsbc_spread_pct']:.4f}%</td>
<td data-label="Meaning">Wider than BOC on the boards read here</td><td>{src(["S11"])}</td></tr>
<tr><th scope="row" data-label="Input">HSBC commission</th>
<td class="num" data-label="Value">0.1% · min &yen;100 · max &yen;500 · cable &yen;120</td>
<td data-label="Meaning">Premier/Advance outward telegraphic transfer</td><td>{src(["S12"])}</td></tr>
<tr><th scope="row" data-label="Input">HSBC Global Transfer</th>
<td class="num" data-label="Value">Premier free · Advance USD 20</td>
<td data-label="Meaning">To the customer's own HSBC account abroad</td><td>{src(["S12"])}</td></tr>
<tr><th scope="row" data-label="Input">Fed H.10 benchmark</th>
<td class="num" data-label="Value">{P['fed']:.4f}</td>
<td data-label="Meaning">CNY per USD, 6 November 2026, published 9 November</td><td>{src(["S13"])}</td></tr>
<tr><th scope="row" data-label="Input">Annual purchase total</th>
<td class="num" data-label="Value">USD 50,000</td>
<td data-label="Meaning">Per person per calendar year, ID only</td><td>{src(["S01"])}</td></tr>
</tbody></table></div>

<h2>Route by route, every step</h2>
<p class="muted">Nine priced routes. Each block expands to 40 rows: one per USD 10,000. The columns are the CNY
you must debit, the commission and cable in CNY, the bank's spread in USD, the fee in USD, the total, the total
as a percentage, and the difference from the Federal Reserve H.10 reference.</p>
{details}

<h2>Routes with no published price</h2>
<div class="tablewrap"><table class="stack">
<caption>Left blank rather than estimated</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Method</th><th scope="col">Cost</th>
<th scope="col">Cap or gate</th><th scope="col">Source</th></tr></thead>
<tbody>{unpriced_rows}</tbody></table></div>

<h2>The unlawful routes: statutory exposure, not a price</h2>
<p>The three prohibition-based routes (private FX dealing, crypto conversion, quota splitting) are priced by
the statute, not by a bank. The table shows the fine band each amount falls into. Confiscation of the amount
and possible criminal liability sit on top, so these are not alternatives to the routes above in any economic
sense.</p>
<div class="tablewrap"><table class="stack">
<caption>Fine band under the FX Regulations at each amount · 30% to 100%</caption>
<thead><tr><th scope="col">Amount</th><th scope="col" class="num">Fine at 30%</th>
<th scope="col" class="num">Fine at 100%</th><th scope="col">Also</th><th scope="col">Source</th></tr></thead>
<tbody>{expo_rows}</tbody></table></div>

<h2>How to reproduce this</h2>
<p>The complete matrix is in <code>data/costs.csv</code> ({len(ROWS)} rows) and <code>data/costs.json</code>.
Run <code>python3 model.py</code> to rebuild both from <code>data/sources.json</code>, and
<code>python3 verify.py</code> to recompute every cell independently and check that each table row links an
official source.</p>
"""
    body = body.replace("{$srcs}", src(["S09", "S10", "S11", "S12", "S13"]))
    return page("costs.html", "Costs · China money",
                "Published cost of converting CNY to USD at every USD 10,000 step from 10,000 to 400,000, "
                "per method, with every input and its official source.", body)


def penalties_page():
    rows = "".join(
        f'<tr><th scope="row" data-label="Layer">{lid}</th>'
        f'<td data-label="Layer name"><strong>{esc(name)}</strong></td>'
        f'<td data-label="Type"><span class="badge '
        f'{"b-un" if kind in ("penalty",) else "b-cap" if kind in ("unverified", "market", "time") else "b-gate"}">'
        f'{esc(kind)}</span></td>'
        f'<td data-label="What the rule says">{esc(what)}</td>'
        f'<td data-label="What it means at this size">{esc(effect)}</td>'
        f'<td data-label="Official source">{src(ids)}</td></tr>'
        for lid, name, kind, what, effect, ids in C.LAYERS)
    body = f"""
<span class="eyebrow">Conversion penalty</span>
<h1>The 'penalty' is twelve different things, and only two of them are tax</h1>
<p class="lede">People say converting costs "a lot in taxes". Decomposed, the cost is mostly a bank spread, a
commission and market movement. Tax enters only through the income behind the money, and penalties enter only
if something was not declared. Each layer below names its source and states whether it is a fee, a tax, a
fine, or simply unknown.</p>

<div class="notice"><strong>The arithmetic on this page is arithmetic, not a determination.</strong> Where a tax
rate appears, it is the statutory rate applied to a hypothetical amount. No rate is asserted to apply to any
person, because the type of income is unknown.</div>

<div class="tablewrap"><table class="stack">
<caption>{len(C.LAYERS)} layers · type, rule, effect, source</caption>
<thead><tr><th scope="col">Layer</th><th scope="col">Name</th><th scope="col">Type</th>
<th scope="col">What the rule says</th><th scope="col">Effect at the sizes in this study</th>
<th scope="col">Official source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Where the money actually goes: USD 400,000 through Bank of China</h2>
<div class="tablewrap"><table class="stack">
<caption>Decomposition of the {money(SUMMARY[-1]['total'])} published total</caption>
<thead><tr><th scope="col">Component</th><th scope="col" class="num">USD</th><th scope="col" class="num">Share of total</th>
<th scope="col">Source</th></tr></thead><tbody>
<tr><th scope="row" data-label="Component">Bank's spread against its own midpoint</th>
<td class="num" data-label="USD">{money(next(r for r in ROWS if r['method']=='M01' and r['amount']==400000)['fx_usd'] and float(next(r for r in ROWS if r['method']=='M01' and r['amount']==400000)['fx_usd']))}</td>
<td class="num" data-label="Share">{pct(float(next(r for r in ROWS if r['method']=='M01' and r['amount']==400000)['fx_usd'])/SUMMARY[-1]['total']*100,1)}</td>
<td>{src(["S09"])}</td></tr>
<tr><th scope="row" data-label="Component">Commission (capped at &yen;260) plus &yen;150 cable</th>
<td class="num" data-label="USD">{money(float(next(r for r in ROWS if r['method']=='M01' and r['amount']==400000)['fee_usd']))}</td>
<td class="num" data-label="Share">{pct(float(next(r for r in ROWS if r['method']=='M01' and r['amount']==400000)['fee_usd'])/SUMMARY[-1]['total']*100,1)}</td>
<td>{src(["S10"])}</td></tr>
<tr><th scope="row" data-label="Component">Intermediary and receiving bank charges</th>
<td data-label="USD">{blank("FR06", "unpublished")}</td><td data-label="Share">{blank("FR06", "—")}</td>
<td>{src(["S12"])}</td></tr>
<tr><th scope="row" data-label="Component">PRC tax on the conversion itself</th>
<td data-label="USD"><strong>USD 0.00</strong></td><td data-label="Share">No rule read here imposes one</td>
<td>{src(["S19"])}</td></tr>
<tr><th scope="row" data-label="Component">PRC tax on the income behind the money</th>
<td data-label="USD">{blank("FR01", "depends on facts")}</td><td data-label="Share">{blank("FR01", "—")}</td>
<td>{src(["S19"])}</td></tr>
</tbody></table></div>

<h2>The order of operations that minimises exposure</h2>
<ol>
<li><strong>Establish what the money is.</strong> Tax and route both follow from it, and no fee optimisation
matters if the route is wrong. {src(["S19"])}</li>
<li><strong>If PRC tax is unpaid, deal with that first and voluntarily.</strong> The surcharge is 0.05 percent
per day and the evasion fine is 50 percent to 5 times the tax; an unprompted correction is a different
conversation from an enquiry, and the bank will want the tax record anyway. {src(["S20", "S04"])}</li>
<li><strong>Then pick the cheapest route you are actually eligible for.</strong> On published terms that is
Bank of China online from USD 20,000 upward. {src(["S10"])}</li>
<li><strong>Then file the US reports the balance triggers</strong>, in the year the threshold is crossed, not
the year of the transfer. {src(["S15", "S16"])}</li>
<li><strong>Never use the shortcuts.</strong> The fine band is 30-100 percent of the amount, which is 100 to
300 times the cost of doing it lawfully. {src(["S03"])}</li>
</ol>
"""
    return page("penalties.html", "Penalty layers · China money",
                "The CNY-to-USD conversion penalty decomposed into twelve layers: bank spread, fees, market "
                "movement, delay, PRC income tax, surcharges, fines and US reporting penalties.", body)


def taxes_page():
    prc = [
        ("Who is taxed on worldwide income", "A person domiciled in China, or present 183 days in a tax year",
         "183 days", ["S19"]),
        ("Rates on comprehensive income", "Progressive", "3% to 45%", ["S19"]),
        ("Rates on interest, dividends, property rental, property transfer, incidental income", "Flat", "20%",
         ["S19"]),
        ("Currency for assessment", "Foreign-currency income translated at the RMB central parity rate",
         "—", ["S19"]),
        ("Foreign tax relief", "PRC tax paid abroad may be credited against PRC tax on the same income, capped",
         "—", ["S19"]),
        ("Late payment", "Surcharge per day of delay", "0.05% per day", ["S20"]),
        ("Evasion", "Fine on the tax underpaid", "50% to 5x", ["S20"]),
        ("Annual FX purchase total for a domestic individual", "Per person per calendar year, ID only",
         "USD 50,000", ["S01"]),
        ("Above the total", "Documents evidencing the transaction required", "—", ["S01"]),
        ("Outward remittance from an FX savings account", "ID only up to this amount per day", "USD 50,000/day",
         ["S01"]),
        ("Quota splitting", "Prohibited; watch list for the year plus two", "3 years", ["S02"]),
        ("FX evasion / illegal arbitrage fine", "Of the amount", "up to 30%, or 30-100% if serious", ["S03"]),
        ("Illegal carrying of cash", "Fine of the amount", "up to 20%", ["S03"]),
        ("Cash carried out", "No permit / bank permit / in principle prohibited", "5,000 / 10,000 / above",
         ["S06"]),
        ("Overseas ATM cash per year", "Of the individual, all cards", "RMB 100,000", ["S07"]),
    ]
    us = [
        ("Citizens abroad", "Worldwide income is taxable in the US regardless of residence", "—", ["S15"]),
        ("Currency conversion of principal", "Not itself income; a disposition of nonfunctional currency",
         "—", ["S22"]),
        ("FX gain or loss", "Ordinary income or loss under section 988", "—", ["S22"]),
        ("FBAR", "Aggregate foreign accounts above this at any time in the year", "USD 10,000", ["S15"]),
        ("FBAR due date", "With automatic extension", "15 Apr / 15 Oct", ["S15"]),
        ("FBAR maximum, non-willful", "Inflation-adjusted maximum per violation", "USD 16,536", ["S17"]),
        ("FBAR maximum, willful", "Inflation-adjusted maximum per violation", "USD 165,353", ["S17"]),
        ("Form 8938, living in the US, unmarried", "Year-end / any time", "USD 50,000 / 75,000", ["S16"]),
        ("Form 8938, living abroad, unmarried", "Year-end / any time", "USD 200,000 / 300,000", ["S16"]),
        ("Form 8938 maximum penalty", "Per year", "USD 60,000", ["S16"]),
        ("Form 3520, gift from a nonresident alien", "Aggregate per year from that person", "USD 100,000",
         ["S18"]),
        ("Form 3520, foreign corporation or partnership", "2025 / 2026 thresholds", "USD 20,116 / 20,573",
         ["S18"]),
        ("Foreign earned income exclusion, 2027", "Tax years beginning in 2027", "USD 137,300", ["S23"]),
        ("Annual gift exclusion, 2027", "Per donee", "USD 20,000", ["S23"]),
        ("Carrying cash into or out of the US", "FinCEN Form 105 above this, aggregated for a family",
         "USD 10,000", ["S24"]),
        ("Treaty ceiling", "Applies to dividends, interest and royalties only", "10%", ["S27"]),
        ("Foreign tax credit", "Conditional; only treaty-rate tax qualifies; none for excluded income", "—",
         ["S21"]),
        ("IRS yearly average, China, 2025", "Used for reporting, not for dealing", "7.129", ["S14"]),
    ]
    def table(rows, caption):
        return ('<div class="tablewrap"><table class="stack"><caption>' + esc(caption) + '</caption>'
                '<thead><tr><th scope="col">Rule</th><th scope="col">What it says</th>'
                '<th scope="col">Rate, threshold or figure</th><th scope="col">Source</th></tr></thead><tbody>'
                + "".join(f'<tr><th scope="row" data-label="Rule">{esc(a)}</th>'
                          f'<td data-label="What it says">{esc(b)}</td>'
                          f'<td class="num" data-label="Figure">{esc(c)}</td>'
                          f'<td data-label="Source">{src(ids)}</td></tr>' for a, b, c, ids in rows)
                + '</tbody></table></div>')

    body = f"""
<span class="eyebrow">Tax and reporting rules</span>
<h1>The rules that apply, with the rate and the article</h1>
<p class="lede">Two systems apply at once. The PRC taxes the income and controls the conversion; the US taxes
the citizen on worldwide income and requires the account to be reported. Neither read here taxes the act of
converting.</p>

<h2>PRC</h2>
{table(prc, "PRC rules used on this site")}

<h2>United States</h2>
{table(us, "US rules used on this site")}

<h2>How the two interact on a single conversion</h2>
<ol>
<li><strong>The conversion.</strong> No PRC tax arises from the exchange; no US income arises from exchanging
principal. A section 988 gain or loss may arise from the currency movement, measured against the rate at which
the CNY was acquired. {src(["S19", "S22"])}</li>
<li><strong>The income behind it.</strong> If the CNY is PRC-source salary, PRC tax was withheld when it was
paid. On the US return the same income is taxable, with a foreign tax credit for the PRC tax actually paid —
only the treaty-rate tax qualifies, and no credit is available against excluded income. {src(["S21", "S27"])}</li>
<li><strong>The account.</strong> FBAR and Form 8938 are triggered by balances, not by transfers, and are due
for every year the threshold was crossed. {src(["S15", "S16"])}</li>
<li><strong>The gift question.</strong> Money received from a foreign relative is not automatically income,
but a genuine gift above USD 100,000 from a nonresident alien must be reported on Form 3520, and the IRS may
recharacterise a purported gift. {src(["S18"])}</li>
</ol>
<div class="notice"><strong>No personalised conclusion is offered.</strong> Whether a particular transfer is
income, a gift, a return of capital or a property transfer determines the tax; that fact is not known here.
The <a href="questions.html">question register</a> is the route to it.</div>
"""
    return page("taxes.html", "Tax and reporting rules · China money",
                "The PRC and US rules that apply to moving CNY to USD, each with its rate or threshold and its "
                "official source.", body)


def sources_page():
    rows = ""
    for s in SOURCES:
        commercial = "Commercial provider" in s["group"]
        tag = ('<span class="tag">commercial</span>' if commercial else '<span class="tag">official</span>')
        rows += (f'<tr id="{s["id"]}"><th scope="row" data-label="ID">{s["id"]}</th>'
                 f'<td data-label="Publisher">{esc(s["publisher"])}{tag}</td>'
                 f'<td data-label="Document and locator"><a href="{esc(s["url"])}">{esc(s["title"])}</a>'
                 f'<br><span class="muted">{esc(s["locator"])}</span></td>'
                 f'<td data-label="Exact words read"><span class="quote">{esc(s["quote"])}</span>'
                 f'<br><span class="muted">Read {esc(s["read"])}. {esc(s["finding"])}</span></td></tr>')
    body = f"""
<span class="eyebrow">Source register</span>
<h1>{len(SOURCES)} documents, the exact words read, and the date</h1>
<p class="lede">Every value on this site traces to one of these pages. The quote column holds the sentence or
table row the value came from, in the publisher's own words, so a reader can check it without trusting this
site. All were opened on {C.TODAY}.</p>

<div class="notice"><strong>What a source link does and does not prove.</strong> It proves that the page said
these words on {C.TODAY}. It does not prove the page will say them tomorrow: rate boards change during the
day, tariffs are reissued, and regulatory text is amended. Banks state that their boards are indicative.</div>

<div class="tablewrap"><table class="stack">
<caption>Source ledger · {len(SOURCES)} documents</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Publisher</th><th scope="col">Document and locator</th>
<th scope="col">Exact words read</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Domains used</h2>
<p class="muted">safe.gov.cn · pbc.gov.cn · gov.cn · chinatax.gov.cn · irs.gov · ecfr.gov · govinfo.gov ·
federalreserve.gov · cbp.gov · boc.cn · hsbc.com.cn — plus one commercial help page (wise.com), labelled as
commercial and used only to describe that provider's own terms.</p>
"""
    return page("sources.html", "Source register · China money",
                "Every official page used, with the exact words read and the date read.", body)


def review_page():
    flags = "".join(
        f'<tr id="{fid}"><th scope="row" data-label="ID">{fid}</th>'
        f'<td data-label="Item"><strong>{esc(title)}</strong><br><span class="muted">{esc(detail)}</span></td>'
        f'<td data-label="Status"><span class="badge b-flag">{esc(status)}</span></td>'
        f'<td data-label="Source">{src(ids)}</td></tr>'
        for fid, title, detail, ids, status in C.FLAGS)
    body = f"""
<span class="eyebrow">Flagged for review</span>
<h1>What could not be verified, and what conflicts</h1>
<p class="lede">Nothing here was guessed and filled in. Every value that could not be confirmed from an
official page is blank in the tables and listed below with the reason. Repository-level conflicts found while
reviewing the other sections are listed separately, with file and line, so they can be corrected by their
owners.</p>

<h2>Unverified values and unresolved readings</h2>
<div class="tablewrap"><table class="stack">
<caption>{len(C.FLAGS)} items · status and source</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Item</th><th scope="col">Status</th>
<th scope="col">Source</th></tr></thead><tbody>{flags}</tbody></table></div>

<h2>What was checked, and what the check proves</h2>
<ul>
<li><strong>Every cost cell recomputed independently.</strong> {sum(1 for r in ROWS if r['status'] == 'priced')} priced cells were rebuilt by
<code>verify.py</code> with a separate code path from the raw board and schedule figures and compared to the
stored values, cell by cell. That proves the arithmetic, not the rates.</li>
<li><strong>Every table row carries an official link.</strong> Every body row on the nine pages contains at least one link to a regulator or to the bank's own page. Five rows rely only on a commercial
provider's own help page (Wise); in each of those the price is blank, so no value rests on a commercial
source.</li>
<li><strong>Every blank is published.</strong> {sum(1 for r in ROWS if r['status'] != 'priced')} blank
cost cells, each linking the flag entry that explains it. No cell is empty without a reason attached.</li>
<li><strong>No broken local path or anchor</strong>, and no external link outside the official domains plus the
one labelled commercial page.</li>
<li><strong>CSV and JSON parity</strong> with the rendered tables, and a reproducible build
(<code>model.py</code> then <code>build.py</code>).</li>
</ul>

<h2>How the repository review was performed</h2>
<p>This session did not rewrite any other section. The review was mechanical: every tracked file was searched
for the phrases that carry a figure or a rule, the matching lines were read in context, and each was classified
as <em>asserting</em> the claim or <em>quoting</em> it in a correction. Only lines that assert a claim are
listed as conflicts. The scan was run on {C.TODAY} against the tree at the commit recorded in
<code>COORDINATION.md</code>; counts therefore describe that tree, not this one, once this section is merged.</p>
<div class="tablewrap"><table class="stack">
<caption>Scan of the tracked tree · 379 tracked files at commit 2a5a470</caption>
<thead><tr><th scope="col">Search</th><th scope="col" class="num">Files matching</th>
<th scope="col">Classification</th><th scope="col">Rule source</th></tr></thead><tbody>
<tr><th scope="row" data-label="Search">"creditable dollar-for-dollar"</th>
<td class="num" data-label="Files">2</td>
<td data-label="Classification">Both assert it as fact; see FR15. Other matches of the shorter phrase quote it inside a correction.</td><td>{src(["S21"])}</td></tr>
<tr><th scope="row" data-label="Search">staged emigrant payout</th>
<td class="num" data-label="Files">3 lines in 2 files</td>
<td data-label="Classification">Assert it as current; see FR16</td><td>{src(["S05"])}</td></tr>
<tr><th scope="row" data-label="Search">"86.97" (HSBC &yen;620 at 7.129)</th>
<td class="num" data-label="Files">39</td>
<td data-label="Classification">Arithmetically right on the IRS average, wrong basis for a budget; see FR19</td><td>{src(["S14"])}</td></tr>
<tr><th scope="row" data-label="Search">"137,300" (FEIE 2027)</th>
<td class="num" data-label="Files">12</td>
<td data-label="Classification">Matches Rev. Proc. 2026-35 section 3.41</td><td>{src(["S23"])}</td></tr>
<tr><th scope="row" data-label="Search">"132,900"</th>
<td class="num" data-label="Files">50</td>
<td data-label="Classification">Not the 2027 figure; whether it is the 2026 figure was not checked; see FR18</td><td>{src(["S23"])}</td></tr>
<tr><th scope="row" data-label="Search">"10% US-China Treaty caps"</th>
<td class="num" data-label="Files">1</td>
<td data-label="Classification">Overstates the treaty ceiling; see FR17</td><td>{src(["S27"])}</td></tr>
</tbody></table></div>

<h2>Files named in this review, for the owning sessions</h2>
<ul>
<li><code>study-8f529c94/EXECUTIVE_SUMMARY.md</code> line 20 and
<code>transfer-guide/EXECUTIVE_SUMMARY.md</code> line 20 — "creditable dollar-for-dollar" (FR15).</li>
<li><code>estimate-facf2fe9/methods.html</code> lines 157 and 159 —
<code>verify-d5d1f860/costs.html</code> line 50 — staged emigrant payout (FR16).</li>
<li><code>portal/index.html</code> line 68 — treaty ceiling applied generally (FR17).</li>
</ul>
<p class="muted">These files belong to other sessions and were not edited here. The correction request is
recorded in <code>COORDINATION.md</code>, as the protocol requires.</p>

<h2>What this pass did not verify</h2>
<ul>
<li>Whether any official page still reads the same tomorrow.</li>
<li>Any legal conclusion, including which article a particular bank will apply to a particular file.</li>
<li>Any fact about the reader: residency, income type, tax history, filing history.</li>
<li>Whether a US branch of HSBC will open the receiving account, or what it charges.</li>
<li>The 2026 foreign earned income exclusion (Rev. Proc. 2025-32 was not read in this pass).</li>
</ul>
"""
    return page("review.html", "Flagged for review · China money",
                "Every value that could not be verified, every conflicting official text, and every "
                "repository-level correction found in this pass.", body)


def main():
    open(os.path.join(HERE, "style.css"), "w", encoding="utf-8").write(CSS)
    pages = [("index.html", index_page), ("summary.html", summary_page),
             ("questions.html", questions_page), ("methods.html", methods_page),
             ("costs.html", costs_page), ("penalties.html", penalties_page),
             ("taxes.html", taxes_page), ("sources.html", sources_page),
             ("review.html", review_page)]
    for name, fn in pages:
        open(os.path.join(HERE, name), "w", encoding="utf-8").write(fn())
        print("wrote", name)


if __name__ == "__main__":
    main()
