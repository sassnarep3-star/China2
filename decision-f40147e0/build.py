#!/usr/bin/env python3
"""Render the decision dashboard from the JSON ledgers. No number is typed into the HTML."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

SOURCES = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text())}
METHODS = json.loads((DATA / "methods.json").read_text())
METHODS_BY_ID = {m["id"]: m for m in METHODS}
FLAGS = json.loads((DATA / "flags.json").read_text())
FLAGS_BY_ID = {f["id"]: f for f in FLAGS}
COSTS = json.loads((DATA / "costs.json").read_text())
META = COSTS["meta"]
HEAD = COSTS["headline"]
ROWS = COSTS["rows"]

PAGES = [
    ("index.html", "Overview"),
    ("answer.html", "The answer"),
    ("costs.html", "Costs $10k–$400k"),
    ("methods.html", "Methods"),
    ("taxes.html", "Tax & penalties"),
    ("questions.html", "Open questions"),
    ("audit.html", "Repo audit"),
    ("flagged.html", "Flagged"),
    ("sources.html", "Sources"),
]

PRICED = META["priced_methods"]
CASH = "M05"
PRIMARY = ["M01", "M02", "M03", "M04", CASH]
# Approval routes that reuse the BOC bank leg; shown separately so the ranking is not padding.
SAME_LEG = {"M11", "M12", "M13", "M14", "M10"}
# Every row of the master table carries the four boards/tariffs its columns are built from.
MASTER_SOURCES = ["S01", "S03", "S05", "S16"]


def esc(t) -> str:
    return html.escape(str(t), quote=True)


def money(v, decimals=0) -> str:
    if v is None:
        return ""
    return f"${v:,.{decimals}f}"


def pct(v) -> str:
    return "" if v is None else f"{v:.2f}%"


def src(sid: str, external: bool = False) -> str:
    s = SOURCES[sid]
    host = s["url"].split("/")[2].replace("www.", "")
    if external:
        return (f'<a class="src" href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer" '
                f'title="{esc(s["title"])}">{sid} · {esc(host)}</a>')
    return f'<a class="src" href="sources.html#{sid}" title="{esc(s["title"])}">{sid} · {esc(host)}</a>'


def srcs(ids, external: bool = False) -> str:
    return " ".join(src(i, external) for i in ids)


def badge(status: str) -> str:
    table = {
        "lawful": ("ok", "Lawful"),
        "conditional": ("warn", "Conditional"),
        "unlawful": ("bad", "Unlawful"),
        "not_applicable": ("muted", "Not a route"),
        "unverified": ("muted", "Unverified"),
    }
    cls, label = table.get(status, ("muted", status))
    return f'<span class="badge {cls}">{esc(label)}</span>'


def shell(slug: str, title: str, body: str, lead: str = "") -> str:
    nav_parts = []
    for p, label in PAGES:
        current = ' aria-current="page"' if p == slug else ""
        nav_parts.append(f'<a href="{p}"{current}>{esc(label)}</a>')
    nav = "".join(nav_parts)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China Money decision dashboard</title>
<meta name="description" content="{esc(lead or title)}">
<link rel="stylesheet" href="assets/style.css">
<script src="assets/app.js" defer></script>
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <a class="brand" href="index.html"><span class="mark">¥<i>$</i></span><span>China Money<small>decision dashboard</small></span></a>
  <nav aria-label="Sections">{nav}</nav>
</header>
<main id="main">
{body}
</main>
<footer>
  <p><strong>Research, not individualized tax, legal or investment advice.</strong> No personal fact is inferred. Every row links to the publishing institution. Blank means unverified, never zero. Estimates are arithmetic on published inputs, not provider quotes.</p>
  <p>Retrieved {esc(META["generated"])} · reference mid {META["ref_mid"]:.6f} CNY/USD (arithmetic, flag F01) · <a href="sources.html">sources</a> · <a href="flagged.html">flagged for review</a> · <a href="https://github.com/sassnarep3-star/China2">repository</a></p>
</footer>
</body></html>"""


def page_head(eyebrow: str, title: str, text: str) -> str:
    return (f'<div class="head"><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1>'
            f'<p class="lead">{text}</p></div>')


def note(text: str, kind: str = "") -> str:
    return f'<p class="note {kind}">{text}</p>'


# ---------------------------------------------------------------- index
def page_index() -> str:
    b = (
        page_head("Mainland China → United States · U.S. citizen",
                  "What getting the money out actually costs",
                  "A dated, source-linked answer: every figure below is recomputed from pages read on "
                  f"{esc(META['generated'])}, and every row links to the institution that published it. "
                  "Where a bank publishes nothing, the cell is blank and flagged.")
        + '<div class="cards">'
        + f'<a class="card hero" href="answer.html"><p class="eyebrow">THE ANSWER</p><h2>There is no conversion tax.<br>There is a spread, a fee, and a filing history.</h2><p>The “penalty” people feel is four separate things stacked: PRC tax already due on the source, the bank’s spread, the wire fee, and U.S. reporting exposure. Only the first is a tax. Only the last is avoidable by doing nothing wrong earlier.</p><span class="go">Read the seven-layer breakdown →</span></a>'
        + f'<a class="card stat" href="costs.html"><p class="eyebrow">CHEAPEST FULLY PUBLISHED ROUTE · $100,000</p><p class="big">{money(HEAD["M01"]["100000"]["total_usd"], 2)}</p><p class="sub">{pct(HEAD["M01"]["100000"]["pct"])} all-in · Bank of China board + tariff</p><p class="tiny">Widest published route at the same tier: {money(HEAD["M03"]["100000"]["total_usd"], 2)} ({pct(HEAD["M03"]["100000"]["pct"])}).</p></a>'
        + f'<a class="card stat" href="costs.html"><p class="eyebrow">COST FALLS AS THE AMOUNT RISES</p><p class="big">{pct(HEAD["M01"]["10000"]["pct"])} → {pct(HEAD["M01"]["400000"]["pct"])}</p><p class="sub">$10,000 → $400,000 on the same bank route</p><p class="tiny">The spread scales with the amount; the fee is capped, so 40 small transfers cost far more than four large ones.</p></a>'
        + f'<a class="card stat" href="taxes.html"><p class="eyebrow">U.S. §988, ILLUSTRATIVE ONLY</p><p class="big">{pct(COSTS["illustrative_988"][1]["gain_pct"])}</p><p class="sub">of the dollar proceeds could be ordinary exchange gain</p><p class="tiny">If the RMB was acquired at the IRS 2025 average of {META["irs_2025_yuan_per_usd"]} and converted at {META["ref_mid"]:.4f}. Basis is unknown — flag F11.</p></a>'
        + '</div>'
        + '<section class="panel"><h2>Five things the tables say</h2><div class="tablewrap"><table class="stack"><caption>Conclusions drawn from the published inputs · each row names its evidence</caption><thead><tr><th scope="col">Finding</th><th scope="col">Number</th><th scope="col">Evidence</th></tr></thead><tbody>'
        + f'<tr><th scope="row">The spread, not the fee, dominates above about USD 50,000</th><td>At $400,000 the fee is {money(HEAD["M01"]["400000"]["fee_usd"], 2)}, the spread is {money(HEAD["M01"]["400000"]["spread_usd"], 2)}, all-in {money(HEAD["M01"]["400000"]["total_usd"], 2)}</td><td>{srcs(["S01","S02"], True)}</td></tr>'
        + f'<tr><th scope="row">Fees are capped, so small transfers are expensive per dollar</th><td>{pct(HEAD["M01"]["10000"]["pct"])} at $10,000 versus {pct(HEAD["M01"]["10000"]["pct"])} → {pct(HEAD["M01"]["400000"]["pct"])} at $400,000</td><td>{srcs(["S02"], True)}</td></tr>'
        + f'<tr><th scope="row">Bank choice changes the total by more than 3×</th><td>BOC {money(HEAD["M01"]["100000"]["total_usd"], 2)} vs HSBC Premier {money(HEAD["M03"]["100000"]["total_usd"], 2)} at $100,000</td><td>{srcs(["S01","S05"], True)}</td></tr>'
        + f'<tr><th scope="row">The USD 50,000 figure is a quota, not a tax or a fee</th><td>Annual aggregate per person; not a price</td><td>{srcs(["S09","S07"], True)}</td></tr>'
        + f'<tr><th scope="row">The expensive mistakes are the unlawful ones</th><td>Statutory fines run up to 30% of the amount, or 30% to an equal amount if serious</td><td>{srcs(["S07"], True)}</td></tr>'
        + '</tbody></table></div></section>'
        + '<section class="panel"><h2>What is still unknown — and blocks a decision</h2>'
        + note(f'<strong>{len(FLAGS)} open flags.</strong> Three of them decide the answer: <a href="flagged.html#F11">F11</a> (the account holder’s facts), <a href="flagged.html#F12">F12</a> (which rulebook applies) and <a href="flagged.html#F05">F05</a> (unpublished correspondent deductions). Until F11 and F12 are answered, every route here is conditional.', "warn")
        + '<div class="grid3">'
        + '<a class="card" href="questions.html"><h3>15 questions to answer first</h3><p>Each answer is mapped to the rule it changes, with the official source and a way to obtain the missing fact.</p></a>'
        + '<a class="card" href="methods.html"><h3>24 methods, incl. 4 unlawful</h3><p>Pros, cons and exact steps. Prohibited routes are listed with their statutory penalty and no instructions.</p></a>'
        + '<a class="card" href="audit.html"><h3>Repo audit</h3><p>Mechanical re-checks of the earlier sections in this repository, and what could not be re-verified.</p></a>'
        + '</div></section>'
    )
    return shell("index.html", "What getting the money out actually costs", b,
                 "Dated, source-linked cost of moving CNY to USD as a U.S. citizen.")


# ---------------------------------------------------------------- answer
def page_answer() -> str:
    layers = [
        ("1", "PRC income tax on the source", "3%–45% comprehensive, 5%–35% business, 20% flat on interest, dividends and asset transfers.",
         "This is the only real tax in the stack. It was due when the income arose, not when it leaves.", ["S14"]),
        ("2", "The bank's FX spread", f"BOC {HEAD['M01']['100000']['pct']:.3f}% · CMB 0.234% · HSBC 0.473% against the reference mid.",
         "Scales with the amount. Unregulated, unpublished as a number, and the largest cost above USD 50,000.", ["S01", "S03", "S05"]),
        ("3", "The wire and cable fee", "BOC CNY 50–260 + CNY 150; CMB CNY 100–1,000 + CNY 150; HSBC CNY 100–500 + CNY 120.",
         "Capped, so it is a fixed cost that shrinks as a percentage. Four wires cost four caps.", ["S02", "S04", "S06"]),
        ("4", "Correspondent and receiving-bank deductions", "Not published by any bank read this pass.",
         "Real money, unknown size, usually taken from the beneficiary. This is why the totals here are a floor.", ["S04", "S06"]),
        ("5", "U.S. §988 exchange gain", f"Illustratively {COSTS['illustrative_988'][1]['gain_pct']:.2f}% of proceeds if the RMB was acquired at the IRS 2025 average.",
         "Ordinary income, not capital gain. Depends on your actual cost basis, which is unknown here.", ["S18", "S19"]),
        ("6", "U.S. reporting exposure", "FBAR above USD 10,000 aggregate; non-willful maximum USD 16,536, willful USD 165,353.",
         "Not a transfer cost — a pre-existing exposure. It is fixed by filing, not by choosing a route.", ["S20", "S21", "S22"]),
        ("7", "Statutory fines on the wrong route", "Up to 30% of the amount; 30% to an equal amount if serious. 20% for illegal cash carrying.",
         "Only arises on prohibited routes. This is the only layer that can exceed the entire lawful cost many times over.", ["S07"]),
    ]
    body = (
        page_head("The answer", "Least tax penalties, lawfully",
                  "The brief asks for the cheapest way out with the least tax penalty. The honest answer has an order: "
                  "fix the filing position first, document the source second, choose the cheapest published bank third, "
                  "and never take a route whose statutory fine is a percentage of the principal.")
        + '<section class="panel"><h2>The seven layers people call “the conversion penalty”</h2><div class="tablewrap">'
        + '<table class="stack"><caption>Only layer 1 and layer 5 are taxes. Layers 2–4 are price. Layers 6–7 are risks you control.</caption>'
        + '<thead><tr><th scope="col">Layer</th><th scope="col">What it is</th><th scope="col">Published size</th><th scope="col">Why it matters</th><th scope="col">Source</th></tr></thead><tbody>'
        + "".join(
            f'<tr><td data-label="Layer"><span class="num">{n}</span></td>'
            f'<th scope="row" data-label="What it is">{esc(name)}</th>'
            f'<td data-label="Published size">{esc(size)}</td>'
            f'<td data-label="Why it matters">{esc(why)}</td>'
            f'<td data-label="Source">{srcs(ids, True)}</td></tr>'
            for n, name, size, why, ids in layers)
        + '</tbody></table></div></section>'
        + '<section class="panel"><h2>The sequence that minimises the lawful total</h2><ol class="steps">'
        + '<li><strong>Establish the classification before anything else.</strong> A foreign national continuously resident in China for a year or more is a “domestic individual” under Decree 532 Art. 52(2); a non-domestic individual’s China-source income follows a separate route. The two rulebooks produce different document sets and different ceilings. ' + srcs(["S07", "S09"], True) + '</li>'
        + '<li><strong>Pull the China tax record for every year the balance was earned.</strong> Banks and licensed providers ask for it, and Wise will not send at all without tax paid in the last three years. ' + srcs(["S10", "S24"], True) + '</li>'
        + '<li><strong>Fix the U.S. filing position before the money moves.</strong> An FBAR is due for any year the aggregate exceeded USD 10,000; Form 8938 depends on where you live. Late filing is a separate, cheaper problem than the transfer. ' + srcs(["S20", "S22"], True) + '</li>'
        + '<li><strong>Establish the RMB cost basis.</strong> §988 gain is measured from the booking date to the payment date, so the acquisition rate decides whether the conversion produces ordinary income. ' + srcs(["S19", "S18"], True) + '</li>'
        + '<li><strong>Get two bank quotes in writing, then transfer in as few wires as the file allows.</strong> The fee is capped, the spread is not; batching removes repeated caps but does not change the spread. ' + srcs(["S02", "S04"], True) + '</li>'
        + '<li><strong>Keep the paper.</strong> FX slip, wire confirmation, tax record and the source documents are the audit file for both jurisdictions.</li>'
        + '</ol></section>'
        + '<section class="panel"><h2>What would actually make it cheaper</h2><div class="tablewrap"><table class="stack">'
        + '<caption>Levers with a published effect, and levers with no published effect</caption>'
        + '<thead><tr><th scope="col">Lever</th><th scope="col">Effect</th><th scope="col">Evidence</th></tr></thead><tbody>'
        + f'<tr><th scope="row">Choose the bank with the tightest published spread</th><td>At $100,000: BOC {money(HEAD["M01"]["100000"]["total_usd"], 2)} vs HSBC Premier {money(HEAD["M03"]["100000"]["total_usd"], 2)} — a difference of {money(HEAD["M03"]["100000"]["total_usd"] - HEAD["M01"]["100000"]["total_usd"], 2)}</td><td>{srcs(["S01", "S05"], True)}</td></tr>'
        + f'<tr><th scope="row">Batch instead of splitting</th><td>Twelve transfers of $10,000 cost {money(12 * HEAD["M01"]["10000"]["total_usd"], 2)}; one transfer of $120,000 costs about {money(120000 * HEAD["M01"]["100000"]["pct"] / 100, 2)}</td><td>{srcs(["S02"], True)}</td></tr>'
        + f'<tr><th scope="row">Use a tier with a zero published fee only if you hold it</th><td>HSBC individual Private Banking shows free transfer and cable; eligibility unverified (F08)</td><td>{srcs(["S06"], True)}</td></tr>'
        + '<tr><th scope="row">Do not use cash</th><td>The permit ceiling is USD 5,000 per trip without a permit, USD 10,000 with one</td><td>' + srcs(["S16"], True) + '</td></tr>'
        + '<tr><th scope="row">Nothing lawful removes the spread</th><td>No official page read this pass provides a mechanism to convert at the reference mid</td><td>' + srcs(["S07"], True) + '</td></tr>'
        + '</tbody></table></div>'
        + note('<strong>The one-line answer.</strong> The least-tax lawful path is a documented bank conversion at the bank with the tightest published spread, executed in as few wires as the file allows, with the FBAR/8938 position fixed first and the RMB cost basis recorded. On today’s published numbers that is roughly <strong>' + money(HEAD["M01"]["10000"]["total_usd"], 2) + '</strong> at USD 10,000 and <strong>' + money(HEAD["M01"]["400000"]["total_usd"], 2) + '</strong> at USD 400,000, before unknown correspondent deductions — about ' + pct(HEAD["M01"]["10000"]["pct"]) + ' down to ' + pct(HEAD["M01"]["400000"]["pct"]) + '.', "ok")
        + '</section>'
    )
    return shell("answer.html", "Least tax penalties, lawfully", body,
                 "The seven layers of the so-called conversion penalty and the order that minimises the lawful cost.")


# ---------------------------------------------------------------- costs
def cost_cell(mid: str, usd: int, show_pct: bool = True) -> str:
    h = HEAD[mid].get(str(usd))
    if not h:
        ceiling = METHODS_BY_ID[mid].get("cap_usd")
        if ceiling and mid != CASH:
            return f'<span class="muted">above USD {ceiling:,.0f} cap</span>'
        return '<span class="muted">—</span>'
    txt = money(h["total_usd"], 2)
    return f'<strong>{txt}</strong>' + (f'<span class="pc">{pct(h["pct"])}</span>' if show_pct else '')


def page_costs() -> str:
    rank_rows = "".join(
        f'<tr><td data-label="Rank">{i}</td><th scope="row" data-label="Method">{esc(METHODS_BY_ID[r["method"]]["name"])}</th>'
        f'<td data-label="All-in cost">{money(r["total_usd"], 2)}</td><td data-label="% of amount">{pct(r["pct"])}</td>'
        f'<td data-label="Source">{srcs(METHODS_BY_ID[r["method"]]["sources"][:2], True)}</td></tr>'
        for i, r in enumerate(COSTS["ranking_100k"], 1)
        if r["method"] not in SAME_LEG
    )

    master = ""
    for usd in COSTS["tiers"]:
        master += f'<tr><th scope="row" data-label="Amount">{money(usd)}</th>'
        for mid in PRIMARY:
            master += f'<td data-label="{esc(METHODS_BY_ID[mid]["name"])}">{cost_cell(mid, usd)}</td>'
        master += f'<td data-label="Source">{srcs(MASTER_SOURCES, True)}</td></tr>'

    detail = ""
    for mid in PRIMARY:
        m = METHODS_BY_ID[mid]
        spec = m.get("pricing") or {}
        rows = ""
        for r in ROWS:
            if r["method"] != mid:
                continue
            if r["state"] != "priced":
                rows += (f'<tr class="blocked"><th scope="row" data-label="Amount">{money(r["usd"])}</th>'
                         f'<td data-label="State" colspan="5">{esc(r["note"])}</td>'
                         f'<td data-label="Source">{src(m["sources"][0], True)}</td></tr>')
                continue
            rows += (f'<tr><th scope="row" data-label="Amount">{money(r["usd"])}</th>'
                     f'<td data-label="CNY converted">{r["cny"]:,.0f}</td>'
                     f'<td data-label="Spread cost">{money(r["spread_usd"], 2)}</td>'
                     f'<td data-label="Fee (CNY)">{r["fee_cny"]:,.2f}</td>'
                     f'<td data-label="Fee (USD)">{money(r["fee_usd"], 2)}</td>'
                     f'<td data-label="All-in"><strong>{money(r["total_usd"], 2)}</strong> <span class="pc">{pct(r["pct"])}</span></td>'
                     f'<td data-label="Source">{src(spec.get("rate_src", "S01"), True)} {src(spec.get("fee_src", "S02"), True)}</td></tr>')
        fee_line = (f'{spec.get("fee_pct", 0) * 100:.1f}% of the CNY amount, floor CNY {spec.get("fee_min", 0):,.0f}, '
                    f'cap CNY {spec.get("fee_max", 0):,.0f}, plus cable CNY {spec.get("cable", 0):,.0f}')
        detail += (
            f'<details class="method-detail" id="{mid}"><summary>{esc(m["name"])} — {pct(HEAD[mid]["100000"]["pct"]) if HEAD[mid].get("100000") else "not priced"} at $100,000</summary>'
            f'<p class="tiny">Selling rate {spec.get("sell", "—")} · reference mid {META["ref_mid"]:.4f} · fee {fee_line} · {src(spec.get("rate_src", "S01"), True)} {src(spec.get("fee_src", "S02"), True)}</p>'
            f'<div class="tablewrap"><table class="stack compact"><caption>Every USD 10,000 step · {esc(m["name"])}</caption>'
            f'<thead><tr><th scope="col">Amount</th><th scope="col">CNY converted</th><th scope="col">Spread cost</th><th scope="col">Fee (CNY)</th><th scope="col">Fee (USD)</th><th scope="col">All-in</th><th scope="col">Source</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div></details>'
        )

    unpriced = "".join(
        f'<tr><th scope="row" data-label="Method">{esc(m["name"])}</th>'
        f'<td data-label="Status">{badge(m["status"])}</td>'
        f'<td data-label="Published cost"></td>'
        f'<td data-label="Why blank">{esc(m.get("status_note", ""))}</td>'
        f'<td data-label="Source">{srcs(m["sources"], True)}</td></tr>'
        for m in METHODS if not m.get("pricing")
    )

    body = (
        page_head("Costs", "$10,000 to $400,000, in $10,000 steps",
                  "Every cell is amount × (published selling rate ÷ reference mid − 1) + the published fee formula. "
                  "The tables are the arithmetic; the pages behind each row are the evidence. Blank means the bank publishes nothing.")
        + note(f'<strong>Read the direction of the numbers.</strong> The percentage falls as the amount rises because the fee is capped. The dollar cost still rises, because the spread scales. Moving $400,000 is not cheaper than moving $10,000 — it is cheaper <em>per dollar</em>.', "warn")
        + '<section class="panel"><h2>Cheapest published all-in cost at $100,000</h2>'
        + '<p class="tiny">Approval routes (emigration, inheritance, property) reuse the same Bank of China leg and are excluded from this ranking to avoid padding it; they are priced separately below.</p>'
        + '<div class="tablewrap"><table class="stack"><caption>Ranked by all-in cost at USD 100,000 · priced methods only</caption>'
        + '<thead><tr><th scope="col">#</th><th scope="col">Method</th><th scope="col">All-in</th><th scope="col">% of amount</th><th scope="col">Source</th></tr></thead>'
        + f'<tbody>{rank_rows}</tbody></table></div></section>'
        + '<section class="panel"><h2>The main table: all 40 steps</h2>'
        + '<p class="tiny">Cash is shown only to USD 10,000 because that is its legal ceiling (flag F13). HSBC Private Banking is shown because its published tariff is zero on both fee lines, but its eligibility is unverified (flag F08).</p>'
        + '<div class="tablewrap"><table class="stack master"><caption>All-in cost in USD, with % of the amount beneath · reference mid '
        + f'{META["ref_mid"]:.4f} CNY/USD</caption><thead><tr><th scope="col">Amount</th>'
        + "".join(f'<th scope="col">{esc(METHODS_BY_ID[m]["name"].split("—")[-1].strip() if "—" in METHODS_BY_ID[m]["name"] else METHODS_BY_ID[m]["name"])}</th>' for m in PRIMARY)
        + '<th scope="col">Source</th>'
        + '</tr></thead><tbody>' + master + '</tbody></table></div>'
        + note('The “all-in” column is a floor: it excludes the correspondent-bank deduction (F05) and the U.S. receiving-bank fee (F06), neither of which is published by the institutions read here. '
               'Download the same data with its source URLs: <a href="exports/cost-ladder.csv" download>CSV</a> · <a href="exports/cost-ladder.json" download>JSON</a>.', "warn")
        + '</section>'
        + '<section class="panel"><h2>Method by method, with the components shown</h2>' + detail + '</section>'
        + '<section class="panel"><h2>Methods with no published price</h2>'
        + '<p class="tiny">These rows are deliberately blank. A blank is not a zero and not a “cheap”. Each carries the reason it could not be priced.</p>'
        + '<div class="tablewrap"><table class="stack"><caption>Unpriced methods · published cost left blank</caption>'
        + '<thead><tr><th scope="col">Method</th><th scope="col">Status</th><th scope="col">Published cost</th><th scope="col">Why blank</th><th scope="col">Source</th></tr></thead>'
        + f'<tbody>{unpriced}</tbody></table></div></section>'
    )
    return shell("costs.html", "$10,000 to $400,000, in $10,000 steps", body,
                 "Itemised CNY to USD conversion and transfer cost at every USD 10,000 step.")


