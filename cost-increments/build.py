#!/usr/bin/env python3
"""Generate the cost-increments sub-site (static, self-contained, no deps).
Every computed figure comes from model.py; every factual claim carries a
source id that resolves on verification.html. Blank cells mean unverified."""
import html, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from model import (RATE_CNY_PER_USD, RECEIVING_USD, ANNUAL_QUOTA_USD, ROWS,
                   CARD_ANNUAL_CAP_RMB, CARD_DAILY_CAP_RMB, DIVIDEND_WHT)

OUT = pathlib.Path(__file__).parent
USD = lambda v: f"${v:,.2f}"
USD0 = lambda v: f"${v:,.0f}"
CNY = lambda v: f"CNY {v:,.2f}"

def esc(s): return html.escape(str(s), quote=True)

# ---------- sources registry (id, label, url, verified-this-session) ----------
SRC = [
 ("SAFE-1","SAFE — Detailed Rules press Q&A: USD 50,000 annual individual FX quota; beyond-quota authenticity review; cash >USD 5,000/day deposit docs; >USD 10,000/day withdrawal SAFE advance filing; foreign cash export >USD 10,000 requires customs declaration forms","https://www.safe.gov.cn/en/2007/0105/819.html","yes"),
 ("SAFE-2","SAFE Tianjin 2026 personal FX FAQ (2026-07-13): foreign individuals with CNY employment income may purchase FX and remit with valid ID + transaction-value source materials incl. tax payment certificates (Huifa 2020 No. 14 Art. 59)","https://www.safe.gov.cn/tianjin/2026/0713/3088.html","yes"),
 ("SAFE-3","SAFE Q&A on Huifa No. 29 [2017]: overseas cash withdrawals with domestic bank cards capped at RMB 100,000 per person per civil year and RMB 10,000 per card per day; excess blocks card withdrawals in current and following 2 years; consumption not capped","https://www.safe.gov.cn/en/2017/1230/1391.html","yes"),
 ("HSBC-1","HSBC Bank (China) Wealth & Personal Banking Tariff, effective 2026-10-31 — item 2.2.4.1 outward TT issuance 0.1% (min CNY100 / max CNY500; Private Banking individuals Free); 2.2.4.2 cable CNY120 (Free PB individuals); 2.2.4.3 additional cable CNY100; 2.2.4.4 amendment/cancellation up to 5 cables CNY200; Pay Exact +CNY200","https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf","yes"),
 ("HSBC-2","HSBC China — Individual Foreign Exchange Services Guide for Non-Chinese Mainland Individuals (documents for employment-income remittance)","https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/foreign-exchange/personal-foreign-exchange-business-handling-guide-en.pdf","repo"),
 ("IIT-1","PRC Individual Income Tax Law (2018 amendment), official English text — Art. 3: comprehensive income 3%–45% progressive; interest/dividends/leasing/asset-transfer income flat 20%; Art. 6: resident basic deduction RMB 60,000","https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245849/content.html","yes"),
 ("EIT-1","PRC Enterprise Income Tax Law, official English text (STA file library) — Art. 4: EIT rate 25% (company-level profits taxed before any dividend)","https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103003/c5245840/content.html","yes"),
 ("TREATY-1","U.S.–China Income Tax Convention (IRS-ratified text) — Art. 9/10/11/12: dividends, interest, royalties capped at 10% of gross for beneficial owners (equipment rental treated under royalties provisions; protocol saving clause applies to US citizens)","https://www.irs.gov/pub/irs-trty/china.pdf","yes"),
 ("USC988","26 U.S.C. §988 (U.S. Code 2024 ed., govinfo) — (a)(1) FX gain/loss on §988 transactions is ordinary; (c)(1)(C) disposition of nonfunctional currency is a §988 transaction; (e)(1) §988 does NOT apply to personal transactions; (e)(2) personal FX disposition: no gain recognized unless gain exceeds $200; (e)(3) personal transaction definition","https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm","yes"),
 ("FEIE-1","IRS Rev. Proc. 2025-32 (2026 inflation adjustments) — §911 foreign earned income exclusion for 2026: USD 132,900 (2025: $130,000)","https://www.irs.gov/pub/irs-drop/rp-25-32.pdf","yes"),
 ("ECFR-1","31 CFR 1010.821 (eCFR as of 2026-11-05) — FBAR civil penalty maxima for penalties assessed on/after 2025-01-17: non-willful (31 U.S.C. 5321(a)(5)(B)(i)) $16,536; willful (31 U.S.C. 5321(a)(5)(C)(i)(I)) $165,353","https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-B/section-1010.821","yes"),
 ("FED-1","Federal Reserve H.10 (released 2026-11-02) — noon buying rate, China yuan vs USD: 6.6538 CNY per USD on 2026-10-30 (week of Oct 26–30, 2026). Reference only; not an executable customer quote","https://www.federalreserve.gov/releases/h10/current/","yes"),
 ("WISE-1","Wise — Guide to CNY transfers (from-CNY): personal accounts only; sender non-mainland or worked in China; valid Chinese tax record ≤3 years; to own account only; per-transfer caps 300,000 CNY (bank app) / 50,000 CNY (Alipay); overall limit = after-tax salary proven by tax records; fees shown only as executable quote at time of transfer (no static official fee schedule published)","https://wise.com/help/articles/2955298/guide-to-cny-transfers","yes"),
 ("CHASE-1","Chase — published fee materials: incoming domestic/international wires $15 per transfer on cited schedules (varies by account type; business schedule also lists $45/$40 outgoing international). Provider-published, not a regulator figure","https://www.chase.com/content/dam/chase-ux/documents/personal/checking/biz-how-your-transaction-will-work.pdf","yes"),
 ("FBAR-1","IRS — Report of Foreign Bank and Financial Accounts (FBAR): aggregate foreign accounts > $10,000 at any time in the calendar year → FinCEN 114; due April 15, automatic extension to October 15; income irrelevant","https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar","repo"),
 ("CBP-1","U.S. CBP / FinCEN — carrying > $10,000 currency or monetary instruments into/out of the US requires FinCEN Form 105 (CMIR); FinCEN e-filing portal","https://fincen105.cbp.dhs.gov/","repo"),
 ("IRS-CUR","IRS — Foreign currency and currency exchange rates (yearly average rates for tax reporting)","https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates","repo"),
 ("PBOC-1","State Council (English) — Sept 2021 notice: virtual-currency-related business activities are illegal financial activities in the PRC","https://english.www.gov.cn/statecouncil/ministries/202109/24/content_WS614dc30bc6d0df57f98e0c84.html","repo"),
 ("SPC-1","Supreme People's Court, Fa Shi [2019] No. 1 — disguised cross-border FX trading constitutes illegal business operation (repo ledger; not re-fetched this session)","../reports/CNY_TO_USD_RESEARCH_LEDGER.json","repo"),
 ("REPO-1","This repository — line-by-line audit of prior sessions' work and source ledgers","../reports/REPO_LINE_BY_LINE_AUDIT.md","n/a"),
]
SRC_BY_ID = {s[0]: s for s in SRC}

def refs(*ids):
    out = []
    for i in ids:
        s = SRC_BY_ID[i]
        out.append(f'<a class="src" href="{esc(s[2])}" target="_blank" rel="noopener noreferrer" title="{esc(s[1])}">{esc(s[0])}</a>')
    return '<span class="refs">' + ' '.join(out) + '</span>'

def head(title, desc, current):
    nav = [("index.html","Summary"),("increments.html","Cost tables $10k–$400k"),("methods.html","Step-by-step · all routes"),("flagged-for-review.html","Flagged for Review"),("verification.html","Sources & verification")]
    navhtml = ''.join(f'<a href="{h}"{" aria-current=true" if h==current else ""}>{esc(t)}</a>' for h,t in nav)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China Money</title><meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="style.css"></head>
<body><header class="site"><div class="brand"><a href="index.html">¥→$ China Money<small>CNY → USD · U.S. citizen · verified research</small></a><a href="https://github.com/sassnarep3-star/China2" style="color:#8ff0cd;text-decoration:none;font-size:.78rem">View repository ↗</a></div>
<nav class="top" aria-label="Section"><div class="wrap">{navhtml}</div></nav></header>
<main class="wrap"><div class="banner"><strong>Research, not tax or legal advice.</strong> No transfer has been made and no return filed. Facts of the account (source of funds, residency, documents) are unknown; nothing here certifies an individual outcome. Blank cells = not verified. “Estimated” = arithmetic from a published figure. “Analysis” = reasoned inference, not an official statement. See <a href="verification.html">Sources &amp; verification</a>.</div>
'''

def foot():
    return '''</main><footer><div class="wrap"><strong>China Money · cost-increments</strong> · research snapshot November 2026 · reference rate 6.6538 CNY/USD (Federal Reserve H.10, 2026-10-30) · <a href="verification.html">méthodology &amp; flags</a> · <a href="https://github.com/sassnarep3-star/China2/tree/main/cost-increments">generator &amp; data</a> · not affiliated with any government. Unauthorized use of someone else’s FX quota, hidden transfers or falsified documents are offences, not strategies.</div></footer></body></html>'''

BADGE = {"ok":'<span class="badge b-ok">Source-backed</span>',"est":'<span class="badge b-est">Estimated</span>',"anl":'<span class="badge b-anl">Analysis</span>',"unv":'<span class="badge b-unv">Unverified / blank</span>',"bad":'<span class="badge b-bad">Unlawful</span>',"flag":'<span class="badge b-flag">Flagged for review</span>'}

# ============================================================
# PAGE 1 — index.html (executive summary, most important first)
# ============================================================
p1 = []
p1.append(head("Executive summary", "The real, verified cost of moving CNY to USD: no Chinese conversion tax, capped bank fees, the $50,000 quota, US §988(e), FBAR — with $10k-increment tables up to $400k.", "index.html"))
r_quota, r_hsbc, r_988, r_ecfr, r_feie = refs("SAFE-1"), refs("HSBC-1"), refs("USC988"), refs("ECFR-1"), refs("FEIE-1")
r_chase, r_iit, r_cbp = refs("CHASE-1"), refs("IIT-1"), refs("ECFR-1","FBAR-1","CBP-1")
p1.append(f'''<h1>The true cost of getting CNY out of China <span style="color:var(--muted);font-weight:600">($10,000 → $400,000)</span></h1>
<p class="lede">For a U.S. citizen holding CNY in a mainland China bank account. Most important findings first; every figure is either tied to a numbered official source (<a href="verification.html#sources">source registry</a>), clearly labeled an estimate/analysis, or left blank as unverified.</p>

<div class="card" style="border-left:4px solid var(--accent)"><h3 style="margin-top:0">The 60-second answer</h3><ol>
<li><strong>There is no “conversion tax” in China.</strong> SAFE’s individual regime imposes an annual <strong>USD 50,000 per person</strong> facilitation quota (valid ID, processed via the bank; authenticity review above it) — it is a documentation/administrative ceiling, not a percentage tax. {r_quota}</li>
<li><strong>The real variable cost is the bank FX spread — and it is not published anywhere official.</strong> Every “all-in 2% fee” quote must be tested: ask each bank for its <em>executable</em> CNY→USD quote and compare final USD credited. Get at least three written quotes.</li>
<li><strong>Bank wire fees are tiny and capped</strong> (HSBC Premier/Advance example: 0.1% min CNY100 / max CNY500 + CNY120 cable ≈ <strong>US$33–$93 per transfer</strong>; Private Banking individuals: Free). On $400,000 that is ~0.03% {r_hsbc}</li>
<li><strong>US tax on the conversion itself is usually $0.</strong> §988 does not apply to personal transactions; personal FX gain is not recognized at all unless it exceeds <strong>$200 per transaction</strong>. Business/investment FX gain is ordinary income. {r_988}</li>
<li><strong>The expensive mistakes are all on the compliance side</strong>: splitting quotas, underground banking, fake invoices, hidden crypto moves. FBAR penalties alone (2025 maxima): non-willful <strong>$16,536</strong> / willful <strong>$165,353</strong>. {r_ecfr}</li>
<li><strong>Above $50,000/year</strong>, lawful headroom exists only with documents: after-tax <em>employment income</em> remittances (tax certificates), <em>genuine trade</em> FX settlement accounts, <em>emigrant/inheritor</em> approvals, or <em>corporate dividends</em> (10% treaty WHT). Time cost: 8 years at quota alone for $400,000.</li>
</ol></div>

<div class="grid4">
<div class="kpi"><b>$0</b><span>Chinese tax on converting lawful, already-taxed personal funds (not a % of conversion) {r_quota}</span></div>
<div class="kpi"><b>$93–$108</b><span>Known cap on one HSBC Premier/Advance outward wire at $400k (fee + cable + $15 Chase-type receiving) {r_hsbc}</span></div>
<div class="kpi"><b>$200</b><span>Personal US FX gain per transaction below which no gain is recognized (26 USC §988(e)(2)) {r_988}</span></div>
<div class="kpi"><b>$132,900</b><span>2026 foreign earned income exclusion (Rev. Proc. 2025-32, §911) {r_feie}</span></div>
</div>

