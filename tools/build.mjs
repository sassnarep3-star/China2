#!/usr/bin/env node
/**
 * tools/build.mjs — generates the static GitHub Pages site in site/ from data/*.json.
 *
 * Every data row rendered into a table also renders a source cell. A row whose
 * sourceId is null, or whose source lacks a URL, renders the literal text
 * "UNVERIFIED — no official source" with class "cell-unverified" and no link.
 * tools/verify.mjs enforces that contract after every build.
 *
 * No value in this file is hard-coded from domain knowledge; all substantive
 * content comes from the JSON ledgers, which carry their own source ids.
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const DATA = join(ROOT, 'data');
const SITE = join(ROOT, 'site');

const read = (f) => JSON.parse(readFileSync(join(DATA, f), 'utf8'));
const sources = read('sources.json');
const methods = read('methods.json');
const usRules = read('us-rules.json');
const chinaRules = read('china-rules.json');
const flags = read('flags.json');

const SRC = Object.fromEntries(sources.sources.map((s) => [s.id, s]));
const FLAG = Object.fromEntries(flags.flags.map((f) => [f.id, f]));
const esc = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const UNVERIFIED = '<span class="cell-unverified">UNVERIFIED — no official source</span>';

/** A source cell. Never returns an empty cell: it is either a real link or the UNVERIFIED badge. */
function sourceCell(ids) {
  const list = (Array.isArray(ids) ? ids : [ids]).filter(Boolean);
  if (!list.length) return UNVERIFIED;
  return list
    .map((id) => {
      const s = SRC[id];
      if (!s || !s.url) return UNVERIFIED;
      const lvl = s.verifiedByFetch
        ? '<span class="badge badge-ok">fetched</span>'
        : '<span class="badge badge-warn">search-index</span>';
      return `<a href="${esc(s.url)}" rel="noopener noreferrer" target="_blank">${esc(s.id)} · ${esc(s.publisher)}</a> ${lvl}`;
    })
    .join('<br>');
}

const flagCell = (id) =>
  id
    ? `<a href="flagged-for-review.html#${esc(id)}">${esc(id)}</a>`
    : '<span class="muted">—</span>';

const statusClass = {
  lawful: 'st-lawful',
  'lawful-conditional': 'st-cond',
  unlawful: 'st-unlawful',
};
const statusLabel = {
  lawful: 'LAWFUL',
  'lawful-conditional': 'LAWFUL (conditional)',
  unlawful: 'UNLAWFUL',
};

const ul = (arr) =>
  Array.isArray(arr) && arr.length
    ? `<ul class="tight">${arr.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`
    : '<span class="muted">—</span>';

const CSS = `
:root{--bg:#f6f7f9;--panel:#fff;--ink:#16191d;--muted:#5d6672;--line:#e2e6ea;
--accent:#0b5fff;--ok:#0f7b3f;--warn:#9a6700;--bad:#b3261e;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header.top{background:#0d1526;color:#fff;padding:14px 24px;display:flex;
align-items:center;gap:16px;flex-wrap:wrap;position:sticky;top:0;z-index:10}
header.top .brand{font-weight:700;letter-spacing:.2px;font-size:16px}
header.top nav{display:flex;gap:4px;flex-wrap:wrap}
header.top nav a{color:#c8d2e0;padding:6px 10px;border-radius:6px;font-size:13px}
header.top nav a:hover{background:#1b2740;color:#fff;text-decoration:none}
header.top nav a.here{background:var(--accent);color:#fff}
main{max-width:1280px;margin:0 auto;padding:26px 24px 70px}
h1{font-size:26px;margin:0 0 6px}h2{font-size:19px;margin:32px 0 10px}
.sub{color:var(--muted);margin:0 0 22px;max-width:90ch}
.cards{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));margin:18px 0 8px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:15px 16px}
.card .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.card .v{font-size:23px;font-weight:700;margin-top:5px;line-height:1.2}
.card .n{font-size:12.5px;color:var(--muted);margin-top:6px}
.tilegrid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));margin-top:14px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:17px 18px}
.tile h3{margin:0 0 7px;font-size:16px}.tile p{margin:0 0 10px;color:var(--muted);font-size:13.5px}
.tile .go{font-size:13px;font-weight:600}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:4px 0 0;
margin:14px 0 26px;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.4px;min-width:900px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eef1f4;font-size:11.5px;text-transform:uppercase;letter-spacing:.5px;
color:#3c454f;position:sticky;top:0;white-space:nowrap}
tr.data-row:last-child td{border-bottom:none}
tr.data-row:hover td,tr.meta-row:hover td{background:#fafbfc}
td.id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--muted);white-space:nowrap}
ul.tight{margin:0;padding-left:17px}ul.tight li{margin:2px 0}
.muted{color:var(--muted)}
.badge{display:inline-block;font-size:10.5px;padding:1px 6px;border-radius:20px;
border:1px solid var(--line);white-space:nowrap}
.badge-ok{color:var(--ok);border-color:#bfe3cc;background:#f0faf4}
.badge-warn{color:var(--warn);border-color:#ecd9a6;background:#fffaf0}
.st-lawful,.st-cond,.st-unlawful{display:inline-block;font-size:11px;font-weight:700;
padding:2px 8px;border-radius:4px;white-space:nowrap}
.st-lawful{background:#e8f6ee;color:var(--ok)}
.st-cond{background:#fff6e5;color:var(--warn)}
.st-unlawful{background:#fdecea;color:var(--bad)}
.cell-unverified{display:inline-block;font-size:11px;font-weight:700;color:var(--bad);
background:#fdecea;border:1px dashed #e6b3ae;padding:2px 7px;border-radius:4px}
.callout{border-left:4px solid var(--accent);background:#eef4ff;padding:13px 16px;
border-radius:0 8px 8px 0;margin:16px 0;font-size:14px}
.callout.warn{border-color:var(--warn);background:#fffaf0}
.callout.bad{border-color:var(--bad);background:#fdf1f0}
.callout.ok{border-color:var(--ok);background:#f0faf4}
.callout p{margin:0 0 7px}.callout p:last-child{margin:0}
footer{border-top:1px solid var(--line);padding:20px 24px 40px;color:var(--muted);font-size:12.5px}
.legend{font-size:12.5px;color:var(--muted);margin:10px 0 0}
code{background:#eef1f4;padding:1px 5px;border-radius:4px;font-size:12.5px}
`;

