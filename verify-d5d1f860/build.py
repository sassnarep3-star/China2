#!/usr/bin/env python3
"""Build the consolidated CNY->USD verification dashboard (session d5d1f860).

Deterministic: no timestamps other than the fixed constants below.
Reads (read-only): ../repatriate/data/methods.json (17 methods, pros/cons/steps)
Reads (owned):     data/verification.json (sources fetched and quoted this session)
Writes:            index.html, costs.html, methods.html, taxes.html, sources.html,
                   audit.html, flagged.html, exports/costs.csv, assets/style.css, assets/app.js
"""
from __future__ import annotations

import csv
import json
import math
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
METHODS_PATH = ROOT / "repatriate" / "data" / "methods.json"
LEDGER_PATH = HERE / "data" / "verification.json"

SESSION = "arena/d5d1f860-china2"
UPDATED = "2026-11-10"
RATE = 7.129  # CNY per USD, IRS 2025 yearly average (VS14)
TIERS = list(range(10_000, 400_001, 10_000))
KEY_TIERS = [10_000, 50_000, 100_000, 200_000, 400_000]

# HSBC tariff 2.2.4.1/2.2.4.2, Premier and Advance individual customers (VS13).
WIRE_PCT = 0.001
WIRE_MIN_CNY = 100.0
WIRE_MAX_CNY = 500.0
CABLE_CNY = 120.0

ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
SRC = {s["id"]: s for s in ledger["sources"]}
METHODS = json.loads(METHODS_PATH.read_text(encoding="utf-8"))["methods"]
METHOD_BY_ID = {m["id"]: m for m in METHODS}


# ----------------------------------------------------------------------------- cost model
def cny_of(usd: float) -> float:
    return round(usd * RATE, 2)


def hsbc_wire(usd: float) -> tuple[float, float]:
    """Return (fee_cny, fee_usd) for one HSBC Premier/Advance telegraphic transfer."""
    cny = cny_of(usd)
    fee_cny = min(max(cny * WIRE_PCT, WIRE_MIN_CNY), WIRE_MAX_CNY) + CABLE_CNY
    return round(fee_cny, 2), round(fee_cny / RATE, 2)


def cost(mid: str, usd: float) -> dict:
    """Published-fee component and binding constraint for one method at one amount.

    Only values stated in a retrieved primary document are returned. Anything a
    provider does not publish is None and is rendered blank.
    """
    cny = cny_of(usd)
    out = {"published_usd": None, "basis": "", "constraint": "", "unverified": "FX spread and intermediary/receiver charges"}

    if mid == "M01":
        fee_cny, fee_usd = hsbc_wire(usd)
        out.update(
            published_usd=fee_usd,
            basis=f"HSBC Premier/Advance: ¥{fee_cny:,.2f} (0.1%, min ¥100, max ¥500 + ¥120 cable)",
            constraint="1 wire",
            unverified="FX spread, correspondent/recipient charges",
        )
    elif mid == "M02":
        years = math.ceil(usd / 50_000)
        total_cny = 0.0
        for i in range(years):
            tranche = min(50_000, usd - i * 50_000)
            total_cny += hsbc_wire(tranche)[0]
        out.update(
            published_usd=round(total_cny / RATE, 2),
            basis=f"{years} yearly tranche(s) of ≤$50,000; ¥{total_cny:,.2f} total",
            constraint=f"{years} calendar year(s)",
            unverified="FX spread; eligibility requires PRC ID or permanent-resident card",
        )
    elif mid == "M03":
        out.update(
            published_usd=0.0,
            basis="HSBC Global Transfer to own-name HSBC account: Free (Private Banking, Premier)",
            constraint="Transfer count unpublished",
            unverified="FX spread; Advance = USD 20/transfer with count unpublished",
        )
    elif mid == "M04":
        out.update(
            constraint=f"{math.ceil(cny/300_000)} transfer(s) at ≤¥300,000",
            unverified="Wise fee is quoted only in-app; overall limit set by your tax records",
        )
    elif mid == "M05":
        out.update(constraint="Eligibility/quote required", unverified="Fee, limit and FX rate are not published")
    elif mid == "M06":
        years = math.ceil(cny / 100_000)
        out.update(
            constraint=f"{years} year(s), {math.ceil(cny/10_000)} withdrawal(s)",
            unverified="Card-issuer and ATM fees; RMB 100,000/year is a hard ceiling (VS05)",
        )
    elif mid == "M07":
        out.update(
            published_usd=0.0,
            basis="HSBC counter FX cash withdrawal: Free (2.2.2.1); USD 5,000/trip needs no permit",
            constraint=f"{math.ceil(usd/5_000)} trip(s)",
            unverified="Cash FX spread, travel cost, insurance/risk (not published)",
        )
    elif mid == "M08":
        out.update(
            constraint=f"{math.ceil(cny/20_000)} trip(s) at ≤¥20,000",
            unverified="Offshore conversion rate and fees; current customs practice",
        )
    elif mid == "M09":
        out.update(
            constraint=f"{math.ceil(usd/500)} ID-only day(s) at ≤$500",
            unverified="Capped at the original exchange amount (unknown); spread",
        )
    elif mid in {"M10", "M11"}:
        out.update(
            constraint="SAFE approval; staged over up to 2 years if ≥¥200,000",
            unverified="Approval, documentation and fees are not published",
        )
    elif mid == "M12":
        out.update(constraint="Eligibility/quote required", unverified="20% IIT on gain may apply; fees not published")
    elif mid == "M13":
        out.update(constraint="Registered trade operator only", unverified="Not available for a savings balance")
    else:  # M14-M17
        out.update(
            constraint="REJECTED — unlawful",
            unverified="Statutory fine exposure, not a price: 30% standard / 30–100% serious (VS06)",
        )
    return out


def fine(usd: float) -> tuple[float, float]:
    return round(usd * 0.30, 2), round(usd * 1.00, 2)


def money(v: float | None, digits: int = 2) -> str:
    if v is None:
        return '<span class="blank" title="Not published by any source retrieved; left blank on purpose">—</span>'
    if v == 0:
        return "$0.00"
    if digits == 2 and abs(v) < 1_000:
        return f"${v:,.2f}"
    return f"${v:,.0f}"


def src_link(sid: str, label: str | None = None) -> str:
    s = SRC[sid]
    return (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">'
            f'{esc(label or sid)}</a>')


def src_links(ids: list[str]) -> str:
    return " ".join(src_link(i) for i in ids)


# ----------------------------------------------------------------------------- data checks
assert [m["id"] for m in METHODS] == [f"M{i:02d}" for i in range(1, 18)], "method set changed"
assert set(ledger["method_sources"]) == set(METHOD_BY_ID), "every method needs a source mapping"
for mid, ids in ledger["method_sources"].items():
    for sid in ids:
        assert sid in SRC, f"{mid} references unknown source {sid}"

LAWFUL = [m for m in METHODS if m["status"] == "lawful-conditional"]
REJECTED = [m for m in METHODS if m["status"] != "lawful-conditional"]
N_ROWS = len(METHODS) * len(TIERS)
FLAGGED_ROWS = sum(1 for m in METHODS for t in TIERS if cost(m["id"], t)["published_usd"] is None)


# ----------------------------------------------------------------------------- assets
CSS = """
:root{--ink:#10231e;--ink2:#1d3a31;--muted:#5b6f66;--paper:#f4f6f2;--card:#fff;--line:#dbe3dc;
--accent:#0a6b57;--accent2:#0f8a70;--warn:#7a4b00;--warnbg:#fff4dc;--bad:#9d2c1f;--badbg:#fdecea;
--ok:#116149;--okbg:#e6f4ee;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:#075b49}
header.top{position:sticky;top:0;z-index:20;background:var(--ink);color:#f3f6f2;box-shadow:0 1px 0 rgba(0,0,0,.2)}
header.top .bar{max-width:1120px;margin:0 auto;padding:.55rem 1rem;display:flex;align-items:center;gap:.9rem;flex-wrap:wrap}
header.top b{font-size:.98rem;letter-spacing:.01em}
header.top .meta{font-size:.78rem;color:#bcd0c7}
nav{max-width:1120px;margin:0 auto;padding:0 .5rem .45rem;display:flex;gap:.25rem;overflow-x:auto;scrollbar-width:thin}
nav a{color:#dcebe3;text-decoration:none;font-size:.85rem;padding:.35rem .6rem;border-radius:8px;white-space:nowrap}
nav a:hover{background:#1d3a31}
nav a[aria-current=page]{background:#f4f6f2;color:#10231e;font-weight:650}
main{max-width:1120px;margin:0 auto;padding:1.1rem 1rem 3rem}
h1{font-size:clamp(1.55rem,4.6vw,2.35rem);line-height:1.12;letter-spacing:-.02em;margin:.3rem 0 .5rem}
h2{font-size:clamp(1.15rem,2.6vw,1.5rem);margin:1.8rem 0 .5rem;letter-spacing:-.01em}
h3{font-size:1.02rem;margin:1.1rem 0 .35rem}
p{margin:.45rem 0}
.lede{color:#31473e;font-size:1.02rem;max-width:78ch}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.6rem;margin:1rem 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.7rem .8rem}
.kpi .n{font-size:1.4rem;font-weight:750;letter-spacing:-.02em;margin:0}
.kpi .l{font-size:.76rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin:.15rem 0 0}
.kpi .s{font-size:.8rem;color:var(--muted);margin:.1rem 0 0}
.box{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:.9rem 1rem;margin:.9rem 0}
.box.answer{border-left:5px solid var(--accent)}
.box.warn{background:var(--warnbg);border:1px solid #e8d3a6;border-left:5px solid #a76d10}
.box.bad{background:var(--badbg);border:1px solid #f0c9c3;border-left:5px solid var(--bad)}
.box.ok{background:var(--okbg);border:1px solid #c6e3d5;border-left:5px solid var(--ok)}
.box h2,.box h3{margin-top:.15rem}
ul,ol{margin:.35rem 0 .35rem 1.15rem;padding:0}
li{margin:.25rem 0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.6rem;margin:.9rem 0}
.card{display:flex;flex-direction:column;gap:.15rem;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.85rem .9rem;text-decoration:none;color:var(--ink)}
.card:hover{border-color:var(--accent2)}
.card strong{color:#075b49;font-size:.97rem}
.card span{font-size:.82rem;font-weight:650;color:#31473e}
.card em{font-style:normal;font-size:.82rem;color:var(--muted)}
.badge{display:inline-block;font-size:.7rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:.12rem .45rem;border-radius:999px;vertical-align:middle}
.b-ok{background:var(--okbg);color:var(--ok)}
.b-warn{background:var(--warnbg);color:var(--warn)}
.b-bad{background:var(--badbg);color:var(--bad)}
.b-mut{background:#e9eeea;color:#41554c}
.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:.7rem 0}
table{border-collapse:collapse;width:100%;font-size:.88rem;min-width:560px}
caption{text-align:left;padding:.6rem .75rem 0;font-size:.82rem;color:var(--muted)}
th,td{padding:.5rem .6rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
thead th{background:#eef2ee;font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:#33483f;position:sticky;top:0;z-index:2}
tbody tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
th.first,td.first{position:sticky;left:0;background:var(--card);z-index:1;min-width:7.5rem;box-shadow:1px 0 0 var(--line)}
thead th.first{background:#eef2ee;z-index:3}
tbody tr:hover td{background:#f7faf7}
.blank{color:#93a49b}
.q{background:#f7faf7;border-left:3px solid var(--line);padding:.45rem .6rem;margin:.3rem 0 .45rem;font-size:.85rem;color:#33483f}
.q .zh{font-family:var(--mono);font-size:.8rem}
.method{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:.9rem 1rem;margin:.8rem 0}
.method h3{margin:0 0 .2rem;font-size:1.05rem}
.method .who{font-size:.86rem;color:#33483f}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:.8rem}
.cols ul{margin-left:1.05rem}
.cols .pros li::marker{color:var(--ok)}
.cols .cons li::marker{color:var(--bad)}
.steps{counter-reset:s;list-style:none;margin-left:0}
.steps li{counter-increment:s;padding-left:1.6rem;position:relative;margin:.3rem 0}
.steps li::before{content:counter(s);position:absolute;left:0;top:.05rem;width:1.15rem;height:1.15rem;border-radius:50%;background:var(--accent);color:#fff;font-size:.7rem;font-weight:700;display:grid;place-items:center}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.55rem .8rem;margin:.5rem 0}
details summary{cursor:pointer;font-weight:650;font-size:.92rem}
.tiers{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.45rem;margin:.55rem 0}
.tier{border:1px solid var(--line);border-radius:10px;padding:.5rem .6rem;background:#fbfcfa}
.tier .a{font-size:.74rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.tier .v{font-size:1.02rem;font-weight:700;font-variant-numeric:tabular-nums}
.tier .x{font-size:.76rem;color:var(--muted)}
.controls{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:.6rem 0}
.controls input,.controls select{font:inherit;font-size:.88rem;padding:.4rem .55rem;border:1px solid #bfcbc3;border-radius:9px;background:#fff;min-width:0}
.controls button{font:inherit;font-size:.86rem;padding:.4rem .7rem;border:1px solid var(--accent);background:var(--accent);color:#fff;border-radius:9px;cursor:pointer}
.controls button.ghost{background:#fff;color:var(--accent)}
.muted{color:var(--muted)}
.small{font-size:.84rem}
.mono{font-family:var(--mono);font-size:.82rem}
footer{border-top:1px solid var(--line);margin-top:2rem;padding:1.1rem 1rem 2rem;color:var(--muted);font-size:.84rem}
footer .in{max-width:1120px;margin:0 auto}
@media(max-width:720px){
  .cols{grid-template-columns:1fr}
  table{font-size:.83rem;min-width:520px}
  th,td{padding:.42rem .5rem}
  header.top .bar{padding:.45rem .8rem}
  main{padding:.9rem .8rem 2.5rem}
}
@media print{
  header.top{position:static}
  nav,.controls{display:none}
  .tablewrap{overflow:visible}
  table{min-width:0;font-size:.78rem}
  th.first,td.first{position:static;box-shadow:none}
  .method,.box,details{break-inside:avoid}
}
"""

JS = """
(function(){
  var q=document.getElementById('q'), t=document.getElementById('tbl'), c=document.getElementById('blankonly');
  if(t&&q){
    var rows=[].slice.call(t.tBodies[0].rows);
    function apply(){
      var v=(q.value||'').toLowerCase(), onlyBlank=c&&c.checked;
      rows.forEach(function(r){
        var ok=v?r.innerText.toLowerCase().indexOf(v)>-1:true;
        if(ok&&onlyBlank){ok=r.querySelectorAll('td .blank').length>0;}
        r.style.display=ok?'':'none';
      });
      var shown=rows.filter(function(r){return r.style.display!=='none'}).length;
      var n=document.getElementById('count'); if(n){n.textContent=shown+' of '+rows.length+' rows shown';}
    }
    q.addEventListener('input',apply); if(c){c.addEventListener('change',apply);}
    var b=document.getElementById('reset');
    if(b){b.addEventListener('click',function(){q.value='';if(c){c.checked=false;}apply();});}
    apply();
  }
})();
"""

NAV = [
    ("index.html", "Overview"),
    ("costs.html", "Costs $10k–$400k"),
    ("methods.html", "17 methods"),
    ("taxes.html", "Tax & reporting"),
    ("sources.html", "Sources verified"),
    ("audit.html", "Repo audit"),
    ("flagged.html", "Flagged for review"),
]


def shell(slug: str, title: str, desc: str, body: str) -> str:
    links = "".join(
        f'<a href="{u}"{" aria-current=page" if u == slug else ""}>{esc(t)}</a>'
        for u, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="bar"><b>China money · CNY → USD</b><span class="meta">Independent verification pass · {UPDATED} · research, not tax or legal advice</span></div>
  <nav aria-label="Sections">{links}</nav>
</header>
<main>
{body}
</main>
<footer><div class="in">
<p><strong>Scope and limits.</strong> Every source on this site was fetched and quoted on {UPDATED}; the quote shown is the text relied on. Values a provider or regulator does not publish are left blank and flagged — blank means unverified, not zero. No private account facts were used, no bank was contacted, no funds moved and no return filed. The {len(SRC)} sources here are a re-verification of load-bearing claims, not a legal opinion or a personalised tax computation.</p>
<p class="small">Session {SESSION} · <a href="sources.html">source ledger</a> · <a href="flagged.html">flags</a> · <a href="../COORDINATION.md">task board</a> · <a href="../index.html">repository hub</a></p>
</div></footer>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


# ----------------------------------------------------------------------------- pages
def page_index() -> str:
    m01_10 = cost("M01", 10_000)["published_usd"]
    m01_80 = cost("M01", 80_000)["published_usd"]
    rows = []
    for m in METHODS:
        cells = []
        for t in KEY_TIERS:
            c = cost(m["id"], t)
            v = money(c["published_usd"])
            if c["published_usd"] == 0.0:
                v = '$0.00<sup title="published fee; other costs unverified">†</sup>'
            cells.append(f'<td class="num">{v}</td>')
        bad = ' class="badrow"' if m["status"] != "lawful-conditional" else ""
        rows.append(f'<tr{bad}><td class="first"><b>{m["id"]}</b> {esc(m["name"].split("(")[0].strip())}</td>'
                    + "".join(cells) + "</tr>")
    glance = f"""
<div class="tablewrap"><table>
<caption>Published transfer-fee component only, USD, at each checkpoint. Fee model: HSBC China tariff (the only published per-wire schedule in the reviewed sources) — Premier/Advance individual. Another bank's tariff will differ. Blank = no provider publishes a fee (unverified, not free). † $0.00 published fee, but FX spread/travel are unpublished.</caption>
<thead><tr><th class="first">Method</th><th class="num">$10,000</th><th class="num">$50,000</th><th class="num">$100,000</th><th class="num">$200,000</th><th class="num">$400,000</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""

    constraints = []
    for m in METHODS:
        c4 = cost(m["id"], 400_000)
        constraints.append(f'<tr><td class="first"><b>{m["id"]}</b></td><td>{esc(c4["constraint"])}</td><td>{esc(c4["unverified"])}</td></tr>')
    ctable = ('<div class="tablewrap"><table><thead><tr><th class="first">Method</th>'
              '<th>Constraint to move $400,000</th><th>Not verified / not published</th></tr></thead>'
              f'<tbody>{"".join(constraints)}</tbody></table></div>')

    body = f"""
<h1>Getting money out of China with the least lawful penalty</h1>
<p class="lede">A US citizen's balance sits in a Chinese bank. This dashboard answers three questions in order: <strong>what is actually being taxed</strong>, <strong>which routes exist</strong>, and <strong>what each route costs from $10,000 to $400,000</strong> — with a link to the primary document behind every number, and blanks where nothing official exists.</p>

<div class="box answer">
<h2>The answer in 60 seconds</h2>
<ol>
<li><strong>There is no "conversion tax" in either country.</strong> The PRC's FX rules impose document, quota and authenticity requirements plus evasion penalties — not a tax on exchanging currency ({src_link("VS06", "FX Regulations")}, {src_link("VS08", "PBOC Decree 3")}). The IRS taxes income, not conversions ({src_link("VS15", "26 USC §988")}).</li>
<li><strong>What feels like a penalty is five separate things</strong> — PRC income tax owed when the money was earned; the bank's FX spread; wire fees; US residual tax (with foreign tax credit / FEIE); and reporting penalties if FBAR/Form 8938/FinCEN 105 are missed. Each has its own fix. See <a href="taxes.html">Tax &amp; reporting</a>.</li>
<li><strong>Least-friction route: documented current-account income → bank conversion + wire (M01).</strong> You need your passport plus source-of-funds materials <em>including PRC tax records</em> for the amount ({src_link("VS01", "SAFE 2026 FAQ")}). If the underlying PRC tax was never paid, resolve that first — that is income tax, not a conversion charge.</li>
<li><strong>Cheapest published wire fee:</strong> HSBC Private Banking individual customers are published <strong>Free</strong>; Premier/Advance pay 0.1% (min ¥100, max ¥500) plus a ¥120 cable ({src_link("VS13", "tariff 2.2.4.1–2.2.4.2")}). At the IRS 2025 average rate of 7.129 that is <strong>{money(m01_10)} at $10,000</strong>, capped at <strong>{money(m01_80)}</strong> from about $80,000 upward. Same-name HSBC Global Transfer is <strong>free</strong> for Premier/Private Banking, USD 20 per transfer for Advance (2.2.6.1).</li>
<li><strong>The $50,000/year quota is not your route</strong> unless you hold a PRC Foreign Permanent Resident ID Card ({src_link("VS04", "SAFE 2024 FAQ")}); it is an annual total for domestic individuals and card holders ({src_link("VS02", "Implementing Rules Art. 2")}).</li>
<li><strong>Never</strong> split the quota, use crypto/stablecoin bridges, underground banks or fabricated documents. Conversion between RMB and virtual currency inside China is an illegal financial activity ({src_link("VS12", "Yinfa [2026] 42")}) and FX evasion carries fines of up to 30% — or 30% to 100% in serious cases ({src_link("VS06", "Arts. 39–45")}).</li>
</ol>
</div>

<div class="kpis">
  <div class="kpi"><p class="n">{len(METHODS)}</p><p class="l">methods catalogued</p><p class="s">{len(LAWFUL)} lawful-conditional · {len(REJECTED)} rejected as unlawful</p></div>
  <div class="kpi"><p class="n">{len(TIERS)}</p><p class="l">amount tiers</p><p class="s">$10,000 → $400,000 in $10,000 steps</p></div>
  <div class="kpi"><p class="n">{N_ROWS:,}</p><p class="l">cost cells checked</p><p class="s">{FLAGGED_ROWS} left blank on purpose (no published fee)</p></div>
  <div class="kpi"><p class="n">{len(SRC)}</p><p class="l">sources re-fetched {UPDATED}</p><p class="s">quote + URL on every row</p></div>
  <div class="kpi"><p class="n">{len(FLAGS)}</p><p class="l">open flags</p><p class="s">published, not resolved by guessing</p></div>
</div>

<h2>Cost at a glance: what is published</h2>
<p class="small muted">Only the fee component a provider actually publishes. All-in cost = this + FX spread + intermediary/recipient charges + any tax, and the last three are not published anywhere in the reviewed sources. Full 40-tier ladder: <a href="costs.html">Costs</a>.</p>
{glance}

<div class="box warn">
<strong>Read this before using the numbers.</strong> The USD figures restate CNY-denominated tariffs at <strong>7.129 CNY/USD</strong>, the IRS 2025 yearly average ({src_link("VS14", "IRS")}) — a reporting convention, not a live quote. The IRS states it has no official exchange rate. A single wire of $400,000 is also an assumption: banks may split large remittances, which multiplies per-wire fees without changing the caps. Neither the bank's FX spread nor correspondent/recipient charges are published, so no all-in USD cost is asserted. See <a href="flagged.html">Flagged for review</a>.
</div>

<h2>What binds each route at $400,000</h2>
{ctable}

<h2>What to ask the bank, in writing</h2>
<div class="box">
<ol>
<li>Which tax, taxpayer, period and legal basis is the hold about — a tax already assessed, a tax certificate you must supply, an FX eligibility question, or a bank fee? Request the refusal in writing.</li>
<li>Which FX category applies to my balance (documented current-account income under Huifa [2020] No. 14 Art. 59, or the annual facilitation quota)?</li>
<li>List the source-of-funds documents you will accept, including the PRC tax records.</li>
<li>Provide an executable quote: applied CNY/USD rate, sender fee, cable, correspondent/intermediary charges and the recipient bank's charge.</li>
<li>Confirm the customer segment your tariff applies to — HSBC's published wire fee is free for Private Banking individuals and 0.1% (min ¥100 / max ¥500) + ¥120 cable for Premier/Advance.</li>
</ol>
</div>

<h2>Go deeper</h2>
<div class="cards">
<a class="card" href="costs.html"><strong>Costs · $10,000 → $400,000</strong><span>17 methods × 40 tiers</span><em>Mobile cards for the five checkpoints, then the full 680-row ladder and CSV.</em></a>
<a class="card" href="methods.html"><strong>All 17 methods</strong><span>pros · cons · step by step</span><em>13 lawful-conditional routes and 4 rejected ones, each with its primary source.</em></a>
<a class="card" href="taxes.html"><strong>Tax &amp; reporting</strong><span>the five penalty layers</span><em>PRC IIT, US FTC/FEIE, FBAR/8938/FinCEN 105 thresholds, and §988(e).</em></a>
<a class="card" href="sources.html"><strong>Sources verified today</strong><span>{len(SRC)} documents · quotes</span><em>What was fetched on {UPDATED}, the exact text relied on, and the link.</em></a>
<a class="card" href="audit.html"><strong>Repository audit</strong><span>cross-site reconciliation</span><em>Count drift, stale figures and overbroad wording found in the existing sites.</em></a>
<a class="card" href="flagged.html"><strong>Flagged for review</strong><span>{len(FLAGS)} open items</span><em>Every value that could not be confirmed, published instead of guessed.</em></a>
</div>
"""
    return shell("index.html", "China money · CNY → USD verified dashboard",
                 "Source-verified CNY to USD repatriation dashboard: 17 methods, costs from $10,000 to $400,000, taxes and reporting, with blanks where nothing is published.", body)


def page_costs() -> str:
    # Mobile-first checkpoint cards
    cards = []
    for m in METHODS:
        tiers = "".join(
            f'<div class="tier"><div class="a">{money(t, 0)}</div>'
            f'<div class="v">{money(cost(m["id"], t)["published_usd"]) if cost(m["id"], t)["published_usd"] is not None else "—"}</div>'
            f'<div class="x">{esc(cost(m["id"], t)["constraint"])}</div></div>'
            for t in KEY_TIERS)
        badge = ('<span class="badge b-bad">rejected</span>' if m["status"] != "lawful-conditional"
                 else '<span class="badge b-ok">lawful, conditional</span>')
        cards.append(f'<div class="method"><h3>{m["id"]} · {esc(m["name"])} {badge}</h3>'
                     f'<p class="small muted">{esc(ledger["method_notes"][m["id"]])}</p>'
                     f'<div class="tiers">{tiers}</div></div>')

    # Full ladder rows
    rows = []
    for m in METHODS:
        for t in TIERS:
            c = cost(m["id"], t)
            fine_std, fine_ser = fine(t)
            fee_txt = money(c["published_usd"])
            if c["published_usd"] == 0.0:
                fee_txt = "$0.00 <span class=\"muted small\">†</span>"
            fine_txt = (f"{money(fine_std, 0)} / {money(fine_ser, 0)}" if m["status"] != "lawful-conditional" else "")
            rows.append(
                f'<tr data-m="{m["id"]}" data-a="{t}"><td class="first"><b>{m["id"]}</b></td>'
                f'<td class="num">{money(t, 0)}</td>'
                f'<td class="num">{cny_of(t):,.0f}</td>'
                f'<td class="num">{fee_txt}</td>'
                f'<td>{esc(c["constraint"])}</td>'
                f'<td class="num">{fine_txt}</td>'
                f'<td class="small">{esc(c["unverified"])}</td>'
                f'<td class="small">{src_links(ledger["method_sources"][m["id"]][:3])}</td></tr>')
    full = "".join(rows)

    body = f"""
<h1>Costs: $10,000 → $400,000 in $10,000 steps</h1>
<p class="lede">Most important first: the five checkpoints as mobile cards, then the complete 680-row ladder. Every published fee is recomputed from the tariff text, not copied; every unpublished component is blank and flagged. <a href="exports/costs.csv">Download the ladder (CSV)</a>.</p>

<div class="box warn">
<strong>What "published fee" means here.</strong> It is the transfer/issuance fee a provider prints in a public tariff (for HSBC, 2.2.4.1–2.2.4.2). It is <em>not</em> the all-in cost: the FX spread, correspondent and recipient bank charges, and any tax are separate. USD restatement uses 7.129 CNY/USD ({src_link("VS14", "IRS 2025 average")}). Where a method publishes nothing, the cell stays blank.</p>
<p><strong>Bank used for the fee model:</strong> HSBC China, because it is the only institution in the reviewed sources that publishes a complete per-wire schedule. If your account is at ICBC, BOC, CCB, CMB or another bank, its tariff (and its minimum/maximum and cable charge) may differ and must be obtained directly — the arithmetic template here still applies.</p>
</div>

<h2>Checkpoints by method</h2>
{''.join(cards)}

<h2>Full ladder · {N_ROWS:,} rows</h2>
<div class="controls">
  <input id="q" type="search" placeholder="Filter: M01, wire, HSBC, 250000…" aria-label="Filter cost rows">
  <select id="blankonly" aria-label="Show only unpublished rows"><option value="">All rows</option><option value="1">Rows with a blank fee</option></select>
  <button id="reset" class="ghost" type="button">Reset</button>
  <span id="count" class="small muted">{N_ROWS:,} rows</span>
</div>
<div class="tablewrap"><table id="tbl">
<caption>Fee column: published HSBC China per-wire fee for Premier/Advance individuals only — not an all-in cost and not your bank's tariff unless you bank with HSBC. Fine columns apply only to the four rejected methods (30% standard / 100% serious-case cap under FX Regulations Arts. 39–45). "†" = published fee is zero but other costs are unpublished.</caption>
<thead><tr><th class="first">Method</th><th class="num">USD</th><th class="num">CNY @7.129</th><th class="num">Published fee USD</th><th>Binding constraint</th><th class="num">Fine band USD</th><th>Not verified</th><th>Source</th></tr></thead>
<tbody>{full}</tbody></table></div>

<h2>Method of computation</h2>
<div class="box">
<ul>
<li><strong>M01</strong>: one HSBC Premier/Advance telegraphic transfer. Fee = min(max(0.1% × CNY amount, ¥100), ¥500) + ¥120 cable, ÷ 7.129. Private Banking individual customers: published Free (0.00).</li>
<li><strong>M02</strong>: annual quota = $50,000 per calendar year, so whole years = ⌈amount ÷ 50,000⌉; the fee is summed tranche by tranche, each capped at ¥500 + ¥120.</li>
<li><strong>M03</strong>: Global Transfer to your own overseas HSBC account — Free for Private Banking and Premier; Advance CNY 145 indicative, actual USD 20 per transfer, with the per-transfer limit unpublished (blank).</li>
<li><strong>M06</strong>: RMB 100,000 per person per calendar year ({src_link("VS05", "Huifa [2017] 29")}), so years = ⌈CNY ÷ 100,000⌉; withdrawals assume the RMB 10,000 per card per day ceiling.</li>
<li><strong>M07</strong>: USD 5,000 per trip without a permit, so trips = ⌈USD ÷ 5,000⌉ ({src_link("VS07", "Huifa [2003] 102")}). Published counter fee is zero; spread/travel are not published.</li>
<li><strong>M08</strong>: CNY 20,000 per trip, so trips = ⌈CNY ÷ 20,000⌉ ({src_link("VS09", "PBC")}, explanatory Q&amp;A — instrument number flagged).</li>
<li><strong>M09</strong>: ID-only reconversion is capped at USD 500 per day ({src_link("VS03", "SAFE 2026 FAQ 10")}), so days = ⌈USD ÷ 500⌉, and the memo route cannot exceed the original exchange amount (unknown).</li>
<li><strong>M10/M11</strong>: SAFE-approved emigrant/inheritor transfers, staged over up to two years for amounts ≥ ¥200,000 ({src_link("VS10", "PBC 2004 rules")}); no fee schedule is published.</li>
<li><strong>M14–M17</strong>: not prices at all — the statutory fine band (30% standard, up to 100% in serious cases) on the amount moved unlawfully ({src_link("VS06", "FX Regulations")}). Losses on crypto or underground arrangements are additional and uncapped.</li>
</ul>
</div>
"""
    return shell("costs.html", "Costs $10,000–$400,000 · China money dashboard",
                 "Every CNY to USD method priced at $10,000 steps to $400,000 with published fees recomputed from tariff text and blanks where nothing is published.", body)


def page_methods() -> str:
    out = []
    for m in METHODS:
        badge = ('<span class="badge b-bad">rejected · unlawful</span>' if m["status"] != "lawful-conditional"
                 else '<span class="badge b-ok">lawful, conditional</span>')
        pros = "".join(f"<li>{esc(p)}</li>" for p in m["pros"])
        cons = "".join(f"<li>{esc(c)}</li>" for c in m["cons"])
        steps = "".join(f"<li>{esc(s)}</li>" for s in m["steps"])
        ids = ledger["method_sources"][m["id"]]
        out.append(f"""<section class="method" id="{m['id']}">
<h3>{m['id']} · {esc(m['name'])} {badge}</h3>
<p class="who"><strong>Who can use it:</strong> {esc(m['who'])}</p>
<p class="small">{esc(ledger['method_notes'][m['id']])}</p>
<div class="cols"><div><h3>Pros</h3><ul class="pros">{pros}</ul></div><div><h3>Cons</h3><ul class="cons">{cons}</ul></div></div>
<h3>Step by step</h3><ol class="steps">{steps}</ol>
<p class="small"><strong>Verified sources for this row:</strong> {src_links(ids)}</p>
</section>""")

    body = f"""
<h1>All {len(METHODS)} ways to turn CNY into USD</h1>
<p class="lede">{len(LAWFUL)} lawful-conditional routes and {len(REJECTED)} rejected as unlawful. Each entry lists who can use it, its pros and cons, the execution steps, and the primary documents checked for that row on {UPDATED}. Costs for every method: <a href="costs.html">Costs</a>.</p>
<div class="box warn"><strong>Selection logic, not a recommendation.</strong> A route is "lawful-conditional" only in the sense that the reviewed instruments describe a legal way to use it, subject to eligibility the bank must confirm. Nothing here establishes that your balance qualifies. The four rejected routes are listed because the brief asked for every way money is moved — not because they are options.</div>
{''.join(out)}
"""
    return shell("methods.html", "All 17 CNY→USD methods · pros, cons, steps",
                 "Seventeen documented CNY to USD conversion and repatriation routes with pros, cons, execution steps and primary sources.", body)


def page_taxes() -> str:
    body = f"""
<h1>Tax &amp; reporting: breaking down the "conversion penalty"</h1>
<p class="lede">No reviewed instrument imposes a tax on the act of converting CNY to USD. What people experience as a penalty decomposes into five layers. Four of them are avoidable or reducible with documents; one (unpaid PRC income tax) is not.</p>

<h2>Layer by layer</h2>
<div class="tablewrap"><table>
<thead><tr><th class="first">Layer</th><th>What it actually is</th><th>Verified anchor</th><th>What changes it</th></tr></thead>
<tbody>
<tr><td class="first"><b>1. PRC income tax</b></td><td>IIT on the income when it arose: 3–45% comprehensive, 5–35% business, 20% flat on dividends/asset transfers/incidental income.</td><td>{src_link("VS11", "IIT Law Art. 3")}</td><td>Whether tax was withheld/paid when earned. Banks ask for tax records before converting documented income ({src_link("VS01", "SAFE FAQ")}).</td></tr>
<tr><td class="first"><b>2. Bank FX spread</b></td><td>The margin between the board rate and mid-market — the largest real cost on a large conversion.</td><td>Not published by banks in the reviewed documents; HSBC tariff Important Note 7 excludes third-party charges.</td><td>Segment, channel, currency and negotiation. Must be obtained as an executable quote — left blank here.</td></tr>
<tr><td class="first"><b>3. Transfer fees</b></td><td>Published per-wire charges: HSBC Premier/Advance 0.1% (min ¥100, max ¥500) + ¥120 cable; Private Banking individual free.</td><td>{src_link("VS13", "tariff 2.2.4.1–2")}</td><td>Customer segment; number of wires; optional "Pay Exact" ¥200.</td></tr>
<tr><td class="first"><b>4. US residual tax</b></td><td>Worldwide income is taxable in the US; moving your own already-taxed money is not new income.</td><td>{src_link("VS24", "IRS FTC")} · {src_link("VS19", "Form 2555 instructions (FEIE 2026: $132,900)")}</td><td>Foreign tax credit (only against US tax on the same income) or FEIE (earned income only, and then no credit for excluded tax).</td></tr>
<tr><td class="first"><b>5. Reporting penalties</b></td><td>FBAR ($10,000 aggregate), Form 8938, FinCEN 105 (&gt;$10,000 cash carried).</td><td>{src_link("VS17", "FBAR")} · {src_link("VS18", "8938 vs FBAR")} · {src_link("VS23", "CBP")}</td><td>Filing. Civil maximums are inflation-adjusted ({src_link("VS16", "31 CFR 1010.821")}).</td></tr>
</tbody></table></div>

<h2>Currency gain: when a conversion can itself create US tax</h2>
<div class="box">
<p>For an individual's <em>personal</em> transaction, exchange-rate gain is not recognised if it is $200 or less; above that the exclusion does not apply ({src_link("VS15", "26 USC §988(e)(2)")}). The statute is the 2024 GPO compilation — later amendments are not reflected here, so confirm the current edition. Basis and holding history of the RMB are private facts and were not assumed.</p>
<p>The IRS has no official exchange rate and generally accepts any consistently used posted rate ({src_link("VS14", "IRS")}). A "conversion penalty" calculated by multiplying the balance by a tax rate is therefore not supported by any reviewed text.</p>
</div>

<h2>US reporting thresholds (verified today)</h2>
<div class="tablewrap"><table>
<thead><tr><th class="first">Form</th><th>Threshold</th><th>Due</th><th>Source</th></tr></thead>
<tbody>
<tr><td class="first"><b>FBAR</b> (FinCEN 114)</td><td>Aggregate foreign accounts exceed <b>$10,000</b> at any time in the calendar year</td><td>Apr 15, automatic extension to Oct 15</td><td>{src_link("VS17")}</td></tr>
<tr><td class="first"><b>Form 8938</b> (living outside US)</td><td>Unmarried: &gt;$200,000 year-end or &gt;$300,000 anytime; married joint: &gt;$400,000 / &gt;$600,000</td><td>With the return</td><td>{src_link("VS18")}</td></tr>
<tr><td class="first"><b>FinCEN 105</b></td><td>Currency/monetary instruments over <b>$10,000</b> into or out of the US</td><td>At the border, electronically</td><td>{src_link("VS23")}</td></tr>
<tr><td class="first"><b>Civil penalty maximums</b></td><td>FBAR non-willful <b>$16,536</b>; willful <b>$165,353</b> (assessed on/after 2025-01-17)</td><td>—</td><td>{src_link("VS16")}</td></tr>
</tbody></table></div>

<h2>PRC side: the limits that actually bind</h2>
<div class="tablewrap"><table>
<thead><tr><th class="first">Rule</th><th>Limit</th><th>Source</th></tr></thead>
<tbody>
<tr><td class="first">Annual FX facilitation total</td><td>USD 50,000 per person per year, for domestic individuals — and for foreign individuals only with a PRC Foreign Permanent Resident ID Card</td><td>{src_link("VS02")} · {src_link("VS04")}</td></tr>
<tr><td class="first">Documented current-account income</td><td>No numeric cap appears in the cited guidance; ID + source-of-funds incl. tax vouchers required, bank review decides</td><td>{src_link("VS01")} · {src_link("VS02", "Art. 13")}</td></tr>
<tr><td class="first">Reconversion of unused RMB</td><td>Original memo, 24 months; ID-only same-day up to USD 500 (USD 1,000 restricted-area)</td><td>{src_link("VS03")}</td></tr>
<tr><td class="first">Cash carried out (FX)</td><td>≤ USD 5,000 no permit; 5,000–10,000 bank permit; &gt;10,000 in principle not allowed</td><td>{src_link("VS07")}</td></tr>
<tr><td class="first">Cash carried out (RMB)</td><td>CNY 20,000 per person per trip</td><td>{src_link("VS09")} (Q&amp;A, instrument flagged)</td></tr>
<tr><td class="first">Overseas ATM</td><td>RMB 100,000 per person per calendar year; RMB 10,000 per card per day</td><td>{src_link("VS05")}</td></tr>
<tr><td class="first">Prohibited</td><td>Splitting to evade limits; fabricated documents; fiat↔virtual-currency business</td><td>{src_link("VS08", "Art. 7")} · {src_link("VS12")}</td></tr>
</tbody></table></div>

<h2>What this page does not do</h2>
<div class="box warn">
<p>It does not compute your tax. The PRC tax already paid, the source and date of the balance, your residence days, other foreign accounts, filing history and the property/employment character of the money are all unknown. A number presented as "your tax" would be invented. The actionable substitute is the document list in <a href="methods.html#M01">M01</a> and the bank questions on the <a href="index.html">overview</a>.</p>
</div>
"""
    return shell("taxes.html", "Tax and reporting breakdown · China money dashboard",
                 "Five-layer breakdown of the CNY to USD conversion penalty: PRC IIT, FX spread, wire fees, US FTC/FEIE and FBAR/8938/FinCEN 105 reporting.", body)


def page_sources() -> str:
    rows = []
    for s in ledger["sources"]:
        cls = "b-ok" if s["status"] == "verified" else "b-warn"
        label = "verified" if s["status"] == "verified" else "verified · limited"
        rows.append(f"""<tr id="{s['id']}">
<td class="first"><b>{s['id']}</b></td>
<td><a href="{esc(s['url'])}" target="_blank" rel="noopener noreferrer">{esc(s['title'])}</a>
<div class="small muted">{esc(s['publisher'])} · document date: {esc(s['doc_date'])}</div>
<div class="q">{esc(s['quote'])}</div></td>
<td><span class="badge {cls}">{label}</span><div class="small muted">fetched {esc(s['retrieved'])}</div></td>
<td class="small">{esc(s['supports'])}</td></tr>""")

    body = f"""
<h1>Sources: fetched, quoted, linked</h1>
<p class="lede">Each row below was retrieved on {UPDATED} and the quoted text is what this dashboard relies on. "Verified" means the fetched document states the proposition; "verified · limited" means it supports a narrower claim than the one usually attributed to it, and the limitation is stated. Nothing is cited from memory.</p>
<div class="box ok"><strong>What changed in this pass.</strong> Earlier sites in this repository disclosed that their checks were structural ("citation coverage"), not substantive. This pass re-read the primary documents themselves and records the exact sentence used, so a reviewer can compare the quote with the link without re-deriving the claim.</div>
<div class="tablewrap"><table>
<thead><tr><th class="first">ID</th><th>Document and quoted text</th><th>Status</th><th>What it supports</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

<h2>Source hierarchy used</h2>
<div class="box">
<ul>
<li><strong>Primary regulator / statute:</strong> SAFE, PBOC, State Council, State Taxation Administration, IRS, CBP, FinCEN/eCFR, GPO. These govern the claim.</li>
<li><strong>Provider primary documents:</strong> HSBC China tariff, Wise help centre, Western Union China page. These state <em>that provider's</em> fees and limits — not a regulator's rule, and not your account's terms.</li>
<li><strong>IRS exchange-rate convention:</strong> the 2025 yearly average is used only to restate CNY fees. It is neither a live rate nor the rate your bank will apply.</li>
</ul>
<p class="small muted">Not used as authority: news articles, blogs, forums, tax-preparer marketing, or any AI-generated figure. Where the only available statement was secondary, the value was left blank.</p>
</div>

<h2>Known weaknesses of these sources</h2>
<div class="box warn">
<ul>
<li>The eCFR is authoritative but <em>not</em> the official print edition ({src_link("VS16")}); the GPO annual CFR is. 26 USC §988 here is the 2024 edition ({src_link("VS15")}).</li>
<li>The IRS FEIE web page is stale — it still lists 2020–2023 amounts ({src_link("VS20")}); the 2026 figure comes from the Form 2555 instructions ({src_link("VS19")}).</li>
<li>The RMB 20,000 carry limit is supported by a 2004 PBC explanatory Q&amp;A ({src_link("VS09")}), not by re-reading Announcement [2004] No. 18 itself. The instrument number is flagged.</li>
<li>The HSBC PDF contains an internal Chinese-language header dated 2024 alongside the 31 October 2026 effective date; the tariff is used as published but that inconsistency is flagged.</li>
</ul>
</div>
"""
    return shell("sources.html", "Verified source ledger · China money dashboard",
                 "Twenty-four primary documents fetched and quoted on 2026-11-10, with the exact text relied on and links for manual review.", body)


AUDIT = [
    ("AU-01", "Cross-site method-count drift",
     "Sites in this repository state 22, 20, 18, 17 and 13 methods/legal routes for the same question. Each has its own scope note, but a reader landing on the hub cannot tell which count is canonical.",
     "Open / documented", "This dashboard reconciles to the 17-method set in repatriate/data/methods.json, which is the only set with a complete 40-tier cost ladder."),
    ("AU-02", "Discounting the fee illustration's customer segment",
     "The headline \"$30.86–$86.97 per wire\" is HSBC Premier/Advance. HSBC's own tariff makes telegraphic transfer issuance and cable charges Free for Private Banking individual customers, so the illustration does not apply to that segment.",
     "Corrected here", "Segment is stated on every cost row; the Private Banking case is shown separately as $0.00."),
    ("AU-03", "Stale IRS FEIE page cited for a current figure",
     "irs.gov's FEIE page still prints 2020–2023 amounts ($120,000 for 2023). Any 2026 amount derived from it would be wrong.",
     "Flagged", "2026 amount taken from Form 2555 instructions ($132,900) and the stale page is cited only as evidence of staleness."),
    ("AU-04", "Absence of a cap presented as an entitlement",
     "SAFE's guidance for foreign individuals' documented income states documents, not a dollar ceiling. Several pages summarise this as \"no annual cap\", which is an inference from silence, not an affirmative unlimited right.",
     "Flagged", "Rendered as \"no numeric cap appears in the cited text; the bank's review decides\"."),
    ("AU-05", "\"$0\" published fees for cash routes",
     "Method pages show a published bank fee of zero for buying/carrying cash. Spread, travel and risk are not zero and are not published; a reader can misread $0 as free.",
     "Flagged", "Marked \"$0.00 †\" with the unverified components named in the same row."),
    ("AU-06", "Mutually inconsistent dashboards",
     "docs/, site/, portal/, repatriate/, ladder/, briefing/ and audit-*/ each present overlapping claim sets with different corrections applied. Several earlier pages were superseded rather than withdrawn.",
     "Open / documented", "This site links the repository hub and states its own scope; it does not silently re-endorse other pages."),
    ("AU-07", "The \"no conversion tax\" headline is true but incomplete",
     "The statement is supported for the act of conversion, but it reads as an all-clear. The real exposure is PRC income tax already owed, FX spread, US reporting penalties and FX-evasion fines.",
     "Corrected here", "Five-layer decomposition on the Tax page, each layer separately sourced."),
    ("AU-08", "Unrealistic single-wire assumption at the top of the ladder",
     "The $400,000 row assumes one wire. Banks commonly split large remittances; each extra wire re-applies the ¥100 floor (or ¥500 cap) and ¥120 cable.",
     "Flagged", "Single-wire assumption disclosed; multi-wire totals are not invented."),
    ("AU-09", "Bank tariff cited as if it were the cost of the transfer",
     "An HSBC tariff line is a published charge of one bank for one segment, excluding correspondent, recipient and third-party charges (tariff Important Note 7) and excluding taxes.",
     "Corrected here", "\"Published fee\" is a named column, never presented as all-in cost."),
    ("AU-10", "No live link-health check in prior CI",
     "Earlier verifiers checked that a URL string was present and looked official, not that the document still exists or says what is claimed. A 404 or rewritten page would pass.",
     "Improved", "24 documents fetched and quote-checked by hand on 2026-11-10; this is a point-in-time check, not continuous monitoring."),
    ("AU-11", "Instrument-number precision on the RMB carry limit",
     "The CNY 20,000 limit is attributed to PBOC Announcement [2004] No. 18, but the fetched PBC page is an explanatory Q&A that states the 20,000 figure without reproducing the announcement.",
     "Flagged", "Marked \"verified · limited\" with the limitation on the source row."),
    ("AU-12", "Different exchange-rate conventions across pages",
     "Some pages restate CNY fees at 6.9, others at 7.129. Mixing conventions changes USD figures by several percent and makes cross-page comparison unreliable.",
     "Corrected here", "One rate (7.129, IRS 2025 average) declared once and repeated in every table footnote."),
]


def page_audit() -> str:
    rows = "".join(
        f'<tr><td class="first"><b>{i}</b></td><td><b>{esc(t)}</b><div class="small">{esc(d)}</div></td>'
        f'<td><span class="badge {"b-warn" if s.startswith("Flagged") or s.startswith("Open") else "b-ok"}">{esc(s)}</span></td>'
        f'<td class="small">{esc(a)}</td></tr>'
        for i, t, d, s, a in AUDIT)
    body = f"""
<h1>Repository audit: what the existing sites get right, and where they drift</h1>
<p class="lede">This repository contains seven prior dashboards built by different sessions. They are preserved, not overwritten. This page records what an independent read of the published claims found on {UPDATED}, and what this dashboard does differently. Nothing below is an accusation of bad faith — several items are already flagged by their own authors.</p>
<div class="box"><strong>Scope.</strong> Read-only review of the checked-in HTML/data plus the primary sources in the <a href="sources.html">ledger</a>. I did not re-verify every row of every prior site; structural checks in those repos do not establish factual accuracy, and this audit does not claim to be exhaustive.</div>
<div class="tablewrap"><table>
<thead><tr><th class="first">ID</th><th>Observation and evidence</th><th>Status</th><th>Handling</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Structural observations</h2>
<div class="box">
<ul>
<li><strong>Seven dashboards, one question.</strong> <span class="mono">docs/ · site/ · portal/ · repatriate/ · ladder/ · briefing/ · audit-*/</span> — each with its own verifier and CI job. Coverage is impressive; coherence is not.</li>
<li><strong>Verifier quality varies.</strong> The strongest existing checks (row counts, citation presence, local links, arithmetic recomputation) prove structure. None of them can prove that a cited page still says what the row claims — the gap this pass targets.</li>
<li><strong>Repeated corrections without retraction.</strong> Later sessions corrected earlier claims by adding new pages rather than amending the old ones, so a search engine or a direct link can still land on superseded wording.</li>
<li><strong>Deterministic builds are enforced.</strong> <span class="mono">verify-ladder</span> regenerates output and fails on any diff; this session kept that contract and regenerated the ladder inventory after adding files.</li>
</ul>
</div>

<h2>What this dashboard adds</h2>
<div class="box ok">
<ol>
<li>Quote-level verification: {len(SRC)} documents fetched on {UPDATED}, with the exact sentence shown next to the link.</li>
<li>A single cost ladder (17 × 40 = {N_ROWS:,} cells) recomputed independently, with the fee model written out line by line.</li>
<li>Explicit separation of published fee, binding constraint, fine exposure and unverified spread — so a "$0" cannot be read as "free".</li>
<li>Segment-correct HSBC fees (Private Banking free; Premier/Advance 0.1% + cable).</li>
<li>Blank-by-default policy for every value no source publishes, with the reason on the row.</li>
</ol>
</div>
"""
    return shell("audit.html", "Repository audit · China money dashboard",
                 "Independent review of the repository's published CNY to USD claims: count drift, stale figures, fee-segment errors and structural-only verification.", body)


FLAGS = [
    ("F01", "Your PRC tax history and the source of the balance are unknown", "The single largest determinant of both PRC tax and route eligibility. No amount is computed.", "Blocking for any personal number"),
    ("F02", "Bank FX spread and all-in cost are unpublished", "No reviewed document publishes the spread or correspondent/recipient charges. Every cost row therefore stops at the published fee.", "Blank by design"),
    ("F03", "Published wire fee depends on customer segment", "HSBC: Private Banking individual free; Premier/Advance 0.1% (min ¥100, max ¥500) + ¥120 cable. The illustration applies to the latter.", "Stated on each row"),
    ("F04", "\"No numeric cap\" is an inference from silence", "SAFE's documented-income guidance lists documents, not a ceiling. It does not create an unlimited entitlement; bank review decides.", "Wording limited"),
    ("F05", "The USD 50,000 quota needs a PRC permanent-resident card", "Foreign individuals without a PRC Foreign Permanent Resident ID Card do not get the annual facilitation quota (SAFE 2024 FAQ).", "Verified, published"),
    ("F06", "Single-wire assumption at large amounts", "The $200k/$400k rows assume one wire. Splitting multiplies per-wire floors; splitting to evade limits is separately prohibited.", "Disclosed"),
    ("F07", "Published $0.00 for cash routes is not zero cost", "Spread, travel and risk are unpublished and not zero.", "Marked †"),
    ("F08", "Wise, Western Union and card-issuer fees are not published", "Wise quotes only in-app; WU publishes no schedule; card ATM fees vary by issuer.", "Blank"),
    ("F09", "Emigrant/inheritor transfers are staged over up to two years", "Amounts ≥ ¥200,000 are remitted in instalments under the 2004 rules — and only if you fall into those categories.", "Published constraint"),
    ("F10", "Stale IRS FEIE page", "irs.gov's FEIE page still shows 2020–2023 amounts. 2026 figure ($132,900) comes from Form 2555 instructions.", "Flagged"),
    ("F11", "Statute editions are dated", "26 USC §988 is the 2024 GPO edition; eCFR is authoritative but unofficial.", "Flagged"),
    ("F12", "RMB-denominated limits move with the exchange rate", "CNY 100,000 ATM and CNY 20,000 carry limits converted at 7.129 are illustrations, not fixed USD amounts.", "Disclosed"),
    ("F13", "Cross-site count drift", "Other pages in this repository state 22/20/18/13 methods; this dashboard uses the 17-method set with the complete cost ladder.", "Reconciled here"),
    ("F14", "7.129 is a yearly average, not today's rate", "It is the IRS 2025 average for reporting; the IRS has no official rate. Your bank's rate will differ.", "Declared once, repeated"),
    ("F15", "Fines are exposure, not cost", "30% / 30–100% figures are statutory maximum bands for unlawful routes, not a price list; crypto losses are additional and uncapped.", "Labelled"),
    ("F16", "No bank was contacted; no account facts used", "Eligibility, tariff segment, limits and the hold itself can only be confirmed by your bank in writing.", "Scope limit"),
]


def page_flags() -> str:
    rows = "".join(
        f'<tr><td class="first"><b>{i}</b></td><td><b>{esc(t)}</b></td><td class="small">{esc(d)}</td>'
        f'<td><span class="badge b-warn">{esc(s)}</span></td></tr>'
        for i, t, d, s in FLAGS)
    body = f"""
<h1>Flagged for review</h1>
<p class="lede">Everything that could not be confirmed from a primary source, or that a reader could reasonably misread, is listed here rather than smoothed over. These items do not block publication; they are the honest boundary of what is known.</p>
<div class="box warn"><strong>Blank ≠ zero.</strong> In every table on this site, an em dash means no retrieved primary document publishes that value. It does not mean the cost is nil.</div>
<div class="tablewrap"><table>
<thead><tr><th class="first">ID</th><th>Flag</th><th>Why it matters</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Also open, owned by other sessions</h2>
<div class="box">
<p>The repository's earlier dashboards publish their own review pages (F01–F15, FLG-01–FLG-13, N01–N09, G01–G05, C-series). They are preserved and not overwritten. Where this dashboard disagrees — the fee-segment illustration, the "no cap" wording, the stale FEIE citation, the $0 cash fees — the difference is recorded in the <a href="audit.html">repo audit</a> with the primary source that settles it.</p>
<p>Open pull requests #2, #12 and #17 from earlier sessions were not touched: their branches are outside this session's scope. The cost-increment request behind them is already published at 40 tiers on this site.</p>
</div>

<h2>How to close a flag</h2>
<div class="box ok">
<ol>
<li>Provide the bank's written, itemised quote (rate, sender fee, cable, correspondent, recipient) → F02, F03, F08 close.</li>
<li>Provide the PRC tax records for the balance → F01 partially closes and M01 eligibility can be assessed.</li>
<li>Confirm your HSBC segment and account type → F03 closes for your case.</li>
<li>Confirm your category (former PRC resident, inheritor, permanent-resident card holder) → M02/M10/M11 eligibility resolves.</li>
</ol>
<p class="small">Until then, this site will keep the cells blank.</p>
</div>
"""
    return shell("flagged.html", "Flagged for review · China money dashboard",
                 "Sixteen published flags: unverified spreads, segment-dependent fees, stale sources, dated statute editions and unknowns left blank on purpose.", body)


# ----------------------------------------------------------------------------- write
def main() -> None:
    (HERE / "assets").mkdir(exist_ok=True)
    (HERE / "exports").mkdir(exist_ok=True)
    (HERE / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    (HERE / "assets" / "app.js").write_text(JS, encoding="utf-8")

    pages = {
        "index.html": page_index(),
        "costs.html": page_costs(),
        "methods.html": page_methods(),
        "taxes.html": page_taxes(),
        "sources.html": page_sources(),
        "audit.html": page_audit(),
        "flagged.html": page_flags(),
    }
    for name, html in pages.items():
        (HERE / name).write_text(html, encoding="utf-8")

    with (HERE / "exports" / "costs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["method", "status", "amount_usd", "amount_cny_at_7.129", "published_fee_usd",
                    "binding_constraint", "fine_standard_30pct_usd", "fine_serious_cap_100pct_usd",
                    "unverified_components", "sources"])
        for m in METHODS:
            for t in TIERS:
                c = cost(m["id"], t)
                fine_std, fine_ser = fine(t)
                w.writerow([m["id"], m["status"], t, f"{cny_of(t):.2f}",
                            "" if c["published_usd"] is None else f"{c['published_usd']:.2f}",
                            c["constraint"],
                            "" if m["status"] == "lawful-conditional" else f"{fine_std:.2f}",
                            "" if m["status"] == "lawful-conditional" else f"{fine_ser:.2f}",
                            c["unverified"], ";".join(ledger["method_sources"][m["id"]])])
    print(f"built {len(pages)} pages, {N_ROWS} cost rows, {FLAGGED_ROWS} blank fees, {len(SRC)} sources, {len(FLAGS)} flags")


if __name__ == "__main__":
    main()
