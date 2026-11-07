#!/usr/bin/env python3
"""Dependency-free, deterministic static dashboard generator."""
from pathlib import Path
import json, html, csv, io

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'
S=json.loads((ROOT/'research/sources.json').read_text())
ROWS=json.loads((ROOT/'research/findings.json').read_text())
SOURCES={s['id']:s for s in S}
esc=lambda x: html.escape(str(x), quote=True)
PAGES=[('index','Overview','01'),('routes','Transfer routes','02'),('costs','Costs & conversion','03'),('taxes','Tax & reporting','04'),('checklist','Execution checklist','05'),('review','Flagged for Review','06'),('sources','Source ledger','07')]

def refs(ids):
    return '<div class="refs">' + ''.join(f'<a class="source" href="{esc(SOURCES[i]["url"])}" target="_blank" rel="noopener noreferrer" title="{esc(SOURCES[i]["title"])}">{i} ↗</a>' for i in ids) + '</div>'

def badge(status):
    cls={'Source-backed':'backed','Analysis':'analysis','Unverified':'unverified','Needs review':'review','Do not use':'blocked'}[status]
    return f'<span class="badge {cls}">{esc(status)}</span>'

def table(rows, route=False, caption='Research findings'):
    heads=['Entry & status','Finding / scope'] + (['Pros · analysis','Cons / limitations · analysis'] if route else []) + ['Published figure / limit','Official evidence']
    body=''
    for r in rows:
        body+=f'<tr id="{esc(r["id"])}"><th scope="row"><span class="row-id">{r["id"]}</span>{esc(r["topic"])}{badge(r["status"])}</th><td>{esc(r["finding"])}'
        if not route:
            for label,k in [('Benefit','pros'),('Caution','cons')]:
                if r[k]: body+=f'<p class="detail"><strong>{label}:</strong> {esc(r[k])}</p>'
        body+='</td>'
        if route:
            body+=f'<td>{esc(r["pros"])}</td><td>{esc(r["cons"])}</td>'
        body+=(f'<td class="figure"'+(' aria-label="Unverified or not stated; intentionally blank"' if not r['value'] else '')+f'>{esc(r["value"])}</td>')
        body+=f'<td>{refs(r["sources"])}<small>{esc(r["locator"])}</small></td></tr>'
    return f'<div class="table-scroll" tabindex="0" role="region" aria-label="{esc(caption)}"><table><caption>{esc(caption)}</caption><thead><tr>'+''.join(f'<th scope="col">{h}</th>' for h in heads)+f'</tr></thead><tbody>{body}</tbody></table></div><p class="empty-state" hidden>No matching entries. Try a broader search or another status.</p>'

def toolbar():
    return '<div class="toolbar"><label class="search-label">Search this page<input id="search" type="search" placeholder="Search findings, requirements, sources…" autocomplete="off"></label><label>Status<select id="status"><option value="">All statuses</option>'+''.join(f'<option>{s}</option>' for s in ['Source-backed','Analysis','Unverified','Needs review','Do not use'])+'</select></label><span id="result-count" aria-live="polite"></span></div>'

summary='''<section class="recommendation"><div><span class="eyebrow">EXECUTIVE SUMMARY</span><h2>Start with the source of the money.<br>Not a workaround.</h2><p>For documented, lawful China employment income, the first route to assess is an authorized bank conversion and outward remittance. Compare Wise only if its salary/tax-record criteria fit; compare HSBC Global Transfer only if account eligibility fits.</p>'''+refs(['S03','S04','S05','S06'])+'''</div><div class="verdict"><span class="eyebrow">BOTTOM LINE · ANALYSIS</span><h3>A restriction is not a tax.</h3><p>Do not accept an unexplained “conversion penalty” as a single tax rate. Separate unpaid source tax, FX spread, wire costs, currency gains and any historical reporting penalties.</p>'''+refs(['S10','S07','S18','S14'])+'''<a class="text-link" href="costs.html">See the cost breakdown →</a></div></section>'''

summary_points=[
('Best first investigation','Documented bank remittance for lawful current-account RMB income. This is a conditional process recommendation, not a finding that this private balance qualifies.',['S03','S01']),
('The $50,000 misconception','Do not use USD50,000 as a universal foreign-salary ceiling or assume an ID-only allowance. The SAFE wording and HSBC guide differ; see F02.',['S02','S03','S04']),
('Minimize tax lawfully','Check source taxes already paid and U.S. foreign tax credit / earned-income-exclusion eligibility. These can address income tax, but cannot automatically waive bank fees or documentation.',['S10','S12','S13']),
('Do not manufacture a route','No friends’ quotas, fake contracts, underground swaps or crypto bridges are recommended. PBOC prohibits evasion by splitting/false vouchers; current crypto-business restrictions are explicit.',['S01','S23']),
('U.S. reporting remains separate','Worldwide taxable income, FBAR and possibly Form 8938 still matter even if funds stay in China. A small transfer or closed account does not erase an earlier balance trigger.',['S11','S14','S15']),
('What cannot be concluded','No verified personal balance, source dossier, charge explanation or executable quote exists here. Exact tax, net USD and cheapest provider remain blank; private compliance and state/third-country exposure remain unresolved.',['S03','S07','S11','S24'])]

