#!/usr/bin/env python3
"""Build the static tax-workbook dashboard. Run model.py first."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SITE = ROOT / "site"
E = html.escape


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SOURCES = {s["id"]: s for s in load("sources.json")}
RULES = load("rules.json")
FLAGS = load("flags.json")
FORMULAS = load("formulas.json")
DECISIONS = load("decisions.json")
INPUTS = load("inputs.json")
WORKBOOK = load("workbook.json")

NAV = [
    ("index.html", "Overview"),
    ("workbook.html", "Cost & tax workbook"),
    ("rules.html", "Verified rules"),
    ("sources.html", "Official sources"),
    ("review.html", "Flagged for review"),
    ("methodology.html", "Methodology"),
]


def esc(value) -> str:
    return E(str(value), quote=True)


def source_link(source_id: str, label: str | None = None) -> str:
    source = SOURCES[source_id]
    text = label or source_id
    return f'<a href="{esc(source["url"])}" target="_blank" rel="noopener">{esc(text)}</a>'


def source_links(ids: list[str]) -> str:
    return " · ".join(source_link(i) for i in ids)


def badge(status: str) -> str:
    cls = "ok" if status.startswith("verified") else "warn"
    return f'<span class="badge {cls}">{esc(status)}</span>'


def blank_cell(label: str) -> str:
    return f'<td class="blank" aria-label="{esc(label)}: unverified"></td>'


def page(filename: str, title: str, body: str, lede: str = "") -> None:
    nav_parts = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == filename else ""
        nav_parts.append(f'<a href="{esc(href)}"{current}>{esc(label)}</a>')
    nav = "".join(nav_parts)
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | China Money Tax Workbook</title>
<meta name="description" content="Source-linked U.S. currency-basis and conversion-cost workbook for CNY to USD. Unknown values are blank, not zero.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html">China Money <span>Tax Workbook</span></a>
    <nav aria-label="Primary">{nav}</nav>
  </div>
</header>
<main id="main" class="wrap">
  <p class="eyebrow">U.S. currency disposition · research update {esc(INPUTS['as_of_utc'])}</p>
  <h1>{esc(title)}</h1>
  {lede_html}
  {body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <p>General research, not personalized legal or tax advice. No funds were moved and no return was filed. Blank cells mean unverified, not zero. Do not add private tax records to this public repository.</p>
    <p><a href="../../docs/index.html">Main research dashboard</a> · <a href="../../audit-86f0/index.html">Independent audit</a> · <a href="https://github.com/sassnarep3-star/China2">Repository</a></p>
  </div>
</footer>
</body>
</html>
"""
    (SITE / filename).write_text(doc, encoding="utf-8")


