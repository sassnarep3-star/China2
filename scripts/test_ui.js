// Dependency-free DOM harness for the real client script (not a visual browser audit).
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
function harness(ledger = false) {
  const listeners = {};
  const label = { hidden: false };
  const input = { value: '', addEventListener: (e, f) => listeners.search = f };
  const select = { value: '', closest: () => label, addEventListener: (e, f) => listeners.status = f };
  const count = {textContent: ''};
  const empty = {hidden: true};
  const printButton = { addEventListener: (e, f) => listeners.print = f };
  const rows = [
    {textContent: 'salary SAFE Source-backed', hidden: false, querySelector: () => ledger ? null : {textContent: 'Source-backed'}},
    {textContent: 'Hong Kong Unverified', hidden: false, querySelector: () => ledger ? null : {textContent: 'Unverified'}}
  ];
  let printed = false;
  const nodes = {'#search': input, '#status': select, '#result-count': count, '.empty-state': empty, '.print': printButton, 'tbody .badge': ledger ? null : {}};
  const document = {getElementById: id => nodes['#' + id], querySelectorAll: () => rows, querySelector: sel => nodes[sel]};
  vm.runInNewContext(fs.readFileSync('docs/assets/app.js', 'utf8'), {document, window: { print: () => { printed = true; } }});
  assert.equal(count.textContent, '2 of 2 entries');
  input.value = 'SALARY'; listeners.search();
  assert.equal(count.textContent, '1 of 2 entries');
  assert.equal(rows[1].hidden, true);
  input.value = ''; select.value = ledger ? '' : 'Unverified'; listeners.status();
  assert.equal(count.textContent, ledger ? '2 of 2 entries' : '1 of 2 entries');
  input.value = 'not-present'; listeners.search();
  assert.equal(empty.hidden, false);
  listeners.print(); assert.equal(printed, true);
  assert.equal(label.hidden, ledger);
}
harness(); harness(true);
// Overview contains no filtering controls; ensure progressive-enhancement script remains safe.
vm.runInNewContext(fs.readFileSync('docs/assets/app.js','utf8'), {document:{getElementById:()=>null,querySelectorAll:()=>[],querySelector:()=>null}, window:{}});
console.log('PASS: search case-insensitivity, status filter, empty state, ledger filter hiding, print action and no-controls overview.');