OVERVIEW=summary+f'''<div class="metrics"><a href="routes.html"><strong>22</strong><span>Routes & alternatives assessed</span></a><a href="sources.html"><strong>{len(S)}</strong><span>Official primary sources</span></a><a href="review.html"><strong>9</strong><span>Open review flags</span></a></div><section class="panel"><div class="section-heading"><div><span class="eyebrow">THE DECISION BRIEF</span><h2>Important details, at a glance</h2></div><a class="button secondary" href="executive-summary.md" download>Download summary ↓</a></div><div class="table-scroll" tabindex="0" role="region" aria-label="Executive decision brief"><table><caption>Executive decision brief · recommendations are analysis</caption><thead><tr><th scope="col">Question</th><th scope="col">Conclusion / boundary</th><th scope="col">Official context</th></tr></thead><tbody>'''+''.join(f'<tr><th scope="row">{esc(t)}</th><td>{esc(b)}</td><td>{refs(ss)}</td></tr>' for t,b,ss in summary_points)+'''</tbody></table></div></section><section class="two-up"><a class="category-card" href="routes.html"><span class="eyebrow">COMPARE THE OPTIONS</span><h3>Find a route that matches the funds ↗</h3><p>Salary, property, inheritance, migration, refunds, cash and provider channels—without conflating their permissions.</p></a><a class="category-card" href="review.html"><span class="eyebrow">TRANSPARENT LIMITATIONS</span><h3>See what is not established ↗</h3><p>Source conflicts, missing private facts, unquoted costs, old statutory editions and questions for professional review.</p></a></section>'''

intro={
'routes':('Transfer routes','Match the legal route to the fund source, then choose a delivery channel. These entries are not 22 independent allowances. Pros and cons are analytical assessments; eligibility remains conditional.'),
'costs':('Costs & conversion','Break the apparent “penalty” into its real components. Blank published-figure cells mean unverified or not stated—not zero. No live exchange rate, fee quote or personal tax amount is invented.'),
'taxes':('Tax & reporting','Chinese source-income tax and U.S. tax/reporting are separate from bank conversion. Figures below are source-described rules, not personalized tax calculations. Check the applicable tax year and eligibility.'),
'checklist':('Execution checklist','A complete delegated workflow for a bank or qualified cross-border adviser. This research does not require more input from you; actual execution still requires private evidence, consent and institution acceptance.'),
'review':('Flagged for Review','Published uncertainties do not block the site. The links below verify the regulatory context—not the missing personal facts. No unknown value is represented as confirmed.'),
'sources':('Source ledger','Official government/regulator pages and providers’ own documentation only. Retrieved and reviewed on 7 November 2026. Every finding links directly to primary evidence; bank policies are not treated as law.')}

def shell(page, title, description, content):
    nav=''.join(f'<a href="{p}.html"'+(' aria-current="page"' if p==page else '')+f'><span>{n}</span>{esc(t)}'+('<i>9</i>' if p=='review' else '')+'</a>' for p,t,n in PAGES)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{esc(description)}"><meta name="theme-color" content="#102d35"><title>{esc(title)} · China Money</title><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/style.css"><script src="assets/app.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a><aside class="sidebar"><a class="brand" href="index.html"><span class="brand-mark">¥<small>$</small></span><span>China Money<small>RESEARCH DESK</small></span></a><div class="nav-label">RESEARCH NAVIGATION</div><nav aria-label="Main navigation">{nav}</nav><div class="sidebar-bottom"><span class="live-dot"></span> Evidence-first research<p>Mainland CNY → USD<br>U.S. citizen perspective</p><a href="https://github.com/sassnarep3-star/China2">View repository ↗</a></div></aside><div class="workspace"><header class="topbar"><span>RESEARCH / <strong>{esc(title)}</strong></span><span class="date">REVIEWED <time datetime="2026-11-07">07 NOV 2026</time></span></header><main id="main"><div class="page-heading"><div><span class="eyebrow">CROSS-BORDER MONEY · MAINLAND CHINA / UNITED STATES</span><h1>{esc(title)}</h1><p>{esc(description)}</p></div><button class="button secondary print" type="button">Print / save PDF</button></div><div class="notice"><strong>Research, not a tax opinion.</strong> No personal eligibility or lowest-cost outcome is certified. No transfers or tax filings have been made. <a href="review.html">Read the limitations →</a></div>{content}<footer><strong>China Money / Research Desk</strong><p>Primary-source review as of 7 November 2026. Policies and quotes can change. English summaries of Chinese text are working translations.</p><p>Source-backed = the stated rule was found in the cited material, not proof it applies to you. Analysis = recommendation or derived formula. Blank numerical cells = not confirmed or not stated. Provider documentation describes that provider only.</p><a href="sources.html">Evidence & methodology</a> · <a href="findings.csv" download>Download findings CSV</a> · <a href="data/sources.json" download>Download source ledger</a></footer></main></div></body></html>'''

