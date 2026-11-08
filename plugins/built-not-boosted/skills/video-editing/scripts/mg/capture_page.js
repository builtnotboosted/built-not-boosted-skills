// Hi-res full-page capture of a public page for B-roll, plus the y-offset of a phrase to scroll to.
// usage: node capture_page.js <url> <out.png> "<phrase to locate>" [more phrases...]
const { chromium } = require('playwright');
(async () => {
  const [url, out, ...phrases] = process.argv.slice(2);
  const b = await chromium.launch({ headless: true });
  const pg = await b.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' });
  await pg.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
  // cookie banner: take the privacy-preserving option if offered, else hide it for the capture
  for (const label of [/reject/i, /necessary only/i, /essential only/i, /decline/i]) {
    const btn = pg.getByRole('button', { name: label }).first();
    if (await btn.count()) { try { await btn.click({ timeout: 2000 }); break; } catch (e) {} }
  }
  await pg.addStyleTag({ content: '[id*=cookie i],[class*=cookie i],[id*=consent i],[class*=consent i]{display:none!important}' });
  await pg.waitForTimeout(800);
  const title = await pg.title();
  const found = {};
  for (const ph of phrases) {
    found[ph] = await pg.evaluate(p => {
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let n; while ((n = w.nextNode())) if (n.textContent.includes(p)) {
        const r = n.parentElement.getBoundingClientRect(); return Math.round((r.top + window.scrollY) * 2);
      }
      return null;
    }, ph);
  }
  await pg.screenshot({ path: out, fullPage: true });
  const h = await pg.evaluate(() => document.documentElement.scrollHeight * 2);
  console.log(JSON.stringify({ title, url: pg.url(), heightPx: h, found }));
  await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });
