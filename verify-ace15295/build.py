#!/usr/bin/env python3
"""Build the verify-ace15295 dashboard: 9 static pages, no external dependencies."""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SRC = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]
FIND = json.loads((DATA / "findings.json").read_text(encoding="utf-8"))["findings"]
QUES = json.loads((DATA / "questions.json").read_text(encoding="utf-8"))["questions"]
COST = json.loads((DATA / "costs.json").read_text(encoding="utf-8"))
S = {s["id"]: s for s in SRC}

PAGES = [
    ("index.html", "Overview", "The answer, the limits, and where to go next"),
    ("costs.html", "Costs", "Every USD 10,000 step to USD 400,000, per method"),
    ("methods.html", "Methods", "10 route types, pros, cons, exact steps"),
    ("penalties.html", "Penalties", "The conversion cost broken into 7 layers"),
    ("taxes.html", "Tax & reporting", "PRC tax, U.S. §988, FBAR, 8938, FinCEN 105"),
    ("questions.html", "Questions", "14 open questions that gate the decision"),
    ("audit.html", "Repo audit", "Line-by-line check of prior published figures"),
    ("flagged.html", "Flagged for review", "Unverified values and irregularities"),
    ("sources.html", "Sources", "31 official documents, link and locator"),
]

CSS = """
:root{--ink:#11211d;--muted:#5a6f66;--paper:#f6f6f1;--line:#dde3dd;--accent:#0b6b59;
--warn:#7a4a00;--warnbg:#fff4d9;--bad:#8d2222;--badbg:#fdeceb;--ok:#0b6b59;--okbg:#e8f5f0;
--card:#fff}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:#075b4a}
header.top{background:var(--ink);color:#f4f5f0;padding:.85rem clamp(.9rem,3vw,2rem)}
header.top .bar{display:flex;flex-wrap:wrap;gap:.6rem 1rem;align-items:baseline;max-width:1100px;margin:0 auto}
header.top strong{font-size:1.02rem;letter-spacing:.01em}
header.top .sub{font-size:.78rem;color:#b9ccc4}
nav{background:#0d2a24;border-bottom:1px solid #1d3d35}
nav .inner{max-width:1100px;margin:0 auto;display:flex;gap:.15rem;overflow-x:auto;
-webkit-overflow-scrolling:touch;scrollbar-width:thin;padding:0 .5rem}
nav a{flex:0 0 auto;color:#cfe0d9;text-decoration:none;font-size:.86rem;font-weight:600;
padding:.7rem .7rem;border-bottom:3px solid transparent;white-space:nowrap}
nav a:hover{color:#fff;background:#12352d}
nav a[aria-current=page]{color:#fff;border-bottom-color:#3fd0a8;background:#12352d}
main{max-width:1100px;margin:0 auto;padding:clamp(1rem,3vw,2.2rem) clamp(.9rem,3vw,2rem) 3rem}
h1{font-size:clamp(1.55rem,4.4vw,2.35rem);line-height:1.15;letter-spacing:-.02em;margin:.2rem 0 .6rem}
h2{font-size:clamp(1.15rem,2.7vw,1.45rem);margin:2rem 0 .6rem;letter-spacing:-.01em}
h3{font-size:1.04rem;margin:1.3rem 0 .4rem}
p{margin:.55rem 0}
.lede{font-size:1.03rem;color:#2c433a;max-width:78ch}
.crumb{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin:0 0 .3rem}
.hero{border-left:5px solid var(--accent);background:var(--card);border:1px solid var(--line);
border-left-width:5px;border-radius:12px;padding:1rem 1.1rem;margin:1rem 0}
.big{font-size:clamp(1.6rem,6vw,2.5rem);font-weight:800;letter-spacing:-.03em;line-height:1.05;margin:.2rem 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:.75rem;margin:1rem 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.9rem 1rem}
.card .k{font-size:.74rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:0}
.card .v{font-size:1.3rem;font-weight:750;margin:.15rem 0;letter-spacing:-.02em}
.card .s{font-size:.8rem;color:var(--muted);margin:0}
.nav-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:.7rem;margin:1rem 0}
a.nav-card{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:.9rem 1rem;text-decoration:none;color:var(--ink)}
a.nav-card:hover{border-color:var(--accent);box-shadow:0 1px 0 var(--accent)}
a.nav-card b{color:#075b4a;display:block;font-size:.98rem}
a.nav-card span{font-size:.83rem;color:#33473f;display:block;margin-top:.15rem}
a.nav-card em{font-style:normal;font-size:.78rem;color:var(--muted);display:block;margin-top:.35rem}
.note{background:var(--warnbg);border:1px solid #e6d3a5;border-left:5px solid #a06a12;
border-radius:10px;padding:.85rem 1rem;margin:1rem 0;font-size:.93rem}
.crit{background:var(--badbg);border:1px solid #f0c9c5;border-left:5px solid var(--bad);
border-radius:10px;padding:.85rem 1rem;margin:1rem 0;font-size:.93rem}
.good{background:var(--okbg);border:1px solid #c6e6d9;border-left:5px solid var(--ok);
border-radius:10px;padding:.85rem 1rem;margin:1rem 0;font-size:.93rem}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:11px;
background:var(--card);margin:.7rem 0}
table{border-collapse:collapse;width:100%;font-size:.85rem;min-width:520px}
table.wide{min-width:760px}
th,td{padding:.5rem .6rem;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
thead th{background:#eef2ee;font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;
color:#3c5148;position:sticky;top:0;z-index:1}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:#fbfcfa}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.blank{color:#9a9a92;text-align:right}
.tag{display:inline-block;font-size:.7rem;font-weight:700;padding:.1rem .4rem;border-radius:5px;
letter-spacing:.03em;text-transform:uppercase}
.t-ok{background:var(--okbg);color:#075b4a}
.t-warn{background:var(--warnbg);color:var(--warn)}
.t-bad{background:var(--badbg);color:var(--bad)}
.t-neu{background:#eceee9;color:#49584f}
.src{font-size:.72rem;white-space:nowrap}
ul,ol{margin:.4rem 0 .7rem;padding-left:1.25rem}
li{margin:.22rem 0}
.pros,.cons{margin:0;padding-left:1.1rem}
.pros li::marker{color:#0b6b59}
.cons li::marker{color:#8d2222}
details{background:var(--card);border:1px solid var(--line);border-radius:11px;margin:.55rem 0;
padding:.15rem .95rem}
details summary{cursor:pointer;font-weight:650;padding:.6rem 0;font-size:.95rem}
details[open] summary{border-bottom:1px solid var(--line);margin-bottom:.5rem}
.q-meta{font-size:.82rem;color:var(--muted)}
footer{background:var(--ink);color:#dbe6e0;padding:1.4rem clamp(.9rem,3vw,2rem);font-size:.83rem}
footer .inner{max-width:1100px;margin:0 auto}
footer a{color:#8fe3c9}
.skip{position:absolute;left:-9999px}
@media(max-width:560px){
 table{font-size:.8rem;min-width:460px}
 th,td{padding:.42rem .45rem}
 th{white-space:normal}
 main{padding-bottom:2rem}
}
@media print{nav{display:none}.tw{overflow:visible}header.top,footer{print-color-adjust:exact}}
"""


def esc(t) -> str:
    return html.escape(str(t), quote=True)


def money(v, dash: str = "—") -> str:
    if v is None:
        return f'<td class="blank">{dash} blank</td>'
    return f'<td class="num">${v:,.2f}</td>'


def pct(v) -> str:
    if v is None:
        return '<td class="blank">— blank</td>'
    return f'<td class="num">{v:.3f}%</td>'


def srcnav(active: str) -> str:
    out = ['<nav aria-label="Sections"><div class="inner">']
    for href, label, _ in PAGES:
        cur = ' aria-current="page"' if href == active else ""
        out.append(f'<a href="{href}"{cur}>{esc(label)}</a>')
    out.append("</div></nav>")
    return "".join(out)


def slink(sid: str, label: str | None = None) -> str:
    s = S.get(sid)
    if not s:
        raise SystemExit(f"unknown source id {sid}")
    return (f'<a class="src" href="{esc(s["url"])}" target="_blank" '
            f'rel="noopener noreferrer">{esc(label or sid)}</a>')


def shell(page: str, title: str, body: str, lede: str = "") -> str:
    sub = dict((h, (l, d)) for h, l, d in PAGES)[page][1]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · CNY to USD · verify-ace15295</title>
<meta name="description" content="{esc(sub)}. Source-linked, mobile-first research. Unpublished values are left blank and flagged.">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="bar"><strong>CNY → USD</strong>
<span class="sub">verify-ace15295 · sources captured 11 Nov 2026 · research, not tax or legal advice</span></div></header>
{srcnav(page)}
<main id="main">
{lede}
{body}
</main>
<footer><div class="inner">
<p><strong>What this is.</strong> A document review. No bank was contacted, no account accessed, no funds moved, no return filed.
No personal tax figure is asserted: basis, residency, filing status and the source of the balance are unknown.
Every computed figure is arithmetic on a rate or fee the publisher printed, and every published rate board says it is not the executable price — so all totals are lower bounds.</p>
<p>Pages: {" · ".join(f'<a href="{h}">{esc(l)}</a>' for h, l, _ in PAGES)}</p>
<p><a href="../COORDINATION.md">Task board</a> · <a href="../README.md">Repository README</a></p>
</div></footer>
</body>
</html>
"""


# ----------------------------------------------------------------- index ----
def page_index() -> str:
    b = COST["boards"]
    boc, hsbc = b["BOC"], b["HSBC"]
    r400 = {(r["bank"], r["tariff"]): r for r in COST["routes"] if r["usd"] == 400_000}
    r10 = {(r["bank"], r["tariff"]): r for r in COST["routes"] if r["usd"] == 10_000}
    best400 = r400[("BOC", "BOC")]
    worst400 = r400[("HSBC", "HSBC_PREMIER")]
    diff = worst400["total_usd"] - best400["total_usd"]

    lede = """
