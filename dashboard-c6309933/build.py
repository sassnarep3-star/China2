#!/usr/bin/env python3
"""
dashboard-c6309933/build.py - renders the static dashboard from data/*.json.

Every table row that carries a figure also carries a link to the official source
that figure was read from. Every figure that could not be read from an official
source renders as a BLANK cell with the literal text "UNVERIFIED".
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = HERE

PAGES = [
    ("index.html", "Overview"),
    ("costs.html", "Cost ladder"),
    ("methods.html", "Methods"),
    ("penalties.html", "Conversion penalty"),
    ("taxes.html", "Tax &amp; reporting"),
    ("questions.html", "Open questions"),
    ("repo-review.html", "Repo review"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(text)


def e(s):
    return html.escape("" if s is None else str(s), quote=True)


def money(v, cur="USD"):
    if v is None:
        return '<span class="blank">UNVERIFIED</span>'
    sym = "$" if cur == "USD" else "¥"
    return f'<span class="mono">{sym}{v:,.2f}</span>'


def pct(v):
    if v is None:
        return '<span class="blank">UNVERIFIED</span>'
    cls = ' class="mono zero"' if v == 0 else ' class="mono"'
    return f"<span{cls}>{v:,.4f}%</span>"


def cny(v):
    if v is None:
        return '<span class="blank">UNVERIFIED</span>'
    return f'<span class="mono">¥{v:,.2f}</span>'


def srclink(sid, sources):
    if not sid:
        return '<span class="blank">no official source</span>'
    s = sources[sid]
    return f'<a href="{e(s["url"])}" rel="noopener noreferrer">{e(sid)} ↗</a>'


def shell(title, current, body, subtitle=""):
    parts = []
    for h, n in PAGES:
        cur = ' aria-current="page"' if h == current else ""
        parts.append('<a href="%s"%s>%s</a>' % (e(h), cur, n))
    nav = "".join(parts)
    sub = f'<p class="lede">{subtitle}</p>' if subtitle else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · China Money · CNY→USD repatriation</title>
<meta name="description" content="Source-linked research on converting CNY to USD from mainland China for a U.S. citizen. Every figure links to an official source; unverified values are left blank.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
  <a class="brand" href="index.html">China Money<small>CNY → USD repatriation research</small></a>
  <nav class="jump" aria-label="Sections">{nav}</nav>
</div></header>
<div class="wrap"><main id="main">
<h1>{e(title)}</h1>
{sub}
{body}
</main></div>
<footer><div class="wrap">
  <p><strong>Research, not advice.</strong> This is a source-linked research record, not individualised
  tax, legal or investment advice. No transfer was made, no return was filed and no personal fact was
  verified. Published tariff inputs were checked against documents fetched on 2026-11-11; illustrative
  USD equivalents are calculations using a historical reference rate, not current quotes. Unknown amounts are left <span class="blank">BLANK</span> rather than estimated.</p>
  <p class="small">Session <code>arena/c6309933-china2</code> · data in <code>dashboard-c6309933/data/</code>
  · <a href="sources.html">12 official sources</a> · <a href="flagged.html">13 flagged values</a> ·
  <a href="../COORDINATION.md">task board</a></p>
</div></footer>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


# ----------------------------------------------------------------- landing
def page_index(d, sources):
    c = d["costs"]
    q = d["questions"]
    f = d["flags"]
    methods = d["methods"]["methods"]
    costed = [m for m in methods if m.get("costed")]
    rate = c["referenceRateCnyPerUsd"]

    # cheapest / dearest verified charge across the whole ladder
    priced = [r for r in c["rows"] if r["verifiedBankFeeUsd"] is not None]
    lo = min(priced, key=lambda r: r["verifiedBankFeeUsd"])
    hi = max(priced, key=lambda r: r["verifiedBankFeeUsd"])

    cards = "".join([
        '<div class="kpi"><div class="n">%s</div>'
        '<div class="l">Lowest verified bank charge</div>'
        '<div class="s">%s, at every tier from $10,000 to $400,000. '
        'Tariff %s &hellip; <span class="src">%s</span></div></div>'
        % (money(lo["verifiedBankFeeUsd"]),
           e(lo["methodName"].split(" - ")[1]),
           e(lo["feeBasis"].split(";")[0][:70]),
           srclink("S09", sources)),
        '<div class="kpi"><div class="n">%s</div>'
        '<div class="l">Highest verified bank charge</div>'
        '<div class="s">Premier wire on the OUR option: the RMB 500 percentage cap, the RMB 120 cable '
        'and the RMB 200 correspondent pre-charge. The cap first binds at the $80,000 tier. <span class="src">%s</span></div></div>'
        % (money(hi["verifiedBankFeeUsd"]), srclink("S09", sources)),
        '<div class="kpi"><div class="n">%s</div><div class="l">Priced tier rows</div>'
        '<div class="s">%d methods &times; %d tiers ($10,000 &rarr; $400,000 in $10,000 steps). '
        '%d rows are deliberately blank.</div></div>'
        % (format(c["rowCount"], ","), c["methodCount"], c["tierCount"],
           c["blankCostCellCount"]),
        '<div class="kpi"><div class="n">7.129</div><div class="l">CNY per USD reference</div>'
        '<div class="s">IRS 2025 yearly average. A tax translation rate, not a dealing rate. '
        '<span class="src">%s</span></div></div>' % srclink("S03", sources),
    ])

    known = "".join(
        f'<li><strong>{e(k["fact"])}</strong> — {e(k["consequence"])}</li>' for k in q["known"])
    answers = "".join(f"""
      <details><summary>{e(a['id'])}. {e(a['finding'])}</summary>
        <p class="small"><strong>Support:</strong> {e(a['support'])}</p>
        <p class="small"><strong>Confidence:</strong> {e(a['confidence'])}</p>
      </details>""" for a in q["answersSoFar"])

    topq = "".join(
        f'<tr><td class="tier">{e(x["id"])}</td><td>{e(x["question"])}</td>'
        f'<td><span class="pill bad">{e(x["status"])}</span></td></tr>'
        for x in q["questions"] if "blocking" in x["status"])

    BLANK_CELL = "<span class='blank'>BLANK</span>"
    mrows = []
    for m in methods:
        if m.get("costed"):
            fees = [r["verifiedBankFeeUsd"] for r in c["rows"]
                    if r["methodId"] == m["id"] and r["verifiedBankFeeUsd"] is not None]
            lo_cell, hi_cell = money(min(fees)), money(max(fees))
        else:
            lo_cell = hi_cell = BLANK_CELL
        mrows.append(
            '<tr><td class="tier">%s</td><td>%s</td>'
            '<td class="num">%s</td><td class="num">%s</td>'
            '<td class="src">%s</td></tr>'
            % (e(m["id"]), e(m["name"]), lo_cell, hi_cell,
               srclink(m.get("sourceId"), sources)))
    methods_list = "".join(mrows)

    body = f"""