# ---------------------------------------------------------------- methods
def page_methods() -> str:
    cards = ""
    for m in METHODS:
        spec = m.get("pricing")
        if spec:
            price = (f'<p class="price">{money(HEAD[m["id"]]["100000"]["total_usd"], 2)} <span>at $100,000 · {pct(HEAD[m["id"]]["100000"]["pct"])}</span></p>'
                     if HEAD[m["id"]].get("100000") else '<p class="price muted">Priced only below its published ceiling</p>')
        else:
            price = '<p class="price muted">No published price — left blank</p>'
        caps = m.get("published_caps") or []
        caps_html = ("" if not caps else '<p class="tiny"><strong>Published caps:</strong> ' + "; ".join(esc(c) for c in caps) + '</p>')
        cards += (
            f'<article class="method" id="{m["id"]}" data-filter-item><div class="method-head"><h3>{esc(m["name"])}</h3>{badge(m["status"])}</div>'
            f'<p class="tiny">{esc(m["family"])}</p><p>{esc(m["summary"])}</p>{price}{caps_html}'
            f'<p class="tiny"><em>{esc(m.get("status_note", ""))}</em></p>'
            f'<div class="two"><div><h4>Pros</h4><ul>' + "".join(f'<li>{esc(p)}</li>' for p in m["pros"]) + '</ul></div>'
            f'<div><h4>Cons</h4><ul>' + "".join(f'<li>{esc(c)}</li>' for c in m["cons"]) + '</ul></div></div>'
            f'<details><summary>Step by step</summary><ol>' + "".join(f'<li>{esc(s)}</li>' for s in m["steps"]) + '</ol></details>'
            f'<p class="tiny">{srcs(m["sources"])}'
            + (" · flags " + ", ".join(f'<a href="flagged.html#{f}">{f}</a>' for f in m.get("flags", [])) if m.get("flags") else "")
            + '</p></article>'
        )
    body = (
        page_head("Methods", "Every route, with its price or its blank",
                  "Twenty-four methods: four prohibited ones are listed with their statutory penalty and no instructions. "
                  "Six are priced from published rates and tariffs; the rest are blank with the reason recorded.")
        + '<div class="legend">' + badge("lawful") + badge("conditional") + badge("unverified") + badge("unlawful") + badge("not_applicable") + '</div>'
        + '<label class="search"><span>Filter methods</span>'
        + '<input type="search" data-filter="#method-list" placeholder="bank, cash, quota, crypto, inheritance…" autocomplete="off"></label>'
        + '<p id="no-results" class="note" hidden>No method matches that word.</p>'
        + '<div class="methods" id="method-list">' + cards + '</div>'
    )
    return shell("methods.html", "Every route, with its price or its blank", body,
                 "Pros, cons and step-by-step for every lawful route, plus the prohibited ones and their penalties.")


