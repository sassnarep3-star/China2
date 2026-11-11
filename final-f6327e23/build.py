#!/usr/bin/env python3
"""Render the final-f6327e23 dashboard. Deterministic; no network; no dependencies.

Run: python3 final-f6327e23/build.py
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

costs = json.load(open(os.path.join(DATA, "costs.json")))
routes = json.load(open(os.path.join(DATA, "routes.json")))
sources = {s["id"]: s for s in json.load(open(os.path.join(DATA, "sources.json")))}
# Sources added after the original 2026-11-10 session carry an "added_by" field (correction by
# arena/8a85759a-china2, 2026-11-11: SAFE Huifa [2014] No. 2 for routes R06/R07). They are counted and
# labelled separately so the page never claims they were fetched in the original session.
ADDED_SOURCES = [s for s in sources.values() if s.get("added_by")]
ORIGINAL_SOURCES = len(sources) - len(ADDED_SOURCES)
ADDED_NOTE = "".join(f"; {s['id']} added in a correction on {s['verified_at']}" for s in ADDED_SOURCES)
meta = json.load(open(os.path.join(DATA, "meta.json")))
ROUTE_BY_ID = {r["id"]: r for r in routes}

NAV = [
    ("index.html", "Overview"),
    ("methods.html", "Methods"),
    ("costs.html", "Costs $10k–$400k"),
    ("taxes.html", "Tax & penalties"),
    ("steps.html", "Step by step"),
    ("sources.html", "Sources"),
    ("review.html", "Flagged for review"),
    ("repo-audit.html", "Repo audit"),
]

CAT_LABEL = {
    "lawful": "Lawful",
    "lawful-capped": "Lawful, capped",
    "lawful-conditional": "Lawful if eligible",
    "unlawful": "Unlawful",
    "does-not-achieve-goal": "Does not achieve the goal",
    "unverified": "Unverified",
    "flagged": "Flagged",
}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def cite(*ids):
    """Superscript source links. Every table row carries at least one."""
    out = []
    for i in ids:
        s = sources[i]
        out.append(f'<a class="src" href="{esc(s["url"])}" target="_blank" '
                   f'rel="noopener noreferrer" title="{esc(s["title"])}">{i}</a>')
    return " ".join(out)


def money(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return ""
    return ("-$" if x < 0 else "$") + f"{abs(x):,.2f}"


def header(title, subtitle, page):
    links = []
    for p, t in NAV:
        cls = ' class="on"' if p == page else ""
        links.append(f'<a href="{p}"{cls}>{esc(t)}</a>')
    nav = "".join(links)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China money</title>
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header class="top">
  <div class="wrap">
    <a class="brand" href="index.html">China money<span>· CNY→USD, verified</span></a>
    <nav aria-label="Sections">{nav}</nav>
  </div>
</header>
<main class="wrap">
<h1>{esc(title)}</h1>
<p class="lede">{subtitle}</p>
"""


def footer():
    return f"""</main>
<footer class="foot"><div class="wrap">
<p><strong>Research, not tax or legal advice.</strong> Every figure on this site is either
quoted from a linked official source or explicitly labelled as a model assumption.
Values that could not be confirmed are blank, and listed on the
<a href="review.html">Flagged for review</a> page. No account-specific facts were assumed.</p>
<p class="small">Built {meta['generated']} · {meta['route_count']} methods ·
{meta['tiers']} cost tiers ({meta['row_count']} model rows) ·
{meta['source_count']} primary sources ({ORIGINAL_SOURCES} re-fetched in the original session on {meta['generated']}{ADDED_NOTE}) ·
rate basis {meta['rate']} CNY/USD (S16, 2026-11-10 17:39:58).</p>
</div></footer>
<script src="assets/app.js"></script>
</body></html>
"""