<div class="callout key"><span class="t">The short answer</span>
Nothing fetched in this session imposes a tax on the act of converting CNY into USD.
26 U.S.C. §988(e)(2) says a gain on a <em>personal</em> currency transaction is not recognised at all
unless the gain exceeds $200 <span class="src">({srclink('S06', sources)})</span>, and the IRS states it has no
official exchange rate and accepts any posted rate used consistently
<span class="src">({srclink('S03', sources)})</span>. The reason for the reported charge is <strong>unknown</strong>. It could involve tax on underlying income, a documentation issue, or another charge; ask the bank for a written itemization and legal basis.
The applicable PRC tax rate could <strong>not</strong> be established for this case and is therefore
left <span class="blank">BLANK</span>, not guessed (flag F01).
</div>

<h2>Key figures</h2>
<div class="grid g2">{cards}</div>

<div class="callout warn"><span class="t">Read this before using any number here</span>
The verified bank charge is a <strong>floor, not a total</strong>. The HSBC tariff states that its free
lines do not extend to receiving-bank or correspondent-bank charges in the payment path
<span class="src">({srclink('S09', sources)})</span>, and it publishes <strong>no</strong> FX dealing spread.
The spread may be material — at an illustrative 0.50% it would be $2,000 on $400,000, more than
seventeen times the highest verified bank fee in this dataset — but 0.50% is an assumption, so it is not published
here as a verified cost (flag F02). Ask for a written executable dealing rate and all fees.
</div>

<h2>What is actually known</h2>
<div class="card"><ul class="tight">{known}</ul></div>

<h2>Answers established so far</h2>
{answers}

<h2>Blocking unknowns</h2>
<p class="small">These must be answered before any route can be selected. Full register with discovery
actions on the <a href="questions.html">Open questions</a> page.</p>
<div class="tscroll"><table class="stack">
<thead><tr><th>ID</th><th>Question</th><th>Status</th></tr></thead>
<tbody>{topq}</tbody></table></div>