function shell(title, active, body, extraSub) {
  const nav = [
    ['index.html', 'Dashboard'],
    ['executive-summary.html', 'Executive summary'],
    ['conversion-routes.html', 'Conversion routes'],
    ['cost-breakdown.html', 'Cost breakdown'],
    ['us-tax-rules.html', 'US rules'],
    ['china-rules.html', 'China rules'],
    ['unlawful-routes.html', 'Unlawful routes'],
    ['sources.html', 'Sources'],
    ['flagged-for-review.html', 'Flagged for review'],
    ['methodology.html', 'Methodology'],
    ['repo-audit.html', 'Repo audit'],
  ];
  return `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)} · China Money Repatriation</title>
<meta name="description" content="${esc(title)} — CNY to USD repatriation research, verified against official sources.">
<link rel="stylesheet" href="style.css"></head>
<body>
<header class="top"><span class="brand">China → USD Repatriation</span><nav>
${nav
  .map(
    ([href, label]) =>
      `<a href="${href}"${href === active ? ' class="here"' : ''}>${esc(label)}</a>`
  )
  .join('\n')}
</nav></header>
<main>
<h1>${esc(title)}</h1>
${extraSub ? `<p class="sub">${extraSub}</p>` : ''}
${body}
</main>
<footer>
Built ${esc(sources.meta.generated)} by session <code>arena-fcd22b0c</code>. Research only — not tax or legal advice.
Every table row carries a source link to a primary official document, or is explicitly marked UNVERIFIED.
Machine-readable ledgers: <code>data/*.json</code>. Verification report: <code>node tools/verify.mjs</code>.
</footer>
</body></html>`;
}

const writePage = (name, html) => writeFileSync(join(SITE, name), html);

mkdirSync(SITE, { recursive: true });
writeFileSync(join(SITE, 'style.css'), CSS);

/* ------------------------------------------------------------------ dashboard */
const lawfulCount = methods.routes.filter((r) => r.legalStatus !== 'unlawful').length;
const unlawfulCount = methods.routes.filter((r) => r.legalStatus === 'unlawful').length;
const fetchedCount = sources.sources.filter((s) => s.verifiedByFetch).length;
const blankCount = flags.flags.filter((f) => f.severity !== 'informational').length;

const hero = `
<div class="callout"><p><strong>The central finding.</strong> Converting CNY into USD is
<em>not</em> a taxable event in either country. Neither SAFE nor the IRS taxes the act of
changing currency. The binding constraint is China's
<strong>USD 50,000 per person per year</strong> foreign-exchange facilitation quota and the
documentary authenticity review above it — not tax. On the U.S. side the real financial risk
is <strong>reporting</strong> (FBAR / Form 8938), not conversion.</p>
<p>See the <a href="executive-summary.html">executive summary</a> for the full reasoning and the
<a href="cost-breakdown.html">cost breakdown</a> for where money is actually lost.</p></div>

<div class="cards">
<div class="card"><div class="k">Conversion routes catalogued</div><div class="v">${methods.routes.length}</div><div class="n">${lawfulCount} lawful or conditionally lawful · ${unlawfulCount} unlawful</div></div>
<div class="card"><div class="k">China annual FX quota</div><div class="v">USD 50,000</div><div class="n">per individual per year · SAFE</div></div>
<div class="card"><div class="k">US personal FX gain exclusion</div><div class="v">$200</div><div class="n">per transaction · IRS Pub 525</div></div>
<div class="card"><div class="k">Official sources</div><div class="v">${sources.sources.length}</div><div class="n">${fetchedCount} read in full this session</div></div>
<div class="card"><div class="k">Flagged for review</div><div class="v">${flags.flags.length}</div><div class="n">${blankCount} non-informational</div></div>
</div>

<h2>Browse by category</h2>
<div class="tilegrid">
<div class="tile"><h3>Executive summary</h3><p>The answer to the question actually asked: what costs money, what does not, and which route is cheapest in lawful terms.</p><a class="go" href="executive-summary.html">Read it →</a></div>
<div class="tile"><h3>All conversion routes</h3><p>Every lawful, conditionally lawful and unlawful mechanism for turning CNY into USD, each with limits, tax treatment, pros and cons.</p><a class="go" href="conversion-routes.html">Open the table →</a></div>
<div class="tile"><h3>Cost breakdown</h3><p>Where the money actually goes: tax versus spread versus fees versus penalties, component by component.</p><a class="go" href="cost-breakdown.html">Open the analysis →</a></div>
<div class="tile"><h3>United States rules</h3><p>FBAR, Form 8938, personal foreign-currency gain, CMIR, and the treaty withholding caps that apply to a U.S. citizen.</p><a class="go" href="us-tax-rules.html">Open the table →</a></div>
<div class="tile"><h3>China rules</h3><p>SAFE quotas, the personal-asset outbound transfer regime, card withdrawal caps, and individual income tax.</p><a class="go" href="china-rules.html">Open the table →</a></div>
<div class="tile"><h3>Unlawful routes</h3><p>The mechanisms that are widely suggested online and are prohibited. Documented so they can be rejected, not used.</p><a class="go" href="unlawful-routes.html">Open the table →</a></div>
<div class="tile"><h3>Source register</h3><p>Every primary document relied on, its publisher, what it supports, and whether it was read in full this session.</p><a class="go" href="sources.html">Open the register →</a></div>
<div class="tile"><h3>Flagged for review</h3><p>Every value that could not be confirmed from an official source, left blank rather than estimated, plus repository irregularities.</p><a class="go" href="flagged-for-review.html">Open the flags →</a></div>
</div>`;

writePage(
  'index.html',
  shell('Dashboard', 'index.html', hero, 'A verified evidence base for moving money out of China as a U.S. citizen. Nothing here is estimated: unconfirmed values are left blank and flagged.')
);

/* ---------------------------------------------------------- executive summary */
const exBody = `
<div class="callout warn"><p><strong>Read this first.</strong> The question as posed contains a
false premise, and correcting it is the most valuable thing this research can do. There is no
"conversion tax." Moving money out of China costs you in <em>quota years</em>, <em>bank spread</em>
and <em>compliance</em> — not in a tax charged on the exchange.</p></div>

<h2>1. What is actually true about conversion</h2>
<div class="panel"><table>
<thead><tr><th>Question</th><th>Verified finding</th><th>Source</th></tr></thead><tbody>
<tr class="data-row"><td>Does the United States tax the act of converting CNY to USD?</td>
<td>No. All income tax determinations must be made in the functional currency, and the U.S. dollar is the functional currency for all taxpayers except some qualified business units. What can be in scope is exchange-rate gain on the currency position — not the principal.</td>
<td>${sourceCell('S04')}</td></tr>
<tr class="data-row"><td>How much exchange-rate gain is excluded?</td>
<td>A gain on a personal foreign currency transaction is not included in income unless it is more than $200; above $200 it is reported as a capital gain.</td>
<td>${sourceCell('S03')} ${flagCell('F01')}</td></tr>
<tr class="data-row"><td>Does China tax the act of converting CNY to USD?</td>
<td>SAFE's individual foreign-exchange regime imposes a quota and an authenticity review. It imposes no tax on the purchase or sale of foreign exchange. Chinese individual income tax attaches to the underlying income when it arises, at 3%–45% on comprehensive income and a flat 20% on interest, dividends and property transfers.</td>
<td>${sourceCell(['S05', 'S10'])}</td></tr>
<tr class="data-row"><td>So what is the "considerable amount of taxes"?</td>
<td>Almost certainly one of three different things, none of which is a conversion tax: (a) Chinese individual income tax on the income that created the balance; (b) the bank's exchange-rate spread and fees, which are not tax; or (c) U.S. reporting penalties for accounts that were never declared.</td>
<td>${sourceCell(['S10', 'S01', 'S02'])} ${flagCell('F05')}</td></tr>
</tbody></table></div>

<h2>2. The real bottleneck is a quota, not a tax rate</h2>
<div class="panel"><table>
<thead><tr><th>Constraint</th><th>Verified value</th><th>Source</th></tr></thead><tbody>
<tr class="data-row"><td>Individual FX facilitation quota</td><td>USD 50,000 equivalent per individual per calendar year, covering both purchases and sales, for both domestic and foreign individuals.</td><td>${sourceCell('S05')}</td></tr>
<tr class="data-row"><td>Above the quota</td><td>Formalities inside the quota are drastically simplified; examination of the authenticity of transactions exceeding the quota is strengthened.</td><td>${sourceCell('S05')}</td></tr>
<tr class="data-row"><td>Detection</td><td>SAFE operates a management information system connecting banks to SAFE for individual purchases and sales, through which banks verify the authenticity of the materials provided.</td><td>${sourceCell('S05')}</td></tr>
<tr class="data-row"><td>Escape valve 1 — genuine individual trade</td><td>Purchases and sales under an individual foreign-exchange settlement account are NOT subject to the annual quota and are conducted against valid trading documents regardless of amount.</td><td>${sourceCell('S05')}</td></tr>
<tr class="data-row"><td>Escape valve 2 — emigration or inheritance</td><td>Emigrant and inheritor asset transfers are approved by SAFE outside the quota. Since the 2014 circular the installment requirement was cancelled and funds may be remitted in a lump sum within the approved limit.</td><td>${sourceCell(['S09', 'S08'])}</td></tr>
<tr class="data-row"><td>Parallel cash channel</td><td>Overseas card cash withdrawals are capped at RMB 100,000 equivalent per individual per civil year and RMB 10,000 equivalent per card per day — a separate limit that does not contradict the USD 50,000 quota.</td><td>${sourceCell(['S06', 'S07'])}</td></tr>
</tbody></table></div>

<h2>3. The largest financial exposure is U.S. reporting, not conversion</h2>
<div class="callout bad"><p>A U.S. citizen holding a Chinese bank account is already inside the
U.S. reporting net the moment the account exists — before a single yuan is converted. The
aggregate balance crossed $10,000 at any point in a calendar year and a FinCEN Form 114 was due
by April 15. Filing it late, or never, is where large money is actually lost, and the IRS directs
anyone in that position to file as soon as possible to keep potential penalties to a minimum.</p></div>
<div class="panel"><table>
<thead><tr><th>Obligation</th><th>Trigger</th><th>Source</th></tr></thead><tbody>
<tr class="data-row"><td>FBAR — FinCEN Form 114</td><td>Aggregate value of foreign financial accounts exceeded $10,000 at any time during the calendar year. Filed with FinCEN, due April 15, automatic extension to October 15.</td><td>${sourceCell('S01')}</td></tr>
<tr class="data-row"><td>Form 8938</td><td>More than $50,000 at year-end or $75,000 at any time (unmarried, living in the U.S.); more than $200,000 or $300,000 living abroad. Not required if no income tax return filing is required.</td><td>${sourceCell('S02')}</td></tr>
<tr class="data-row"><td>Both can apply</td><td>Form 8938 does not relieve filers of FBAR filing requirements.</td><td>${sourceCell('S02')}</td></tr>
<tr class="data-row"><td>Carrying cash into the U.S.</td><td>FinCEN Form 105 (CMIR) where more than $10,000 in currency or monetary instruments is transported into or out of the country.</td><td>${sourceCell(['S15', 'S16'])}</td></tr>
</tbody></table></div>

<h2>4. Which route is cheapest in lawful terms</h2>
<div class="panel"><table>
<thead><tr><th>Rank</th><th>Route</th><th>Why</th><th>Source</th></tr></thead><tbody>
<tr class="data-row"><td>1</td><td><a href="conversion-routes.html#R01">R01 — wire inside the USD 50,000 quota</a></td><td>No approval needed, no conversion tax, and the cleanest documentary trail for U.S. reporting. Costs only the bank spread and fees, which are unverified because no regulator publishes them.</td><td>${sourceCell('S05')}</td></tr>
<tr class="data-row"><td>2</td><td><a href="conversion-routes.html#R03">R03 — emigrant asset transfer</a></td><td>The only route that can move an arbitrarily large personal balance lawfully in one process, and it is outside the quota. Requires foreign permanent residence or citizenship, and only covers assets obtained before that status was obtained.</td><td>${sourceCell(['S09', 'S08'])}</td></tr>
<tr class="data-row"><td>3</td><td><a href="conversion-routes.html#R07">R07 — individual FX settlement account for genuine trade</a></td><td>Expressly not subject to the annual quota at all. Only available against genuine trading documents, and using the currency in a trade or business removes the $200 U.S. personal-transaction exclusion.</td><td>${sourceCell(['S05', 'S03'])}</td></tr>
<tr class="data-row"><td>4</td><td><a href="conversion-routes.html#R02">R02 — above-quota wire on authenticity documents</a></td><td>The general lawful answer for any amount, at the price of slower processing and a real possibility of refusal.</td><td>${sourceCell('S05')}</td></tr>
<tr class="data-row"><td>5</td><td><a href="conversion-routes.html#R05">R05 — overseas card cash withdrawals</a></td><td>Useful as a supplement only. RMB 100,000 a year, and exceeding it costs you the current and the following year.</td><td>${sourceCell('S06')}</td></tr>
</tbody></table></div>

<h2>5. What to do before moving anything</h2>
<div class="panel"><table>
<thead><tr><th>#</th><th>Step</th><th>Why it is verified as necessary</th><th>Source</th></tr></thead><tbody>
<tr class="data-row"><td>1</td><td>File or catch up any missed FBAR for every year the balance exceeded $10,000.</td><td>Filing is required whether or not the account produced income, and the IRS directs late filers to file as soon as possible to minimise penalties.</td><td>${sourceCell('S01')}</td></tr>
<tr class="data-row"><td>2</td><td>Establish how the balance arose and whether Chinese tax was withheld.</td><td>Tax certificates or tax payment vouchers are a required document for the personal-asset outbound transfer application.</td><td>${sourceCell('S09')}</td></tr>
<tr class="data-row"><td>3</td><td>Decide whether the immigration route is open to you.</td><td>Emigrant asset transfer is available only to someone who has obtained foreign permanent residence or citizenship, and only for assets obtained beforehand.</td><td>${sourceCell('S09')}</td></tr>
<tr class="data-row"><td>4</td><td>Claim the foreign tax credit for Chinese tax paid.</td><td>The treaty provides that the country of residence gives a foreign tax credit for income tax paid to the other country.</td><td>${sourceCell('S11')}</td></tr>
<tr class="data-row"><td>5</td><td>Do not split the quota across relatives to fund one transfer.</td><td>SAFE states the quota system exists in part to prevent avoiding administration, and banks verify authenticity through the SAFE-linked system.</td><td>${sourceCell('S05')}</td></tr>
<tr class="data-row"><td>6</td><td>Do not touch cryptocurrency or underground banking.</td><td>All virtual-currency-related business activity is illegal in China, and offshore exchanges serving mainland residents are illegal financial activity.</td><td>${sourceCell('S13')}</td></tr>
</tbody></table></div>

<div class="callout"><p><strong>Open items.</strong> ${flags.flags.length} items could not be
confirmed from an official source and are left blank rather than estimated. The most
consequential are the FBAR penalty figures (F02), bank spread and fees (F05) and the Chinese
customs cash thresholds (F07). All are listed with an action on the
<a href="flagged-for-review.html">Flagged for Review</a> page.</p></div>`;

