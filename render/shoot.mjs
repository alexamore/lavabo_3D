// Render delle viste: node render/shoot.mjs <url_base> <cartella_uscita>
import { chromium } from 'playwright-core';
const [base, out] = process.argv.slice(2);
const views = [['ambient', 1600, 1200], ['front', 1400, 1200], ['spout', 1400, 1100], ['section', 1500, 1300], ['exploded', 1400, 1600], ['top', 1400, 1150]];
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const [v, w, h] of views) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  page.on('console', m => { if (m.type() === 'error') console.log('console:', m.text()); });
  page.on('pageerror', e => console.log('pageerror:', e.message));
  await page.goto(`${base}?view=${v}&shot=1`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${out}/${v}.png` });
  console.log('ok', v);
  await page.close();
}
await browser.close();
