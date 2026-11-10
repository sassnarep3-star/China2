#!/usr/bin/env python3
"""Build the consolidated CNY->USD dashboard for session arena/416f3c1b-china2.

All numbers come from data/*.json. Nothing is estimated: a value that has no
published source is rendered blank and marked unverified.
"""
from __future__ import annotations

import html
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"

S = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
M = json.loads((DATA / "methods.json").read_text(encoding="utf-8"))
C = json.loads((DATA / "costs.json").read_text(encoding="utf-8"))
F = json.loads((DATA / "findings.json").read_text(encoding="utf-8"))

SRC = {s["id"]: s for s in S["sources"]}
ROUTES = {r["id"]: r for r in M["routes"]}

RATE = C["rate_cny_per_usd"]
TIERS = list(range(C["tiers"]["start_usd"], C["tiers"]["end_usd"] + 1, C["tiers"]["step_usd"]))

NAV = [
    ("index.html", "Dashboard"),
    ("routes.html", "Methods"),
    ("costs.html", "Costs $10k-$400k"),
    ("tax.html", "Tax & penalties"),
    ("steps.html", "Step by step"),
    ("sources.html", "Sources"),
    ("audit.html", "Repo audit"),
    ("flagged.html", "Flagged for review"),
]
PAGE_TITLES = dict(NAV)


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def src_link(sid: str, label: str | None = None) -> str:
    s = SRC[sid]
    return (
        f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">'
        f"{esc(label or sid)}</a>"
    )


def src_list(ids) -> str:
    return " ".join(src_link(i) for i in ids)


def usd(x: float) -> str:
    return f"${x:,.2f}"


# ---------------------------------------------------------------- computations
def r01_fee_usd(usd_amount: int) -> dict:
    """HSBC Premier/Advance telegraphic transfer, published tariff only."""
    cfg = C["routes"]["R01"]
    cny = usd_amount * RATE
    pct = cfg["pct"] * cny
    clamped = min(max(pct, cfg["min_cny"]), cfg["max_cny"])
    total_cny = clamped + cfg["cable_cny"]
    return {
        "cny": cny,
        "pct_cny": pct,
        "clamped_cny": clamped,
        "total_cny": total_cny,
        "usd": total_cny / RATE,
        "pct_of_amount": (total_cny / RATE) / usd_amount * 100,
    }


def r02_fee_usd(usd_amount: int, segment: str) -> float:
    cfg = C["routes"]["R02"]
    return {"pb": cfg["usd_pb"], "premier": cfg["usd_premier"], "advance": cfg["usd_advance"]}[segment]


def r07(usd_amount: int) -> dict:
    cfg = C["routes"]["R07"]
    trips = math.ceil(usd_amount / cfg["per_trip_cap_usd"])
    return {"fee_usd": cfg["fee_usd"], "trips": trips, "feasible": trips == 1}