<h2>Cost leaderboard — USD 100,000 moved (the most-requested increment)</h2>
<div class="table-scroll" role="region" aria-label="Cost at USD 100,000" tabindex="0"><table>
<thead><tr><th>Order</th><th>Route</th><th>Legal status</th><th>Known cost today</th><th>China tax</th><th>US tax on FX gain</th><th>Time to $100k</th></tr></thead><tbody>
<tr><td>1</td><td>After-tax employment income remitted with tax certificates (docs route)</td><td>Lawful, conditional</td><td>≈ $108 known + spread <span class="blank">(spread unverified)</span></td><td>0 (income already taxed; IIT paid at source)</td><td>$0 if personal &le;$200 gain; salary side: FEIE $132,900 possible</td><td>Immediate (subject to bank authenticity check)</td></tr>
<tr><td>2</td><td>Bank wire via annual quota (ID-only, personal funds)</td><td>Lawful</td><td>≈ $108 known + spread <span class="blank">(unverified)</span></td><td>0</td><td>$0 if personal &le;$200 gain</td><td>2 years ($50,000/yr)</td></tr>
<tr><td>3</td><td>Wise from-CNY (personal; tax record ≤3y; to own account)</td><td>Lawful, conditional (provider)</td><td>Quote-only; no published static fee — <span class="blank">unverified</span></td><td>0 (source tax settled)</td><td>same §988(e) rule</td><td>Immediate; capped by proven after-tax salary</td></tr>
<tr><td>4</td><td>Genuine trade FX settlement account remittance</td><td>Lawful, conditional</td><td>Bank-wire fee + docs/admin <span class="blank">(docs unverified)</span></td><td>0 (trade profits taxed via EIT/IIT)</td><td>same §988 rule; business FX gain = ordinary</td><td>Immediate with trade docs</td></tr>
<tr><td>5</td><td>Corporate dividends to you (10% treaty WHT)</td><td>Lawful, conditional</td><td><strong>$10,000 tax</strong> (10% treaty WHT on $100k dividend) + EIT 25% already paid at company level</td><td>10% WHT (treaty)</td><td>dividend taxable; FTC may offset Chinese WHT</td><td>After audit &amp; filing; weeks</td></tr>
<tr><td>6</td><td>Overseas card cash withdrawals</td><td>Lawful</td><td>ATM/FX markup <span class="blank">(unverified)</span>; ≤ RMB100,000/yr total, RMB10,000/day/card</td><td>0</td><td>same §988(e) rule</td><td>≈ 7 years (cap ≈ $15,028/yr at 6.6538) — impractical</td></tr>
<tr><td>7</td><td>Carry banknotes out (≤ USD 50,000 purchase quota)</td><td>Lawful, conditional</td><td>Cash spread (worse than telegraphic) + customs declaration &gt; $10,000 — <span class="blank">unverified</span></td><td>0</td><td>same §988(e) rule</td><td>Physically bounded; declarations both sides</td></tr>
<tr><td>8</td><td>Emigrant asset transfer approval (one-off, SAFE approval)</td><td>Lawful, conditional</td><td>Approval-specific; documentation/adviser costs <span class="blank">(unverified)</span></td><td>0 on transfer itself</td><td>same §988 rule</td><td>Once, after emigration approval</td></tr>
<tr><td>9</td><td>Inheritor asset transfer approval</td><td>Lawful, conditional</td><td>Approval-specific <span class="blank">(unverified)</span></td><td>0 on transfer</td><td>same §988 rule</td><td>Once, per decedent estate</td></tr>
<tr><td>10</td><td>QDII / QDLP institutional channels</td><td>Lawful, conditional (institutional)</td><td>Fund/management fees, subscription costs <span class="blank">(unverified)</span></td><td>0 on transfer</td><td>fund distributions taxable; FTC possible</td><td>Days–weeks; product-dependent</td></tr>
<tr class="unlawful-row"><td>✗</td><td>Underground banking · quota splitting/pooling · fake invoices · crypto rails</td><td><strong>Unlawful</strong></td><td>“Cheap” — but criminal exposure in China (FX &amp; 2021 virtual-currency notices) + US reporting penalties</td><td>—</td><td>—</td><td>Do not use</td></tr>
</tbody></table></div>
<p class="small">“Known cost” = figures published in official/provider tariffs applied mechanically at reference rate 6.6538. “Spread unverified” appears because no official or provider source publishes your bank’s CNY→USD spread — never accept a percentage “conversion tax” quote without an itemized, written breakdown. Sources: {r_hsbc} {r_chase} {r_quota}</p>

<h2>Why the penalty feels big — and where it actually comes from</h2>
<div class="grid3">
<div class="card"><h3>1 · Source-income tax (China)</h3><p>IIT on salary/services (3–45% progressive, RMB 60,000 basic deduction) or 20% flat on interest/dividends/leases/asset transfers. Paid when income arose — usually already paid before conversion. {r_iit}</p></div>
<div class="card"><h3>2 · FX spread (the real cost)</h3><p>Difference between the interbank rate and your executable rate. <strong>Not published.</strong> On $400,000 even 1% = $4,000 — larger than every wire fee above combined. Negotiate or walk away from bad quotes.</p></div>
<div class="card"><h3>3 · Transfer &amp; cable fees</h3><p>Capped: 0.1% (min CNY100/max CNY500) + CNY120 cable (HSBC Premier/Advance). <strong>$33–$108 per transfer</strong>. Pay Exact +CNY200 guarantees beneficiary gets full amount. {r_hsbc}</p></div>
<div class="card"><h3>4 · Quota / time cost</h3><p>USD 50,000 per person per calendar year with ID only. $400,000 takes <strong>8 years</strong> at quota alone; documented routes compress this legally. {r_quota}</p></div>
<div class="card"><h3>5 · US currency-gain tax</h3><p>§988(e)(1): personal transactions are outside §988. (e)(2): no gain recognized unless gain &gt; <strong>$200</strong> per transaction. Business/investment FX gain = ordinary income. {r_988}</p></div>
<div class="card"><h3>6 · Reporting penalties</h3><p>FBAR if aggregate foreign accounts &gt; $10,000 any day (FinCEN 114). 2025 maxima: $16,536 (non-willful) / $165,353 (willful). CMIR &gt; $10,000 physical. Streamlined procedures may cure past misses. {r_cbp}</p></div>
</div>

<h2>Go deeper</h2>
<div class="grid4">
<a class="card" style="text-decoration:none;color:inherit" href="increments.html"><h3>Cost tables $10k→$400k →</h3><p>40 increments; per-method fees, quotas, WHT, spread sensitivity; master matrix.</p></a>
<a class="card" style="text-decoration:none;color:inherit" href="methods.html"><h3>Step-by-step · all 18 routes →</h3><p>Exact procedure, pros/cons and legality for every identified route and workaround.</p></a>
<a class="card" style="text-decoration:none;color:inherit" href="verification.html"><h3>Sources &amp; verification →</h3><p>17-entry official source registry; what was verified this session vs prior ledger; all flags.</p></a>
<a class="card" style="text-decoration:none;color:inherit" href="../docs/index.html"><h3>Research dashboards →</h3><p>The repo’s fuller evidence ledgers: routes, findings, flags (docs / site / portal).</p></a>
</div>
''')
p1.append(foot())
(OUT / "index.html").write_text("".join(p1), encoding="utf-8")
print("index.html", (OUT/"index.html").stat().st_size)

# ============================================================
# PAGE 2 — increments.html ($10k–$400k tables)
# ============================================================
p2 = []
p2.append(head("Cost tables $10k–$400k", "Every USD 10,000 increment from $10,000 to $400,000: verified China-side wire fees (HSBC tariff), receiving fee (Chase example), dividend-route 10% treaty WHT, quota timing, and an illustrative spread sensitivity block.", "increments.html"))
p2.append(f'''<h1>Cost tables: USD 10,000 → USD 400,000 in $10,000 steps</h1>
<p class="lede">Every figure below is computed mechanically from a published source (formula shown). Reference rate <strong>6.6538 CNY/USD</strong> (Federal Reserve H.10, 2026-10-30 — a reference, <em>not</em> an executable customer rate). Your executable rate will be worse by the <strong>spread — which no official source publishes</strong>; it is left blank everywhere and an <em>illustrative, clearly-labeled</em> sensitivity block is provided instead.</p>

<div class="card"><h3 style="margin-top:0">How to read</h3><ul class="small" style="margin:0;padding-left:18px">
<li><span class="badge b-ok">Source-backed</span> = directly from a numbered official/provider document (formula items 2.2.4.1–2.2.4.2).</li>
<li><span class="badge b-est">Estimated</span> = mechanical arithmetic from that source (e.g., CNY→USD at 6.6538), not a quote.</li>
<li><span class="badge b-anl">Analysis</span> = reasoned inference (e.g., quota-years count), not an official statement.</li>
<li><span class="blank">BLANK</span> = cannot be confirmed from an official source today → see <a href="verification.html#flags">flags I-01…</a>. Never filled in “to be helpful”.</li>
<li>“Known subtotal” = China-side wire fee + one US receiving fee ($15, Chase published schedule example). It <strong>excludes</strong> the FX spread, intermediary deductions and any “Pay Exact” CNY200 option.</li></ul></div>