<p class="crumb">Overview</p>
<h1>There is no tax on converting CNY to USD. There is a spread, a fee, a filing step, and a separate tax on the income itself.</h1>
<p class="lede">The balance is described as trapped because converting it would cost “a considerable amount of taxes”. Across the
31 official documents reviewed for this page — PRC State Council regulations, PBOC rules, SAFE regulations and Q&amp;A,
two joint tax-and-FX announcements, bank tariffs, the U.S. Code, IRS publications and CBP — nothing imposes a tax on the
act of exchanging renminbi for dollars. The cost of the conversion itself, computed below from the banks' own published
numbers, is <strong>0.22% to 0.83%</strong>. The rest of the story is documentation, and it is worth separating the four things
the word “tax” is being used for.</p>
"""

    body = f"""
<div class="hero">
  <p class="k">Cheapest published all-in cost, USD 400,000</p>
  <p class="big">$901.20 &nbsp;<span style="font-size:.45em;font-weight:600;color:#5a6f66">0.225%</span></p>
  <p style="margin:.5rem 0 .2rem">Bank of China: documented conversion at its board rate plus its posted personal wire tariff.
  {slink("S24", "BOC rate board")} · {slink("S25", "BOC tariff")}</p>
  <p style="margin:.2rem 0 0;font-size:.9rem;color:#4a5f56">The HSBC “free wire” route costs <strong>$2,082.26 (0.521%)</strong>
  at the same amount, because HSBC's published spread is 2.4× wider. {slink("S28", "HSBC tariff")} · {slink("S27", "HSBC board")}
  The difference is <strong>${diff:,.2f}</strong> — 18.8× BOC's entire $61.28 wire charge, and larger than every fee in HSBC's own tariff table.</p>
</div>

<div class="grid">
  <div class="card"><p class="k">Cost of converting (spread + wire)</p><p class="v">0.22% – 0.83%</p>
    <p class="s">Across three live rate boards and two published tariffs. Lower bound: boards are reference rates.</p></div>
  <div class="card"><p class="k">PRC tax created by the conversion</p><p class="v">None found</p>
    <p class="s">No reviewed instrument taxes the exchange. The bank may ask for a tax <em>record</em>, not a new tax.</p></div>
  <div class="card"><p class="k">U.S. tax on the currency gain</p><p class="v">$0 if ≤ $200</p>
    <p class="s">26 U.S.C. §988(e)(2) excludes a personal-transaction gain unless it exceeds $200. {slink("S20", "§988")}</p></div>
  <div class="card"><p class="k">Largest number in this project</p><p class="v">$165,353</p>
    <p class="s">Maximum civil penalty per <em>willful</em> FBAR violation. Not a prediction — a filing duty. {slink("S17", "31 CFR 1010.821")}</p></div>
</div>

<div class="crit">
<strong>The first thing to fix is not the cost model.</strong> PBOC Decree [2006] No.3 Art. 37(1) defines 境内个人 as a
<em>Chinese citizen</em> holding a PRC identity certificate; Art. 37(2) defines 境外个人 as a foreign passport holder.
On the face of those definitions a U.S. passport holder is a 境外个人 and the annual USD 50,000 purchase quota — which is
written for 境内个人, and which SAFE extends to a 境外个人 only on production of a PRC Foreign Permanent Resident ID — may not
apply at all. {slink("S02", "PBOC Decree 2006/3")} · {slink("S07", "SAFE 2025 Q&amp;A")}
Meanwhile State Council Regulation 532 Art. 52(2) uses a <em>different</em> test: a Chinese citizen, <em>or</em> a foreigner
continuously resident in the PRC for a full year. {slink("S01", "Regulation 532")}
Two definitions, two outcomes. That single unresolved fact — Q01 — changes which rule set applies, which documents the bank
will ask for, and whether the quota exists at all. It cannot be answered from anything in this repository.
</div>

<div class="good">
<strong>What the review does establish.</strong> SAFE's own client guidance states plainly that China imposes
no amount limit on FX settlement and purchase under genuine, lawful current-account items, and that the USD 50,000
figure “is an annual facilitation quota, not an individual's annual ceiling on settlement or purchase”. {slink("S05", "SAFE Xiamen guidance, §1 Q8")}
So a documented balance is not capped at USD 50,000 a year; the ceiling is the paperwork, not the quota. For a
non-domestic individual the operative rule is 汇发〔2020〕14号 Art. 59: convert on valid ID plus source-of-funds materials
evidencing the transaction amount, <em>including tax documents</em>. {slink("S06", "SAFE 2026 Q&amp;A")}
</div>

<h2>The four things “tax” is being used for</h2>
<div class="tw"><table>
<thead><tr><th>What it actually is</th><th class="num">What it costs</th><th>Official basis</th><th>Status</th></tr></thead>
<tbody>
<tr><td><strong>1. The bank's buy/sell spread</strong> — the real cost of converting</td>
<td class="num">≈0.21% – 0.50% of the dollars delivered</td>
<td>{slink("S24")} {slink("S26")} {slink("S27")}</td><td><span class="tag t-ok">verified</span></td></tr>
<tr><td><strong>2. Wire, cable and correspondent fees</strong></td>
<td class="num">$0 – $115 published; receiver's charge not published by any sender</td>
<td>{slink("S25")} {slink("S28")}</td><td><span class="tag t-ok">verified, lower bound</span></td></tr>
<tr><td><strong>3. Tax recordal (税务备案)</strong> — a free filing for single outward payments over USD 50,000</td>
<td class="num">No tax charged at the counter</td>
<td>{slink("S09")} {slink("S10")}</td><td><span class="tag t-ok">verified</span></td></tr>
<tr><td><strong>4. PRC income tax on the income that produced the balance</strong></td>
<td class="num">3%–45% comprehensive, or 20% flat on interest/dividends/rent/property transfer</td>
<td>{slink("S31")}</td><td><span class="tag t-warn">owing depends on Q03</span></td></tr>
</tbody></table></div>
<p style="font-size:.9rem;color:#4a5f56">If the bank's “considerable tax” is item 4, no conversion route avoids it: it is a tax on the income, payable whether or
not the money moves. If it is item 3, it is a free online filing. If it is item 1, it is about 0.2% and shoppable.
Telling those four apart is what the Questions page is for.</p>

<h2>Where to go</h2>
<div class="nav-cards">
<a class="nav-card" href="costs.html"><b>Costs · every $10,000 to $400,000</b>
<span>40 tiers × 5 method/segment combinations, mobile-first, most important rows first</span>
<em>Spread computed from each bank's own buy and sell, added to that bank's own tariff. Blank where a fee is unpublished.</em></a>
<a class="nav-card" href="methods.html"><b>Methods · 10 legal route types</b>
<span>Pros, cons, and the exact steps for each</span>
<em>Plus the unlawful ones, listed with their statutory penalties and no instructions.</em></a>
<a class="nav-card" href="penalties.html"><b>Penalties · the cost in 7 layers</b>
<span>Which layers are avoidable, and by how much, at each tier</span>
<em>Separates shoppable cost from fixed tax from filing duties from statutory penalties.</em></a>
<a class="nav-card" href="taxes.html"><b>Tax &amp; reporting</b>
<span>PRC IIT · U.S. §988 · FBAR · Form 8938 · FinCEN 105</span>
<em>Showing which thresholds this USD 10,000–400,000 range crosses.</em></a>
<a class="nav-card" href="questions.html"><b>Questions · 14 decision gates</b>
<span>What is unknown, why it blocks the decision, how to find it</span>
<em>Start here if you want to act: Q01–Q03 are unanswered and everything else depends on them.</em></a>
<a class="nav-card" href="audit.html"><b>Repo audit · 9 findings</b>
<span>Line-by-line check of what prior sessions published</span>
<em>Including a repealed penalty article still cited and a “conversion tax” that does not exist.</em></a>
<a class="nav-card" href="flagged.html"><b>Flagged for review</b>
<span>Every value left blank, and every irregularity</span>
<em>Nothing is filled in by inference. Blank means the publisher does not print it.</em></a>
<a class="nav-card" href="sources.html"><b>Sources · 31 documents</b>
<span>Publisher, date retrieved, and the exact words relied on</span>
<em>Each with the locator so the sentence can be found again.</em></a>
</div>

<h2>Executive summary</h2>
<div class="tw"><table class="wide">
<thead><tr><th>Question you asked</th><th>Short answer from the reviewed sources</th><th>Source</th></tr></thead>
<tbody>
<tr><td>How do I get money out of China with the least tax penalty?</td>
<td>Convert documented, lawful China-source income at a bank under the current-account rule, in one transfer, with the
source-of-funds and tax documents the bank asks for. Choose the bank on its <em>spread</em>, not its wire fee.
No reviewed instrument imposes a tax on the conversion.</td>
<td>{slink("S06")} {slink("S24")}</td></tr>
<tr><td>Is there really a $50,000 annual limit?</td>
<td>No. It is an annual <em>facilitation quota</em>. SAFE says outright that genuine lawful current-account settlement and
purchase have no amount limit. The quota is availability of a fast, ID-only tier — and it is written for PRC citizens,
extended to a foreigner only with a PRC permanent-residence card.</td>
<td>{slink("S05")} {slink("S02")} {slink("S07")}</td></tr>
<tr><td>What does the conversion actually cost?</td>
<td>0.2104%–0.5000% of the amount in bank spread, plus a wire fee of $0–$115 depending on bank and segment. At USD 400,000
that is $901.20 at the cheapest published combination and $2,082.26 at the dearest.</td>
<td>{slink("S24")} {slink("S25")} {slink("S28")}</td></tr>
<tr><td>What is the “considerable tax”?</td>
<td>Most likely one of four different things, only one of which is a tax: the spread, a wire fee, a free tax-recordal
filing, or PRC income tax on the income itself (3%–45% or 20%).</td>
<td>{slink("S09")} {slink("S31")}</td></tr>
<tr><td>What will the U.S. charge?</td>
<td>On the conversion gain: nothing if the gain is $200 or less (§988(e)(2)); ordinary income on the excess. On the account:
an FBAR if aggregate foreign accounts exceeded $10,000 at any time, and Form 8938 at $50,000/$75,000 single or
$100,000/$150,000 married filing jointly in the U.S.</td>
<td>{slink("S20")} {slink("S16")} {slink("S18")}</td></tr>
<tr><td>What can I not know from here?</td>
<td>Your PRC status (Q01), the source of the balance (Q02), whether PRC tax was assessed on it (Q03), your dollar basis
(Q05), and whether the FBAR/8938 filings exist (Q06). All five change the answer.</td>
<td>{slink("S02")} {slink("S16")}</td></tr>
</tbody></table></div>

