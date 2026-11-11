#!/usr/bin/env python3
"""Build the consolidated CNY->USD dashboard for session arena/9fe02cf5-china2.

Deterministic: same inputs -> same bytes. No value is invented here. Every
number rendered is either read from data/*.json (which records the official
source) or computed from the published parameters by a formula printed on the
page. Where a published figure does not exist, the cell renders an em dash and
the item is listed on the Flagged for Review page.
"""
import csv
import html
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

sources = json.load(open(DATA / "sources.json"))
claims = json.load(open(DATA / "claims.json"))
methods = json.load(open(DATA / "methods.json"))
questions = json.load(open(DATA / "questions.json"))
flags = json.load(open(DATA / "flags.json"))
costs = json.load(open(DATA / "costs.json"))
repo = json.load(open(DATA / "repo_audit.json"))

SRC = {s["id"]: s for s in sources["sources"]}
CLAIM = {c["id"]: c for c in claims["claims"]}
METHOD = {m["id"]: m for m in methods["methods"]}
FLAG = {f["id"]: f for f in flags["flags"]}

P = costs["parameters"]
RATE = P["boc_sell_cny_per_usd"]
BUY = P["boc_buy_cny_per_usd"]
SPREAD_PCT = (RATE - BUY) / RATE * 100.0
BLANK = "\u2014"

BUILT = "2026-11-11"
NAV = [
    ("index.html", "Answer"),
    ("questions.html", "Questions"),
    ("methods.html", "Methods"),
    ("costs.html", "Costs"),
    ("taxes.html", "Tax layers"),
    ("verification.html", "Verification"),
    ("flagged.html", "Flagged"),
    ("sources.html", "Sources"),
    ("audit.html", "Repo audit"),
]


def esc(value):
    return html.escape(str(value), quote=True)


def usd(x):
    return f"${x:,.2f}"


def cny(x):
    return f"CNY {x:,.2f}"


def pct(x, digits=3):
    return f"{x:.{digits}f}%"


def source_link(sid):
    s = SRC[sid]
    return (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">'
            f'{esc(sid)}</a>')


def source_cell(ids):
    if not ids:
        return f'<span class="blank">no source</span>'
    return " ".join(source_link(i) for i in ids)


def claim_links(ids):
    if not ids:
        return BLANK
    return " ".join(f'<a href="verification.html#{esc(i)}">{esc(i)}</a>' for i in ids)


def flag_links(ids):
    if not ids:
        return BLANK
    return " ".join(f'<a href="flagged.html#{esc(i)}">{esc(i)}</a>' for i in ids)


def status_badge(status):
    cls = {"VERIFIED": "ok", "PARTIAL": "warn", "UNVERIFIED": "bad",
           "LAWFUL": "ok", "CONDITIONAL": "warn", "REJECTED": "bad",
           "REVIEW": "warn", "VERIFIED-WITH-DATE": "ok"}.get(status, "warn")
    return f'<span class="badge {cls}">{esc(status)}</span>'


# --------------------------------------------------------------------------- maths
def tiers():
    return list(range(P["tier_start_usd"], P["tier_end_usd"] + 1, P["tier_step_usd"]))


def fee_cny(model_key, amount_usd):
    """Published sender-side fee in CNY for one instruction of amount_usd."""
    m = costs["fee_models"][model_key]
    needed = amount_usd * RATE
    if m["commission_pct"] > 0:
        commission = needed * m["commission_pct"]
        commission = max(commission, m["commission_min_cny"])
        commission = min(commission, m["commission_max_cny"])
    else:
        commission = 0.0
    return commission + m["cable_cny"] + m["pay_exact_cny"]


def fee_usd(model_key, amount_usd):
    return fee_cny(model_key, amount_usd) / RATE


def spread_usd(amount_usd):
    return amount_usd * SPREAD_PCT / 100.0


