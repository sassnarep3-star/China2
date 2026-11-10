#!/usr/bin/env python3
"""Render static HTML for verify-88f5a1be/ from the JSON ledgers. No runtime deps."""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

sources = json.loads((HERE / "sources.json").read_text())["sources"]
findings = json.loads((HERE / "findings.json").read_text())["findings"]
costs = json.loads((HERE / "costs.json").read_text())
methods = json.loads((HERE / "methods.json").read_text())["methods"]
flags = json.loads((HERE / "flags.json").read_text())["flags"]
SRC = {s["id"]: s for s in sources}
ROWS = costs["rows"]
RECON = costs["reconciliation"]

esc = html.escape


def src_links(ids):
    out = []
    for i in ids:
        s = SRC.get(i)
        if s:
            out.append(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(i)} · {esc(s["publisher"])}</a>')
    return " · ".join(out) if out else '<span class="blank">— blank (unverified, see Flagged)</span>'


def money(v):
    if v is None:
        return '<span class="blank">—</span>'
    return f"${v:,.2f}"


NAV = [
    ("index.html", "Summary"),
    ("costs.html", "Costs $10k→$400k"),
    ("methods.html", "Methods & steps"),
    ("penalties.html", "Penalty breakdown"),
    ("findings.html", "Verification"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]


def page(title, current, body):
    cur = ' aria-current="page"'
    nav = "".join(
        f'<a href="{h}"{cur if h == current else ""}>{esc(t)}</a>' for h, t in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — China money verification</title>
<meta name="description" content="Fresh official-source verification and $10k-step cost reconciliation for CNY to USD repatriation.">
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header><div class="bar"><strong>China money · verification</strong>
<nav>{nav}</nav></div></header>
<main>
{body}
</main>
<footer><p><strong>Research, not advice.</strong> No private account facts were used, no bank was contacted, no funds moved, no returns filed. Every unverified figure is blank or flagged; modelled bands are marked and are not quotes.</p>
<p><a href="index.html">Summary</a> · <a href="exports/costs.csv">Costs CSV</a> · <a href="exports/costs.json">Costs JSON</a> · <a href="../COORDINATION.md">Task board</a></p></footer>
<script src="assets/app.js"></script></body></html>
"""


def table(headers, rows):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = []
    for r in rows:
        tds = "".join(f'<td data-label="{esc(h)}">{c}</td>' for h, c in zip(headers, r))
        trs.append(f"<tr>{tds}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'


# ---------- index ----------
decision_rows = []
for r in ROWS:
    decision_rows.append([
        f"<strong>${r['amount_usd']:,}</strong>",
        money(r["m01_fee_usd"]),
        money(r["m03_premier_fee_usd"]),
        f"{money(r['m02_fee_usd'])} · {r['m02_years']} yr",
        f"{r['m06_years']} yr",
        f"{r['m07_trips']} trips",
        money(r["fine_serious_max_usd"]),
    ])

index_body = f"""
<h1>China money: the least-tax, lawful way to move CNY → USD</h1>
<p class="lede">As a U.S. citizen: there is no such thing as a CNY→USD “conversion tax”. What people call the conversion penalty is a stack of separate things — PRC income tax on the source of the balance, the bank's spread and wire fees, PRC fines for unlawful routes, and U.S. reporting penalties. This page is the executive summary; every claim links its official source, re-fetched 2026-11-10.</p>
<div class="notice"><strong>Not tax or legal advice.</strong> No private account facts were used. Every unverifiable number is blank and flagged (<a href="flagged.html">F01–F10</a>). Take the <a href="#checklist">bank-first checklist</a> to a Chinese-qualified adviser.</div>
<div class="kpi">
<div class="box"><div class="n">$0</div><div class="d">PRC or U.S. tax on the conversion act itself · <a href="findings.html#V01">V01</a></div></div>
<div class="box"><div class="n">$86.97</div><div class="d">Published fee: HSBC Premier/Advance wire at $400k (0.1% capped CNY 500 + CNY 120 cable) · <a href="findings.html#V21">V21</a></div></div>
<div class="box"><div class="n">$16,536</div><div class="d">Max non-willful FBAR penalty per report (assessed on/after 2025-01-17) · <a href="findings.html#V16">V16</a></div></div>
<div class="box"><div class="n">30–100%</div><div class="d">PRC fine band for FX evasion / illegal conversion routes · <a href="findings.html#V11">V11</a></div></div>
</div>

<h2>1 · The “conversion penalty”, broken down line by line</h2>
{table(["#", "Layer", "What it actually is", "Official source"], [
    ["1", "PRC conversion tax", "<strong>None exists.</strong> SAFE limits by quota (USD 50,000/yr facilitation for domestic individuals) and authenticity review; above quota, review is strengthened — not banned, not taxed.", src_links(["S01", "S05"])],
    ["2", "PRC IIT on the income", "3%–45% progressive on comprehensive income (after RMB 60,000 deduction); flat 20% interest/dividends/property. Owed when income arose, not at remittance. Unpaid → bank conversion stalls until tax certifies.", src_links(["S08"])],
    ["3", "Bank spread + fees (not tax)", "The real ordinary cost. HSBC Premier/Advance (tariff eff. 2026-10-31): outward TT 0.1%, min CNY 100 / max CNY 500 + CNY 120 cable. ≥≈$70,135 the fee caps → $86.97 for $400k. Private Banking individuals: free. <strong>Spread unpublished</strong> — blank, flagged F02.", src_links(["S20"])],
    ["4", "U.S. tax on the conversion", "None on the exchange. Personal FX gain excluded from income unless &gt; <strong>$200</strong>; above that, capital gain. (Business/investment currency differs — §988.)", src_links(["S16"])],
    ["5", "U.S. reporting penalties", "<strong>FBAR</strong> (accounts &gt; $10,000 aggregate any time): non-willful ≤ <strong>$16,536</strong>/report; willful ≤ greater of <strong>$165,353</strong> or <strong>50%</strong> of balance. <strong>Form 8938</strong>: $10,000 + $10,000 per 30 days after notice, max <strong>$60,000</strong>.", src_links(["S11", "S12", "S13", "S14"])],
    ["6", "PRC fines for unlawful routes", "Evasion / illegal FX purchase: warning, confiscate illegal gains, fine ≤ <strong>30%</strong>; serious: <strong>30–100%</strong> + criminal liability. Applies to crypto bridges, quota pooling, underground banks, false documents.", src_links(["S05", "S10"])],
    ["7", "U.S.–China treaty / FTC", "PRC tax on the same income may be credited via Form 1116, subject to category &amp; limitation rules (credit, not refund). Treaty withholding % not verified this session (F05).", src_links(["S17", "S21"])],
])}

<h2>2 · The least-tax path, in decision order</h2>
<ol>
<li><strong>Prove the source of the balance</strong> (contract/invoices + bank statements + tax vouchers). Nothing moves lawfully without this.</li>
<li><strong>Settle any unpaid PRC tax on that income</strong> — this is the step that stalls large balances.</li>
<li>Move it via <strong>M01</strong> (bank conversion + same-name SWIFT wire — published fee caps at $86.97 regardless of size) or <strong>M03</strong> (Global Transfer, $0 published fee for PB/Premier) — see <a href="costs.html">cost tables</a>.</li>
<li>US side: <strong>FBAR + Form 8938</strong> on time; <strong>Form 1116</strong> for the PRC tax; if past years were missed, use <strong>Streamlined procedures</strong> before the IRS finds you.</li>
<li><strong>Never</strong> use M14–M17 (crypto/smurfing/underground banks/false docs): fines 30–100% + criminal exposure.</li>
</ol>
<div class="summary"><strong>Cheapest published-cost path for a documented after-tax balance:</strong> one wire from China → own US account. At $400,000: published fees $86.97 (HSBC Premier/Advance) or $0 (Private Banking individual / Global Transfer PB-Premier), plus the unpublished spread (blank, F02). At $10,000: same routes, fee $30.86. The fee is trivial; the spread and the paperwork are the game.</div>

<h2>3 · Decision table — published-fee floors at every $10,000 step</h2>
<p>Most important first: M01 (1 wire) and M03 (Premier $0) are the cheapest lawful published costs. M02 needs calendar years; M06/M07 need years/trips. Fine column is the statutory serious-case maximum for unlawful routes (M14–M17) — not a price. Full detail in <a href="costs.html">costs</a>.</p>
{table(["Amount", "M01 1 wire", "M03 Premier", "M02 quota + years", "M06 ATM years", "M07 cash trips", "Unlawful fine max"], decision_rows)}

<h2 id="checklist">4 · The bank-first checklist (take this to your branch)</h2>
<ol>
<li>Ask for the refusal/approval <strong>in writing</strong>; note the tax type, taxpayer, period, base, amount and legal basis — distinguish a tax payment from a tax certificate or a bank fee.</li>
<li>Ask which FX category applies to you (documented foreign-individual income vs annual quota vs settlement account) and what evidence satisfies it (contract, invoices, tax vouchers, permits).</li>
<li>Get the <strong>executable all-in quote</strong>: applied CNY→USD rate, fee and cable, Pay Exact surcharge, intermediary/receiving charges, and the delivery date.</li>
<li>Confirm your <strong>PRC tax settlement</strong> for the years the income arose (annual 汇算清缴) and get the 完税证明.</li>
<li>US filings: FBAR by Apr 15 (auto-extension to Oct 15), Form 8938 with the return, Form 1116 for the credit.</li>
<li>Past years unreported? Ask a US tax professional about <strong>Streamlined Filing Compliance Procedures</strong> now, not after an IRS letter.</li>
<li>Carrying &gt; $10,000 cash into the US? File <strong>FinCEN 105</strong>. China: USD 5,000/trip no permit; USD 5,000–10,000 with bank permit.</li>
</ol>

<h2>5 · Where to go next</h2>
<div class="cols">
<a class="card" href="costs.html"><strong>Cost tables $10k→$400k</strong><span>All 17 methods at every $10k step; decision table first; mobile-friendly.</span></a>
<a class="card" href="methods.html"><strong>Methods &amp; step-by-step</strong><span>Eligibility, pros/cons and execution for each of the 17 routes.</span></a>
<a class="card" href="penalties.html"><strong>Penalty breakdown</strong><span>The 7-layer conversion-penalty deep dive with dollar exposures.</span></a>
<a class="card" href="findings.html"><strong>Verification ledger</strong><span>30 claims re-checked against official sources fetched 2026-11-10.</span></a>
<a class="card" href="sources.html"><strong>Source register</strong><span>21 official/provider sources with direct links and locators.</span></a>
<a class="card" href="flagged.html"><strong>Flagged for review</strong><span>F01–F10: blanks, stale claims, and open irregularities.</span></a>
<a class="card" href="../briefing/index.html"><strong>Prior briefing (briefing/)</strong><span>The earlier consolidated study this verification re-checks.</span></a>
<a class="card" href="../repatriate/index.html"><strong>Prior study (repatriate/)</strong><span>17 methods × 40 increments = 680 rows (reconciled here).</span></a>
</div>
"""
(HERE / "index.html").write_text(page("Executive summary", "index.html", index_body))

# ---------- findings ----------
frows = []
for f in findings:
    badge = {"verified": '<span class="badge ok">verified</span>', "verified-limited": '<span class="badge warn">verified-limited</span>', "unverified-blank": '<span class="badge bad">unverified-blank</span>'}[f["status"]]
    val = esc(f["value"]) if f["value"] else '<span class="blank">— blank</span>'
    frows.append([f"<strong>{esc(f['id'])}</strong>", esc(f["claim"]), val, badge, src_links(f["sources"]), esc(f["note"])])
findings_body = f"""
<h1>Verification ledger — 30 claims re-checked 2026-11-10</h1>
<p class="lede">Every row was checked against the cited official source body fetched this session. “Verified” means confirmed; “verified-limited” means confirmed in part; “unverified-blank” means the value is left blank and flagged. No value is inferred.</p>
<div class="tools"><input id="q" type="search" placeholder="Filter findings…" aria-label="Filter findings">
<select id="st" aria-label="Filter by status"><option value="">All statuses</option><option>verified</option><option>verified-limited</option><option>unverified-blank</option></select></div>
{table(["ID", "Claim", "Value", "Status", "Official source", "Note"], frows)}
"""
(HERE / "findings.html").write_text(page("Verification ledger", "findings.html", findings_body))

# ---------- costs ----------
def full_rows():
    out = []
    for r in ROWS:
        out.append([
            f"${r['amount_usd']:,}",
            f"¥{r['amount_cny_ref']:,.0f}",
            money(r["m01_fee_usd"]),
            f"{money(r['m02_fee_usd'])} · {r['m02_wires']}w/{r['m02_years']}y",
            money(r["m03_premier_fee_usd"]),
            money(r["m03_advance_fee_usd"]),
            f"{r['m04_transfers']}x",
            money(r["m04_fee_usd"]),
            money(r["m05_fee_usd"]),
            f"{r['m06_years']}y/{r['m06_days']}d",
            money(r["m06_fee_usd"]),
            f"{r['m07_trips']}x",
            money(r["m07_fee_usd"]),
            f"{r['m08_trips']}x",
            money(r["m08_fee_usd"]),
            f"{r['m09_days']}d",
            money(r["m09_fee_usd"]),
            money(r["fine_standard_max_usd"]),
            f"{money(r['fine_serious_min_usd'])}–{money(r['fine_serious_max_usd'])}",
            money(r["split_wire_fee_usd"]),
        ])
    return out

recon_rows = []
for r in RECON:
    recon_rows.append([
        f"${r['amount_usd']:,}",
        money(r["ours"]),
        money(r["repatriate"]),
        money(r["ladder"]),
        money(r["diff_repatriate"]),
        money(r["diff_ladder"]),
    ])

costs_body = f"""
<h1>Costs $10,000 → $400,000 in $10,000 steps</h1>
<p class="lede">Published-fee floors recomputed from the HSBC tariff formula (S20) at the IRS 2025 yearly-average reference rate 7.129 (S19). <strong>Blank (—) means unpublished, not zero.</strong> Fine bands are statutory maxima for unlawful routes, not prices. Reference rate is for fee comparison only — not an executable quote.</p>
<div class="notice"><strong>How to read this:</strong> M01 = one SWIFT wire of documented after-tax income. M03 Premier = $0 published (HSBC both sides). M02 = quota tranches (needs calendar years). M06/M07/M08/M09 = cash channels (needs years/trips/days). M14–M17 fines = 30% / 30–100% of the amount (S05). Spread is blank everywhere (F02).</div>
<div class="tools"><input id="q" type="search" placeholder="Filter amounts…" aria-label="Filter amounts"></div>

<h2>Decision table — cheapest lawful published costs first</h2>
{table(["Amount", "M01 1 wire", "M03 Premier", "M02 quota + years", "M06 ATM years", "M07 cash trips", "Unlawful fine max"], decision_rows)}

<h2>Full table — every method at every step</h2>
{table(["Amount", "CNY ref", "M01 fee", "M02 fee/wires/years", "M03 Prem", "M03 Adv", "M04 xfers", "M04 fee", "M05 fee", "M06 y/d", "M06 fee", "M07 trips", "M07 fee", "M08 trips", "M08 fee", "M09 days", "M09 fee", "Fine std max", "Fine serious", "Split-wire fee"], full_rows())}

<h2>Reconciliation — this session vs prior dashboards (M01 fee)</h2>
<p>This session matches <a href="../repatriate/exports/cost-ladders.csv">repatriate</a> exactly (same 7.129 rate + formula). Ladder differs only by its 7.1 reference rate (same CNY 620 cap → $87.32 vs $86.97). Ladder additionally models a 0.30–1.50% spread band; this session and repatriate publish the fee floor only and leave spread blank (F02).</p>
{table(["Amount", "This session", "Repatriate", "Ladder", "Diff vs repatriate", "Diff vs ladder"], recon_rows)}

<h2>Assumptions and limits</h2>
<ul>
<li>Reference rate 7.129 CNY/USD (IRS 2025 yearly average, S19). At 7.1 the $400k M01 fee would be $87.32 instead of $86.97.</li>
<li>M01 assumes one wire. If the bank splits into N wires, fee = N × per-wire fee (split-wire column = M02 math). No source publishes a per-transfer ceiling for documented-income wires (F09).</li>
<li>M02 assumes one wire per calendar-year tranche of ≤$50,000. Years = wires.</li>
<li>M03 Advance ($20/transaction) total is blank: per-transaction limit unpublished (F02).</li>
<li>M04 transfers = ceil(CNY/300,000) bank-app route; fee blank (F03). M10–M13 have no published schedule → blank (F02).</li>
<li>Fine bands: standard max 30%, serious 30–100% (S05 Arts. 39/40/45). Carrying fine is 20% (Art. 42), not shown here.</li>
</ul>
<p>Downloads: <a href="exports/costs.csv">costs.csv</a> · <a href="exports/costs.json">costs.json</a> · <a href="costs.json">costs + reconciliation JSON</a></p>
"""
(HERE / "costs.html").write_text(page("Costs $10k to $400k", "costs.html", costs_body))

# ---------- methods ----------
mrows = []
for m in methods:
    pros = "<br>".join(f"✓ {esc(p)}" for p in m["pros"])
    cons = "<br>".join(f"✗ {esc(c)}" for c in m["cons"])
    steps = "<br>".join(f"{i+1}. {esc(s)}" for i, s in enumerate(m["steps"]))
    badge = '<span class="badge ok">lawful-conditional</span>' if m["status"] == "lawful-conditional" else '<span class="badge bad">rejected-unlawful</span>'
    mrows.append([f"<strong>{esc(m['id'])}</strong><br>{badge}", f"<strong>{esc(m['name'])}</strong><br><span class='muted'>{esc(m['who'])}</span>", pros, cons, steps, esc(m["sources"])])
methods_body = f"""
<h1>Methods &amp; step-by-step — 17 routes</h1>
<p class="lede">13 lawful-conditional routes and 4 rejected-unlawful routes (documented because the brief asks for as many ways as possible — they are <strong>not</strong> recommendations). Pros/cons/steps summarize the cited sources; analysis is labeled.</p>
<div class="tools"><input id="q" type="search" placeholder="Filter methods…" aria-label="Filter methods"></div>
{table(["Method", "Who / what", "Pros", "Cons", "Step by step", "Sources"], mrows)}
"""
(HERE / "methods.html").write_text(page("Methods and steps", "methods.html", methods_body))

# ---------- penalties ----------
pen_body = f"""
<h1>The conversion penalty, broken down line by line</h1>
<p class="lede">There is no single “conversion penalty”. The phrase covers seven different layers with different legal bases, different amounts, and different ways to avoid them. This page prices each layer at $10,000 → $400,000 where the law gives a number, and leaves it blank where it does not.</p>

<h2>Layer 1 — PRC conversion tax: $0</h2>
<p>SAFE imposes a quota and authenticity review, not a tax (S01). FE Regs Art. 5 does not restrict current transfers (S05). <strong>Amount at every tier: $0.</strong> Source: {src_links(["S01", "S05"])} · Finding <a href="findings.html#V01">V01</a>.</p>

<h2>Layer 2 — PRC income tax on the source: 3–45% / 5–35% / 20% (if unpaid)</h2>
<p>Tax attaches to the income when it arises (S08). If already paid, incremental tax at remittance is $0. If unpaid, the bank stalls conversion until tax certifies — the practical “penalty” for large balances. <strong>Your personal amount: blank (F01)</strong> — it depends on income type, years, and tax already paid. Source: {src_links(["S08"])} · Finding <a href="findings.html#V09">V09</a>.</p>

<h2>Layer 3 — Bank spread: blank (unpublished)</h2>
<p>No bank publishes a CNY/USD customer spread. Ladder models 0.30–1.50% as an explicit assumption; this session leaves it blank (F02). At $400,000, that assumption would be $1,200–$6,000 — <strong>not a quote</strong>. Get the executable rate in writing at the counter. Source: {src_links(["S20"])} · Finding <a href="findings.html#V27">V27</a>.</p>

<h2>Layer 4 — Wire fees: $30.86 → $86.97 (published)</h2>
<p>HSBC Premier/Advance TT: 0.1% min CNY 100 max CNY 500 + CNY 120 cable (S20). Fee floors: $10k → $30.86; $50k → $66.83; $100k → $86.97 (capped); $400k → $86.97. Private Banking individuals and Global Transfer PB/Premier: $0. Source: {src_links(["S20"])} · Finding <a href="findings.html#V21">V21</a>. See <a href="costs.html">costs</a> for all 40 tiers.</p>

<h2>Layer 5 — U.S. tax on the conversion: $0 unless personal gain &gt; $200</h2>
<p>Moving your own already-taxed money is not new income. Personal FX gain is excluded unless it exceeds $200 per transaction (S16). Above that, the gain is a capital gain. Business/investment currency is different (ordinary under §988(a)). Source: {src_links(["S16"])} · Finding <a href="findings.html#V19">V19</a>.</p>

<h2>Layer 6 — U.S. reporting penalties: avoidable by filing</h2>
<p><strong>FBAR</strong> (&gt;$10,000 aggregate any time, S11): non-willful ≤ $16,536/report; willful ≤ greater of $165,353 or 50% of balance (S12/S13). <strong>Form 8938</strong> (S15): $10,000 + $10,000/30 days, max $60,000/form (S14). <strong>FinCEN 105</strong> for &gt;$10,000 cash entry (S18). These dwarf wire fees — at $400,000, one willful FBAR penalty (50% = $200,000) exceeds 2,000× the wire fee. File on time; use Streamlined procedures for past years. Findings <a href="findings.html#V15">V15–V18</a>, <a href="findings.html#V24">V24</a>.</p>

<h2>Layer 7 — PRC fines for unlawful routes: 30% / 30–100%</h2>
<p>Evasion, fraudulent purchase, and illegal dealing: up to 30%; serious 30–100% + criminal liability (S05). At $400,000: standard max $120,000; serious $120,000–$400,000. Crypto bridges are additionally illegal financial activity (S10). These fines are why M14–M17 are rejected. Finding <a href="findings.html#V11">V11</a>. Dollar bands in <a href="costs.html">costs</a>.</p>

<h2>Bottom line</h2>
<p>If PRC tax on the income is already settled, the lawful cost of conversion is <strong>Layer 4 + Layer 3 only</strong> (fees $30.86–$86.97 + unpublished spread). The cheapest lawful strategy is not a tax shelter: settle Layer 2 so the authenticity review passes; claim the FTC (Layer 7 in the index summary) so PRC tax is not paid twice; minimise Layer 4 with competing written quotes; and shorten Layer 3 by using the documented-income route (M01) instead of quota staging (M02). Every “cheap” alternative attacks the quota by breaking the law and converts a modest quantifiable cost into Layers 6–7.</p>
"""
(HERE / "penalties.html").write_text(page("Penalty breakdown", "penalties.html", pen_body))

# ---------- sources ----------
srows = []
for s in sources:
    srows.append([f"<strong>{esc(s['id'])}</strong>", esc(s["title"]), esc(s["publisher"]), f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">open source</a>', esc(s["kind"]), esc(s["status"]), esc(s["locator"]), esc(s["facts"])])
sources_body = f"""
<h1>Source register — 21 sources fetched 2026-11-10</h1>
<p class="lede">Every source below was fetched and read this session. Regulator/statute sources are primary law; the HSBC tariff is primary only for HSBC's own fees. English translations of PRC rules are reference translations; the Chinese text prevails.</p>
<div class="tools"><input id="q" type="search" placeholder="Filter sources…" aria-label="Filter sources"></div>
{table(["ID", "Title", "Publisher", "Link", "Kind", "Status", "Locator", "What it supports"], srows)}
"""
(HERE / "sources.html").write_text(page("Sources", "sources.html", sources_body))

# ---------- flagged ----------
flagrows = []
for f in flags:
    flagrows.append([f"<strong>{esc(f['id'])}</strong>", esc(f["title"]), esc(f["detail"]), '<span class="badge warn">needs review</span>'])
flagged_body = f"""
<h1>Flagged for review — F01–F10</h1>
<p class="lede">Unverified values are left blank, never estimated. These items do not block the site; they are published here for your manual review. Request changes after the site is live.</p>
{table(["ID", "Issue", "Detail", "Status"], flagrows)}
"""
(HERE / "flagged.html").write_text(page("Flagged for review", "flagged.html", flagged_body))

print("rendered: index, findings, costs, methods, penalties, sources, flagged")