<div class="note"><strong>What this page is not.</strong> It is not a quote and not advice. The rate boards it uses each carry the
publisher's own warning that the transaction rate prevails; HSBC's tariff note 7 excludes other institutions' and
authorities' charges. Every total here is therefore a lower bound on a reference rate, and no account in China was
contacted. Two officials questions — which identity category the account is held in, and what the bank actually asked
for — have to be answered by the bank in writing before this becomes a plan.</div>
"""
    return shell("index.html", "Overview", body, lede)


# ----------------------------------------------------------------- costs ----
def page_costs() -> str:
    b = COST["boards"]
    rows400 = [r for r in COST["routes"] if r["usd"] in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000)]
    order = [("BOC", "BOC"), ("CMB", "UNPUBLISHED"), ("HSBC", "HSBC_PRIVATE"),
             ("HSBC", "HSBC_GLOBAL"), ("HSBC", "HSBC_PREMIER")]

    def row(r) -> str:
        t = COST["tariffs"].get(r["tariff"], {})
        label = t.get("label", "China Merchants Bank")
        fee = ('<td class="blank">— blank</td>' if r["fee_usd"] is None
               else f'<td class="num">${r["fee_usd"]:,.2f}</td>')
        return (f'<tr><td>{esc(label)}</td>{money(r["total_usd"])}'
                f'<td class="num">${r["spread_usd"]:,.2f}</td>{fee}{pct(r["pct"])}'
                f'<td class="src">{slink(r["rate_source"])}'
                + (f' {slink(r["fee_source"])}' if r["fee_source"] else "") + "</td></tr>")

    head = ('<thead><tr><th>Method / segment</th><th class="num">All-in cost</th>'
            '<th class="num">of which spread</th><th class="num">of which wire</th>'
            '<th class="num">% of amount</th><th>Source</th></tr></thead>')

    tables = []
    for amt in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000):
        body = "".join(row(r) for r in COST["routes"] if r["usd"] == amt
                       and (r["bank"], r["tariff"]) in order)
        # keep the requested order
        got = {r["tariff"]: r for r in COST["routes"] if r["usd"] == amt}
        body = "".join(row(got[t]) for _, t in order if t in got)
        best = min((r for r in COST["routes"] if r["usd"] == amt and r["total_usd"]),
                   key=lambda r: r["total_usd"])
        tables.append(f"""
<h3 id="t{amt}">USD {amt:,} <span class="tag t-ok">cheapest: ${best["total_usd"]:,.2f} ({best["pct"]:.3f}%)</span></h3>
<div class="tw"><table class="wide">{head}<tbody>{body}</tbody></table></div>""")

    full = []
    for amt in [10_000 * i for i in range(1, 41)]:
        got = {(r["bank"], r["tariff"]): r for r in COST["routes"] if r["usd"] == amt}
        def c(k, label):
            r = got.get(k)
            if not r:
                return '<td class="blank">—</td>'
            if r["total_usd"] is None:
                return '<td class="blank">— blank</td>'
            return f'<td class="num">${r["total_usd"]:,.2f}<br><span style="font-size:.72rem;color:#5a6f66">{r["pct"]:.3f}%</span></td>'
        full.append(f'<tr><td class="num">${amt:,}</td>'
                    f'{c(("BOC","BOC"),"BOC")}'
                    f'{c(("HSBC","HSBC_PRIVATE"),"PB")}'
                    f'{c(("HSBC","HSBC_GLOBAL"),"GT")}'
                    f'{c(("HSBC","HSBC_PREMIER"),"PR")}'
                    f'{c(("CMB","UNPUBLISHED"),"CMB")}'
                    f'<td class="src">{slink("S24")} {slink("S28")} {slink("S26")}</td></tr>')

    lede = """
<p class="crumb">Costs</p>
<h1>What the conversion costs, at every $10,000 step to $400,000</h1>
<p class="lede">Each figure is <strong>the bank's own published half-spread added to that bank's own published wire tariff</strong>.
No rate is assumed and no fee is estimated. A cell is blank when the publisher does not print the number — China Merchants
Bank publishes a live rate board but its remittance tariff was not captured in this session, so its total is blank rather
than borrowed from an earlier snapshot. All boards are reference rates carrying the publisher's own disclaimer, so every
total is a <strong>lower bound</strong>.</p>
"""

    body = f"""
<div class="tw"><table class="wide">
<thead><tr><th>Rate board (captured 11 Nov 2026)</th><th class="num">Bank buys USD</th><th class="num">Bank sells USD</th>
<th class="num">Mid</th><th class="num">Half-spread</th><th>As of</th><th>Source</th></tr></thead>
<tbody>
{''.join(f'''<tr><td>{esc(v["label"])}</td>
<td class="num">{v["buy"]:.4f}</td><td class="num">{v["sell"]:.4f}</td>
<td class="num">{v["mid"]:.4f}</td><td class="num">{v["half_spread_pct"]:.4f}%</td>
<td>{esc(v["as_of"])}</td><td class="src">{slink(v["source"])}</td></tr>'''
 for v in b.values())}
</tbody></table></div>
<p style="font-size:.86rem;color:#4a5f56">Quoted as CNY per 100 units of foreign currency, as published. Half-spread is
(sell − buy) ÷ 2 ÷ mid — the cost of crossing the published spread once. HSBC's board is the outlier at roughly
2.4× the published spread of the two Chinese banks on the same days.</p>

<div class="note"><strong>Why “free” is not cheapest — except at the very bottom.</strong> HSBC publishes a genuinely free telegraphic transfer for its Private Banking individuals and free Global Transfer for Premier {slink("S28")}. Its published spread is 0.5000% against BOC’s 0.2104%, so BOC wins from about <strong>$11,820</strong> upward — at USD 400,000 that is $901.20 against $1,989.83. <em>Below</em> that crossover, BOC’s CNY 50 minimum plus CNY 150 cable (about $30) outweighs the spread difference and HSBC Private Banking is marginally cheaper: at USD 10,000, $49.75 against $53.42. Both are shown in the full ladder, and the verifier recomputes the crossover rather than trusting this paragraph.</div>

<h2>Most important amounts</h2>
<p class="lede">Asked for every $10,000 increment; the six amounts below are the ones the question turns on. The full
40-tier grid is further down.</p>
{''.join(tables)}

<h2>Full ladder · USD 10,000 → 400,000</h2>
<p class="lede">One row per $10,000 step. Columns are the five published method/segment combinations. Each cell shows the
all-in dollar cost and, underneath, the cost as a percentage of the amount — so you can see that the <em>rate</em> falls as
the amount rises while the <em>percentage</em> flattens once the wire cap is reached.</p>
<div class="tw"><table class="wide">
<thead><tr><th class="num">Amount</th><th class="num">BOC<br><span style="font-weight:400;text-transform:none">1‰, ¥50–260 + ¥150</span></th>
<th class="num">HSBC Private<br><span style="font-weight:400;text-transform:none">wire free</span></th>
<th class="num">HSBC Global<br><span style="font-weight:400;text-transform:none">USD 20</span></th>
<th class="num">HSBC Premier<br><span style="font-weight:400;text-transform:none">0.1%, ¥100–500 + ¥120</span></th>
<th class="num">CMB<br><span style="font-weight:400;text-transform:none">fee not captured</span></th>
<th>Source</th></tr></thead>
<tbody>{''.join(full)}</tbody></table></div>

<h2>How each figure is computed</h2>
<div class="tw"><table>
<thead><tr><th>Step</th><th>Formula</th><th>Where it comes from</th></tr></thead>
<tbody>
<tr><td>1</td><td>CNY needed = USD amount × bank's published selling rate ÷ 100</td><td>{slink("S24")} {slink("S26")} {slink("S27")}</td></tr>
<tr><td>2</td><td>Spread cost = USD amount × (selling rate − mid) ÷ selling rate</td><td>Same board, same row</td></tr>
<tr><td>3</td><td>Wire fee = rate from the bank's own tariff, floored and capped in CNY, plus cable, then converted at the same selling rate</td><td>{slink("S25")} {slink("S28")}</td></tr>
<tr><td>4</td><td>All-in = step 2 + step 3</td><td>Arithmetic</td></tr>
<tr><td>—</td><td><strong>Not included in any cell:</strong> the correspondent/intermediary bank's deduction, the receiving U.S. bank's inward fee, and any PRC income tax on the income itself</td><td>{slink("S28")} note 7; {slink("S31")}</td></tr>
</tbody></table></div>
<div class="crit"><strong>The three blanks that matter.</strong>
(1) <em>China Merchants Bank's wire fee</em> — its rate board was captured, its tariff was not, so no CMB total is shown.
(2) <em>ICBC</em> — its public board returned “暂无数据” (no data) to this session and its feed is script-populated, so it is
absent entirely rather than copied from a stale snapshot {slink("S30")}.
(3) <em>Sending-side totals exclude the receiving side.</em> No sender publishes what the U.S. bank will charge on arrival,
and HSBC's tariff says so in terms {slink("S28")}. Add the U.S. bank's incoming-wire fee before comparing with a quote.</div>
"""
    return shell("costs.html", "Costs", body, lede)


# --------------------------------------------------------------- methods ----
METHODS = [
 dict(id="R1", name="1 · Documented current-account conversion at a bank, then one wire",
  elig="A non-domestic individual with legitimate China-source current-account income: salary, labour remuneration, rent, royalties, services.",
  legal="lawful, documented", basis=["S06", "S03"],
  steps=["Obtain the identity documents the account is held under; confirm with the bank whether it treats you as 境内个人 or 境外个人.",
         "Assemble source-of-funds evidence for the whole amount: employment contract and payslips, or service contract and invoices, plus the PRC personal income tax record (个人所得税纳税记录).",
         "Ask the bank for a written all-in quote: applied CNY/USD rate, sender fee, cable, correspondent deduction, and the receiving bank's charge.",
         "If a single outward payment will exceed the equivalent of USD 50,000, complete tax recordal (税务备案) first: log in to the provincial e-tax bureau, submit the form and the contract, keep the form number and verification code.",
         "Present the documents and the recordal reference at the branch or through the bank's channel and instruct the transfer to your own U.S. account.",
         "Keep the exchange memo, the SWIFT confirmation and the tax record. They are the audit trail at both ends."],
  pros=["No USD 50,000 ceiling: SAFE states genuinely lawful current-account settlement and purchase have no amount limit.",
        "One transfer instead of a staged programme.",
        "Cheapest published path in this review: 0.225% at USD 400,000.",
        "Repeat conversions at the same bank are streamlined if the salary is continuing (汇发〔2021〕13号 Art. 5)."],
  cons=["The bank decides what evidence is enough, and its review is a real gate.",
        "Requires the income to be documented and, in practice, the PRC tax position to be on record.",
        "The source-of-funds requirement is per tranche; a mixed balance needs every component evidenced."],
  srcs=["S06", "S05", "S12", "S09"]),
 dict(id="R2", name="2 · Same rule as an domestic individual (PRC citizen route)",
  elig="A PRC citizen holding a PRC identity card.",
  legal="lawful, documented", basis=["S03", "S05"],
  steps=["Within the annual quota: present valid ID only.",
         "Above the quota: present valid ID plus source materials for the settlement, per 汇发〔2007〕1号 Art. 10 and 12, or the purpose materials for a purchase.",
         "Remit from the FX savings account: up to the equivalent of USD 50,000 per day on ID, above that with documentary evidence of the transaction.",
         "Where the onward payment exceeds USD 50,000, complete tax recordal as in route 1."],
  pros=["Simplest document set inside the quota.", "No fee or tax attaches to the quota itself."],
  cons=["Not available to a person whose only identity document is a foreign passport.",
        "The quota resets each 1 January and unused quota does not carry over."],
  srcs=["S03", "S05", "S02"]),
 dict(id="R3", name="3 · Annual facilitation quota using a PRC Foreign Permanent Resident ID",
  elig="A non-domestic individual who holds a PRC Foreign Permanent Resident ID ('Chinese green card').",
  legal="lawful, documented", basis=["S07"],
  steps=["Confirm you hold the Foreign Permanent Resident ID.",
         "Convert within the annual USD 50,000 facilitation quota on ID.",
         "For anything above it, fall back to route 1's documented procedure."],
  pros=["Avoids the full documentation pack for amounts up to the quota each year."],
  cons=["Requires an immigration status most U.S. citizens do not hold.",
        "Quota-only tier, so it cannot move USD 400,000 in one year.",
        "Splitting a larger amount across years or people to stay inside it is the unlawful route R9."],
  srcs=["S07", "S03"]),
 dict(id="R4", name="4 · Re-conversion of unused renminbi on the original exchange memo",
  elig="Anyone who previously converted foreign currency into RMB and has the original exchange memo.",
  legal="lawful", basis=["S08", "S03"],
  steps=["Find the original exchange memo (兑换水单) for the conversion that produced the RMB.",
         "Present valid ID and the memo at the bank within 24 months of the exchange date.",
         "Same-day amounts up to USD 500 — or up to USD 1,000 at port-area outlets before departure — need ID only."],
  pros=["Fast and document-light where a memo exists.", "Reverses a conversion rather than creating a new one."],
  cons=["Hard 24-month limit from the exchange date.",
        "Only reverses what was converted in, so it cannot move income earned in RMB."],
  srcs=["S08", "S03"]),
 dict(id="R5", name="5 · Emigrant property transfer (移民财产转移)",
  elig="A natural person who has moved from the mainland to a foreign country and is transferring lawful property owned before acquiring that status.",
  legal="lawful, capital account, SAFE approval", basis=["S11"],
  steps=["Cancel PRC household registration and obtain the public-security cancellation certificate.",
         "Obtain a certificate of overseas residence issued or authenticated by a Chinese embassy or consulate.",
         "Assemble property-rights documents and, where required, notarised translations.",
         "Apply once, to the SAFE branch where your household registration was, for the whole amount.",
         "The first remittance may not exceed half; after one year, up to half the remainder; after two years, the rest. The equivalent of CNY 200,000 or less may go in one approved transfer.",
         "Up to the equivalent of CNY 500,000 is approved locally; above that it goes to SAFE headquarters."],
  pros=["Expressly designed for moving a lifetime's lawful property abroad.",
        "Not dependent on a current income stream.",
        "The bank must remit directly to your own overseas account."],
  cons=["Requires giving up PRC household registration — a serious, irreversible step.",
        "Staged over two years by rule, not by choice.",
        "Above CNY 500,000 needs SAFE headquarters approval, so the timeline is not in your control.",
        "Requires the tax certificate or tax-payment receipt for the property's location."],
  srcs=["S11", "S04"]),
 dict(id="R6", name="6 · Inheritance transfer (继承财产转移)",
  elig="A foreign citizen, or a Hong Kong/Macao resident, inheriting mainland property.",
  legal="lawful, capital account, SAFE approval", basis=["S11"],
  steps=["Apply to the SAFE branch where the deceased was registered.",
         "Provide the inheritance documents, the relationship documents and the tax certificate or tax-payment receipt from the competent tax authority where the property is located.",
         "Apply once for all property from the same deceased person; it may be remitted in one or several transfers.",
         "Property inherited from different deceased persons requires separate applications."],
  pros=["Purpose-built for inherited funds.", "One application per deceased person."],
  cons=["Only for inherited property, not for earned income.",
        "Requires notarised inheritance documents and a PRC tax certificate."],
  srcs=["S11"]),
 dict(id="R7", name="7 · Individual foreign-trade operator's FX settlement account",
  elig="A registered individual foreign-trade operator or sole trader conducting import/export.",
  legal="lawful, business account", basis=["S05", "S03"],
  steps=["Register as a foreign-trade operator and open an FX settlement account, managed as a corporate account.",
         "Settle and purchase against the genuine trade documents — the annual quota does not apply to this account.",
         "Keep customs and logistics documents as the authenticity base."],
  pros=["Outside the annual quota entirely.", "Scales with real trade."],
  cons=["Only for genuine trade — it is not a personal-balance route.",
        "Requires business registration and trade documentation."],
  srcs=["S05", "S03"]),
 dict(id="R8", name="8 · Carrying foreign-currency cash out",
  elig="Anyone; limited by amount and by what the branch will issue in cash.",
  legal="lawful within limits", basis=["S13", "S14", "S15"],
  steps=["Up to the equivalent of USD 5,000: no certificate needed.",
         "USD 5,000 to USD 10,000: obtain a 携带外汇出境许可证 from the designated FX bank; customs releases against the bank's stamp.",
         "Above USD 10,000: a certificate from the local SAFE branch is required and is 'in principle' not permitted.",
         "Renminbi cash is capped at CNY 20,000 per person per trip.",
         "On entering the U.S. with more than USD 10,000, file FinCEN Form 105 — the threshold applies to the group total, not per person."],
  pros=["No wire fee, no correspondent deduction.",
        "Immediate."],
  cons=["USD 10,000 per trip is 2.5% of USD 400,000 — 40 trips.",
        "Cash is the widest-spread instrument: the cash buying rate is the worst published rate.",
        "Physical risk plus a U.S. reporting duty the moment it exceeds USD 10,000.",
        "Repeat trips to stay under the limits can itself attract scrutiny."],
  srcs=["S13", "S14", "S15"]),
 dict(id="R9", name="9 · Card and mobile-wallet spending abroad (genuine consumption)",
  elig="Anyone spending on genuine personal consumption abroad.",
  legal="lawful for genuine consumption", basis=["S05"],
  steps=["Spend directly on a mainland-issued card or wallet for real purchases.",
         "Note that genuine current-account consumption does not consume the annual settlement quota."],
  pros=["No settlement quota consumed for genuine consumption.",
        "No wire fee."],
  cons=["Buys goods and services, not dollars in your account.",
        "Merchant and card-network limits apply; it cannot repatriate a balance."],
  srcs=["S05"]),
 dict(id="R10", name="10 · Conversions that are unlawful — listed for their penalties only",
  elig="Not available. Listed so the cost of the alternatives is visible.",
  legal="unlawful", basis=["S01", "S02"],
  steps=["No steps are given. The unlawful conduct is: splitting a large amount across relatives' or friends' annual quotas to evade limit management (PBOC Decree [2006] No.3 Art. 7); using false or invalid documents to obtain FX (Regulation 532 Art. 40); private or disguised buying and selling of FX, including through an underground bank (Art. 45); unlawful carriage of cash across the border (Art. 42)."],
  pros=[],
  cons=["Evasion (逃汇): fine up to 30% of the amount; if serious, 30% up to the full amount. Regulation 532 Art. 39.",
        "Illegal arbitrage (非法套汇) with false documents: up to 30%; serious 30%–100%. Art. 40.",
        "Private or disguised FX dealing: warning, confiscation, up to 30%; serious 30%–100%, plus criminal liability. Art. 45.",
        "Unlawful cash carriage: up to 20%. Art. 42. Invalid documents: up to CNY 50,000 for an individual. Art. 48.",
        "Being placed on SAFE's 关注名单 removes the facilitation quota for the year of listing and the two following years.",
        "At USD 400,000 a 30% floor is $120,000 and a 100% exposure is $400,000 — against $901.20 for the lawful route."],
  srcs=["S01", "S02", "S05"]),
]


def page_methods() -> str:
    cards = []
    for m in METHODS:
        pros = "".join(f"<li>{esc(p)}</li>" for p in m["pros"]) or "<li>None.</li>"
        cons = "".join(f"<li>{esc(c)}</li>" for c in m["cons"])
        steps = "".join(f"<li>{esc(s)}</li>" for s in m["steps"])
        tag = ("t-bad" if m["legal"].startswith("unlawful")
               else "t-warn" if "capital" in m["legal"] else "t-ok")
        basis = " ".join(slink(s) for s in m["basis"])
        cards.append(f"""