# ------------------------------------------------------------------ overview
def page_index():
    r01_10 = next(r for r in costs["rows"] if r["route"] == "R01" and r["amount"] == 10000)
    r01_400 = next(r for r in costs["rows"] if r["route"] == "R01" and r["amount"] == 400000)
    r02_400 = next(r for r in costs["rows"] if r["route"] == "R02" and r["amount"] == 400000)
    picks = [10000, 50000, 100000, 250000, 400000]
    quick = ""
    for t in picks:
        row = next(r for r in costs["rows"] if r["route"] == "R01" and r["amount"] == t)
        quick += (f'<tr><td data-label="Amount">{money(t)}</td>'
                  f'<td data-label="Bank fee">{money(row["fx_fee_usd"])}</td>'
                  f'<td data-label="FX spread">{money(row["spread_usd"])}</td>'
                  f'<td data-label="US bank">${row["receive_usd"]}</td>'
                  f'<td class="num strong" data-label="All-in cost">{money(row["all_in_usd"])}</td>'
                  f'<td data-label="% of amount">{row["pct"]}%</td>'
                  f'<td data-label="Sources">{cite("S14","S15","S16")}</td></tr>')

    rank = ""
    order = ["R01", "R02", "R03", "R04", "R06", "R07", "R09", "R12", "R05", "R08",
             "R13", "R14", "R10", "R11", "R15"]
    for rid in order:
        r = ROUTE_BY_ID[rid]
        row = next((x for x in costs["rows"] if x["route"] == rid and x["amount"] == 100000), None)
        if row and row["all_in_usd"] and rid not in ("R10", "R11"):
            cost = money(row["all_in_usd"]) + f' ({row["pct"]}%)'
        elif rid in ("R10", "R11"):
            cost = "up to " + money(row["all_in_usd"]) + " fine"
        else:
            cost = '<span class="blank">—</span>'
        rank += (f'<tr data-cat="{esc(r["category"])}"><td data-label="Method">'
                 f'<a href="methods.html#{rid.lower()}"><strong>{rid}</strong> {esc(r["short"])}</a></td>'
                 f'<td data-label="Status"><span class="tag {esc(r["category"])}">{esc(CAT_LABEL[r["category"]])}</span></td>'
                 f'<td data-label="Cost at $100,000">{cost}</td>'
                 f'<td data-label="Verdict">{esc(r["verdict"])}</td>'
                 f'<td data-label="Source">{cite(*r["sources"][:3]) if r["sources"] else "<span class=blank>none</span>"}</td></tr>')

    return header("Getting CNY out of China legally, at least cost",
                  "A US citizen's question, answered from primary sources: what actually costs money, "
                  "what is actually taxed, and what the rules actually cap.", "index.html") + f"""
<section class="hero">
  <p class="answer">The conversion itself is <strong>not</strong> a taxable event, and the famous
  <strong>USD 50,000</strong> limit is <strong>not a cap</strong> on converting documented
  current-account income. The real cost of the lawful route is small — roughly
  <strong>{r01_10['pct']}%</strong> at $10,000 falling to <strong>{r01_400['pct']}%</strong> at $400,000
  — and the real risk is <strong>US reporting</strong>, not a Chinese conversion levy.</p>
</section>

<div class="grid cards">
  <article class="card">
    <h2>1 · There is no Chinese tax on the conversion</h2>
    <p>The FX Regulations state that "the State does not restrict current international payments and
    transfers" (Art. 5) {cite('S02')}. The conversion rule requires the bank to see your ID and the
    source-of-funds papers <em>including tax vouchers</em> {cite('S01')} — the tax attaches to the
    <em>income</em>, which is assessed separately, not to the act of changing currency.</p>
    <p class="small caveat">Analytical conclusion. No provision imposing a conversion levy appears in
    the texts I read; that is not a regulator's positive statement. See flag F06.</p>
  </article>
  <article class="card">
    <h2>2 · The USD 50,000 quota is a different channel</h2>
    <p>Art. 54 imposes the USD 50,000 annual <em>facilitation</em> quota on individuals' FX sales and
    on <em>domestic</em> individuals' purchases. Art. 59 handles a non-domestic individual's documented
    current-account income with no quota stated {cite('S01', 'S03')}. A PRC permanent-resident ID holder
    may use the quota instead.</p>
    <p class="small caveat">Watch the wording trap: "no quota" is not "no documents". The bank decides.</p>
  </article>
  <article class="card">
    <h2>3 · What the transfer actually costs</h2>
    <p>Bank fee + cable + FX spread + your US bank's incoming fee. At $100,000: bank fee
    {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==100000)['fx_fee_usd'])},
    spread {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==100000)['spread_usd'])},
    receiving $16 → <strong>{money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==100000)['all_in_usd'])}</strong>
    all-in {cite('S14', 'S15', 'S16')}.</p>
    <p class="small caveat">Fee schedule is HSBC China's; your bank's will differ.</p>
  </article>
  <article class="card">
    <h2>4 · Where the real tax risk sits</h2>
    <p>US side: a personal conversion with more than <strong>$200</strong> of exchange gain falls
    outside the personal-transaction exclusion {cite('S08')}; the account itself triggers
    <strong>FBAR</strong> above $10,000 {cite('S10')} and possibly <strong>Form 8938</strong>
    {cite('S11')}. Penalty maxima are published and large {cite('S09')}.</p>
    <p class="small caveat">Gain depends on when you acquired the CNY — a private fact.</p>
  </article>
</div>

<h2>Cost at a glance — the lawful documented route (R01)</h2>
<p class="small">Amounts are the USD you intend to receive. Bank fee is HSBC China's published
telegraphic-transfer tariff (0.1%, min CNY 100, max CNY 500, plus CNY 120 cable) converted at the
2026-11-10 BOC selling rate; spread is the measured BOC half-spread; receiving fee is one US bank's
published price. <a href="costs.html">All 40 tiers and every method →</a></p>
<div class="table-wrap"><table class="stack">
<thead><tr><th>Amount</th><th>Bank fee</th><th>FX spread</th><th>US bank</th><th>All-in cost</th><th>% of amount</th><th>Sources</th></tr></thead>
<tbody>{quick}</tbody></table></div>

<h2>Every method, ranked by what it actually costs</h2>
<p class="small">Costs shown at $100,000 for comparability. "—" means no lawful published price exists
to quote. Unlawful routes show the <em>statutory maximum fine</em>, not a price.
<a href="methods.html">Full pros, cons and documents →</a></p>
<div class="table-wrap"><table class="stack" id="rank-table">
<thead><tr><th>Method</th><th>Status</th><th>Cost at $100,000</th><th>Verdict</th><th>Sources</th></tr></thead>
<tbody>{rank}</tbody></table></div>

<h2>What I could not verify</h2>
<p>These determine the answer and are <strong>not</strong> guessed anywhere on this site: whether the
balance is CNY or already foreign currency; whether it came from wages, a property sale, a gift or an
inheritance; your PRC household-registration and residency status; the date and rate at which you
acquired the money. Each is recorded on the <a href="review.html">Flagged for review</a> page with the
consequence of not knowing it.</p>

<h2>Read next</h2>
<div class="grid links">
  <a class="card link" href="methods.html"><strong>15 methods</strong><span>Pros, cons, documents, caps and the exact steps</span></a>
  <a class="card link" href="costs.html"><strong>Cost ladder</strong><span>$10,000 to $400,000 in $10,000 steps, per method</span></a>
  <a class="card link" href="taxes.html"><strong>Tax &amp; penalties</strong><span>What is taxed, what is not, and the statutory ceilings</span></a>
  <a class="card link" href="steps.html"><strong>Step by step</strong><span>The playbook and the document checklist</span></a>
  <a class="card link" href="sources.html"><strong>{meta['source_count']} sources</strong><span>Quotes, locators and retrieval dates</span></a>
  <a class="card link" href="repo-audit.html"><strong>Repo audit</strong><span>What I checked in this repository, and what disagrees</span></a>
</div>
""" + footer()


