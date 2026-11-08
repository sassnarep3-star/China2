/* Optional real-browser check for the tax workbook.
   Install test-only packages under ignored .cache/browser:
   npm install --prefix .cache/browser --no-save --package-lock=false playwright-core @sparticuz/chromium
   Run: node tax-workbook/tests/browser_test.cjs
   Server: python3 tax-workbook/serve.py --port 8000
*/
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../.cache/browser/node_modules/playwright-core');

(async () => {
  const { default: binary, inflate } = await import('../../.cache/browser/node_modules/@sparticuz/chromium/build/index.js');
  const libRoot = await inflate(path.resolve('.cache/browser/node_modules/@sparticuz/chromium/bin/al2023.tar.br'));
  process.env.LD_LIBRARY_PATH = libRoot + '/lib' + (process.env.LD_LIBRARY_PATH ? ':' + process.env.LD_LIBRARY_PATH : '');
  const browser = await chromium.launch({ args: binary.args, executablePath: await binary.executablePath(), headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const base = (process.env.BASE_URL || 'http://127.0.0.1:8000/tax-workbook/site/').replace(/\/?$/, '/');
  const counts = { index: 0, workbook: 40, rules: 18, sources: 15, review: 10, methodology: 0 };

  for (const [name, count] of Object.entries(counts)) {
    const response = await page.goto(base + name + '.html');
    assert.equal(response.status(), 200, name);
    await page.waitForLoadState('networkidle');
    assert.equal(await page.locator('h1').count(), 1, name);
    assert.equal(await page.locator('nav a[aria-current="page"]').count(), 1, name);
    assert.equal(await page.locator('tbody tr').count(), count, name);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `desktop overflow: ${name}`);
  }

  await page.goto(base + 'workbook.html');
  assert.equal(await page.locator('td.blank').count(), 240);
  assert.equal(await page.locator('tbody tr').first().locator('th').textContent(), '$10,000');
  assert.equal(await page.locator('tbody tr').last().locator('th').textContent(), '$400,000');
  for (const file of ['workbook.csv', 'workbook.json']) {
    const res = await page.request.get(base + file);
    assert.equal(res.status(), 200, file);
  }

  fs.mkdirSync('.cache/screenshots', { recursive: true });
  await page.goto(base + 'index.html');
  await page.screenshot({ path: '.cache/screenshots/tax-workbook-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  for (const name of Object.keys(counts)) {
    await page.goto(base + name + '.html');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `mobile overflow: ${name}`);
    assert.equal(await page.locator('h1').isVisible(), true, name);
  }
  await page.goto(base + 'workbook.html');
  await page.screenshot({ path: '.cache/screenshots/tax-workbook-mobile.png', fullPage: true });
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('PASS: real Chromium, 6 pages desktop/mobile, 40 workbook rows, 240 blank unverified cells, downloads, no page errors or viewport overflow.');
})().catch(e => { console.error(e); process.exit(1); });