<h2>Master matrix — known, source-backed cost per $10k step</h2>
<div class="table-scroll" role="region" aria-label="Master cost matrix" tabindex="0"><table>
<thead><tr><th>Amount (USD)</th><th>CNY equivalent</th><th>China wire fee (issuance+cable)</th><th>+ US receiving (Chase ex. $15)</th><th>Known subtotal</th><th>Known %</th><th>US §988(e) personal FX gain</th><th>Years at quota only</th><th>If paid as dividend: 10% treaty WHT</th></tr></thead><tbody>
''')
for r in ROWS:
    hi = ' class="hi"' if r["usd"] in (50_000, 100_000, 200_000, 400_000) else ''
    p2.append(f'<tr{hi}><td>{USD0(r["usd"])}</td><td>{CNY(r["cny"])}</td><td>{USD(r["wire_fee_usd"])}</td><td>${RECEIVING_USD}.00</td><td><strong>{USD(r["known_subtotal_usd"])}</strong></td><td>{r["known_pct"]}%</td><td>$0 if personal &amp; ≤$200 gain (statute); else tax on gain</td><td>{r["quota_years"]} yr{"s" if r["quota_years"]>1 else ""}</td><td>{USD0(r["dividend_wht_usd"])}</td></tr>\n')
p2.append(f'''</tbody></table></div>
<p class="small">Highlighted rows ($50k/$100k/$200k/$400k) are anchor points. China wire fee reaches its CNY500 cap at ≈ $75,150, so every amount ≥ $80k costs the same ≈ $93.18 in China-side fees. Dividend WHT column applies only if the balance is extracted as a dividend from a Chinese company (10% treaty cap for beneficial owners) — it is a <em>tax</em>, not a fee, and is normally offset for U.S. purposes by the foreign tax credit (mechanics not verified; see <a href="verification.html#flags">flags</a>). Sources: {refs("HSBC-1","CHASE-1","FED-1","SAFE-1","USC988","TREATY-1")}</p>

<h2>Table A — Bank telegraphic wire (ID-only quota route R01; above-quota documented R02; employment-income remit R09)</h2>
<p class="small">Identical fee mechanics for all three routes (same tariff items). Difference is eligibility &amp; documents, not price: R01 needs only ID &amp; the USD 50,000 quota; R02 needs authenticity documents and has no quota; R09 needs tax payment certificates (foreign individuals’ after-tax employment income). “Pay Exact” option adds CNY200 and removes the receiver’s fee exposure. Private Banking <em>individual</em> customers: fee &amp; cable <strong>Free</strong>.</p>
<div class="table-scroll" role="region" aria-label="Wire route fees per increment" tabindex="0"><table>
<thead><tr><th>Amount</th><th>CNY equivalent</th><th>Issuance fee (0.1%, min 100 / max 500)</th><th>Cable (2.2.4.2)</th><th>Wire fee (CNY)</th><th>Wire fee (USD)</th><th>Known subtotal (incl. $15 receiving)</th><th>Subtotal %</th><th>Quota (ID-only) years</th></tr></thead><tbody>
''')
for r in ROWS:
    p2.append(f'<tr><td>{USD0(r["usd"])}</td><td>{CNY(r["cny"])}</td><td>CNY {r["issuance_cny"]:,.2f}</td><td>CNY {r["cable_cny"]}</td><td>CNY {r["wire_fee_cny"]:,.2f}</td><td>{USD(r["wire_fee_usd"])}</td><td><strong>{USD(r["known_subtotal_usd"])}</strong></td><td>{r["known_pct"]}%</td><td>{r["quota_years"]}</td></tr>\n')
p2.append(f'''</tbody></table></div>
<p class="small">Formula: issuance_fee_CNY = clamp(0.001 × amount_CNY, 100, 500); total_CNY = issuance + 120; USD = ÷ 6.6538. HSBC Premier &amp; Advance identical on these items; Private Banking individuals Free. Additional cable messages (2.2.4.3) CNY100 each; amendment/cancellation (2.2.4.4) CNY200 up to 5 cables; Pay Exact (full payment to beneficiary) +CNY200. No third-party/correspondent deductions included ({refs("HSBC-1","FED-1")}).</p>

<h2>Table B — If the money is company profit: treaty WHT on dividends (R08)</h2>
<p class="small">Applies only to balances held in a Chinese company distributed as dividends to you. Steps 1–2 taxed before distribution: EIT 25% at company level (Art. 4 EIT Law), then 10% treaty WHT on the dividend (Art. 9/10; beneficial owner). US side: dividend taxable at ordinary rates; FTC generally available for the WHT (mechanics &amp; ceilings <strong>not verified this session</strong> — see flags).</p>
<div class="table-scroll" role="region" aria-label="Dividend withholding per increment" tabindex="0"><table>
<thead><tr><th>Dividend (USD)</th><th>10% treaty WHT</th><th>You receive (before US tax)</th><th>Company-level EIT note</th></tr></thead><tbody>
''')
for r in ROWS:
    p2.append(f'<tr><td>{USD0(r["usd"])}</td><td><strong>{USD0(r["dividend_wht_usd"])}</strong></td><td>{USD0(r["usd"]-r["dividend_wht_usd"])}</td><td>Profits already taxed 25% EIT before dividend declared</td></tr>\n')
p2.append(f'''</tbody></table></div>
<p class="small">Sources: {refs("TREATY-1","EIT-1","IIT-1")} The 20% IIT flat rate (Art. 3(3)) applies to individual dividends where treaty relief is not claimed — the 10% treaty cap prevails for a US resident beneficial owner.</p>

<h2>Table C — Overseas card cash withdrawals (R05) &amp; banknotes carried out (R06): feasibility per step</h2>
<div class="table-scroll" role="region" aria-label="Cash feasibility" tabindex="0"><table>
<thead><tr><th>Amount (USD)</th><th>Card route — days needed (RMB 10,000/day/card)</th><th>Card route — annual feasibility (RMB 100,000/yr)</th><th>Banknotes route (R06) — quota consumed</th><th>CMIR/customs declaration</th></tr></thead><tbody>
''')
for r in ROWS[::2]:
    import math as _m
    days = _m.ceil(r["cny"]/CARD_DAILY_CAP_RMB)
    fais = "Within 1 year" if r["cny"] <= CARD_ANNUAL_CAP_RMB else f"{_m.ceil(r['cny']/CARD_ANNUAL_CAP_RMB)} years at card cap"
    quota = "Yes — uses ID-only quota" if r["usd"] <= 50_000 else "Exceeds USD 50,000/yr quota"
    p2.append(f'<tr><td>{USD0(r["usd"])}</td><td>≥ {days:,} days (single card)</td><td>{fais}</td><td>{quota}</td><td>&gt; $10,000 cash → FinCEN 105 (US) + customs declaration forms (CN)</td></tr>\n')
p2.append(f'''</tbody></table></div>
<p class="small">Card markup/ATM fees are provider- and network-specific and are <strong>not published by any official source — left blank/unverified</strong>. Banknotes route additionally requires SAFE purchase within the USD 50,000 quota and worse cash-notes FX rates. Sources: {refs("SAFE-1","SAFE-3","CBP-1")}</p>

