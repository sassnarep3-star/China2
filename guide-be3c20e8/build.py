#!/usr/bin/env python3
"""Deterministic static-site generator for guide-be3c20e8.

Inputs: content.py, data/sources.json, data/costs.json,
data/penalty_costs.json, data/review.json.  No clock, network or random value
is used.  Run model.py and audit.py first.

Run: python3 build.py
"""
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"
ASSETS = HERE / "assets"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import content  # noqa: E402

S = content.SRC
LEDGER = content.LEDGER
READ = LEDGER["retrieved"]
COSTS = json.loads((DATA / "costs.json").read_text(encoding="utf-8"))
PEN_COSTS = json.loads((DATA / "penalty_costs.json").read_text(encoding="utf-8"))
REVIEW = json.loads((DATA / "review.json").read_text(encoding="utf-8"))
P = COSTS["params"]
COST_ROWS = COSTS["rows"]
PEN_ROWS = PEN_COSTS["rows"]
FLAGS = content.FLAGS
FLAG_BY_ID = {f["id"]: f for f in FLAGS}
METHODS = content.METHODS
QUESTIONS = content.QUESTIONS
PENALTY = content.PENALTY
SUMMARY = content.SUMMARY

NAV = [
    ("index.html", "Dashboard"),
    ("summary.html", "Executive summary"),
    ("questions.html", "Decision questions"),
    ("methods.html", "Routes"),
    ("costs.html", "Cost ladder"),
    ("penalties.html", "Penalty layers"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
    ("review.html", "Repo audit"),
]

PLACE = dict(content.PLACEHOLDERS)
PLACE.update({
    "PLACEHOLDER": "resolved",
    "SOURCE_COUNT": len(S),
    "READ": READ,
    "SCANNED_FILES": REVIEW["scan"]["text_files"],
    "COST_ROWS": len(COST_ROWS),
    "BOC_SPREAD_PCT": f"{P['boc_spread_pct']:.4f}%",
    "HSBC_SPREAD_PCT": f"{P['hsbc_spread_pct']:.4f}%",
    "BOC_SPREAD_400": content.usd(P["boc_spread_400_usd"]),
    "HSBC_SPREAD_400": content.usd(P["hsbc_spread_400_usd"]),
    "LOW_10_METHOD": P["low_10_method"],
    "LOW_10_VALUE": content.usd(P["low_10_value_usd"]),
    "LOW_400_METHOD": P["low_400_method"],
    "LOW_400_VALUE": content.usd(P["low_400_value_usd"]),
})
PLACE = {k: str(v) for k, v in PLACE.items()}

def e(value):
    return html.escape(str(value), quote=True)

def resolve(value):
    if not isinstance(value, str):
        return value
    def sub(match):
        key = match.group(1)
        if key not in PLACE:
            raise KeyError(f"unresolved placeholder {key}")
        return PLACE[key]
    out = re.sub(r"\{\{([A-Z0-9_]+)\}\}", sub, value)
    if "{{" in out:
        raise ValueError(f"unresolved template text: {out[:120]}")
    return out

def deep_resolve(value):
    if isinstance(value, str):
        return resolve(value)
    if isinstance(value, list):
        return [deep_resolve(v) for v in value]
    if isinstance(value, dict):
        return {k: deep_resolve(v) for k, v in value.items()}
    return value

def src_links(ids, limit=None):
    ids = [x for x in ids if x in S]
    if limit:
        ids = ids[:limit]
    return " ".join(
        f'<a href="{e(S[i]["url"])}" target="_blank" rel="noopener noreferrer" title="{e(S[i]["publisher"])}">{e(i)}</a>'
        for i in ids
    ) or '<span class="blank">blank</span>'

def flag_links(ids):
    return " ".join(f'<a href="flagged.html#{e(i)}">{e(i)}</a>' for i in ids) or "—"

def method_class(status):
    low = status.lower()
    if low.startswith("unlawful"):
        return "unlawful"
    if low.startswith("lawful"):
        return "lawful"
    return "conditional"

def status_key(status):
    low = status.lower()
    if low.startswith("lawful"):
        return "lawful"
    if low.startswith("unlawful"):
        return "unlawful"
    if low.startswith("unverified"):
        return "unverified"
    return "conditional"

def page(title, active, body, description):
    nav_items = []
    for h, t in NAV:
        current = ' aria-current="page"' if h == active else ""
        nav_items.append(f'<li><a href="{h}"{current}>{e(t)}</a></li>')
    nav = "".join(nav_items)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · guide-be3c20e8</title>
<meta name="description" content="{e(description)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="site"><div class="wrap">
  <p class="eyebrow" style="color:#bcd8ff">Independent decision guide · read {e(READ)}</p>
  <h1>{e(title)}</h1>
  <p>CNY to USD for a U.S. person: published inputs only, blanks where facts are unverified, official links on every substantive row.</p>
</div></header>
<nav class="site" aria-label="Sections"><div class="wrap"><ul>{nav}</ul></div></nav>
<main id="content"><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap">
  <p><strong>Research, not advice.</strong> No account facts were supplied, no bank was contacted, no funds moved and no tax return was filed. Every unresolved personal value is blank and flagged.</p>
  <p class="small"><a href="../index.html">Landing hub</a> · <a href="../README.md">README</a> · <a href="../COORDINATION.md">Task board</a> · <a href="EXECUTIVE_SUMMARY.md">Executive summary (Markdown)</a> · <a href="data/costs.csv">Costs CSV</a> · <a href="data/penalty_costs.csv">Penalty CSV</a></p>
  <p class="small">Rate boards are dated reference-only publisher values, not executable quotes. Known totals are arithmetic illustrations; all-in totals are blank by design.</p>
</div></footer>
<script src="assets/app.js"></script>
</body></html>
"""

def write(name, text):
    path = HERE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path

def write_json(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# Data exports (resolved prose, no template tokens)
# ---------------------------------------------------------------------------
write_json("summary.json", deep_resolve({"retrieved": READ, "items": SUMMARY, "params": P}))
write_json("questions.json", deep_resolve({"retrieved": READ, "questions": QUESTIONS}))
write_json("methods.json", deep_resolve({"retrieved": READ, "methods": METHODS}))
write_json("penalty_layers.json", deep_resolve({"retrieved": READ, "layers": PENALTY}))
write_json("flags.json", deep_resolve({"retrieved": READ, "status": "needs review", "flags": FLAGS}))
write_json("pages_manifest.json", {
    "generator": "guide-be3c20e8/build.py",
    "retrieved": READ,
    "pages": [{"href": h, "title": t} for h, t in NAV],
    "exports": sorted(p.name for p in DATA.glob("*.json")) + sorted(p.name for p in DATA.glob("*.csv")),
})

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def milestone_rows():
    rows = []
    for amt in (10000, 100000, 200000, 400000):
        priced = [r for r in COST_ROWS if r["usd"] == amt and r["method_id"] in {"R01", "R05", "R06", "R07", "R08"} and r["total_known_usd"] is not None]
        low = min(priced, key=lambda r: (r["total_known_usd"], r["method_id"]))
        rows.append(f"""<tr>
<th scope="row" data-label="Amount">{content.usd(amt)}</th>
<td class="primary" data-label="Lowest published known total">{content.usd(low['total_known_usd'])}</td>
<td data-label="Method">{e(low['method_id'])} · {e(low['method_name'])}</td>
<td data-label="All-in"><span class="blank">blank + flagged</span></td>
<td class="src" data-label="Official sources">{src_links(low['source_ids'])}</td>
</tr>""")
    return "".join(rows)

index_body = f"""
<section class="callout" id="answer">
  <p class="eyebrow">Start here</p>
  <h2>Least-penalty answer, with its limits</h2>
  <p>{resolve(SUMMARY[0]['text'])}</p>
  <p class="small">{src_links(SUMMARY[0]['sources'])}</p>
</section>
<section class="status" aria-label="At a glance">
  <div class="card"><p class="label">Primary sources</p><p class="value">{len(S)}</p><p>Exact quotes, locators, figures and limitations.</p></div>
  <div class="card"><p class="label">Amount tiers</p><p class="value">{P['tiers']}</p><p>Every {PLACE['STEP']} step from {content.usd(10000)} to {content.usd(400000)}.</p></div>
  <div class="card"><p class="label">Cost rows</p><p class="value">{len(COST_ROWS)}</p><p>{P['methods']} routes × {P['tiers']} tiers, blanks flagged.</p></div>
  <div class="card"><p class="label">Open checks</p><p class="value">{len(FLAGS)}</p><p><a href="flagged.html">Flagged for Review</a> · needs review, non-blocking.</p></div>
</section>
<section id="read-first">
  <h2>Read first</h2>
  <div class="grid">
    <a class="card" href="summary.html"><p class="eyebrow">Decision</p><h3>Executive summary</h3><p>Seven conclusions, each with direct official links and explicit limits.</p></a>
    <a class="card" href="questions.html"><p class="eyebrow">Gate</p><h3>{len(QUESTIONS)} decision questions</h3><p>Known, missing, consequence and an exact discovery action for every private fact.</p></a>
    <a class="card" href="methods.html"><p class="eyebrow">Routes</p><h3>{len(METHODS)} distinguishable routes</h3><p>Lawful, conditional, unverified and prohibited status; pros, cons and steps only for lawful routes.</p></a>
    <a class="card" href="costs.html"><p class="eyebrow">Costs</p><h3>40-tier cost ladder</h3><p>800 rows; total known first, all-in blank, official links on every row.</p></a>
    <a class="card" href="penalties.html"><p class="eyebrow">Risk</p><h3>{len(PENALTY)} penalty layers</h3><p>Tax, spread, fees, fines, reporting and currency gain separated.</p></a>
    <a class="card" href="flagged.html"><p class="eyebrow">Evidence</p><h3>Flagged for Review</h3><p>{len(FLAGS)} unpublished values and irregularities, each with an official discovery route.</p></a>
  </div>
</section>
<section id="milestones">
  <h2>Published known components at milestones</h2>
  <p class="muted">The lowest known-component illustration among priced one-transfer bank routes; it is not an all-in quote or an eligibility decision.</p>
  <div class="tablewrap"><table>
    <caption>Four of {P['tiers']} tiers · all {P['tiers']} tiers are in the cost ladder</caption>
    <thead><tr><th scope="col">Amount</th><th scope="col">Lowest published known total</th><th scope="col">Method</th><th scope="col">All-in</th><th scope="col">Official sources</th></tr></thead>
    <tbody>{milestone_rows()}</tbody>
  </table></div>
  <div class="downloads"><a href="data/costs.csv">All 800 cost rows (CSV)</a> <a href="data/costs.json">Costs (JSON)</a> <a href="data/penalty_costs.csv">Penalty ceilings (CSV)</a> <a href="data/review.json">Line-level audit (JSON)</a></div>
</section>
<section id="boundaries">
  <h2>What this pass does not claim</h2>
  <div class="grid">
    <div class="card"><h3>No executable quote</h3><p>Both bank boards say reference only; the BOC page says the actual transaction rate governs. Future rates are blank.</p><p class="src">{src_links(['B01','B02'])}</p></div>
    <div class="card"><h3>No personal tax bill</h3><p>Income source, tax-paid status, acquisition basis, filing history and residence were not supplied.</p><p class="src">{src_links(['B20','B21','B27','B29'])}</p></div>
    <div class="card"><h3>No hidden all-in number</h3><p>Intermediary, receiving, monthly, cash-handling and personal-tax components are blank and flagged.</p><p class="src">{src_links(['B03','B04','B05'])}</p></div>
    <div class="card"><h3>No other session edited</h3><p>The line-level audit records file:line comparisons and leaves the owning files untouched.</p><p class="src">{src_links(['B12','B13','B26','B29'])}</p></div>
  </div>
</section>
"""
write("index.html", page("Decision dashboard", "index.html", index_body, "Independent CNY-to-USD decision dashboard with published inputs, blanks and official source links."))

# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------
summary_cards = "".join(f"""
<article class="card" id="{e(item['id'])}">
  <p class="eyebrow">{e(item['id'])}</p><h3>{e(item['title'])}</h3>
  <p>{resolve(item['text'])}</p>
  <p class="src">{src_links(item['sources'])}</p>
</article>""" for item in SUMMARY)
summary_body = f"""
<section class="callout"><h2>Executive summary</h2><p>Seven conclusions. A computed illustration is labelled as such; an unpublished value is blank.</p></section>
<div class="grid">{summary_cards}</div>
<section><h2>Headline arithmetic</h2><div class="tablewrap"><table>
<caption>Board-derived published inputs · {e(READ)}</caption>
<thead><tr><th scope="col">Item</th><th scope="col">Value</th><th scope="col">Meaning</th><th scope="col">Official sources</th></tr></thead>
<tbody>
<tr><th scope="row" data-label="Item">BOC midpoint spread</th><td class="primary" data-label="Value">{P['boc_spread_pct']:.4f}%</td><td data-label="Meaning">USD sell {P['boc_sell']:.4f} vs midpoint {P['boc_mid']:.4f} CNY/USD; reference-only board.</td><td class="src" data-label="Official sources">{src_links(['B01','B07'])}</td></tr>
<tr><th scope="row" data-label="Item">HSBC midpoint spread</th><td class="primary" data-label="Value">{P['hsbc_spread_pct']:.4f}%</td><td data-label="Meaning">USD sell {P['hsbc_sell']:.4f} vs midpoint {P['hsbc_mid']:.4f} CNY/USD; board dated {P['hsbc_board_date']}.</td><td class="src" data-label="Official sources">{src_links(['B02','B07'])}</td></tr>
<tr><th scope="row" data-label="Item">Lowest known at {content.usd(10000)}</th><td class="primary" data-label="Value">{content.usd(P['low_10_value_usd'])}</td><td data-label="Meaning">{e(P['low_10_method'])}; all-in remains blank.</td><td class="src" data-label="Official sources">{src_links(['B02','B04'])}</td></tr>
<tr><th scope="row" data-label="Item">Lowest known at {content.usd(400000)}</th><td class="primary" data-label="Value">{content.usd(P['low_400_value_usd'])}</td><td data-label="Meaning">{e(P['low_400_method'])}; all-in remains blank.</td><td class="src" data-label="Official sources">{src_links(['B01','B03'])}</td></tr>
</tbody></table></div></section>
"""
write("summary.html", page("Executive summary", "summary.html", summary_body, "Seven source-linked conclusions and the exact limits of the cost arithmetic."))

# ---------------------------------------------------------------------------
# Decision questions
# ---------------------------------------------------------------------------
q_cards = "".join(f"""
<article class="card" id="{e(q['id'])}">
  <p class="eyebrow">{e(q['id'])} · decision gate</p><h3>{resolve(q['question'])}</h3>
  <p><strong>What is published / known:</strong> {resolve(q['known'])}</p>
  <p><strong>Missing private fact:</strong> {resolve(q['missing'])}</p>
  <p><strong>Why it changes the answer:</strong> {resolve(q['why'])}</p>
  <p><strong>Exact discovery action:</strong> {resolve(q['discover'])}</p>
  <p class="src">{src_links(q['sources'])}</p>
</article>""" for q in QUESTIONS)
questions_body = f"""
<section class="callout"><h2>{len(QUESTIONS)} questions before a decision</h2><p>No route can be chosen and no personal tax figure can be computed until these are established. Each has a concrete way to find out.</p></section>
<div class="grid">{q_cards}</div>
"""
write("questions.html", page("Decision questions", "questions.html", questions_body, "Known, missing, consequence and exact discovery action for every gating personal fact."))

# ---------------------------------------------------------------------------
# Methods
# ---------------------------------------------------------------------------
def method_card(m):
    cls = method_class(m["status"])
    pros = "".join(f"<li>{resolve(x)}</li>" for x in m["pros"])
    cons = "".join(f"<li>{resolve(x)}</li>" for x in m["cons"])
    if m["steps"]:
        steps = "<ol class=\"steps\">" + "".join(f"<li>{resolve(x)}</li>" for x in m["steps"]) + "</ol>"
    else:
        steps = '<p class="callout stop"><strong>No execution steps are provided for a prohibited route.</strong> Use a lawful route only after a written bank/SAFE decision.</p>'
    return f"""
<article class="card method {cls}" id="{e(m['id'])}">
  <p class="eyebrow">{e(m['id'])} · <span class="tag {cls}">{e(m['status'])}</span> · {e(m['pricing'])} pricing</p>
  <h3>{e(m['name'])}</h3><p>{resolve(m['short'])}</p>
  <p><strong>Best for:</strong> {resolve(m['best_for'])}</p>
  <div class="cols"><div><h3>Pros</h3><ul>{pros}</ul></div><div><h3>Cons / limits</h3><ul>{cons}</ul></div></div>
  <h3>Step-by-step</h3>{steps}
  <p><strong>Flags:</strong> {flag_links(m['flags'])}</p>
  <p class="src"><strong>Official sources:</strong> {src_links(m['sources'])}</p>
</article>"""

method_cards = "".join(method_card(m) for m in METHODS)
methods_body = f"""
<section class="callout"><h2>{len(METHODS)} distinguishable routes</h2><p>Lawful, conditional, unverified and prohibited channels are separated. Prohibited channels have no execution steps; their statutory exposure is on the penalty-layers page.</p></section>
<div class="grid">{method_cards}</div>
"""
write("methods.html", page("Routes and steps", "methods.html", methods_body, "Lawful, conditional, unverified and prohibited CNY-to-USD routes with pros, cons and steps."))

# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------
cost_options = "".join(f'<option value="{e(m["id"])}">{e(m["id"])} · {e(m["name"])}</option>' for m in METHODS)
amount_options = "".join(f'<option value="{a}">{content.usd(a)}</option>' for a in range(10000, 400001, 10000))

def cost_row(r):
    total = content.usd(r["total_known_usd"]) if r["total_known_usd"] is not None else '<span class="blank">blank</span>'
    pct = f'{r["total_known_pct"]:.4f}%' if r["total_known_pct"] is not None else '<span class="blank">blank</span>'
    blank_names = ", ".join(b["field"] for b in r["blanks"])
    return f"""<tr data-method="{e(r['method_id'])}" data-status="{e(status_key(r['status']))}" data-amount="{r['usd']}" data-has-blank="yes">
<td class="primary" data-label="Total known">{total}</td>
<td data-label="All-in"><span class="blank">blank + flagged</span></td>
<td class="num" data-label="Known %">{pct}</td>
<td data-label="Method"><strong>{e(r['method_id'])}</strong> · {e(r['method_name'])}<br><span class="small">{e(r['status'])}</span></td>
<td class="num" data-label="Amount">{content.usd(r['usd'])}</td>
<td data-label="Blank components"><span class="blank">{len(r['blanks'])} blank</span><br><span class="small">{e(blank_names)}</span></td>
<td class="src" data-label="Official sources">{src_links(r['source_ids'])} {flag_links(r['flag_ids'])}</td>
</tr>"""

cost_rows_html = "".join(cost_row(r) for r in COST_ROWS)
costs_body = f"""
<section class="callout"><h2>{len(COST_ROWS)} cost rows · {P['tiers']} tiers × {P['methods']} methods</h2>
<p><strong>Total known</strong> comes first. It is the board-spread illustration plus published sender/transfer fees only. <strong>All-in</strong> is always blank and flagged; blank is never zero. Every row carries its official source links.</p></section>
<section class="filters" aria-label="Cost filters">
  <div><label for="method-filter">Method</label><select id="method-filter"><option value="">All methods</option>{cost_options}</select></div>
  <div><label for="status-filter">Status</label><select id="status-filter"><option value="">All statuses</option><option value="lawful">Lawful</option><option value="conditional">Conditional</option><option value="unverified">Unverified</option><option value="unlawful">Unlawful</option></select></div>
  <div><label for="amount-filter">Amount</label><select id="amount-filter"><option value="">All amounts</option>{amount_options}</select></div>
  <div><label for="cost-search">Search row text</label><input id="cost-search" type="search" placeholder="Method, blank field or source"></div>
  <div><label class="checkline"><input id="blank-only" type="checkbox"> show rows with blanks only</label><button id="reset-filters" class="secondary" type="button">Reset</button></div>
</section>
<p class="muted">Showing <strong id="visible-count">{len(COST_ROWS)}</strong> of {len(COST_ROWS)} rows. <a href="data/costs.csv">Download all rows (CSV)</a> · <a href="data/costs.json">JSON</a></p>
<div class="tablewrap"><table id="cost-table">
<caption>Known components first · all {P['tiers']} {PLACE['STEP']} steps from {content.usd(10000)} to {content.usd(400000)}</caption>
<thead><tr><th scope="col">Total known</th><th scope="col">All-in</th><th scope="col">Known %</th><th scope="col">Method</th><th scope="col">Amount</th><th scope="col">Blank components</th><th scope="col">Official sources / flags</th></tr></thead>
<tbody>{cost_rows_html}</tbody>
</table></div>
<section class="notice"><h2>Formula and boundaries</h2><p>Board spread = USD amount × (sell − midpoint) / sell, where midpoint = (published TT buy + published TT sell) / 2. Sender fees apply the published 0.1% formula, floor, cap and cable charge to the CNY amount at the published sell rate. Flat Global Transfer fees are added in USD. This is an arithmetic illustration from reference-only boards, not a quote, an approval or a tax conclusion.</p><p class="src">{src_links(['B01','B02','B03','B04','B07'])}</p></section>
"""
write("costs.html", page("Cost ladder", "costs.html", costs_body, "800 published-input cost rows with blank all-in totals and official links."))

# ---------------------------------------------------------------------------
# Penalty layers
# ---------------------------------------------------------------------------
layer_cards = "".join(f"""
<article class="card" id="{e(layer['id'])}">
  <p class="eyebrow">{e(layer['id'])} · {e(layer['published'])}</p><h3>{resolve(layer['layer'])}</h3>
  <p>{resolve(layer['what'])}</p>
  <p><strong>Flags:</strong> {flag_links(layer['flags'])}</p>
  <p class="src">{src_links(layer['sources'])}</p>
</article>""" for layer in PENALTY)

def penalty_row(r):
    c = r["published_ceilings"]
    ids = sorted({x for item in c for x in item["source_ids"]})
    return f"""<tr>
<th scope="row" data-label="Amount">{content.usd(r['usd'])}</th>
<td class="primary" data-label="PRC 30% ceiling">{content.usd(c[0]['value_usd'])}</td>
<td data-label="PRC serious ceiling">{content.usd(c[1]['value_usd'])}</td>
<td data-label="Cash 20% ceiling">{content.usd(c[2]['value_usd'])}</td>
<td data-label="FBAR maxima">{content.usd(c[3]['value_usd'])} / {content.usd(c[4]['value_usd'])}</td>
<td data-label="Form 8938 max">{content.usd(c[5]['value_usd'])}</td>
<td data-label="Actual penalty"><span class="blank">blank + flagged</span></td>
<td class="src" data-label="Official sources">{src_links(ids)}</td>
</tr>"""

pen_milestones = [r for r in PEN_ROWS if r["usd"] in (10000, 100000, 200000, 400000)]
pen_rows_html = "".join(penalty_row(r) for r in pen_milestones)
penalties_body = f"""
<section class="callout warn"><h2>{len(PENALTY)} layers, not one number</h2><p>Tax on underlying income, documentary review, exchange spread, sender fees, third-party charges, PRC fines, U.S. currency gain and reporting penalties are separate. Statutory ceilings below are published maxima, not predicted personal penalties.</p></section>
<div class="grid">{layer_cards}</div>
<section><h2>Published statutory ceilings at milestones</h2>
<p class="muted">The full {len(PEN_ROWS)}-tier table is in <a href="data/penalty_costs.csv">penalty_costs.csv</a>; actual personal penalties are blank in every row.</p>
<div class="tablewrap"><table>
<caption>Published ceilings · actual penalty remains blank and flagged</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">PRC 30% ceiling</th><th scope="col">PRC serious ceiling</th><th scope="col">Cash 20% ceiling</th><th scope="col">FBAR non-willful / willful max</th><th scope="col">Form 8938 max</th><th scope="col">Actual penalty</th><th scope="col">Official sources</th></tr></thead>
<tbody>{pen_rows_html}</tbody>
</table></div></section>
"""
write("penalties.html", page("Penalty layers", "penalties.html", penalties_body, "Twelve separated penalty layers and published statutory ceilings with blank personal penalties."))

# ---------------------------------------------------------------------------
# Flagged for Review
# ---------------------------------------------------------------------------
flag_rows = "".join(f"""
<tr id="{e(f['id'])}">
<th scope="row" data-label="ID">{e(f['id'])}</th>
<td data-label="Status"><span class="tag review">needs review</span><br><span class="small">{e(f['kind'])}</span></td>
<td data-label="Affected">{resolve(f['affected'])}</td>
<td data-label="Why blank / irregular">{resolve(f['why'])}</td>
<td data-label="How to resolve">{resolve(f['discover'])}</td>
<td class="src" data-label="Official sources">{src_links(f['sources'])}</td>
</tr>""" for f in FLAGS)
flagged_body = f"""
<section class="callout warn"><h2>Flagged for Review · {len(FLAGS)} items</h2><p><strong>Status: needs review; non-blocking.</strong> A blank is an unpublished value, never zero. An irregularity is published with its exact official source and a concrete way to resolve it. No personal fact is inferred.</p></section>
<div class="tablewrap"><table>
<caption>Unverified values, eligibility limits and publisher irregularities</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Status</th><th scope="col">Affected</th><th scope="col">Why blank / irregular</th><th scope="col">How to resolve</th><th scope="col">Official sources</th></tr></thead>
<tbody>{flag_rows}</tbody>
</table></div>
"""
write("flagged.html", page("Flagged for Review", "flagged.html", flagged_body, "Every unpublished value and publisher irregularity, with status, resolution and official links."))

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
source_rows = "".join(f"""
<tr id="{e(s['id'])}">
<th scope="row" data-label="ID">{e(s['id'])}</th>
<td data-label="Publisher / official link"><strong>{e(s['publisher'])}</strong><br>{src_links([s['id']])}<br><span class="small">{e(s['source_class'])} · {e(s['status'])}</span></td>
<td data-label="Title / locator"><strong>{e(s['title'])}</strong><br><span class="small">{e(s['locator'])}</span></td>
<td data-label="Exact text read"><pre class="quote">{e(s['quote'])}</pre></td>
<td data-label="Reading">{e(s['reading'])}</td>
<td data-label="Limits">{e(s['limits'])}</td>
<td data-label="Figures"><pre class="quote">{e(json.dumps(s['figures'], ensure_ascii=False, indent=2))}</pre></td>
</tr>""" for s in LEDGER["sources"])
sources_body = f"""
<section class="callout"><h2>{len(S)} primary sources, re-read {e(READ)}</h2><p>Each row has the exact URL, locator, selected verbatim text, a plain-language reading and the published figures used by the model. Bank and provider pages are primary commercial sources, not government endorsements. Multi-chunk PDFs are quoted only from chunks actually read.</p></section>
<div class="downloads"><a href="data/sources.json">Source ledger (JSON)</a> <a href="data/make_sources.py">Generator (Python)</a></div>
<div class="tablewrap"><table>
<caption>Exact quotes, locators, figures and limitations</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Publisher / official link</th><th scope="col">Title / locator</th><th scope="col">Exact text read</th><th scope="col">Reading</th><th scope="col">Limits</th><th scope="col">Figures</th></tr></thead>
<tbody>{source_rows}</tbody>
</table></div>
"""
write("sources.html", page("Source register", "sources.html", sources_body, "34 primary sources with exact quotes, locators, figures and limitations."))

# ---------------------------------------------------------------------------
# Repository audit
# ---------------------------------------------------------------------------
review_rows = "".join(f"""
<tr id="{e(f['id'])}">
<th scope="row" data-label="ID">{e(f['id'])}</th>
<td data-label="File:line"><a href="../{e(f['file'])}">{e(f['file'])}:{f['line']}</a></td>
<td data-label="Status"><span class="tag review">{e(f['status'])}</span><br><span class="small">{e(f['category'])}</span></td>
<td data-label="Finding">{e(f['finding'])}<br><span class="small">{e(f['reviewer_note'])}</span></td>
<td data-label="Line excerpt"><pre class="quote">{e(f['excerpt'])}</pre></td>
<td class="src" data-label="Official sources">{src_links(f['source_ids'])}</td>
</tr>""" for f in REVIEW["findings"])
scan = REVIEW["scan"]
review_body = f"""
<section class="callout"><h2>Line-level repository audit</h2><p>Read {scan['text_files']} tracked text files and {scan['lines_read']:,} lines line by line outside this section. {len(REVIEW['findings'])} representative findings were re-located at build time; every finding has a file:line excerpt, a status and an official source link. Other sessions' files were not edited.</p></section>
<div class="grid">
  <div class="card"><p class="label">Tracked files considered</p><p class="value">{scan['tracked_files_considered']}</p></div>
  <div class="card"><p class="label">Text files read</p><p class="value">{scan['text_files']}</p></div>
  <div class="card"><p class="label">Lines read</p><p class="value">{scan['lines_read']:,}</p></div>
  <div class="card"><p class="label">Substantive lines</p><p class="value">{scan['substantive_lines']:,}</p></div>
</div>
<p class="muted">{e(REVIEW['scope'])} {e(REVIEW['limitations'])}</p>
<div class="downloads"><a href="data/review.json">Audit snapshot (JSON)</a> <a href="audit.py">Audit generator (Python)</a></div>
<div class="tablewrap"><table>
<caption>Findings · needs review unless explicitly marked verified or corrected</caption>
<thead><tr><th scope="col">ID</th><th scope="col">File:line</th><th scope="col">Status</th><th scope="col">Finding</th><th scope="col">Line excerpt</th><th scope="col">Official sources</th></tr></thead>
<tbody>{review_rows}</tbody>
</table></div>
"""
write("review.html", page("Repository audit", "review.html", review_body, "Mechanical line-by-line review with file:line findings and official source links."))

# ---------------------------------------------------------------------------
# Markdown executive summary
# ---------------------------------------------------------------------------
md = [f"""# guide-be3c20e8 · executive summary

Independent CNY-to-USD decision guide read on {READ}. Research, not individualized tax, legal or investment advice. No private account facts were supplied, no bank was contacted, no funds moved and no tax return was filed.

## Least-penalty answer

{resolve(SUMMARY[0]['text'])}

## What is published

- {len(S)} primary sources with exact quotes, locators, figures and limitations: [sources.html](sources.html).
- {len(METHODS)} distinguishable routes, including {len(QUESTIONS)} gating questions and {len(PENALTY)} penalty layers: [methods.html](methods.html), [questions.html](questions.html), [penalties.html](penalties.html).
- {len(COST_ROWS)} cost rows: every {PLACE['STEP']} step from {content.usd(10000)} to {content.usd(400000)} for every method: [costs.html](costs.html), [costs.csv](data/costs.csv), [costs.json](data/costs.json).
- {len(FLAGS)} flagged items, all **needs review / non-blocking**: [flagged.html](flagged.html).
- A mechanical line-by-line audit of {REVIEW['scan']['text_files']} tracked text files and {REVIEW['scan']['lines_read']:,} lines: [review.html](review.html).

## Headline arithmetic, with limits

BOC's reference-only board implies a {P['boc_spread_pct']:.4f}% midpoint spread; HSBC's dated board implies {P['hsbc_spread_pct']:.4f}%. Among priced one-transfer bank routes, the lowest published known-component illustration is **{content.usd(P['low_10_value_usd'])}** at {content.usd(10000)} ({P['low_10_method']}) and **{content.usd(P['low_400_value_usd'])}** at {content.usd(400000)} ({P['low_400_method']}). Every all-in total, intermediary/receiving charge, executable rate, future rate, personal tax and eligibility outcome is **blank and flagged**. Bank of China's page says the actual transaction rate governs; the web board is for reference only: {S['B01']['url']}

## Decision sequence

1. Establish the origin, tax-paid status and 完税证明 for every CNY in the account.
2. Classify PRC status, residence, emigration/hukou and foreign permanent-residence ID facts.
3. Ask the bank in writing for its eligibility decision, executable rate and full fee schedule.
4. Compare a documented-income wire, the applicable approval route and any provider route using the cost ladder's blanks.
5. Reconstruct acquisition dates/rates for U.S. §988 and review FBAR, Form 8938, Form 3520 and CBP filing history before filing.
6. Do not use quota splitting, underground swaps, crypto, false labels, excess cash or third-party straw-man channels.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/data/make_sources.py
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/audit.py
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/model.py
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/build.py
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/verify.py
node --check guide-be3c20e8/assets/app.js
```

The build is deterministic: no clock, network call or random value is used. `verify.py` independently recomputes every cost row from `sources.json`, checks every blank/flag, every official link in every substantive table row, all local links and anchors, and each review finding against its file:line text.
"""]
write("EXECUTIVE_SUMMARY.md", "".join(md))

print(f"wrote {len(NAV)} HTML pages, EXECUTIVE_SUMMARY.md and {len(list(DATA.glob('*.json'))) + len(list(DATA.glob('*.csv')))} data exports")
