#!/usr/bin/env node
/*
 animate_render.js: turn a generated background scene + a text config into a looping MP4
 (an "animated static"): kinetic type over the scene, a slow push-in, optional audio bed.

 Usage:   node animate_render.js config.json
          node animate_render.js --help

 The hero headline, its scrim and its underline are fully visible from FRAME 0, because profile
 grids poster a video from its first frame. Supporting lines (kicker, body, payoff, CTA, footer)
 animate in after that.

 Needs: Node 18+, ffmpeg on PATH, Playwright (found if installed globally or via NODE_PATH;
 otherwise installed into the scratch folder on first run) and a Chromium for Playwright.
 Scratch lives in $ANIMATE_RENDER_DIR (default: <tmp>/animate-render); only the MP4 is output.

 Config (only bg, headline, aspect, out are required):
 {
   "bg": "/abs/path/scene.png",            // full-bleed scene at (or near) the target aspect
   "aspect": "4x5",                         // 4x5 (1080x1350) | 9x16 (1080x1920) | 1x1 (1080x1080)
   "headline": ["Open before", "the school run"],
   "accent": "Open",                        // one word/phrase in the headline shown in the accent colour
   "kicker": "Local tip",
   "subhead": "Fresh bread from 7am,\nMonday to Friday.",
   "payoff": "Pre-order the night before.",
   "cta": "What would you order first?",
   "footer": "Your name · What you do · Your town",
   "brand": {                               // or "brandFile": "/abs/path/brand.json" with the same keys
     "accent": "#F2A900", "primary": "#C8102E", "ink": "#FFFFFF", "dark": "#111111",
     "headFont": "/abs/path/HeadlineFont.ttf", "bodyFont": "/abs/path/BodyFont.ttf",
     "headFamily": "Barlow Condensed", "bodyFamily": "Inter"
   },
   "durationMs": 5000, "fps": 30,
   "audio": "/abs/path/cleared-track.mp3",  // optional; only tracks cleared for commercial social use
   "audioVolume": 0.18,
   "poster": true,                          // also write <out>.poster.png (frame 0) for review
   "gif": false,
   "out": "/abs/path/piece.mp4"
 }
*/
const { execSync, spawnSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');

if (process.argv.length < 3 || ['-h', '--help'].includes(process.argv[2])) {
  const src = fs.readFileSync(__filename, 'utf8');
  process.stdout.write(src.slice(src.indexOf('/*') + 2, src.indexOf('*/')).replace(/^ /gm, '') + '\n');
  process.exit(process.argv.length < 3 ? 1 : 0);
}

const WORK = process.env.ANIMATE_RENDER_DIR || path.join(os.tmpdir(), 'animate-render');
fs.mkdirSync(WORK, { recursive: true });
const log = m => process.stderr.write('[animate] ' + m + '\n');
const sh = (c, opts) => execSync(c, Object.assign({ stdio: 'pipe', encoding: 'utf8' }, opts));

const SIZES = { '4x5': { w: 1080, h: 1350 }, '9x16': { w: 1080, h: 1920 }, '1x1': { w: 1080, h: 1080 } };

// ---------- find (or install) Playwright ----------
function loadPlaywright() {
  const tries = [() => require('playwright'),
    () => require(path.join(sh('npm root -g').trim(), 'playwright')),
    () => require(path.join(WORK, 'node_modules', 'playwright'))];
  for (const t of tries) { try { return t(); } catch (e) { /* next */ } }
  log('Playwright not found: installing it into ' + WORK + ' (one time)...');
  sh('npm init -y >/dev/null 2>&1; npm i playwright >/dev/null 2>&1', { cwd: WORK, shell: true });
  return require(path.join(WORK, 'node_modules', 'playwright'));
}

// Some minimal Linux sandboxes lack libXdamage, which headless Chromium links against. Build a tiny
// no-op stub (needs gcc) only if the browser actually fails to launch for that reason.
function xdamageStub() {
  if (process.platform !== 'linux') return null;
  const libdir = path.join(WORK, 'libs'); fs.mkdirSync(libdir, { recursive: true });
  const stub = path.join(libdir, 'libXdamage.so.1');
  if (!fs.existsSync(stub)) {
    const c = path.join(WORK, 'xdamage_stub.c');
    fs.writeFileSync(c, 'int XDamageQueryExtension(void*a,void*b,void*c){return 0;}\nunsigned long XDamageCreate(void*a,unsigned long b,int c){return 0;}\nvoid XDamageDestroy(void*a,unsigned long b){}\nvoid XDamageSubtract(void*a,unsigned long b,unsigned long c,unsigned long d){}\n');
    try { sh(`gcc -shared -fPIC -Wl,-soname,libXdamage.so.1 -o "${stub}" "${c}"`); } catch (e) { return null; }
  }
  return libdir;
}

async function launch(pw) {
  try { return await pw.chromium.launch({ headless: true }); }
  catch (e) {
    const msg = String(e.message || e);
    if (/Executable doesn't exist|playwright install/i.test(msg)) {
      log('installing Playwright Chromium (one time)...');
      spawnSync('npx', ['--yes', 'playwright', 'install', 'chromium'], { stdio: 'inherit', cwd: WORK, shell: process.platform === 'win32' });
      return await pw.chromium.launch({ headless: true });
    }
    if (/libXdamage/i.test(msg)) {
      const libdir = xdamageStub();
      if (libdir) {
        return await pw.chromium.launch({ headless: true, env: { ...process.env, LD_LIBRARY_PATH: libdir + ':' + (process.env.LD_LIBRARY_PATH || '') } });
      }
    }
    throw e;
  }
}

// ---------- page ----------
const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function brandOf(cfg) {
  let b = {};
  if (cfg.brandFile) b = JSON.parse(fs.readFileSync(cfg.brandFile, 'utf8'));
  b = Object.assign({ accent: '#FFD166', primary: '#FFD166', ink: '#FFFFFF', dark: '#111111' }, b, cfg.brand || {});
  return b;
}

function buildHtml(cfg, dims) {
  const b = brandOf(cfg);
  const accent = cfg.accent ? esc(cfg.accent) : null;
  const H = (cfg.headline || []).map(line => {
    const l = esc(line);
    return accent && l.includes(accent) ? l.replace(accent, '<span class="acc">' + accent + '</span>') : l;
  }).join('<br>');
  const sub = esc(cfg.subhead).replace(/\n/g, '<br>');
  const tall = cfg.aspect === '9x16', sq = cfg.aspect === '1x1';
  const scale = tall ? 1.06 : 1.0;
  // grid-safe: the content block ends at the bottom of the centred square (inset), so the headline sits inside it
  const sqTop = Math.round((dims.h - dims.w) / 2);
  const contentBottom = sq ? 150 : (dims.h - (sqTop + dims.w)) + 80;
  const footerBottom = tall ? 120 : (sq ? 48 : 56);
  const ff = (fam, file) => file ? `@font-face{font-family:'${fam}';src:url('file://${file}');}` : '';
  const head = `'BrandHead',${b.headFamily ? `'${b.headFamily}',` : ''}'Barlow Condensed','Arial Narrow','Liberation Sans Narrow',Arial,sans-serif`;
  const body = `'BrandBody',${b.bodyFamily ? `'${b.bodyFamily}',` : ''}Inter,'Helvetica Neue',Arial,sans-serif`;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
${ff('BrandHead', b.headFont)} ${ff('BrandBody', b.bodyFont)}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:${dims.w}px;height:${dims.h}px;overflow:hidden;background:#000;}
#stage{position:relative;width:${dims.w}px;height:${dims.h}px;font-family:${body};}
#bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transform-origin:center;}
#scrim{position:absolute;inset:0;opacity:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 20%,rgba(0,0,0,0.35) 45%,rgba(0,0,0,0.88) 82%);}
.content{position:absolute;left:84px;right:84px;bottom:${contentBottom}px;}
#bar{width:84px;height:10px;background:${b.accent};border-radius:5px;margin-bottom:24px;transform-origin:left center;}
#kicker{color:${b.ink};letter-spacing:5px;font-size:${Math.round(27 * scale)}px;font-weight:700;text-transform:uppercase;margin-bottom:18px;font-family:${head};}
#headline{color:${b.ink};font-family:${head};font-size:${Math.round(96 * scale)}px;line-height:0.98;font-weight:800;text-transform:uppercase;margin-bottom:24px;text-shadow:0 2px 20px rgba(0,0,0,0.55);}
#headline .acc{color:${b.accent};}
#body{color:${b.ink};opacity:.94;font-size:${Math.round(35 * scale)}px;line-height:1.3;font-weight:400;margin-bottom:14px;}
#payoff{color:${b.accent};font-size:${Math.round(42 * scale)}px;line-height:1.22;font-weight:800;margin-bottom:34px;transform-origin:left center;font-family:${head};}
#cta{display:inline-block;background:${b.primary};color:${b.ctaText || b.ink};font-size:${Math.round(30 * scale)}px;font-weight:700;padding:22px 34px;border-radius:16px;box-shadow:0 10px 28px rgba(0,0,0,0.4);}
#footer{position:absolute;left:84px;bottom:${footerBottom}px;color:${b.ink};opacity:.85;font-size:${Math.round(24 * scale)}px;font-weight:500;}
.el{opacity:0;}
</style></head><body>
<div id="stage">
<img id="bg" src="bg.png">
<div id="scrim"></div>
<div class="content">
<div id="bar" class="el"></div>
${cfg.kicker ? `<div id="kicker" class="el">${esc(cfg.kicker)}</div>` : ''}
<div id="headline" class="el">${H}</div>
${sub ? `<div id="body" class="el">${sub}</div>` : ''}
${cfg.payoff ? `<div id="payoff" class="el">${esc(cfg.payoff)}</div>` : ''}
${cfg.cta ? `<div id="cta" class="el">${esc(cfg.cta)}</div>` : ''}
</div>
${cfg.footer ? `<div id="footer" class="el">${esc(cfg.footer)}</div>` : ''}
</div>
<script>
function eoc(x){return 1-Math.pow(1-x,3);}
function eob(x){var c1=1.70158,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);}
function cl(x){return Math.max(0,Math.min(1,x));}
// scrim, bar and headline start before t=0 so they are fully on in frame 0 (the grid poster)
var TL=[['scrim',-400,400,'fade'],['bar',-400,400,'growx'],['headline',-400,400,'rise'],['kicker',450,600,'riseL'],
        ['body',1600,650,'rise'],['payoff',2450,650,'popL'],['cta',3250,700,'pop'],['footer',3650,600,'fade']];
var DUR=${cfg.durationMs || 5000};
function ap(id,ty,p){var e=document.getElementById(id);if(!e)return;
if(ty==='fade'){e.style.opacity=p;}
else if(ty==='growx'){e.style.opacity=p>0?1:0;e.style.transform='scaleX('+eoc(p)+')';}
else if(ty==='rise'){var q=eoc(p);e.style.opacity=q;e.style.transform='translateY('+(1-q)*42+'px)';}
else if(ty==='riseL'){var q=eoc(p);e.style.opacity=q;e.style.transform='translateX('+(1-q)*-32+'px)';}
else if(ty==='popL'){var q=eob(cl(p));e.style.opacity=cl(p*1.6);e.style.transform='scale('+(0.8+0.2*q)+')';}
else if(ty==='pop'){var q=eob(cl(p));e.style.opacity=cl(p*1.6);e.style.transform='scale('+(0.72+0.28*q)+')';}}
window.seek=function(t){
 var z=1.04+0.05*(t/DUR); document.getElementById('bg').style.transform='scale('+z+')';
 for(var i=0;i<TL.length;i++){var s=TL[i];ap(s[0],s[3],cl((t-s[1])/s[2]));}};
window.__ready=false;var img=document.getElementById('bg');
function rdy(){document.fonts.ready.then(function(){window.seek(0);window.__ready=true;});}
if(img.complete)rdy();else img.onload=rdy;
</script></body></html>`;
}

async function main() {
  const cfgPath = process.argv[2];
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  for (const k of ['bg', 'headline', 'aspect', 'out']) if (!cfg[k]) throw new Error(`config needs "${k}"`);
  const dims = SIZES[cfg.aspect];
  if (!dims) throw new Error(`aspect must be one of ${Object.keys(SIZES).join(', ')}`);
  if (!fs.existsSync(cfg.bg)) throw new Error('background not found: ' + cfg.bg);
  try { sh('ffmpeg -version'); } catch (e) { throw new Error('ffmpeg not found on PATH'); }

  const scene = fs.mkdtempSync(path.join(WORK, 'scene-'));
  fs.copyFileSync(cfg.bg, path.join(scene, 'bg.png'));
  fs.writeFileSync(path.join(scene, 'card.html'), buildHtml(cfg, dims));
  const framesDir = path.join(scene, 'frames'); fs.mkdirSync(framesDir);
  const fps = cfg.fps || 30, dur = cfg.durationMs || 5000, N = Math.round(fps * dur / 1000);

  const pw = loadPlaywright();
  const browser = await launch(pw);
  const pg = await browser.newPage({ viewport: { width: dims.w, height: dims.h }, deviceScaleFactor: 1 });
  await pg.goto('file://' + path.join(scene, 'card.html'));
  await pg.waitForFunction('window.__ready===true', null, { timeout: 30000 });
  for (let i = 0; i < N; i++) {
    await pg.evaluate(tt => window.seek(tt), i * (1000 / fps));
    await pg.screenshot({ path: path.join(framesDir, 'f' + String(i).padStart(4, '0') + '.png') });
  }
  await browser.close();

  fs.mkdirSync(path.dirname(path.resolve(cfg.out)), { recursive: true });
  if (cfg.poster !== false) fs.copyFileSync(path.join(framesDir, 'f0000.png'), cfg.out.replace(/\.mp4$/i, '') + '.poster.png');
  const silent = cfg.audio ? path.join(scene, 'silent.mp4') : cfg.out;
  sh(`ffmpeg -y -v error -framerate ${fps} -i "${framesDir}/f%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart "${silent}"`);
  if (cfg.audio) {
    if (!fs.existsSync(cfg.audio)) throw new Error('audio not found: ' + cfg.audio);
    const vol = cfg.audioVolume == null ? 0.18 : cfg.audioVolume;
    const fo = Math.max(0, dur / 1000 - 0.6);
    sh(`ffmpeg -y -v error -i "${silent}" -stream_loop -1 -i "${cfg.audio}" -filter_complex "[1:a]volume=${vol},afade=t=in:st=0:d=0.5,afade=t=out:st=${fo.toFixed(2)}:d=0.6[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart "${cfg.out}"`);
  }
  if (cfg.gif) {
    const gif = cfg.out.replace(/\.mp4$/i, '.gif');
    sh(`ffmpeg -y -v error -i "${cfg.out}" -vf "fps=20,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" "${gif}"`);
  }
  fs.rmSync(scene, { recursive: true, force: true });
  log(`rendered ${N} frames at ${dims.w}x${dims.h} -> ${cfg.out}`);
  console.log(cfg.out);
}
main().catch(e => { log('FAIL ' + (e.message || e)); process.exit(1); });