<h2>Table D — Illustrative FX-spread sensitivity <span class="badge b-anl">Analysis</span></h2>
<p class="small"><strong>ILLUSTRATIVE ONLY — not a quote and not from any official source.</strong> Shows what an unpublished spread would cost if it equaled 0.25% / 0.50% / 1.00% / 2.00% of the amount. Compare with Table A’s ≈$33–$93 fees: <strong>the spread dominates everything</strong>.</p>
<div class="table-scroll" role="region" aria-label="Illustrative spread sensitivity" tabindex="0"><table>
<thead><tr><th>Amount (USD)</th><th>Spread 0.25%</th><th>Spread 0.5%</th><th>Spread 1%</th><th>Spread 2%</th><th>Known wire fee at same amount</th></tr></thead><tbody>
''')
for r in ROWS:
    p2.append(f'<tr><td>{USD0(r["usd"])}</td><td>{USD0(r["usd"]*0.0025)}</td><td>{USD0(r["usd"]*0.005)}</td><td>{USD0(r["usd"]*0.01)}</td><td>{USD0(r["usd"]*0.02)}</td><td>{USD(r["known_subtotal_usd"])}</td></tr>\n')
p2.append(f'''</tbody></table></div>
<p class="small">Get your bank’s executable quote; do not accept “estimated 1%” from any intermediary. Reference: Federal Reserve H.10 for checking arithmetic only. Sources: {refs("FED-1","HSBC-1")}</p>