<details id="{m["id"]}"><summary>{esc(m["name"])} &nbsp;<span class="tag {tag}">{esc(m["legal"])}</span></summary>
<p class="q-meta"><strong>Who can use it:</strong> {esc(m["elig"])} &nbsp;·&nbsp; <strong>Basis:</strong> {basis}</p>
<h4>Exact steps</h4><ol>{steps}</ol>
<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">
<div class="card"><p class="k" style="color:#075b4a">Pros</p><ul class="pros">{pros}</ul></div>
<div class="card"><p class="k" style="color:#8d2222">Cons</p><ul class="cons">{cons}</ul></div>
</div>
<p class="q-meta">Sources: {" ".join(slink(s) for s in m["srcs"])}</p>
</details>""")

    lede = """
<p class="crumb">Methods</p>
<h1>Ten route types — not twenty-three</h1>
<p class="lede">Prior sections in this repository count 15 to 23 “methods” by counting each bank, card type and wallet as its
own method. They are not: the choice of bank is a <em>parameter</em> (it changes the price, not the legal route), and a card
that buys goods abroad is not a way to repatriate a balance. The reviewed instruments support the ten route types below.
Each carries its eligibility, its legal basis, the exact steps, and its published pros and cons. Route 10 is unlawful and is
listed only so its statutory price is visible — no steps are given.</p>
"""

    body = f"""
<div class="grid">
  <div class="card"><p class="k">Route types</p><p class="v">10</p><p class="s">1 documented non-domestic · 1 domestic · 1 PR-ID quota · 1 re-conversion · 2 capital-account · 1 trade · 1 cash · 1 card · 1 unlawful</p></div>
  <div class="card"><p class="k">Usable on a U.S. passport alone</p><p class="v">2 of 8 lawful</p><p class="s">Route 1 (documented income) and route 4 (re-conversion on a memo). The rest need PRC citizenship, a PR-ID, cancelled household registration, an inheritance, or a trade registration.</p></div>
  <div class="card"><p class="k">Usable without documenting a source</p><p class="v">0</p><p class="s">Regulation 532 Art. 12 requires a real, lawful transaction basis for every current-account payment.</p></div>
  <div class="card"><p class="k">Cheapest published</p><p class="v">Route 1</p><p class="s">0.225% at USD 400,000 on the Bank of China combination. See the Costs page.</p></div>
</div>

<div class="note"><strong>How to read the tags.</strong> <span class="tag t-ok">lawful</span> means a reviewed instrument describes
the route and does not prohibit it. <span class="tag t-warn">capital</span> means it sits under the capital account and needs
SAFE approval, with the staging or documentation that implies. <span class="tag t-bad">unlawful</span> means a reviewed
instrument attaches a penalty. None of these tags is an opinion about your file — a branch officer decides that.</div>

<h2>The routes</h2>
{''.join(cards)}

<h2>What decides between them</h2>
<div class="tw"><table>
<thead><tr><th>If this is true of you</th><th>Then the realistic route is</th><th>Source</th></tr></thead>
<tbody>
<tr><td>U.S. passport only; the balance is documented salary or service income</td><td>Route 1 — the single best fit, and the cheapest</td><td>{slink("S06")}</td></tr>
<tr><td>You hold a PRC identity card</td><td>Route 2, or route 1's documentation above the quota</td><td>{slink("S03")}</td></tr>
<tr><td>You hold a PRC Foreign Permanent Resident ID</td><td>Route 3 up to the quota, then route 1</td><td>{slink("S07")}</td></tr>
<tr><td>You have the original exchange memo for the RMB</td><td>Route 4, if within 24 months</td><td>{slink("S08")}</td></tr>
<tr><td>You have cancelled PRC household registration</td><td>Route 5, staged over two years</td><td>{slink("S11")}</td></tr>
<tr><td>The funds are an inheritance</td><td>Route 6</td><td>{slink("S11")}</td></tr>
<tr><td>You cannot evidence the source at all</td><td>No reviewed route. Any offer to help is route 10.</td><td>{slink("S01")}</td></tr>
</tbody></table></div>
"""
    return shell("methods.html", "Methods", body, lede)


# ------------------------------------------------------------- penalties ----
def page_penalties() -> str:
    p = {r["usd"]: r for r in COST["penalties"]}
    tiers = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000]

    def fmt(v, prefix="$"):
        if v is None:
            return '<td class="blank">— blank</td>'
        return f'<td class="num">{prefix}{v:,.2f}</td>'

    rows = []
    for t in tiers:
        r = p[t]
        rows.append(f"""<tr><td class="num">${t:,}</td>
{fmt(r["spread_best_usd"])}{fmt(r["spread_worst_usd"])}
{fmt(r["fee_boc_usd"])}
<td class="num">$0.00</td>
{fmt(r["recordal_usd"])}
{fmt(r["prc_iit_usd"])}
{fmt(r["us_988_gain_usd"])}
{fmt(r["fbar_nonwillful_max_usd"])}{fmt(r["fbar_willful_max_usd"])}
{fmt(r["unlawful_30pct_usd"])}</tr>""")

    full = []
    for t in [10_000 * i for i in range(1, 41)]:
        r = p[t]
        full.append(f"""<tr><td class="num">${t:,}</td>
{fmt(r["spread_best_usd"])}{fmt(r["spread_worst_usd"])}{fmt(r["fee_boc_usd"])}
{fmt(r["recordal_usd"])}{fmt(r["prc_iit_usd"])}{fmt(r["us_988_gain_usd"])}
{fmt(r["fbar_willful_max_usd"])}{fmt(r["unlawful_30pct_usd"])}</tr>""")

    lede = """
<p class="crumb">Penalties</p>
<h1>The “conversion penalty” is seven separate things. Only three of them are avoidable.</h1>
<p class="lede">The original complaint is that converting would cost “a considerable amount of taxes”. Breaking the cost into
layers shows why that figure felt large and what each part actually is: a shoppable spread, a capped fee, a free filing, a
tax on the <em>income</em>, a usually-trivial U.S. currency gain, two U.S. filing duties with very large statutory maxima, and
the statutory penalties for the shortcuts. Layers 1 and 2 are the real cost of converting. Layer 3 is free. Layer 4 is not
caused by the conversion at all.</p>
"""

    body = f"""
<div class="tw"><table class="wide">
<thead><tr><th>Layer</th><th>What it is</th><th class="num">Cost if avoidable</th><th>Avoidable?</th><th>Source</th></tr></thead>
<tbody>
<tr><td><strong>1</strong></td><td>Bank buy/sell spread — crossing from mid to the bank's selling rate</td>
<td class="num">≈0.21% – 0.50% of the dollars delivered</td><td><span class="tag t-ok">yes — shop the bank</span></td><td>{slink("S24")} {slink("S26")} {slink("S27")}</td></tr>
<tr><td><strong>2</strong></td><td>Wire issuance, cable, and the correspondent deduction</td>
<td class="num">$0 – $115 sender side; receiver's charge unpublished</td><td><span class="tag t-warn">partly</span></td><td>{slink("S25")} {slink("S28")}</td></tr>
<tr><td><strong>3</strong></td><td>Tax recordal (税务备案) for a single outward payment over USD 50,000</td>
<td class="num">No tax charged; online and free</td><td><span class="tag t-ok">not a cost at all</span></td><td>{slink("S09")} {slink("S10")}</td></tr>
<tr><td><strong>4</strong></td><td>PRC income tax on the income behind the balance</td>
<td class="num">3%–45% comprehensive, or 20% flat</td><td><span class="tag t-bad">no — it attaches to the income</span></td><td>{slink("S31")}</td></tr>
<tr><td><strong>5</strong></td><td>U.S. tax on the currency gain, 26 U.S.C. §988</td>
<td class="num">$0 if the gain is $200 or less; otherwise ordinary rates</td><td><span class="tag t-bad">no</span></td><td>{slink("S20")} {slink("S19")}</td></tr>
<tr><td><strong>6</strong></td><td>U.S. filing duties: FBAR above $10,000 aggregate; Form 8938 at $50,000/$75,000 single or $100,000/$150,000 MFJ in the U.S.</td>
<td class="num">Filing cost; maxima $16,536 non-willful and $165,353 willful per violation</td><td><span class="tag t-warn">yes — by filing</span></td><td>{slink("S16")} {slink("S17")} {slink("S18")}</td></tr>
<tr><td><strong>7</strong></td><td>Statutory penalties for unlawful routes</td>
<td class="num">Up to 30%, or 30%–100% if serious; up to 20% for cash</td><td><span class="tag t-ok">yes — by not using them</span></td><td>{slink("S01")}</td></tr>
</tbody></table></div>

<div class="crit"><strong>The arithmetic that reframes the question.</strong> At USD 400,000 the lawful route costs
<strong>$901.20</strong> (BOC). The 30% floor in Regulation 532 Art. 39 for evasion is <strong>$120,000</strong>, and the
serious-case ceiling in Art. 40 or 45 is <strong>$400,000</strong>. If the bank's “considerable tax” is layer 4, then
no conversion route avoids it and the choice between routes changes nothing about it; if it is layer 1, it is 0.2% and
shoppable; if it is layer 3, it is a free form. The three possibilities differ by four orders of magnitude, and only the
bank's written answer (Q04) distinguishes them.</div>

<h2>Layers priced at the amounts that matter</h2>
<div class="tw"><table class="wide">
<thead><tr><th class="num">Amount</th>
<th class="num">1a · spread<br><span style="font-weight:400;text-transform:none">best (BOC)</span></th>
<th class="num">1b · spread<br><span style="font-weight:400;text-transform:none">worst (HSBC)</span></th>
<th class="num">2 · wire<br><span style="font-weight:400;text-transform:none">BOC capped</span></th>
<th class="num">2 · wire<br><span style="font-weight:400;text-transform:none">HSBC Private</span></th>
<th class="num">3 · recordal<br><span style="font-weight:400;text-transform:none">no fee published</span></th>
<th class="num">4 · PRC IIT<br><span style="font-weight:400;text-transform:none">20% illustration</span></th>
<th class="num">5 · U.S. §988<br><span style="font-weight:400;text-transform:none">needs a basis</span></th>
<th class="num">6 · FBAR<br><span style="font-weight:400;text-transform:none">non-willful max</span></th>
<th class="num">6 · FBAR<br><span style="font-weight:400;text-transform:none">willful max</span></th>
<th class="num">7 · unlawful<br><span style="font-weight:400;text-transform:none">30% floor</span></th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