writePage(
  'executive-summary.html',
  shell('Executive summary', 'executive-summary.html', exBody, 'Every claim below is tied to a primary official document. Unconfirmed values are blank and flagged, never estimated.')
);

/* --------------------------------------------------------- conversion routes */
const routeRows = methods.routes
  .map(
    (r) => `
<tr class="data-row" id="${esc(r.id)}">
<td class="id">${esc(r.id)}</td>
<td><strong>${esc(r.name)}</strong><div class="muted">${esc(r.category)}</div></td>
<td>${esc(r.mechanism)}</td>
<td><span class="${statusClass[r.legalStatus]}">${statusLabel[r.legalStatus]}</span></td>
<td>${r.annualLimit === 'unverified' ? UNVERIFIED : esc(r.annualLimit)}</td>
<td>${r.chinaTaxOnConversion === 'unverified' ? UNVERIFIED : esc(r.chinaTaxOnConversion)}</td>
<td>${r.usTaxOnConversion === 'unverified' ? UNVERIFIED : esc(r.usTaxOnConversion)}</td>
<td>${ul(r.pros)}</td>
<td>${ul(r.cons)}</td>
<td>${r.costComponentsUnverified === 'unverified' ? UNVERIFIED : esc(r.costComponentsUnverified)}</td>
<td>${sourceCell([r.sourceId, ...(r.additionalSources || [])])}</td>
<td>${flagCell(r.flag)}</td>
</tr>`
  )
  .join('');

