#!/usr/bin/env node
/**
 * tools/verify.mjs — the project's own check. Exits non-zero on any failure.
 *
 * Enforces the four rules the brief set:
 *   1. every table row carries a source link to an official site, or is explicitly UNVERIFIED
 *   2. a value that cannot be confirmed is left blank/flagged, never estimated
 *   3. no broken internal links or dangling anchors
 *   4. every source is on an official domain allowlist
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
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
const FLAG_IDS = new Set(flags.flags.map((f) => f.id));

const OFFICIAL_DOMAINS = [
  'irs.gov',
  'ecfr.gov',
  'cbp.dhs.gov',
  'treas.gov',
  'loc.gov',
  'safe.gov.cn',
  'pbc.gov.cn',
  'chinatax.gov.cn',
  'www.gov.cn',
  'customs.gov.cn',
  'github.com',
];
const isOfficial = (u) => {
  let h;
  try {
    h = new URL(u).hostname.replace(/^www\./, '');
  } catch {
    return false;
  }
  return OFFICIAL_DOMAINS.some((d) => h === d || h.endsWith('.' + d));
};

let failures = 0;
let checks = 0;
const fail = (msg) => {
  failures++;
  console.log('  FAIL  ' + msg);
};
const ok = (msg) => {
  checks++;
  console.log('  ok    ' + msg);
};

/* ------------------------------------------------- check 1: data-row sources */
console.log('\n[1] Every data row has an official source, or is explicitly unverified');

function checkRowSource(label, row) {
  checks++;
  const ids = [row.sourceId, ...(row.additionalSources || [])].filter(Boolean);
  if (ids.length === 0) {
    // A row with no source at all is only acceptable when it is disclosed as a flag.
    if (row.flag && FLAG_IDS.has(row.flag)) {
      ok(`${label} has no source but is disclosed as flag ${row.flag}`);
      return;
    }
    fail(`${label} has no sourceId and no flag — an unsourced row is not allowed`);
    return;
  }
  for (const id of ids) {
    const s = SRC[id];
    if (!s) {
      fail(`${label} references unknown source id ${id}`);
      continue;
    }
    if (!s.url || !/^https?:\/\//.test(s.url)) {
      fail(`${label} source ${id} has no usable URL`);
      continue;
    }
    if (!isOfficial(s.url)) {
      fail(`${label} source ${id} URL is not on the official allowlist: ${s.url}`);
      continue;
    }
  }
  ok(`${label} sourced to ${ids.join(', ')}`);
}

for (const r of methods.routes) checkRowSource(`route ${r.id}`, r);
for (const r of usRules.rules) checkRowSource(`us-rule ${r.id}`, r);
for (const r of chinaRules.rules) checkRowSource(`china-rule ${r.id}`, r);

/* ------------------------------------------- check 2: no blank/empty values */
console.log('\n[2] No blank fields — a blank cell and an unverified cell are different claims');

function walkStrings(obj, path, bad) {
  if (typeof obj === 'string') {
    if (obj.trim() === '') bad.push(path);
    return;
  }
  if (Array.isArray(obj)) {
    // `affects: []` is meaningful — it means the flag is site-wide rather than row-specific.
    if (obj.length === 0 && !path.endsWith('.affects')) bad.push(path + ' (empty array)');
    obj.forEach((v, i) => walkStrings(v, `${path}[${i}]`, bad));
    return;
  }
  if (obj && typeof obj === 'object') {
    for (const [k, v] of Object.entries(obj)) walkStrings(v, `${path}.${k}`, bad);
  }
}

for (const [name, doc] of [
  ['sources.json', sources],
  ['methods.json', methods],
  ['us-rules.json', usRules],
  ['china-rules.json', chinaRules],
  ['flags.json', flags],
]) {
  checks++;
  const bad = [];
  walkStrings(doc, name, bad);
  if (bad.length) fail(`${name} has ${bad.length} empty field(s): ${bad.slice(0, 8).join(', ')}`);
  else ok(`${name} has no empty fields`);
}

/* ------------------------------ check 3: every flag referenced actually exists */
console.log('\n[3] Every flag id referenced from a data row exists in flags.json');
const referenced = new Set();
for (const set of [methods.routes, usRules.rules, chinaRules.rules])
  for (const r of set) if (r.flag) referenced.add(r.flag);
for (const id of referenced) {
  checks++;
  if (!FLAG_IDS.has(id)) fail(`flag ${id} is referenced but not defined`);
  else ok(`flag ${id} defined`);
}
// flags claiming to affect rows should name real rows
const ALL_IDS = new Set([
  ...methods.routes.map((r) => r.id),
  ...usRules.rules.map((r) => r.id),
  ...chinaRules.rules.map((r) => r.id),
]);
for (const f of flags.flags) {
  checks++;
  const unknown = f.affects.filter((a) => !ALL_IDS.has(a));
  if (unknown.length) fail(`flag ${f.id} affects unknown row ids: ${unknown.join(', ')}`);
  else ok(`flag ${f.id} affects ${f.affects.length} known row id(s)`);
}