<h2>Bottom line at the largest increment ($400,000)</h2>
<div class="card" style="border-left:4px solid var(--accent)"><ul style="margin:0;padding-left:18px">
<li><strong>Known fees (wire + $15 receiving): $108.18</strong> — 0.027% of the amount.</li>
<li><strong>Chinese tax on the conversion: $0</strong> (no conversion tax exists; income tax attaches to the income when earned).</li>
<li><strong>US tax on the conversion: $0</strong> if the disposition is a personal transaction whose FX gain ≤ $200; otherwise ordinary/capital tax on the gain (basis &amp; dates required — cannot be computed without your acquisition data; left blank by design).</li>
<li><strong>The unknowables (blank by policy):</strong> your bank’s spread, correspondent deductions, document/translation/notarisation and adviser costs, Wise’s executable fee, your FEIE/FTC position.</li>
<li><strong>Time:</strong> 8 years via quota alone vs. immediate (documented) via R02/R09 — choose on documents, not on price.</li>
<li><strong>Reporting:</strong> FBAR if aggregate accounts &gt; $10,000 at any time; CMIR &gt; $10,000 carried; retain bank confirmations for basis/booking date.</li>
</ul></div>
''')
p2.append(foot())
(OUT / "increments.html").write_text("".join(p2), encoding="utf-8")
print("increments.html", (OUT/"increments.html").stat().st_size)

# ============================================================
# PAGE 3 — methods.html (step-by-step for every route, R01–R18)
# ============================================================
ROUTES = [
("R01","Bank wire inside the USD 50,000 annual individual FX quota","lawful","USD 50,000 / person / calendar year",
 ["Valid ID (passport/PRC ID) at any Chinese bank counter or FX app","State the purpose (e.g., personal remittance)","Bank buys USD for you from CNY within your remaining annual quota (SAFE system checks)","Funds wired to your US account; keep the remittance advice for FBAR basis/booking"],
 ["Simplest lawful route — ID only, no transaction documents inside the quota","Clean audit trail for SAFE and the IRS","Per-person, per-year only — $400,000 means 8 calendar years via this route alone"],
 ["Hard USD 50,000/yr ceiling","Authenticity review still applies; bank may ask purpose questions","Spread and fees as in Table A (page 2); spread unpublished"],
 refs("SAFE-1","HSBC-1")),
("R02","Above-quota bank wire with authenticity documents","lawful-conditional","Not capped by the quota; conditioned on documentary support",
 ["Identify the underlying genuine transaction (employment income, family maintenance, inheritance, donation, services)","Collect supporting documents: tax payment certificates, employment contract + payslips, notarised relationship/donation/inheritance instruments, income proof of overseas payer","Apply at bank for FX purchase/remittance above quota; bank reviews authenticity via SAFE-linked system","Wire executes if documents support the full amount; keep everything for 7+ years"],
 ["The only lawful >USD 50,000 fast route for personal balances with documentary basis","No annual ceiling where documents prove the transaction","Defence-grade documentation trail"],
 ["Bank discretion on document sufficiency; can be slow","Notarisation/translation costs unverified (blank)","Family maintenance requires notarised relationship + overseas payer’s income & tax certificates"],
 refs("SAFE-1","SAFE-2","HSBC-2")),
("R03","Emigrant asset transfer (property proceeds transferred abroad on emigration)","lawful-conditional","Governed by SAFE approval document; lump sum or batches",
 ["Emigrate with visa/permission first (PRC no longer uses the old hukou cancellation certificate in all cities — check the SAFE approver for your locale)","Apply to SAFE with identity, emigration approval, asset transfer contract & tax settlement proof","SAFE issues an approval for a capped amount","Remit within the approved limit; batch if needed"],
 ["Moves property-sale proceeds that would otherwise take many quota-years","One approval; no quota consumption"],
 ["Emigration is a life decision, not a fee choice","Approval-specific cap; adviser/legal costs blank (unverified)","Time-consuming; tight documentary scrutiny"],
 refs("SAFE-1")),
("R04","Inheritor asset transfer (inherited China assets)","lawful-conditional","Governed by SAFE approval; one application per decedent",
 ["Obtain decedent’s death certificate + your inheritance right document (notarised will / statutory inheritance agreement)","Apply to SAFE with identity, decedent proof, estate contract and tax settlement where applicable","SAFE issues approval capped to the estate","Remit lump sum or batches"],
 ["Lawful route for inherited balances","No quota consumption"],
 ["Only for genuine inheritances","Notarisation costs blank (unverified)","False documents → criminal exposure (R17)"],
 refs("SAFE-1")),
("R05","Overseas cash withdrawals with a Chinese bank card","lawful","RMB 100,000 per person per civil year (all cards); RMB 10,000 per card per day",
 ["Withdraw cash at overseas ATMs/counters with domestic debit card — never above daily/annual caps","Arrival in US: >$10,000 in currency must be reported on FinCEN Form 105"],
 ["No quota consumption, no bank interview","Genuinely useful for travel float"],
 ["≈ USD 15,028/yr ceiling at 6.6538 — hopeless for $400k","ATM & FX markup fees blank (unverified)","Excess → cards blocked in current + next 2 years"],
 refs("SAFE-3","CBP-1")),
("R06","Purchase FX and carry banknotes out of China","lawful-conditional","Bounded by USD 50,000 purchase quota; >USD 10,000 cash → customs declaration forms",
 ["Within quota, buy USD banknotes at the bank (cash buy rate — worse than telegraphic)","If carrying >USD 10,000 equivalent: obtain bank/customs-signed declaration forms","Declare on both borders (CN exit; US entry CMIR >$10,000)"],
 ["Works without any wire intermediary","No remittance fee at all"],
 ["Cash notes rate is worse than spot — spread penalty highest here","Physical risk; limited to USD 50k/yr","Two declarations required"],
 refs("SAFE-1","CBP-1")),
("R07","Individual FX settlement account for genuine trade","lawful-conditional","No quota — bounded only by genuine trading documents",
 ["Prove you are an individual trader (contract for goods/services, customs declarations, tax filings)","Open a foreign exchange settlement account (treated as institutional account)","FX settlement/payment against trade documents regardless of amount"],
 ["No annual cap; scalable to any size","Institutional-style processing"],
 ["Only if you genuinely trade","Fabricated trade documents = R16 (criminal)","Admin overhead; account thresholds for customs practice blank (unverified)"],
 refs("SAFE-1")),
("R08","Corporate profit repatriation (your Chinese company)","lawful-conditional","Not governed by the individual quota; current-account",
 ["Company declares profits & pays EIT 25% (Art. 4) and any surcharges","Allocate dividends with board resolution; withhold treaty WHT (10% for US beneficial owner, Art. 9/10)","File tax certificates; bank remits dividend — no quota consumed","US: report dividend; claim FTC for Chinese WHT (mechanics unverified)"],
 ["Scales to $400k+ without quota or personal drama","10% WHT is capped and usually creditable in the US"],
 ["Requires a real company, real profits, audited books","EIT 25% + 10% WHT leak (≈32.5% of pre-EIT profit)","FTC mechanics for your case: blank (unverified)"],
 refs("TREATY-1","EIT-1","IIT-1","SAFE-1")),
("R09","After-tax employment income — foreign individuals working in China","lawful-conditional","Current-account with documents; NOT the USD 50,000 purchase quota route",
 ["Keep every payslip + annual IIT final settlement (汇算清缴) certificate","Apply at bank to purchase FX & remit with valid ID + source materials incl. tax payment certificates (Huifa 2020 No. 14, Art. 59)","US: salary taxable in US; FEIE (2026: $132,900) may exclude it if you qualify (bona fide residence / physical presence)","FTC alternative if not FEIE-eligible"],
 ["Handles exactly the “money earned in China” fact pattern","No quota games; authenticity proven by tax receipts","Direct answer to “least tax” for salary balances"],
 ["Only the after-tax salary portion qualifies — never principal/deposits","Wise’s parallel product requires same proof and caps per transfer","FEIE ≠ automatic; bona fide residence test is fact-heavy"],
 refs("SAFE-2","HSBC-2","FEIE-1","IIT-1")),
("R10","Remit foreign exchange already held in a Chinese FX account","lawful-conditional","Quota covers FX purchases/sales — not transfers of FX you already hold, subject to authenticity review",
 ["If the account already holds USD/EUR: instruct the bank to outward-remit","Bank authenticates the source; no purchase occurs, so no quota consumption","Your CNY question doesn’t apply directly — but converting CNY→FX first consumes quota (R01)"],
 ["Bypasses quota for pre-existing FX balances","Clean, documented"],
 ["Irrelevant if your balance is CNY (conversion itself is the FX purchase)","FX account rules differ by bank; terms blank (unverified)"],
 refs("SAFE-1")),
("R11","Transfers between your own FX accounts / direct relatives","lawful-conditional","Bounded by recipient’s own quota position",
 ["Same-name or direct-relative FX account transfer","Bank verifies same nature & relationship","No purchase occurs; receiver’s quota untouched for transfers of existing FX"],
 ["Useful repositioning within family FX accounts","No fees beyond wire (if wired externally)"],
 ["Does not convert CNY→USD; only moves existing FX","Gift/contract docs needed cross-border"],
 refs("SAFE-1")),
("R12","Leave it in CNY and spend abroad (card consumption)","lawful","No cap on overseas consumption itself",
 ["Use UnionPay/international card for overseas spending — consumption is excluded from the RMB 100,000 cash-withdrawal cap","Merchant/acquirer converts at purchase time; spread embedded in the purchase rate"],
 ["Zero FX paperwork; best for genuine living costs abroad","No remittance fee; no quota"],
 ["Doesn’t put USD in a US bank — unusable for a US balance or US bills","Card purchase FX markup: blank (unverified)","Not a strategy for idle $400k"],
 refs("SAFE-3")),
("R13","Virtual currency / crypto rails out of China","unlawful","Prohibited — all crypto business is an illegal financial activity in the PRC (2021 notice)",
 ["— do not do this —"],
 ["None that survives audit"],
 ["Criminal exposure in China (illegal business operation; FX offences)","US side: full reporting (Form 8949/8938/FBAR) never disappears; “crypto didn’t move through banks” is not a defence","Losing the funds is common; recovery nil"],
 refs("PBOC-1")),
("R14","Splitting / pooling annual quotas via relatives’ IDs","unlawful","Prohibited — quota evasion",
 ["— do not do this —"],
 ["None"],
 ["SAFE’s bank-linked system flags repeated/structured purchases","Penalties under FX regulations; criminal if organised","Every ‘helper’ absorbs personal liability"],
 refs("SAFE-1")),
("R15","Underground banking / offset matching with no cross-border flow","unlawful","Prohibited",
 ["— do not do this —"],
 ["None"],
 ["SPC Fa Shi [2019] No. 1: disguised cross-border FX trading = illegal business operation (repo ledger)","Confiscation + fines; imprisonment at scale"],
 refs("SPC-1","REPO-1")),
("R16","Fabricated or inflated trade invoicing to open the current account","unlawful","Prohibited",
 ["— do not do this —"],
 ["None"],
 ["Documentary fraud; customs and SAFE penalties; criminal at scale","Forensic audits routinely catch it"],
 refs("SAFE-1")),
("R17","False emigrant/inheritor applications","unlawful","Prohibited",
 ["— do not do this —"],
 ["None"],
 ["Negates R03/R04 and invites criminal referral; SAFE approvals are revocable"],
 refs("SAFE-1")),
("R18","QDII / QDLP institutional outbound investment","lawful-conditional","Institutional quotas; product-dependent (personal not direct)",
 ["Buy QDII/QDLP fund via bank/broker (denominated USD/HKD) with CNY through normal sales channel","Subject to fund’s own quota & dealing spread; repatriate on redemption"],
 ["Only regulated outbound investment channel for retail CNY","Fits long-term investors, not cash-outs"],
 ["Not a same-day remittance tool; lock-ups and NAV spreads","Fund fees & limits: blank (unverified)","Redemption timing not guaranteed"],
 refs("SAFE-1","REPO-1")),
]
STATUS_LABEL = {"lawful":"Lawful","lawful-conditional":"Lawful · conditional","unlawful":"UNLAWFUL"}

p3 = []
p3.append(head("Step-by-step · all routes", "Exact procedure, pros, cons and legality for all 18 identified routes to move CNY→USD — including the unlawful ones you must avoid.", "methods.html"))
p3.append(f'''<h1>Step-by-step: every identified route (R01–R18)</h1>
<p class="lede">For each route: who qualifies, the exact steps in order, the pros, the cons, and the cost references to <a href="increments.html">page 2</a>. Unlawful routes are listed so you can recognise and refuse them — they are never cost alternatives.</p>
''')
for rid, name, status, limit, steps, pros, cons, srefs in ROUTES:
    cls = "unlawful-row" if status=="unlawful" else ""
    badge = f'<span class="badge b-bad">{STATUS_LABEL[status]}</span>' if status=="unlawful" else (f'<span class="badge b-flag">{STATUS_LABEL[status]}</span>' if status=="lawful-conditional" else f'<span class="badge b-ok">{STATUS_LABEL[status]}</span>')
    p3.append(f'<section class="card" id="{esc(rid)}"><h2 style="border:none;margin:0 0 4px">{esc(rid)} — {esc(name)} {badge}</h2><p class="small" style="margin:2px 0 6px"><strong>Limit / headroom:</strong> {esc(limit)} &nbsp; {srefs}</p><div class="grid3"><div><h3>Steps</h3><ol class="steps">' + ''.join(f'<li>{esc(s)}</li>' for s in steps) + '</ol></div><div><h3>Pros</h3><ul class="steps">' + ''.join(f'<li>{esc(s)}</li>' for s in pros) + f'</ul></div><div><h3>Cons / risks</h3><ul class="steps">' + ''.join(f'<li>{esc(s)}</li>' for s in cons) + '</ul></div></div></section>\n')
p3.append(f'''<div class="card" style="border-left:4px solid var(--gold)"><h3 style="margin-top:0">The one-line rule</h3><p style="margin:0"><strong>If someone offers you a CNY→USD conversion cheaper than the bank route (R01/R02/R09), it is either subsidised by a real document (R02/R07/R09) or it is a crime wearing a fee schedule.</strong> Ask for the written tariff item and the FX quote behind any number you are quoted; if they hesitate, walk away.</p></div>''')
p3.append(foot())
(OUT / "methods.html").write_text("".join(p3), encoding="utf-8")
print("methods.html", (OUT/"methods.html").stat().st_size)

FLAGS = [
  ('I-01','Any bank’s CNY→USD FX spread for your account','No official or provider page publishes it; only an executable quote at transaction time does. Close via: written quote from 3 banks before moving funds.','HSBC transfers page (provider) <a href="https://www.hsbc.com.cn/en-cn/transfer-payments/" target="_blank" rel="noopener noreferrer">link</a>'),
  ('I-02','Wise executable fee for your exact amount &amp; date','Wise publishes fees only inside the flow; no static schedule. Close via: screenshot of quote at booking; verify limit derived from your tax records.','WISE-1'),
  ('I-03','Correspondent/intermediary bank deductions end-to-end','Varies by routing; HSBC tariff expressly excludes third-party charges. Close via: “Pay Exact” option (+CNY200) or written SWIFT fee split.','HSBC-1'),
  ('I-04','Receiving-bank fee at non-Chase US banks (BofA, Wells, credit unions)','Chase $15 used as labelled example only. Close via: your bank’s published fee schedule PDF.','CHASE-1'),
  ('I-05','Documentary costs (notarisation, translation, legal/adviser, translation of tax certificates) for R02/R03/R04/R09','Market-priced, not regulated; no official figure exists. Close via: 2–3 provider quotes in writing.','HSBC-2 (documents listed, prices not published)'),
  ('I-06','Chinese VAT/surcharges on outward-remittance service or on FX-sale fees','Rate application to bank FX fees for individuals not confirmed in an official English text this session. Close via: STA written ruling or bank’s invoice line items.','—'),
  ('I-07','PRC penalties for FX violations (arts. of FX Regulations, amounts)','Regulation text not re-read line-by-line this session (prior repo ledger excluded stale provisions). Close via: full English text of the FX Regulations + SAFE penalty notices.','../reports/CNY_TO_USD_RESEARCH_LEDGER.json (repo)'),
  ('I-08','Form 8938 thresholds for your filing status/residence','IRS comparison page exists; threshold values not re-verified this session; deliberately omitted. Close via: IRS comparison page + 26 USC 6038D.','https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements'),
  ('I-09','FTC mechanics &amp; ceilings for your Chinese WHT/IIT against §904 limitation','Category, basket, and §904(d) analysis require your full income picture. Close via: preparer computation; IRS FTC page.','https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit'),
  ('I-10','Treaty saving clause effect on <em>your</em> WHT claims (you are a US citizen)','Protocol saving clause lets the US tax its citizens anyway; China-side WHT still capped at 10% (Art. 9/10/11/12) for beneficial owners, but the US net position depends on FTC. Analysis, not legal advice.','TREATY-1'),
  ('I-11','“No quota for documented employment remittances” — official text reading','SAFE 2026 FAQ states the documentary condition; it does not print the phrase “no quota”. Repo prior analysis treated it as current-account outside the facilitation quota. Treat as strong, flagged inference; confirm at your SAFE-supported bank before relying.','SAFE-2'),
  ('I-12','Exact PRC cash-carry declaration threshold in English (USD 5,000 vs 10,000 reporting lines; customs vs SAFE split)','SAFE 2007 Q&amp;A confirms: foreign cash out &gt; USD 10,000 equivalent → customs/bank declaration forms required. A separate customs declaration figure for CNY banknotes (commonly cited RMB 20,000) is NOT confirmed from an official English source; omitted.','SAFE-1'),
  ('I-13','FBAR “greater of $100,000/50% of balance” branch of the willful penalty per account','eCFR 1010.821 states the adjusted $165,353 ceiling; the statute’s greater-of rule not restated in the table. Both readings captured; penalty exposure analysis belongs to counsel.','ECFR-1; 31 USC 5321(a)(5)(C)'),
  ('I-14','Whether HSBC Advance tier equals Premier on items 2.2.4.1–2.2.4.4 for your account','Tariff shows identical Advance &amp; Premier pricing on these items (verified in-place), but your eligibility tier &amp; negotiated waivers are bank-specific. Close via: account’s own tariff letter.','HSBC-1'),
  ('I-15','Carrying USD into the US: CBP inspection mechanics and record-retention duties at the border','CMIR filing duty confirmed; inspection protocol not line-by-line re-verified. Close via: CBP “Money and Other Monetary Instruments” page.','https://www.cbp.gov/travel/international-visitors/money-monetary-instruments'),
]

def flags_rows():
    return ''.join(f'<tr><td>{fid}</td><td>{item}</td><td>{why}</td><td>{src}</td></tr>' for fid,item,why,src in FLAGS)

# ============================================================
# PAGE 4 — verification.html (methodology, flags, sources)
# ============================================================
p4 = []
p4.append(head("Sources & verification", "What was verified, how, and what is flagged — 17 official/provider sources; blank cells explained; repo spot-audit notes.", "verification.html"))
r_iit_eit, r_hsbc4, r_safe4, r_ecfr_cbp = refs("IIT-1","EIT-1"), refs("HSBC-1"), refs("SAFE-1"), refs("ECFR-1","CBP-1","PBOC-1")
p4.append(f'''<h1>Sources, method &amp; flagged items</h1>