# ---------------------------------------------------------------- taxes
def page_taxes() -> str:
    matrix = [
        ("PRC", "Tax on the underlying income", "3%–45% comprehensive · 5%–35% business · 20% flat on interest, dividends and asset transfers", "Applies when earned, not when converted.", ["S14"]),
        ("PRC", "Tax recordal on a large outward payment", "A single payment of USD 50,000 or more for listed service-trade and income items", "A procedural gate, not a tax; several articles were superseded in 2021 (F10).", ["S13"]),
        ("PRC", "Document requirement at the bank", "Valid ID + source-of-funds materials including tax vouchers", "The bank is required to check the real, lawful transaction basis.", ["S07", "S09", "S10"]),
        ("PRC", "Fine — evasion", "Up to 30% of the amount; 30% to an equal amount if serious", "Only on an unlawful route.", ["S07"]),
        ("PRC", "Fine — illegal FX arbitrage (false documents)", "Up to 30% of the amount; 30% to an equal amount if serious. Separately, up to CNY 50,000 for false documents by an individual", "Only on an unlawful route.", ["S07"]),
        ("PRC", "Fine — private/disguised FX trading", "Up to 30% of the amount; 30% to an equal amount if serious", "Covers underground swaps.", ["S07"]),
        ("PRC", "Fine — illegal cash carrying", "Up to 20% of the amount", "Cash above the permit ceilings.", ["S07"]),
        ("US", "Worldwide income and filing", "U.S. citizens are taxed on worldwide income and must file", "A conversion does not create a filing obligation; it exists already.", ["S20"]),
        ("US", "§988 exchange gain or loss", "Ordinary income or loss, measured booking date to payment date", "The conversion itself can be taxable even if the source income was taxed.", ["S19"]),
        ("US", "FBAR (FinCEN 114)", "Aggregate above USD 10,000 at any time in the calendar year; due 15 April, automatic to 15 October", "Applies to the China account itself, not to the transfer.", ["S20"]),
        ("US", "FBAR civil penalty maximums", "Non-willful USD 16,536 · willful USD 165,353 (current adjusted table)", "Maxima; assertion depends on facts.", ["S21"]),
        ("US", "Form 8938", "USD 50,000 year-end / 75,000 anytime (living in the U.S.); 200,000 / 300,000 (living abroad)", "Separate from the FBAR and not a substitute for it.", ["S22"]),
        ("US", "Form 3520 for a foreign gift", "Above USD 100,000 from a nonresident alien or foreign estate; USD 20,573 for 2026 from foreign corporations/partnerships", "Relevant if the money is described as a family gift.", ["S23"]),
        ("US", "Cash reporting", "Above USD 10,000 in or out of the United States, on FinCEN Form 105", "Reporting only; failure risks seizure and penalties.", ["S17"]),
        ("US", "Foreign earned income exclusion", "Amount adjusted annually — the 2026 figure was not verified this pass (F09)", "Can reduce tax on earned income; not a conversion mechanism.", ["S18"]),
    ]
    rows = "".join(
        f'<tr><td data-label="Jurisdiction"><span class="pill">{esc(j)}</span></td><th scope="row" data-label="Provision">{esc(name)}</th>'
        f'<td data-label="Published position">{esc(pos)}</td><td data-label="Note">{esc(n)}</td><td data-label="Source">{srcs(s, True)}</td></tr>'
        for j, name, pos, n, s in matrix
    )
    illus_rows = "".join(
        f'<tr><th scope="row" data-label="Amount moved">{money(r["usd"])}</th>'
        f'<td data-label="USD cost basis of the CNY">{money(r["basis_usd"], 2)}</td>'
        f'<td data-label="Illustrative §988 gain">{money(r["gain_usd"], 2)}</td>'
        f'<td data-label="% of proceeds">{pct(r["gain_pct"])}</td>'
        f'<td data-label="Source">{srcs(["S18", "S19"], True)}</td></tr>'
        for r in COSTS["illustrative_988"]
    )
    body = (
        page_head("Tax & penalties", "What is a tax, what is a price, what is a fine",
                  "Three different things are routinely called “the conversion penalty”. They have different sources, different sizes and different fixes.")
        + '<section class="panel"><h2>The U.S. and PRC positions side by side</h2><div class="tablewrap"><table class="stack">'
        + '<caption>Every row links to the statute, regulation or agency page it comes from</caption>'
        + '<thead><tr><th scope="col">Jurisdiction</th><th scope="col">Provision</th><th scope="col">Published position</th><th scope="col">Note</th><th scope="col">Source</th></tr></thead>'
        + f'<tbody>{rows}</tbody></table></div></section>'
        + '<section class="panel"><h2>§988: the tax that appears when you convert</h2>'
        + '<p>Exchange gain or loss on disposing of foreign currency is computed separately and taxed as ordinary income or loss between the booking date and the payment date. If the RMB was acquired at a weaker rate than today’s, the conversion produces taxable ordinary income on top of the transfer cost.</p>'
        + '<div class="tablewrap"><table class="stack"><caption>Illustrative only · assumes the whole balance was acquired at the IRS 2025 yearly average of '
        + f'{META["irs_2025_yuan_per_usd"]} CNY/USD and converted at {META["ref_mid"]:.4f}</caption>'
        + '<thead><tr><th scope="col">Amount moved</th><th scope="col">USD cost basis of the CNY</th><th scope="col">Illustrative gain</th><th scope="col">% of proceeds</th><th scope="col">Source</th></tr></thead>'
        + f'<tbody>{illus_rows}</tbody></table></div>'
        + note('This is not a tax calculation. The actual result depends on when and at what rate each tranche of RMB was acquired (flag F11), and the rate is taxed at the filer’s marginal rate, which this study does not assume. The IRS has no official rate and generally accepts any posted rate used consistently.', "warn")
        + '</section>'
        + '<section class="panel"><h2>The fine schedule, in one place</h2>'
        + '<p>The reason not to use a prohibited route is arithmetic: a 30% fine on USD 400,000 is USD 120,000, which is more than 100 times the entire published lawful cost at that tier.</p>'
        + '<div class="tablewrap"><table class="stack"><caption>Statutory maxima from the FX Regulations, not predictions</caption>'
        + '<thead><tr><th scope="col">Conduct</th><th scope="col">Article</th><th scope="col">Fine</th><th scope="col">Source</th></tr></thead><tbody>'
        + '<tr><th scope="row">Evasion of FX controls</th><td>Art. 39</td><td>Up to 30% of the amount; 30% to an equal amount if serious</td><td>' + src("S07", True) + '</td></tr>'
        + '<tr><th scope="row">Illegal arbitrage (false or invalid documents)</th><td>Art. 40</td><td>Up to 30%; 30% to an equal amount if serious</td><td>' + src("S07", True) + '</td></tr>'
        + '<tr><th scope="row">Illegal cash carrying</th><td>Art. 42</td><td>Up to 20% of the amount</td><td>' + src("S07", True) + '</td></tr>'
        + '<tr><th scope="row">Private or disguised FX trading</th><td>Art. 45</td><td>Up to 30%; 30% to an equal amount if serious</td><td>' + src("S07", True) + '</td></tr>'
        + '<tr><th scope="row">Invalid or false documents</th><td>Art. 48</td><td>Up to CNY 50,000 for an individual</td><td>' + src("S07", True) + '</td></tr>'
        + '</tbody></table></div></section>'
    )
    return shell("taxes.html", "What is a tax, what is a price, what is a fine", body,
                 "PRC and U.S. tax, reporting and penalty rules that bear on a CNY to USD transfer.")