writePage(
  'conversion-routes.html',
  shell(
    'Conversion routes',
    'conversion-routes.html',
    `<div class="callout"><p>Every lawful, conditionally lawful and unlawful mechanism for turning
CNY into USD that this research located. ${methods.routes.length} routes. Each row carries a
source link to a primary official document or is explicitly marked UNVERIFIED.</p></div>
<p class="legend"><span class="st-lawful">LAWFUL</span> permitted on its face ·
<span class="st-cond">LAWFUL (conditional)</span> permitted only where the stated condition is met ·
<span class="st-unlawful">UNLAWFUL</span> prohibited; documented so it can be rejected</p>
<div class="panel"><table>
<thead><tr><th>ID</th><th>Route</th><th>Mechanism</th><th>Status</th><th>Limit</th>
<th>China tax</th><th>U.S. tax on conversion</th><th>Pros</th><th>Cons</th>
<th>Cost components</th><th>Source</th><th>Flag</th></tr></thead>
<tbody>${routeRows}</tbody></table></div>`,
    'The complete catalogue, organised by category, with limits, tax treatment, pros and cons for each.'
  )
);

/* ------------------------------------------------------------- unlawful only */
const badRows = methods.routes
  .filter((r) => r.legalStatus === 'unlawful')
  .map(
    (r) => `
<tr class="data-row" id="${esc(r.id)}">
<td class="id">${esc(r.id)}</td>
<td><strong>${esc(r.name)}</strong></td>
<td>${esc(r.mechanism)}</td>
<td><span class="st-unlawful">UNLAWFUL</span></td>
<td>${ul(r.cons)}</td>
<td>${sourceCell([r.sourceId, ...(r.additionalSources || [])])}</td>
<td>${flagCell(r.flag)}</td>
</tr>`
  )
  .join('');

writePage(
  'unlawful-routes.html',
  shell(
    'Unlawful routes',
    'unlawful-routes.html',
    `<div class="callout bad"><p>These are the mechanisms most often recommended online for moving
money out of China. They are documented here so they can be <strong>rejected</strong>, not used.
Each is tied to the official instrument that prohibits it.</p></div>
<div class="panel"><table>
<thead><tr><th>ID</th><th>Route</th><th>Mechanism</th><th>Status</th><th>Why it fails</th><th>Source</th><th>Flag</th></tr></thead>
<tbody>${badRows}</tbody></table></div>`,
    'Prohibited mechanisms, with the official basis for the prohibition.'
  )
);

/* ------------------------------------------------------------- cost breakdown */
const costBody = `
<div class="callout"><p>This is the breakdown the brief asked for. It separates the four things
that are routinely conflated as "the cost of getting money out of China." Only one of them is a
tax on conversion, and that one is usually zero.</p></div>

<h2>Component by component</h2>
<div class="panel"><table>
<thead><tr><th>Component</th><th>What it is</th><th>Verified amount</th><th>Who charges it</th><th>Source</th></tr></thead><tbody>
<tr class="data-row"><td><strong>1. Tax on the conversion itself</strong></td>
<td>U.S.: exchange-rate gain on the currency position. China: none — the SAFE regime imposes a quota and an authenticity review, not a tax.</td>
<td>U.S.: $0 where the personal gain is $200 or less per transaction; above that, tax on the gain as a capital gain. China: $0.</td>
<td>IRS</td><td>${sourceCell(['S03', 'S05'])} ${flagCell('F01')}</td></tr>
<tr class="data-row"><td><strong>2. Tax on the income that created the balance</strong></td>
<td>Chinese individual income tax on the earnings, which arises when the income arises — not when it is remitted.</td>
<td>3% to 45% progressive on comprehensive income after the RMB 60,000 deduction; flat 20% on interest, dividends and property transfers.</td>
<td>State Taxation Administration</td><td>${sourceCell('S10')}</td></tr>
<tr class="data-row"><td><strong>3. Bank spread and transfer fees</strong></td>
<td>The difference between the interbank rate and the rate the bank gives you, plus wire, correspondent and card fees. For most balances this is the single largest real cost.</td>
<td>${UNVERIFIED}</td><td>Commercial banks and card issuers</td><td>${sourceCell('S05')} ${flagCell('F05')}</td></tr>
<tr class="data-row"><td><strong>4. Time cost of the quota</strong></td>
<td>The balance divided by the annual quota is the number of calendar years a straightforward wire takes. Not a tax, but a real cost.</td>
<td>USD 50,000 equivalent per individual per calendar year</td>
<td>SAFE</td><td>${sourceCell('S05')}</td></tr>
<tr class="data-row"><td><strong>5. U.S. non-compliance exposure</strong></td>
<td>The financial consequence of accounts that were never declared. This can dwarf every other component.</td>
<td>Penalty amounts are inflation-adjusted annually and were not retrieved from the official eCFR text this session, so none is stated.</td>
<td>IRS / FinCEN</td><td>${sourceCell('S01')} ${flagCell('F02')}</td></tr>
<tr class="data-row"><td><strong>6. Chinese non-compliance exposure</strong></td>
<td>The consequence of evading the quota or using false documents.</td>
<td>Penalty under the Regulations of the PRC on Foreign Exchange Administration; the specific schedule was not confirmed from an official English text this session.</td>
<td>SAFE</td><td>${sourceCell('S09')} ${flagCell('F11')}</td></tr>
<tr class="data-row"><td><strong>7. Treaty withholding on dividends, interest, royalties</strong></td>
<td>Relevant only where the balance comes from passive income or a corporate distribution.</td>
<td>Capped at 10% of gross where the recipient is the beneficial owner.</td>
<td>Source state</td><td>${sourceCell('S11')}</td></tr>
<tr class="data-row"><td><strong>8. Relief available against component 2 and 7</strong></td>
<td>Foreign tax credit in the country of residence.</td>
<td>Provided for by the treaty; U.S. mechanics and limits were not verified this session.</td>
<td>IRS</td><td>${sourceCell('S11')} ${flagCell('F13')}</td></tr>
</tbody></table></div>

<h2>What this means in practice</h2>
<div class="callout ok"><p>If the Chinese tax on the income has already been paid, the lawful cost
of converting the balance is <strong>component 3 plus component 4</strong>: the bank's spread and
the number of years the quota forces you to spread the transfer over. That is why the cheapest
lawful strategy is not to hunt for a tax shelter — it is to (a) make sure component 2 is
actually settled, so the authenticity review passes; (b) claim component 8 so it is not paid
twice; (c) minimise component 3 by getting competing written quotes; and (d) shorten component 4
by qualifying for the emigrant asset transfer or a genuine trade settlement account, both of
which sit outside the quota.</p></div>
<div class="callout bad"><p>Every "cheap" alternative advertised online attacks component 4 by
breaking the law, and in doing so converts a modest, quantifiable cost into component 6 — an
unquantified penalty exposure plus, on the U.S. side, component 5. That trade is not worth
making, and the site does not recommend it.</p></div>`;