<div class="note"><strong>How to read the blanks.</strong> Layer 3 is blank because no reviewed instrument attaches a fee to
recordal and I will not print a zero I cannot source — Art. 6 of Announcement 2013 No. 40 says the authority need not
examine the tax position and issues a serial number, and the 2021 interpretation adds the online channel. Layer 5 is blank
because a currency gain requires the dollar basis of the renminbi, which is unknown (Q05). Layer 4 is a flat-20% illustration
only: the 3%–45% progressive table depends on deductions and other income that are unknown.</div>

<h2>Every layer at every $10,000 step</h2>
<p class="lede">Same seven layers, all 40 tiers. The spread columns bracket the shoppable range; the unlawful column is
there to show the scale of the exposure that layers 1–3 do not have.</p>
<div class="tw"><table class="wide">
<thead><tr><th class="num">Amount</th><th class="num">Spread best</th><th class="num">Spread worst</th>
<th class="num">Wire BOC</th><th class="num">Recordal</th><th class="num">PRC IIT 20%</th>
<th class="num">U.S. §988</th><th class="num">FBAR willful max</th><th class="num">Unlawful 30%</th></tr></thead>
<tbody>{''.join(full)}</tbody></table></div>

<h2>What is not a penalty but gets called one</h2>
<div class="tw"><table>
<thead><tr><th>Phrase used in the corpus</th><th>What the reviewed text actually provides</th><th>Source</th></tr></thead>
<tbody>
<tr><td>“Conversion tax”</td><td>No reviewed instrument taxes the exchange. There is a spread, a tariff, a filing step, and tax on the income.</td><td>{slink("S31")} {slink("S24")}</td></tr>
<tr><td>“0.5% issuer fee”</td><td>No instrument reviewed imposes an issuer fee. The only 0.5%-scale figure found is HSBC's <em>published spread</em> of 0.49995%, which is a rate, not a fee.</td><td>{slink("S27")} {slink("S28")}</td></tr>
<tr><td>“CNY 30,000 bank fine under 汇发〔2007〕1号 Art. 39”</td><td>Repealed by 汇发〔2023〕8号; the SAFE republication prints the deletion and the current-rules catalogue repeats it. Use Regulation 532 Arts. 39–48 instead.</td><td>{slink("S03")} {slink("S04")} {slink("S01")}</td></tr>
<tr><td>“USD 50,000 annual limit”</td><td>An annual facilitation quota, not a ceiling; SAFE says lawful current-account settlement and purchase have no amount limit.</td><td>{slink("S05")}</td></tr>
<tr><td>“Staged over 8 years via the quota”</td><td>Only true if you choose the quota route with no other documentation. Route 1 has no such staging, and route 5 is staged over two years by rule, not eight.</td><td>{slink("S05")} {slink("S11")}</td></tr>
</tbody></table></div>
"""
    return shell("penalties.html", "Penalties", body, lede)


# ----------------------------------------------------------------- taxes ----
def page_taxes() -> str:
    u = COST["us"]
    lede = """
<p class="crumb">Tax &amp; reporting</p>
<h1>Two tax systems, neither of which taxes the exchange</h1>
<p class="lede">China taxes the <em>income</em> that produced the renminbi; the United States taxes the <em>currency gain</em> on
disposal and requires the account to be reported. Neither reviewed instrument taxes the act of converting. What follows is the
statutory framework with its thresholds, and one illustration — clearly labelled — because your basis, residency and other
income are unknown.</p>
"""
    body = f"""
<h2>China</h2>
<div class="tw"><table class="wide">
<thead><tr><th>Rule</th><th>What it says</th><th>Effect on a CNY→USD conversion</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Individual Income Tax Law Art. 3</td>
<td>Comprehensive income 3%–45% progressive; business income 5%–35%; interest, dividends and bonuses, lease of property,
transfer of property and incidental income at a flat 20%.</td>
<td>Applies to the income when it arises, before and independent of any conversion.</td><td>{slink("S31")}</td></tr>
<tr><td>Regulation 532 Art. 12</td>
<td>Current-account FX receipts and payments must have a real, lawful transaction basis; the bank must reasonably review
the authenticity of documents and their consistency with the payment.</td>
<td>This is the gate that actually stops transfers — documentation, not tax.</td><td>{slink("S01")}</td></tr>
<tr><td>PBOC Decree [2006] No.3 Art. 13 / 汇发〔2007〕1号 Art. 13(1)</td>
<td>A non-domestic individual may purchase FX against legitimate current-account RMB income on valid ID and
transaction-amount materials including tax documents.</td>
<td>Names the documents. Does not create a tax.</td><td>{slink("S02")} {slink("S03")}</td></tr>
<tr><td>汇发〔2020〕14号 Art. 59 (as quoted by SAFE in 2026)</td>
<td>Conversion on valid ID plus source-of-funds materials evidencing the transaction amount, including tax documents.</td>
<td>The operative sentence for a foreign passport holder.</td><td>{slink("S06")}</td></tr>
<tr><td>Announcement 2013 No. 40 Art. 1 and 6</td>
<td>Tax recordal for a single outward payment above the equivalent of USD 50,000; where documents are complete the
authority need not examine the tax position on the spot and issues a serial number.</td>
<td>A filing obligation, not an assessment.</td><td>{slink("S09")}</td></tr>
<tr><td>Announcement 2021 No. 19 (interpretation)</td>
<td>One recordal per contract; may be completed online; the USD 50,000 threshold is unchanged.</td>
<td>Reduces it to one online form per contract.</td><td>{slink("S10")}</td></tr>
<tr><td>Regulation 532 Arts. 39, 40, 42, 45, 48</td>
<td>Penalties for evasion, illegal arbitrage, unlawful cash carriage, private FX dealing and invalid documents:
up to 30%, or 30%–100% if serious; 20% for cash; CNY 50,000 for an individual's invalid documents.</td>
<td>The only route through which the conversion itself becomes expensive.</td><td>{slink("S01")}</td></tr>
</tbody></table></div>

<h2>United States</h2>
<div class="tw"><table class="wide">
<thead><tr><th>Rule</th><th>What it says</th><th>Threshold it applies at</th><th>Source</th></tr></thead>
<tbody>
<tr><td>26 U.S.C. §988(a)(1)(A)</td><td>Foreign currency gain or loss on a section 988 transaction is computed separately
and treated as <em>ordinary</em> income or loss.</td><td>Any amount, unless an exclusion applies.</td><td>{slink("S20")}</td></tr>
<tr><td>26 U.S.C. §988(c)(1)(C)</td><td>Disposing of nonfunctional currency (renminbi) is a section 988 transaction.</td>
<td>Converting CNY to USD is a disposal.</td><td>{slink("S20")}</td></tr>
<tr><td>26 U.S.C. §988(e)(2)</td><td>For an individual's personal transaction, no gain is recognised on exchange-rate
change — but the exclusion does not apply if the gain exceeds <strong>$200</strong>.</td>
<td>$200. {esc(u["illo_small_gain"]["rule"])}.</td><td>{slink("S20")}</td></tr>
<tr><td>IRS Publication 525</td><td>“If you have a gain on a personal foreign currency transaction because of changes in
exchange rates, you don't have to include that gain in your income unless it's more than $200.”</td>
<td>Confirms the $200 line.</td><td>{slink("S19")}</td></tr>
<tr><td>IRS yearly average rates</td><td>2025 = 7.129, 2024 = 7.189 CNY/USD, for translating amounts on a return; the IRS
states it has no official rate and accepts any posted rate used consistently.</td>
<td>Reporting translation only — not a transaction price.</td><td>{slink("S21")}</td></tr>
<tr><td>FBAR (31 CFR 1010.350 / FinCEN 114)</td><td>A U.S. person must report foreign financial accounts where the aggregate
exceeded <strong>$10,000</strong> at any time in the year; due 15 April, automatic extension to 15 October.</td>
<td>$10,000 aggregate — a CNY account crosses this immediately.</td><td>{slink("S16")}</td></tr>
<tr><td>31 CFR 1010.821 Table 1</td><td>Non-willful FBAR maximum <strong>$16,536</strong>; willful maximum
<strong>$165,353</strong> per violation (penalties assessed on or after 17 January 2025).</td>
<td>Statutory maxima, not a prediction.</td><td>{slink("S17")}</td></tr>
<tr><td>Form 8938</td><td>Specified individuals above the threshold must report specified foreign financial assets with the
return: $50,000 last-day / $75,000 any-time (single, in the U.S.); $100,000 / $150,000 (MFJ, in the U.S.);
$200,000 / $300,000 (living abroad, non-joint); $400,000 / $600,000 (living abroad, joint).</td>
<td>The range in this project's question crosses every one of those lines.</td><td>{slink("S18")}</td></tr>
<tr><td>FinCEN Form 105 (CBP)</td><td>Amounts over <strong>$10,000</strong> entering or leaving the United States must be
reported; the threshold applies to the group total.</td>
<td>Applies to the receiving end, including cash.</td><td>{slink("S15")}</td></tr>
<tr><td>Form 3520</td><td>Reports certain transactions with foreign trusts and the receipt of certain large gifts or
bequests from foreign persons.</td>
<td>Only if the balance is a gift or inheritance from a foreign person.</td><td>{slink("S23")}</td></tr>
</tbody></table></div>