def build_index() -> None:
    decision_rows = []
    for d in DECISIONS:
        decision_rows.append(
            "<tr>"
            f'<th scope="row">{esc(d["id"])} · {esc(d["condition"])}</th>'
            f'<td>{esc(d["tax_question"])}</td>'
            f'<td>{esc(d["next_action"])}</td>'
            f'<td class="sources">{source_links(d["sources"])}</td>'
            "</tr>"
        )
    body = f"""
<section class="callout">
  <strong>Most important finding.</strong>
  <p>A CNY→USD transfer amount alone does not determine U.S. tax. Separate the underlying income, any currency-disposition gain, execution fees and reporting penalties. For a qualifying personal currency disposition, exchange-rate gain up to $200 on the transaction is not recognized; above $200, IRS Publication 525 says report the gain as a capital gain. Business/investment transactions can follow different ordinary-income rules. {source_links(['S01','S02'])}</p>
</section>
<section class="grid cards">
  <article class="card">
    <span class="card-kicker">01 · Workbook</span>
    <h2>40 amounts, no invented costs</h2>
    <p>$10,000 through $400,000 in $10,000 increments. Total cost, federal tax, fees, basis and gain are blank because the required private facts and executable quotes were not supplied.</p>
    <a class="button" href="workbook.html">Open workbook</a>
  </article>
  <article class="card">
    <span class="card-kicker">02 · Rules</span>
    <h2>Official-source rule table</h2>
    <p>Section 988, IRS Publication 525, basis/holding-period guidance, exchange-rate policy, foreign tax credit limits, FBAR and Form 8938 triggers.</p>
    <a class="button" href="rules.html">Read rules</a>
  </article>
  <article class="card">
    <span class="card-kicker">03 · Review</span>
    <h2>Corrections and unknowns</h2>
    <p>Flags identify missing basis, missing quotes and overbroad claims in earlier repository material. They are published for review, not silently treated as verified.</p>
    <a class="button" href="review.html">Review flags</a>
  </article>
</section>
<section class="panel">
  <h2>Executive summary</h2>
  <ol class="summary-list">
    <li><strong>Do not assume “conversion tax = 0%.”</strong> The U.S. may tax a currency-disposition gain or the underlying income; the amount depends on basis, use, year and filing facts. {source_links(['S01','S02','S14'])}</li>
    <li><strong>Reconstruct basis before converting.</strong> Identify each CNY lot, acquisition date, USD basis and the disposition rate. Current balance is not basis. {source_links(['S04','S06','S03'])}</li>
    <li><strong>Use the $200 rule narrowly.</strong> It is a per-transaction personal-gain cliff, not an annual transfer allowance and not a shelter for the whole balance. {source_links(['S01','S02'])}</li>
    <li><strong>Compare all-in execution quotes separately.</strong> The Treasury rate used here is an official reporting reference, not a bank quote. Fees and spread remain blank. {source_links(['S12','S13','S09'])}</li>
    <li><strong>Check reporting before moving large sums.</strong> FBAR and Form 8938 are separate from income tax and depend on aggregate accounts/assets and residence/filing status. {source_links(['S10','S11'])}</li>
  </ol>
</section>
<section class="panel">
  <h2>Reference rate used in the workbook</h2>
  <p>The workbook computes a labeled CNY reference amount using Treasury’s September 30, 2026 reporting rate: <strong>6.7050 CNY per USD</strong>. This is not an executable conversion quote, not necessarily the correct tax transaction-date rate, and the PDF excludes online amendments. {source_links(['S12','S13'])}</p>
</section>
<section class="panel">
  <h2>Choose the tax path before the transfer path</h2>
  <p>The source and use of the CNY determine which U.S. tax questions must be answered. This table is a tax-basis decision aid, not a PRC transfer-eligibility determination.</p>
  <div class="table-scroll" role="region" aria-label="Tax-basis decision paths" tabindex="0">
    <table class="data">
      <thead><tr><th>If the CNY is…</th><th>Tax question</th><th>Next action</th><th>Official source</th></tr></thead>
      <tbody>{''.join(decision_rows)}</tbody>
    </table>
  </div>
</section>
<section class="panel">
  <h2>Where this fits</h2>
  <p>This session owns only the U.S. currency-basis workbook. Other sessions are building the broader route catalogue and cost matrices. Earlier dashboards remain available: <a href="../../docs/index.html">docs</a>, <a href="../../site/index.html">site</a>, <a href="../../portal/index.html">portal</a>, and <a href="../../audit-86f0/index.html">independent audit</a>. Their claims are not all certified by this workbook.</p>
</section>
"""
    page("index.html", "Know the tax before moving the money", body,
         "A mobile-friendly, source-linked workbook for the U.S. tax layer of moving CNY to USD. Unknown values stay blank.")