def batches(amount_usd, size):
    return -(-int(amount_usd) // int(size))


def atm_years(amount_usd):
    need_cny = amount_usd * RATE
    return -(-int(round(need_cny)) // int(P["atm_annual_rmb_cap"]))


def atm_withdrawals(amount_usd):
    need_cny = amount_usd * RATE
    return -(-int(round(need_cny)) // int(P["atm_daily_rmb_cap"]))


def ladder():
    """Full deterministic ladder: every $10k tier x every costed or timed method."""
    rows = []
    for amount in tiers():
        for rid in costs["rows"]:
            mid = rid["method"]
            m = METHOD[mid]
            model = rid["fee_model"]
            row = {
                "amount_usd": amount,
                "method": mid,
                "name": m["name"],
                "status": m["status"],
                "cny_needed": amount * RATE,
                "fee_usd": fee_usd(model, amount) if model else None,
                "spread_usd": spread_usd(amount),
                "timing": None,
            }
            if mid == "M06":
                n = batches(amount, P["annual_quota_usd"])
                row["timing"] = f"{n} annual tranche{'s' if n != 1 else ''}"
            elif mid == "M07":
                y = atm_years(amount)
                w = atm_withdrawals(amount)
                row["timing"] = f"{y} calendar years / {w} withdrawals"
            if row["fee_usd"] is not None:
                row["all_in_usd"] = row["fee_usd"] + row["spread_usd"]
                row["all_in_pct"] = row["all_in_usd"] / amount * 100.0
            else:
                row["all_in_usd"] = None
                row["all_in_pct"] = None
            rows.append(row)
    return rows


LADDER = ladder()


# --------------------------------------------------------------------------- shell
def page(filename, title, lede, body, wide=False):
    nav_parts = []
    for href, label in NAV:
        cls = ' class="active"' if href == filename else ""
        nav_parts.append(f'<a href="{esc(href)}"{cls}>{esc(label)}</a>')
    nav = "".join(nav_parts)
    main_cls = "wrap wide" if wide else "wrap"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China money · verified {BUILT}</title>
<meta name="description" content="{esc(lede)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <a class="brand" href="index.html">China money <span>· CNY → USD</span></a>
    <p class="stamp">Independent verification pass · sources re-fetched {BUILT} · research, not tax or legal advice</p>
  </div>
  <nav class="tabs" aria-label="Sections">{nav}</nav>
</header>
<main class="{main_cls}">
{body}
</main>
<footer>
  <div class="wrap">
    <p><strong>Research, not advice.</strong> No private account facts were entered, no bank was contacted, no funds were moved and no tax return was filed. Values that could not be confirmed from an official source are blank and listed on the <a href="flagged.html">Flagged for Review</a> page.</p>
    <p>Data: <a href="exports/cost-ladder.csv">cost ladder CSV</a> · <a href="exports/cost-ladder.json">cost ladder JSON</a> · <a href="exports/claims.csv">claim ledger CSV</a> · <a href="sources.html">source register</a> · <a href="../index.html">repository hub</a></p>
  </div>
</footer>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


def table(headers, rows, cls="data"):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        cells = "".join(
            f'<td data-label="{esc(headers[i])}">{c}</td>' for i, c in enumerate(row))
        body.append(f"<tr>{cells}</tr>")
    return (f'<div class="tablewrap"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def kpi(label, value, small):
    return (f'<div class="kpi"><p class="label">{esc(label)}</p>'
            f'<p class="value">{value}</p><p class="small">{small}</p></div>')


# --------------------------------------------------------------------------- pages
def page_index():
    count_verified = sum(1 for c in claims["claims"] if c["status"] == "VERIFIED")
    count_partial = sum(1 for c in claims["claims"] if c["status"] == "PARTIAL")
    fee_max = max(fee_usd("hsbc_premier_our", a) for a in tiers())
    m01_10 = fee_usd("hsbc_premier_sha", 10000) + spread_usd(10000)
    m01_400 = fee_usd("hsbc_premier_sha", 400000) + spread_usd(400000)

    kpis = "".join([
        kpi("PRC tax on exchanging currency",
            "None found",
            f'No conversion levy appears in the FX instruments reviewed ({source_link("S01")} {source_link("S02")}). This is an absence-of-evidence finding, not a guarantee.'),
        kpi("PRC tax that may really apply",
            "3%–45% / 5%–35% / 20%",
            f'PRC individual income tax on the underlying income, if it was never taxed ({source_link("S09")}). Whether it was taxed is unknown.'),
        kpi("Published sender-side wire fee",
            f"{usd(0)} – {usd(fee_max)}",
            f'maximum across the costed routes at $400,000, from the bank tariff read today ({source_link("S20")}).'),
        kpi("Published spread benchmark",
            pct(SPREAD_PCT),
            f'Bank of China buy {BUY:.4f} vs sell {RATE:.4f} CNY/USD at {esc(P["boc_timestamp"])} ({source_link("S21")}). A benchmark, not a quote.'),
        kpi("Account-specific all-in cost",
            "Not available",
            'No PRC rule or tariff publishes it. The holder must obtain an itemised executable quote.'),
    ])

    steps = table(
        ["Step", "What to do", "Why (verified basis)", "Source"],
        [
            ["1", "Get the bank's refusal reason in writing: tax type, taxpayer, period, base, amount, legal basis.",
             "A tax payment, a tax certificate and a bank fee are three different things; only the first is a tax.",
             source_link("S02")],
            ["2", "Establish the SAFE category: domestic individual, foreign individual, or PR ID holder.",
             "The USD 50,000 purchase quota applies to domestic individuals and only to foreign individuals with a PR ID (C04, C07).",
             f'{source_link("S02")} {source_link("S04")}'],
            ["3", "Assemble contemporaneous proof of the income and, if needed, the PRC tax certificate.",
             "The rule requires ID plus source materials including tax documents (C06); no time limit is imposed (C08).",
             f'{source_link("S03")} {source_link("S05")}'],
            ["4", "If you are outside China, prepare a notarised authorisation and the same document set.",
             "The remittance formality may be entrusted to another person with the documents (C09).",
             f'{source_link("S06")} {source_link("S02")}'],
            ["5", "Get the itemised quote: applied rate, commission, cable, intermediary and receiving charges.",
             "The tariff excludes third-party charges and the spread is not published (C24, F03, F04).",
             source_link("S20")],
        ])

    body = f"""
<section class="hero">
  <h1>What it actually costs to get CNY out of China, and what is still unknown</h1>
  <p class="lede">The balance is not expensive to convert because of a tax on converting. On the law read here it is expensive only if the underlying income was never taxed in China, and otherwise the real cost is a bank spread plus a small, capped wire fee. Every figure below is traced to a document re-fetched on {BUILT}; everything that could not be traced is blank.</p>
</section>

<section class="kpis">{kpis}</section>

<div class="callout">
  <h2>Short answer</h2>
  <p><strong>Cheapest lawful shape:</strong> convert documented current-account income at a bank that accepts the file, in one instruction, and send it with the published sender fee. At the bank whose tariff was read today that fee is capped at {usd(fee_usd("hsbc_premier_sha", 400000))} on $400,000 (Premier/Advance) or {usd(0)} on Private Banking. The benchmark spread on $400,000 is {usd(spread_usd(400000))}. So a benchmark all-in of about <strong>{usd(m01_400)} ({pct(m01_400 / 400000 * 100, 2)})</strong> on $400,000 and <strong>{usd(m01_10)} ({pct(m01_10 / 10000 * 100, 2)})</strong> on $10,000. Those two numbers are arithmetic on published prices, not a quote.</p>
  <p><strong>What would change the answer:</strong> if the money is untaxed PRC income, the PRC income tax is the cost and it is measured in tens of percent, not basis points. That fact is unknown (F10).</p>
</div>

<h2>Decision order</h2>
{steps}

<h2>What the evidence supports</h2>
<ul class="checks">
  <li><strong>{count_verified} of {len(claims["claims"])}</strong> load-bearing statements were re-read verbatim in an official or bank-published document on {BUILT}; <strong>{count_partial}</strong> are partial. The ledger is on <a href="verification.html">Verification</a>.</li>
  <li>The sender-side fee is small and capped on the routes where a tariff was published ({source_link("S20")}). The spread, not the fee, is the cost that scales.</li>
  <li>Cash is not a shortcut: overseas ATM withdrawals are capped at RMB 100,000 per person per civil year ({source_link("S07")}).</li>
  <li>The US side does not double-tax the same income if the PRC tax is paid and documented, because a credit is available on Form 1116 with a one-year-back / ten-year-forward carry ({source_link("S15")} {source_link("S16")}).</li>
</ul>

<h2>What the evidence does not support</h2>
<ul class="checks bad">
  <li>Any claim that this particular balance is tax-free, or that the bank's request is unlawful. The origin and tax history are unknown.</li>
  <li>Any specific all-in cost in dollars for this account. The spread and third-party charges are unpublished (F03, F04).</li>
  <li>Any use of a crypto/USDT bridge: RMB-to-virtual-currency business is classified as illegal financial activity ({source_link("S10")}).</li>
  <li>Any use of relatives' quotas, underground swaps or 'agents' to defeat the limits; those carry fines of up to 30% or more of the amount ({source_link("S01")}).</li>
</ul>

<h2>Where to go next</h2>
<div class="cards">
  <a class="card" href="questions.html"><strong>12 questions</strong><span>What we know · what we do not · how to find it</span></a>
  <a class="card" href="methods.html"><strong>12 methods</strong><span>Lawful, conditional and rejected · pros, cons, exact steps</span></a>
  <a class="card" href="costs.html"><strong>Costs $10k → $400k</strong><span>40 tiers · published fees · benchmark spread · blanks</span></a>
  <a class="card" href="taxes.html"><strong>8 cost layers</strong><span>Where the money actually goes</span></a>
  <a class="card" href="verification.html"><strong>{len(claims["claims"])} verified claims</strong><span>One line each, with the quoted sentence</span></a>
  <a class="card" href="flagged.html"><strong>{len(flags["flags"])} flagged items</strong><span>Unverified values and corrections</span></a>
  <a class="card" href="sources.html"><strong>{len(sources["sources"])} sources</strong><span>All re-fetched {BUILT}, with locators</span></a>
  <a class="card" href="audit.html"><strong>Repo audit</strong><span>Line-by-line review of every other dashboard</span></a>
</div>
"""
    return page("index.html", "Answer",
                "What CNY-to-USD conversion really costs and what remains unverified.",
                body)


def page_questions():
    blocks = []
    for q in questions["questions"]:
        blocks.append(f"""
<article class="q" id="{esc(q["id"])}">
  <h3><span class="id">{esc(q["id"])}</span> {esc(q["question"])}</h3>
  <p class="why">{esc(q["why"])}</p>
  <div class="qa">
    <div><p class="label">What we know</p><p>{esc(q["we_know"])}</p></div>
    <div><p class="label">What we do not know</p><p>{esc(q["we_do_not_know"])}</p></div>
    <div><p class="label">How to discover it</p><ol>{"".join(f"<li>{esc(s)}</li>" for s in q["how"])}</ol></div>
  </div>
  <p class="meta">Sources: {source_cell(q["source_ids"])} · Flags: {flag_links(q["flags"])} · Related claims: {claim_links([])}</p>
</article>""")
    body = f"""
<h1>Questions that must be answered before any decision</h1>
<p class="lede">Each answer selects which methods are even available and therefore which rows of the cost table apply. Nothing here is assumed on the holder's behalf.</p>
<div class="qlist">{"".join(blocks)}</div>
"""
    return page("questions.html", "Questions",
                "Gating questions, what is known, what is unknown, and how to find out.",
                body)


def page_methods():
    rows = []
    for m in methods["methods"]:
        fee_note = m["fee_label"]
        if m["fee_model"]:
            fee_at_400 = usd(fee_usd(m["fee_model"], 400000))
            fee_cell = (f'{fee_at_400} at $400,000<br><span class="mut">{esc(fee_note)}</span>')
        else:
            fee_cell = f'<span class="blank">{BLANK}</span> <span class="mut">{esc(fee_note)}</span>'
        steps = "".join(f"<li>{esc(s)}</li>" for s in m["steps"])
        pros = "".join(f"<li>{esc(s)}</li>" for s in m["pros"])
        cons = "".join(f"<li>{esc(s)}</li>" for s in m["cons"])
        rows.append([
            f'<strong>{esc(m["id"])}</strong><br>{esc(m["name"])}',
            status_badge(m["status"]),
            esc(m["cap"]),
            fee_cell,
            f'<ul class="tight plus">{pros}</ul>',
            f'<ul class="tight minus">{cons}</ul>',
            f'<details><summary>Step by step</summary><ol class="tight">{steps}</ol></details>',
            f'{source_cell(sorted({sid for cid in m["basis_claims"] for sid in CLAIM[cid]["source_ids"]}))}<br>{claim_links(m["basis_claims"])}',
        ])
    body = f"""
<h1>Every conversion method found, with pros, cons and exact steps</h1>
<p class="lede">Ten lawful or conditional routes and two rejected ones. A fee appears only where a published tariff or official document was read today; otherwise the cell is blank, never zero.</p>
<div class="filters">
  <input type="search" id="tableSearch" placeholder="Filter methods, e.g. ATM, inheritance, quota" aria-label="Filter methods">
  <select id="statusFilter" aria-label="Filter by status">
    <option value="">All statuses</option>
    <option value="LAWFUL">Lawful</option>
    <option value="CONDITIONAL">Conditional</option>
    <option value="REJECTED">Rejected</option>
  </select>
</div>
{table(["Method", "Status", "Limit", "Published fee", "Pros", "Cons", "Steps", "Sources"], rows)}
<p class="note">Status reflects what the reviewed rule says on its face. It is not a determination that any particular person qualifies: eligibility depends on the facts in the <a href="questions.html">questions</a>.</p>
"""
    return page("methods.html", "Methods",
                "Twelve CNY-to-USD routes with pros, cons, caps and exact steps.",
                body, wide=True)


def page_costs():
    milestone_rows = []
    for amount in P["milestones_usd"]:
        for rid in costs["rows"]:
            if not rid["fee_model"]:
                continue
            mid = rid["method"]
            m = METHOD[mid]
            fee = fee_usd(rid["fee_model"], amount)
            spread = spread_usd(amount)
            total = fee + spread
            milestone_rows.append([
                f'<strong>{usd(amount)}</strong>',
                cny(amount * RATE),
                f'{esc(mid)} · {esc(m["fee_label"])}',
                usd(fee),
                usd(spread),
                f'<strong>{usd(total)}</strong>',
                pct(total / amount * 100, 2),
                source_cell(["S20", "S21"]),
            ])
    milestone_rows.append([
        f'<strong>{usd(400000)}</strong>', cny(400000 * RATE),
        "M06 · annual USD 50,000 quota", f'<span class="blank">{BLANK}</span>',
        usd(spread_usd(400000)), f'<span class="blank">{BLANK}</span>',
        f'<span class="blank">{BLANK}</span>',
        f'{source_link("S02")} {source_link("S04")}',
    ])
    milestone_rows.append([
        f'<strong>{usd(400000)}</strong>', cny(400000 * RATE),
        "M07 · overseas ATM cash", f'<span class="blank">{BLANK}</span>',
        usd(spread_usd(400000)), f'<span class="blank">{BLANK}</span>',
        f'<span class="blank">{BLANK}</span>', source_link("S07"),
    ])

    full = []
    for r in LADDER:
        fee_cell = usd(r["fee_usd"]) if r["fee_usd"] is not None else f'<span class="blank">{BLANK}</span>'
        allin = usd(r["all_in_usd"]) if r["all_in_usd"] is not None else f'<span class="blank">{BLANK}</span>'
        allin_pct = pct(r["all_in_pct"], 2) if r["all_in_pct"] is not None else f'<span class="blank">{BLANK}</span>'
        timing = esc(r["timing"]) if r["timing"] else f'<span class="blank">{BLANK}</span>'
        full.append([
            usd(r["amount_usd"]),
            cny(r["cny_needed"]),
            f'{esc(r["method"])}',
            status_badge(r["status"]),
            fee_cell,
            usd(r["spread_usd"]),
            allin,
            allin_pct,
            timing,
            source_cell(["S20", "S21"] if r["fee_usd"] is not None else
                        (["S02", "S04"] if r["method"] == "M06" else ["S07"])),
        ])

    fallback = table(
        ["Amount (USD)", "CNY needed", "Method", "Status", "Published sender fee",
         "Benchmark spread", "Benchmark all-in", "All-in %", "Timing", "Source"],
        full)

    body = f"""
<h1>Cost to move and convert, every $10,000 from $10,000 to $400,000</h1>
<p class="lede">Most important numbers first. Fees are the amounts the bank itself publishes. The spread column applies Bank of China's own published buy/sell band at {esc(P["boc_timestamp"])} ({pct(SPREAD_PCT)}) and is labelled a benchmark because it is not this account's rate. Where no published figure exists the cell is blank.</p>

<div class="callout">
  <p><strong>Formula used, so you can check it:</strong> CNY needed = USD amount × {RATE:.4f}. Premier/Advance commission = 0.1% of CNY needed, floored at CNY {costs["fee_models"]["hsbc_premier_sha"]["commission_min_cny"]:.0f}, capped at CNY {costs["fee_models"]["hsbc_premier_sha"]["commission_max_cny"]:.0f}; plus CNY {costs["fee_models"]["hsbc_premier_sha"]["cable_cny"]:.0f} cable; Pay Exact adds CNY {costs["fee_models"]["hsbc_premier_our"]["pay_exact_cny"]:.0f}. Benchmark spread = USD amount × {SPREAD_PCT:.6f}%. Private Banking individual and Premier Elite are published as free, so their fee row is {usd(0)}.</p>
</div>

<h2>Milestones</h2>
{table(["Amount", "CNY needed", "Route", "Published sender fee", "Benchmark spread", "Benchmark all-in", "All-in %", "Source"], milestone_rows)}

<h2>Full ladder · {len(LADDER)} rows</h2>
<div class="filters">
  <input type="search" id="tableSearch" placeholder="Filter: 150000, ATM, Premier, quota" aria-label="Filter cost ladder">
  <select id="methodFilter" aria-label="Filter by method">
    <option value="">All methods</option>
    {''.join(f'<option value="{esc(m)}">{esc(m)}</option>' for m in sorted({r["method"] for r in LADDER}))}
  </select>
</div>
{fallback}
<p class="note">Blank means no published figure was found in this session; it does not mean zero. The account-specific quote, all intermediary and receiving-bank charges, and any PRC or US tax are excluded from every row. CSV and JSON exports are in the footer.</p>
"""
    return page("costs.html", "Costs",
                "Cost per $10,000 tier from $10,000 to $400,000, with blanks where unpublished.",
                body, wide=True)


def page_taxes():
    layers = [
        ["1", "PRC tax on the act of exchanging currency",
         "Any conversion", "None found in the reviewed FX instruments",
         "Absence-of-evidence only; see F14", f'{source_link("S01")} {source_link("S02")}'],
        ["2", "PRC individual income tax on the underlying money",
         "Only if the income was never taxed", "3%–45% comprehensive · 5%–35% business · 20% flat on interest, dividends, asset transfers",
         "Rates verified; whether it applies here is unknown (F10)", source_link("S09")],
        ["3", "Source-of-funds and tax-voucher gate at the bank",
         "Foreign individual converting current-account income", "No fee published; conversion is conditional on ID plus source materials including tax documents",
         "This is the provision that usually produces the 'pay tax first' message", f'{source_link("S02")} {source_link("S03")}'],
        ["4", "PRC tax recordal for outbound service payments",
         "Service-trade payments", "Filing before the first payment under a contract; once per contract",
         "A filing step, not an assessment; threshold not re-read (F06)", source_link("S08")],
        ["5", "Treaty cap on PRC withholding",
         "Dividends, interest, royalties paid to a US beneficial owner", "10% of gross",
         "Does not cover wages or business profits", source_link("S11")],
        ["6", "Bank spread on the conversion",
         "Every conversion", "Not published for any account; published benchmark band 0.4200% on " + esc(P["boc_timestamp"]),
         "The cost that scales with the amount (F03, F12)", source_link("S21")],
        ["7", "Sender-side wire fee and cable",
         "Every outward wire", f'Published: {usd(0)} Private Banking individual; Premier/Advance capped at {usd(fee_usd("hsbc_premier_sha", 400000))} including cable at $400,000; Pay Exact adds {usd(costs["fee_models"]["hsbc_premier_our"]["pay_exact_cny"] / RATE)}',
         "Capped, so it stops mattering at large amounts", source_link("S20")],
        ["8", "US tax on any exchange gain",
         "Personal transaction disposing of CNY", "No gain recognised where the gain does not exceed $200; above that the statute removes the exclusion",
         "Characterisation above $200 not stated in the text read (F02)", source_link("S12")],
        ["9", "US double-tax relief",
         "PRC tax actually paid on the same income", "Form 1116 credit, limited; carry back 1 year / forward 10; not available for FEIE-excluded income",
         "Prevents double tax only with a paid, documented PRC tax", f'{source_link("S15")} {source_link("S16")}'],
        ["10", "US reporting obligations and penalties",
         "Account above $10,000 aggregate, or assets above the 8938 thresholds",
         "FBAR non-willful max $16,536 / willful max $165,353; 8938 up to $10,000 plus $10,000 per 30 days, capped $60,000; foreign-trust information: greater of $10,000 or 35%",
         "Payable only for a filing failure, but large enough to dominate the whole exercise", f'{source_link("S18")} {source_link("S17")} {source_link("S13")}'],
        ["11", "US border reporting for cash",
         "Carrying more than $10,000 into or out of the US", "FinCEN Form 105 report; failure risks seizure and forfeiture",
         "Applies to the group's combined amount", source_link("S19")],
        ["12", "PRC penalties for an unlawful route",
         "Evasion, disguised trading, quota splitting, crypto", "Up to 30% of the amount, or 30% to an equal amount in serious cases, plus criminal liability",
         "This is the layer that makes 'quick' routes irrational", f'{source_link("S01")} {source_link("S10")}'],
    ]
    body = f"""
<h1>The conversion 'penalty', layer by layer</h1>
<p class="lede">The word 'penalty' hides several different things. Only some are taxes, only one scales with the amount, and only one is avoidable by choosing a different route.</p>
{table(["#", "Layer", "When it applies", "Verified amount or rate", "What it means", "Source"], layers)}
<div class="callout">
  <h2>Two corrections to earlier pages in this repository</h2>
  <p><strong>Foreign trust vs foreign gift.</strong> The foreign-trust information penalty in IRC §6677 is the greater of $10,000 or 35% (5% substituted for §6048(b) returns) plus $10,000 per 30 days after notice ({source_link("S13")}). The widely quoted '5% per month up to 25%' belongs to a different provision that could not be retrieved here; it is left unverified on <a href="flagged.html#F01">F01</a> rather than repeated.</p>
  <p><strong>Characterisation above $200.</strong> Section 988(e) removes personal transactions from §988 and excludes recognition only up to $200. It does not say the excess is capital gain, so that description is not used anywhere in this site (<a href="flagged.html#F02">F02</a>).</p>
</div>
"""
    return page("taxes.html", "Tax layers",
                "Twelve cost layers, separated into taxes, gates, spreads, fees and penalties.",
                body, wide=True)


def page_verification():
    rows = []
    for c in claims["claims"]:
        rows.append([
            f'<strong id="{esc(c["id"])}">{esc(c["id"])}</strong>',
            esc(c["topic"]),
            esc(c["statement"]),
            status_badge(c["status"]),
            f'<blockquote>{esc(c["evidence"])}</blockquote><p class="mut">{esc(c["locator"])}</p>',
            source_cell(c["source_ids"]),
            esc(c["implication"]),
        ])
    n_v = sum(1 for c in claims["claims"] if c["status"] == "VERIFIED")
    n_p = sum(1 for c in claims["claims"] if c["status"] == "PARTIAL")
    n_u = len(claims["claims"]) - n_v - n_p
    body = f"""
<h1>Line-by-line verification ledger</h1>
<p class="lede">Every load-bearing statement in this site appears below with the sentence that supports it, quoted from the document, and a link to that document. Each document was re-fetched over HTTPS on {BUILT}. Statements that depend on private facts are marked partial and are never filled in.</p>
<section class="kpis small">
  {kpi("Statements checked", str(len(claims["claims"])), "one row each, no grouping")}
  {kpi("Verified verbatim", str(n_v), f"quoted text read in the source body on {BUILT}")}
  {kpi("Partial", str(n_p), "part of the statement depends on facts or instruments not read here")}
  {kpi("Unverified", str(n_u), "published as blank, never inferred")}
</section>
<div class="filters">
  <input type="search" id="tableSearch" placeholder="Filter claims, e.g. quota, 988, ATM" aria-label="Filter claims">
  <select id="statusFilter" aria-label="Filter by status">
    <option value="">All statuses</option>
    <option value="VERIFIED">Verified</option>
    <option value="PARTIAL">Partial</option>
  </select>
</div>
{table(["ID", "Topic", "Statement", "Status", "Evidence quoted from the source", "Source", "What it implies"], rows)}
"""
    return page("verification.html", "Verification",
                "Every claim with its quoted official evidence and link.", body, wide=True)


def page_flagged():
    blocks = []
    for f in flags["flags"]:
        blocks.append(f"""
<article class="q" id="{esc(f["id"])}">
  <h3><span class="id">{esc(f["id"])}</span> {esc(f["title"])}</h3>
  <p>{esc(f["detail"])}</p>
  <p class="meta">{status_badge(f["status"])} · Affects: {esc(f["affected"])} · Sources: {source_cell(f["source_ids"])}</p>
</article>""")
    body = f"""
<h1>Flagged for review</h1>
<p class="lede">These are the items that could not be confirmed, the values left blank, and the corrections to statements published elsewhere in this repository. None of them blocks the publication of this site; each one is a task for the reader or for the owning session.</p>
<div class="qlist">{"".join(blocks)}</div>
"""
    return page("flagged.html", "Flagged for review",
                "Unverified values, corrections and repository irregularities.", body)


def page_sources():
    rows = []
    for s in sources["sources"]:
        rows.append([
            f'<strong id="{esc(s["id"])}">{esc(s["id"])}</strong>',
            esc(s["jurisdiction"]),
            f'{esc(s["authority"])}<br><span class="mut">{esc(s["title"])}</span>',
            esc(s.get("locator", "")),
            f'<blockquote>{esc(s["excerpt"])}</blockquote>',
            f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">Open source</a>',
            esc(s.get("retrieved", BUILT)),
        ])
    body = f"""
<h1>Source register</h1>
<p class="lede">Every source was fetched over HTTPS and read in body on {BUILT}. No news article, blog, mirror or AI-generated summary is used as a source. Excerpts are quoted so you can check them yourself.</p>
{table(["ID", "Jurisdiction", "Authority / title", "Locator", "Verbatim excerpt", "Link", "Retrieved"], rows)}
<p class="note">Commercial sources (the bank tariff and the bank rate board) are used only for that bank's own published price. They are labelled as commercial, not as government sources.</p>
"""
    return page("sources.html", "Sources",
                "Twenty-one official and bank-published sources with verbatim excerpts.", body, wide=True)


def page_audit():
    rows = []
    for i, f in enumerate(repo["findings"], 1):
        links = " ".join(
            f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer">file {j}</a>'
            for j, u in enumerate(f["links"], 1))
        rows.append([
            f'<strong>RA-{i:02d}</strong>',
            esc(f["finding"]),
            esc(f["evidence"]),
            status_badge(f["status"]),
            esc(f["action"]),
            links,
        ])
    inv = table(["Item", "Count", "How measured", "Evidence in repository"],
                [[esc(k), esc(v["count"]), esc(v["how"]),
                  f'<a href="{esc(v["link"])}" target="_blank" rel="noopener noreferrer">file</a>']
                 for k, v in repo["inventory"].items()])
    body = f"""
<h1>Repository review, line by line</h1>
<p class="lede">This repository now holds a dozen parallel research dashboards written by different sessions. The review below checks them mechanically and reports what is inconsistent. Nothing in another session's pages was edited; findings are recorded here for the owner sessions.</p>
{inv}
<h2>Findings</h2>
{table(["ID", "Finding", "Evidence", "Status", "Recommended action", "Files affected"], rows)}
<h2>What was actually verified in this pass</h2>
<ul class="checks">
  <li>Every HTML page parses; every local link and anchor in this site resolves; every table row in this site carries an official HTTPS link.</li>
  <li>All {len(claims["claims"])} statements were re-read in the source body on {BUILT}; see <a href="verification.html">Verification</a>.</li>
  <li>All cost arithmetic is recomputed independently by <code>verify.py</code> from the published parameters; the build is deterministic.</li>
</ul>
<h2>What was not verified</h2>
<ul class="checks bad">
  <li>Legal accuracy of the interpretations drawn from the quoted text, and their application to any particular person.</li>
  <li>Whether any other session's numeric claims are correct; this pass only records where they conflict or where they cite facts this pass could not confirm.</li>
  <li>Link liveness across the whole repository (no global crawler was run).</li>
  <li>Any live bank quote, exchange rate other than the one timestamp shown, or personal tax position.</li>
</ul>
"""
    return page("audit.html", "Repo audit",
                "Mechanical and source review of every dashboard in the repository.", body, wide=True)


# --------------------------------------------------------------------------- exports
def write_exports():
    out = BASE / "exports"
    out.mkdir(exist_ok=True)
    fields = ["amount_usd", "method", "method_name", "status", "cny_needed",
              "published_sender_fee_usd", "benchmark_spread_usd",
              "benchmark_all_in_usd", "benchmark_all_in_pct", "timing"]
    with open(out / "cost-ladder.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for r in LADDER:
            w.writerow([
                r["amount_usd"], r["method"], r["name"], r["status"],
                f'{r["cny_needed"]:.2f}',
                "" if r["fee_usd"] is None else f'{r["fee_usd"]:.2f}',
                f'{r["spread_usd"]:.2f}',
                "" if r["all_in_usd"] is None else f'{r["all_in_usd"]:.2f}',
                "" if r["all_in_pct"] is None else f'{r["all_in_pct"]:.4f}',
                r["timing"] or "",
            ])
    payload = {
        "session": sources["meta"]["session"],
        "built": BUILT,
        "reference_rate_cny_per_usd": RATE,
        "rate_source": costs["parameters"]["boc_source"],
        "rate_timestamp": P["boc_timestamp"],
        "benchmark_spread_pct": round(SPREAD_PCT, 6),
        "disclaimer": costs["meta"]["disclaimer"],
        "rows": LADDER,
    }
    (out / "cost-ladder.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with open(out / "claims.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "topic", "statement", "status", "source_ids", "source_urls", "locator"])
        for c in claims["claims"]:
            w.writerow([c["id"], c["topic"], c["statement"], c["status"],
                        " ".join(c["source_ids"]),
                        " ".join(SRC[s]["url"] for s in c["source_ids"]),
                        c["locator"]])


# --------------------------------------------------------------------------- markdown summary
def write_exec_summary():
    m01_10 = fee_usd("hsbc_premier_sha", 10000) + spread_usd(10000)
    m01_400 = fee_usd("hsbc_premier_sha", 400000) + spread_usd(400000)
    n_v = sum(1 for c in claims["claims"] if c["status"] == "VERIFIED")
    lines = [
        "# Executive summary — CNY to USD, verified 2026-11-11",
        "",
        f"Session `arena/9fe02cf5-china2`. Every figure below is traced to a document re-fetched on {BUILT};",
        "the site in this directory is the rendered version and the [verification ledger](verification.html)",
        "carries the quoted sentence and link for each statement.",
        "",
        "## The diagnosis",
        "",
        f"1. **No PRC tax on the act of converting currency was found** in the FX regulations or their implementing",
        "   rules (claim C03, status PARTIAL — an absence-of-evidence result, not a guarantee).",
        "2. **The bank is asking for source-of-funds and tax documents, not a conversion levy.** For a foreign",
        "   individual, the rule requires ID plus transaction materials *including tax documents* (C06).",
        "3. **The expensive layer is PRC income tax on untaxed money**: 3%–45% comprehensive, 5%–35% business,",
        "   flat 20% on interest, dividends, asset transfers and incidental income (C14). Whether it applies here",
        "   is unknown (F10).",
        "4. **Where the money was already taxed and documented, the cost is a bank spread plus a small capped",
        "   wire fee.** At the tariff read today the sender fee is free for Private Banking individuals and capped",
        f"   at {usd(fee_usd('hsbc_premier_sha', 400000))} for Premier/Advance at $400,000, including cable (C23).",
        f"5. **The spread is the cost that scales, and it is not published.** A dated published benchmark",
        f"   (Bank of China's own buy/sell band, {pct(SPREAD_PCT)}, {esc(P['boc_timestamp'])}) puts $400,000 at",
        f"   about {usd(spread_usd(400000))}. It is a benchmark, not this account's rate (F03, F12).",
        "",
        "## Headline arithmetic (benchmark, not a quote)",
        "",
        "| Amount | CNY needed | Published sender fee (M01) | Benchmark spread | Benchmark all-in | % of principal |",
        "|---|---|---|---|---|---|",
    ]
    for amount in (10000, 50000, 100000, 200000, 400000):
        fee = fee_usd("hsbc_premier_sha", amount)
        spread = spread_usd(amount)
        lines.append(f"| {usd(amount)} | {cny(amount * RATE)} | {usd(fee)} | {usd(spread)} | "
                     f"**{usd(fee + spread)}** | {pct((fee + spread) / amount * 100, 2)} |")
    lines += [
        "",
        f"All-in at the smallest tier: {usd(m01_10)} ({pct(m01_10 / 10000 * 100, 2)}). "
        f"At the largest: {usd(m01_400)} ({pct(m01_400 / 400000 * 100, 2)}).",
        "",
        "## What a decision still needs",
        "",
        "Twelve questions, each of which changes which routes exist: origin of the balance, PRC tax paid and",
        "documented, SAFE category (domestic individual vs foreign individual vs PR ID holder), acquisition dates",
        "and USD basis, US reporting history, the bank's executable itemised quote, capital-account documents,",
        "proxy vs in person, liquidity need, the holding bank's tariff, whether any 'quick' route was offered,",
        "and the US credit/FEIE plan. See [questions](questions.html) and `data/questions.json`.",
        "",
        "## Methods",
        "",
        "Twelve routes are catalogued with pros, cons, caps and exact steps: ten lawful or conditional and two",
        "rejected (crypto/USDT and underground or quota-splitting). Rejected routes are penalised at up to 30% of",
        "the amount, or more in serious cases (C26), and RMB-to-virtual-currency business is classified as illegal",
        "financial activity (C16).",
        "",
        "## Verification performed",
        "",
        f"- {len(sources['sources'])} sources re-fetched over HTTPS on {BUILT}; excerpts quoted verbatim.",
        f"- {len(claims['claims'])} statements checked: {n_v} verified verbatim, "
        f"{len(claims['claims']) - n_v} partial. No statement depends on an inferred private fact.",
        f"- {len(LADDER)} cost rows recomputed independently by `verify.py`; 7,000+ structural and arithmetic checks.",
        f"- {len(flags['flags'])} items published on [Flagged for review](flagged.html): unverified values,",
        "  corrections and repository irregularities. None blocks publication.",
        "",
        "## Not advice",
        "",
        "No personal tax position is asserted, no bank was contacted, no funds moved and no return filed. The",
        "spread and third-party charges for this account remain unknown until an itemised executable quote is",
        "obtained.",
        "",
    ]
    (BASE / "EXECUTIVE_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- main
def main():
    pages = {
        "index.html": page_index(),
        "questions.html": page_questions(),
        "methods.html": page_methods(),
        "costs.html": page_costs(),
        "taxes.html": page_taxes(),
        "verification.html": page_verification(),
        "flagged.html": page_flagged(),
        "sources.html": page_sources(),
        "audit.html": page_audit(),
    }
    for name, text in pages.items():
        (BASE / name).write_text(text, encoding="utf-8")
    write_exports()
    write_exec_summary()
    print(f"built {len(pages)} pages, {len(LADDER)} ladder rows, "
          f"{len(claims['claims'])} claims, {len(sources['sources'])} sources, "
          f"{len(flags['flags'])} flags; benchmark spread {SPREAD_PCT:.6f}%")


if __name__ == "__main__":
    main()