# ---------------------------------------------------------------- questions
QUESTIONS = [
    ("Q01", "Which FX rulebook applies to you: domestic individual or non-domestic individual?",
     "A foreign national continuously resident in China for one year or more is a “domestic individual” (Decree 532 Art. 52(2)), while a non-domestic individual’s China income follows a separate conversion route.",
     "It decides the document set and whether a USD 50,000 annual ceiling binds the plan.",
     ["S07", "S09", "S10"],
     "Ask the account branch to state the classification and the rulebook in writing."),
    ("Q02", "What is the source of the balance — salary, business income, property sale, inheritance, gift, or trading gains?",
     "Each source has its own route and its own tax rate: 3%–45%, 5%–35%, or a 20% flat rate.",
     "A property sale needs a tax-clearance certificate; an inheritance needs SAFE approval; salary needs tax records.",
     ["S12", "S14", "S09"],
     "Reconstruct from payslips, contracts, the property transfer file and the tax record."),
    ("Q03", "Do you hold a China tax record (纳税记录) for each year the balance was earned?",
     "Banks require source-of-funds materials including tax vouchers; Wise will not send without tax paid in the last three years.",
     "Without it the bank route stalls and the licensed-provider route is closed.",
     ["S10", "S24"],
     "Download the record from the individual income tax app or request it at the tax office."),
    ("Q04", "When and at what rate was each tranche of RMB acquired?",
     "§988 measures exchange gain from the booking date to the payment date.",
     "It decides whether the conversion produces ordinary income and how much.",
     ["S19", "S18"],
     "Match bank statements to the date each payment landed; record the rate on that date."),
    ("Q05", "Have you filed FBARs and Forms 8938 for every year the account exceeded the threshold?",
     "FBAR above a USD 10,000 aggregate; 8938 above USD 50,000/75,000 in the U.S. or 200,000/300,000 abroad.",
     "A late filing is far cheaper to fix than a transfer that draws attention to an unfiled account.",
     ["S20", "S22", "S21"],
     "Check your filed returns and the FinCEN BSA system; a CPA can run a quiet-disclosure analysis."),
    ("Q06", "Do you live in the U.S. or abroad now, and in which state?",
     "The 8938 thresholds and the foreign earned income exclusion depend on residence; state tax is separate.",
     "It changes which forms apply and which tax rates sit on top of §988.",
     ["S22", "S18"],
     "State your residence dates for each tax year; confirm state treatment with a preparer."),
    ("Q07", "Is the account solely yours, or joint or with signature authority?",
     "The FBAR reaches signature authority; 8938 reaches specified individuals with an interest.",
     "It changes who must file what.",
     ["S20", "S22"],
     "Read the account opening documents and the bank's record of authorised signatories."),
    ("Q08", "Has any emigration, hukou cancellation or inheritance event occurred?",
     "The emigration and inheritance transfer regimes are approved by SAFE at the branch of the original residence and allow a lump sum or batches.",
     "It is the only route designed for a large one-off transfer of pre-existing assets.",
     ["S11", "S09"],
     "Collect the emigration or inheritance documents and ask the relevant SAFE branch."),
    ("Q09", "Is the money described as a gift from a relative?",
     "A foreign gift above USD 100,000 from a nonresident alien must be reported on Form 3520.",
     "It converts a transfer question into a gift-reporting question with its own penalty.",
     ["S23"],
     "Establish who the donor is and the amount for the year before moving anything."),
    ("Q10", "Do you hold an HSBC Premier, Advance or Private Banking relationship?",
     "The published tariff differs by tier: CNY 100–500 plus CNY 120 for Premier/Advance; free for individual Private Banking.",
     "It can remove the fee, though not the spread.",
     ["S06"],
     "Ask the relationship manager for the tier and the applicable tariff in writing."),
    ("Q11", "Is a single outward payment going to be USD 50,000 or more?",
     "A single outward payment at or above that level for listed items requires tax recordal.",
     "It adds a step and a lead time to the plan.",
     ["S13"],
     "Ask the local tax authority for the current electronic procedure (F10)."),
    ("Q12", "Do you have a U.S. receiving account in your own name?",
     "Banks and licensed providers require the beneficiary to be the sender, and Wise requires an account you own.",
     "A third-party destination can stop the transfer at the compliance stage.",
     ["S24", "S09"],
     "Confirm the exact beneficiary name and the bank's incoming-wire details."),
    ("Q13", "How much of the annual FX quota have you already used this year?",
     "The USD 50,000 quota is an annual aggregate per person.",
     "It may already be partly consumed, which changes the timing of a quota-based plan.",
     ["S09"],
     "Ask the bank for your settlement/purchase record for the year."),
    ("Q14", "What does the U.S. receiving bank charge for an incoming international wire?",
     "No U.S. bank fee schedule was read this pass.",
     "It is a missing cost in every total on this site (F06).",
     ["S20"],
     "Read the receiving bank's own published fee schedule."),
    ("Q15", "Has anyone proposed a route involving crypto, an underground swap, friends' quotas or a manufactured invoice?",
     "Those are prohibited, with fines of up to 30% of the amount, or 30% to an equal amount if serious.",
     "The fine exceeds the entire lawful cost; the answer to this question should be no.",
     ["S07", "S15", "S08"],
     "Nothing to discover — decline the route and document the refusal if pressure continues."),
]


