#!/usr/bin/env python3
"""Deterministic builder for the repatriate/ dashboard (session arena/3e494fa5-china2).

Reads only repatriate/data/*.json (verified this session) and writes static HTML,
CSV and JSON exports. No network, no timestamps, no randomness - byte-identical
output on every run so CI can `git diff --exit-code`.

Cost policy: computed cells are deterministic arithmetic from published inputs
(cited per row). Unknown commercial values are rendered as blank cells with an
"unverified" flag reference. Nothing is inferred.
"""
import csv
import html
import io
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

SOURCES = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text())["sources"]}
RULES_DOC = json.loads((DATA / "rules.json").read_text())
RULES = {p["id"]: p for p in RULES_DOC["parameters"]}
METHODS = json.loads((DATA / "methods.json").read_text())["methods"]
FLAGS = json.loads((DATA / "flags.json").read_text())["flags"]
AUDIT = json.loads((DATA / "audit.json").read_text())["findings"]
RATE = RULES_DOC["reference_rate"]["cny_per_usd"]  # 7.129, IRS 2025 yearly average (S23)
AMOUNTS = list(range(10000, 400001, 10000))  # 40 increments

NAV = [
    ("index.html", "Overview"),
    ("methods.html", "Methods & steps"),
    ("costs.html", "Cost tables $10k–$400k"),
    ("taxes.html", "Tax & reporting"),
    ("sources.html", "Sources"),
    ("audit.html", "Repo audit"),
    ("flagged.html", "Flagged for review"),
]


def e(x):
    return html.escape(str(x), quote=True)


def src_links(ids, label_prefix=""):
    out = []
    for sid in ids:
        s = SOURCES[sid]
        out.append(
            f'<a class="src" href="{e(s["url"])}" target="_blank" rel="noopener noreferrer" '
            f'title="{e(s["title"])}">{e(label_prefix + sid)} ↗</a>'
        )
    return " ".join(out)


def flag_link(fid):
    return f'<a class="flag" href="flagged.html#{e(fid)}">{e(fid)}</a>'


def usd(x):
    return f"${x:,.2f}"


def blank(reason_flag="F03"):
    return f'<span class="blank" aria-label="blank: unverified"></span> {flag_link(reason_flag)}'


# ---------------- cost models (deterministic, published inputs only) ----------------

def tt_fee_cny(amount_cny):
    """HSBC Premier/Advance TT: 0.1%, min CNY100, max CNY500, + CNY120 cable (S29 2.2.4.1-2)."""
    p = RULES["P11"]["value"]
    issuance = min(max(amount_cny * p["pct"] / 100.0, p["min_cny"]), p["max_cny"])
    return issuance + RULES["P12"]["value"]