# ------------------------------------------------------------------- methods
def page_methods():
    cards = ""
    for r in routes:
        pros = "".join(f"<li>{esc(p)}</li>" for p in r["pros"]) or "<li>—</li>"
        cons = "".join(f"<li>{esc(c)}</li>" for c in r["cons"]) or "<li>—</li>"
        reqs = "".join(f"<li>{esc(x)}</li>" for x in r["requirements"]) or "<li>—</li>"
        steps = "".join(f"<li>{esc(s)}</li>" for s in r["steps"]) or "<li>—</li>"
        unp = "".join(f"<li>{esc(u)}</li>" for u in r["unverified"]) or "<li>Nothing recorded</li>"
        src = cite(*r["sources"]) if r["sources"] else '<span class="blank">no official source verified</span>'
        corr = (f'\n  <p class="small correction"><strong>Correction.</strong> {esc(r["correction"])} {cite("S17")}</p>'
                if r.get("correction") else "")
        cards += f"""
<article class="method" id="{r['id'].lower()}" data-cat="{esc(r['category'])}">
  <header class="method-head">
    <h3><span class="rid">{r['id']}</span> {esc(r['name'])}</h3>
    <span class="tag {esc(r['category'])}">{esc(CAT_LABEL[r['category']])}</span>
  </header>
  <p class="verdict">{esc(r['verdict'])}</p>
  <dl class="facts">
    <dt>Who it fits</dt><dd>{esc(r['who'])}</dd>
    <dt>Legal basis</dt><dd>{esc(r['legal_basis'])} {src}</dd>
    <dt>Caps / limits</dt><dd>{esc(r['caps'])}</dd>
  </dl>
  <div class="two-col">
    <div><h4>Pros</h4><ul class="pros">{pros}</ul></div>
    <div><h4>Cons</h4><ul class="cons">{cons}</ul></div>
  </div>
  <details><summary>Documents required</summary><ul>{reqs}</ul></details>
  <details><summary>Exact steps</summary><ol>{steps}</ol></details>
  <p class="small"><strong>Not verified:</strong></p><ul class="small unverified">{unp}</ul>{corr}
</article>"""
    return header("Methods: 15 ways to move CNY out of mainland China",
                  "Every method I could find, with its legal basis, its published caps, its real pros and "
                  "cons, and the documents it demands. Costs are on the cost page; nothing here is priced "
                  "unless a source prices it.", "methods.html") + f"""
<div class="filters" role="group" aria-label="Filter methods">
  <button class="chip on" data-filter="all">All ({len(routes)})</button>
  <button class="chip" data-filter="lawful">Lawful</button>
  <button class="chip" data-filter="lawful-capped">Lawful, capped</button>
  <button class="chip" data-filter="lawful-conditional">Lawful if eligible</button>
  <button class="chip" data-filter="unlawful">Unlawful</button>
  <button class="chip" data-filter="other">Other</button>
</div>
<p class="small">The two unlawful routes are included because the brief asked for every way, including
the ones that look attractive. They are not recommendations and they are not priced as if they were.</p>
{cards}
""" + footer()


# --------------------------------------------------------------------- costs
def page_costs():
    primary = ""
    for row in costs["rows"]:
        if row["route"] != "R01":
            continue
        primary += (f'<tr id="t{row["amount"]}"><td data-label="Amount">{money(row["amount"])}</td>'
                    f'<td data-label="Bank fee (USD)">{money(row["fx_fee_usd"])}<span class="sub">CNY {row["fx_fee_cny"]}</span></td>'
                    f'<td data-label="FX spread">{money(row["spread_usd"])}</td>'
                    f'<td data-label="US bank">${row["receive_usd"]}</td>'
                    f'<td class="num strong" data-label="All-in">{money(row["all_in_usd"])}</td>'
                    f'<td data-label="% of amount">{row["pct"]}%</td>'
                    f'<td class="small" data-label="Basis">{esc(row["note"])}</td>'
                    f'<td data-label="Sources">{cite("S14","S15","S16")}</td></tr>')

    pivot_head = ""
    pivot_body = ""
    piv_routes = ["R01", "R02", "R03", "R12", "R04", "R10", "R11"]
    for rid in piv_routes:
        pivot_head += f'<th class="num">{rid}</th>'
    pivot_head += '<th>Sources</th>'
    for t in costs["tiers"]:
        cells = ""
        for rid in piv_routes:
            row = next(r for r in costs["rows"] if r["route"] == rid and r["amount"] == t)
            if rid == "R04":
                cells += f'<td class="num {"blank" if row.get("capability") != "capable" else ""}" data-label="{rid}">{"cap" if row.get("capability") == "capable" else "over cap"}</td>'
            elif rid in ("R10", "R11"):
                cells += f'<td class="num bad" data-label="{rid}">{money(row["all_in_usd"])}</td>'
            else:
                cells += f'<td class="num" data-label="{rid}">{money(row["all_in_usd"])}</td>'
        pivot_body += (f'<tr><td data-label="Amount">{money(t)}</td>{cells}'
                       f'<td data-label="Sources">{cite("S02","S14","S15","S16")}</td></tr>')

    def row_legend(rid):
        r = ROUTE_BY_ID[rid]
        return f'<li><strong>{rid}</strong> — {esc(r["short"])} <span class="tag {esc(r["category"])}">{esc(CAT_LABEL[r["category"]])}</span></li>'

    legend = "".join(row_legend(r) for r in piv_routes)

    assumptions = ""
    for a in costs["assumptions"]:
        assumptions += f"""<details class="assume"><summary><strong>{a['id']}</strong> {esc(a['text'][:110])}…</summary>
<p>{esc(a['text'])}</p><p class="small"><strong>Why:</strong> {esc(a['why'])}<br>
<strong>Effect if wrong:</strong> {esc(a['impact'])}<br>
<strong>Status:</strong> {esc(a['status'])}</p></details>"""

    return header("Cost to convert and transfer, $10,000 to $400,000",
                  "Forty amounts in $10,000 steps. Costs are the sum of a published bank fee, the measured "
                  "FX markup, and a published US receiving fee. Tax is never folded into these numbers.",
                  "costs.html") + f"""
<div class="notice">
  <strong>Read this before using the numbers.</strong> These are <em>estimates built from public
  price lists</em>, not quotes. Three components: (1) a bank fee that is published (S14), (2) an FX
  markup measured from one dated official quotation (S16), (3) a US receiving fee published by one
  bank (S15). A commercial FX spread is not regulated and is not published as a rule; your bank's
  executable quote supersedes this page. No tax is included — see <a href="taxes.html">Tax &amp;
  penalties</a> for the conditional layer.
</div>

<h2>1 · The lawful documented route, tier by tier (R01)</h2>
<p class="small">Bank fee = 0.1% of the CNY remitted, floor CNY 100, cap CNY 500, plus CNY 120 cable
{cite('S14')}. Spread = {costs['rate']['spread_pct']}% of the USD received, measured as the half-spread
between BOC's published USD buying and selling rates {cite('S16')}. US bank = $16 {cite('S15')}.</p>
<div class="table-wrap"><table class="stack" id="primary-costs">
<thead><tr><th>Amount</th><th>Bank fee (USD)</th><th>FX spread</th><th>US bank</th><th>All-in</th><th>% of amount</th><th>Basis</th><th>Sources</th></tr></thead>
<tbody>{primary}</tbody></table></div>
<p><a class="btn" href="data/costs.csv" download>Download all {meta['row_count']} rows (CSV)</a>
<a class="btn" href="data/costs.json" download>JSON</a></p>

<h2>2 · Compare methods at the same amount</h2>
<p class="small">Pick the row for your amount. <strong>R04</strong> shows "cap" or "over cap" because the
annual ceiling is CNY 100,000 (about USD 14,958 on 2026-11-10). <strong>R10/R11</strong> are unlawful:
their figures are the statutory <em>maximum fine</em>, not a cost you pay to move money.</p>
<ul class="legend small">{legend}</ul>
<div class="table-wrap scroll-x"><table class="pivot">
<thead><tr><th>Amount</th>{pivot_head}</tr></thead><tbody>{pivot_body}</tbody></table></div>

<h2>3 · Where the money goes at each scale</h2>
<div class="grid cards">
  <article class="card"><h3>$10,000</h3>
    <p>Fixed costs dominate: the CNY 220 floor-plus-cable is about
    {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==10000)['fx_fee_usd'])}
    regardless of size, so the all-in is
    {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==10000)['all_in_usd'])}
    ({next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==10000)['pct']}%).</p></article>
  <article class="card"><h3>$100,000</h3>
    <p>Spread overtakes the fee:
    {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==100000)['spread_usd'])}
    of spread vs
    {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==100000)['fx_fee_usd'])}
    of bank fee; all-in
    {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==100000)['all_in_usd'])}
    ({next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==100000)['pct']}%).</p></article>
  <article class="card"><h3>$400,000</h3>
    <p>The fee is capped at CNY 500 + CNY 120, so it is nearly irrelevant; the spread is
    {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==400000)['spread_usd'])}.
    All-in
    {money(next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==400000)['all_in_usd'])}
    ({next(r for r in costs['rows'] if r['route']=='R01' and r['amount']==400000)['pct']}%).</p></article>
  <article class="card"><h3>The one lever that matters</h3>
    <p>Negotiating the FX markup moves the answer far more than any fee. Each 0.10 percentage point of
    spread costs <strong>$100 per $100,000</strong>. That is why the brief's "conversion penalty" is
    mostly a pricing question, not a tax question.</p></article>
</div>

<h2>4 · Assumptions, in full</h2>
<p class="small">Every departure from a published figure is listed here rather than buried in the table.</p>
{assumptions}
""" + footer()