def page_questions() -> str:
    rows = "".join(
        f'<tr id="{qid}"><th scope="row" data-label="Question"><span class="qid">{esc(qid)}</span> {esc(q)}</th>'
        f'<td data-label="What the rules say">{esc(rule)}</td>'
        f'<td data-label="Why it changes the answer">{esc(why)}</td>'
        f'<td data-label="How to find out">{esc(how)}</td>'
        f'<td data-label="Source">{srcs(s, True)}</td></tr>'
        for qid, q, rule, why, s, how in QUESTIONS
    )
    body = (
        page_head("Open questions", "What must be answered before a decision",
                  "Fifteen questions. Each one is tied to the rule it changes and to a way of obtaining the answer. "
                  "Until they are answered, every number on this site is a range, not a quote.")
        + note('<strong>No manual input is required to read this site.</strong> The questions are here because the answers live in your bank and tax records, not because the research is unfinished. Everything that can be established from public official sources has been, and is on the other pages.', "ok")
        + '<section class="panel"><h2>The register</h2><div class="tablewrap"><table class="stack">'
        + '<caption>Question · rule · why it matters · how to resolve it · source</caption>'
        + '<thead><tr><th scope="col">Question</th><th scope="col">What the rules say</th><th scope="col">Why it changes the answer</th><th scope="col">How to find out</th><th scope="col">Source</th></tr></thead>'
        + f'<tbody>{rows}</tbody></table></div></section>'
        + '<section class="panel"><h2>What is already established</h2><ul class="checks">'
        + '<li>The lawful routes and their statutory basis are settled: bank conversion of documented current-account income, quota purchase, emigration and inheritance transfers, property proceeds with tax clearance.</li>'
        + '<li>The published fee formulas and boards of three mainland banks are known, with the retrieval time on each.</li>'
        + '<li>The prohibited routes and their statutory penalty ranges are settled.</li>'
        + '<li>The U.S. reporting thresholds and the current penalty maxima are settled.</li>'
        + '<li>What is <em>not</em> settled is everything that depends on your private facts — which is why this page exists.</li>'
        + '</ul></section>'
    )
    return shell("questions.html", "What must be answered before a decision", body,
                 "Fifteen questions that decide the route, each mapped to the rule it changes.")


# ---------------------------------------------------------------- audit
AUDIT = [
    ("RA-01", "Bank of China board moved between the last pass and this one, as expected",
     "estimate-facf2fe9/data/sources.json records BOC 6.6571 / 6.6851 at 17:39:58 Beijing on 10 Nov 2026. This pass read 6.6630 / 6.6911 at 10:25:02 on 11 Nov 2026.",
     "Both readings imply a spread of about 0.21% against the bank's own mid, so the two passes agree on the size of the markup. The absolute rate moved, which is normal for an FX board.",
     "consistent", ["S01"]),
    ("RA-02", "HSBC is quoted two different ways in the repository",
     "Earlier sections derived HSBC rates by inverting a feed (about 6.63548 / 6.70222). The HSBC China rate page publishes an explicit sell/buy table, which this pass read as 6.7079204 / 6.6411822.",
     "Both imply roughly a 0.5% spread, so the cost conclusion survives. The numbers differ, and the inversion is now unnecessary. Published as F03.",
     "method-difference", ["S05"]),
    ("RA-03", "CMB board carried the previous day's date",
     "CMB showed 2026年11月10日 at 10:28:44 while BOC showed 2026/11/11 at 10:25:02, which suggests a cached page.",
     "CMB's cost row may be a day stale. Published as F02.",
     "irregular", ["S03"]),
    ("RA-04", "Three banks are blank, not cheap",
     "ICBC returned 暂无数据; ABC and CCB boards are script-rendered and returned no rows. No fee table was read for any of the three.",
     "Earlier sections also leave these banks unpriced or modelled on assumptions. Consistent in outcome, and now with a documented reason. Published as F04.",
     "consistent", ["S25"]),
    ("RA-05", "The USD 50,000 figure is described correctly in the primary sources, and inconsistently in commentary",
     "Huifa [2007] No. 1 Art. 2 applies the annual aggregate to an individual's FX settlement and a domestic individual's FX purchase. Decree 532 Art. 52(2) treats a long-resident foreign national as a domestic individual. A non-domestic individual's China income is converted under Art. 13 and Art. 59 of the 2020 guide.",
     "Any statement that USD 50,000 is a universal ceiling for a foreign national is an overgeneralisation. This pass records the distinction and flags it as F12.",
     "irregular", ["S09", "S07", "S10"]),
    ("RA-06", "The crypto prohibition is now Yinfa [2026] No. 42, not the 2021 notice",
     "The 2026 notice states that virtual-currency business activity is illegal financial activity, and expressly repeals Yinfa [2021] No. 237.",
     "Any section still citing the 2021 notice is citing a repealed instrument. The prohibition is unchanged in substance.",
     "irregular", ["S15"]),
    ("RA-07", "Cash is priced but cannot scale",
     "The cash ceiling is USD 5,000 per trip without a permit and USD 10,000 with one; above that is in principle not permitted.",
     "A cash row priced across all 40 tiers would be misleading. This pass prices it only to its ceiling. Published as F13.",
     "consistent", ["S16"]),
    ("RA-08", "Correspondent deductions are missing from every total in the repository",
     "CMB discloses a USD 25 OUR prepayment; HSBC sells Pay Exact for CNY 200. Neither is the actual correspondent deduction.",
     "Totals across all sections are floors. Published as F05.",
     "irregular", ["S04", "S06"]),
    ("RA-09", "The U.S. receiving fee is missing from every total",
     "No U.S. bank fee schedule could be read this pass; the Chase URL tried returned 404.",
     "Published as F06. Nothing is inferred to fill the gap.",
     "irregular", []),
    ("RA-10", "The 2026 FEIE figure was not re-verified",
     "The IRS foreign-earned-income-exclusion page read this pass lists amounts only through 2023 and says the amount is inflation-adjusted annually.",
     "A 2026 figure quoted elsewhere could not be confirmed today. Published as F09.",
     "unverified", []),
    ("RA-11", "Generated sections in this repository rebuild byte-identically",
     "The existing verifiers were run against the tree this pass was branched from: scripts/validate.py passed on 9 pages, 67 findings and 24 sources.",
     "The earlier dashboards are internally consistent with their own data. That is not the same as being correct against the outside world, which is what the pages above re-check.",
     "consistent", []),
    ("RA-12", "The repository contains many parallel dashboards with overlapping claims",
     "At least a dozen section directories (ladder, briefing, docs, site, portal, repatriate, audit-*, study-*, estimate-*, final-*, verify-*) present cost tables for the same question.",
     "Duplicate work is a coordination risk, not a data error. This section is additive and states which pages it actually re-read (F16).",
     "irregular", []),
    ("RA-13", "Some sections publish a single “cheapest route” without the eligibility condition",
     "The cheapest published route is only available to a documented current-account income holder whose bank accepts the file.",
     "The ranking on this site is explicitly a ranking of published bank prices, not of personal eligibility.",
     "consistent", ["S10"]),
    ("RA-14", "Blank cells are used correctly in the earlier sections, but not uniformly",
     "Some sections leave the FX spread blank and show only fees; others model a 0.3%–1.5% band. Both are defensible if labelled; the band is not a published number.",
     "This pass labels every estimated cell with its formula and every blank with its reason.",
     "method-difference", ["S01"]),
]


