/* Optional real-browser audit. Install test-only packages under ignored .cache/browser:
   npm install --prefix .cache/browser --no-save --package-lock=false playwright-core @sparticuz/chromium
   node scripts/browser_test.cjs
   Server: python -m http.server 8000 --bind 0.0.0.0 --directory docs
   BASE_URL may include a subpath to test deployed GitHub Pages.
*/
const {chromium} = require('../.cache/browser/node_modules/playwright-core');

const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const {default: binary, inflate} = await import('../.cache/browser/node_modules/@sparticuz/chromium/build/index.js');
  const libRoot=await inflate(require('node:path').resolve('.cache/browser/node_modules/@sparticuz/chromium/bin/al2023.tar.br'));
  process.env.LD_LIBRARY_PATH=libRoot+'/lib'+(process.env.LD_LIBRARY_PATH ? ':'+process.env.LD_LIBRARY_PATH : '');
  const browser = await chromium.launch({args:binary.args, executablePath:await binary.executablePath(), headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1050}});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const base=(process.env.BASE_URL || 'http://127.0.0.1:8000/').replace(/\/?$/,'/');
  for(const name of ['index','routes','costs','taxes','checklist','review','sources']) {
    const response=await page.goto(base+name+'.html'); assert.equal(response.status(),200,name);
    await page.waitForLoadState('networkidle');
    assert.equal(await page.locator('h1').count(),1);
    assert.equal(await page.locator('nav a[aria-current="page"]').count(),1);
    assert.equal(await page.locator('tbody tr').count(),{index:6,routes:22,costs:12,taxes:17,checklist:7,review:9,sources:24}[name]);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`desktop overflow: ${name}`);
  }
  await page.goto(base+'routes.html');
  await page.locator('#search').fill('Wise');
  assert.match(await page.locator('#result-count').textContent(),/^2 of 22/);
  await page.locator('#search').fill('');await page.locator('#status').selectOption('Do not use');
  assert.match(await page.locator('#result-count').textContent(),/^2 of 22/);
  await page.locator('#search').fill('no-such-route');assert.equal(await page.locator('.empty-state').isVisible(),true);
  await page.goto(base+'index.html');
  fs.mkdirSync('.cache/screenshots',{recursive:true});
  await page.screenshot({path:'.cache/screenshots/desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  for(const name of ['index','routes','costs','taxes','checklist','review','sources']) {
    await page.goto(base+name+'.html');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`mobile overflow: ${name}`);
    assert.equal(await page.locator('h1').isVisible(),true);
  }
  await page.goto(base+'index.html');await page.screenshot({path:'.cache/screenshots/mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);
  await browser.close();
  console.log('PASS: real Chromium, 7 pages desktop/mobile, row counts, search/status/no-results, no page errors or viewport overflow.');
})().catch(e=>{console.error(e);process.exit(1)});