<h2>All methods at a glance</h2>
<p class="small">Verified charge range across the whole $10,000 → $400,000 ladder. Blank means no fee
schedule was published in a document this session fetched. Full pros, cons and step-by-step playbooks on
the <a href="methods.html">Methods</a> page; every tier on the <a href="costs.html">Cost ladder</a> page.</p>
<div class="tscroll"><table class="stack">
<caption>Lowest and highest verified bank charge per method, at the IRS 2025 reference rate of {rate} CNY/USD
<span class="src">{srclink('S03', sources)}</span></caption>
<thead><tr><th>ID</th><th>Method</th><th class="num">From</th><th class="num">To</th><th>Source</th></tr></thead>
<tbody>{methods_list}</tbody></table></div>
<p class="legend"><span class="blank">BLANK</span> = no official source published this value; not estimated.</p>

<h2>Where to go next</h2>
<div class="grid g3">
  <div class="card"><h3><a href="costs.html">Cost ladder →</a></h3>
    <p>Every method priced at each $10,000 step from $10,000 to $400,000. {c['rowCount']:,} rows,
    each linked to its source.</p></div>
  <div class="card"><h3><a href="penalties.html">Conversion penalty →</a></h3>
    <p>The charge broken into its separate layers, showing which layers are verified and which are blank.</p></div>
  <div class="card"><h3><a href="questions.html">Open questions →</a></h3>
    <p>{len(q['questions'])} questions, {len(q['answersSoFar'])} answers so far, and a concrete discovery
    action for each gap.</p></div>
  <div class="card"><h3><a href="repo-review.html">Repo review →</a></h3>
    <p>{len(f['repoFindings'])} targeted repository findings, each with the command
    that produced it.</p></div>
  <div class="card"><h3><a href="flagged.html">Flagged for review →</a></h3>
    <p>{len(f['dataFlags'])} values that could not be confirmed from an official source, left blank with a
    discovery action.</p></div>
  <div class="card"><h3><a href="sources.html">Sources →</a></h3>
    <p>{len(d['sources']['sources'])} official documents, each fetched on 2026-11-11, with the exact text
    that was read.</p></div>
</div>
"""
    return shell("China Money — CNY→USD repatriation research", "index.html", body,
                 "Lawful routes, verified costs and honest blanks for moving a mainland China CNY balance "
                 "into USD as a U.S. citizen. Research, not tax or legal advice.")


# ------------------------------------------------------------------- costs
def page_costs(d, sources):
    c = d["costs"]
    rate = c["referenceRateCnyPerUsd"]
    blocks = []
    for m in d["methods"]["methods"]:
        rows = [r for r in c["rows"] if r["methodId"] == m["id"]]
        body_rows = "".join(f"""
          <tr>
            <td class="tier" data-label="Tier">{money(r['tierUsd'])}</td>
            <td class="num" data-label="Verified bank charge">{money(r['verifiedBankFeeUsd'])}</td>
            <td class="num" data-label="% of amount">{pct(r['verifiedBankFeePct'])}</td>
            <td class="num" data-label="In CNY">{cny(r['verifiedBankFeeCny'])}</td>
            <td class="num" data-label="FX spread"><span class="blank">BLANK</span></td>
            <td class="num" data-label="Correspondent + receiving bank"><span class="blank">BLANK</span></td>
            <td class="num" data-label="PRC tax"><span class="blank">BLANK</span></td>
            <td class="num" data-label="U.S. tax"><span class="blank">BLANK</span></td>
            <td class="num" data-label="TOTAL"><span class="blank">BLANK</span></td>
            <td class="num" data-label="CNY needed @ {rate}">{money(r['cnyAtReferenceRate'], 'CNY')}</td>
            <td class="src" data-label="Source">{srclink(r['sourceId'], sources)}</td>
          </tr>""" for r in rows)
        basis = (f'<p class="small"><strong>Fee basis:</strong> {e(m["feeBasis"])}</p>'
                 if m.get("feeBasis") else
                 '<p class="small"><strong>Fee basis:</strong> none published in a document fetched this '
                 'session — every cost cell is blank.</p>')
        blocks.append(f"""
<h3 id="{e(m['id'])}">{e(m['id'])} · {e(m['name'])}</h3>
{basis}
<div class="tscroll"><table class="stack">
<caption>{len(rows)} tiers, $10,000 → $400,000 in $10,000 steps. Columns are ordered most-important-first:
the verified bank charge is the only figure that is not blank.</caption>
<thead><tr>
  <th>Tier</th><th class="num">Verified bank charge</th><th class="num">% of amount</th>
  <th class="num">In CNY</th><th class="num">FX spread</th>
  <th class="num">Correspondent + receiving bank</th><th class="num">PRC tax</th>
  <th class="num">U.S. tax</th><th class="num">TOTAL</th>
  <th class="num">CNY needed @ {rate}</th><th>Source</th>