# --------------------------------------------------------------------- taxes
def page_taxes():
    tax = costs["tax_layer"]
    scen = ""
    for s in tax["scenarios"]:
        scen += (f'<tr><td data-label="If acquired">{esc(s["label"])}</td>'
                 f'<td data-label="Gain %">{s["gain_pct"]}%</td>'
                 f'<td data-label="On $10,000">{money(s["gain_on_10k"])}</td>'
                 f'<td data-label="On $100,000">{money(s["gain_on_100k"])}</td>'
                 f'<td data-label="On $400,000">{money(s["gain_on_400k"])}</td>'
                 f'<td data-label="Sources">{cite("S12","S16")}</td></tr>')

    return header("Tax and penalties: what is actually taxed",
                  "A conversion is not the taxable event people fear. This page separates the currency "
                  "trade, the income that funded it, the reporting duties, and the penalties for getting "
                  "the route itself wrong.", "taxes.html") + f"""
<h2>The five things people call "the tax"</h2>
<div class="table-wrap"><table class="stack">
<thead><tr><th>Layer</th><th>Does it apply to moving your own CNY out?</th><th>Amount</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="Layer"><strong>A Chinese conversion levy</strong></td>
    <td data-label="Applies?">No such levy appears in the rules I verified. The bank's job is to verify authenticity; it is not collecting a tax on the exchange.</td>
    <td data-label="Amount"><span class="blank">none found</span></td><td data-label="Source">{cite('S01','S02')}</td></tr>
<tr><td data-label="Layer"><strong>PRC income tax on the underlying income</strong></td>
    <td data-label="Applies?">This is the tax that is real — but it attaches to the income (salary, property gain), and the conversion file requires the tax voucher as proof it was dealt with.</td>
    <td data-label="Amount"><span class="blank">depends on the income</span></td><td data-label="Source">{cite('S01','S07')}</td></tr>
<tr><td data-label="Layer"><strong>US §988 exchange gain on the conversion</strong></td>
    <td data-label="Applies?">A personal transaction is excluded, unless the exchange gain exceeds $200 — then the exclusion does not apply.</td>
    <td data-label="Amount">see the table below</td><td data-label="Source">{cite('S08','S12')}</td></tr>
<tr><td data-label="Layer"><strong>FBAR / Form 8938 reporting</strong></td>
    <td data-label="Applies?">Reporting duties on the <em>account</em>, not the transfer. FBAR above $10,000 aggregate at any point in the year; 8938 at higher thresholds.</td>
    <td data-label="Amount">penalties, not tax</td><td data-label="Source">{cite('S10','S11')}</td></tr>
<tr><td data-label="Layer"><strong>Fines if the route is unlawful</strong></td>
    <td data-label="Applies?">Splitting quotas, private dealing, illegal carriage.</td>
    <td data-label="Amount">up to 30% of the amount</td><td data-label="Source">{cite('S02')}</td></tr>
</tbody></table></div>

<h2>US §988: the $200 line</h2>
<p>The statute says that where an individual disposes of nonfunctional currency in a personal
transaction, "no gain shall be recognized … by reason of changes in exchange rates", and then:
<em>"The preceding sentence shall not apply if the gain which would otherwise be recognized on the
transaction exceeds $200."</em> {cite('S08')} A "personal transaction" excludes anything whose
allocable expenses meet §162 (other than travel) or §212 (other than taxes) — so business use changes
the analysis {cite('S08')}.</p>
<p class="small caveat">Technical caveat, flagged as F08: §988(e)(1) says the section does not apply to
an individual's personal transactions, while (e)(2) sets the $200 rule. How the two sentences interact
when the gain exceeds $200 is a question for a professional; this page reports the text, not a
conclusion about your return.</p>

<h3>What the arithmetic looks like</h3>
<p class="small">Formula: <code>{esc(tax['formula'])}</code>. Rate history from the IRS yearly averages
{cite('S12')}; conversion rate is BOC's published selling rate on 2026-11-10 {cite('S16')}. These rows
illustrate the size of the gain, not a tax bill: the marginal rate, the acquisition date and the amount
actually held are unknown.</p>
<div class="table-wrap"><table class="stack">
<thead><tr><th>If the CNY was acquired at…</th><th>Gain on conversion</th><th>On $10,000</th><th>On $100,000</th><th>On $400,000</th><th>Sources</th></tr></thead>
<tbody>{scen}</tbody></table></div>
<p class="small">Note the far right column: the gain is comfortably over $200 at every tier where the
yuan strengthened, so the $200 exclusion is not a practical shelter for a large balance — the question
is the acquisition rate. A balance acquired when the rate was <em>weaker</em> than today produces a loss,
and the treatment of a personal-transaction loss is not resolved on this page (F08).</p>

<h2>Reporting: FBAR and Form 8938</h2>
<div class="table-wrap"><table class="stack">
<thead><tr><th></th><th>FBAR (FinCEN 114)</th><th>Form 8938</th></tr></thead>
<tbody>
<tr><td data-label="Trigger">Trigger</td>
    <td data-label="FBAR">Aggregate value of foreign financial accounts exceeded <strong>$10,000</strong> at any time in the calendar year {cite('S10')}</td>
    <td data-label="8938">US resident: >$50,000 year-end or >$75,000 anytime (single); >$100,000 / >$150,000 (joint). Living abroad: >$200,000 / >$300,000 (single); >$400,000 / >$600,000 (joint) {cite('S11')}</td></tr>
<tr><td data-label="Deadline">Deadline</td>
    <td data-label="FBAR">April 15, automatic extension to October 15; filed with FinCEN, not the return {cite('S10')}</td>
    <td data-label="8938">Attached to the return, due with it {cite('S11')}</td></tr>
<tr><td data-label="Penalty">Penalty ceiling</td>
    <td data-label="FBAR">Non-willful <strong>$16,536</strong>; willful <strong>$165,353</strong> (amounts for penalties assessed on or after 2025-01-17) {cite('S09')}</td>
    <td data-label="8938">Up to $10,000, plus $10,000 per 30 days after notice, maximum $60,000 {cite('S11')}</td></tr>
</tbody></table></div>
<p class="small">These are ceilings published by the authorities, not predictions. They are the largest
number in this whole project, and they are triggered by <em>not filing</em>, not by converting.</p>

<h2>If the route is unlawful: the statutory ceiling</h2>
<div class="table-wrap"><table class="stack">
<thead><tr><th>Conduct</th><th>Provision</th><th>Ceiling</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="Conduct">Moving funds abroad in evasion (逃汇)</td><td data-label="Provision">条例 Art. 39</td><td data-label="Ceiling">Fine up to 30% of the amount; 30% to the equivalent amount if serious; criminal liability possible</td><td data-label="Source">{cite('S02')}</td></tr>
<tr><td data-label="Conduct">Illegal FX purchase / 套汇</td><td data-label="Provision">条例 Art. 40</td><td data-label="Ceiling">Fine up to 30%; 30% to the equivalent if serious</td><td data-label="Source">{cite('S02')}</td></tr>
<tr><td data-label="Conduct">Carrying currency across the border illegally</td><td data-label="Provision">条例 Art. 42</td><td data-label="Ceiling">Warning plus fine up to 20% of the amount</td><td data-label="Source">{cite('S02')}</td></tr>
<tr><td data-label="Conduct">Private or disguised FX trading</td><td data-label="Provision">条例 Art. 45</td><td data-label="Ceiling">Warning, confiscation of gains, fine up to 30%; 30%–100% if serious; criminal liability possible</td><td data-label="Source">{cite('S02')}</td></tr>
<tr><td data-label="Conduct">Splitting to evade the quota</td><td data-label="Provision">汇发〔2020〕14号 Art. 62</td><td data-label="Ceiling">"关注名单" watchlist for the year plus two more, with enhanced review; plus the 逃汇 provisions above</td><td data-label="Source">{cite('S01')}</td></tr>
</tbody></table></div>
""" + footer()