# ---------------------------------------------------------------- shell
def page(slug: str, title: str, body: str, subtitle: str = "") -> str:
    def _a(href, text):
        cls = ' class="on"' if href == slug else ""
        return f'<a href="{href}"{cls}>{esc(text)}</a>'

    nav = "".join(_a(h, t) for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China money</title>
<meta name="description" content="Source-linked research on converting CNY to USD as a U.S. citizen. Verified figures only; unknown values are blank and flagged.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap bar">
    <a class="brand" href="index.html">China money<span>CNY → USD, verified</span></a>
    <nav aria-label="Sections">{nav}</nav>
  </div>
  <div class="wrap"><p class="sub">{esc(subtitle or 'Official-source research · verified 10 November 2026 · not tax, legal or investment advice')}</p></div>
</header>
<main class="wrap">
{body}
</main>
<footer>
  <div class="wrap">
    <p><strong>Research, not advice.</strong> Every figure carries a link to the official page it came from. Where no official figure exists the cell is blank and published on <a href="flagged.html">Flagged for review</a>. Blank means unverified, never zero.</p>
    <p>Session <code>arena/416f3c1b-china2</code> · {len(S['sources'])} sources · {len(M['routes'])} methods · {len(TIERS)} cost tiers · <a href="sources.html">full source register</a></p>
  </div>
</footer>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


def table(headers, rows, cls="data", caption=None, first_sticky=False):
    ths = "".join(f"<th scope=\"col\">{h}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(cells) + "</tr>" for cells in rows)
    cap = f"<caption>{caption}</caption>" if caption else ""
    sticky = " sticky-first" if first_sticky else ""
    return (
        f'<div class="tw"><table class="{cls}{sticky}">{cap}'
        f"<thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>"
    )


def badge(status: str) -> str:
    labels = {
        "lawful-conditional": ("conditional", "Lawful if documents qualify"),
        "prohibited": ("stop", "Prohibited"),
        "conditional-unverified": ("warn", "Unverified"),
    }
    cls, text = labels[status]
    return f'<span class="badge {cls}">{esc(text)}</span>'


# ---------------------------------------------------------------- index
def build_index() -> str:
    top = [r for r in M["routes"] if r["status"] == "lawful-conditional"]
    cards = "".join(
        f'<a class="card" href="routes.html#{esc(r["id"])}"><span class="tag">{esc(r["id"])}</span>'
        f'<strong>{esc(r["short"])}</strong><em>{esc(r["category"])}</em></a>'
        for r in M["routes"]
    )
    n_con = sum(1 for i in F["audit"]["items"] if i["verdict"] == "contradicted")
    n_ok = sum(1 for i in F["audit"]["items"] if i["verdict"] == "verified")
    ex_rows = []
    for r in M["routes"]:
        ex_rows.append(
            [
                f'<td data-label="ID"><a href="routes.html#{esc(r["id"])}">{esc(r["id"])}</a></td>',
                f'<td data-label="Method">{esc(r["short"])}</td>',
                f'<td data-label="Status">{badge(r["status"])}</td>',
                f'<td data-label="Ceiling">{esc(r["ceiling"])}</td>',
                f'<td data-label="Fee">{esc(r["cost_note"])}</td>',
                f'<td data-label="Source">{src_list(r["sources"])}</td>',
            ]
        )
    body = f"""
<h1>Getting CNY out of China: what is verified, what it costs, and what is still unknown</h1>
<p class="lede">A U.S. citizen with money in a mainland China bank account does not face a special
"conversion tax". The PRC Individual Income Tax Law taxes nine listed categories of income, and
turning your own renminbi into dollars is not one of them. The real constraints are three: whether the
balance can be documented, what the bank charges and spreads, and whether your U.S. reporting is clean.
This page separates those three and leaves every unverifiable number blank.</p>

<div class="grid g4">
  <div class="kpi"><p class="k">PRC tax on the conversion itself</p><p class="v">None found</p><p class="s">Not one of the nine taxable income categories {src_link("S19")}</p></div>
  <div class="kpi"><p class="k">U.S. tax on the conversion itself</p><p class="v">$200 threshold</p><p class="s">Personal transaction; no gain recognised unless exchange gain exceeds $200 {src_link("S06")}</p></div>
  <div class="kpi"><p class="k">USD 50,000 annual quota</p><p class="v">Not the limit</p><p class="s">Documented current-account income is not capped at it {src_link("S02")} {src_link("S03")}</p></div>
  <div class="kpi"><p class="k">Published fee, USD 400k</p><p class="v">{usd(r01_fee_usd(400000)["usd"])}</p><p class="s">HSBC Premier/Advance wire, tariff only — spread excluded {src_link("S24")}</p></div>
</div>

<section class="note">
<h2>The short answer</h2>
<ol class="tight">
<li><strong>Do not try to avoid a tax on converting.</strong> Both tax systems attach to income, not to the exchange itself. The "considerable tax" you were quoted is most likely one of: an under-documented source of funds, a Chinese income tax liability on the money when earned, a bank refusal dressed up as a tax, or a U.S. reporting exposure that has nothing to do with the transfer.</li>
<li><strong>Fix the paper first.</strong> If the balance came from lawful employment in China, the route is a bank purchase of foreign exchange against documented current-account income, with tax vouchers. That route has no published USD ceiling; it is limited by evidence, not by a number {src_link("S02")} {src_link("S03")}.</li>
<li><strong>The fee is not the problem.</strong> The published wire fee at {usd(r01_fee_usd(400000)["usd"])} on a USD 400,000-equivalent transfer is trivial. The unpublished FX spread and the penalty exposure are where the money actually goes.</li>
<li><strong>Never use crypto, underground banks or quota splitting.</strong> All three are prohibited and the "saving" is the price of an unlawful transaction {src_link("S23")} {src_link("S20")} {src_link("S01")}.</li>
</ol>
<p class="small">Which of the lawful routes applies to you depends on facts that were not supplied: your residency, whether you ever held Chinese household registration, the origin and dates of the balance, and your U.S. filing history. Those are listed openly on <a href="flagged.html">Flagged for review</a> rather than guessed.</p>
</section>

<h2>All {len(M['routes'])} methods, at a glance</h2>
<p class="small">Tap a row's ID for pros, cons and the exact steps. Full cost tables are on <a href="costs.html">Costs</a>.</p>
{table(["ID", "Method", "Status", "Ceiling", "Published fee", "Source"], ex_rows, caption=None, first_sticky=True)}

<h2>Repo audit — what the existing pages get right and wrong</h2>
<p class="lede-s">{len(F["audit"]["items"])} claims taken from the other published pages and re-checked against the
document they cite: <strong>{n_ok} verified</strong>, <strong>{n_con} contradicted</strong>. The headline defect is a
repeated statement that a personal currency gain above $200 is a <em>capital</em> gain; §988(a)(1)(A) makes it
ordinary income. <a href="audit.html">Read the audit with exact quotes and source links →</a></p>

<h2>Where to go next</h2>
<div class="grid">{cards}</div>
"""
    return page("index.html", "Dashboard", body)


# ---------------------------------------------------------------- routes
def build_routes() -> str:
    out = []
    for r in M["routes"]:
        pros = "".join(f"<li>{esc(p)}</li>" for p in r["pros"])
        cons = "".join(f"<li>{esc(p)}</li>" for p in r["cons"])
        steps = "".join(f"<li>{esc(s)}</li>" for s in r["steps"])
        cap_src = f' <span class="small">({src_link(r["ceiling_source"])})</span>' if r.get("ceiling_source") else ""
        cost_src = f' <span class="small">({src_list(r["sources"])})</span>'
        out.append(
            f"""
<article class="route" id="{esc(r['id'])}">
  <div class="route-head">
    <span class="tag">{esc(r['id'])}</span>
    <h2>{esc(r['name'])}</h2>
  </div>
  <p>{badge(r['status'])} <span class="pill">{esc(r['category'])}</span></p>
  <p class="lede-s">{esc(r['mechanism'])}</p>
  <p class="small"><strong>Who it is for:</strong> {esc(r['who'])}</p>
  <div class="two">
    <div class="pros"><h3>Pros</h3><ul>{pros}</ul></div>
    <div class="cons"><h3>Cons</h3><ul>{cons}</ul></div>
  </div>
  <h3>Exactly how it would work</h3>
  <ol class="steps">{steps}</ol>
  <p class="small"><strong>Ceiling:</strong> {esc(r['ceiling'])}{cap_src}</p>
  <p class="small"><strong>Cost, published only:</strong> {esc(r['cost_note'])}{cost_src}</p>
  <p class="small"><strong>Sources:</strong> {src_list(r['sources'])}</p>
</article>"""
        )
    body = f"""
<h1>Methods: {len(M['routes'])} ways to move CNY to USD, with pros, cons and steps</h1>
<p class="lede">Every route below was checked against the official text linked in its row. Routes that are
prohibited in China are listed too, because the brief asked for as many ways as possible — they are labelled,
not recommended. None is recommended for you personally, because your eligibility facts are unknown
(<a href="flagged.html#G-01">G-01</a>).</p>
<div class="note small"><strong>How to read the status labels.</strong>
{badge('lawful-conditional')} the rule permits it if your documents and status qualify.
{badge('conditional-unverified')} it may exist, but the governing terms were not verified in this session, so it carries no numbers.
{badge('prohibited')} the published rule forbids it.</div>
{''.join(out)}
"""
    return page("routes.html", "Methods", body)


# ---------------------------------------------------------------- costs
def build_costs() -> str:
    rows = []
    for t in TIERS:
        a = r01_fee_usd(t)
        adv = r02_fee_usd(t, "advance")
        pb = r02_fee_usd(t, "premier")
        cash = r07(t)
        rows.append(
            [
                f'<th scope="row">{usd(t)}</th>',
                f"<td>{a['cny']:,.0f}</td>",
                f"<td>{usd(a['usd'])}</td>",
                f"<td>{a['pct_of_amount']:.3f}%</td>",
                f"<td>{usd(adv)}</td>",
                f"<td>{usd(pb)}</td>",
                f'<td data-blank="unverified" class="blank">—</td>',
                f'<td class="caphint">{cash["trips"]} trip{"s" if cash["trips"] != 1 else ""}</td>',
                f'<td data-src="{esc(SRC["S24"]["url"])}">{src_link("S24", "HSBC")} {src_link("S14", "SAFE")}</td>',
            ]
        )

    sample = [10000, 50000, 100000, 200000, 300000, 400000]
    hi_rows = []
    for t in sample:
        a = r01_fee_usd(t)
        hi_rows.append(
            [
                f'<th scope="row">{usd(t)}</th>',
                f'<td><strong>{usd(a["usd"])}</strong></td>',
                f'<td>{a["pct_of_amount"]:.3f}%</td>',
                f'<td>{usd(r02_fee_usd(t, "advance"))}</td>',
                f'<td>{usd(r02_fee_usd(t, "premier"))}</td>',
                f'<td data-src="{esc(SRC["S24"]["url"])}">{src_link("S24", "HSBC tariff")}</td>',
            ]
        )

    blank_rows = []
    for rid in ["R03", "R04", "R05", "R06", "R11", "R12", "R13"]:
        r = ROUTES[rid]
        blank_rows.append(
            [
                f'<td><a href="routes.html#{esc(rid)}">{esc(rid)}</a></td>',
                f'<td>{esc(r["short"])}</td>',
                f'<td data-blank="unverified" class="blank">—</td>',
                f'<td>{esc(r["cost_note"])}</td>',
                f'<td data-src="{esc(SRC[r["sources"][0]]["url"])}">{src_list(r["sources"])}</td>',
            ]
        )

    body = f"""
<h1>What it costs, in $10,000 steps from $10,000 to $400,000</h1>
<p class="lede">Two columns are real money you can check: the published bank fee. One column is not:
the FX spread, which no regulator or bank in these sources publishes, so it is blank everywhere and
flagged (<a href="flagged.html#G-02">G-02</a>). Use the published-fee column to see that <em>fees are
not the obstacle</em>, and the blank column to see what actually needs a written quote from your bank.</p>

<div class="grid g4">
  <div class="kpi"><p class="k">USD 10,000</p><p class="v">{usd(r01_fee_usd(10000)["usd"])}</p><p class="s">Documented wire, HSBC Premier/Advance, published fee only</p></div>
  <div class="kpi"><p class="k">USD 100,000</p><p class="v">{usd(r01_fee_usd(100000)["usd"])}</p><p class="s">Same route, fee now capped</p></div>
  <div class="kpi"><p class="k">USD 400,000</p><p class="v">{usd(r01_fee_usd(400000)["usd"])}</p><p class="s">0.022% of the amount</p></div>
  <div class="kpi warnk"><p class="k">FX spread</p><p class="v">Unverified</p><p class="s">Not published anywhere in the sources — blank, not zero</p></div>
</div>

<section class="note">
<h2>How the published fee is calculated</h2>
<p>HSBC China's tariff sets a telegraphic transfer at <strong>0.1% of the remittance amount, minimum CNY 100,
maximum CNY 500</strong> per transaction, plus a <strong>CNY 120 cable charge</strong>, for Premier and Advance
customers; Private Banking individual customers are charged nothing for issuance. Figures below convert CNY at
the IRS 2025 yearly average of <strong>7.129 CNY per USD</strong>. That rate is a labelled reference conversion,
not an executable rate {src_link("S24")} {src_link("S05")}.</p>
<p class="small">Worked example, USD 10,000: 10,000 × 7.129 = CNY 71,290. 0.1% = CNY 71.29, which is below the
floor, so CNY 100 applies. Add CNY 120 cable = CNY 220. Divide by 7.129 = <strong>{usd(r01_fee_usd(10000)["usd"])}</strong>.</p>
<p class="small">Worked example, USD 400,000: 400,000 × 7.129 = CNY 2,851,600. 0.1% = CNY 2,851.60, which is above
the cap, so CNY 500 applies. Add CNY 120 cable = CNY 620. Divide by 7.129 = <strong>{usd(r01_fee_usd(400000)["usd"])}</strong>.</p>
</section>

<h2>Headline table: six key amounts</h2>
{table(["Amount sent", "Documented wire fee (R01)", "% of amount", "Global Transfer, Advance (R02)", "Global Transfer, Premier/PB (R02)", "Source"], hi_rows, first_sticky=True)}

<h2>Full ladder: all {len(TIERS)} tiers</h2>
<p class="small">R01 = documented purchase of FX plus SWIFT wire (HSBC Premier/Advance tariff). R02 = same-name
HSBC Global Transfer. R07 = carrying cash, shown as the number of permitted exit trips at the USD 10,000 per-person
cap, not as a cost {src_link("S24")} {src_link("S14")}. The spread column is intentionally blank.</p>
{table(
    ["USD sent", "CNY equivalent", "R01 wire fee", "% of amount", "R02 Advance", "R02 Premier/PB", "FX spread", "R07 cash", "Source"],
    rows, cls="data ladder", first_sticky=True
)}
<p class="small">A dash means <em>no official published figure exists</em>. It is not a zero and it is not an estimate.</p>

<h2>Routes with no publishable cost</h2>
<p class="small">These routes are real, but their cost depends on a scheme, a provider, a tax authority or a
commercial spread that was not published in the sources read. The cost cell therefore stays blank
(<a href="flagged.html">G-02, G-04, G-05, G-08</a>).</p>
{table(["ID", "Method", "Cost", "Why it is blank", "Source"], blank_rows, first_sticky=True)}

<section class="note warn">
<h2>What is missing from every number above</h2>
<ul class="tight">
<li><strong>FX spread.</strong> The bank buys your renminbi and sells you dollars at prices it sets. The tariff
expressly excludes other institutions' charges and any duties, levies or taxes {src_link("S24")}.</li>
<li><strong>Correspondent and receiving-bank fees.</strong> Never in the sender's tariff; only in an executable quote.</li>
<li><strong>Optional "Pay Exact".</strong> CNY 200 equivalent if you want the beneficiary to receive the full amount {src_link("S24")}.</li>
<li><strong>PRC income tax on the money when it was earned.</strong> Separate question, unknown.</li>
<li><strong>U.S. tax and penalties.</strong> See <a href="tax.html">Tax &amp; penalties</a>.</li>
<li><strong>Professional fees</strong> for notarisation, translation, probate or advice.</li>
</ul>
</section>
"""
    return page("costs.html", "Costs", body)


# ---------------------------------------------------------------- tax
def build_tax() -> str:
    rates = {"2021": 6.452, "2022": 6.730, "2023": 7.075, "2024": 7.189, "2025": 7.129}
    conv = []
    for yr in ["2021", "2022", "2023", "2024"]:
        acq = rates[yr]
        pct = (acq / rates["2025"] - 1) * 100
        # USD 10,000 of 2025 value converted from RMB acquired in year yr
        rmb = 10000 * rates["2025"]
        cost_acquired = rmb / acq
        gain = 10000 - cost_acquired
        conv.append(
            [
                f"<th scope=\"row\">{yr}</th>",
                f"<td>{acq:.3f}</td>",
                f"<td>{rates['2025']:.3f}</td>",
                f"<td>{pct:+.2f}%</td>",
                f"<td>{usd(gain)}</td>",
                f"<td>{'Loss — no gain to recognise' if gain <= 0 else ('Gain below the $200 threshold' if gain <= 200 else 'Gain above $200')}</td>",
                f'<td data-src="{esc(SRC["S05"]["url"])}">{src_link("S05")} {src_link("S06")}</td>',
            ]
        )
    thr = 200 / ((rates["2024"] / rates["2025"]) - 1)
    comp = [
        ["PRC income tax on wages/salaries", "3%–45% progressive", "On income when earned, not on the exchange", ["S19"]],
        ["PRC income tax on interest/dividends/property/incidental", "20% flat", "Same: an income tax, not an exchange tax", ["S19"]],
        ["PRC tax on exchanging your own currency", "None found", "Not one of the nine listed categories", ["S19"]],
        ["U.S. income tax on the same foreign wages", "Ordinary rates, with FTC or FEIE relief", "Credit for foreign tax paid on the same income; exclusion if eligible", ["S11", "S12"]],
        ["U.S. tax on a personal currency conversion (sec. 988)", "No gain recognised unless the exchange gain exceeds $200", "Personal transaction; above $200 the exclusion does not apply", ["S06"]],
        ["U.S. FBAR (FinCEN 114)", "Non-willful max $16,536; willful max $165,353", "Filing obligation, not a tax; per-violation maximums", ["S08", "S09"]],
        ["U.S. Form 8938", "Separate reporting thresholds", "Unmarried in U.S.: over $50,000 year-end or $75,000 any time", ["S10"]],
        ["U.S. currency report on entry (FinCEN 105)", "Report over $10,000 carried", "Applies to the total carried collectively", ["S13"]],
        ["PRC FX violation (evasion/illegal arbitrage)", "Fine up to 30% of the amount; 30% to equal amount if serious", "Applies to unlawful channels, not to documented conversion", ["S01"]],
    ]
    comp = [[f"<td>{esc(c)}</td>" for c in row[:3]] + [f"<td>{src_list(row[3])}</td>"] for row in comp]
    body = f"""
<h1>Tax and penalties: what actually attaches to the money</h1>
<p class="lede">Three different things get confused in this conversation: a tax on income, a tax on a currency
gain, and a penalty for not reporting. Only the first two are taxes. Below, each is tied to the statute or
regulation that actually says it.</p>

<section class="note">
<h2>1. China: there is no tax on converting</h2>
<p>The Individual Income Tax Law taxes nine enumerated categories of income: wages and salaries; remuneration for
labour services; author's remuneration; royalties; business income; interest, dividends and bonuses; property
leasing; property transfer; and incidental income. Disposing of your own renminbi is not one of them. Rates run
from 3% to 45% on comprehensive income, 5% to 35% on business income, and a flat 20% on interest, dividends,
property leasing, property transfer and incidental income {src_link("S19")}.</p>
<p class="small">This does <strong>not</strong> mean the balance was never taxable. If the money is unpaid
remuneration or an unreported gain, the PRC tax attaches to the income, and the bank is required to review the
real, lawful transaction basis before it sells you foreign exchange {src_link("S01")}. That is the distinction the
brief's "conversion penalty" most likely refers to (<a href="flagged.html#G-03">G-03</a>).</p>
</section>

<section class="note">
<h2>2. United States: sec. 988 and the $200 line</h2>
<p>A personal conversion of non-functional currency is a section 988 transaction, but for an individual's
<em>personal</em> transaction no gain is recognised by reason of exchange-rate changes unless the gain would exceed
<strong>$200</strong>. Above that line the exclusion does not apply and the gain is ordinary income. "Personal
transaction" excludes anything whose allocable expenses meet section 162 or 212, so business or investment activity
can fall outside the exclusion {src_link("S06")}.</p>
<p>Income is translated into dollars when it is received, paid or accrued, at the spot rate; the IRS has no official
rate and accepts any posted rate used consistently {src_link("S05")}. So a later conversion cannot create income
twice — at most it creates an exchange difference between the acquisition date and the conversion date.</p>
</section>

<h2>3. Is there a currency gain on your balance? It depends on the date</h2>
<p class="small">Computed only from the IRS yearly averages {src_link("S05")}. Each row asks: renminbi worth
$10,000 at the 2025 average, if acquired in year X, what is the dollar gain or loss on conversion?
A negative number is a loss — there is no gain to recognise and the $200 test is never reached.</p>
{table(["Acquired", "Yearly average", "2025 average", "Change", "Gain/loss on $10,000", "Section 988 result", "Source"], conv, first_sticky=True)}
<p class="small">Because the averages moved from 6.452 (2021) to 7.129 (2025), renminbi acquired in 2021-2023 and
converted at the 2025 average shows a <strong>loss</strong>, not a gain. Only 2024 shows a gain, and on the 2024
average a gain exceeds $200 at roughly <strong>{usd(thr)}</strong> converted. This is arithmetic on published
averages; it is not a tax computation for you, and it uses yearly averages rather than your actual acquisition
dates (<a href="flagged.html#G-01">G-01</a>).</p>

<h2>4. Every tax and penalty in one table</h2>
{table(["Item", "Published rate or amount", "What it attaches to", "Source"], comp, first_sticky=True)}

<section class="note warn">
<h2>5. The real penalty exposure is reporting, not conversion</h2>
<p>A foreign account holding over $10,000 at any time in the year must be reported on an FBAR even if it produced
no income. The current inflation-adjusted per-violation maxima are <strong>$16,536</strong> non-willful and
<strong>$165,353</strong> willful; the general willful BSA range is $71,545 to $286,184 {src_link("S08")}
{src_link("S09")}. Those are maximums, asserted on facts and circumstances — not typical amounts. Compare them with
the {usd(r01_fee_usd(400000)["usd"])} published wire fee on $400,000: the compliance question is orders of magnitude
larger than the transfer cost.</p>
<p class="small">Form 8938 is a separate obligation with its own thresholds {src_link("S10")}. Bringing more than
$10,000 in cash into the U.S. requires a FinCEN Form 105 {src_link("S13")}.</p>
</section>
"""
    return page("tax.html", "Tax & penalties", body)


# ---------------------------------------------------------------- steps
def build_steps() -> str:
    phases = [
        (
            "Phase 0 — before you talk to anyone",
            [
                "Write down, for yourself, where the balance came from: salary, services, a sale, a gift, savings you brought in. Attach dates and amounts. Everything downstream depends on this and nothing on this site can substitute for it.",
                "Find the tax evidence you already have: withholding records, annual IIT filings, the employer's certificate of income. If none exist, that is the first problem to solve, not the exchange rate.",
                "Check your U.S. position for past years: FBAR for each year the aggregate exceeded $10,000, and Form 8938 where the threshold applies. Fixing this before moving a large sum is far cheaper than after.",
            ],
        ),
        (
            "Phase 1 — get the bank's written position (free, and it settles the argument)",
            [
                "Ask, in writing: “Which current-account category will you book a purchase of foreign exchange against my documented China income under, and what is your full document list?” Cite Art. 13(1) of the Detailed Rules and Art. 59 of the 2020 Current Account Guidelines.",
                "If they say “tax”, ask them to identify in writing the tax type, the taxpayer, the period, the tax base, the amount and the legal basis — and to distinguish a tax payment from a tax certificate from a bank fee.",
                "Ask for an itemised quote showing the applied CNY/USD rate and its source, the sender fee, cable, correspondent fees, the receiving bank's fee and any 'Pay Exact' charge.",
                "Ask whether they will remit to your own same-name overseas account, and whether the amount is limited in any way.",
            ],
        ),
        (
            "Phase 2 — choose the route that matches your facts",
            [
                "Lawful China employment or service income, documented: <a href='routes.html#R01'>R01</a> (bank purchase + SWIFT wire) or, if you hold an HSBC account abroad, <a href='routes.html#R02'>R02</a> (same-name Global Transfer).",
                "You emigrated from China and cancelled your household registration: <a href='routes.html#R03'>R03</a> (emigrant property transfer, SAFE approval).",
                "You inherited a mainland estate: <a href='routes.html#R04'>R04</a>.",
                "You previously changed foreign currency into renminbi and still hold the memo: <a href='routes.html#R05'>R05</a>.",
                "Small amounts you will actually spend: <a href='routes.html#R06'>R06</a> (card) or <a href='routes.html#R07'>R07</a> (cash within USD 10,000).",
                "Never: <a href='routes.html#R08'>R08</a> quota splitting, <a href='routes.html#R09'>R09</a> crypto, <a href='routes.html#R10'>R10</a> underground banks.",
            ],
        ),
        (
            "Phase 3 — execute, in this order",
            [
                "Get the executable quote in writing and check the effective rate against a reference rate yourself. The difference between the two is the spread you are really paying — the number nobody publishes.",
                "Send a small test transfer first (for example USD 1,000-5,000). Reconcile what lands against what left. This reveals correspondent deductions that no tariff shows.",
                "Send the remainder in the size that matches your documentation. There is no published advantage to splitting a documented transfer; splitting to dodge a limit is what SAFE calls evasion (<a href='routes.html#R08'>R08</a>).",
                "Keep the exchange memo, tax certificate, SWIFT confirmation, bank statements and the quote, together, in one folder.",
            ],
        ),
        (
            "Phase 4 — the U.S. side, which is where the money is actually at risk",
            [
                "Translate the amounts into dollars at the rate you consistently use {src_link('S05')}.",
                "File the FBAR if the aggregate of your foreign accounts exceeded $10,000 at any time in the year {src_link('S08')}.",
                "File Form 8938 if you cross the applicable threshold {src_link('S10')}.",
                "Claim the foreign tax credit on the same income if PRC tax was paid, or the foreign earned income exclusion if you qualify — not both on the same income {src_link('S11')} {src_link('S12')}.",
                "File FinCEN Form 105 if you physically bring in more than $10,000 {src_link('S13')}.",
                "If you have unreported prior years, consider the IRS streamlined compliance procedures before the transfer makes the account visible.",
            ],
        ),
    ]
    blocks = []
    for title, items in phases:
        lis = "".join(f"<li>{i}</li>" for i in items)
        blocks.append(f"<section class='phase'><h2>{esc(title)}</h2><ol class='steps'>{lis}</ol></section>")
    body = f"""
<h1>Step by step, from “the money is stuck” to a filed U.S. return</h1>
<p class="lede">This is the order that minimises both cost and risk. It is deliberately front-loaded on
documentation and on your U.S. filing position, because those — not the wire fee — determine the outcome.</p>
<div class="note small"><strong>Nothing here is personalised advice.</strong> The sequence assumes facts you have to
confirm: that the balance is lawful, documented China income or another eligible category, and that you can produce
tax evidence. If that assumption fails, stop at Phase 1 and get professional help
(<a href="flagged.html#G-01">G-01</a>, <a href="flagged.html#G-03">G-03</a>).</div>
{''.join(blocks)}
"""
    return page("steps.html", "Step by step", body)


# ---------------------------------------------------------------- sources
def build_sources() -> str:
    rows = []
    for s in S["sources"]:
        rows.append(
            [
                f"<td><strong>{esc(s['id'])}</strong></td>",
                f'<td>{esc(s["title"])}</td>',
                f'<td>{esc(s["publisher"])}</td>',
                f'<td><span class="pill">{esc(s["kind"])}</span></td>',
                f'<td class="loc">{esc(s.get("locator", ""))}</td>',
                f'<td>{src_link(s["id"], "Open source")}</td>',
            ]
        )
    body = f"""
<h1>Source register: {len(S['sources'])} official documents</h1>
<p class="lede">Every one of these was fetched and read in this session on 10 November 2026. Government and
statutory texts are primary law. One provider document (HSBC China's tariff) is primary only for HSBC's own
published prices and is never treated as a regulator's statement. PRC texts are cited from the official Chinese
pages; where an official English version exists it is named and its own “Chinese prevails” note is preserved.</p>
<div class="note small"><strong>Verification standard.</strong> A value is published only if it appears in the
document listed here. If it does not, the cell is blank and the issue appears on
<a href="flagged.html">Flagged for review</a>. No secondary source, blog, forum or press summary is relied on.</div>
{table(["ID", "Document", "Publisher", "Type", "Article / page locator", "Link"], rows, first_sticky=True)}
<h2>What each document was used for</h2>
{''.join(f"<article class='srcf'><h3>{esc(s['id'])} · {esc(s['title'])}</h3><p>{esc(s['facts'])}</p><p class='small'>{src_link(s['id'], s['url'])}</p></article>" for s in S['sources'])}
"""
    return page("sources.html", "Sources", body)


# ---------------------------------------------------------------- flagged
def build_flagged() -> str:
    items = "".join(
        f"""
<article class="flag" id="{esc(f['id'])}">
  <h2><span class="tag warn-tag">{esc(f['id'])}</span> {esc(f['title'])}</h2>
  <p>{esc(f['detail'])}</p>
  <p class="small"><strong>What this blocks:</strong> {esc(f['impact'])}</p>
  <p class="small"><strong>Sources for manual review:</strong> {src_list(f['sources'])}</p>
</article>"""
        for f in F["flags"]
    )
    unver = [f for f in F["findings"] if f["status"] == "unverified"]
    urows = [
        [f"<td>{esc(f['id'])}</td>", f"<td>{esc(f['claim'])}</td>", f"<td>{esc(f['note'])}</td>", f"<td>{src_list(f['sources'])}</td>"]
        for f in unver
    ]
    body = f"""
<h1>Flagged for review: {len(F['flags'])} unresolved items</h1>
<p class="lede">These are the questions this session could not close from official sources. They are published
rather than filled in. Nothing here blocks the site — it blocks a confident answer, which is the honest position.</p>
<section class="note warn">
<p><strong>Read this first.</strong> No route on this site is recommended for you, and no personal tax figure is
given, because the underlying facts were never supplied: your residency, your Chinese household registration status,
the account type, the origin and dates of the balance, and your prior U.S. filing history. Guessing any of those
would produce a confident wrong answer, which is worse than a blank.</p>
</section>
{items}
<h2>Findings that remain unverified</h2>
{table(["ID", "Claim", "Note", "Sources"], urows, first_sticky=True)}
<h2>Findings that were verified</h2>
<div class="grid">
{''.join(f"<div class='card flat'><span class='tag ok-tag'>{esc(f['id'])}</span><p>{esc(f['claim'])}</p><p class='small'>{src_list(f['sources'])}</p></div>" for f in F['findings'] if f['status'] == 'verified')}
</div>
"""
    return page("flagged.html", "Flagged for review", body)


# ---------------------------------------------------------------- repo audit
def build_audit() -> str:
    A = F["audit"]
    rows = []
    for it in A["items"]:
        verdict = {
            "verified": ('ok-tag', 'Verified'),
            "verified-limited": ('warn-tag', 'Verified, limited'),
            "contradicted": ('bad-tag', 'Contradicted'),
            "unverified": ('warn-tag', 'Unverified'),
        }[it["verdict"]]
        rows.append(
            [
                f'<td><strong>{esc(it["id"])}</strong></td>',
                f'<td>{esc(it["page"])}</td>',
                f'<td>{esc(it["claim"])}</td>',
                f'<td><span class="tag {verdict[0]}">{esc(verdict[1])}</span></td>',
                f'<td>{esc(it["finding"])}</td>',
                f'<td>{src_list(it["sources"])}</td>',
            ]
        )
    counts = {}
    for it in A["items"]:
        counts[it["verdict"]] = counts.get(it["verdict"], 0) + 1
    detail = "".join(
        f"""<article class="flag" id="{esc(it['id'])}">
  <h2><span class="tag {'bad-tag' if it['verdict'] == 'contradicted' else ('ok-tag' if it['verdict'] == 'verified' else 'warn-tag')}">{esc(it['id'])}</span> {esc(it['title'])}</h2>
  <p class="small"><strong>Pages:</strong> {esc(it['page'])} · <strong>Verdict:</strong> {esc(it['verdict'])}</p>
  <p><strong>What the pages say:</strong> {esc(it['claim'])}</p>
  <p><strong>What the official source says:</strong> {esc(it['finding'])}</p>
  {f'<p class="small"><strong>Cross-scope request:</strong> {esc(it["request"])}</p>' if it.get('request') else ''}
  <p class="small"><strong>Official source to review by hand:</strong> {src_list(it['sources'])}</p>
</article>"""
        for it in A["items"]
    )
    body = f"""
<h1>Repo audit: {len(A['items'])} claims in the existing site re-checked against official text</h1>
<p class="lede">I read the claims the other published pages make and checked each one against the document it
cites, fetched again on 10 November 2026. Most hold up. One pattern does not: {counts.get('contradicted', 0)} pages
describe the U.S. treatment of a personal currency gain above $200 as a <em>capital gain</em>, which is the opposite
of what 26 U.S.C. §988 says. That is flagged below with the exact pages, the quoted text and the statute.</p>

<div class="grid g4">
  <div class="kpi"><p class="k">Claims re-checked</p><p class="v">{len(A['items'])}</p><p class="s">Across briefing/, site/, ladder/ and the root hub</p></div>
  <div class="kpi"><p class="k">Verified</p><p class="v">{counts.get('verified', 0)}</p><p class="s">Matches the official text</p></div>
  <div class="kpi warnk"><p class="k">Verified, limited</p><p class="v">{counts.get('verified-limited', 0)}</p><p class="s">True but easily over-read</p></div>
  <div class="kpi warnk" style="border-left-color:#8a1c1c"><p class="k">Contradicted</p><p class="v" style="color:#8a1c1c">{counts.get('contradicted', 0)}</p><p class="s">Official text says otherwise</p></div>
</div>

<h2>Findings table</h2>
{table(["ID", "Page(s)", "Claim as published", "Verdict", "What the official source actually says", "Source"], rows, first_sticky=True)}

<h2>Detail and manual-review links</h2>
{detail}

<section class="note">
<h2>Method and its limits</h2>
<p>This is a targeted audit of claims that can be checked against a specific official document — tax rates,
statutory thresholds, penalty amounts, regulatory ceilings and published bank fees. It is <strong>not</strong> a
line-by-line certification of all {A['meta']['pages_scanned']} published HTML pages in the repository, and it is not
a review of every sentence. Internal link integrity and page structure are already covered by each session's own
verifier and CI; I did not re-run those suites.</p>
<p class="small">The cross-scope requests above are also logged in <code>COORDINATION.md</code>. I did not edit any
page outside <code>verify-416f3c1b/</code>, because those pages belong to other sessions' scopes.</p>
</section>
"""
    return page("audit.html", "Repo audit", body)


# ---------------------------------------------------------------- write
def main() -> None:
    pages = {
        "index.html": build_index(),
        "routes.html": build_routes(),
        "costs.html": build_costs(),
        "tax.html": build_tax(),
        "steps.html": build_steps(),
        "sources.html": build_sources(),
        "audit.html": build_audit(),
        "flagged.html": build_flagged(),
    }
    for name, content in pages.items():
        (ROOT / name).write_text(content, encoding="utf-8")
    print(f"wrote {len(pages)} pages, {sum(len(p) for p in pages.values()):,} bytes")


if __name__ == "__main__":
    main()
