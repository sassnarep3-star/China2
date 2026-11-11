#!/usr/bin/env python3
"""Build the corrective acceptance page from the small, source-bound ledger."""
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "index.html"

SAFE_INCOME = "https://www.safe.gov.cn/tianjin/2026/0713/3088.html"
SAFE_QUOTA = "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"
IRS_FTC = "https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit"
IRS_FBAR = "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar"
IRS_RATE = "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates"
GPO_988 = "https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm"
BOC_FEE = "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html"
PRC_COLLECTION = "https://12366.chinatax.gov.cn/bzds/120/120-1-4.html"

FINDINGS = [
    ("V01", "Documented employment income", "SAFE states that an overseas individual's lawful current-account RMB income can be converted at a bank with valid identity documents and transaction-amount/source materials, including tax vouchers.", "Official publisher text checked 11 Nov 2026", SAFE_INCOME, "SAFE Tianjin FAQ 08"),
    ("V02", "USD 50,000 purchase facility is conditional", "SAFE states that overseas individuals holding a Foreign Permanent Resident ID may use the annual purchase facilitation quota. It separately describes the documented-income route; U.S. citizenship alone is not evidence of eligibility for that quota.", "Official publisher text checked 11 Nov 2026", SAFE_QUOTA, "SAFE Tianjin 2024 case 9"),
    ("V03", "Foreign tax credit is not an unrestricted refund", "IRS says a credit may be available when foreign tax is paid or accrued and U.S. tax applies to the same income. It cannot be claimed for tax on income excluded from U.S. gross income, and treaty-reduced tax limits can matter.", "Official publisher text checked 11 Nov 2026", IRS_FTC, "IRS Foreign Tax Credit"),
    ("V04", "FBAR uses an aggregate annual threshold", "IRS states that a U.S. person files FBAR when the person has a qualifying interest or authority and aggregate foreign financial accounts exceed USD 10,000 at any time during the calendar year. Form 8938 is separate.", "Official publisher text checked 11 Nov 2026", IRS_FBAR, "IRS FBAR"),
    ("V05", "Personal currency gain needs analysis", "Section 988(e)(2) excludes certain personal-transaction exchange-rate gain, but the sentence says the exclusion does not apply if the gain exceeds USD 200. The user's acquisition dates and basis are unknown.", "2024 GPO Code edition checked 11 Nov 2026; current application requires review", GPO_988, "26 USC 988(e)(2)"),
    ("V06", "IRS annual averages are not executable bank quotes", "IRS says it has no official exchange rate and generally accepts a posted rate used consistently. Its annual averages therefore must not be presented as a customer's current conversion rate.", "Official publisher text checked 11 Nov 2026", IRS_RATE, "IRS yearly average rates"),
    ("V07", "Bank of China published wire components", "The bank's personal e-banking tariff publishes a cross-border telegraphic-transfer commission of 1‰, minimum CNY 50 and maximum CNY 260 per transfer, plus CNY 150 cable outside Hong Kong, Macau and Taiwan. Its notes allow agreements, discounts and local differences.", "Official bank tariff text checked 11 Nov 2026; not an all-in quote", BOC_FEE, "Bank of China fee table"),
    ("V08", "Overdue PRC tax can add more than principal", "Tax Collection Law Art. 32 publishes a daily 0.05% late-payment surcharge. Arts. 63–64 publish fines of 50% to five times the unpaid or underpaid tax in the circumstances described; they do not establish that the user owes tax.", "Official STA text checked 11 Nov 2026; applicability unknown", PRC_COLLECTION, "PRC Tax Collection Law"),
]