</tr></thead>
<tbody>{body_rows}</tbody></table></div>
""")

    body = f"""
<div class="callout key"><span class="t">How to read this table</span>
The <strong>Verified bank charge</strong> column is the only one with numbers, and it is the sum of the
charges HSBC Bank (China) actually publishes in its tariff effective 2026-10-31
<span class="src">({srclink('S09', sources)})</span>. It is a <strong>floor, not a total</strong>.
The FX spread, correspondent and receiving-bank deductions, PRC tax and U.S. tax are all
<span class="blank">BLANK</span> because no official source published them — they are not estimated, and
the TOTAL column is blank for the same reason. CNY amounts use the IRS 2025 yearly average of
<strong>{rate}</strong> CNY/USD <span class="src">({srclink('S03', sources)})</span>, which is a tax
translation rate, not a dealing rate.
</div>

<div class="grid g3">
  <div class="kpi"><div class="n">{c['rowCount']:,}</div><div class="l">Rows</div>
    <div class="s">{c['methodCount']} methods × {c['tierCount']} tiers</div></div>
  <div class="kpi"><div class="n">{c['costedMethodCount']}</div><div class="l">Methods with a published fee</div>
    <div class="s">{', '.join(e(i) for i in c['costedMethodIds'])}</div></div>
  <div class="kpi"><div class="n">{c['blankCostCellCount']}</div><div class="l">Rows left blank</div>
    <div class="s">No fee schedule published in a fetched document</div></div>
</div>

<h2>Download</h2>
<div class="card"><p>
  <a href="exports/cost-ladder.csv">cost-ladder.csv</a> ·
  <a href="exports/cost-ladder.json">cost-ladder.json</a> — all {c['rowCount']:,} rows.
</p></div>

<h2>Jump to a method</h2>
<div class="card"><p class="small">{' · '.join(f'<a href="#{e(m["id"])}">{e(m["id"])}</a>' for m in d["methods"]["methods"])}</p></div>

{''.join(blocks)}
"""
    return shell("Cost ladder: $10,000 → $400,000", "costs.html", body,
                 "Every method priced at each $10,000 step. Unverified components are left blank rather "
                 "than estimated.")


# ----------------------------------------------------------------- methods
def page_methods(d, sources):
    blocks = []
    for m in d["methods"]["methods"]:
        pros = "".join(f"<li>{e(x)}</li>" for x in m["pros"])
        cons = "".join(f"<li>{e(x)}</li>" for x in m["cons"])
        steps = "".join(f"<li>{e(x)}</li>" for x in m["steps"])
        pill = ('<span class="pill ok">costed</span>' if m.get("costed")
                else '<span class="pill na">no published fee</span>')
        if m["id"] == "M13":
            pill = '<span class="pill bad">not recommended</span>'
        blocks.append(f"""
<details id="{e(m['id'])}" {"open" if m["id"] in ("M01","M03","M08") else ""}>
<summary>{e(m['id'])} · {e(m['name'])} &nbsp;{pill}</summary>
<p class="small"><strong>Route:</strong> {e(m['route'])}</p>
<p class="small"><strong>Standing:</strong> {e(m['lawful'])} &nbsp;
  <span class="src">Source: {srclink(m.get('sourceId'), sources)}</span></p>
<div class="grid g2">
  <div><h3>Pros</h3><ul class="tight">{pros}</ul></div>
  <div><h3>Cons</h3><ul class="tight">{cons}</ul></div>
</div>
<h3>Step by step</h3><ol class="steps">{steps}</ol>
<p class="small"><strong>Fee basis:</strong> {e(m['feeBasis']) if m.get('feeBasis') else
  'none published in a document fetched this session'}</p>
<p class="small"><a href="costs.html#{e(m['id'])}">See all 40 tiers for this method →</a></p>
</details>""")

    body = f"""