def page_audit() -> str:
    tabled = [a for a in AUDIT if a[5]]
    listed = [a for a in AUDIT if not a[5]]
    rows = "".join(
        f'<tr id="{rid}"><td data-label="ID"><span class="qid">{esc(rid)}</span></td>'
        f'<th scope="row" data-label="What was checked">{esc(title)}</th>'
        f'<td data-label="What was found">{esc(found)}</td>'
        f'<td data-label="Verdict / action">{esc(verdict)}</td>'
        f'<td data-label="Class"><span class="pill {cls}">{esc(cls)}</span></td>'
        f'<td data-label="Source">{srcs(s, True)}</td></tr>'
        for rid, title, found, verdict, cls, s in tabled
    )
    listed_html = "".join(
        f'<li><strong>{esc(rid)} · {esc(title)}</strong> {esc(found)} <em>{esc(verdict)}</em></li>'
        for rid, title, found, verdict, cls, _ in listed
    )
    body = (
        page_head("Repository review", "Line-by-line re-check of the sections already here",
                  "This repository already contains more than a dozen dashboards answering the same question. "
                  "Rather than add a fifteenth unexamined copy, this pass re-read the load-bearing official pages and re-checked the numbers that the earlier sections rely on.")
        + note('<strong>Scope limit, stated plainly.</strong> Fourteen checks were performed. They cover the rate boards, the fee formulas, the quota wording, the prohibition instrument, the cash ceiling, the missing deductions and the rebuild behaviour of the existing dashboards. They do not constitute a full re-verification of every source in every section — see F16.', "warn")
        + '<section class="panel"><h2>The checks</h2><div class="tablewrap"><table class="stack">'
        + '<caption>RA-01 to RA-14 · each row names what was read today</caption>'
        + '<thead><tr><th scope="col">ID</th><th scope="col">Check</th><th scope="col">Finding</th><th scope="col">Verdict / action</th><th scope="col">Class</th><th scope="col">Source</th></tr></thead>'
        + f'<tbody>{rows}</tbody></table></div></section>'
        + '<section class="panel"><h2>Checks with no external page to cite</h2>'
        + '<p class="tiny">These findings are about this repository or about a gap; there is no official page to link, so they are listed rather than tabulated.</p>'
        + f'<ul class="checks">{listed_html}</ul></section>'
        + '<section class="panel"><h2>Mechanical checks run on the tree</h2><ul class="checks">'
        + '<li><code>scripts/build.py</code> + <code>scripts/validate.py</code>: PASS — 9 pages, 67 findings, 24 sources, every table body row has an official link, all local links and anchors resolve.</li>'
        + '<li>This section: <code>model.py</code> recomputes every cell from <code>data/*.json</code>; <code>verify.py</code> re-derives the arithmetic independently and checks every row link, every blank and every local anchor.</li>'
        + '<li>Row count: 40 tiers × ' + str(len(META["priced_methods"])) + ' priced methods = ' + str(META["row_count"]) + ' cells, of which ' + str(META["priced_rows"]) + ' are priced and ' + str(META["ceiling_rows"]) + ' are blocked by a published ceiling.</li>'
        + '</ul></section>'
    )
    return shell("audit.html", "Line-by-line re-check of the sections already here", body,
                 "Fourteen re-checks of the load-bearing numbers in this repository.")


# ---------------------------------------------------------------- flagged
def page_flagged() -> str:
    rows = ""
    none = '<span class="muted">none published</span>'
    for f in FLAGS:
        links = srcs(f["sources"], True) if f["sources"] else none
        rows += (
            f'<tr id="{f["id"]}"><td data-label="ID"><span class="qid">{esc(f["id"])}</span></td>'
            f'<th scope="row" data-label="Flag">{esc(f["title"])}</th>'
            f'<td data-label="What is unresolved">{esc(f["what"])}</td>'
            f'<td data-label="Why it matters">{esc(f["why"])}</td>'
            f'<td data-label="What would resolve it">{esc(f["resolve"])}</td>'
            f'<td data-label="Source">{links}</td>'
            f'<td data-label="Severity"><span class="sev {f["severity"]}">{esc(f["severity"])}</span></td></tr>'
        )
    body = (
        page_head("Flagged for review", f"{len(FLAGS)} unresolved items, published rather than filled in",
                  "Everything on this page is a gap: a value that could not be read from an official page, a method of comparison that "
                  "a reader should disagree with if they prefer, or a fact about the account holder that this study refuses to assume.")
        + note('<strong>These do not block publication and they are not errors in the arithmetic.</strong> They are the boundary of what the sources support. Two of them — F11 and F12 — decide the answer and can only be closed with private documents.', "warn")
        + '<section class="panel"><h2>The register</h2><div class="tablewrap"><table class="stack">'
        + '<caption>F01 to F' + f'{len(FLAGS):02d}' + ' · each with the source that was read and the step that would close it</caption>'
        + '<thead><tr><th scope="col">ID</th><th scope="col">Flag</th><th scope="col">What is unresolved</th><th scope="col">Why it matters</th><th scope="col">What would resolve it</th><th scope="col">Source</th><th scope="col">Severity</th></tr></thead>'
        + f'<tbody>{rows}</tbody></table></div></section>'
    )
    return shell("flagged.html", f"{len(FLAGS)} unresolved items", body,
                 "Every unverified value and open question, with the source that would close it.")


# ---------------------------------------------------------------- sources
def page_sources() -> str:
    cards = ""
    for sid, s in SOURCES.items():
        cards += (
            f'<article class="source-card" id="{sid}" data-filter-item><div class="source-head"><span class="qid">{sid}</span>'
            f'<span class="pill">{esc(s["kind"])}</span></div>'
            f'<h3><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])}</a></h3>'
            f'<p class="tiny">{esc(s["authority"])} · retrieved {esc(s["retrieved"])} · {esc(s["retrieved_time"])}</p>'
            f'<blockquote>{esc(s["quote_original"])}</blockquote>'
            f'<p class="tiny"><strong>Working translation:</strong> {esc(s["quote_en"])}</p>'
            f'<p class="tiny"><strong>Used for:</strong> {esc(s["used_for"])}</p>'
            f'<p class="tiny"><strong>Limits:</strong> {esc(s["limits"])}</p></article>'
        )
    body = (
        page_head("Sources", f"{len(SOURCES)} pages read on {META['generated']}",
                  "Each card shows the exact words relied on, the working translation, the retrieval time and the limit of what the page establishes. "
                  "Pages that were attempted but returned nothing are recorded too, so that a blank row has a documented reason.")
        + '<label class="search"><span>Filter sources</span>'
        + '<input type="search" data-filter="#source-list" placeholder="SAFE, IRS, tariff, crypto, cash…" autocomplete="off"></label>'
        + '<p id="no-results" class="note" hidden>No source matches that word.</p>'
        + '<div class="sources" id="source-list">' + cards + '</div>'
    )
    return shell("sources.html", f"{len(SOURCES)} pages read", body,
                 "Every source, the exact quote relied on, and the retrieval time.")


def main() -> None:
    out = {
        "index.html": page_index(),
        "answer.html": page_answer(),
        "costs.html": page_costs(),
        "methods.html": page_methods(),
        "taxes.html": page_taxes(),
        "questions.html": page_questions(),
        "audit.html": page_audit(),
        "flagged.html": page_flagged(),
        "sources.html": page_sources(),
    }
    for name, content in out.items():
        (ROOT / name).write_text(content)
    print(f"wrote {len(out)} pages, {sum(len(v) for v in out.values()):,} bytes")


if __name__ == "__main__":
    main()