FLAGS = [
    ("F01", "Origin and legal ownership of the balance", "Blank — no bank statement, earning record, property record, gift/inheritance record or emigration history was supplied.", "Obtain statements and the documents that match each tranche to its origin; do not upload private records to this public repository.", SAFE_INCOME),
    ("F02", "PRC tax actually assessed, paid and evidenced", "Blank — no tax record, assessment, withholding certificate or bank refusal was supplied. A large amount described as 'tax' cannot yet be classified.", "Ask the bank for the exact tax type, period, base, legal basis and refusal reason in writing; reconcile against official tax records.", SAFE_INCOME),
    ("F03", "SAFE status and permanent-resident documentation", "Blank — residence history and Foreign Permanent Resident ID status are unknown.", "Have the account-holding bank classify the customer and identify the applicable procedure in writing.", SAFE_QUOTA),
    ("F04", "U.S. currency basis and acquisition dates", "Blank — tranche dates, original USD basis, personal/business character and prior reporting are unknown; no gain or tax is estimated.", "Build a tranche-level acquisition ledger and have a U.S. international tax professional apply §988 and the return rules.", GPO_988),
    ("F05", "FBAR, FATCA and other filing history", "Blank — maximum aggregate balances, filing status, residence and prior filings are unknown.", "Reconstruct annual maximum balances and compare each year with FBAR and Form 8938 instructions; address omissions before moving funds.", IRS_FBAR),
    ("F06", "Executable FX rate and all-in receiving cost", "Blank — no bank supplied an executable quote; intermediary, lifting and U.S. receiving charges are not established by the sender's tariff.", "Request a written same-day quote showing applied rate, sender commission, cable/OUR charge, intermediary deductions and expected net USD.", BOC_FEE),
    ("F07", "Foreign tax credit or exclusion outcome", "Blank — income category, source, treaty position, prior elections and U.S. return history are unknown.", "Have a U.S. international tax professional compare Form 1116 and any exclusion using the actual income and tax records; do not double-count excluded income.", IRS_FTC),
]

CSS = """
:root{--ink:#14231e;--muted:#5a6c64;--paper:#f5f6f2;--card:#fff;--line:#dce3dd;--accent:#086854;--warn:#7b4a06;--warnbg:#fff7e5}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.58 system-ui,-apple-system,Segoe UI,sans-serif}a{color:var(--accent);overflow-wrap:anywhere}.wrap{max-width:1080px;margin:auto;padding:0 1rem}header{background:var(--ink);color:#fff;padding:1rem 0}header a{color:#d8eee7}main{padding:1.5rem 0 3rem}h1{font-size:clamp(1.8rem,5vw,2.65rem);line-height:1.15;margin:.5rem 0}h2{margin-top:2.1rem}.lead{max-width:75ch;font-size:1.05rem}.notice{background:var(--warnbg);border-left:4px solid #b47a13;padding:.85rem 1rem;border-radius:.5rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.75rem;margin:1rem 0}.card{background:var(--card);border:1px solid var(--line);border-radius:.75rem;padding:1rem}.card b,.card span{display:block}.card span{color:var(--muted);font-size:.88rem;margin-top:.3rem}.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:.75rem}table{border-collapse:collapse;width:100%;font-size:.89rem}th,td{text-align:left;vertical-align:top;padding:.72rem;border-bottom:1px solid var(--line)}thead th{background:#edf2ee;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em}tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}.status{font-size:.78rem;color:var(--muted)}footer{border-top:1px solid var(--line);padding:1rem 0;color:var(--muted);font-size:.85rem}@media(max-width:650px){table.cards,table.cards tbody,table.cards tr,table.cards th,table.cards td{display:block;width:100%}table.cards thead{display:none}table.cards tr{border-bottom:8px solid var(--paper);padding:.45rem}table.cards td,table.cards th{border:0;padding:.35rem .55rem}table.cards td::before,table.cards th::before{content:attr(data-label);display:block;font-size:.7rem;font-weight:750;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}.tw{overflow:visible;border:0;background:transparent}}
"""

def link(url, label):
    return f'<a href="{escape(url, quote=True)}" rel="noopener">{escape(label)}</a>'