# --------------------------------------------------------------------- steps
def page_steps():
    r = ROUTE_BY_ID["R01"]
    steps = "".join(f"<li><strong>Step {i+1}.</strong> {esc(s)}</li>" for i, s in enumerate(r["steps"]))
    return header("Step by step: the playbook",
                  "The documented route, in order, with the document checklist and the variants for the "
                  "cases where the money did not come from salary.", "steps.html") + f"""
<h2>Before you start: three questions only you can answer</h2>
<ol class="big">
  <li><strong>What is the money?</strong> Salary and other current-account income? A property sale? A
  gift? An inheritance? The route changes, and choosing wrongly is the main way people get refused.</li>
  <li><strong>Is it CNY, or already a foreign currency?</strong> If it is already USD, you may only need
  the remittance step {cite('S01')}.</li>
  <li><strong>Have you ever held PRC household registration, and did you cancel it?</strong> If yes, the
  emigration-asset route may cover the whole balance {cite('S04')}. If you never held it, that route is
  not open to you.</li>
</ol>
<p class="small">I do not assume any of these. Each is a flag on the <a href="review.html">review page</a>.</p>

<h2>The primary playbook (salary / current-account income)</h2>
<ol class="steps">{steps}</ol>
<p class="small">Sources for each step: {cite('S01','S02','S03','S07','S14')}</p>

<h2>The document checklist</h2>
<div class="table-wrap"><table class="stack">
<thead><tr><th>Item</th><th>Why it is needed</th><th>Official basis</th></tr></thead>
<tbody>
<tr><td data-label="Item">Passport (valid ID)</td><td data-label="Why">Identity for every conversion and remittance</td><td data-label="Basis">Art. 59 {cite('S01')}; Art. 65 {cite('S01')}</td></tr>
<tr><td data-label="Item">Employment contract + payslips</td><td data-label="Why">Shows the RMB is lawful current-account income</td><td data-label="Basis">Art. 59 "购汇资金来源材料" {cite('S01')}</td></tr>
<tr><td data-label="Item">PRC individual income tax record (完税凭证)</td><td data-label="Why">Art. 59 names tax vouchers expressly</td><td data-label="Basis">Art. 59 {cite('S01')}; SAFE Q&amp;A {cite('S07')}</td></tr>
<tr><td data-label="Item">Bank conversion slip (水单)</td><td data-label="Why">Proves the exchange happened; also the 24-month reconversion window</td><td data-label="Basis">Art. 60 {cite('S01')}</td></tr>
<tr><td data-label="Item">SWIFT confirmation</td><td data-label="Why">Evidence of the amount sent and received for US reporting</td><td data-label="Basis">Reporting duties {cite('S10','S11')}</td></tr>
<tr><td data-label="Item">If emigrated: 户籍注销证明 + embassy-authenticated settlement proof</td><td data-label="Why">Required for an emigration asset transfer</td><td data-label="Basis">Art. 8 {cite('S04')}</td></tr>
<tr><td data-label="Item">If inherited: inheritance proof + deceased's property documents</td><td data-label="Why">Required for an inheritance transfer</td><td data-label="Basis">Art. 9 {cite('S04')}</td></tr>
</tbody></table></div>

<h2>Variants</h2>
<details open><summary><strong>If the account already holds USD</strong></summary>
<p>Skip the conversion. A non-domestic individual remitting from a foreign-currency account needs valid
ID under Art. 65(1), with no amount cap stated {cite('S01')}. Cost drops to the wire fee plus the
receiving fee — about {money(next(r for r in costs['rows'] if r['route']=='R02' and r['amount']==400000)['all_in_usd'])}
at $400,000 in the model.</p></details>
<details><summary><strong>If you emigrated and cancelled PRC household registration</strong></summary>
<p>One application for the whole amount to the SAFE branch of your original household registration
{cite('S04')}. Once it is approved, the bank may send the approved amount in one remittance or in
several: the instalment schedule in the 2004 measure (half, half of the remainder after a year, the
balance after two years) and the head-office step above RMB 500,000 were both removed with effect from
10 February 2014 {cite('S17')}. <em>Corrected 11 November 2026: this paragraph previously gave the 2004
schedule as current.</em></p></details>
<details><summary><strong>If the money is an inheritance</strong></summary>
<p>Same measure, different documents: proof of inheritance, the deceased's property documents and the
tax certificate {cite('S04')}. Since 2014, property inherited from different deceased persons may be
combined in one application, and the bank may remit once or in several payments after approval
{cite('S17')}. <em>Corrected 11 November 2026: this paragraph previously required one application per
deceased person.</em></p></details>
<details><summary><strong>If the amount is small and you want cash</strong></summary>
<p>Legal ceilings are low: up to USD 5,000 without a permit, USD 5,000–10,000 with a bank 携带证, and in
principle not more than USD 10,000 at all {cite('S05')}. The US requires a FinCEN 105 declaration over
USD 10,000, and the threshold aggregates across a family or group {cite('S13')}. Do not split cash
between travellers.</p></details>

<h2>Before you file your US return</h2>
<ol class="big">
  <li>Reconstruct when you acquired the CNY and at what rate — this decides whether §988 gain exceeds
  $200 {cite('S08','S12')}.</li>
  <li>Check the FBAR threshold: aggregate foreign accounts over $10,000 at any point in the year
  {cite('S10')}.</li>
  <li>Check the Form 8938 threshold for your filing status and residence {cite('S11')}.</li>
  <li>Keep the Chinese conversion slips and tax vouchers for at least five years {cite('S10')}.</li>
</ol>
""" + footer()