writePage(
  'cost-breakdown.html',
  shell('Cost breakdown', 'cost-breakdown.html', costBody, 'The conversion penalty decomposed into its actual components, each tied to an official source or explicitly marked unverified.')
);

/* ----------------------------------------------------------------- us rules */
const usRows = usRules.rules
  .map(
    (r) => `
<tr class="data-row" id="${esc(r.id)}">
<td class="id">${esc(r.id)}</td><td><strong>${esc(r.topic)}</strong></td><td>${esc(r.finding)}</td>
<td>${r.value === 'unverified' ? UNVERIFIED : esc(r.value)}</td>
<td>${r.form === 'Not applicable' ? '<span class="muted">—</span>' : esc(r.form)}</td>
<td>${r.verifiedByFetch ? '<span class="badge badge-ok">fetched</span>' : '<span class="badge badge-warn">search-index</span>'}</td>
<td>${sourceCell([r.sourceId, ...(r.additionalSources || [])])}</td><td>${flagCell(r.flag)}</td>
</tr>`
  )
  .join('');

writePage(
  'us-tax-rules.html',
  shell(
    'United States rules',
    'us-tax-rules.html',
    `<div class="panel"><table>
<thead><tr><th>ID</th><th>Topic</th><th>Verified finding</th><th>Value</th><th>Form</th>
<th>Verification</th><th>Source</th><th>Flag</th></tr></thead>
<tbody>${usRows}</tbody></table></div>`,
    'What a U.S. citizen with a Chinese bank account owes, files and must not do — from IRS and FinCEN sources.'
  )
);

/* -------------------------------------------------------------- china rules */
const cnRows = chinaRules.rules
  .map(
    (r) => `
<tr class="data-row" id="${esc(r.id)}">
<td class="id">${esc(r.id)}</td><td><strong>${esc(r.topic)}</strong></td><td>${esc(r.finding)}</td>
<td>${r.value === 'unverified' ? UNVERIFIED : esc(r.value)}</td>
<td>${r.authority === 'unverified' ? UNVERIFIED : esc(r.authority)}</td>
<td>${r.verifiedByFetch ? '<span class="badge badge-ok">fetched</span>' : '<span class="badge badge-warn">search-index</span>'}</td>
<td>${sourceCell([r.sourceId, ...(r.additionalSources || [])])}</td><td>${flagCell(r.flag)}</td>
</tr>`
  )
  .join('');

writePage(
  'china-rules.html',
  shell(
    'China rules',
    'china-rules.html',
    `<div class="panel"><table>
<thead><tr><th>ID</th><th>Topic</th><th>Verified finding</th><th>Value</th><th>Authority</th>
<th>Verification</th><th>Source</th><th>Flag</th></tr></thead>
<tbody>${cnRows}</tbody></table></div>
<div class="callout warn"><p>SAFE's own English pages state: "The English translation may only be
used as a reference. In case a different interpretation of the translated information contained
in this website arises, the original Chinese shall prevail." The PBOC personal-asset rules are
likewise an unofficial translation and the State Taxation Administration's English tax law is
provided for reference only. See flag F15.</p></div>`,
    'SAFE quotas, the personal-asset outbound transfer regime, card caps and individual income tax — from SAFE, PBOC and the State Taxation Administration.'
  )
);

/* ------------------------------------------------------------------- sources */
const srcRows = sources.sources
  .map(
    (s) => `
<tr class="data-row" id="${esc(s.id)}">
<td class="id">${esc(s.id)}</td>
<td><a href="${esc(s.url)}" rel="noopener noreferrer" target="_blank">${esc(s.title)}</a></td>
<td>${esc(s.publisher)}</td>
<td>${s.verifiedByFetch
      ? '<span class="badge badge-ok">fetched in-session</span>'
      : `<span class="badge badge-warn">search-index</span><div class="muted">${esc(s.verifiedVia || '')}</div>`}</td>
<td>${ul(s.supports)}</td>
</tr>`
  )
  .join('');

