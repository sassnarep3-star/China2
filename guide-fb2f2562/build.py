#!/usr/bin/env python3
"""Build every page of guide-fb2f2562 from data/*.json and content.py. Deterministic output.

Run (after model.py; audit.py only when refreshing the repo snapshot):
    python3 guide-fb2f2562/model.py && python3 guide-fb2f2562/build.py
"""
import csv
import html
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as C  # noqa: E402

SOURCES = json.load(open(os.path.join(HERE, "data", "sources.json"), encoding="utf-8"))
SRC = {s["id"]: s for s in SOURCES}
COSTS = json.load(open(os.path.join(HERE, "data", "costs.json"), encoding="utf-8"))
REVIEW = json.load(open(os.path.join(HERE, "data", "review.json"), encoding="utf-8"))
P = COSTS["params"]
ROWS = COSTS["rows"]
METHODS = {m["id"]: m for m in C.METHODS}
RULES = {r["id"]: r for r in REVIEW["rules"]}

esc = html.escape


def usd(x):
    return "" if x is None else f"${x:,.2f}"


def cny(x):
    return "" if x is None else f"CNY {x:,.2f}"


def pct(x):
    return "" if x is None else f"{x:.3f}%"


def n0(x):
    return "" if x is None else f"{x:,}"


def srcs(ids):
    return "".join(f'<a href="{esc(SRC[i]["url"])}" title="{esc(SRC[i]["title"])}" rel="noopener">{i}</a>' for i in ids)


def link_refs(text):
    """Turn [S01 Art. 2, S03] style markers into links to the official page."""
    import re

    def rep(m):
        inner = m.group(1)
        parts = []
        for chunk in inner.split(","):
            chunk = chunk.strip()
            mm = re.match(r"(S\d\d)(.*)", chunk)
            if mm and mm.group(1) in SRC:
                parts.append(f'<a href="{esc(SRC[mm.group(1)]["url"])}" rel="noopener">{mm.group(1)}</a>{esc(mm.group(2))}')
            else:
                parts.append(esc(chunk))
        return '<span class="src">[' + ", ".join(parts) + "]</span>"

    out, last = [], 0
    for m in re.finditer(r"\[((?:S\d\d[^\]]*))\]", text):
        out.append(esc(text[last:m.start()]))
        out.append(rep(m))
        last = m.end()
    out.append(esc(text[last:]))
    return "".join(out)


def blank_td(label):
    return f'<td class="blank" data-label="{esc(label)}"></td>'


def td(v, label, cls="num"):
    if v is None or v == "":
        return blank_td(label)
    return f'<td class="{cls}" data-label="{esc(label)}">{v}</td>'


NAV = [("index.html", "Dashboard"), ("summary.html", "Summary"), ("questions.html", "Questions"),
       ("methods.html", "Methods"), ("penalty.html", "Penalty"), ("costs.html", "Costs"),
       ("review.html", "Repo review"), ("flagged.html", "Flagged"), ("sources.html", "Sources")]


def page(fname, title, body):
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{h}"{cur if h == fname else ""}>{t}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China money guide</title>
<meta name="description" content="Lawful CNY to USD for a US citizen: methods, costs at every USD 10,000 step, tax layers, flagged items — every row linked to its official source.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a href="index.html">China money · CNY → USD<small>Decision guide · sources read {C.TODAY}</small></a>
<span class="meta"><a href="../index.html">← All sections</a> · not tax or legal advice</span></div></header>
<nav class="site" aria-label="Guide pages"><div class="wrap">{nav}</div></nav>
<main id="main" class="wrap">
{body}
</main>
<footer><div class="wrap">Section <code>guide-fb2f2562</code> · every figure links to the official page it came from ·
blank cells are values no official page states (see <a href="flagged.html">Flagged for Review</a>) ·
rates are dated published boards, not executable quotes.</div></footer>
<script src="assets/app.js"></script>
</body>
</html>
"""


FMT = dict(
    m01_10=usd(ROWS["M01"][0]["total_known_usd"]), m01_400=usd(ROWS["M01"][-1]["total_known_usd"]),
    m01_400_pct=f'{ROWS["M01"][-1]["total_known_pct"]:.3f}%', m02_400=usd(ROWS["M02"][-1]["total_known_usd"]),
    gain_pct=f'{P["gain_pct_2025"]:.2f}%', boc_spread=f'{P["boc_spread_pct"]:.2f}%', hsbc_spread=f'{P["hsbc_spread_pct"]:.2f}%',
)
CHEAPER_M03 = [a["usd"] for a, c in zip(ROWS["M01"], ROWS["M03"]) if c["total_known_usd"] < a["total_known_usd"]]
FMT["m03_note"] = ("" if not CHEAPER_M03 else
                   f" (an existing HSBC Premier customer pays less with Global Transfer at {', '.join(usd(x)[:-3] for x in CHEAPER_M03)}, before the CNY 300 monthly Premier fee)")
SUMMARY = [s.format(**FMT) for s in C.SUMMARY]
SUMMARY_SRC = [["S09", "S01", "S02", "S03", "S04", "S20", "S21"], ["S08", "S10", "S13"], ["S01", "S03", "S02", "S04"],
               ["S12", "S14"], ["S15", "S09", "S18"], ["S27", "S07", "S01", "S21", "S23", "S25", "S26"], ["S12", "S29", "S18"]]

REPO_FLAGS = [x for x in REVIEW["findings"] if x["verdict"] == "conflict"]


# ------------------------------------------------------------------------------------------------
def p_index():
    m01, m02, m03 = ROWS["M01"], ROWS["M02"], ROWS["M03"]
    t = REVIEW["totals"]
    picks = [0, 4, 9, 19, 29, 39]
    rows = "".join(
        f'<tr><th scope="row" data-label="Amount">{usd(m01[i]["usd"])[:-3]}</th>'
        f'{td(usd(m01[i]["total_known_usd"]), "BOC (M01)")}{td(usd(m02[i]["total_known_usd"]), "HSBC TT (M02)")}'
        f'{td(usd(m03[i]["total_known_usd"]), "HSBC Premier GT (M03)")}<td class="src" data-label="Source">{srcs(["S01", "S03", "S02", "S04"])}</td></tr>'
        for i in picks)
    body = f"""
<h1>Getting your RMB out of China as US dollars — lawfully, at the lowest cost</h1>
<p class="lede">For a US citizen with CNY in a mainland bank account. Built only from official pages read on {C.TODAY};
anything they do not state is left blank and listed on <a href="flagged.html">Flagged for Review</a>.</p>
<div class="kpis">
 <div class="kpi"><p class="l">Tax on converting</p><p class="v">None found</p><p class="s">No official page read imposes one; the gate is paperwork. {srcs(["S09", "S08", "S10"])}</p></div>
 <div class="kpi"><p class="l">Cheapest published route</p><p class="v">BOC wire</p><p class="s">{FMT["m01_10"]} at $10k · {FMT["m01_400"]} at $400k (fee + spread){" · HSBC Premier GT is lower at " + ", ".join(usd(x)[:-3] for x in CHEAPER_M03) if CHEAPER_M03 else ""} {srcs(["S01", "S03", "S04"])}</p></div>
 <div class="kpi"><p class="l">Spread to midpoint</p><p class="v">{FMT["boc_spread"]} / {FMT["hsbc_spread"]}</p><p class="s">Bank of China / HSBC China boards {srcs(["S01", "S02"])}</p></div>
 <div class="kpi"><p class="l">US gain if RMB bought at 7.129</p><p class="v">≈ {FMT["gain_pct"]}</p><p class="s">Not excluded above $200 per conversion {srcs(["S27", "S07"])}</p></div>
</div>
<div class="notice"><strong>Before you choose:</strong> the route depends on where the money came from and whether PRC tax was paid.
Answer the <a href="questions.html">12 decision questions</a> first. Nothing here is a personal tax determination or an executable quote.</div>
<h2>Start here</h2>
<div class="cards">
 <a class="card" href="methods.html#M01"><b>Salary or other taxed income</b><span>Documented USD purchase + wire to your own US account (M01–M03). Bring passport, contract, tax records.</span></a>
 <a class="card" href="methods.html#M05"><b>You emigrated; pre-emigration savings or property</b><span>SAFE emigrant property transfer (M05): free, ≤ 25 working days, no staging since 2014.</span></a>
 <a class="card" href="methods.html#M04"><b>Recent China salary, smaller sums</b><span>Wise CNY out (M04): CNY 300,000 per transfer, tax record ≤ 3 years.</span></a>
 <a class="card warn" href="methods.html#U01"><b>Do not use</b><span>Quota splitting, underground swaps, disguised transfers, crypto — fines up to 30%–100% or illegal outright.</span></a>
</div>
<h2>Known cost at a glance (USD sent)</h2>
<p class="small">Published fee + exchange spread to the board midpoint. Correspondent/receiving fees are not published (blank). All 40 steps: <a href="costs.html">Costs</a>.</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>Amount</th><th class="num">BOC (M01)</th><th class="num">HSBC TT (M02)</th><th class="num">HSBC Premier GT (M03)</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Pages</h2>
<div class="cards">
 <a class="card" href="summary.html"><b>Executive summary</b><span>Seven points, each sourced</span></a>
 <a class="card" href="questions.html"><b>Decision questions</b><span>{len(C.QUESTIONS)} questions · known · unknown · how to find out</span></a>
 <a class="card" href="methods.html"><b>All methods</b><span>{len(C.METHODS)} methods · pros, cons, step by step</span></a>
 <a class="card" href="penalty.html"><b>The “conversion penalty”</b><span>{len(C.PENALTY)} layers · FX-gain calculator</span></a>
 <a class="card" href="costs.html"><b>Costs $10k–$400k</b><span>40 steps × {len(C.METHODS)} methods + US gain table</span></a>
 <a class="card" href="review.html"><b>Repo review</b><span>{REVIEW["scanned_files"]} files scanned · {t["conflict"]} conflicting lines · {t["check"]} to check</span></a>
 <a class="card warn" href="flagged.html"><b>Flagged for Review</b><span>{len(C.FLAGS)} blanks/open items + {len(REPO_FLAGS)} conflicting repo lines</span></a>
 <a class="card" href="sources.html"><b>Sources</b><span>{len(SOURCES)} official pages read {C.TODAY}</span></a>
</div>
"""
    return page("index.html", "Dashboard", body)


def p_summary():
    items = "".join(f'<tr><th scope="row" data-label="#">{i + 1}</th><td class="text" data-label="Point">{esc(s)}</td>'
                    f'<td class="src" data-label="Sources">{srcs(SUMMARY_SRC[i])}</td></tr>' for i, s in enumerate(SUMMARY))
    body = f"""<h1>Executive summary</h1>
<p class="lede">The short answer, with the official page behind each point.</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>#</th><th>Point</th><th>Sources</th></tr></thead><tbody>{items}</tbody></table></div>
<h2>Recommended order of work</h2>
<ol class="steps">
<li>Answer the <a href="questions.html">decision questions</a> — origin of the money, tax paid, residence status, emigrant or not.</li>
<li>Collect passport, source-of-funds documents and PRC tax records {srcs(["S08", "S10", "S14"])}.</li>
<li>Bring US reporting up to date before moving large sums (FBAR, Form 8938; streamlined procedures if non-wilful) {srcs(["S21", "S23", "S30"])}.</li>
<li>Ask the bank for its current rate, fee and online limits; compare with the <a href="costs.html">cost tables</a> {srcs(["S01", "S03"])}.</li>
<li>Convert and wire to your own US account; keep every slip {srcs(["S13"])}.</li>
<li>Record the CNY acquisition rate and the conversion rate for each transaction to work out any gain above $200 {srcs(["S27"])}.</li>
</ol>"""
    return page("summary.html", "Executive summary", body)


def p_questions():
    rows = "".join(
        f'<tr id="{q["id"]}"><th scope="row" class="text" data-label="Question"><span class="key">{q["id"]}</span> {esc(q["q"])}</th>'
        f'<td class="text" data-label="Why it matters">{esc(q["why"])}</td><td class="text" data-label="What we know">{link_refs(q["known"])}</td>'
        f'<td class="text" data-label="Still unknown">{esc(q["unknown"])}</td><td class="text" data-label="How to find out">{esc(q["find"])}</td>'
        f'<td class="src" data-label="Sources">{srcs(q["sources"])}</td></tr>' for q in C.QUESTIONS)
    body = f"""<h1>Questions to answer before deciding</h1>
<p class="lede">Each row: what the official text already tells us, what only you can supply, and how to get it.</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>Question</th><th>Why it matters</th><th>What we know</th><th>Still unknown</th><th>How to find out</th><th>Sources</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return page("questions.html", "Decision questions", body)


KIND = {"priced": "Priced from published inputs", "partial": "Partly priced — some inputs unpublished", "unlawful": "Unlawful — do not use"}


def p_methods():
    over = "".join(
        f'<tr><th scope="row" class="text" data-label="Method"><a href="#{m["id"]}">{m["id"]}</a> {esc(m["name"])}</th>'
        f'<td class="text" data-label="Status">{KIND[m["kind"]]}</td><td class="text" data-label="Who can use it">{link_refs(m["who"])}</td>'
        f'<td class="text" data-label="Limit">{link_refs(m["limit"])}</td><td class="src" data-label="Sources">{srcs(m["sources"])}</td></tr>'
        for m in C.METHODS)
    det = []
    for m in C.METHODS:
        pros = "".join(f"<li>{link_refs(x)}</li>" for x in m["pros"]) or "<li>None.</li>"
        cons = "".join(f"<li>{link_refs(x)}</li>" for x in m["cons"])
        steps = "".join(f"<li>{link_refs(x)}</li>" for x in m["steps"])
        det.append(f"""<section class="method {m['kind']}" id="{m['id']}"><h3>{m['id']} · {esc(m['name'])}</h3>
<p class="small">{KIND[m['kind']]} · Speed: {link_refs(m['speed'])} · <a href="costs.html#c-{m['id']}">Cost table</a></p>
<div class="grid2"><div><strong>Pros</strong><ul class="tight">{pros}</ul></div><div><strong>Cons</strong><ul class="tight">{cons}</ul></div></div>
<strong>Step by step</strong><ol class="steps">{steps}</ol><p class="src">Sources: {srcs(m['sources'])}</p></section>""")
    body = f"""<h1>Every CNY → USD method</h1>
<p class="lede">{sum(1 for m in C.METHODS if m['kind'] != 'unlawful')} lawful routes and {sum(1 for m in C.METHODS if m['kind'] == 'unlawful')} unlawful ones (kept visible so they are not mistaken for strategies).</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>Method</th><th>Status</th><th>Who can use it</th><th>Limit</th><th>Sources</th></tr></thead><tbody>{over}</tbody></table></div>
{''.join(det)}"""
    return page("methods.html", "Methods", body)


def p_penalty():
    rows = "".join(
        f'<tr><th scope="row" class="text" data-label="Layer">{p["id"]} · {esc(p["layer"])}</th>'
        + (td(esc(p["size"]), "Size", "text") if p["size"] else blank_td("Size"))
        + f'<td class="text" data-label="What the official text says">{link_refs(p["note"])}</td><td class="src" data-label="Sources">{srcs(p["sources"])}</td></tr>'
        for p in C.PENALTY)
    g = ROWS["USTAX"]
    grows = "".join(
        f'<tr><th scope="row" data-label="USD received">{usd(r["usd"])}</th>{td(usd(r["gain_if_basis_2025"]), "Gain if basis 7.129 (2025 avg)")}'
        f'{td(usd(r["gain_if_basis_2024"]), "Gain if basis 7.189 (2024 avg)")}{td(cny(r["cny_converted"]), "CNY converted at 6.6886")}'
        f'{blank_td("US tax on the gain")}<td class="src" data-label="Source">{srcs(["S27", "S07", "S01"])}</td></tr>' for r in g)
    body = f"""<h1>The “conversion penalty”, layer by layer</h1>
<p class="lede">There is no single penalty. These are the separate costs and risks people lump together.</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>Layer</th><th>Size</th><th>What the official text says</th><th>Sources</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2 id="gain">US exchange-gain check</h2>
<p>Under 26 U.S.C. §988(e)(2), gain on a personal currency conversion is ignored only if it is $200 or less {srcs(["S27"])}.
Enter your own figures (nothing is sent anywhere):</p>
<div class="calc" id="fxcalc">
 <label>CNY converted<input id="fx-cny" inputmode="decimal" value="1000000"></label>
 <label>CNY per USD when you acquired the CNY<input id="fx-basis" inputmode="decimal" placeholder="e.g. your deposit-date rate"></label>
 <label>CNY per USD when converting<input id="fx-now" inputmode="decimal" value="{P['boc_sell']}"></label>
 <div>USD gain (loss): <output id="fx-out">enter your acquisition rate</output><div class="small" id="fx-note"></div></div>
</div>
<p class="small">Illustration below uses the IRS yearly averages as stand-in acquisition rates {srcs(["S07"])} and today's BOC sell rate {srcs(["S01"])}. Your actual basis is the rate on each deposit date. The tax on the gain depends on your return and is left blank (flag F-11).</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>USD received</th><th class="num">Gain if basis 7.129</th><th class="num">Gain if basis 7.189</th><th class="num">CNY converted</th><th>US tax on gain</th><th>Source</th></tr></thead><tbody>{grows}</tbody></table></div>"""
    return page("penalty.html", "Conversion penalty", body)


COST_SPECS = {
    "M01": ("wire", ["S01", "S03"]), "M02": ("wire", ["S02", "S04"]), "M03": ("wire", ["S02", "S04"]),
    "M04": ("wise", ["S05", "S06"]), "M05": ("emig", ["S14"]), "M06": ("atm", ["S16", "S06"]), "M07": ("cash", ["S17", "S01", "S28"]),
    "U01": ("fine", ["S15"]), "U02": ("fine", ["S09"]), "U03": ("fine", ["S18"]), "U04": ("fine", ["S09"]),
}