<div class="callout key"><span class="t">What makes a route lawful</span>
A route is lawful when the FX purchase is either inside the individual's annual USD 50,000 quota
<span class="src">({srclink('S02', sources)})</span>, supported by authenticity documents above that quota,
or covered by a SAFE approval under Huifa [2014] No. 2 Section VI
<span class="src">({srclink('S01', sources)})</span> . For listed categories of outbound payment above USD 50,000 equivalent, tax recordal may apply; exemptions exist. Confirm applicability with the bank and tax authority
<span class="src">({srclink('S10', sources)}, {srclink('S11', sources)})</span>.
</div>
{''.join(blocks)}
"""
    return shell("Methods: every route, with pros, cons and steps", "methods.html", body,
                 "Thirteen routes from mainland CNY to USD, each with its legal standing, trade-offs and a "
                 "step-by-step playbook.")


# --------------------------------------------------------------- penalties
def page_penalties(d, sources):
    layers = [
        ("L1", "PRC tax on the income that created the balance", "BLANK", "F01",
         "Tax on underlying income is possible, but the reason for the reported charge and applicable amount are unknown. Obtain the bank’s written itemization and tax records.", "S10"),
        ("L2", "PRC tax recordal for covered outbound payments above USD 50,000", "No charge stated",
         "F08", "S10 applies to listed categories and includes exemptions; S11 confirms one per contract and an online channel. Neither "
         "states a fee, and absence of a stated fee is not evidence that it is free.", "S10"),
        ("L3", "Bank FX dealing spread", "BLANK", "F02",
         "A potentially material unquantified cost. The HSBC tariff publishes wire charges but no spread, and "
         "note 7 excludes anything not priced by HSBC.", "S09"),
        ("L4", "Bank wire and cable charge", "RMB 0 – 620 (wire and cable only)", None,
         "Fully verified. 0.1% with a RMB 100 minimum and RMB 500 maximum, plus a RMB 120 cable; RMB 0 for "
         "Private Banking and Premier Elite. About $30.86 to $115.02 at 7.129, depending on tier "
         "and charge-sharing option.", "S09"),
        ("L5", "Correspondent bank deduction", "BLANK", "F03",
         "S09 states expressly that free tariff lines do not cover receiving or correspondent banks in the "
         "payment path. OUR adds a RMB 200 pre-charge whose shortfall is billed later, uncapped.", "S09"),
        ("L6", "U.S. receiving bank inbound wire fee", "BLANK", "F03",
         "No U.S. bank schedule was fetched in this session; S09 notes that other banks may charge.", "S09"),
        ("L7", "U.S. tax on a currency gain", "BLANK", "F01",
         "26 U.S.C. 988(e)(2): no gain is recognised on a personal currency transaction unless the gain "
         "exceeds $200. Section 988(e)(1) disapplies the rest of the section to personal transactions.", "S06"),
        ("L8", "U.S. tax on the underlying income", "BLANK", "F01",
         "Depends entirely on Q01 (source of the balance) and Q08 (residence). The FEIE reaches earned "
         "income only: $132,900 for 2026, $137,300 for 2027. Treaty caps PRC withholding on dividends and "
         "interest at 10%.", "S07"),
        ("L9", "U.S. reporting exposure (FBAR)", "$16,536 / $165,353", None,
         "Inflation-adjusted amounts in 31 CFR 1010.821 as accessed; the willful maximum can be greater where 50% of the balance exceeds the listed amount. Applicability and assessment depend on the facts; check current adjustments.", "S05"),
        ("L10", "PRC penalty for unlawful routes (quota splitting, underground swaps)", "BLANK", "F11",
         "S02 confirms SAFE built the bank-to-SAFE monitoring system specifically to prevent repeated "
         "purchases and instalment sales. The penalty amount was not verified and is left blank.", "S02"),
    ]
    rows = "".join(f"""
      <tr>
        <td class="tier" data-label="Layer">{e(i)}</td>
        <td data-label="Layer">{e(n)}</td>
        <td class="num" data-label="Amount">{('<span class="blank">BLANK</span>' if a == "BLANK"
                                              else f'<span class="mono">{e(a)}</span>')}</td>
        <td data-label="Why">{e(w)}</td>
        <td class="src" data-label="Source">{srclink(s, sources) if s else '<span class="blank">none</span>'}
            {f' · <a href="flagged.html#{e(fl)}">{e(fl)}</a>' if fl else ''}</td>
      </tr>""" for i, n, a, fl, w, s in layers)

    body = f"""
