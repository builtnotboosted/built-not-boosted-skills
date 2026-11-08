// Render motion-graphic specs to transparent ProRes 4444 (.mov) — or PNG stills in preview mode.
// usage: node mg_render.js specs.json outDir [preview]
//   spec: { "id":"stat_bankrate", "tpl":"stat", "dur":3.2, "params":{...}, "previewAt":[2.0] }
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
(async () => {
  const [specFile, outDir, mode] = process.argv.slice(2);
  const specs = JSON.parse(fs.readFileSync(specFile, 'utf8'));
  fs.mkdirSync(outDir, { recursive: true });
  const b = await chromium.launch({ headless: true });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await pg.goto('file://' + path.join(__dirname, 'kit.html'));
  // per-project brand override: colours + fonts injected over the kit defaults.
  // build.py writes brand.json beside the specs when project.json has a "brand"; no file = the house look.
  const brandFile = path.join(path.dirname(specFile), 'brand.json');
  if (fs.existsSync(brandFile)) {
    const br = JSON.parse(fs.readFileSync(brandFile, 'utf8'));
    const ff = (fam, file) => file ? `@font-face{font-family:'${fam}';src:url('file://${file}');}` : '';
    await pg.addStyleTag({ content: `
      ${ff('BrandHead', br.head_ttf)} ${ff('BrandBody', br.body_ttf)}
      :root{--lime:${br.accent};--green:${br.primary};--ink:${br.ink};--soft:${br.ink};
            --panel:${br.panel || 'rgba(17,17,17,.94)'};--panel2:${br.panel2 || 'rgba(28,28,28,.96)'};}
      body{font-family:'BrandBody',Arial,Helvetica,sans-serif;}
      .hl,.chipq{font-family:'BrandHead','Arial Narrow',Arial,sans-serif;}
      .chipq{color:${br.chip_text || '#111'};}
    ` });
  }
  await pg.evaluate(() => document.fonts.ready);
  for (const s of specs) {
    const FPS = s.fps || 30;
    await pg.evaluate(([t, p, d]) => window.setup(t, p, d), [s.tpl, s.params, s.dur]);
    if (mode === 'preview') {
      for (const t of (s.previewAt || [s.dur * 0.6])) {
        await pg.evaluate(t => window.render(t), t);
        await pg.screenshot({ path: path.join(outDir, `${s.id}_t${t.toFixed(1)}.png`), omitBackground: true });
      }
      console.log('preview', s.id); continue;
    }
    const fd = path.join(outDir, `_frames_${s.id}`); fs.rmSync(fd, { recursive: true, force: true }); fs.mkdirSync(fd);
    const n = Math.round(s.dur * FPS);
    for (let i = 0; i < n; i++) {
      await pg.evaluate(t => window.render(t), i / FPS);
      await pg.screenshot({ path: path.join(fd, 'f' + String(i).padStart(4, '0') + '.png'), omitBackground: true });
    }
    execSync(`ffmpeg -y -v error -framerate ${FPS} -i "${fd}/f%04d.png" -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le -vendor apl0 "${path.join(outDir, s.id + '.mov')}"`);
    fs.rmSync(fd, { recursive: true, force: true });
    console.log('rendered', s.id, n, 'frames');
  }
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