def cost_table(mid):
    kind, sids = COST_SPECS[mid]
    s = srcs(sids)
    rows = []
    if kind == "wire":
        head = ["USD sent", "Known cost", "% of amount", "Bank fee", "FX spread", "CNY debited", "Gap to Fed H.10", "Intermediary + receiving fee", "Source"]
        for r in ROWS[mid]:
            rows.append(f'<tr><th scope="row" data-label="USD sent">{usd(r["usd"])}</th>{td("<b>" + usd(r["total_known_usd"]) + "</b>", "Known cost")}'
                        f'{td(pct(r["total_known_pct"]), "% of amount")}{td(cny(r["fee_cny"]), "Bank fee")}{td(usd(r["margin_usd"]), "FX spread")}'
                        f'{td(cny(r["cny_debited"]), "CNY debited")}{td(usd(r["gap_to_fed_usd"]), "Gap to Fed H.10")}{blank_td("Intermediary + receiving fee")}'
                        f'<td class="src" data-label="Source">{s}</td></tr>')
    elif kind == "wise":
        head = ["USD", "Transfers (bank app ≤ CNY 300k)", "Transfers (Alipay ≤ CNY 50k)", "CNY at Fed H.10", "Wise fee", "Wise rate", "Source"]
        for r in ROWS[mid]:
            rows.append(f'<tr><th scope="row" data-label="USD">{usd(r["usd"])}</th>{td(n0(r["transfers_bank_app"]), "Transfers (bank app)")}'
                        f'{td(n0(r["transfers_alipay"]), "Transfers (Alipay)")}{td(cny(r["cny_at_fed"]), "CNY at Fed H.10")}{blank_td("Wise fee")}{blank_td("Wise rate")}'
                        f'<td class="src" data-label="Source">{s}</td></tr>')
    elif kind == "emig":
        head = ["USD", "SAFE approval fee", "SAFE max working days", "Bank fee", "FX spread", "Source"]
        for r in ROWS[mid]:
            rows.append(f'<tr><th scope="row" data-label="USD">{usd(r["usd"])}</th>{td(cny(r["safe_fee_cny"]), "SAFE approval fee")}'
                        f'{td(n0(r["safe_max_working_days"]), "SAFE max working days")}{blank_td("Bank fee")}{blank_td("FX spread")}<td class="src" data-label="Source">{s}</td></tr>')
    elif kind == "atm":
        head = ["USD", "Calendar years at RMB 100k/yr", "Card-days at RMB 10k/day", "CNY at Fed H.10", "ATM + issuer fees", "Source"]
        for r in ROWS[mid]:
            rows.append(f'<tr><th scope="row" data-label="USD">{usd(r["usd"])}</th>{td("<b>" + n0(r["calendar_years"]) + "</b>", "Calendar years")}'
                        f'{td(n0(r["card_days"]), "Card-days")}{td(cny(r["cny_at_fed"]), "CNY at Fed H.10")}{blank_td("ATM + issuer fees")}<td class="src" data-label="Source">{s}</td></tr>')
    elif kind == "cash":
        head = ["USD", "Exits at ≤ $5,000 (no permit)", "Exits at ≤ $10,000 (bank permit)", "FX spread (BOC cash sell)", "Withdrawal fee", "Source"]
        for r in ROWS[mid]:
            rows.append(f'<tr><th scope="row" data-label="USD">{usd(r["usd"])}</th>{td("<b>" + n0(r["trips_no_permit"]) + "</b>", "Exits ≤ $5,000")}'
                        f'{td(n0(r["trips_bank_permit"]), "Exits ≤ $10,000")}{td(usd(r["fx_margin_usd"]), "FX spread")}{blank_td("Withdrawal fee")}<td class="src" data-label="Source">{s}</td></tr>')
    else:
        head = ["USD", "Fine up to 30%", "Serious case up to 100%", "Consequence", "Source"]
        for r in ROWS[mid]:
            rows.append(f'<tr><th scope="row" data-label="USD">{usd(r["usd"])}</th>{td(usd(r["fine_ordinary_usd"]), "Fine up to 30%")}'
                        f'{td(usd(r["fine_serious_usd"]), "Serious case up to 100%")}<td class="text" data-label="Consequence">{esc(r["consequence"])}</td><td class="src" data-label="Source">{s}</td></tr>')
    numc = ' class="num"'
    th = "".join(f'<th{numc if i and i < len(head) - 1 else ""}>{esc(h)}</th>' for i, h in enumerate(head))
    return f'<div class="tablewrap"><table class="stack"><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def p_costs():
    m01, m02, m03 = ROWS["M01"], ROWS["M02"], ROWS["M03"]
    comp = "".join(
        f'<tr><th scope="row" data-label="USD sent">{usd(a["usd"])}</th>{td("<b>" + usd(a["total_known_usd"]) + "</b>", "BOC (M01)")}'
        f'{td(usd(b["total_known_usd"]), "HSBC TT (M02)")}{td(usd(c["total_known_usd"]), "HSBC Premier GT (M03)")}'
        f'{td(pct(a["total_known_pct"]), "BOC %")}<td class="src" data-label="Source">{srcs(["S01", "S03", "S02", "S04"])}</td></tr>'
        for a, b, c in zip(m01, m02, m03))
    opts = "".join(f'<option value="c-{m["id"]}">{m["id"]} · {esc(m["name"])}</option>' for m in C.METHODS)
    sections = "".join(
        f'<section class="ctab" id="c-{m["id"]}"><h3>{m["id"]} · {esc(m["name"])}</h3><p class="small">{KIND[m["kind"]]} · '
        f'<a href="methods.html#{m["id"]}">Method details</a></p>{cost_table(m["id"])}</section>' for m in C.METHODS)
    body = f"""<h1>Costs at every $10,000 step, $10,000 – $400,000</h1>
<p class="lede">Published inputs only: Bank of China board 666.06 / 668.86 per 100 USD (15:30, {C.TODAY}) {srcs(["S01"])} and fee table {srcs(["S03"])};
HSBC China board 6.6386339 / 6.7053746 (10 Nov) {srcs(["S02"])} and tariff {srcs(["S04"])}. “Known cost” = bank fee + spread to the board midpoint.
Blank (yellow) = no official figure; see <a href="flagged.html">Flagged</a>.</p>
<div class="notice">Fee caps: BOC CNY {P['boc_fee_cap_cny']:.0f} (≈ {usd(P['boc_cap_usd'])}); HSBC CNY {P['hsbc_fee_cap_cny']:.0f} (≈ {usd(P['hsbc_cap_usd'])} at HSBC's sell rate).
Above about $40,000 (BOC) and $75,000 (HSBC) the fee stops growing and the spread is almost the whole cost.
CSV: <a href="data/costs.csv">costs.csv</a> · JSON: <a href="data/costs.json">costs.json</a></div>
<h2 id="compare">Compare the priced routes</h2>
<div class="tablewrap"><table class="stack"><thead><tr><th>USD sent</th><th class="num">BOC (M01)</th><th class="num">HSBC TT (M02)</th><th class="num">HSBC Premier GT (M03)</th><th class="num">BOC % of amount</th><th>Source</th></tr></thead><tbody>{comp}</tbody></table></div>
<h2 id="each">Every method, every step</h2>
<label for="msel" class="small">Show one method:</label><br><select id="msel" class="filter"><option value="">All methods</option>{opts}</select>
{sections}"""
    return page("costs.html", "Costs", body)