/* ------------------------------------------- check 4: source allowlist + urls */
console.log('\n[4] Every source and flag URL is an official government or registry domain');
for (const s of sources.sources) {
  checks++;
  if (!isOfficial(s.url)) fail(`source ${s.id} is not an official domain: ${s.url}`);
  else ok(`source ${s.id} ${new URL(s.url).hostname}`);
}
for (const f of flags.flags) {
  checks++;
  if (!isOfficial(f.sourceUrl)) fail(`flag ${f.id} sourceUrl is not official: ${f.sourceUrl}`);
  else ok(`flag ${f.id} ${new URL(f.sourceUrl).hostname}`);
}

/* --------------------------------------------- check 5: built HTML integrity */
console.log('\n[5] Built HTML: every data row carries a source link or the UNVERIFIED badge');
if (!existsSync(SITE)) {
  fail('site/ does not exist — run `node tools/build.mjs` first');
} else {
  const pages = readdirSync(SITE).filter((f) => f.endsWith('.html'));
  for (const p of pages) {
    const html = readFileSync(join(SITE, p), 'utf8');
    const rows = html.match(/<tr class="data-row"[\s\S]*?<\/tr>/g) || [];
    let bad = 0;
    for (const row of rows) {
      const hasExternal = /<a href="https?:\/\//.test(row);
      const hasUnverified = /class="cell-unverified"/.test(row);
      if (!hasExternal && !hasUnverified) bad++;
    }
    checks++;
    if (bad) fail(`${p}: ${bad} of ${rows.length} data rows lack both a source link and an UNVERIFIED badge`);
    else ok(`${p}: ${rows.length} data rows all sourced or explicitly unverified`);
  }

  console.log('\n[6] No broken internal links or dangling anchors');
  const idIndex = new Map();
  for (const p of pages) {
    const html = readFileSync(join(SITE, p), 'utf8');
    idIndex.set(p, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])));
  }
  for (const p of pages) {
    const html = readFileSync(join(SITE, p), 'utf8');
    let broken = 0;
    for (const m of html.matchAll(/<a href="([^"]+)"/g)) {
      const href = m[1];
      if (/^https?:|^mailto:|^tel:/.test(href)) continue;
      checks++;
      const [file, frag] = href.split('#');
      const target = file || p;
      if (!existsSync(join(SITE, target))) {
        fail(`${p}: internal link to missing file "${target}"`);
        broken++;
        continue;
      }
      if (frag && target.endsWith('.html')) {
        const ids = idIndex.get(target);
        if (!ids || !ids.has(frag)) {
          fail(`${p}: anchor "${href}" targets missing id "${frag}" in ${target}`);
          broken++;
        }
      }
    }
    if (!broken) ok(`${p}: all internal links resolve`);
  }

  console.log('\n[7] Style sheet present and referenced by every page');
  for (const p of pages) {
    const html = readFileSync(join(SITE, p), 'utf8');
    checks++;
    if (!/href="style\.css"/.test(html)) fail(`${p} does not reference style.css`);
    else ok(`${p} references style.css`);
  }
  checks++;
  if (!existsSync(join(SITE, 'style.css'))) fail('site/style.css missing');
  else ok('site/style.css present');

  console.log('\n[8] meta-row is not used to escape the source-link rule');
  // which documents process rather than evidence. Anything else must use data-row.
  for (const p of pages) {
    const html = readFileSync(join(SITE, p), 'utf8');
    const n = (html.match(/<tr class="meta-row"/g) || []).length;
    if (n === 0) continue;
    checks++;
    if (p !== 'methodology.html')
      fail(`${p} uses meta-row (${n} rows); only methodology.html may hold sourceless process rows`);
    else ok(`methodology.html holds ${n} process rows (process documentation, not evidence)`);
  }
}

/* ------------------------------------ check 9: prose counts match the ledgers */
console.log('\n[9] Counts stated in EXECUTIVE-SUMMARY.md match the ledgers');
const SUMMARY = join(ROOT, 'EXECUTIVE-SUMMARY.md');
if (!existsSync(SUMMARY)) {
  fail('EXECUTIVE-SUMMARY.md is missing');
} else {
  const md = readFileSync(SUMMARY, 'utf8');
  const nLawful = methods.routes.filter((r) => r.legalStatus !== 'unlawful').length;
  const nUnlawful = methods.routes.filter((r) => r.legalStatus === 'unlawful').length;
  const nFetched = sources.sources.filter((s) => s.verifiedByFetch).length;
  const expectations = [
    [`${methods.routes.length} routes were catalogued`, 'route count'],
    [`${nLawful} lawful or conditionally lawful`, 'lawful/conditional count'],
    [`${nUnlawful} unlawful`, 'unlawful count'],
    [`${sources.sources.length} official sources`, 'source count'],
    [`${nFetched} were retrieved in full this session`, 'fetch-verified count'],
    [`${sources.sources.length - nFetched} are marked \`search-index\``, 'search-index count'],
    [`${flags.flags.length} flags are published`, 'flag count'],
  ];
  for (const [needle, label] of expectations) {
    checks++;
    if (md.includes(needle)) ok(`${label}: "${needle}"`);
    else fail(`EXECUTIVE-SUMMARY.md does not state ${label} as "${needle}" — prose has drifted from the ledgers`);
  }
}

console.log(`\n${'-'.repeat(64)}`);
console.log(`${checks} checks run, ${failures} failure(s)`);
if (failures) {
  console.log('VERIFICATION FAILED');
  process.exit(1);
}
console.log('VERIFICATION PASSED');