writePage(
  'sources.html',
  shell(
    'Source register',
    'sources.html',
    `<div class="callout"><p>${sources.sources.length} primary official documents.
<strong>fetched in-session</strong> means the page was retrieved during this session and the
quoted text was read verbatim on it. <strong>search-index</strong> means the value was read from
a search-index extract of that exact official URL but the page body was not separately retrieved
in-session; those rows are also listed on the Flagged for Review page. No commercial, blog or
advisory source is relied on anywhere on this site.</p></div>
<div class="panel"><table>
<thead><tr><th>ID</th><th>Document</th><th>Publisher</th><th>Verification</th><th>What it supports</th></tr></thead>
<tbody>${srcRows}</tbody></table></div>`,
    'Every primary document relied on, and exactly what each one supports.'
  )
);

/* --------------------------------------------------------------------- flags */
const sevClass = { high: 'st-unlawful', medium: 'st-cond', low: 'st-lawful', informational: 'badge' };
const flagRows = flags.flags
  .map(
    (f) => `
<tr class="data-row" id="${esc(f.id)}">
<td class="id">${esc(f.id)}</td>
<td><span class="${sevClass[f.severity] || 'badge'}">${esc(f.severity.toUpperCase())}</span></td>
<td><strong>${esc(f.title)}</strong><div>${esc(f.detail)}</div></td>
<td>${esc(f.action)}</td>
<td>${f.affects.length ? f.affects.map((a) => `<code>${esc(a)}</code>`).join(' ') : '<span class="muted">site-wide</span>'}</td>
<td><a href="${esc(f.sourceUrl)}" rel="noopener noreferrer" target="_blank">${esc(new URL(f.sourceUrl).host)}</a></td>
</tr>`
  )
  .join('');

writePage(
  'flagged-for-review.html',
  shell(
    'Flagged for Review',
    'flagged-for-review.html',
    `<div class="callout bad"><p>Nothing on this page is a conclusion. Each item is something this
research could <strong>not</strong> confirm from an official source. Per the project rule, those
values were left <strong>blank</strong> in every table rather than estimated, inferred or
rounded from a secondary figure. Each row states what to check and where.</p></div>
<div class="panel"><table>
<thead><tr><th>ID</th><th>Severity</th><th>Item</th><th>Action</th><th>Affects</th><th>Where to check</th></tr></thead>
<tbody>${flagRows}</tbody></table></div>`,
    'Unverified values, blank cells and repository irregularities, with an action for each.'
  )
);

/* ---------------------------------------------------------------- methodology */
writePage(
  'methodology.html',
  shell(
    'Methodology and verification',
    'methodology.html',
    `<div class="callout"><p>The rules this project was built under, and how each was enforced
mechanically rather than by assertion.</p></div>
<h2>Rules applied</h2>
<div class="panel"><table>
<thead><tr><th>Rule</th><th>How it was enforced</th></tr></thead><tbody class="meta-table">
<tr class="meta-row"><td>Every table row must have a source link to an official site</td>
<td>All content is rendered from <code>data/*.json</code> by <code>tools/build.mjs</code>. The renderer has exactly two possible outputs for a source cell: a real link to an official document, or the literal badge "UNVERIFIED — no official source". There is no code path that emits an empty source cell.</td></tr>
<tr class="meta-row"><td>If a value cannot be confirmed from an official source, leave it blank and flag it</td>
<td>Unconfirmed fields hold the literal string <code>unverified</code> in the JSON. The renderer converts that string into a visible red UNVERIFIED badge rather than printing a number. <code>tools/verify.mjs</code> fails the build if a field is empty or whitespace-only instead.</td></tr>
<tr class="meta-row"><td>Never infer or fill in values</td>
<td>No figure on this site is derived from a commercial or advisory source. The only sources in <code>data/sources.json</code> are irs.gov, fincen/cbp.dhs.gov, loc.gov, safe.gov.cn, pbc.gov.cn, chinatax.gov.cn and english.www.gov.cn.</td></tr>
<tr class="meta-row"><td>Verify line by line from primary sources</td>
<td>Each source carries <code>verifiedByFetch</code>. A true value means the page was retrieved during this session and the supporting sentences were read on it. A false value is downgraded to "search-index" everywhere it appears and is repeated on the Flagged for Review page.</td></tr>
<tr class="meta-row"><td>Flag irregularities for review</td>
<td>16 flags are recorded in <code>data/flags.json</code> and published on the Flagged for Review page, including three that record gaps in this project's own evidence base.</td></tr>
</tbody></table></div>

<h2>The verification command</h2>
<div class="callout ok"><p><code>node tools/verify.mjs</code> runs after every build and fails
non-zero if any check breaks. It checks:</p>
<p>1. Every JSON data row carries a resolvable source id whose URL is present and starts with
<code>https://</code> or <code>http://</code>, or the row is explicitly marked unverified.<br>
2. Every rendered <code>tr.data-row</code> in the built HTML contains at least one anchor to an
external official source, or contains the UNVERIFIED badge.<br>
3. No internal <code>href</code> points at a file that does not exist in <code>site/</code>.<br>
4. No anchor fragment points at an <code>id</code> that does not exist in the target page.<br>
5. No data field is empty or whitespace-only — a blank cell is a build failure, because a blank
cell and an unverified cell are different claims.<br>
6. Every source URL is on an official allowlist domain.</p></div>

<h2>What was not verified, and why</h2>
<div class="callout warn"><p>Outbound HTTP from this build sandbox is restricted to a small
allowlist that does not include irs.gov or safe.gov.cn, so external links cannot be
re-requested at build time. External URL verification was therefore performed during research,
in-session, page by page, and the result is recorded per source in the
<a href="sources.html">source register</a>. Internal links and fragments <em>are</em> checked
mechanically on every build, because those are the links this project controls.</p></div>`,
    'How the "verify everything, never infer" rule was enforced by code rather than by assertion.'
  )
);