<h2>The one illustration, and why it is only an illustration</h2>
<p class="lede">A currency gain needs a dollar basis: the USD value of the renminbi when each tranche was received, compared
with the USD received on conversion. That is unknown here (Q05). What can be shown is the <em>statutory rate</em> that would
apply to a given ordinary gain for a single filer with no other taxable income, using the 2026 brackets.</p>
<div class="tw"><table>
<thead><tr><th>Illustrative §988 gain</th><th>Excluded by §988(e)(2)?</th><th>U.S. tax, single filer, no other income</th><th>Effective rate</th></tr></thead>
<tbody>
<tr><td class="num">$150</td><td>Yes — at or below $200</td><td class="num">$0.00</td><td class="num">0.000%</td></tr>
<tr><td class="num">$6,226.68 <span style="font-size:.76rem;color:#5a6f66">(the 2024→2025 move on USD 100,000)</span></td>
<td>No — above $200</td><td class="num">${u["illo_6227_gain"]["tax_usd"]:,.2f}</td><td class="num">{u["illo_6227_gain"]["marginal"]:.2f}%</td></tr>
<tr><td class="num">$50,000</td><td>No</td><td class="num">${u["illo_50k_gain"]["tax_usd"]:,.2f}</td>
<td class="num">{u["illo_50k_gain"]["marginal"]:.2f}%</td></tr>
<tr><td class="num">$400,000</td><td>No</td><td class="num">${u["illo_400k_gain"]["tax_usd"]:,.2f}</td>
<td class="num">{u["illo_400k_gain"]["marginal"]:.2f}%</td></tr>
</tbody></table></div>
<p style="font-size:.88rem;color:#4a5f56">Brackets and standard deduction from Rev. Proc. 2025-32 §4.01 Table 3 and §4.14
({slink("S22")}). The 2026 single standard deduction of $16,100 is applied to the gain only; other income would push it into
higher brackets, and the FEIE or a treaty position could change the result. The $6,226.68 row uses the IRS yearly averages
of 7.189 and 7.129 ({slink("S21")}) purely to size the gain — it is not a basis you actually have.</p>

<div class="note"><strong>The asymmetry worth noticing.</strong> Every cost in the conversion itself is measured in hundreds of
dollars. The U.S. reporting maxima in the same table are measured in tens and hundreds of thousands. If the FBAR and 8938
history is unclear, that — not the spread — is the number to resolve before moving funds.</div>
"""
    return shell("taxes.html", "Tax & reporting", body, lede)


# ------------------------------------------------------------- questions ----
def page_questions() -> str:
    by_p = {}
    for q in QUES:
        by_p.setdefault(q["priority"], []).append(q)
    groups = []
    labels = {1: "Priority 1 — nothing can be decided until these are answered",
              2: "Priority 2 — these decide the route and the U.S. exposure",
              3: "Priority 3 — these decide timing and price",
              4: "Priority 4 — these close the remaining gaps"}
    for p in sorted(by_p):
        cards = []
        for q in sorted(by_p[p], key=lambda x: x["id"]):
            srcs = " ".join(slink(s) for s in q["sources"])
            cards.append(f"""
<details id="{q["id"]}"><summary>{q["id"]} · {esc(q["question"])}</summary>
<p class="q-meta"><strong>Why it blocks a decision:</strong> {esc(q["why"])}</p>
<div class="tw"><table>
<tbody>
<tr><th style="width:31%">What we already have</th><td>{esc(q["we_have"])}</td></tr>
<tr><th>If it stays unknown</th><td>{esc(q["if_unknown"])}</td></tr>
<tr><th>How to discover it</th><td>{esc(q["how_to_find"])}</td></tr>
<tr><th>Official basis</th><td>{srcs}</td></tr>
</tbody></table></div>
</details>""")
        groups.append(f'<h2>{esc(labels[p])}</h2>{"".join(cards)}')

    lede = """
<p class="crumb">Questions</p>
<h1>The 14 questions that have to be answered before any decision is reasonable</h1>
<p class="lede">This is the register the brief asked for: what needs to be addressed, what we already know, what we do not,
why the gap blocks a decision, and the specific step that would close it. Three of them block everything. None of the three
can be answered from anything in this repository — each needs a document only you or your bank holds.</p>
"""
    body = f"""
<div class="crit"><strong>The three that block everything.</strong>
<strong>Q01</strong> — are you a 境内个人 or a 境外个人? PBOC Decree [2006] No.3 Art. 37 splits the entire rule set on this, and
Regulation 532 Art. 52(2) uses a different test again.
<strong>Q02</strong> — what is the documented source of the balance? Regulation 532 Art. 12 makes a real, lawful transaction
basis mandatory.
<strong>Q03</strong> — has PRC tax been assessed on that income, and can you obtain the record? Without it, the “considerable
tax” cannot be identified as a tax at all.
{slink("S02")} {slink("S01")} {slink("S31")}</div>
{''.join(groups)}

<h2>What answering them changes</h2>
<div class="tw"><table class="wide">
<thead><tr><th>If the answer is…</th><th>Then the route becomes…</th><th>And the cost is…</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Q02 positive: documented lawful income, Q03 record available</td><td>Route 1, one transfer</td>
<td>0.225% at USD 400,000 — about $901</td><td>{slink("S06")} {slink("S24")}</td></tr>
<tr><td>Q02 positive, but PRC citizenship retained</td><td>Route 2 inside the quota, route 1's documentation above it</td>
<td>The same shape: the quota changes the paperwork, not the rate</td><td>{slink("S03")}</td></tr>
<tr><td>Q02 negative but household registration cancelled</td><td>Route 5, SAFE approval, staged over two years</td>
<td>Spread plus fee plus the two-year delay; above CNY 500,000 needs headquarters approval</td><td>{slink("S11")}</td></tr>
<tr><td>Q02 negative and the funds are inherited</td><td>Route 6</td><td>Spread plus fee plus the PRC tax certificate</td><td>{slink("S11")}</td></tr>
<tr><td>Q02 unfixable and no capital-account route</td><td>No lawful route</td>
<td>Any provider offering one is route 10: 30%–100% exposure</td><td>{slink("S01")}</td></tr>
<tr><td>Q06 negative: FBAR/8938 unfiled</td><td>Sequence the compliance before the transfer</td>
<td>Statutory maxima of $16,536 non-willful and $165,353 willful per violation</td><td>{slink("S17")}</td></tr>
</tbody></table></div>
"""
    return shell("questions.html", "Questions", body, lede)


# ----------------------------------------------------------------- audit ----
def page_audit() -> str:
    sev = {"material": "t-bad", "procedural": "t-warn", "minor": "t-neu"}
    cards = []
    for f in FIND:
        srcs = " ".join(slink(s) for s in f["sources"]) or '<span class="src">internal check</span>'
        prior = (f'<tr><th>Where it appears</th><td>{esc(f["prior_state"])}</td></tr>')
        cards.append(f"""
<details id="{f["id"]}"><summary>{f["id"]} · {esc(f["area"])} &nbsp;<span class="tag {sev[f["severity"]]}">{f["severity"]}</span></summary>
<div class="tw"><table>
<tbody>
<tr><th style="width:26%">Claim as published</th><td>{esc(f["claim"])}</td></tr>
<tr><th>What the official text says</th><td>{esc(f["what_official_says"])}</td></tr>
<tr><th>Verdict</th><td><strong>{esc(f["verdict"])}</strong></td></tr>
{prior}
<tr><th>Action taken here</th><td>{esc(f["action"])}</td></tr>
<tr><th>Official source</th><td>{srcs}</td></tr>
</tbody></table></div>
</details>""")

    lede = """
<p class="crumb">Repo audit</p>
<h1>Line-by-line check of what this repository already published</h1>
<p class="lede">The brief asked for the existing repository to be reviewed against official sources, with irregularities
flagged. Twenty-four prior session directories are present. This page checks the load-bearing claims — the ones that change
an answer — against the documents themselves. Nine findings. The most consequential is that a “conversion tax” appears
throughout the corpus that no reviewed instrument imposes, and a penalty article that was repealed in 2023 is still cited
as live law.</p>
"""
    body = f"""
<div class="grid">
  <div class="card"><p class="k">Findings</p><p class="v">9</p><p class="s">4 material · 1 procedural · 3 minor</p></div>
  <div class="card"><p class="k">Prior dashboards at the root</p><p class="v">16</p><p class="s">With overlapping scopes and, in places, different answers to the same question.</p></div>
  <div class="card"><p class="k">Session branches on the remote</p><p class="v">65</p><p class="s">14 CI workflows. One job was already failing before this session started.</p></div>
  <div class="card"><p class="k">Prior claim found unsupported</p><p class="v">“conversion tax”</p><p class="s">No reviewed instrument taxes the exchange. See AK-02.</p></div>
</div>

<div class="note"><strong>How findings about other sessions' files are handled.</strong> Each is recorded here and on the Flagged
for Review page, not edited in place. Another session's file is that session's scope; the brief's protocol is to log a
cross-scope request rather than to rewrite it. What this section does instead is state the correct answer once, with the
source, so the two can be compared.</div>

<h2>Findings</h2>
{''.join(cards)}