# ------------------------------------------------------------------- sources
def page_sources():
    rows = ""
    for sid, s in sources.items():
        rows += f"""<tr id="{sid.lower()}">
<td data-label="ID"><strong>{sid}</strong></td>
<td data-label="Authority">{esc(s['authority'])}<span class="sub">{esc(s['jur'])} · {esc(s['lang'])}</span></td>
<td data-label="Document"><a href="{esc(s['url'])}" target="_blank" rel="noopener noreferrer">{esc(s['title'])}</a>
  <span class="sub">Locator: {esc(s['locator'])}</span></td>
<td data-label="Quoted text" class="quote">{esc(s['quote'])}</td>
<td data-label="Checked">{esc(s['verified_at'])}</td></tr>"""
    return header(f"{len(sources)} primary sources, quoted and dated",
                  "Every source on this site was fetched and quoted here with its locator: "
                  + str(ORIGINAL_SOURCES) + " in the original session on " + meta["generated"]
                  + "".join(f", and {s['id']} on {s['verified_at']} by a later correction" for s in ADDED_SOURCES)
                  + ". If a page did not load or a figure was not in the text, it is not on this site.",
                  "sources.html") + f"""
<div class="notice"><strong>What "verified" means here:</strong> I opened the document, found the
passage, and copied it. It does not mean the document is still current law tomorrow, and it does not
mean a bank will apply it to your file. Two sources are commercial price lists (S14, S15) and one is a
dated market quotation (S16); they are labelled as such, and they are never used to state a rule.</div>
<div class="table-wrap"><table class="stack sources">
<thead><tr><th>ID</th><th>Authority</th><th>Document &amp; locator</th><th>What it says (verbatim)</th><th>Checked</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<h2>Not used, and why</h2>
<p class="small">Company help-centre pages describing CNY corridors, aggregator blogs quoting "average"
wire fees, and any page whose figure I could not read in the primary document. Prior sessions in this
repository cited some of these; the <a href="repo-audit.html">repo audit</a> lists them.</p>
""" + footer()