<div class="callout key"><span class="t">The headline finding</span>
Of the ten layers that make up what feels like a "conversion penalty", only some tariff and regulatory amounts could be identified. Actual taxes, the exchange spread and total transfer cost are <span class="blank">BLANK</span> because they depend on facts or quotes not available here. Penalty amounts are exposure, not a normal transfer cost.
</div>
<div class="tscroll"><table class="stack">
<caption>Ten layers of the conversion penalty, ordered from the underlying income to the destination account</caption>
<thead><tr><th>Layer</th><th>What it is</th><th class="num">Amount</th><th>Why / what is known</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>What this means in practice</h2>
<div class="grid g2">
  <div class="card"><h3>Stop optimising the wire</h3>
    <p>The modeled HSBC tariff components range from $0 to $115.02 across the illustrated $10,000 to $400,000 tiers
    <span class="src">({srclink('S09', sources)})</span>. These estimates exclude other bank charges, FX spread and taxes, and are not quotes.</p></div>
  <div class="card"><h3>Get the dealing rate in writing</h3>
    <p>Ask the bank for a written executable CNY/USD dealing rate and all fees for the actual amount. Compare it with a contemporaneous reference rate; the difference is indicative, not necessarily a complete measure of cost.</p></div>
  <div class="card"><h3>Settle PRC tax before you move the money</h3>
    <p>S10 makes "whether the outbound item has paid tax as required" an express subject of the 15-working-day
    review where recordal applies <span class="src">({srclink('S10', sources)})</span>. Verify whether any tax or filing is due with the relevant authorities.</p></div>
  <div class="card"><h3>Reporting exposure does not shrink by instalments</h3>
    <p>Potential FBAR penalties depend on the facts and the filing obligations for each year. Splitting a transfer does not erase an existing reporting violation, and can multiply bank charges.</p></div>
</div>
"""
    return shell("The conversion penalty, broken down", "penalties.html", body,
                 "What the charge is actually made of — and how much of it can be verified at all.")


# ------------------------------------------------------------------ taxes
def page_taxes(d, sources):
    def tbl(rows):
        return "".join(f"""
      <tr>
        <td class="tier" data-label="ID">{e(r['id'])}</td>
        <td data-label="Rule">{e(r['rule'])}</td>
        <td data-label="Value">{('<span class="blank">BLANK</span>' if r['value'] is None
                                  else f'<strong>{e(r["value"])}</strong>')}</td>
        <td data-label="Applies to">{e(r['appliesTo']) if r['appliesTo'] else '<span class="blank">—</span>'}</td>
        <td class="src" data-label="Source">{srclink(r['sourceId'], sources)}</td>
      </tr>""" for r in rows)

    quotes = "".join(
        f'<div class="quote"><strong>{e(r["id"])}:</strong> {e(r["quote"])}</div>'
        for r in d["rules"]["usRules"] + d["rules"]["prcRules"] if r["quote"])
    notes = "".join(
        f'<li><strong>{e(r["id"])} {e(r["rule"])}:</strong> {e(r["note"])}</li>'
        for r in d["rules"]["usRules"] + d["rules"]["prcRules"] if r["note"])

    body = f"""
<div class="callout key"><span class="t">The distinction that matters</span>
Nothing below taxes the <em>conversion</em>. PRC rules govern <strong>whether the money may leave and what
must be filed first</strong>. U.S. rules govern <strong>how it is translated, what is excluded and what must
be reported</strong>. The one provision that touches a currency gain directly — 26 U.S.C. §988(e)(2) —
exempts it unless the gain exceeds $200 <span class="src">({srclink('S06', sources)})</span>.
</div>

<h2>PRC rules</h2>
<div class="tscroll"><table class="stack">
<caption>Verified from SAFE, the State Taxation Administration and the HSBC China tariff</caption>
<thead><tr><th>ID</th><th>Rule</th><th>Value</th><th>Applies to</th><th>Source</th></tr></thead>
<tbody>{tbl(d['rules']['prcRules'])}</tbody></table></div>

<h2>U.S. rules</h2>
<div class="tscroll"><table class="stack">
<caption>Verified from the IRS, the eCFR and govinfo</caption>
<thead><tr><th>ID</th><th>Rule</th><th>Value</th><th>Applies to</th><th>Source</th></tr></thead>
<tbody>{tbl(d['rules']['usRules'])}</tbody></table></div>

<h2>Verbatim source text</h2>
<p class="small">Quoted from the documents fetched on 2026-11-11, so each value above can be checked
against its origin.</p>
{quotes}

<h2>Notes and limits</h2>
<ul class="tight">{notes}</ul>
"""
    return shell("Tax and reporting rules", "taxes.html", body,
                 "PRC foreign-exchange and tax-recordal rules, and U.S. translation, exclusion and "
                 "reporting rules — each with the text it was read from.")


# -------------------------------------------------------------- questions
def page_questions(d, sources):
    known = "".join(f"""
      <tr><td data-label="Fact">{e(k['fact'])}</td>
          <td data-label="Source">{e(k['source'])}</td>
          <td data-label="Consequence">{e(k['consequence'])}</td></tr>""" for k in d["questions"]["known"])
    qs = "".join(f"""