OUT.mkdir(exist_ok=True)
(OUT/'data').mkdir(exist_ok=True)
for name in ['sources','findings']:
    (OUT/f'data/{name}.json').write_text((ROOT/f'research/{name}.json').read_text())
(OUT/'index.html').write_text(shell('index','Move money with clarity.','A source-linked decision dashboard for getting lawful funds out of mainland China—separating conversion costs, tax obligations and transfer restrictions.',OVERVIEW))
for page,title,num in PAGES[1:]:
    desc=intro[page][1]
    if page=='sources':
        content='''<section class="panel methodology"><h2>How this was verified</h2><p>Each published research row was compared with the cited official page body or specified PDF sections. The ledger records the authority, relevant passage, review date and limitation. Search results were discovery aids, not final evidence. No current price is inferred from a marketing example.</p><p>“Official” includes a bank or provider speaking about its own product; this is primary product evidence, not government endorsement. Review flags distinguish source conflicts, incomplete legal currency checks and unknown private facts. Citation coverage tests are structural checks—not an independent legal audit.</p><p>Outbound browsing through the shell is restricted in this environment. Official-page retrieval used the research fetch tool. Local/CI checks validate internal links and citation presence; external site availability is not continuously guaranteed.</p></section>'''+toolbar()
        body=''
        for s in S:
            body+=f'<tr id="{s["id"]}"><th scope="row"><span class="row-id">{s["id"]}</span>{esc(s["title"])}<small>{esc(s["authority"])}</small></th><td><strong>{esc(s["locator"])}</strong><p>{esc(s["evidence"])}</p></td><td>{esc(s["limitation"])}</td><td>{esc(s["published"])}<small>Reviewed {s["accessed"]}<br>{esc(s["method"])}</small></td><td>{refs([s["id"]])}</td></tr>'
        content+='<div class="table-scroll" tabindex="0" role="region" aria-label="Source ledger"><table><caption>Primary-source evidence ledger</caption><thead><tr><th scope="col">Source / authority</th><th scope="col">Passage / evidence reviewed</th><th scope="col">Limitations</th><th scope="col">Dates / method</th><th scope="col">Official link</th></tr></thead><tbody>'+body+'</tbody></table></div><p class="empty-state" hidden>No matching sources.</p>'
    else:
        content=''
        if page=='routes': content+='<div class="context-strip"><strong>Read in layers</strong><span>Legal basis → documentation → bank/provider channel → all-in USD proceeds</span></div>'
        if page=='costs': content+='<section class="panel formula"><span class="eyebrow">NO ASSUMED NUMBERS</span><h2>Tax ≠ spread ≠ fee ≠ penalty</h2><p>Do not apply Chinese income-tax rates to the entire account balance. Do not count taxes already paid as a new conversion cost. Do not treat a reporting threshold as an allowance to evade reporting.</p>'+refs(['S10','S14','S07'])+'</section>'
        if page=='review': content+='<p class="review-banner">Open review items are intentionally published. Values that cannot be confirmed remain empty. The research can be complete while your personal eligibility remains unverified.</p>'
        content+=toolbar()+table([r for r in ROWS if r['category']==page],page=='routes',title+' · source-linked findings')
    (OUT/f'{page}.html').write_text(shell(page,title,desc,content))
# Portable artifacts are generated from the same evidence used on the site.
summary_md='# China Money — Executive Summary\n\nResearch reviewed: 7 November 2026. Not individualized legal, tax or investment advice.\n\n'
for title,body,ids in summary_points:
    summary_md+=f'## {title}\n\n{body}\n\n'+', '.join(f'[{i}: {SOURCES[i]["authority"]}]({SOURCES[i]["url"]})' for i in ids)+'\n\n'
summary_md+='## Execution boundary\n\nNo transfer or tax filing has been made. The bank/adviser must establish ownership, source, years, paid taxes, approval requirements, personal compliance history and live quotes privately. No passports or account numbers belong in this public repository.\n'
(OUT/'executive-summary.md').write_text(summary_md)
(ROOT/'research/EXECUTIVE_SUMMARY.md').write_text(summary_md)
buf=io.StringIO(newline='')
fields=['id','category','topic','finding','status','value','pros','cons','locator','official_sources']
w=csv.DictWriter(buf,fieldnames=fields,lineterminator="\n");w.writeheader()
for r in ROWS:
    item={k:r[k] for k in fields if k!='official_sources'}
    item['official_sources']=' | '.join(SOURCES[i]['url'] for i in r['sources']);w.writerow(item)
(OUT/'findings.csv').write_text(buf.getvalue())
(OUT/'.nojekyll').touch()
print(f'Built {len(PAGES)} pages, {len(ROWS)} research rows and {len(S)} sources.')
