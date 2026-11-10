/* Real-browser checks for final-f6327e23. Test-only dependency, not shipped to the site.
 * Run: node final-f6327e23/browser_check.cjs <baseUrl>
 */
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium as pwChromium } from "../.cache/browser/node_modules/playwright-core/index.mjs";
import sparticuz from "../.cache/browser/node_modules/@sparticuz/chromium/build/index.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const chromium = pwChromium;

const PAGES = ["index.html", "methods.html", "costs.html", "taxes.html",
               "steps.html", "sources.html", "review.html", "repo-audit.html"];
const BASE = process.argv[2] || "http://127.0.0.1:8123";

(async () => {
  const executablePath = process.env.CHROME_PATH || (await sparticuz.executablePath());
  const browser = await chromium.launch({
    executablePath,
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
  });
  const failures = [];
  let checks = 0;
  const check = (cond, msg) => { checks++; if (!cond) failures.push(msg); };

  for (const [label, viewport] of [["mobile-390", { width: 390, height: 844 }],
                                   ["desktop-1440", { width: 1440, height: 900 }]]) {
    const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    for (const p of PAGES) {
      const page = await ctx.newPage();
      const errors = [];
      page.on("pageerror", (e) => errors.push(String(e)));
      page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
      const resp = await page.goto(`${BASE}/final-f6327e23/${p}`, { waitUntil: "load" });
      check(resp && resp.status() === 200, `${label}/${p}: HTTP ${resp && resp.status()}`);
      check(errors.length === 0, `${label}/${p}: JS errors ${errors.join(" | ")}`);
      // document-level horizontal overflow
      const overflow = await page.evaluate(() =>
        document.documentElement.scrollWidth - document.documentElement.clientWidth);
      check(overflow <= 1, `${label}/${p}: horizontal overflow ${overflow}px`);
      // tables must be inside a scroll container on mobile, never clipped
      const wide = await page.evaluate(() => {
        const out = [];
        document.querySelectorAll("table").forEach((t) => {
          const w = t.getBoundingClientRect().width;
          const parent = t.closest(".table-wrap, .scroll-x");
          if (w > window.innerWidth + 2 && !parent) out.push(Math.round(w));
        });
        return out;
      });
      check(wide.length === 0, `${label}/${p}: unclipped wide table ${wide.join(",")}`);
      // tap targets
      const small = await page.evaluate(() => {
        let n = 0;
        document.querySelectorAll("nav a, .chip, .btn").forEach((el) => {
          const r = el.getBoundingClientRect();
          if (r.height > 0 && r.height < 28) n++;
        });
        return n;
      });
      check(small === 0, `${label}/${p}: ${small} tap targets under 28px`);
      if (label === "mobile-390") {
        await page.screenshot({ path: path.join(__dirname, "..", ".cache", `shot-${p.replace(".html", "")}-390.png`), fullPage: false });
      }
      await page.close();
    }
    await ctx.close();
  }

  // interaction: filter on methods page
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/final-f6327e23/methods.html`, { waitUntil: "load" });
  const total = await page.locator(".method").count();
  check(total === 15, `methods: expected 15 cards, found ${total}`);
  await page.locator('.chip[data-filter="unlawful"]').click();
  const visible = await page.locator(".method:not(.hidden)").count();
  check(visible === 2, `methods filter unlawful: expected 2, found ${visible}`);
  await page.locator('.chip[data-filter="all"]').click();
  check(await page.locator(".method:not(.hidden)").count() === 15, "methods filter all failed");

  // interaction: nav
  await page.locator('nav a[href="costs.html"]').click();
  await page.waitForLoadState("load");
  check(page.url().endsWith("costs.html"), "nav link did not navigate");
  check(await page.locator("#primary-costs tbody tr").count() === 40, "costs table not 40 rows");

  await browser.close();
  console.log(`browser checks: ${checks}`);
  if (failures.length) {
    console.log(`FAILURES: ${failures.length}`);
    failures.forEach((f) => console.log("  -", f));
    process.exit(1);
  }
  console.log("FAILURES: 0");
})();