<details id="{e(q['id'])}" {"open" if "blocking" in q["status"] else ""}>
<summary>{e(q['id'])} · {e(q['question'])} &nbsp;
  <span class="pill {'bad' if 'blocking' in q['status'] else 'warn'}">{e(q['status'])}</span></summary>
  <p class="small"><strong>Why it decides the answer:</strong> {e(q['why'])}</p>
  <p class="small"><strong>How to discover it:</strong> {e(q['discovery'])}</p>
</details>""" for q in d["questions"]["questions"])
    ans = "".join(f"""
<details open><summary>{e(a['id'])}. {e(a['finding'])}</summary>
  <p class="small"><strong>Support:</strong> {e(a['support'])}</p>
  <p class="small"><strong>Confidence:</strong> {e(a['confidence'])}</p>
</details>""" for a in d["questions"]["answersSoFar"])

    blocking = sum(1 for q in d["questions"]["questions"] if "blocking" in q["status"])
    body = f"""
<div class="callout key"><span class="t">Two facts known, {len(d['questions']['questions'])} unknown</span>
The brief supplied exactly two facts: that the requester is a U.S. citizen, and that a CNY balance sits in a
mainland bank account. Nothing else. Every unknown below is left unknown — none has been inferred, because
each one changes the answer. <strong>{blocking}</strong> are blocking: the route cannot be chosen without them.
</div>

<h2>What is known</h2>
<div class="tscroll"><table class="stack">
<thead><tr><th>Fact</th><th>Source</th><th>Consequence</th></tr></thead>
<tbody>{known}</tbody></table></div>

<h2>Questions that must be answered</h2>
{qs}

<h2>Answers established so far</h2>
{ans}
"""
    return shell("Open questions and discovery actions", "questions.html", body,
                 "What is known, what is missing, why the decision turns on it, and how to find out.")


# ------------------------------------------------------------- repo review
def page_repo(d, sources):
    sev = {"high": "bad", "medium": "warn", "low": "na", "info": "na"}
    rows = "".join(f"""
<details {"open" if r['severity'] == 'high' else ""}>
<summary>{e(r['id'])} · {e(r['title'])} &nbsp;
  <span class="pill {sev[r['severity']]}">{e(r['severity'])}</span>
  <span class="pill na">{e(r['status'])}</span></summary>
  <p class="small"><strong>Evidence:</strong> {e(r['evidence'])}</p>
  <p class="small"><strong>Why it matters:</strong> {e(r['why'])}</p>
  <p class="small"><strong>Recommendation:</strong> {e(r['recommendation'])}</p>
</details>""" for r in d["flags"]["repoFindings"])

    body = f"""
<div class="callout key"><span class="t">Method</span>
Every finding below came from a command run against the checked-out tree in this session, not from reading
prose. Where a finding was later disproved it is recorded as resolved rather than quietly dropped — see
<code>R02</code>.
</div>
<h2>Findings</h2>
{rows}
<hr class="sep">
<div class="card"><h3>Scope of this review</h3>
<p class="small">This session read and re-verified only its own deliverable and the repository's structure,
CI workflows and verification suites. It did <strong>not</strong> re-verify the substantive legal claims
inside the nineteen other published sites in this repository; those are covered by
<a href="flagged.html">Flagged for review</a> where a value could not be confirmed from an official source.</p></div>
"""
    return shell("Repository review", "repo-review.html", body,
                 "Targeted findings from reviewing this repository, each with the command that produced "
                 "it.")


# ---------------------------------------------------------------- flagged
def page_flagged(d, sources):
    rows = "".join(f"""
      <tr id="{e(f['id'])}">
        <td class="tier" data-label="ID">{e(f['id'])}</td>
        <td data-label="Field">{e(f['field'])}</td>
        <td data-label="Value">{('<span class="blank">BLANK</span>' if f['value'] == 'BLANK'
                                  else e(f['value']))}</td>
        <td data-label="Reason">{e(f['reason'])}</td>
        <td data-label="How to discover">{e(f['discovery'])}</td>
        <td data-label="Severity"><span class="pill {'bad' if f['severity']=='high' else
                    'warn' if f['severity']=='medium' else 'na'}">{e(f['severity'])}</span></td>
      </tr>""" for f in d["flags"]["dataFlags"])

    body = f"""
