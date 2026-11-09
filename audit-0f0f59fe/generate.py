#!/usr/bin/env python3
"""Generate the independent source-checked review page from its JSON ledgers."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FINDINGS = json.loads((ROOT / "findings.json").read_text(encoding="utf-8"))
SOURCES = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
SOURCE_BY_ID = {s["id"]: s for s in SOURCES}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def source_link(source_id: str) -> str:
    source = SOURCE_BY_ID[source_id]
    return (
        f'<a class="source-link" href="{esc(source["url"])}" '
        f'target="_blank" rel="noopener noreferrer">'
        f'{esc(source_id)} · {esc(source["authority"])}</a>'
    )


def finding_row(item: dict) -> str:
    links = " ".join(source_link(sid) for sid in item["sources"])
    return f"""<tr class="finding" id="{esc(item['id'])}">
      <th scope="row" data-label="Finding">
        <span class="fid">{esc(item['id'])}</span>
        <strong>{esc(item['topic'])}</strong>
        <span class="badge">{esc(item['severity'])} · {esc(item['status'])}</span>
      </th>
      <td data-label="Existing claim">{esc(item['claim'])}</td>
      <td data-label="Source review">{esc(item['evidence'])}</td>
      <td data-label="Correction / action">{esc(item['action'])}</td>
      <td data-label="Official sources" class="citations">{links}</td>
    </tr>"""


def source_row(source: dict) -> str:
    return f"""<tr id="{esc(source['id'])}">
      <th scope="row" data-label="Source">{esc(source['id'])} · {esc(source['title'])}</th>
      <td data-label="Authority">{esc(source['authority'])}</td>
      <td data-label="Locator">{esc(source['locator'])}</td>
      <td data-label="Retrieval / status">{esc(source['retrieved'])} · {esc(source['status'])}</td>
      <td data-label="Manual review"><a class="source-link" href="{esc(source['url'])}" target="_blank" rel="noopener noreferrer">Open official source ↗</a></td>
    </tr>"""


findings_html = "\n".join(finding_row(item) for item in FINDINGS)
sources_html = "\n".join(source_row(source) for source in SOURCES)

PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Independent official-source re-review of the China CNY-to-USD landing-page claims, route eligibility, tax statements and modelled transfer costs.">
<title>Claim review · China money</title>
<style>
:root{{--ink:#142722;--muted:#52675f;--paper:#f5f5ef;--card:#fff;--line:#d8dfd8;--accent:#0b705e;--warn:#7b4b00;--warn-bg:#fff3d8;--blue:#174d69}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.58 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
a{{color:#075d8b;text-underline-offset:2px;overflow-wrap:anywhere}}
a:hover{{color:#003d5d}}
.skip{{position:absolute;left:-9999px;top:auto}}
.skip:focus{{left:1rem;top:1rem;background:#fff;padding:.7rem;z-index:5}}
header.top{{background:var(--ink);color:#f7f6ef;padding:1rem max(1rem,calc((100vw - 1180px)/2))}}
.brand{{font-weight:750;letter-spacing:.02em}}
.stamp{{color:#d0ded6;font-size:.83rem;margin:.2rem 0 0}}
nav{{background:#fff;border-bottom:1px solid var(--line);display:flex;gap:.5rem;overflow-x:auto;padding:.7rem max(1rem,calc((100vw - 1180px)/2));white-space:nowrap}}
nav a{{padding:.42rem .62rem;border-radius:7px;text-decoration:none;font-size:.9rem}}
nav a:hover,nav a[aria-current=page]{{background:#e9f3ee;color:#064d3e}}
main{{max-width:1180px;margin:0 auto;padding:1.3rem clamp(1rem,3vw,2rem) 3rem}}
h1{{font-size:clamp(1.8rem,4.5vw,2.8rem);line-height:1.1;letter-spacing:-.03em;margin:.4rem 0 .7rem}}
h2{{font-size:clamp(1.25rem,3vw,1.7rem);line-height:1.2;margin:0 0 .65rem}}
h3{{font-size:1.08rem;margin:.4rem 0}}
.lede{{font-size:1.07rem;max-width:76ch;color:#30463d}}
section{{margin:1.4rem 0}}
.panel,.notice,.summary{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:1rem clamp(.9rem,2vw,1.35rem);margin:1rem 0;box-shadow:0 7px 24px rgba(20,39,34,.045)}}
.notice{{background:var(--warn-bg);border-color:#ead6a6;border-left:5px solid #a36a10}}
.summary{{border-left:5px solid var(--accent)}}
.summary strong{{color:#075243}}
.steps{{padding-left:1.4rem}}
.steps li{{padding:.28rem 0 .48rem}}
.steps li::marker{{color:var(--accent);font-weight:700}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.75rem;margin:1rem 0}}
.kpi{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:1rem}}
.kpi .label{{margin:0;color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.06em}}
.kpi .value{{font-size:1.45rem;font-weight:760;margin:.22rem 0}}
.kpi .small{{font-size:.86rem;color:var(--muted);margin:0}}
.table-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:#fff}}
table{{border-collapse:collapse;width:100%;min-width:950px}}
th,td{{border-bottom:1px solid var(--line);padding:.82rem .75rem;text-align:left;vertical-align:top}}
thead th{{background:#edf2ed;font-size:.83rem;line-height:1.35;color:#314940}}
tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}}
.finding th{{width:16%;min-width:180px}}
.finding td{{min-width:190px}}
.fid{{display:inline-block;font-size:.75rem;color:var(--muted);font-weight:750;margin-right:.35rem}}
.badge{{display:block;width:max-content;max-width:100%;margin-top:.45rem;padding:.18rem .52rem;background:#fff0cf;color:#654000;border-radius:999px;font-size:.75rem;font-weight:650}}
.citations{{min-width:220px}}
.source-link{{display:inline-block;margin:.1rem .35rem .18rem 0;font-size:.86rem}}
.resources{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:.7rem}}
.resource{{display:block;padding:.85rem 1rem;border:1px solid var(--line);background:#fff;border-radius:10px;text-decoration:none;color:var(--ink)}}
.resource strong{{display:block;color:var(--blue)}}
.resource span{{font-size:.86rem;color:var(--muted)}}
.smallprint{{font-size:.88rem;color:var(--muted)}}
footer{{background:var(--ink);color:#e0e9e3;padding:1.4rem max(1rem,calc((100vw - 1180px)/2));font-size:.86rem}}
footer a{{color:#9fe6cf}}
@media(max-width:760px){{
  main{{padding-top:1rem}}
  .table-wrap{{border:0;background:transparent;overflow:visible}}
  table,thead,tbody,tr,th,td{{display:block;min-width:0;width:100%}}
  thead{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}
  tr.finding,tr[id^="P"]{{border:1px solid var(--line);border-radius:12px;background:#fff;margin:.75rem 0;overflow:hidden}}
  th,td{{border-bottom:1px solid #e8ece8;padding:.66rem .75rem}}
  tbody tr:last-child th,tbody tr:last-child td{{border-bottom:1px solid #e8ece8}}
  tr td:last-child{{border-bottom:0}}
  td::before{{content:attr(data-label);display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:750;margin-bottom:.2rem}}
  .finding th{{min-width:0}}
  .finding td{{min-width:0}}
}}
@media print{{
  nav,.skip{{display:none}}
  body{{background:#fff;font-size:11pt}}
  main{{max-width:none;padding:0}}
  .panel,.notice,.summary,.kpi{{box-shadow:none;break-inside:avoid}}
  a{{color:#000}}
  .table-wrap{{overflow:visible}}
}}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="brand">CHINA MONEY · INDEPENDENT CLAIM REVIEW</div>
<p class="stamp">Official-source text re-retrieved 9 November 2026 · Review limited to the published recommendations and cost framing</p></header>
<nav aria-label="Main navigation">
  <a href="../index.html">Project hub</a>
  <a href="../ladder/index.html">Cost ladder</a>
  <a href="../ladder/costs.html">Scenario cost tables</a>
  <a href="../audit-86f0/costs.html">Blank source-only cost matrix</a>
  <a aria-current="page" href="index.html">Claim review</a>
</nav>
<main id="main">
<h1>What is—and is not—verified about getting CNY to USD</h1>
<p class="lede">This independent re-review checks the current root landing page and generated cost-ladder overview against official Chinese, U.S. and bank-published source text. It does not claim to re-audit every historical repository sentence or decide what tax applies to the private balance.</p>
<div class="notice"><strong>Personal eligibility, tax and total cost remain undetermined.</strong> The request does not identify who owns the account, the source/category and dates of the RMB, tax paid, continuous China residence, permanent-residence ID status, bank/branch, written refusal, or executable FX quote. No route, tax amount, foreign-tax credit or exact cost can be determined from the facts provided. Do not pay an unexplained amount described only as a “conversion tax”; ask the bank to state what it is and why.</div>

<section class="summary" aria-labelledby="summary-title">
<h2 id="summary-title">Executive summary</h2>
<p><strong>Best source-supported next move:</strong> get a written explanation from the account bank that separates (1) a tax amount assessed on the underlying income/asset, (2) a document the bank requires to establish the transaction, and (3) the bank's own fee or FX margin. SAFE's published guidance for a foreign individual's lawful current-account RMB income calls for valid ID and transaction-source evidence including tax documents; the applicable person category and the balance's source still matter. <a href="https://www.safe.gov.cn/tianjin/2026/0713/3088.html" target="_blank" rel="noopener noreferrer">SAFE 2026 current-account income Q&amp;A</a> · <a href="https://www.safe.gov.cn/safe/2008/0806/5321.html" target="_blank" rel="noopener noreferrer">State Council FX Regulations, Arts. 12 and 52</a>.</p>
<p>No separate tax imposed solely for currency conversion was located in the instruments reviewed, but that is not proof that the balance is tax-paid or that no tax is owed. PRC income tax depends on the source category and tax base. A possible U.S. foreign-tax credit is conditional and limited, not an automatic refund. Current all-in bank cost is blank because the bank's executable CNY/USD rate and the user's full fee chain are not published.</p>
</section>

<section id="steps" class="panel">
<h2>Practical sequence, without assuming private facts</h2>
<ol class="steps">
  <li><strong>Ask the bank for its refusal in writing.</strong> Request the exact reason, document list, whether it is asking for a tax payment or a tax certificate, the taxpayer, tax type, tax period, tax base, statutory/administrative basis, and the amount calculation. PRC FX rules require a real and lawful transaction basis and bank document review; they do not make a bank's unexplained label an assessment. <a href="https://www.safe.gov.cn/safe/2008/0806/5321.html" target="_blank" rel="noopener noreferrer">State Council FX Regulations, Art. 12</a> · <a href="https://www.safe.gov.cn/tianjin/2026/0713/3088.html" target="_blank" rel="noopener noreferrer">SAFE 2026 guidance</a>.</li>
  <li><strong>Reconstruct the balance's source.</strong> Match deposits to employment/service, original FX conversion, sale, dividend, inheritance or other source documents; collect PRC tax-payment/withholding records where relevant. Do not apply a salary rate to property proceeds or the reverse. <a href="https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html" target="_blank" rel="noopener noreferrer">PRC Individual Income Tax Law, Arts. 1–6</a>.</li>
  <li><strong>Confirm the FX category and eligibility with the bank.</strong> A U.S. passport alone does not settle the category: the FX regulation includes some foreign nationals continuously resident in China for at least a year in its domestic-individual definition; SAFE separately discusses foreign permanent-residence-ID status. <a href="https://www.safe.gov.cn/safe/2008/0806/5321.html" target="_blank" rel="noopener noreferrer">State Council FX Regulations, Art. 52(2)</a> · <a href="https://www.safe.gov.cn/tianjin/2024/0621/2529.html" target="_blank" rel="noopener noreferrer">SAFE 2024 foreign-individual quota FAQ</a>.</li>
  <li><strong>Get a current executable quote before choosing a channel.</strong> Request the exact applied CNY/USD rate, all conversion and remittance charges, OUR/SHA/BEN fee option, any correspondent/intermediary fees, receiving-bank charges, any per-transfer limits, and the same-name/service eligibility. HSBC's current tariff shows only its own charges and excludes fees by other institutions; its fee-paying currency may use a bank-set exchange rate. <a href="https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf" target="_blank" rel="noopener noreferrer">HSBC China tariff effective 31 Oct 2026</a>.</li>
  <li><strong>Calculate tax separately, with the right professional.</strong> If PRC tax is actually due, have the competent tax office or qualified PRC tax adviser calculate it from the underlying transaction. A U.S. credit may be possible only for qualifying foreign taxes and is subject to U.S. limits; have a U.S. international-tax preparer assess it. <a href="https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html" target="_blank" rel="noopener noreferrer">PRC IIT Law</a> · <a href="https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit" target="_blank" rel="noopener noreferrer">IRS Foreign Tax Credit</a> · <a href="https://www.irs.gov/publications/p514" target="_blank" rel="noopener noreferrer">IRS Publication 514 (2025)</a>.</li>
  <li><strong>Use only the bank-approved route; preserve the audit trail.</strong> Keep the bank's document checklist, tax records, approval, conversion advice, exchange memo and final transfer advice. Do not split transactions to evade limits, use false documents or treat crypto/third-party quota arrangements as a lawful shortcut. <a href="https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html" target="_blank" rel="noopener noreferrer">PBOC FX Rules, Art. 7</a> · <a href="https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html" target="_blank" rel="noopener noreferrer">PBOC virtual-currency notice (2026)</a>.</li>
</ol>
</section>

<section id="costs" class="panel">
<h2>Cost answer: no verified all-in USD amount</h2>
<p>The current published bank tariff is not an executable offer for this account. It can verify some bank fee items for stated HSBC customer segments; it cannot verify the user's CNY/USD spread, the account's eligibility, the exact route, or every receiving/intermediary charge. Since those required components are not source-confirmed, the source-only all-in figure remains <strong>— / unverified</strong>, not zero.</p>
<div class="kpis">
  <div class="kpi"><p class="label">$10,000 principal</p><p class="value">All-in cost: —</p><p class="small">No current account quote or complete fee chain verified.</p></div>
  <div class="kpi"><p class="label">$100,000 principal</p><p class="value">All-in cost: —</p><p class="small">No current account quote or complete fee chain verified.</p></div>
  <div class="kpi"><p class="label">$400,000 principal</p><p class="value">All-in cost: —</p><p class="small">No current account quote or complete fee chain verified.</p></div>
</div>
<div class="notice"><strong>Important about the existing ladder:</strong> its displayed ranges are scenario-model outputs built with spread and route assumptions, including a 2021 tariff, not amounts confirmed for this account. They are preserved for auditability, but do not treat them as official quotes or as satisfying the source-only cost rule. The separate matrix intentionally leaves unverified cells blank.</div>
<div class="resources">
  <a class="resource" href="../ladder/costs.html"><strong>Scenario cost ladder</strong><span>600 route/tier rows; read only with its assumptions and flags.</span></a>
  <a class="resource" href="../ladder/assumptions.html"><strong>Assumptions register</strong><span>Discloses modelled FX spreads and other unknown inputs.</span></a>
  <a class="resource" href="../audit-86f0/costs.html"><strong>Source-only blank-cost matrix</strong><span>22 method rows × 40 increments; blank means unverified, not zero.</span></a>
  <a class="resource" href="../ladder/flagged.html"><strong>Flagged for review</strong><span>Current uncertainties and conditions in the cost-ladder site.</span></a>
</div>
</section>

<section id="findings" class="panel">
<h2>Landing-page findings</h2>
<p class="smallprint">Each row records the inherited claim, what was checked in the official source body, the safer wording/action, and direct links for manual review. “Needs review” means source rules may be verified while this account's eligibility or tax result is unknown.</p>
<div class="table-wrap"><table>
<thead><tr><th>Finding</th><th>Existing claim</th><th>Source review</th><th>Correction / action</th><th>Official sources</th></tr></thead>
<tbody>{findings_html}</tbody>
</table></div>
</section>

<section id="sources" class="panel">
<h2>Official source register</h2>
<p>Source bodies were retrieved directly on 9 November 2026. The HSBC tariff is a bank-published fee schedule, not a government legal source; it is labelled as such. Retrieval does not guarantee that an online document will remain unchanged.</p>
<div class="table-wrap"><table>
<thead><tr><th>Source</th><th>Publisher</th><th>Article / item locator</th><th>Retrieval / status</th><th>Manual review</th></tr></thead>
<tbody>{sources_html}</tbody>
</table></div>
</section>

<section class="panel">
<h2>Other U.S. reporting is separate from transfer permission</h2>
<p>A U.S. citizen may have U.S. tax and foreign-account reporting duties independent of converting funds. IRS guidance says an FBAR generally applies when the aggregate value of reportable foreign financial accounts exceeds $10,000 at any time during the year, and whether an account generated taxable income does not change that FBAR test. Other reporting forms have different thresholds and tests. <a href="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar" target="_blank" rel="noopener noreferrer">IRS FBAR guidance</a> · <a href="https://www.irs.gov/businesses/corporations/do-i-need-to-file-form-8938-statement-of-specified-foreign-financial-assets" target="_blank" rel="noopener noreferrer">IRS Form 8938 guidance</a>.</p>
</section>

<section class="panel">
<h2>Scope and limitations</h2>
<ul>
<li>This review covers the public root landing page and claims presented on the generated cost-ladder overview. It is not a fresh line-by-line review of every legacy dashboard.</li>
<li>It is an informational source review, not legal or tax advice. No bank was contacted, no quote was obtained, no funds were moved, and no returns were prepared.</li>
<li>Where the official evidence does not establish a current account-specific amount or eligibility, this page leaves it undetermined and flags it rather than infer it.</li>
<li>Material source conflict, route uncertainty and outdated statements from the wider repository remain documented in the existing <a href="../ladder/audit.html">repository audit</a> and <a href="../ladder/flagged.html">Flagged for Review</a> pages.</li>
</ul>
</section>
</main>
<footer>
<p><strong>Research, not advice.</strong> Keep passports, account details, statements and tax records out of this public repository.</p>
<p><a href="../index.html">Project hub</a> · <a href="../COORDINATION.md">Task board and verification record</a></p>
</footer>
</body>
</html>
"""

(ROOT / "index.html").write_text(PAGE, encoding="utf-8")
print(f"Generated {ROOT / 'index.html'}: {len(FINDINGS)} findings, {len(SOURCES)} sources")