# ---------------------------------------------------------------- review page
FLAGS = [
    ("F01", "Private facts that decide the answer",
     "Whether the balance is CNY or a foreign currency; whether it is salary, property proceeds, a gift "
     "or an inheritance; whether you have cancelled PRC household registration; when and at what rate "
     "you acquired it. Every one of these changes the lawful route.",
     "Not inferred anywhere on this site. The methods page separates them explicitly.",
     ["S01", "S04"]),
    ("F02", "The USD 50,000 cap is described inconsistently across the repo",
     "Some pages say no cap applies to documented current-account income; the repository's site/index.html "
     "calls the USD 50,000 facilitation quota 'the binding constraint'. Both cannot be right.",
     "In this site: Art. 54 puts the quota on FX sales and domestic individuals' purchases; Art. 59 "
     "governs a non-domestic individual's documented purchase with no quota stated.",
     ["S01", "S03", "S07"]),
    ("F03", "Published dollar costs for the same CNY 220 fee disagree",
     "Prior sessions publish $30.86 (repatriate), $30.99 (ladder, rate 7.1) and this session computes "
     "$32.91 at the dated BOC selling rate 6.6851. The fee in CNY is identical; only the rate differs.",
     "All three are arithmetically correct. None is wrong — but a reader comparing pages sees three "
     "prices for one fee. This site uses one dated rate and states it.",
     ["S14", "S16"]),
    ("F04", "FX spread bands in prior cost tables have no source",
     "ladder/data/costs.csv applies a 0.30%–1.50% spread band ($30–$150 per $10,000). No source is "
     "cited for the band.",
     "This site replaces the band with a measured half-spread of 0.2098% from one dated BOC quotation, "
     "and says so. Neither figure is a quote for your transaction.",
     ["S16"]),
    ("F05", "Commercial provider pages appear in an 'Official sources' column",
     "briefing/costs.html labels Wise and Western Union help pages as official sources for methods.",
     "A company page is evidence of what that company advertises, not of a rule. This site lists the "
     "corridor as unverified (R13) and cites no commercial page as authority.",
     []),
    ("F06", "No Chinese conversion levy was found — that is an absence, not a ruling)",
     "I read the FX Regulations, the 2020 current-account guideline and the individual FX rules. None "
     "imposes a tax on exchanging currency; the conversion file requires tax vouchers instead.",
     "Stated as an analytical conclusion on the overview and tax pages, with the basis visible. Confirm "
     "with a PRC tax adviser before relying on it.",
     ["S01", "S02"]),
    ("F07", "§988(e)(1) and §988(e)(2) interact awkwardly above $200",
     "(e)(1) disapplies the section for personal transactions; (e)(2) sets the $200 gain rule and says "
     "the no-gain sentence does not apply above it.",
     "The page quotes both and does not assert a conclusion. A preparer should resolve this for the "
     "actual facts.",
     ["S08"]),
    ("F08", "A personal-transaction FX loss is not resolved here",
     "The gain rule is explicit; the loss side is not addressed in the text I quoted.",
     "Left blank rather than guessed. Do not assume a loss is deductible.",
     ["S08"]),
    ("F09", "The property-proceeds route is only partly verified",
     "PBOC Order No. 3 Art. 22 covers a non-domestic individual buying housing; I did not re-read the "
     "property repatriation rules this session.",
     "Route R08 is marked conditional and its document list is marked unverified.",
     ["S03", "S04"]),
    ("F10", "FBAR penalty amounts are the 2025-01-17 adjustment",
     "The eCFR table is current to 2026-11-06 but its last codified change is 2025-01-17; amounts are "
     "adjusted annually for inflation.",
     "Quoted as published with the effective date attached. Re-check before relying on a number.",
     ["S09"]),
    ("F11", "The cost model is one bank's tariff",
     "HSBC China's schedule is used because it is the only dated, published per-transfer tariff I could "
     "verify. It binds HSBC China customers only.",
     "Labelled on every cost page. ICBC, BOC, CCB and others publish their own tariffs and were not "
     "verified here.",
     ["S14"]),
    ("F12", "Correspondent and intermediary bank deductions are excluded",
     "No source publishes what a correspondent bank will take from a China→US wire.",
     "The all-in figures therefore understate the possible deduction. Choose OUR / 'Pay Exact' if you "
     "want the amount to arrive whole — CNY 200 at HSBC China.",
     ["S14"]),
    ("F13", "Third-party remittance corridor is unverified",
     "No official source confirms a mainland personal CNY balance can be sent to the US through a "
     "Wise-type platform.",
     "R13 is marked unverified with no cost. Verify the corridor directly before relying on it.",
     []),
    ("F14", "Crypto / USDT status was not re-verified",
     "Widely described as prohibited in the PRC, but I did not re-read the notice this session.",
     "R15 is present but flagged, with no assertion and no cost.",
     []),
]


EVIDENCE = {
    "F01": "methods.html", "F02": "index.html", "F03": "costs.html",
    "F04": "costs.html", "F05": "../briefing/costs.html", "F06": "index.html",
    "F07": "taxes.html", "F08": "taxes.html", "F09": "methods.html#r08",
    "F10": "taxes.html", "F11": "costs.html", "F12": "costs.html",
    "F13": "methods.html#r13", "F14": "methods.html#r15",
}


def page_review():
    rows = ""
    for code, title, what, treatment, srcs in FLAGS:
        rows += f"""<tr id="{code.lower()}">
<td data-label="Flag"><strong>{code}</strong></td>
<td data-label="Irregularity"><strong>{esc(title)}</strong><span class="sub">{esc(what)}</span></td>
<td data-label="How it is handled here">{esc(treatment)}</td>
<td data-label="Sources">{cite(*srcs) if srcs else ""} <a class="src" href="{EVIDENCE[code]}" title="Where this is shown in this site">evidence</a></td></tr>"""
    return header("Flagged for review",
                  "Everything I could not confirm, everything that disagrees with another page in this "
                  "repository, and everything that depends on facts I do not have. None of it is "
                  "silently resolved.", "review.html") + f"""
<div class="notice warning"><strong>These flags do not block the site.</strong> They are published so you
can see exactly where the evidence stops. Nothing here was filled in by inference.</div>
<div class="table-wrap"><table class="stack">
<thead><tr><th>Flag</th><th>Irregularity</th><th>How it is handled</th><th>Sources</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<h2>Blank, not zero</h2>
<p>Where this site shows "—" or an empty cell, the value is unknown, not zero. The three blanks that
matter most: your acquisition rate (drives §988), your bank's FX markup (drives the all-in cost), and
your eligibility for the emigration/inheritance routes (drives whether the whole balance can move at once).</p>
""" + footer()