def ladder_row(m, amount):
    """Return dict for one (method, amount) cell set. None => blank/unverified."""
    cny = amount * RATE
    cm = m["cost_model"]
    t = cm["type"]
    row = {"method": m["id"], "amount_usd": amount, "amount_cny_ref": round(cny, 2)}
    if t == "hsbc_tt":
        fee_cny = tt_fee_cny(cny)
        row.update(published_fee_usd=round(fee_cny / RATE, 2), published_fee_cny=round(fee_cny, 2),
                   constraint="1 wire", constraint_detail="Single wire assumed; bank splitting practice unknown",
                   sources=["S29", "S23", "S03"])
    elif t == "hsbc_tt_quota":
        q = cm["quota_usd"]
        years = math.ceil(amount / q)
        remaining = amount
        total_cny = 0.0
        while remaining > 0:
            tranche = min(remaining, q)
            total_cny += tt_fee_cny(tranche * RATE)
            remaining -= tranche
        row.update(published_fee_usd=round(total_cny / RATE, 2), published_fee_cny=round(total_cny, 2),
                   constraint=f"{years} calendar year{'s' if years != 1 else ''}",
                   constraint_detail=f"{years} wire(s) of ≤$50,000 (own quota only)",
                   sources=["S01", "S29", "S23"])
    elif t == "global_transfer":
        row.update(published_fee_usd=0.0, published_fee_cny=0.0,
                   constraint="Premier / Private Banking",
                   constraint_detail="Advance: $20/transaction; transaction count unknown → total unverified",
                   sources=["S29", "S03"])
    elif t == "wise":
        transfers = math.ceil(cny / RULES["P17"]["value"])
        row.update(published_fee_usd=None, published_fee_cny=None,
                   constraint=f"{transfers} transfer(s)",
                   constraint_detail="≤CNY 300,000 per bank-app transfer; overall limit = your documented after-tax salary",
                   sources=["S30", "S23"])
    elif t == "atm":
        years = math.ceil(cny / RULES["P04"]["value"])
        days = math.ceil(cny / RULES["P05"]["value"])
        row.update(published_fee_usd=None, published_fee_cny=None,
                   constraint=f"{years} calendar year{'s' if years != 1 else ''}",
                   constraint_detail=f"≥{days} withdrawal days (RMB 10,000/card/day); RMB 100,000/person/year across all cards",
                   sources=["S07", "S23"])
    elif t == "cash_carry":
        trips_free = math.ceil(amount / RULES["P06"]["value"])
        trips_permit = math.ceil(amount / RULES["P07"]["value"])
        row.update(published_fee_usd=0.0, published_fee_cny=0.0,
                   constraint=f"{trips_free} trips (no permit)",
                   constraint_detail=f"{trips_permit} trips with bank permits ($5k–$10k/trip); published bank withdrawal fee $0; travel cost unverified; repeat-traveler limits apply",
                   sources=["S10", "S29", "S28"])
    elif t == "rmb_carry":
        trips = math.ceil(cny / RULES["P08"]["value"])
        row.update(published_fee_usd=None, published_fee_cny=None,
                   constraint=f"{trips} trips",
                   constraint_detail="≤CNY 20,000/trip; offshore conversion cost unverified",
                   sources=["S11", "S12", "S23"])
    elif t == "reconversion":
        days = math.ceil(amount / RULES["P09"]["value"])
        row.update(published_fee_usd=None, published_fee_cny=None,
                   constraint=f"{days} bank days (ID-only)",
                   constraint_detail="Only previously exchanged unused RMB; memo route limited to original exchange amount (24-month validity)",
                   sources=["S04", "S01"])
    elif t == "penalty":
        p = RULES[cm["fine_pct_source"]]["value"]
        row.update(published_fee_usd=None, published_fee_cny=None,
                   fine_standard_max_usd=round(amount * p["standard_max_pct"] / 100.0, 2),
                   fine_serious_min_usd=round(amount * p["serious_min_pct"] / 100.0, 2),
                   fine_serious_max_usd=round(amount * p["serious_max_pct"] / 100.0, 2),
                   constraint="REJECTED — unlawful",
                   constraint_detail="Statutory fine exposure (not a price); confiscation/repatriation orders and criminal liability may also apply",
                   sources=["S13", "S06"] if cm["fine_pct_source"] == "P32" else ["S13"])
    else:  # unknown
        row.update(published_fee_usd=None, published_fee_cny=None,
                   constraint="Eligibility / quote required",
                   constraint_detail=cm.get("note", "No published fee schedule"),
                   sources=m["sources"][:3])
    return row


def build_ladders():
    return {m["id"]: [ladder_row(m, a) for a in AMOUNTS] for m in METHODS}