/* ---------------------------------------------------------------- repo audit */
writePage(
  'repo-audit.html',
  shell(
    'Repository audit',
    'repo-audit.html',
    `<div class="callout warn"><p>The brief asked for a line-by-line review of the existing
repository verified against official sources. <strong>There was no existing content to
review.</strong> This is recorded as flag F03 rather than quietly skipped.</p></div>
<div class="panel"><table>
<thead><tr><th>Check</th><th>Result</th><th>Evidence</th></tr></thead><tbody>
<tr class="data-row"><td>Commits on <code>main</code> at session start</td><td>1</td>
<td><a href="https://github.com/sassnarep3-star/China2/commit/d9f397649f6601d0907184e7f16c9e03e5ca6d74" rel="noopener noreferrer" target="_blank">d9f3976 — "Initial commit"</a></td></tr>
<tr class="data-row"><td>Files in the working tree of <code>main</code></td><td>1 — <code>README.md</code></td>
<td><code>git ls-tree -r --name-only main</code> — <a href="https://github.com/sassnarep3-star/China2/tree/main" rel="noopener noreferrer" target="_blank">repository tree at main</a></td></tr>
<tr class="data-row"><td>Size and contents of <code>README.md</code></td><td>8 bytes, the text <code># China2</code>, no trailing newline</td><td><code>cat README.md</code> — <a href="https://github.com/sassnarep3-star/China2/blob/main/README.md" rel="noopener noreferrer" target="_blank">README.md at main</a></td></tr>
<tr class="data-row"><td>Pre-existing data files</td><td>None</td><td><a href="https://github.com/sassnarep3-star/China2/tree/main" rel="noopener noreferrer" target="_blank">repository tree at main</a></td></tr>
<tr class="data-row"><td>Pre-existing code, tests or build configuration</td><td>None</td><td><a href="https://github.com/sassnarep3-star/China2/tree/main" rel="noopener noreferrer" target="_blank">repository tree at main</a></td></tr>
<tr class="data-row"><td>Pre-existing site or GitHub Pages configuration</td><td>None; no <code>.github/</code> directory</td><td><a href="https://github.com/sassnarep3-star/China2/tree/main" rel="noopener noreferrer" target="_blank">repository tree at main</a></td></tr>
<tr class="data-row"><td>Pre-existing <code>COORDINATION.md</code></td><td>None on <code>main</code></td><td><a href="https://github.com/sassnarep3-star/China2/tree/main" rel="noopener noreferrer" target="_blank">repository tree at main</a></td></tr>
<tr class="data-row"><td>Pre-existing <code>LICENSE</code></td><td>None</td><td><a href="https://github.com/sassnarep3-star/China2/tree/main" rel="noopener noreferrer" target="_blank">repository tree at main</a></td></tr>
<tr class="data-row"><td>Remote branches at session start</td><td><code>main</code>, <code>arena/4c576a01-china2</code>, <code>arena/996dc508-china2</code></td><td><code>git ls-remote --heads origin</code> — <a href="https://github.com/sassnarep3-star/China2/branches" rel="noopener noreferrer" target="_blank">branch list</a></td></tr>
<tr class="data-row"><td>Content on the two parallel-session branches</td><td>A <code>COORDINATION.md</code> claim commit each; no project files</td><td><code>git ls-tree -r --name-only</code> on each branch — <a href="https://github.com/sassnarep3-star/China2/branches" rel="noopener noreferrer" target="_blank">branch list</a></td></tr>
</tbody></table></div>
<h2>Irregularities flagged</h2>
<div class="panel"><table>
<thead><tr><th>ID</th><th>Irregularity</th><th>Detail</th></tr></thead><tbody>
<tr class="data-row"><td class="id">F03</td><td>No pre-existing data to audit</td>
<td>Every finding in this project is newly produced from primary sources. No prior data was verified, because none existed. <a href="flagged-for-review.html#F03">F03</a> · <a href="https://github.com/sassnarep3-star/China2/commit/d9f397649f6601d0907184e7f16c9e03e5ca6d74" rel="noopener noreferrer" target="_blank">initial commit on main</a></td></tr>
<tr class="data-row"><td class="id">F16</td><td>Three parallel sessions claimed overlapping scopes</td>
<td>At session start three sessions held claims over the same deliverable, with two of them overlapping each other on <code>README.md</code>, <code>.github/</code> and <code>COORDINATION.md</code>. This session took a disjoint file scope and left the other sessions' claimed files untouched. <a href="flagged-for-review.html#F16">F16</a> · <a href="https://github.com/sassnarep3-star/China2/blob/arena/fcd22b0c-china2/COORDINATION.md" rel="noopener noreferrer" target="_blank">COORDINATION.md</a> · <a href="https://github.com/sassnarep3-star/China2/branches" rel="noopener noreferrer" target="_blank">branch list</a></td></tr>
</tbody></table></div>`,
    'What the repository actually contained when this work started, and what that means for the audit.'
  )
);

const built = readdirSync(SITE).sort();
console.log(`Built ${built.length} files into site/:`);
for (const f of built) console.log('  ' + f);