finding_rows = "".join(
    f'<tr id="{i}"><th scope="row" data-label="Check">{i}</th><td data-label="Finding"><strong>{escape(title)}</strong><br>{escape(text)}</td>'
    f'<td data-label="Verification" class="status">{escape(status)}</td><td data-label="Primary source">{link(url, label)}</td></tr>'
    for i, title, text, status, url, label in FINDINGS
)
flag_rows = "".join(
    f'<tr id="{i}"><th scope="row" data-label="Flag">{i}</th><td data-label="Missing decision input"><strong>{escape(title)}</strong></td>'
    f'<td data-label="Known value">{escape(value)}</td><td data-label="How to discover">{escape(action)}</td><td data-label="Official starting point">{link(url, "Official source")}</td></tr>'
    for i, title, value, action, url in FLAGS
)

HTML = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Corrective acceptance · China Money</title><meta name="description" content="Fresh source checks, final-integration corrections, and unresolved decision inputs for CNY to USD repatriation."><style>{CSS}</style></head>
<body><header><div class="wrap"><a href="../index.html">← China Money dashboard</a><h1>Corrective acceptance</h1><div>11 November 2026 · source-bound final integration · not individualized tax or legal advice</div></div></header>
<main class="wrap">
<p class="lead">This pass improves the existing site rather than adding another competing cost model. It corrects categorical landing-page and README wording, links the complete published-input cost playbook, and records what remains unknown.</p>
<div class="notice"><strong>Bottom line.</strong> Assess a documented bank conversion and outbound wire first only when the balance matches a lawful documented-income route. Property, inheritance, emigrant assets and reconversion need their own procedures. No personal tax amount, route eligibility, executable rate or all-in cost can be established from the information supplied.</div>
<div class="grid">
<a class="card" href="../playbook-c1d73006/EXECUTIVE_SUMMARY.md"><b>Executive summary</b><span>Decision answer and evidence limits</span></a>
<a class="card" href="../playbook-c1d73006/costs.html"><b>Every $10,000 increment</b><span>17 methods × 40 tiers = 680 rows; dated estimates, not quotes</span></a>
<a class="card" href="../playbook-c1d73006/methods.html"><b>Methods and exact steps</b><span>Pros, cons, conditions and rejected channels</span></a>
<a class="card" href="../playbook-c1d73006/questions.html"><b>Decision questions</b><span>What is known, missing and how to discover it</span></a>
</div>
<h2 id="findings">Fresh official-source checks</h2>
<p>Each row below states the narrow proposition checked against the publisher's own text. It is not a conclusion about the user's private facts.</p>
<div class="tw"><table class="cards"><thead><tr><th>Check</th><th>Finding</th><th>Verification boundary</th><th>Primary source</th></tr></thead><tbody>{finding_rows}</tbody></table></div>
<h2 id="flags">Flagged for Review</h2>
<p>These are <strong>needs review</strong>, not blockers to publication. Blank means unverified—not zero. The actions describe how to obtain the missing information without placing sensitive records in this public repository.</p>
<div class="tw"><table class="cards"><thead><tr><th>Flag</th><th>Missing decision input</th><th>Known value</th><th>How to discover</th><th>Official starting point</th></tr></thead><tbody>{flag_rows}</tbody></table></div>
<h2 id="corrections">Repository corrections and limits</h2>
<ul><li>Replaced the root headline's unsupported causal generalization and the KPI's categorical <code>$0</code> conversion-tax presentation.</li><li>Added U.S. basis/currency-gain and foreign-tax-credit qualifications to the first-screen guidance.</li><li>Removed the README's unsupported generic 0.30%–1.50% spread band and unverified future-year exclusion figure from the key conclusions.</li><li>Corrected README build/publishing instructions to identify <code>verification-3347ca0a/build.py</code> as the root-page generator.</li><li>Promoted the 680-row route-by-origin cost playbook; historical 600/680/920-row models remain archived with their assumptions and are not treated as equivalent.</li><li>This is a targeted final-integration review, not a fresh legal certification of every historical line in the repository. Existing frozen audits remain available for manual review.</li></ul>
</main><footer><div class="wrap">No funds moved, bank contacted or return filed. No passport, account number, statement or tax identifier should be committed here. <a href="../COORDINATION.md">Coordination and verification record</a>.</div></footer></body></html>'''
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT} · {len(FINDINGS)} findings · {len(FLAGS)} flags")
