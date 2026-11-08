#!/usr/bin/env node
/*
 render_html.js: render an HTML/CSS design to a PNG at its TRUE output size.

 Usage:  node render_html.js page.html out.png --size 1080x1350 [--wait 300] [--selector "#card"]

 - The viewport is exactly the target size, device scale factor 1 (no CSS scale tricks).
 - Waits for fonts and images before the screenshot, so no fallback font sneaks in.
 - Prints the PNG's real width and height read back from the file. Exit 1 if they differ from --size.
 Needs Node 18+ and Playwright with Chromium (npm i -g playwright && npx playwright install chromium).
*/
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');

const args = process.argv.slice(2);
if (args.length < 2 || args.includes('-h') || args.includes('--help')) {
  const src = fs.readFileSync(__filename, 'utf8');
  process.stdout.write(src.slice(src.indexOf('/*') + 2, src.indexOf('*/')).replace(/^ /gm, '') + '\n');
  process.exit(args.length < 2 && !args.includes('--help') && !args.includes('-h') ? 1 : 0);
}
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const [page, out] = args;
const [W, H] = (opt('--size', '1080x1350')).toLowerCase().split('x').map(Number);
const wait = Number(opt('--wait', '200')), selector = opt('--selector', null);

function loadPlaywright() {
  try { return require('playwright'); } catch (e) {}
  try { return require(path.join(execSync('npm root -g', { encoding: 'utf8' }).trim(), 'playwright')); } catch (e) {}
  console.error('Playwright not found. Install it: npm i -g playwright && npx playwright install chromium');
  process.exit(2);
}

function pngSize(file) {           // width/height from the IHDR chunk
  const b = fs.readFileSync(file);
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}

(async () => {
  if (!fs.existsSync(page)) { console.error('no such page: ' + page); process.exit(1); }
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await pg.goto('file://' + path.resolve(page), { waitUntil: 'load' });
  await pg.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
  });
  if (wait) await pg.waitForTimeout(wait);
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  if (selector) await pg.locator(selector).first().screenshot({ path: out, omitBackground: false });
  else await pg.screenshot({ path: out, clip: { x: 0, y: 0, width: W, height: H } });
  await browser.close();
  const [w, h] = pngSize(out);
  console.log(`${out}: ${w}x${h}` + (w === W && h === H ? ' (matches target)' : ` MISMATCH: expected ${W}x${H}`));
  process.exit(w === W && h === H ? 0 : 1);
})().catch(e => { console.error('FAIL ' + (e.message || e)); process.exit(1); });