def build_workbook() -> None:
    rows = []
    for row in WORKBOOK["rows"]:
        rows.append(
            "<tr>"
            f'<th scope="row">${row["target_usd"]:,.0f}</th>'
            + blank_cell("Total cost")
            + blank_cell("U.S. federal tax")
            + blank_cell("Execution fees")
            + f'<td class="num">{esc(row["cny_reference"])}</td>'
            + blank_cell("Acquisition basis")
            + blank_cell("Realized gain")
            + blank_cell("Taxable gain")
            + f'<td class="sources">{source_links(row["source_ids"])}</td>'
            + '<td><a class="badge warn" href="review.html">needs review</a></td>'
            + "</tr>"
        )
    table = "".join(rows)
    body = f"""
<section class="callout warn">
  <strong>Blank means unverified, not zero.</strong>
  <p>No executable bank quote, acquisition basis, disposition rate, transaction classification, filing status or taxable income was supplied. The only computed numeric column is a CNY reference amount from an official reporting rate. It is not a transfer cost estimate.</p>
</section>
<section class="panel">
  <div class="toolbar">
    <p><strong>Target:</strong> USD delivered. <strong>Reference:</strong> {esc(INPUTS['reference_rate']['value'])} CNY/USD, effective {esc(INPUTS['reference_rate']['effective_date'])}. {source_links(INPUTS['reference_rate']['sources'])}</p>
    <p class="downloads"><a class="button small" href="workbook.csv" download>Download CSV</a> <a class="button small" href="workbook.json" download>Download JSON</a></p>
  </div>
  <div class="table-scroll" role="region" aria-label="Currency basis and cost workbook" tabindex="0">
    <table class="data sticky-first">
      <thead>
        <tr>
          <th>USD target</th>
          <th>Total cost USD</th>
          <th>U.S. federal tax USD</th>
          <th>Execution fees USD</th>
          <th>CNY reference</th>
          <th>Acquisition basis USD</th>
          <th>Realized gain USD</th>
          <th>Taxable gain USD</th>
          <th>Official source context</th>
          <th>Review status</th>
        </tr>
      </thead>
      <tbody>{table}</tbody>
    </table>
  </div>
  <p class="note">Source links provide rule/reference context. They do not verify the blank cost cells. A real estimate requires an eligible route, executable quote, exact debit/credit, all fees, and lot-level tax basis.</p>
</section>
<section class="panel">
  <h2>How to complete a real estimate</h2>
  <ol>
    <li>Identify the source of each CNY deposit and whether the account is personal, business or investment.</li>
    <li>For each lot disposed of, record acquisition date, CNY amount, USD basis and the exchange rate used.</li>
    <li>Record the disposition date, executed CNY/USD rate, gross USD proceeds and all sender/intermediary/receiver fees.</li>
    <li>Classify the gain under section 988 and the personal-transaction exception; if capital, determine holding period and rate bracket.</li>
    <li>Compute tax only after tax year, filing status, taxable income, foreign taxes and credit limitations are known.</li>
  </ol>
  <p>{source_links(['S02','S01','S04','S06','S09'])}</p>
</section>
"""
    page("workbook.html", "Cost & tax workbook", body,
         "Most important columns first: total cost, U.S. tax and fees are blank because they cannot be verified from the supplied facts.")


def build_rules() -> None:
    rows = []
    for rule in RULES:
        value = esc(rule["value"]) if rule["value"] else ""
        rows.append(
            "<tr>"
            f'<th scope="row">{esc(rule["id"])} · {esc(rule["topic"])}</th>'
            f'<td>{esc(rule["rule"])}</td>'
            f'<td class="num">{value}</td>'
            f'<td>{badge(rule["status"])}</td>'
            f'<td>{esc(rule["note"])}</td>'
            f'<td class="sources">{source_links(rule["sources"])}</td>'
            "</tr>"
        )
    body = f"""
<section class="panel">
  <div class="table-scroll" role="region" aria-label="Verified rules" tabindex="0">
    <table class="data">
      <thead><tr><th>Rule</th><th>Verified statement</th><th>Value</th><th>Status</th><th>Limit / note</th><th>Official source</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""
    page("rules.html", "Verified U.S. rules", body,
         "Each row links to an official source. Unverified personal amounts are blank and flagged.")


def build_sources() -> None:
    rows = []
    for s in SOURCES.values():
        rows.append(
            "<tr>"
            f'<th scope="row">{esc(s["id"])}</th>'
            f'<td><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a></td>'
            f'<td>{esc(s["locator"])}</td>'
            f'<td>{esc(s["verified_text"])}</td>'
            f'<td>{esc(s["limitation"])}</td>'
            f'<td>{esc(s["retrieved_utc"])}</td>'
            f'<td>{badge(s["status"])}</td>'
            "</tr>"
        )
    body = f"""
<section class="panel">
  <div class="table-scroll" role="region" aria-label="Official sources" tabindex="0">
    <table class="data">
      <thead><tr><th>ID</th><th>Official source</th><th>Locator</th><th>What was read</th><th>Limitation</th><th>Retrieved UTC</th><th>Status</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""
    page("sources.html", "Official source registry", body,
         "Primary U.S. government sources read for this workbook. Training material and dated editions are labeled.")


