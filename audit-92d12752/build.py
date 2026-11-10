#!/usr/bin/env python3
"""Build a point-in-time audit of tracked HTML; excluded self to avoid recursion."""
import html
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from scan import scan

HERE = Path(__file__).resolve().parent
R = scan()
(HERE / 'results.json').write_text(json.dumps(R, ensure_ascii=False, indent=2) + '\n')
def e(s): return html.escape(str(s), quote=True)
items = []
for p in R['pages']:
    if p['without_direct_primary']:
        items.append('<li><a href="../'+e(p['path'])+'">'+e(p['path'])+'</a>: <strong>'+str(p['without_direct_primary'])+' of '+str(p['rows'])+'</strong> rows lack a direct allowlisted link. Example: '+e(p['first_example'])+'</li>')
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Flagged for review · direct-source audit</title><style>
*{box-sizing:border-box}body{font:16px/1.6 system-ui,sans-serif;color:#172640;background:#f4f7fa;margin:0}main{max-width:850px;margin:auto;padding:24px}h1,h2{line-height:1.2}a{color:#174e96;overflow-wrap:anywhere}.box{background:white;border:1px solid #dce4ec;border-radius:12px;padding:1.2rem;margin:1rem 0}.alert{border-left:5px solid #bd7620}li{margin:.75rem 0}code{overflow-wrap:anywhere}small{color:#4e6175}</style></head><body><main>
<p><a href="../index.html">← Dashboard</a> · <a href="../briefing/flagged.html">Existing flags</a> · <a href="../briefing/costs.html">Strict-blank cost tables</a></p>
<h1>Flagged for review: source links &amp; cost assumptions</h1><p>Independent targeted review · snapshot 10 November 2026. No account was accessed and no funds were transferred.</p>
<section class="box alert"><h2>Most important findings</h2><ol>
<li><strong>Unverified spread assumptions are displayed as numeric all-in estimates and rankings.</strong> The <a href="../ladder/costs.html">cost scenarios</a> and <a href="../ladder/ladder.html">40-tier ladder</a> disclose that they use modeled spreads, but showing assumed numeric ranges conflicts with the request to leave unverified values blank. They cannot identify the cheapest actual option. See <a href="../ladder/assumptions.html">assumptions</a> and <a href="../briefing/costs.html">the strict-blank alternative</a>. The bank's <a href="https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf">published tariff, important note 7</a>, excludes other institutions' charges and government taxes; it is not an all-in quote. <strong>Status: needs review.</strong></li>
<li><strong>Direct row-level source links are not universal.</strong> In particular, ladder cost and tax rows link to an internal source page rather than directly to the authority. This can help navigation but does not satisfy the literal request for an official-site link in every row. Some other rows have no source link at all. See the scoped inventory below. <strong>Status: needs review.</strong></li>
<li><strong>Personal tax and actual cost remain unknown.</strong> <a href="https://www.safe.gov.cn/tianjin/2026/0713/3088.html">SAFE Tianjin</a> says lawful current-account RMB income of overseas individuals can be converted at a bank with valid ID and source documentation including tax documents; that does not establish eligibility for every source of funds. <a href="https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates">IRS guidance</a> notes that foreign currency gains or losses may need recognition; its 2025 average of 7.129 is historical, not a live executable rate. <strong>Status: needs review.</strong></li>
<li><strong>Reporting is separate from tax.</strong> <a href="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar">IRS FBAR guidance</a> describes an aggregate foreign-account threshold exceeding $10,000 at any time in the year, subject to exceptions. That threshold is not a tax on transfers. <strong>Status: review individual filing history.</strong></li>
</ol></section>
<section class="box"><h2>What the static scan found</h2><p>Scanned <strong>__PAGES__ HTML pages</strong> and <strong>__ROWS__ data rows</strong>; <strong>__MISSING__ rows on __AFFECTED__ pages</strong> have no direct link to an allowlisted government, institutional or primary-provider domain in their own <code>&lt;tr&gt;</code>.</p>
<p>These are <em>review candidates</em>, not a count of unsupported facts. Internal links may lead to official sources on another page; some rows are repository inventories or unverified placeholders rather than claims needing a legal source. Conversely, a matching domain does not prove a link works, that the source supports the row, or that all cells are verified. Bank and provider websites are primary commercial sources, not government authorities.</p>
<p>The scan reads static <code>&lt;tr&gt;</code> elements containing <code>&lt;td&gt;</code>; it does not execute JavaScript, check CSV/JSON, follow indirect links, verify facts, or check remote link health. It excludes this audit's own folder, Git metadata, caches and dependencies. Results are a dated snapshot, not an ongoing certification. The finite host allowlist can miss other valid official domains.</p>
<details><summary>Pages with candidate rows (expand)</summary><ul>__ITEMS__</ul></details><p>Reproduce with <code>python3 audit-92d12752/scan.py</code>; <a href="results.json">download snapshot</a>. The first text snippet per page is a locator only.</p></section>
<section class="box"><h2>Next steps</h2><p>Ask the integration owner to replace unverified modeled values with blanks and direct-link each substantive row to its actual primary source, without implying that a link verifies every number. Review transaction-specific documentation, quotes and tax treatment with a qualified China/U.S. adviser. See the existing <a href="../briefing/methods.html">methods and steps</a> and <a href="../briefing/flagged.html">Flagged for Review</a>.</p><small>This review is structural and targeted, not legal advice or a line-by-line certification of the repository.</small></section>
</main></body></html>'''
for a,b in {'__PAGES__':R['pages_scanned'],'__ROWS__':R['data_rows'],'__MISSING__':R['without_direct_primary'],'__AFFECTED__':R['pages_with_candidates'],'__ITEMS__':'\n'.join(items)}.items(): page=page.replace(a,str(b))
(HERE / 'index.html').write_text(page, encoding='utf-8')
print('Snapshot:', R['pages_scanned'], 'pages,', R['data_rows'], 'rows,', R['without_direct_primary'], 'candidates on', R['pages_with_candidates'], 'pages')