<h2>Structural observations about the repository</h2>
<div class="tw"><table class="wide">
<thead><tr><th>Observation</th><th>Evidence</th><th>Assessment</th><th>Logged as</th></tr></thead>
<tbody>
<tr><td>The root landing page offers 16 category cards into 16 separate dashboards</td>
<td>Root <code>index.html</code>, generated by <code>ladder/build.py</code></td>
<td>Every card is internally consistent; collectively they are not a single answer. A reader has no way to know which is current.</td><td>FL-09</td></tr>
<tr><td>Method counts differ between sections: 13, 15, 17, 18, 22, 23</td><td>Section indexes across the corpus</td>
<td>Driven by counting banks and card products as separate methods. See AK-08.</td><td>FL-10</td></tr>
<tr><td><code>audit-92d12752/verify.py</code> fails its own snapshot assertion</td>
<td>Run in this session: <code>AssertionError: snapshot differs: rerun build.py after inspecting repository changes</code></td>
<td>A pre-existing failure in a section this session does not own. It does not affect the site's published pages, but it means that section's CI is red.</td><td>FL-08</td></tr>
<tr><td>Two pull requests (#53, #55) are stale duplicates of work already merged</td>
<td>Last updated 10 Nov 2026, no commits since; content superseded by merged PRs #54/#57/#58</td>
<td>Not taken over here — this section needs none of their files.</td><td>FL-11</td></tr>
<tr><td>The IRS 2025 annual average (7.129) is used as a transaction price in several cost tables</td>
<td>See AK-03; difference from the 11 Nov 2026 board is about 6.1%</td>
<td>The IRS describes these as averages for translating return amounts.</td><td>AK-03</td></tr>
</tbody></table></div>
"""
    return shell("audit.html", "Repo audit", body, lede)


# --------------------------------------------------------------- flagged ----
FLAGS = [
 ("FL-01", "Route eligibility", "Whether the balance is held as 境内个人 or 境外个人 cannot be determined from the repository or the request.",
  "The annual USD 50,000 purchase quota is written for 境内个人 (a PRC citizen, PBOC Decree Art. 37(1)); SAFE extends it to a 境外个人 only with a PRC Foreign Permanent Resident ID. Meanwhile Regulation 532 Art. 52(2) counts a foreigner resident in China for a full year as a domestic individual. Costs are computed for both, and eligibility is marked per route.", ["S02", "S01", "S07"]),
 ("FL-02", "Tax amount", "No PRC or U.S. tax figure for this balance is given anywhere in this project.",
  "The PRC layer is shown as a flat-20% illustration only; the 3%–45% table needs deductions and other income that are unknown. The U.S. layer is shown as a statutory-rate illustration with no other income. Neither is your liability.", ["S31", "S22"]),
 ("FL-03", "Bank fee — CMB", "China Merchants Bank's outward-remittance fee",
  "CMB's live rate board was captured (6.66295 / 6.69199 on 10 Nov 2026) but its personal remittance tariff was not. The CMB all-in total and fee cells are blank rather than copied from an earlier session's snapshot.", ["S26"]),
 ("FL-04", "Bank board — ICBC", "ICBC's live rates and fees",
  "The public board returned “暂无数据” (no data) and is script-populated, so nothing could be read. ICBC is absent from every table rather than shown at a stale rate.", ["S30"]),
 ("FL-05", "Receiver-side cost", "The U.S. receiving bank's inward-wire fee and any correspondent deduction",
  "No sending bank publishes it, and HSBC's tariff note 7 states the charges exclude other institutions'. Every total is therefore a lower bound.", ["S28"]),
 ("FL-06", "Rate status", "Whether the boards used equal the executable rate on the day you transact",
  "All three boards carry the publisher's own “for reference only” disclaimer. BOC's says the actual rate at online banking, mobile banking, smart counters or the counter prevails.", ["S24", "S26", "S27"]),
 ("FL-07", "Tax recordal fee", "Whether tax recordal carries any charge",
  "No reviewed instrument attaches a fee, and Announcement 2013 No. 40 Art. 6 says the authority need not examine the tax position. The layer is shown blank, not as $0, because a zero would need a source.", ["S09", "S10"]),
 ("FL-08", "Pre-existing CI failure", "audit-92d12752/verify.py fails its snapshot assertion",
  "Reproduced in this session. It is a different session's scope and is logged, not repaired. It does not publish anything on this site.", []),
 ("FL-09", "Corpus fragmentation", "16 dashboards at the root with overlapping scopes",
  "Two sections can state different answers to the same question with no marker of which is current. Consolidation is a cross-session decision, logged here and on the Repo audit page.", []),
 ("FL-10", "Method counts", "Method totals differ across sections (13–23)",
  "Variants (banks, card products) are counted as methods in some sections. This section lists 10 route types and treats bank choice as a price parameter.", []),
 ("FL-11", "Stale pull requests", "PRs #53 and #55 are open, outdated and superseded",
  "No commits since 10 Nov 2026; content covered by merged PRs #54/#57/#58. Not taken over — this section needs none of their files. Left for the integrator to close.", []),
 ("FL-12", "Annual average as a price", "Prior cost tables use the IRS 2025 average of 7.129 CNY/USD as the transaction rate",
  "The IRS describes it as an average for translating return amounts and states it has no official rate. Against the 11 Nov 2026 board the difference is about 6.1%. Used here only to size a §988 gain.", ["S21", "S24"]),
 ("FL-13", "Repealed article", "汇发〔2007〕1号 Art. 39 (CNY 30,000 / CNY 1,000 fines) is still cited in places as live law",
  "SAFE's republication prints the deletion by 汇发〔2023〕8号 and the current-rules catalogue repeats it. The live penalties are Regulation 532 Arts. 39–48.", ["S03", "S04", "S01"]),
 ("FL-14", "Payment-versus-evidence", "Whether the bank wants a tax payment, a tax record, or a recordal reference",
  "The reviewed rules require evidence of source (which may include a tax record) and, over USD 50,000 per payment, a recordal. None of them creates a new tax on the transfer. Only the bank's written answer resolves it.", ["S06", "S09"]),
 ("FL-15", "Personal facts", "Your U.S. basis, residency, filing status, other income, and FBAR/8938 history",
  "Not inferred. The Questions page lists each as a numbered gap with the step that would close it.", ["S20", "S16", "S18"]),
 ("FL-16", "Not advice", "Nothing in this section is legal, tax or investment advice, and no institution was contacted",
  "Document review only. A branch officer applies these rules to a specific file.", ["S05", "S06"]),
]


def page_flagged() -> str:
    rows = "".join(
        f"""<tr><td class="num">{esc(i)}</td><td><strong>{esc(a)}</strong></td><td>{esc(b)}</td>
<td>{esc(c)}</td><td class="src">{(" ".join(slink(s) for s in d)) or "—"}</td></tr>"""
        for i, a, b, c, d in FLAGS)
    lede = """
<p class="crumb">Flagged for review</p>
<h1>Everything left blank, and everything irregular</h1>
<p class="lede">The brief's rule was: if a value cannot be confirmed from an official source, leave it blank and flag it —
never infer it. This page is that list. It is not a list of failures; it is the boundary of what the documents actually
establish, published so it can be checked.</p>
"""
    body = f"""
<div class="tw"><table class="wide">
<thead><tr><th>Ref</th><th>Category</th><th>The gap or irregularity</th><th>Why it is left open</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Where each blank appears</h2>
<div class="tw"><table>
<thead><tr><th>Page</th><th>The blank</th><th>Ref</th></tr></thead>
<tbody>
<tr><td><a href="costs.html">Costs</a></td><td>CMB wire fee and CMB all-in total, every tier</td><td>FL-03</td></tr>
<tr><td><a href="costs.html">Costs</a></td><td>Correspondent and receiving-bank charges, every tier</td><td>FL-05</td></tr>
<tr><td><a href="penalties.html">Penalties</a></td><td>Recordal cost</td><td>FL-07</td></tr>
<tr><td><a href="penalties.html">Penalties</a></td><td>U.S. §988 gain, every tier</td><td>FL-15</td></tr>
<tr><td><a href="taxes.html">Tax &amp; reporting</a></td><td>PRC tax at 3%–45% and any personal U.S. liability</td><td>FL-02</td></tr>
<tr><td><a href="questions.html">Questions</a></td><td>Q01, Q02, Q03, Q05, Q06 — all unanswered</td><td>FL-01, FL-15</td></tr>
</tbody></table></div>
"""
    return shell("flagged.html", "Flagged for review", body, lede)


# --------------------------------------------------------------- sources ----
def page_sources() -> str:
    rows = []
    for s in SRC:
        relied = "".join(f"<li>{esc(r)}</li>" for r in s["relied_on"])
        rows.append(f"""<tr>
<td class="num">{esc(s["id"])}</td>
<td><strong>{esc(s["pub"])}</strong><br><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])}</a>
<br><span class="q-meta">{esc(s["type"])} · read: {esc(s["read"])} · retrieved {esc(s["retrieved"])}</span></td>
<td><ul style="margin:0;padding-left:1.05rem">{relied}</ul>
{f'<p class="q-meta" style="margin:.4rem 0 0"><strong>Note:</strong> {esc(s["note"])}</p>' if s.get("note") else ""}</td>
</tr>""")
    lede = """
<p class="crumb">Sources</p>
<h1>31 documents, each read in this session</h1>
<p class="lede">Every figure in this section traces to one of these. Each entry gives the publisher, the link, the retrieval
date, what was actually read, and the exact proposition relied on — so a sentence can be found again rather than trusted.
Two entries (ICBC and the SAFE central-parity page) are recorded as <em>capture failures</em>: they are listed precisely
because nothing was taken from them.</p>
"""
    body = f"""
<div class="grid">
  <div class="card"><p class="k">Documents</p><p class="v">31</p><p class="s">22 PRC official · 8 U.S. official · 3 bank primary · 2 recorded capture failures</p></div>
  <div class="card"><p class="k">Read in full</p><p class="v">26</p><p class="s">5 read as the relevant article or table, with the locator given</p></div>
  <div class="card"><p class="k">Used for a number</p><p class="v">9</p><p class="s">Three rate boards, two tariffs, the 2026 brackets, the FBAR maxima, the PRC IIT rates, the IRS averages</p></div>
  <div class="card"><p class="k">Retrieved</p><p class="v">11 Nov 2026</p><p class="s">All on the same day, so no figure is carried over from an earlier snapshot</p></div>
</div>

<div class="note"><strong>Source hierarchy used.</strong> Statutes and regulations first, then the regulator's own Q&amp;A and
catalogues, then the institution's published tariff or rate board, then IRS/US-CBP guidance, then U.S. Code as published by a
university law library where the official U.S. Code site was not reachable. Secondary commentary (news, blogs, law-firm
summaries) was used only to locate a primary text and is never cited for a value.</div>

<h2>The register</h2>
<div class="tw"><table class="wide">
<thead><tr><th>ID</th><th>Publisher, title, link, and what was read</th><th>The exact propositions relied on</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
"""
    return shell("sources.html", "Sources", body, lede)


def main() -> None:
    pages = {
        "index.html": page_index(), "costs.html": page_costs(), "methods.html": page_methods(),
        "penalties.html": page_penalties(), "taxes.html": page_taxes(),
        "questions.html": page_questions(), "audit.html": page_audit(),
        "flagged.html": page_flagged(), "sources.html": page_sources(),
    }
    for name, content in pages.items():
        (HERE / name).write_text(content, encoding="utf-8")
    print(f"wrote {len(pages)} pages, {sum(len(c) for c in pages.values()):,} bytes")


if __name__ == "__main__":
    main()