<h2>Methodology in 6 lines</h2>
<ol>
<li>Primary sources only: .gov / .gov.cn / irs.gov / ecfr.gov / federalreserve.gov / chinatax.gov.cn / safe.gov.cn / gov.cn / govinfo.gov, plus published bank/provider tariffs (HSBC China; Chase; Wise), which are price evidence, not law.</li>
<li>Every number in the increment tables is computed by <code>model.py</code> from a published figure; the exact formulas are printed under each table. Nothing is hand-typed per row.</li>
<li>Reference rate 6.6538 CNY/USD = Federal Reserve H.10 noon buying rate, 2026-10-30 (published 2026-11-02). Used only for CNY↔USD arithmetic parity checks, not as a quote.</li>
<li>No value was inferred, back-filled or rounded from memory. Unreachable or unofficial figures are left blank and flagged below.</li>
<li>“This session” = 2026-11-08 (UTC). Prior-session ledgers are linked and labelled “repo” — not silently re-asserted as re-verified.</li>
<li>This is a research document. It is not personalized advice; account facts (source category, residency, documents) change every answer.</li>
</ol>

<h2>The conversion penalty, decomposed (5 layers)</h2>
<ol>
<li><strong>Chinese income/profit tax on the source</strong> — usually already suffered; not a “conversion” cost. IIT 3–45% / 20% flat; EIT 25% (company). {r_iit_eit}</li>
<li><strong>FX spread at conversion</strong> — unpublished; your real negotiation lever. Illustrative sensitivity on <a href="increments.html">page 2</a>.</li>
<li><strong>Fees</strong> — capped wire (≈$33–$93) + cable; receiving $15 (Chase example); Pay Exact +CNY200. {r_hsbc4}</li>
<li><strong>Time/quota cost</strong> — USD 50,000/yr ID-only; documented routes uncap the wait. {r_safe4}</li>
<li><strong>Failure/reporting exposure</strong> — FBAR $16,536/$165,353 (2025); CMIR; FX-regulation penalties; criminal law for unlawful routes. {r_ecfr_cbp}</li>
</ol>