VLABEL = {"conflict": ("Conflicts with official text", "b-conflict"), "check": ("Check", "b-check"),
          "consistent": ("Consistent", "b-ok"), "corrected": ("Carries correction", "b-ok"), "quoted": ("Quotes another file", "b-ok")}


def p_review():
    t = REVIEW["totals"]
    rrows = []
    for r in REVIEW["rules"]:
        c = {v: sum(1 for x in REVIEW["findings"] if x["rule"] == r["id"] and x["verdict"] == v) for v in VLABEL}
        rrows.append(f'<tr id="{r["id"]}"><th scope="row" class="text" data-label="Rule">{r["id"]} · {esc(r["title"])}</th>'
                     f'<td class="text" data-label="Official text">{esc(r["official"])}</td>'
                     + "".join(td(n0(c[v]), VLABEL[v][0]) for v in VLABEL)
                     + f'<td class="src" data-label="Source">{srcs(r["sources"])}</td></tr>')
    secs = REVIEW["sections"]
    srows = []
    for s in sorted(secs):
        cells = []
        for r in REVIEW["rules"]:
            c = secs[s][r["id"]]
            if c["conflict"]:
                cells.append(f'<td data-label="{r["id"]}"><span class="badge b-conflict">{c["conflict"]} ✗</span></td>')
            elif c["check"]:
                cells.append(f'<td data-label="{r["id"]}"><span class="badge b-check">{c["check"]} ?</span></td>')
            elif c["consistent"] or c["corrected"] or c["quoted"]:
                cells.append(f'<td data-label="{r["id"]}"><span class="badge b-ok">✓</span></td>')
            else:
                cells.append(f'<td data-label="{r["id"]}">—</td>')
        srows.append(f'<tr><th scope="row" data-label="Section"><code>{esc(s)}</code></th>{"".join(cells)}<td class="src" data-label="Sources">{srcs(sorted({i for r in REVIEW["rules"] for i in r["sources"]}))}</td></tr>')
    sh = "".join(f'<th><a href="#{r["id"]}">{r["id"]}</a></th>' for r in REVIEW["rules"])
    lines = []
    for x in REVIEW["findings"]:
        if x["verdict"] != "conflict":
            continue
        r = RULES[x["rule"]]
        lines.append(f'<tr data-rule="{x["rule"]}"><th scope="row" class="text" data-label="File : line"><code>{esc(x["file"])}:{x["line"]}</code></th>'
                     f'<td data-label="Rule">{x["rule"]}</td><td data-label="Verdict"><span class="badge {VLABEL[x["verdict"]][1]}">{VLABEL[x["verdict"]][0]}</span></td>'
                     f'<td class="text" data-label="Text on that line">{esc(x["excerpt"])}</td><td class="text" data-label="Why">{esc(x["why"])}</td>'
                     f'<td class="src" data-label="Official source">{srcs(r["sources"])}</td></tr>')
    groups = {}
    for x in REVIEW["findings"]:
        if x["verdict"] == "check":
            groups.setdefault((x["rule"], x["file"]), []).append(x)
    checks = []
    for (rid, f), xs in sorted(groups.items()):
        nums = ", ".join(str(x["line"]) for x in xs)
        checks.append(f'<tr data-rule="{rid}"><th scope="row" class="text" data-label="File"><code>{esc(f)}</code></th><td data-label="Rule">{rid}</td>'
                      f'<td class="num" data-label="Lines">{len(xs)}</td><td class="text" data-label="Line numbers">{esc(nums)}</td>'
                      f'<td class="text" data-label="Example">{esc(xs[0]["excerpt"][:200])}</td><td class="text" data-label="Why">{esc(xs[0]["why"])}</td>'
                      f'<td class="src" data-label="Official source">{srcs(RULES[rid]["sources"])}</td></tr>')
    body = f"""<h1>Repository review — line by line</h1>
<p class="lede">An automated scan of all {REVIEW["scanned_files"]} tracked text files outside this section (commit <code>{esc(REVIEW["scanned_at_commit"])}</code>, {REVIEW["generated"]})
for {len(REVIEW["rules"])} load-bearing figures and claims, compared with the official text read today. It finds {t["conflict"]} lines that conflict with the
official text and {t["check"]} lines to check; {t["consistent"] + t["corrected"]} lines agree or carry a correction, and {t["quoted"]} only quote another file.</p>
<div class="notice">Pattern matching, not legal review: every line is listed with its file and line number so you can open it. “Check” means the line is
not wrong on its face but differs from the official framing (for example the HSBC CNY 620 cap converted at the IRS 7.129 average rather than the bank's rate).
Files are not edited here; corrections are requested in <code>COORDINATION.md</code>. Full data: <a href="data/review.json">review.json</a> (all {len(REVIEW["findings"])} matches) · <a href="data/review.csv">review.csv</a> (conflict and check lines).</div>
<h2>Rules and results</h2>
<div class="tablewrap"><table class="stack"><thead><tr><th>Rule</th><th>Official text</th>{''.join(f'<th class="num">{VLABEL[v][0]}</th>' for v in VLABEL)}<th>Source</th></tr></thead><tbody>{''.join(rrows)}</tbody></table></div>
<h2>Scorecard by section</h2>
<p class="small">✗ = lines conflicting with official text · ? = lines to check · ✓ = mentions agree · — = not mentioned.</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>Section</th>{sh}<th>Sources</th></tr></thead><tbody>{''.join(srows)}</tbody></table></div>
<h2 id="lines">Every line that conflicts with official text ({len(lines)})</h2>
<input id="rfilter" class="filter" type="search" placeholder="Filter by file, rule or text" aria-label="Filter lines">
<div class="tablewrap"><table class="stack" id="rtable"><thead><tr><th>File : line</th><th>Rule</th><th>Verdict</th><th>Text on that line</th><th>Why</th><th>Official source</th></tr></thead><tbody>{''.join(lines)}</tbody></table></div>
<h2 id="checks">Lines to check, grouped by file ({REVIEW["totals"]["check"]} lines; {len(checks)} rule × file groups)</h2>
<p class="small">Every line number is listed; the example is the first one in the file. Full excerpts for each line are in <a href="data/review.csv">review.csv</a>.</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>File</th><th>Rule</th><th class="num">Lines</th><th>Line numbers</th><th>Example</th><th>Why</th><th>Official source</th></tr></thead><tbody>{''.join(checks)}</tbody></table></div>"""
    return page("review.html", "Repo review", body)