def build_review() -> None:
    rows = []
    for flag in FLAGS:
        rows.append(
            "<tr>"
            f'<th scope="row">{esc(flag["id"])} · {esc(flag["title"])}</th>'
            f'<td>{badge(flag["status"])}</td>'
            f'<td>{esc(flag["detail"])}</td>'
            f'<td>{esc(flag["affected"])}</td>'
            f'<td class="sources">{source_links(flag["sources"])}</td>'
            "</tr>"
        )
    body = f"""
<section class="callout warn">
  <strong>Needs review does not block publication.</strong>
  <p>These items are published so they can be reviewed after the site is live. They are not verified facts. Corrections to files owned by other sessions are requested in COORDINATION.md rather than edited here.</p>
</section>
<section class="panel">
  <div class="table-scroll" role="region" aria-label="Flagged for review" tabindex="0">
    <table class="data">
      <thead><tr><th>Flag</th><th>Status</th><th>Detail</th><th>Affected</th><th>Official source context</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""
    page("review.html", "Flagged for review", body,
         "Missing private facts, missing quotes, reference-rate limits and repository correction requests.")


def build_methodology() -> None:
    formula_rows = []
    for f in FORMULAS:
        result = esc(f["result"]) if f["result"] else ""
        formula_rows.append(
            "<tr>"
            f'<th scope="row">{esc(f["id"])} · {esc(f["name"])}</th>'
            f'<td><code>{esc(f["formula"])}</code></td>'
            f'<td>{result}</td>'
            f'<td>{badge(f["status"])}</td>'
            f'<td>{esc(f["note"])}</td>'
            f'<td class="sources">{source_links(f["sources"])}</td>'
            "</tr>"
        )
    body = f"""
<section class="panel">
  <h2>Scope</h2>
  <p>This workbook covers the U.S. personal foreign-currency disposition / tax-basis layer. It does not duplicate the general route catalogue or provider price matrices owned by other active sessions. It supplies a reproducible computation contract and correction requests for overbroad conversion-tax claims.</p>
</section>
<section class="panel">
  <h2>Verification standard</h2>
  <ul>
    <li>Every table row links to an official U.S. government source.</li>
    <li>Values that cannot be confirmed from an official source or supplied private fact are blank and flagged.</li>
    <li>Arithmetic is labeled as a computed reference, not a verified transfer cost.</li>
    <li>IRS training material and dated code editions are identified as such.</li>
    <li>No personal account facts, bank quotes or live FX rates were inferred.</li>
  </ul>
</section>
<section class="panel" id="formulas">
  <h2>Computation contract</h2>
  <p>These formulas define what would be computed once verified inputs exist. They are not populated with personal facts or provider quotes. Blank results remain blank.</p>
  <div class="table-scroll" role="region" aria-label="Computation formulas" tabindex="0">
    <table class="data">
      <thead><tr><th>Step</th><th>Formula / rule</th><th>Result</th><th>Status</th><th>Limit / note</th><th>Official source</th></tr></thead>
      <tbody>{''.join(formula_rows)}</tbody>
    </table>
  </div>
  <p class="note"><a class="button small" href="basis-input-template.csv" download>Download blank basis-input template</a> The template contains headers only; do not commit private financial records to this public repository.</p>
</section>
<section class="panel">
  <h2>Reproduce</h2>
  <pre><code>python3 tax-workbook/model.py
python3 tax-workbook/build.py
python3 tax-workbook/verify.py
python3 tax-workbook/serve.py --port 8000</code></pre>
  <p>The static site is generated into <code>tax-workbook/site/</code>. GitHub Pages serves it from the repository root at <code>/China2/tax-workbook/site/</code>.</p>
</section>
<section class="panel">
  <h2>Known limits</h2>
  <p>External links were read during research but are not continuously monitored by this workbook. The Treasury PDF rate excludes online amendments. IRS rate thresholds retrieved are labeled 2025 and are not applied to an unknown tax year. This is not a full repository audit or personalized tax advice.</p>
  <p>{source_links(['S12','S13','S05','S09'])}</p>
</section>
"""
    page("methodology.html", "Methodology & limits", body,
         "How the workbook was built, what was verified, and what remains blank.")


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    build_index()
    build_workbook()
    build_rules()
    build_sources()
    build_review()
    build_methodology()
    shutil.copyfile(DATA / "workbook.csv", SITE / "workbook.csv")
    shutil.copyfile(DATA / "workbook.json", SITE / "workbook.json")
    shutil.copyfile(DATA / "basis-input-template.csv", SITE / "basis-input-template.csv")
    print(f"Built {len(NAV)} pages into {SITE}")


if __name__ == "__main__":
    main()