<h2 id="flags">Flagged for review — nothing here may be relied on until closed</h2>
<div class="table-scroll" role="region" aria-label="Flags" tabindex="0"><table>
<thead><tr><th>ID</th><th>Item flagged</th><th>Why blank / what would close it</th><th>Best source found</th></tr></thead><tbody>
{flags_rows()}</tbody></table></div>

<h2>Repository spot-audit (this session, 2026-11-08)</h2>
<ul>
<li>Base <code>bb7796b</code> = <code>main</code> HEAD; contains all prior sessions’ merged work (PRs #1, #3, #4, #6–#11). Working tree was clean.</li>
<li>All prior dashboards re-checked only at the seams relevant here: <code>docs/costs.html</code> blank-cell policy upheld (no invented spreads); <code>data/methods.json</code> 18 routes reviewed line-by-line; <code>reports/CNY_TO_USD_RESEARCH_LEDGER.json</code> spot-checked for SPC/PBOC citations used here.</li>
<li><code>reports/REPO_LINE_BY_LINE_AUDIT.md</code> (prior session) found pre-existing irregularities — retained, endorsed, and cross-linked; none were silently “fixed” in another session’s files.</li>
<li>Open PR #12 (<code>arena/5cdc93ae-china2</code>) was in flight during this session and is <strong>not touched</strong> by this work; it edits <code>research/00–06*.md</code>, <code>deep-dive/**</code>.</li>
<li>Merge note (2026-11-08, merged onto <code>84967fc</code> = current <code>main</code>): while this work was in flight, sessions <code>arena/86f0e94b-china2</code> (<code>audit-86f0/</code>, PRs #13/#14) and <code>arena/de9755b1-china2</code> (<code>ladder/</code>, PR #15) merged to <code>main</code>. Root <code>index.html</code> is now a generated navigation hub linking <code>ladder/</code>, <code>docs/</code>, <code>site/</code>, <code>portal/</code> and <code>audit-86f0/</code>; <code>README.md</code> leads with <code>ladder/</code>. This session edited neither (shared outputs of the integration role). Re-verified after the merge (<code>verify.py</code> green); the earlier “root redirect” wording was removed. Relationship stated plainly: <code>ladder/</code> models a spread <em>band</em> on 15 routes; <code>audit-86f0/</code> leaves cost cells blank on 22 routes; this site publishes the <strong>source-backed fee components computed mechanically and leaves the spread blank</strong> — consistent caps, different presentation; none is a quote.</li>
<li>Link request logged in COORDINATION.md to add <code>/China2/cost-increments/</code> to the root hub and <code>docs/</code> navigation at the next integration that owns those files; this session did not edit other sessions’ files.</li>
<li>Arithmetic parity &amp; link checks: <code>python3 verify.py</code> (see <a href="https://github.com/sassnarep3-star/China2/tree/main/cost-increments">generator directory</a>).</li>
</ul>

<h2 id="sources">Source registry</h2>
<div class="table-scroll" role="region" aria-label="Source registry" tabindex="0"><table>
<thead><tr><th>ID</th><th>What it supports</th><th>Verification</th></tr></thead><tbody>
''')
for sid, title, url, status in SRC:
    status_label = {"yes":'<span class="badge b-ok">Fetched this session</span>',"repo":'<span class="badge b-flag">Repo ledger (prior session)</span>',"n/a":'<span class="badge b-anl">Internal — repo content</span>'}[status]
    p4.append(f'<tr><td><strong>{esc(sid)}</strong><br><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">open ↗</a></td><td>{esc(title)}</td><td>{status_label}</td></tr>\n')
p4.append('</tbody></table></div><p class="small">“Fetched this session” = the page/PDF was retrieved and read on 2026-11-08. “Repo ledger” = cited in the repository’s prior verified ledgers; not re-retrieved 2026-11-08; retained solely with its original label.</p>')
p4.append(foot())
(OUT / "verification.html").write_text("".join(p4), encoding="utf-8")

# ============================================================
# PAGE 5 — flagged-for-review.html (clearly labeled flags)
# ============================================================
p5 = []
p5.append(head("Flagged for Review", "Every unverified or unconfirmed item on this site, with links — review these before acting.", "flagged-for-review.html"))
p5.append(f"""<h1>Flagged for Review <span class="badge b-flag">Not verified — do not rely</span></h1>
<p class="lede">Every item this site could not confirm from an official source is listed here with the best source found and exactly what would close it. Cross-links to the other dashboards’ flagged pages are at the bottom. Nothing on this page is advice; blanks elsewhere on the site correspond to these entries.</p>
<div class="table-scroll" role="region" aria-label="Flagged items" tabindex="0"><table>
<thead><tr><th>ID</th><th>Item flagged</th><th>Why blank / what would close it</th><th>Best source found</th></tr></thead><tbody>
{flags_rows()}
</tbody></table></div>
<div class="card"><h3 style="margin-top:0">Related Flagged-for-Review pages (same repository, live)</h3><ul>
<li><a href="../docs/review.html">docs/review.html</a> — F01–F09 (research ledger, 2026-11-07)</li>
<li><a href="../site/flagged-for-review.html">site/flagged-for-review.html</a> — earlier session flags</li>
<li><a href="../portal/flagged-for-review.html">portal/flagged-for-review.html</a> — FLG-01–FLG-13 (session arena/85f37d08)</li>
<li><a href="../reports/REPO_LINE_BY_LINE_AUDIT.md">reports/REPO_LINE_BY_LINE_AUDIT.md</a> — repo audit R-01…</li>
</ul></div>
""")
p5.append(foot())
(OUT / "flagged-for-review.html").write_text("".join(p5), encoding="utf-8")
print("flagged-for-review.html", (OUT/"flagged-for-review.html").stat().st_size)

# ============================================================
# data.json — machine-readable model for parity checks
# ============================================================
import json
data = {
  "meta": {
    "title": "CNY→USD cost increments $10,000–$400,000",
    "generated": "2026-11-08",
    "generatedBy": "arena/8a2bd205-china2",
    "referenceRate": {"cnyPerUsd": RATE_CNY_PER_USD, "source": "Federal Reserve H.10, released 2026-11-02, noon buying rate 2026-10-30","url": "https://www.federalreserve.gov/releases/h10/current/", "note": "Reference for arithmetic parity only; not an executable customer quote."},
    "knownSubtotalDefinition": "HSBC China Tariff eff. 2026-10-31 items 2.2.4.1 (0.1% issuance, min CNY100 max CNY500) + 2.2.4.2 (CNY120 cable) + one US receiving fee (Chase published schedule example, $15; varies by account/bank). Excludes FX spread, intermediary deductions, Pay Exact (+CNY200).",
    "blankPolicy": "Unverifiable values are empty strings, never invented."
  },
  "increments": ROWS,
  "sources": [{"id": s[0], "label": s[1], "url": s[2], "verifiedThisSession": s[3]=="yes"} for s in SRC],
}
(OUT / "data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("verification.html", (OUT/"verification.html").stat().st_size)
print("data.json", (OUT/"data.json").stat().st_size)

print("BUILD OK — 5 pages + data.json")