# --------------------------------------------------------------- repo audit
def page_audit():
    return header("Repository audit",
                  "What is in this repository, what I checked mechanically, and what disagrees. Line "
                  "references are to the committed files at the commit shown below.", "repo-audit.html") + f"""
<h2>What I checked</h2>
<div class="table-wrap"><table class="stack">
<thead><tr><th>Check</th><th>Method</th><th>Result</th><th>Evidence</th></tr></thead>
<tbody>
<tr><td data-label="Check">Internal links and fragments</td><td data-label="Method">Crawled all 69 HTML files in the repository for href/src targets and resolved them on disk</td><td data-label="Result"><strong>0 broken internal references</strong></td><td data-label="Evidence"><a href="../index.html">root hub</a>, <a href="../ladder/index.html">ladder</a>, <a href="../docs/index.html">docs</a></td></tr>
<tr><td data-label="Check">Route-count claims</td><td data-label="Method">Regex scan of rendered text for "N routes / methods"</td><td data-label="Result">Six different counts published: 15, 17, 18, 20, 22, 26</td><td data-label="Evidence"><a href="../briefing/methods.html">briefing/methods.html</a>, <a href="../ladder/routes.html">ladder/routes.html</a>, <a href="../repatriate/methods.html">repatriate/methods.html</a></td></tr>
<tr><td data-label="Check">Cost datasets</td><td data-label="Method">Row counts and first-row comparison of ladder, repatriate and audit-86f0 CSVs</td><td data-label="Result">600 / 680 / 880 rows, same fee expressed at three different USD values</td><td data-label="Evidence"><a href="../ladder/data/costs.csv">ladder/data/costs.csv</a>, <a href="../repatriate/exports/cost-ladders.csv">repatriate/exports/cost-ladders.csv</a>, <a href="../audit-86f0/cost-matrix.csv">audit-86f0/cost-matrix.csv</a></td></tr>
<tr><td data-label="Check">Non-official sources</td><td data-label="Method">Domain extraction from every external link</td><td data-label="Result">24 domains; commercial pages (wise.com, westernunion.com) cited in an "Official sources" column</td><td data-label="Evidence"><a href="../briefing/costs.html">briefing/costs.html</a>, <a href="review.html#f05">flag F05</a></td></tr>
<tr><td data-label="Check">Quote fidelity</td idioma="x" data-label="Method">Re-fetched 16 sources and compared to the passages quoted here</td><td data-label="Result">All 16 quoted passages appear in the fetched documents</td><td data-label="Evidence"><a href="sources.html">sources.html</a></td></tr>
<tr><td data-label="Check">Arithmetic</td><td data-label="Method">Independent recomputation of the HSBC fee tiers and the cost ladder</td><td data-label="Result">Prior sessions' CNY 220 arithmetic reproduces at their stated rates (7.129 → $30.86); this site uses 6.6851 → $32.91</td><td data-label="Evidence"><a href="costs.html">costs.html</a>, <a href="review.html#f03">flag F03</a></td></tr>
</tbody></table></div>

<h2>Duplicate dashboards</h2>
<p>This repository contains {meta.get('pages', 69)} published HTML pages across 14 directories, produced
by at least ten sessions working the same brief independently. Several publish overlapping cost tables
with different numbers. That is not a merge bug — it is what happens when ten sessions answer the same
question without a single source of truth. The honest fix is not to delete the others but to state
plainly which figures this site uses, on what rate, and why.</p>
<ul>
  <li><a href="../docs/index.html"><strong>docs/</strong></a> — 9 pages, 67 findings / 24 sources (per its README)</li>
  <li><a href="../ladder/index.html"><strong>ladder/</strong></a> — 10 pages, 600 cost rows, rate basis 7.1</li>
  <li><a href="../repatriate/index.html"><strong>repatriate/</strong></a> — 17 methods, 680 cost rows, rate basis 7.129</li>
  <li><a href="../briefing/index.html"><strong>briefing/</strong></a> — 7 pages, consolidated briefing with commercial-provider citations</li>
  <li><strong>audit-86f0/, audit-0f0f59fe/, audit-ad300459/, audit-456e7542/</strong> — audit lenses</li>
  <li><strong>acceptance-*/, verify-*/, portal/, site/</strong> — acceptance and portal layers</li>
</ul>

<h2>Commit and scope</h2>
<p>This site is additive: <code>final-f6327e23/</code> plus one CI workflow plus an append to
<code>COORDINATION.md</code>. No other session's file was edited. The task board records the claim,
the scope and this result.</p>

<h2>What this audit is not</h2>
<p>It is not a certification of the other directories' factual claims, and it is not a legal review.
It is a mechanical check of links, counts and arithmetic, plus a fresh read of the 16 sources this site
cites. Where another page asserts something I could not verify, it is listed as a flag rather than
silently adopted or silently "corrected".</p>
""" + footer()


def write(name, html):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(html)


def write_csv():
    keys = ["route", "amount", "fx_fee_usd", "spread_usd", "receive_usd",
            "all_in_usd", "pct", "capability", "note"]
    with open(os.path.join(DATA, "costs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in costs["rows"]:
            w.writerow({k: r.get(k, "") for k in keys})


def main():
    write("index.html", page_index())
    write("methods.html", page_methods())
    write("costs.html", page_costs())
    write("taxes.html", page_taxes())
    write("steps.html", page_steps())
    write("sources.html", page_sources())
    write("review.html", page_review())
    write("repo-audit.html", page_audit())
    write_csv()
    print("built 8 pages + data/costs.csv")


if __name__ == "__main__":
    main()