# ---------------- HTML layout ----------------

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#17202a;--mut:#5b6b7b;--line:#dfe5ec;--acc:#0b5fa5;--acc2:#0a7d4f;--warn:#9a6700;--bad:#b42318;--chip:#eef3f8}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--acc)}
header.top{background:#0d1b2a;color:#fff;padding:14px 16px}
header.top .wrap{max-width:1080px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px 18px;align-items:baseline}
header.top h1{font-size:1.05rem;margin:0;letter-spacing:.3px}
header.top .tag{font-size:.75rem;color:#9fb3c8}
nav.main{background:#13273d;padding:6px 8px;position:sticky;top:0;z-index:5}
nav.main .wrap{max-width:1080px;margin:0 auto;display:flex;gap:2px;overflow-x:auto;-webkit-overflow-scrolling:touch}
nav.main a{color:#cfe0f1;text-decoration:none;font-size:.82rem;padding:8px 10px;border-radius:8px;white-space:nowrap}
nav.main a[aria-current=page]{background:#0b5fa5;color:#fff}
main{max-width:1080px;margin:0 auto;padding:18px 14px 60px}
h2{font-size:1.25rem;margin:26px 0 10px}h3{font-size:1.02rem;margin:18px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0}
.grid{display:grid;gap:12px}.grid.c2{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.kpi{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.kpi .k{flex:1 1 150px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}
.kpi .k b{display:block;font-size:1.35rem;color:var(--acc)}
.kpi .k span{font-size:.78rem;color:var(--mut)}
.notice{border-left:4px solid var(--warn);background:#fff8e6;padding:10px 12px;border-radius:8px;font-size:.9rem;margin:12px 0}
.notice.bad{border-color:var(--bad);background:#fdecea}
.notice.ok{border-color:var(--acc2);background:#e9f7f0}
.table-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:.85rem;min-width:560px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
thead th{background:var(--chip);position:sticky;top:0;font-size:.78rem;text-transform:uppercase;letter-spacing:.4px;color:#33475b}
tbody tr:nth-child(even){background:#fafbfd}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr:last-child td{border-bottom:0}
.src{display:inline-block;font-size:.72rem;background:var(--chip);border:1px solid var(--line);border-radius:6px;padding:1px 6px;margin:1px 2px 1px 0;text-decoration:none;white-space:nowrap}
.flag{display:inline-block;font-size:.7rem;background:#fff3cd;color:#7a5b00;border-radius:6px;padding:1px 6px;text-decoration:none;border:1px solid #f0e0a0}
.blank{display:inline-block;min-width:28px;border-bottom:1px dashed #b9c4cf;height:.9em}
.chip{display:inline-block;font-size:.72rem;border-radius:999px;padding:2px 10px;border:1px solid var(--line);background:var(--chip);color:#33475b}
.chip.ok{background:#e9f7f0;color:var(--acc2);border-color:#bfe6d2}
.chip.warn{background:#fff3cd;color:var(--warn);border-color:#f0e0a0}
.chip.bad{background:#fdecea;color:var(--bad);border-color:#f3c1bc}
.method{border:1px solid var(--line);border-radius:12px;background:var(--card);margin:14px 0;padding:16px}
.method h3{margin-top:0}
.method .cols{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.method ul{margin:6px 0;padding-left:20px;font-size:.9rem}
.method ol{margin:6px 0;padding-left:20px;font-size:.9rem}
details{margin:10px 0}summary{cursor:pointer;font-weight:600;color:var(--acc);padding:6px 0}
footer{border-top:1px solid var(--line);margin-top:30px;padding-top:14px;font-size:.8rem;color:var(--mut)}
.small{font-size:.8rem;color:var(--mut)}
a.button{display:inline-block;background:var(--acc);color:#fff;text-decoration:none;border-radius:8px;padding:8px 14px;font-size:.85rem;margin:4px 6px 4px 0}
a.button.sec{background:#fff;color:var(--acc);border:1px solid var(--acc)}
@media (max-width:640px){table{font-size:.78rem;min-width:520px}th,td{padding:6px 7px}main{padding:12px 8px 48px}}
@media print{nav.main{position:static}header.top{background:#fff;color:#000}.table-scroll{overflow:visible;border:0}table{min-width:0}}
"""


def page(name, title, body, active):
    nav = "".join(
        '<a href="' + e(href) + '"' + (' aria-current="page"' if href == active else '') + '>' + e(label) + '</a>'
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · China → USD repatriation research</title>
<meta name="description" content="Source-verified research: converting CNY to USD and moving money out of China as a US citizen. Every row links an official source; unverified values are blank.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top"><div class="wrap"><h1>China → USD · Repatriation Research</h1><span class="tag">US-citizen perspective · verified {e(RULES_DOC['meta']['retrieved'])} · research, not advice</span></div></header>
<nav class="main" aria-label="Main"><div class="wrap">{nav}</div></nav>
<main>
{body}
<footer>
<p><strong>Verification standard:</strong> every table row links at least one official or provider-primary source fetched on 2026-11-08 (see <a href="sources.html">Sources</a>). Computed cells are deterministic arithmetic from cited published inputs at the IRS 2025 reference rate (7.129 CNY/USD, <a href="sources.html#S23">S23</a>) — they are fee floors, not all-in quotes. Blank cells = value not published by an official/primary source; see <a href="flagged.html">Flagged for review</a>. Provider terms describe that provider only. No funds moved, no returns filed. Parallel-session dashboards elsewhere in this repo are preserved unedited.</p>
</footer>
</main>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


def status_chip(s):
    if s == "rejected-unlawful":
        return '<span class="chip bad">Rejected · unlawful</span>'
    if s == "lawful-conditional":
        return '<span class="chip ok">Lawful · conditional</span>'
    return f'<span class="chip">{e(s)}</span>'


def audit_chip(s):
    return {"ok": '<span class="chip ok">OK</span>', "note": '<span class="chip">Note</span>',
            "needs review": '<span class="chip warn">Needs review</span>'}.get(s, e(s))


# ---------------- pages ----------------

def index_page(ladders):
    m1 = ladders["M01"]
    ex = {a: r for r in m1 for a in [r["amount_usd"]]}
    rows = ""
    for a in (10000, 50000, 100000, 200000, 400000):
        r = ex[a]
        rows += (f'<tr><td class="num">{usd(a)}</td><td class="num">{usd(r["published_fee_usd"])}</td>'
                 f'<td>{blank()}</td><td>M01 single SWIFT wire, HSBC Premier/Advance published tariff</td>'
                 f'<td>{src_links(r["sources"])}</td></tr>')
    body = f"""
<h2>Executive summary — getting money out of China with the least lawful cost</h2>
<div class="notice"><strong>The premise matters:</strong> neither the US nor China taxes the <em>act</em> of converting CNY to USD. What people call a “conversion penalty” is really up to five separate things: (1) PRC income tax on the money’s source, (2) US tax on worldwide income (with credits/exclusion), (3) the bank’s FX spread, (4) transfer fees, (5) reporting penalties if accounts were never declared. Only #3–#4 are costs of moving the money itself. {src_links(['S15','S16','S24','S13'])}</div>
<div class="kpi">
<div class="k"><b>{len(METHODS)}</b><span>methods catalogued ({sum(1 for m in METHODS if m['status']=='lawful-conditional')} lawful-conditional, {sum(1 for m in METHODS if m['status']=='rejected-unlawful')} rejected)</span></div>
<div class="k"><b>{len(SOURCES)}</b><span>official / provider-primary sources fetched this session</span></div>
<div class="k"><b>40</b><span>cost increments per method ($10k → $400k)</span></div>
<div class="k"><b>{len(FLAGS)}</b><span>published review flags (blank ≠ zero)</span></div>
</div>
<div class="grid c2">
<div class="card"><h3>Best first move for a stuck bank balance</h3>
<p>If the balance is <strong>documented, taxed China-source income</strong> (salary/services), SAFE’s 2026 guidance lets a foreign individual convert and remit it with ID + income/tax documents — <strong>no annual dollar cap is stated</strong> for that route. The famous $50,000/year quota is a separate facilitation channel, not the ceiling. {src_links(['S03','S05','S01'])}</p>
<p class="small">If the source income was never taxed, the tax must be resolved first — that is income tax under the IIT Law (3–45% progressive / 20% flat categories), not a conversion tax. {src_links(['S15'])}</p></div>
<div class="card"><h3>What it costs (published parts only)</h3>
<p>HSBC China’s published tariff: <strong>0.1% (min ¥100, max ¥500) + ¥120 cable</strong> per wire for Premier/Advance; <strong>free</strong> for Private Banking individuals; Global Transfer to your own overseas HSBC <strong>free</strong> for Premier/PB. The FX spread and correspondent fees are <strong>not published</strong> — left blank and flagged, never guessed. {src_links(['S29'])} {flag_link('F03')}</p></div>
<div class="card"><h3>US side: the real penalty risk is reporting</h3>
<p>FBAR required if all foreign accounts combined exceeded <strong>$10,000</strong> at any time; Form 8938 thresholds are higher. Penalties (2025-adjusted): up to <strong>$16,536</strong> non-willful per violation; willful up to <strong>$165,353</strong> or 50% of the balance. Non-willful catch-up: Streamlined Foreign Offshore Procedures (3 returns + 6 FBARs, penalties waived if compliant). {src_links(['S17','S18','S19','S27'])}</p></div>
<div class="card"><h3>Do not use</h3>
<p>Crypto bridges (illegal financial activity in China, 2026 notice), quota splitting, underground banks, fake contracts: fines up to <strong>30%</strong> of the amount, serious cases <strong>30–100%</strong>, plus confiscation and criminal liability. {src_links(['S14','S13','S06'])}</p></div>
</div>
<h3>Most important numbers first — M01 published-fee floor at key amounts</h3>
<div class="table-scroll" role="region" aria-label="Key cost examples" tabindex="0">
<table><thead><tr><th class="num">Amount</th><th class="num">Published bank fee (computed)</th><th class="num">FX spread + other costs</th><th>Basis</th><th>Sources</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="small">Computed = tariff arithmetic at the labeled reference rate; the all-in cost additionally includes the unpublished spread/fees (blank, {flag_link('F03')}). Full 40-row tables for every method: <a href="costs.html">Cost tables</a>.</p>
<h3>Start here</h3>
<p><a class="button" href="methods.html">All {len(METHODS)} methods, pros/cons & step-by-step</a>
<a class="button" href="costs.html">$10k→$400k cost tables</a>
<a class="button sec" href="taxes.html">Tax & reporting rules</a>
<a class="button sec" href="flagged.html">What’s unverified</a></p>
<h3>Downloads</h3>
<p><a href="exports/cost-ladders.csv" download>cost-ladders.csv</a> · <a href="exports/cost-ladders.json" download>cost-ladders.json</a> · <a href="data/sources.json" download>sources.json</a> · <a href="data/rules.json" download>rules.json</a> · <a href="data/methods.json" download>methods.json</a></p>
"""
    return page("index.html", "Overview", body, "index.html")


def methods_page():
    parts = ['<h2>Method catalogue — pros, cons and exact steps</h2>',
             '<p class="small">Lawful-conditional = permitted if you meet the cited conditions. Rejected = documented because the brief asks for as many ways as possible; these are <strong>not</strong> recommendations. Every claim row links its source.</p>']
    cats = []
    for m in METHODS:
        if m["category"] not in cats:
            cats.append(m["category"])
    for cat in cats:
        parts.append(f"<h3 id=\"cat-{e(cat).replace(' ', '-')}\">{e(cat)}</h3>")
        for m in METHODS:
            if m["category"] != cat:
                continue
            pros = "".join(f"<li>{e(p)}</li>" for p in m["pros"])
            cons = "".join(f"<li>{e(c)}</li>" for c in m["cons"])
            steps = "".join(f"<li>{e(s.split('. ', 1)[1] if s[:2].isdigit() else s)}</li>" for s in m["steps"])
            parts.append(f"""
<div class="method" id="{e(m['id'])}">
<h3>{e(m['id'])} · {e(m['name'])} {status_chip(m['status'])}</h3>
<p class="small"><strong>Who it fits:</strong> {e(m['who'])}</p>
<div class="cols"><div><strong>Pros</strong><ul>{pros}</ul></div><div><strong>Cons</strong><ul>{cons}</ul></div></div>
<details><summary>Step-by-step</summary><ol>{steps}</ol></details>
<p class="small"><strong>Cost model:</strong> {e(m['cost_model'].get('note', ''))} <a href="costs.html#{e(m['id'])}">40-row cost table →</a></p>
<p>{src_links(m['sources'])}</p>
</div>""")
    return page("methods.html", "Methods & steps", "\n".join(parts), "methods.html")


def costs_page(ladders):
    parts = ['<h2>Cost tables — $10,000 → $400,000 in $10,000 increments</h2>',
             f"""<div class="notice">Read this first: <strong>published fee</strong> columns are computed only from officially published tariffs/limits (cited per row) at the IRS 2025 reference rate 7.129 CNY/USD {src_links(['S23'])}. They are <strong>fee floors, not all-in costs</strong>. FX spread, correspondent charges and provider quotes are not published — those cells are blank and flagged {flag_link('F03')}. “Constraint” shows the lawful throughput limit (years/trips/transfers) computed from cited caps. Rejected methods show <strong>statutory fine exposure</strong>, not a price.</div>""",
             '<p><a class="button sec" href="exports/cost-ladders.csv" download>Download all tables (CSV)</a><a class="button sec" href="exports/cost-ladders.json" download>JSON</a></p>',
             '<p><label for="amount-filter"><strong>Show one amount across all methods:</strong></label> '
             '<select id="amount-filter"><option value="all">All 40 increments</option>'
             + "".join(f'<option value="{a}">${a:,}</option>' for a in AMOUNTS)
             + '</select> <span id="filter-note" class="small">Showing all 40 increments per method.</span></p>',
             '<p class="small">Jump to: ' + " · ".join(f'<a href="#{m["id"]}">{m["id"]}</a>' for m in METHODS) + "</p>"]
    for m in METHODS:
        rows = ladders[m["id"]]
        rejected = m["status"] == "rejected-unlawful"
        parts.append(f'<h3 id="{e(m["id"])}">{e(m["id"])} · {e(m["name"])} {status_chip(m["status"])}</h3>')
        parts.append(f'<p class="small">{e(m["cost_model"].get("note", ""))} <a href="methods.html#{e(m["id"])}">Steps & pros/cons →</a></p>')
        head = ('<tr><th class="num">Amount (USD)</th><th class="num">Standard fine ≤30%</th>'
                '<th class="num">Serious-case fine range (30–100%)</th><th>Constraint</th><th>Sources</th></tr>') if rejected else (
                '<tr><th class="num">Amount (USD)</th><th class="num">Published fee (USD)</th>'
                '<th class="num">Spread + other costs</th><th>Lawful throughput constraint</th><th>Sources</th></tr>')
        trs = []
        for r in rows:
            if rejected:
                trs.append(
                    f'<tr><td class="num">{usd(r["amount_usd"])}</td>'
                    f'<td class="num">{usd(r["fine_standard_max_usd"])}</td>'
                    f'<td class="num">{usd(r["fine_serious_min_usd"])} – {usd(r["fine_serious_max_usd"])}</td>'
                    f'<td>{e(r["constraint_detail"])}</td><td>{src_links(r["sources"])}</td></tr>')
            else:
                fee = usd(r["published_fee_usd"]) if r["published_fee_usd"] is not None else blank()
                trs.append(
                    f'<tr><td class="num">{usd(r["amount_usd"])}</td><td class="num">{fee}</td>'
                    f'<td class="num">{blank()}</td>'
                    f'<td><strong>{e(r["constraint"])}</strong><br><span class="small">{e(r["constraint_detail"])}</span></td>'
                    f'<td>{src_links(r["sources"])}</td></tr>')
        parts.append(f'<div class="table-scroll" role="region" aria-label="{e(m["id"])} cost table" tabindex="0"><table><thead>{head}</thead><tbody>{"".join(trs)}</tbody></table></div>')
    return page("costs.html", "Cost tables", "\n".join(parts), "costs.html")


def taxes_page():
    rows = [
        ("PRC tax on the source income", "Resident: comprehensive income 3–45% after ¥60,000 + deductions; non-resident wages: ¥5,000/month deduction. Interest/dividends/property transfer/incidental: flat 20% (property transfer on gain). Tax attaches when income arises — not on conversion.", ["S15"]),
        ("PRC residency trigger", "Domicile, or ≥183 days in the tax year → resident taxed on China + overseas income; otherwise China-source only. Emigration with hukou cancellation triggers a tax return.", ["S15"]),
        ("No conversion tax found", "The fetched SAFE/PBOC rules impose quotas, authenticity review and penalties for evasion — no tax on the FX purchase itself. Current international payments are not restricted in principle (Art. 5).", ["S01", "S06", "S13"]),
        ("US worldwide income", "US citizens are taxed on worldwide income regardless of where they live; benefits (FEIE/FTC) require filing.", ["S16"]),
        ("FEIE (2026)", "Up to $132,900 of foreign EARNED income per person if tax-home + bona-fide-residence or 330-day tests met; does not cover passive income; does not remove FBAR.", ["S21", "S22"]),
        ("Foreign Tax Credit", "Credit = lesser of PRC income tax paid or US tax × (foreign-source taxable income / total taxable income); Form 1116; carryback 1 / forward 10 years. Not an unlimited offset.", ["S20"]),
        ("US–China treaty", "Saving clause: the US may still tax its citizens. Source tax on dividends/interest/royalties capped at 10% for beneficial owners; Art. 22 credit relief per US law. No remittance exemption.", ["S25"]),
        ("Personal currency gain (US)", "Disposing of personal foreign currency: no gain recognized unless the gain exceeds $200 per transaction (26 USC 988(e)(2), 2024 ed.). Moving your own after-tax funds is not new income; business/investment currency positions follow different rules.", ["S24", "S16"]),
        ("FBAR", "Required if aggregate foreign accounts > $10,000 at any time in the calendar year; due Apr 15 (auto-ext Oct 15); e-file with FinCEN; keep records 5 years.", ["S17"]),
        ("FBAR penalties (assessed ≥2025-01-17)", "Non-willful: up to $16,536 per violation. Willful: up to $165,353 or 50% of the account balance (statutory alternative). Adjusted annually.", ["S19", "S18"]),
        ("Form 8938", "Unmarried living abroad: >$200,000 last day or >$300,000 any time (in US: $50k/$75k; MFJ abroad: $400k/$600k). Penalty up to $10,000 + $10,000/30 days after notice, max $60,000.", ["S18"]),
        ("Cash across the US border", "> $10,000 (person or family/group, one time) must be reported on FinCEN 105. It is reporting, not a tax; failure risks forfeiture and penalties.", ["S28"]),
        ("Non-willful catch-up", "Streamlined Foreign Offshore Procedures: 3 years of returns + 6 years of FBARs, tax + interest due; failure-to-file/pay, accuracy, information-return and FBAR penalties waived if compliant and certified non-willful; non-residency requirement applies.", ["S26", "S27"]),
        ("Foreign gifts/inheritance received", "Gifts/bequests from nonresident aliens/foreign estates > $100,000: Form 3520 reporting (not income tax on the gift itself).", ["S16"]),
    ]
    trs = "".join(
        f'<tr><th scope="row">{e(t)}</th><td>{e(d)}</td><td>{src_links(s)}</td></tr>'
        for t, d, s in rows)
    body = f"""
<h2>Tax & reporting — verified rules only</h2>
<div class="notice">Personal tax amounts cannot be computed without your facts (income mix, tax paid, filing history) — {flag_link('F01')}. This page states the rules; it does not compute your liability.</div>
<div class="table-scroll" role="region" aria-label="Tax and reporting rules" tabindex="0">
<table><thead><tr><th>Topic</th><th>Verified rule</th><th>Sources</th></tr></thead><tbody>{trs}</tbody></table></div>
<h3>How the layers stack (analysis)</h3>
<div class="card"><ol>
<li><strong>Source tax (PRC):</strong> owed when the income arose. If unpaid, resolving it is a prerequisite for the documented conversion route — not a penalty for converting. {src_links(['S15','S03'])}</li>
<li><strong>US residual tax:</strong> worldwide income, reduced by FEIE (earned only) and/or limited FTC. Often small or zero for already-taxed salary, but never assume — the FTC is ratio-limited. {src_links(['S16','S20','S21'])}</li>
<li><strong>FX spread:</strong> the bank’s real conversion margin; unpublished → blank everywhere on this site. {flag_link('F03')}</li>
<li><strong>Transfer fees:</strong> published tariff floors computed on <a href="costs.html">Cost tables</a>. {src_links(['S29'])}</li>
<li><strong>Reporting penalties:</strong> avoidable entirely by filing (FBAR/8938/105) and, for past non-willful gaps, the streamlined procedures. {src_links(['S17','S18','S28','S27'])}</li>
</ol></div>
"""
    return page("taxes.html", "Tax & reporting", body, "taxes.html")


def sources_page():
    trs = []
    for s in SOURCES.values():
        kind = s["kind"]
        chip = '<span class="chip ok">fetched</span>' if s["status"] == "fetched" else f'<span class="chip warn">{e(s["status"])}</span>'
        trs.append(
            f'<tr id="{e(s["id"])}"><th scope="row">{e(s["id"])}</th><td><a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(s["title"])}</a><br>'
            f'<span class="small">{e(s["publisher"])} · {e(kind)} · locator: {e(s["locator"])}</span></td>'
            f'<td>{chip}</td><td>{e(s["facts"])}</td></tr>')
    body = f"""
<h2>Source registry — {len(SOURCES)} sources, all fetched 2026-11-08</h2>
<p class="small">Regulator/statute sources are primary law. Provider sources (HSBC, Wise, Western Union) are primary <em>for that provider’s own terms only</em>. PRC English texts are reference translations; Chinese prevails. Failed candidates (e.g., a wrong CBP article number that returned an unrelated page, and a 404 IRS newsroom URL) were excluded and replaced with the working official pages below.</p>
<div class="table-scroll" role="region" aria-label="Source registry" tabindex="0">
<table><thead><tr><th>ID</th><th>Source / locator</th><th>Retrieval</th><th>What was verified in it</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>
"""
    return page("sources.html", "Sources", body, "sources.html")


def audit_page():
    trs = []
    for a in AUDIT:
        links = f'<a class="src" href="{e(a["repo"])}" target="_blank" rel="noopener noreferrer">repo file ↗</a> ' + src_links(a["sources"])
        trs.append(
            f'<tr id="{e(a["id"])}"><th scope="row">{e(a["id"])}</th><td>{e(a["file"])}<br><span class="small">{e(a["line"])}</span></td>'
            f'<td>{audit_chip(a["status"])}</td><td>{e(a["finding"])}</td><td>{links}</td></tr>')
    body = f"""
<h2>Repository audit — inherited content reviewed line by line</h2>
<p class="small">Read-only review of the parallel sessions’ deliverables on this branch’s base commit. Files owned by other sessions are flagged, never edited; correction requests go through <a href="https://github.com/sassnarep3-star/China2/blob/main/COORDINATION.md" target="_blank" rel="noopener noreferrer">COORDINATION.md</a>. All three prior validation suites were re-run green before this session’s work (A10).</p>
<div class="table-scroll" role="region" aria-label="Repository audit" tabindex="0">
<table><thead><tr><th>ID</th><th>File / line</th><th>Status</th><th>Finding</th><th>Evidence</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>
"""
    return page("audit.html", "Repo audit", body, "audit.html")


def flagged_page():
    trs = []
    for f in FLAGS:
        detail = e(f["detail"])
        # linkify any URLs present in the detail (e.g., repo links on F12)
        detail = re.sub(r'(https://[^\s,]+)', r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', detail)
        links = src_links(f["sources"]) if f["sources"] else '<span class="small">repo-internal; evidence links in detail</span>'
        trs.append(
            f'<tr id="{e(f["id"])}"><th scope="row">{e(f["id"])}</th><td>{e(f["title"])}</td>'
            f'<td><span class="chip warn">{e(f["severity"])}</span></td><td>{detail}</td><td>{links}</td></tr>')
    body = f"""
<h2>Flagged for review — {len(FLAGS)} items</h2>
<div class="notice">These items are published for your review and do not block the site. <strong>Blank cells anywhere on this site map to a flag below</strong> — a blank is never a zero. Unverified commercial values were left blank deliberately, per the project’s verification policy.</div>
<div class="table-scroll" role="region" aria-label="Flagged items" tabindex="0">
<table><thead><tr><th>ID</th><th>Item</th><th>Status</th><th>Detail</th><th>Sources</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>
"""
    return page("flagged.html", "Flagged for review", body, "flagged.html")


def write_exports(ladders):
    (ROOT / "exports").mkdir(exist_ok=True)
    flat = [r for m in METHODS for r in ladders[m["id"]]]
    (ROOT / "exports" / "cost-ladders.json").write_text(
        json.dumps({"meta": {"reference_rate_cny_per_usd": RATE, "rate_source": "S23",
                             "policy": "null = unverified/blank; computed values are published-input arithmetic, not quotes"},
                    "rows": flat}, indent=1, sort_keys=True) + "\n")
    buf = io.StringIO()
    cols = ["method", "amount_usd", "amount_cny_ref", "published_fee_usd", "published_fee_cny",
            "fine_standard_max_usd", "fine_serious_min_usd", "fine_serious_max_usd",
            "constraint", "constraint_detail", "sources"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in flat:
        r2 = dict(r)
        r2["sources"] = ";".join(r["sources"])
        for k in cols:
            if r2.get(k) is None:
                r2[k] = ""
        w.writerow(r2)
    (ROOT / "exports" / "cost-ladders.csv").write_text(buf.getvalue())


def main():
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "style.css").write_text(CSS.strip() + "\n")
    ladders = build_ladders()
    pages = {
        "index.html": index_page(ladders),
        "methods.html": methods_page(),
        "costs.html": costs_page(ladders),
        "taxes.html": taxes_page(),
        "sources.html": sources_page(),
        "audit.html": audit_page(),
        "flagged.html": flagged_page(),
    }
    for name, content in pages.items():
        (ROOT / name).write_text(content)
    write_exports(ladders)
    print(f"built {len(pages)} pages, {len(METHODS)} methods x {len(AMOUNTS)} increments = {len(METHODS)*len(AMOUNTS)} cost rows")


if __name__ == "__main__":
    main()