def p_flagged():
    frows = "".join(
        f'<tr id="{f["id"]}"><th scope="row" class="text" data-label="Flag">{f["id"]} · {esc(f["item"])}</th><td class="text" data-label="Status">{esc(f["status"])}</td>'
        f'<td class="text" data-label="How to resolve">{esc(f["action"])}</td><td class="src" data-label="Source">{srcs(f["sources"])}</td></tr>' for f in C.FLAGS)
    rrows = "".join(
        f'<tr><th scope="row" class="text" data-label="File : line"><code>{esc(x["file"])}:{x["line"]}</code></th><td data-label="Rule"><a href="review.html#{x["rule"]}">{x["rule"]}</a></td>'
        f'<td class="text" data-label="Text">{esc(x["excerpt"])}</td><td class="text" data-label="Official text says">{esc(RULES[x["rule"]]["official"])}</td>'
        f'<td class="src" data-label="Source">{srcs(RULES[x["rule"]]["sources"])}</td></tr>' for x in REPO_FLAGS)
    body = f"""<h1>Flagged for Review</h1>
<p class="lede">Every value left blank in this section, every open question about the sources, and every line elsewhere in the repository that
conflicts with the official text. Flagged items are published, not hidden.</p>
<h2>Blanks and open items in this section ({len(C.FLAGS)})</h2>
<div class="tablewrap"><table class="stack"><thead><tr><th>Flag</th><th>Status</th><th>How to resolve</th><th>Source</th></tr></thead><tbody>{frows}</tbody></table></div>
<h2>Now verified (previously flagged elsewhere)</h2>
<div class="tablewrap"><table class="stack"><thead><tr><th>Item</th><th>Official text</th><th>Source</th></tr></thead><tbody>
<tr><th scope="row" class="text" data-label="Item">2027 foreign earned income exclusion USD 137,300</th><td class="text" data-label="Official text">{esc(SRC["S26"]["quote"])}</td><td class="src" data-label="Source">{srcs(["S26"])}</td></tr>
<tr><th scope="row" class="text" data-label="Item">Emigrant transfers are not staged</th><td class="text" data-label="Official text">{esc(SRC["S12"]["finding"])}</td><td class="src" data-label="Source">{srcs(["S12"])}</td></tr>
</tbody></table></div>
<h2>Repository lines that conflict with official text ({len(REPO_FLAGS)})</h2>
<div class="tablewrap"><table class="stack"><thead><tr><th>File : line</th><th>Rule</th><th>Text</th><th>Official text says</th><th>Source</th></tr></thead><tbody>{rrows}</tbody></table></div>
<p class="small">Lines marked “check” ({REVIEW["totals"]["check"]}) are listed on <a href="review.html#lines">Repo review</a>.</p>"""
    return page("flagged.html", "Flagged for Review", body)


def quote_html(s):
    return "<br><q>" + esc(s["quote"]) + "</q>" if s.get("quote") else ""


def p_sources():
    rows = "".join(
        f'<tr id="{s["id"]}"><th scope="row" class="text" data-label="Source"><a href="{esc(s["url"])}" rel="noopener">{s["id"]} · {esc(s["title"])}</a></th>'
        f'<td class="text" data-label="Publisher">{esc(s["publisher"])}</td><td class="text" data-label="Where">{esc(s["locator"])}</td>'
        f'<td class="text" data-label="What it says">{esc(s["finding"])}{quote_html(s)}</td>'
        f'<td data-label="Read">{s["read"]}</td></tr>' for s in SOURCES)
    body = f"""<h1>Sources</h1>
<p class="lede">{len(SOURCES)} official pages, each opened on {C.TODAY}. “What it says” is a close paraphrase with exact figures; quoted text is verbatim.</p>
<div class="tablewrap"><table class="stack"><thead><tr><th>Source</th><th>Publisher</th><th>Where</th><th>What it says</th><th>Read</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return page("sources.html", "Sources", body)


def exec_md():
    lines = ["# China money — executive summary (guide-fb2f2562)", "",
             f"Official sources read {C.TODAY}. Site: `guide-fb2f2562/index.html`. Not tax or legal advice.", ""]
    for i, s in enumerate(SUMMARY):
        refs = ", ".join(f"[{x}]({SRC[x]['url']})" for x in SUMMARY_SRC[i])
        lines.append(f"{i + 1}. {s} ({refs})")
    lines += ["", "## Known cost (fee + spread to board midpoint), USD sent", "",
              "| USD | BOC M01 | HSBC TT M02 | HSBC Premier GT M03 |", "|---:|---:|---:|---:|"]
    for a, b, c in zip(ROWS["M01"], ROWS["M02"], ROWS["M03"]):
        lines.append(f"| {usd(a['usd'])} | {usd(a['total_known_usd'])} | {usd(b['total_known_usd'])} | {usd(c['total_known_usd'])} |")
    lines += ["", f"Repo review: {REVIEW['totals']['conflict']} conflicting lines, {REVIEW['totals']['check']} to check, across {REVIEW['scanned_files']} files (see `review.html`).", ""]
    return "\n".join(lines)


def review_csv():
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["rule", "verdict", "file", "line", "col", "match", "excerpt", "official_source_urls"])
    for x in REVIEW["findings"]:
        if x["verdict"] not in ("conflict", "check"):
            continue
        w.writerow([x["rule"], x["verdict"], x["file"], x["line"], x["col"], x["match"], x["excerpt"],
                    " ".join(SRC[i]["url"] for i in RULES[x["rule"]]["sources"])])
    return buf.getvalue()


def main():
    out = {
        "index.html": p_index(), "summary.html": p_summary(), "questions.html": p_questions(), "methods.html": p_methods(),
        "penalty.html": p_penalty(), "costs.html": p_costs(), "review.html": p_review(), "flagged.html": p_flagged(),
        "sources.html": p_sources(), "EXECUTIVE_SUMMARY.md": exec_md(), "data/review.csv": review_csv(),
    }
    data = {"methods": C.METHODS, "questions": C.QUESTIONS, "penalty": C.PENALTY, "flags": C.FLAGS, "summary": SUMMARY}
    out["data/content.json"] = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    for name, text in out.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print("built", len(out), "files")


if __name__ == "__main__":
    main()