<div class="callout warn"><span class="t">These values are deliberately blank</span>
The brief requires that a value which cannot be confirmed from an official source be left blank and flagged
rather than inferred. Each row below is such a value. <strong>None blocks publication</strong>; each has a
concrete discovery action so it can be filled in later.
</div>
<div class="tscroll"><table class="stack">
<caption>{len(d['flags']['dataFlags'])} values that could not be confirmed from an official source in this session</caption>
<thead><tr><th>ID</th><th>Field</th><th>Value</th><th>Why it is blank</th><th>How to discover it</th><th>Severity</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="small">Repository-level findings are on the <a href="repo-review.html">Repository review</a> page.</p>
"""
    return shell("Flagged for review", "flagged.html", body,
                 "Values that could not be confirmed from an official source, left blank with a discovery "
                 "action. None of these blocks publication.")


# ---------------------------------------------------------------- sources
def page_sources(d, sources):
    rows = "".join(f"""
      <tr>
        <td class="tier" data-label="ID">{e(s['id'])}</td>
        <td data-label="Publisher">{e(s['publisher'])}</td>
        <td data-label="Document"><a href="{e(s['url'])}" rel="noopener noreferrer">{e(s['title'])}</a>
            <div class="small">{e(s['locator'])}</div></td>
        <td data-label="Status"><span class="pill {'ok' if s['status']=='verified' else 'warn'}">{e(s['status'])}</span></td>
        <td class="num" data-label="Fetched">{e(s['retrieved'])}</td>
      </tr>""" for s in d["sources"]["sources"])
    quotes = "".join(f"""
<details {"open" if i < 3 else ""}><summary>{e(s['id'])} · {e(s['title'][:110])}</summary>
  <p class="small"><strong>Publisher:</strong> {e(s['publisher'])}</p>
  <p class="small"><strong>Locator:</strong> {e(s['locator'])}</p>
  <div class="quote">{e(s['quote'])}</div>
  <p class="small"><a href="{e(s['url'])}" rel="noopener noreferrer">Open the original ↗</a></p>
</details>""" for i, s in enumerate(d["sources"]["sources"]))

    body = f"""
<div class="callout key"><span class="t">Verification standard</span>
Every source below was fetched directly over HTTPS on 2026-11-11 and the quoted text was read from the
returned document body. <span class="pill ok">verified</span> means the value was read in the fetched body.
<span class="pill warn">verified-limited</span> means the official document was located but the value was
read from a search-index rendering of that same document rather than re-read in the returned chunk — those
rows are marked so the distinction is never hidden.
</div>
<div class="tscroll"><table class="stack">
<caption>{len(d['sources']['sources'])} official and primary sources</caption>
<thead><tr><th>ID</th><th>Publisher</th><th>Document</th><th>Status</th><th class="num">Fetched</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<h2>Verbatim text relied on</h2>
{quotes}
"""
    return shell("Sources", "sources.html", body,
                 "Every document this dashboard's figures were read from, with the exact text relied on.")


# ----------------------------------------------------------------- exports
def write_exports(d):
    c = d["costs"]
    os.makedirs(os.path.join(OUT, "exports"), exist_ok=True)
    cols = ["methodId", "methodName", "tierUsd", "verifiedBankFeeCny", "verifiedBankFeeUsd",
            "verifiedBankFeePct", "fxSpreadUsd", "correspondentFeeUsd", "receivingBankFeeUsd",
            "prcTaxUsd", "usTaxUsd", "totalVerifiedCostUsd", "totalCostUsd",
            "cnyAtReferenceRate", "sourceId", "feeBasis"]
    lines = [",".join(cols)]
    for r in c["rows"]:
        lines.append(",".join(
            "" if r[k] is None else (f'"{str(r[k]).replace(chr(34), chr(34)*2)}"'
                                     if k in ("methodName", "feeBasis") else str(r[k]))
            for k in cols))
    write(os.path.join("exports", "cost-ladder.csv"), "\n".join(lines) + "\n")
    write(os.path.join("exports", "cost-ladder.json"),
          json.dumps(c, ensure_ascii=False, indent=2) + "\n")


def main():
    d = {
        "sources": load("sources.json"),
        "methods": load("methods.json"),
        "questions": load("questions.json"),
        "rules": load("rules.json"),
        "flags": load("flags.json"),
        "costs": load("costs.json"),
    }
    src = {s["id"]: s for s in d["sources"]["sources"]}
    write("index.html", page_index(d, src))
    write("costs.html", page_costs(d, src))
    write("methods.html", page_methods(d, src))
    write("penalties.html", page_penalties(d, src))
    write("taxes.html", page_taxes(d, src))
    write("questions.html", page_questions(d, src))
    write("repo-review.html", page_repo(d, src))
    write("flagged.html", page_flagged(d, src))
    write("sources.html", page_sources(d, src))
    write_exports(d)
    print("dashboard-c6309933: wrote 9 pages + 2 exports")


if __name__ == "__main__":
    main()
