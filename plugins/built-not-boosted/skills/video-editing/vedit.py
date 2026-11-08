#!/usr/bin/env python3
"""vedit: raw talking-head clip(s) -> release-ready 1080x1920 short or 16:9 long-form.

  vedit.py doctor                     check ffmpeg, node, Playwright, the venv, Whisper, fonts (run this first)
  vedit.py init <slug> --raw CLIP (--pack DIR | --script FILE) [--title T] [--version v1] [--long]
                [--cam B=CLIP ...] [--out DIR] [--workspace DIR]
  vedit.py prep <slug>                upright master + 16 kHz audio + extra cameras synced + two transcripts (slow)
  vedit.py transcribe <slug>          same as prep
  vedit.py takes <slug>               align speech to the script: every attempt at every line becomes a scored take,
                                      plus a second listen for stumbles, and proxy clips for the picker
  vedit.py picker <slug> [--port 8765]   serve the take picker in a browser (run in the background)
  vedit.py build <slug> [plan|cues|cut|mg|caps|final|all] [--until S]
  vedit.py captions <slug>            show the caption check (script vs what was heard) and the SRT
  vedit.py gate <slug>                QA gate on build/final.mp4: re-transcribes the render, listens to every cut,
                                      checks every cut lands in quiet. deliver refuses without a fresh PASS
  vedit.py frames <slug> [--every 5 | T T ...]   frames + contact sheet for picking a cover frame
  vedit.py cover <slug>               designed real-frame covers from project.json "cover" (+ grid preview)
  vedit.py mg-preview <slug>          stills of every graphic, for review before a full render
  vedit.py capture <url> <out.png> [phrase ...]   hi-res mobile capture of a PUBLIC page (for B-roll)
  vedit.py broll-scroll <capture.png> <stem> <y0> <y1> --desc D --tags T --url U   scrolling B-roll clip from a capture
  vedit.py deliver <slug> [--force]   file the finished set (video, SRT, covers, cut list, QA report, chapters)
  vedit.py release <slug> --to DIR [--name N]   copy video + .srt + .jpg thumbnail under ONE filename to a posting folder
  vedit.py status <slug>

Scratch (big files) lives in $VEDIT_HOME/work/<slug>/ (default ~/.vedit). Nothing is posted or scheduled by this tool.
"""
import csv, datetime, glob, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
from vcommon import (SCRIPTS, VENV_PY, VH, WORK, FONTS_HOME, load_project, project_env, FONT_BOLD, FONT_NARROW,  # noqa: E402
                     frame_size, project_fps, brand, brand_from_profile)

A = sys.argv[1:]
CMD = A[0] if A else None
NO_VENV_OK = {None, "-h", "--help", "help", "doctor"}

# run under the tool's venv (Whisper, numpy, Pillow, OpenCV live there) once setup.sh has made it
if CMD not in NO_VENV_OK and os.path.exists(VENV_PY) and os.path.realpath(sys.executable) != os.path.realpath(VENV_PY) \
        and not os.environ.get("VEDIT_NOREEXEC"):
    os.execv(VENV_PY, [VENV_PY, os.path.abspath(__file__), *sys.argv[1:]])
if CMD not in NO_VENV_OK and not os.path.exists(VENV_PY) and not os.environ.get("VEDIT_NOREEXEC"):
    sys.exit(f"Not set up yet: run  bash \"{os.path.join(HERE, 'setup.sh')}\"  (or set VEDIT_NOREEXEC=1 to use this Python)")


def opt(name, default=None):
    return A[A.index(name) + 1] if name in A and A.index(name) + 1 < len(A) else default


def run(cmd, env=None, quiet=False):
    print("+", " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd[:4])), "...", flush=True)
    r = subprocess.run(cmd, env=env, capture_output=quiet, text=True)
    if r.returncode:
        sys.exit(f"FAILED ({r.returncode}): {' '.join(cmd[:5])}" + (("\n" + r.stderr[-1500:]) if quiet else ""))
    return r


def P(cfg, *p): return os.path.join(cfg["_dir"], *p)


def save(cfg):
    json.dump({k: v for k, v in cfg.items() if k != "_dir"}, open(P(cfg, "project.json"), "w"), indent=1)


# ------------------------------------------------------------------ doctor
def doctor():
    ok = True
    def line(good, what, fix=""):
        nonlocal ok
        ok &= bool(good) or what.startswith("(optional)")
        print(f"  {'OK  ' if good else 'MISS'} {what}" + ("" if good else f"   -> {fix}"))
    print(f"vedit doctor  (VEDIT_HOME = {VH})")
    for b, fix in (("ffmpeg", "install ffmpeg (brew / apt / winget)"), ("ffprobe", "comes with ffmpeg"), ("node", "install Node.js 18+")):
        line(shutil.which(b), b, fix)
    line(os.path.exists(VENV_PY), ("(optional) " if os.environ.get("VEDIT_NOREEXEC") else "") + f"Python venv {VENV_PY}",
         f"bash {os.path.join(HERE, 'setup.sh')}")
    py = VENV_PY if os.path.exists(VENV_PY) else sys.executable
    for mod, fix in (("numpy", "setup.sh"), ("PIL", "setup.sh"), ("faster_whisper", "setup.sh (or pip install openai-whisper)")):
        r = subprocess.run([py, "-c", f"import {mod}"], capture_output=True)
        if mod == "faster_whisper" and r.returncode:
            r = subprocess.run([py, "-c", "import whisper"], capture_output=True)
            line(r.returncode == 0, "Whisper (faster-whisper or openai-whisper)", fix); continue
        line(r.returncode == 0, {"PIL": "Pillow"}.get(mod, mod), fix)
    r = subprocess.run([py, "-c", "import cv2,os; assert os.path.exists(cv2.data.haarcascades+'haarcascade_frontalface_alt2.xml')"], capture_output=True)
    line(r.returncode == 0, "(optional) OpenCV with face cascades (cover face check, lipsync)", "pip install opencv-python-headless==4.10.0.84")
    r = subprocess.run([py, "-c", "import noisereduce"], capture_output=True)
    line(r.returncode == 0, "(optional) noisereduce (audio.denoise)", "pip install noisereduce")
    env = project_env({})
    r = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True, env=env) if shutil.which("node") else None
    line(r is not None and r.returncode == 0, "Playwright for Node (graphics, page captures)", "setup.sh, or npm i -g playwright")
    line(FONT_NARROW, f"headline font: {FONT_NARROW}", "setup.sh fetches Barlow Condensed into " + FONTS_HOME)
    line(FONT_BOLD, f"caption/body font: {FONT_BOLD}", "setup.sh fetches Inter into " + FONTS_HOME)
    print("ready" if ok else "not ready: fix the MISS lines above")
    sys.exit(0 if ok else 1)


# ------------------------------------------------------------------ init
def _find_workspace(start):
    d = os.path.abspath(start)
    for _ in range(6):
        for cand in (os.path.join(d, "brand", "brand-profile.md"), os.path.join(d, "marketing", "brand", "brand-profile.md")):
            if os.path.exists(cand): return os.path.dirname(os.path.dirname(cand))
        d = os.path.dirname(d)
    return None


def init():
    if len(A) < 2: sys.exit(__doc__)
    slug = A[1]; raw = opt("--raw"); pack = opt("--pack"); script = opt("--script")
    if not raw or not os.path.exists(raw): sys.exit("--raw must point at the raw clip (camera A: its sound is used for the edit)")
    if pack and not script:
        script = next((os.path.join(pack, n) for n in ("script.txt", "script-main.txt", "script.md") if os.path.exists(os.path.join(pack, n))), None)
    if not script or not os.path.exists(script):
        sys.exit("give --script FILE, or --pack DIR containing script.txt (one spoken line per sentence; [notes] in brackets are ignored)")
    pack = pack or os.path.dirname(os.path.abspath(script))
    d = os.path.join(WORK, slug); os.makedirs(d, exist_ok=True)
    pj = os.path.join(d, "project.json")
    if os.path.exists(pj): sys.exit(f"{pj} already exists; edit it instead")
    title = opt("--title", os.path.basename(os.path.abspath(pack).rstrip("/\\")))
    ver = opt("--version", "v1")
    cfg = json.load(open(os.path.join(HERE, "references", "project-template.json")))
    cfg.update({"slug": slug, "title": title, "version": ver, "raw": os.path.abspath(raw), "pack": os.path.abspath(pack),
                "out_dir": os.path.abspath(opt("--out", os.path.join(pack, "video")))})
    if "--long" in A: cfg["format"] = "long"
    cams = [A[i + 1] for i, x in enumerate(A) if x == "--cam" and i + 1 < len(A)]
    cfg["cameras"] = [{"name": c.split("=", 1)[0], "raw": os.path.abspath(c.split("=", 1)[1])} for c in cams]
    for c in cfg["cameras"]:
        if not os.path.exists(c["raw"]): sys.exit(f"camera {c['name']}: no such file {c['raw']}")
    ws = opt("--workspace") or _find_workspace(pack)
    if ws:
        b = brand_from_profile(os.path.join(ws, "brand", "brand-profile.md"))
        if b:
            cfg["brand"] = {**cfg.get("brand", {}), **b}
            print("brand from", os.path.join(ws, "brand", "brand-profile.md"), "->", b)
        cfg["workspace"] = os.path.abspath(ws)
    else:
        print("no marketing workspace found: using the neutral default look (set \"brand\" in project.json, or run the brand-setup skill)")
    shutil.copy(script, os.path.join(d, "script.txt"))
    for n in ("sources.txt",):
        if os.path.exists(os.path.join(pack, n)): shutil.copy(os.path.join(pack, n), os.path.join(d, n))
    en = os.path.join(pack, "edit-notes.txt")       # HOOK ON SCREEN / COVER / OUTCOME lines from the script stage
    if os.path.exists(en):
        notes = {}
        for line in open(en, encoding="utf-8-sig"):
            if ":" in line:
                k, v = line.split(":", 1)
                notes[k.strip().lower().replace(" ", "_")] = v.strip()
        cfg["edit_notes"] = notes
        print("edit notes:", notes)
    else:
        print("no edit-notes.txt next to the script: add \"edit_notes\" (hook_on_screen, cover, outcome) to project.json by hand if you have them")
    json.dump(cfg, open(pj, "w"), indent=1)
    if not os.path.exists(os.path.join(d, "graphics.json")): json.dump([], open(os.path.join(d, "graphics.json"), "w"))
    print(f"project: {d}\n  next: put every proper name in the script into \"vocab\" (and Whisper misspellings into \"syn\"), then  vedit.py prep {slug}")


# ------------------------------------------------------------------ prep
def prep(cfg):
    raw = cfg["raw"]
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height,color_transfer:stream_side_data=rotation", "-of", "json", raw],
                                   capture_output=True, text=True).stdout)["streams"][0]
    if pr.get("color_transfer") in ("arib-std-b67", "smpte2084"):
        sys.exit("STOP: this clip is HDR (HLG/PQ). Re-shoot with HDR video turned off in the camera settings, or tone-map it "
                 "to SDR first. Converting HDR without tone-mapping gives washed-out grey footage.")
    # Call-quality audio: phones drop to 8-16 kHz when a Bluetooth mic or earbuds connect in hands-free mode. Everything above
    # 4-8 kHz is never recorded (boxy, echoey), and that audio is usually ~270 ms LATE as well. No edit can restore it.
    au = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                                    "stream=sample_rate,channels,bit_rate", "-of", "json", raw],
                                   capture_output=True, text=True).stdout).get("streams") or [{}]
    sr = int(au[0].get("sample_rate") or 0)
    if sr and sr < 32000 and not cfg.get("allow_low_audio"):
        sys.exit(f"STOP: the clip's audio is {sr} Hz ({au[0].get('channels')} ch, {int(au[0].get('bit_rate') or 0) // 1000} kbps): "
                 "phone-call quality. A Bluetooth mic or earbuds was probably connected in hands-free mode, and that audio is "
                 "usually ~270 ms late too. Re-record with a wired/lav mic or the camera's own mic; or rescue the SOURCE first "
                 "(speech enhancement, then measure and fix the offset with scripts/lipsync.py, then a fresh init: see "
                 "references/audio-and-sync.md); or set \"allow_low_audio\": true in project.json to edit it anyway.")
    W, H = frame_size(cfg)
    if "fps" not in cfg:             # keep the camera's own rate (25p cameras exist): converting 25 -> 30 judders
        def _fps(entry):   # robust: some ffprobe builds trail a comma; avg can be 0/0; VFR gives a fraction
            fr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", f"stream={entry}",
                                 "-of", "default=noprint_wrappers=1:nokey=1", raw], capture_output=True, text=True).stdout.strip().strip(",")
            m = re.match(r"\s*([0-9.]+)\s*(?:[/:]\s*([0-9.]+))?", fr)
            if not m: return 0.0
            num = float(m.group(1)); den = float(m.group(2)) if m.group(2) else 1.0
            return num / den if den else 0.0
        f = _fps("avg_frame_rate") or _fps("r_frame_rate") or 30.0
        f = f / 2 if f > 45 else f
        cfg["fps"] = min((24, 25, 30), key=lambda x: abs(x - f)); save(cfg)
        print(f"frame rate: {f:.2f} -> working at {cfg['fps']} fps")
    FPS = project_fps(cfg)
    norm = P(cfg, "norm.mp4")
    if not os.path.exists(norm):
        run(["ffmpeg", "-y", "-v", "error", "-stats", "-i", raw, "-map", "0:v:0", "-map", "0:a:0",
             "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,setsar=1,fps={FPS}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", norm])
    w, h = (int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                            "-of", "csv=p=0", norm], capture_output=True, text=True).stdout.strip().strip(",").split(",")[:2])
    if (w, h) != (W, H):
        os.remove(norm)
        sys.exit(f"the clip came out {w}x{h}, expected {W}x{H} " + ("(vertical footage: drop --long?)" if W > H else "(landscape footage? use init --long for a 16:9 long-form)"))
    wav = P(cfg, "audio.wav")
    if not os.path.exists(wav):
        run(["ffmpeg", "-y", "-v", "error", "-i", norm, "-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", wav])
    for c in cfg.get("cameras", []):                     # extra cameras: same size/rate, then line up by sound
        if cfg.get("sync", {}).get(c["name"], {}).get("method") in ("motion", "manual"): continue   # silent camera / hand-made crop
        cn = P(cfg, f"cam_{c['name']}.mp4"); cw = P(cfg, f"cam_{c['name']}.wav")
        if not os.path.exists(cn):
            run(["ffmpeg", "-y", "-v", "error", "-stats", "-i", c["raw"], "-map", "0:v:0", "-an",
                 "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", cn])
        if not os.path.exists(cw):
            run(["ffmpeg", "-y", "-v", "error", "-i", c["raw"], "-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", cw])
        sr_ = subprocess.run([sys.executable, os.path.join(SCRIPTS, "sync_cams.py"), wav, cw], capture_output=True, text=True)
        try: res = json.loads((sr_.stdout or sr_.stderr or "{}").strip().splitlines()[-1])
        except (ValueError, IndexError): res = {"error": (sr_.stderr or "sync failed")[-300:]}
        cfg.setdefault("sync", {})[c["name"]] = res; save(cfg)
        # untrusted: an error, a weak exact match, or a weak whole-recording envelope match that the exact match doesn't
        # overrule (a raw-audio match of 0.5+ is strong evidence on its own, e.g. on short clips)
        if "error" in res or res.get("confidence", 0) < 0.12 or (res.get("envelope_peak", 0) < 6 and res.get("confidence", 0) < 0.5):
            print(f"camera {c['name']}: SYNC NOT TRUSTED {res}. It will be left out of the cut; it needs clear sound of the presenter.")
        else:
            print(f"camera {c['name']}: in sync, starts {res['b']:+.3f}s vs A, drift {(res['a'] - 1) * 1e6:+.0f} ppm, covers A {res['covers'][0]:.1f}-{res['covers'][1]:.1f}s")
            if res.get("max_residual_ms", 0) > 20: print(f"  note: windows disagree by {res['max_residual_ms']} ms; check lip sync on camera {c['name']} shots")
    env = project_env(cfg)
    for model, out in (("large-v3", "tr_large.json"), ("medium.en", "tr_medium.json")):
        if not os.path.exists(P(cfg, out)):
            print(f"transcribing with {model} (roughly 1-2x the clip length on a laptop CPU)...", flush=True)
            run([sys.executable, os.path.join(SCRIPTS, "transcribe_v.py"), wav, P(cfg, out), model], env=env, quiet=True)
    print("prep done:", norm, f"\n  next: vedit.py takes {cfg['slug']}")


# ------------------------------------------------------------------ takes / picker
def _picker_meta(cfg):
    json.dump({"title": cfg.get("title", cfg["slug"])}, open(P(cfg, "picker", "meta.json"), "w"))


def takes(cfg):
    env = project_env(cfg); pk = P(cfg, "picker"); os.makedirs(pk, exist_ok=True)
    run([sys.executable, os.path.join(SCRIPTS, "align_takes.py"), P(cfg, "tr_large.json"), P(cfg, "script.txt"), P(cfg, "audio.wav"), pk,
         P(cfg, "tr_medium.json")], env=env)
    run([sys.executable, os.path.join(SCRIPTS, "relisten.py"), os.path.join(pk, "takes.json"), P(cfg, "audio.wav")], env=env)
    run([sys.executable, os.path.join(SCRIPTS, "make_clips.py"), os.path.join(pk, "takes.json"), P(cfg, "norm.mp4"), pk,
         "960:540" if cfg.get("format") == "long" else "540:960"], env=env)
    shutil.copy(os.path.join(SCRIPTS, "picker", "index.html"), os.path.join(pk, "index.html")); _picker_meta(cfg)
    print(open(os.path.join(pk, "takes_report.txt")).read()[-3000:])
    print(f"\nnext: vedit.py picker {cfg['slug']}   (in the background), or write picker/picks.json yourself if asked to pick")


def picker(cfg):
    port = opt("--port", "8765")
    shutil.copy(os.path.join(SCRIPTS, "picker", "index.html"), P(cfg, "picker", "index.html")); _picker_meta(cfg)
    os.execv(sys.executable, [sys.executable, os.path.join(SCRIPTS, "picker_server.py"), P(cfg, "picker"), port])


# ------------------------------------------------------------------ build / captions / gate
def build(cfg):
    stage = A[2] if len(A) > 2 and not A[2].startswith("--") else "all"
    extra = ["--until", opt("--until")] if opt("--until") else []
    if stage in ("cut", "mg", "caps", "final", "all") and not os.path.exists(P(cfg, "picker", "picks.json")):
        print("WARNING: no picks.json yet: building from MACHINE picks (preview only, deliver will refuse this)")
    run([sys.executable, os.path.join(SCRIPTS, "build.py"), cfg["_dir"], stage, *extra], env=project_env(cfg))


def captions(cfg):
    rep, srt = P(cfg, "build", "caption_check.txt"), P(cfg, "build", "final.srt")
    if not os.path.exists(rep): sys.exit(f"no caption check yet: run  vedit.py build {cfg['slug']} caps")
    print(open(rep).read())
    if os.path.exists(srt):
        n = sum(1 for l in open(srt, encoding="utf-8") if "-->" in l)
        print(f"SRT: {srt} ({n} captions). FIX = misheard and corrected to the script; REWORD = said differently, kept; CHECK = listen.")


def gate(cfg):
    v = P(cfg, "build", "final.mp4")
    if not os.path.exists(v): sys.exit("no build/final.mp4 yet")
    rep = P(cfg, "build", "qa", "qa_report.txt"); t0 = __import__("time").time()
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "qa_gate.py"), v, P(cfg, "script.txt"), P(cfg, "build", "qa")], env=project_env(cfg))
    if not os.path.exists(rep) or os.path.getmtime(rep) < t0:          # the words gate crashed: never leave an old PASS behind
        os.makedirs(os.path.dirname(rep), exist_ok=True)
        open(rep, "w").write("FAIL — the words gate did not complete (see the error above; is a Whisper model available?)\n")
    # the words gate can't hear a clipped word-tail or a start inside a word: check every audio cut lands in quiet
    c = subprocess.run([sys.executable, os.path.join(SCRIPTS, "cut_check.py"), cfg["_dir"]], capture_output=True, text=True, env=project_env(cfg))
    print(c.stdout, end="")
    body = open(rep).read() if os.path.exists(rep) else ""
    open(rep, "w").write(("FAIL — audio cut check (a cut lands on sound)\n" + c.stdout + "\n" + body) if c.returncode else (body.rstrip("\n") + "\n" + c.stdout))
    sys.exit(r.returncode or c.returncode)


# ------------------------------------------------------------------ frames / cover / graphics
def frames(cfg):
    from PIL import Image, ImageDraw, ImageFont
    cd = P(cfg, "cover"); os.makedirs(cd, exist_ok=True)
    every = opt("--every")
    if every:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", P(cfg, "norm.mp4")],
                                   capture_output=True, text=True).stdout.strip().strip(","))
        ts = [round(x * float(every), 2) for x in range(int(dur // float(every)) + 1)]
    else:
        ts = [float(x) for x in A[2:]]
    tw, th = (480, 270) if cfg.get("format") == "long" else (270, 480)
    tiles = []
    for t in ts:
        f = os.path.join(cd, f"f_{t:.2f}.png")
        if not os.path.exists(f):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", P(cfg, "norm.mp4"), "-frames:v", "1", f])
        if os.path.exists(f): tiles.append((t, Image.open(f).convert("RGB").resize((tw, th))))
    if not tiles: sys.exit("no frames grabbed")
    cols = 5 if tw > th else 8; rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 4), rows * (th + 32)), "white"); d = ImageDraw.Draw(sheet)
    F = ImageFont.truetype(FONT_BOLD, 22) if FONT_BOLD else ImageFont.load_default()
    for i, (t, im) in enumerate(tiles):
        x, y = (i % cols) * (tw + 4), (i // cols) * (th + 32); sheet.paste(im, (x, y)); d.text((x + 6, y + th + 4), f"{t:.2f}s", font=F, fill="black")
    out = os.path.join(cd, "frames_sheet.jpg"); sheet.save(out, quality=88); print("contact sheet:", out)


def cover(cfg):
    from PIL import Image
    cv = cfg.get("cover") or {}
    if not cv.get("variants"): sys.exit('project.json "cover" needs "frame" (raw seconds) and "variants"')
    cd = P(cfg, "cover"); os.makedirs(cd, exist_ok=True)
    rc = 0; made = []
    for name, spec in cv["variants"].items():
        t = spec.get("frame", cv.get("frame"))
        if t is None: sys.exit(f'cover variant {name}: no "frame" time (raw seconds of camera A)')
        cam = spec.get("camera", "A"); src = P(cfg, "norm.mp4") if cam == "A" else P(cfg, f"cam_{cam}.mp4")
        ts = t if cam == "A" else cfg["sync"][cam]["a"] * t + cfg["sync"][cam]["b"]      # frame times are camera-A times
        fr = os.path.join(cd, f"f_{cam}_{t:.2f}.png")
        if not os.path.exists(fr):
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ts:.3f}", "-i", src, "-frames:v", "1", fr])
        vj = os.path.join(cd, f"variant_{name}.json")
        json.dump({"reframe": cv.get("reframe", {}), "format": cfg.get("format", "short"),
                   "unbranded": cv.get("unbranded", False), "wordmark": cv.get("wordmark"),
                   "brand": brand(cfg), "face_x": (cfg.get("framing") or {}).get("face_x"), **spec}, open(vj, "w"))
        out = os.path.join(cd, f"cover_{name}.png")
        print(f"cover {name}:")
        rc |= subprocess.run([sys.executable, os.path.join(SCRIPTS, "cover_designer.py"), fr, vj, out]).returncode
        if os.path.exists(out):
            Image.open(out).convert("RGB").save(out[:-4] + ".jpg", quality=92); made.append(out)
    if made:   # what the viewer sees small: shorts = the centre 1:1 square of the profile grid; long-form = a search thumbnail
        tiles = [Image.open(m).convert("RGB").resize((360, 203)) if cfg.get("format") == "long"
                 else Image.open(m).convert("RGB").crop((0, 420, 1080, 1500)).resize((360, 360)) for m in made]
        sheet = Image.new("RGB", (len(tiles) * 370, tiles[0].size[1]), "white")
        for i, t in enumerate(tiles): sheet.paste(t, (i * 370, 0))
        sheet.save(os.path.join(cd, "grid_tiles.jpg"), quality=90)
        print("covers:", made, "| grid preview:", os.path.join(cd, "grid_tiles.jpg"))
    sys.exit(rc)


def _brand_json(cfg, path):
    if cfg.get("brand"):
        b = brand(cfg)
        json.dump({"accent": b["accent"], "primary": b["primary"], "ink": b["ink"], "panel": b.get("panel"),
                   "panel2": b.get("panel2"), "chip_text": b.get("chip_text"), "head_ttf": b["head_ttf"], "body_ttf": b["body_ttf"]}, open(path, "w"))
    elif os.path.exists(path):
        os.remove(path)


def mg_preview(cfg):
    from PIL import Image
    specs = json.load(open(P(cfg, cfg.get("graphics", "graphics.json"))))
    if not specs: sys.exit("graphics.json is empty: nothing to preview")
    for s in specs: s.setdefault("dur", 4.0)
    sp = P(cfg, "build", "mg_preview_specs.json"); os.makedirs(P(cfg, "build"), exist_ok=True); json.dump(specs, open(sp, "w"))
    _brand_json(cfg, P(cfg, "build", "brand.json"))
    pd = P(cfg, "build", "mg_preview"); shutil.rmtree(pd, ignore_errors=True)
    run(["node", os.path.join(SCRIPTS, "mg", "mg_render.js"), sp, pd, "preview"], env=project_env(cfg))
    pngs = sorted(glob.glob(os.path.join(pd, "*.png")))
    cols = 6; rows = (len(pngs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 274, max(1, rows) * 490), (40, 40, 40))
    for i, p in enumerate(pngs):
        base = Image.new("RGBA", (1080, 1920), (90, 96, 92, 255))
        base.alpha_composite(Image.open(p).convert("RGBA"))
        sheet.paste(base.convert("RGB").resize((270, 480)), ((i % cols) * 274, (i // cols) * 490))
    out = os.path.join(pd, "_sheet.jpg"); sheet.save(out, quality=88); print("graphics sheet:", out)


def capture():
    if len(A) < 3: sys.exit("usage: vedit.py capture <url> <out.png> [phrase ...]")
    run(["node", os.path.join(SCRIPTS, "mg", "capture_page.js"), A[1], A[2], *A[3:]], env=project_env({}))


def broll_scroll():
    """A 6 s vertical scroll through a page capture, filed into the B-roll library with an index row."""
    if len(A) < 5: sys.exit("usage: vedit.py broll-scroll <capture.png> <stem> <y0> <y1> --desc D --tags T --url U [--root DIR]")
    png, stem, y0, y1 = A[1], A[2], int(A[3]), int(A[4])
    desc, tags, url = opt("--desc"), opt("--tags"), opt("--url")
    root = os.path.expanduser(opt("--root") or os.environ.get("VEDIT_BROLL") or "")
    if not (desc and tags and url): sys.exit("--desc, --tags and --url are required (the library index needs them)")
    if not root: sys.exit("say where the B-roll library is: --root DIR (or set VEDIT_BROLL); use the project's broll_root")
    day = datetime.date.today().strftime("%Y%m%d")
    rel = os.path.join("screen-captures", f"{stem}_{day}_v916.mp4"); out = os.path.join(root, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True); tmp = out + ".part.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", png, "-t", "6",
         "-vf", f"crop=1080:1920:0:'{y0}+({y1}-{y0})*(min(t/4.2,1)*min(t/4.2,1)*(3-2*min(t/4.2,1)))',format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", "30", "-movflags", "+faststart", tmp])
    os.replace(tmp, out)
    idx = os.path.join(root, "broll-index.csv")
    F = ["id", "file", "description", "tags", "duration_s", "orientation", "resolution", "source", "licence", "licence_proof",
         "people_in_shot", "consent", "contains_text_or_brands", "date_added"]
    rows = list(csv.DictReader(open(idx))) if os.path.exists(idx) else []
    if rows: F = list(rows[0].keys())
    nid = 1 + max([int(r["id"]) for r in rows if str(r.get("id", "")).isdigit()] or [0])
    rows.append({k: "" for k in F} | {"id": str(nid), "file": rel.replace(os.sep, "/"), "description": desc, "tags": tags,
                 "duration_s": "6.0", "orientation": "vertical", "resolution": "1080x1920",
                 "source": "public web page (headless browser capture)",
                 "licence": "Public page: credit the source on screen; check reuse terms before paid promotion",
                 "licence_proof": url, "people_in_shot": "none", "consent": "n/a", "contains_text_or_brands": "yes: page text",
                 "date_added": day})
    with open(idx + ".part", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=F, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    os.replace(idx + ".part", idx)
    print("B-roll:", out, "| indexed as id", nid, "| cue path:", rel.replace(os.sep, "/"))


# ------------------------------------------------------------------ deliver / release / status
def cutlist(cfg, qa_head):
    edl = json.load(open(P(cfg, "build", "edl.json"))); T = json.load(open(P(cfg, "picker", "takes.json")))
    picks = json.load(open(P(cfg, "picker", "picks.json")))
    kept = {u["sid"]: u for u in edl["units"]}
    L = [f"# {cfg['title']} — {cfg['version']} cut list", "",
         f"Runtime {edl['total']:.1f}s · {len(kept)} of {len(T['sentences'])} script lines kept · {len(edl['pieces'])} shots · QA gate: {qa_head}", "",
         "| Line | Take | Source (raw s) | Trims inside the take | Script |", "|---|---|---|---|---|"]
    for s in T["sentences"]:
        u = kept.get(s["sid"]); txt = s["text"].replace("|", "/")
        if not u: L.append(f"| L{s['sid'] + 1} | skipped | | | {txt} |"); continue
        tr = "; ".join(f"{c['from']:.2f}–{c['to']:.2f} “{c['words'][:40]}”" for c in u["trims"]) or ""
        L.append(f"| L{s['sid'] + 1} | {u['take']} of {len(s['takes'])} | {u['a']:.2f}–{u['b']:.2f} | {tr} | {txt} |")
    notes = [(int(k), v["note"]) for k, v in picks.items() if v.get("note")]
    if notes:
        L += ["", "## Changes made to the picks (and why)", ""] + [f"- **L{k + 1}**: {n}" for k, n in sorted(notes)]
    return "\n".join(L) + "\n"


def deliver(cfg):
    out = cfg["out_dir"]; b = P(cfg, "build")
    v, rep = os.path.join(b, "final.mp4"), os.path.join(b, "qa", "qa_report.txt")
    if not os.path.exists(v): sys.exit("no build/final.mp4")
    if not os.path.exists(P(cfg, "picker", "picks.json")): sys.exit("REFUSED: built from machine picks; nobody has confirmed the takes")
    head = open(rep).readline().strip() if os.path.exists(rep) else "NOT RUN"
    stale = not os.path.exists(rep) or os.path.getmtime(rep) < os.path.getmtime(v)
    if (stale or not head.startswith("PASS")) and "--force" not in A:
        sys.exit(f"REFUSED: QA gate is '{head}'{' (older than the render)' if stale else ''}. Run vedit.py gate, fix, rebuild.")
    os.makedirs(out, exist_ok=True)
    base = f"{cfg['title']} - {cfg['version']}"
    files = [(v, f"{base}.mp4"), (os.path.join(b, "final.srt"), f"{base}.srt"), (rep, f"{cfg['version']}-QA-gate-report.txt"),
             (P(cfg, "picker", "picks.json"), f"{cfg['version']}-picks.json")]
    if os.path.exists(os.path.join(b, "chapters.txt")):         # long-form: paste into the YouTube description
        files.append((os.path.join(b, "chapters.txt"), f"{cfg['version']}-youtube-chapters.txt"))
    lead = (cfg.get("cover") or {}).get("lead", "A")
    for cpng in sorted(glob.glob(P(cfg, "cover", "cover_*.png"))):
        n = os.path.basename(cpng)[6:-4]
        for ext in (".png", ".jpg"):
            src = cpng[:-4] + ext
            if os.path.exists(src): files.append((src, f"{cfg['title']} - Cover{'' if n == lead else f' {n} (alt)'}{ext}"))
    lj = P(cfg, "cover", f"cover_{lead}.jpg")
    if os.path.exists(lj): files.append((lj, f"{base}.jpg"))   # thumbnail with the SAME filename as the video
    for src, name in files:
        if not os.path.exists(src): continue
        dst = os.path.join(out, name); shutil.copyfile(src, dst + ".part"); os.replace(dst + ".part", dst)
    cl = os.path.join(out, f"{cfg['version']}-cutlist.md"); open(cl + ".part", "w").write(cutlist(cfg, head)); os.replace(cl + ".part", cl)
    print("delivered to", out); [print("  ", n) for s, n in files if os.path.exists(s)]; print("  ", os.path.basename(cl))
    print("NOTHING is scheduled or posted by this tool.")


def release(cfg):
    """Copy the delivered video + SRT + lead thumbnail into a posting folder under ONE filename (what schedulers and
    YouTube expect: same-name captions and thumbnail travel with the video)."""
    r = cfg.get("release") or {}
    dst_dir = opt("--to") or r.get("dir")
    if not dst_dir: sys.exit("usage: vedit.py release <slug> --to '<posting folder>' [--name '<date - title>']  (remembered in project.json)")
    name = opt("--name") or r.get("name") or os.path.basename(dst_dir.rstrip("/\\"))
    out = cfg["out_dir"]; base = f"{cfg['title']} - {cfg['version']}"
    src = {ext: os.path.join(out, f"{base}{ext}") for ext in (".mp4", ".srt", ".jpg")}
    missing = [os.path.basename(s) for s in src.values() if not os.path.exists(s)]
    if missing: sys.exit(f"deliver first: missing {missing} in {out}")
    os.makedirs(dst_dir, exist_ok=True)
    for ext, s in src.items():
        d = os.path.join(dst_dir, name + ext); shutil.copyfile(s, d + ".part"); os.replace(d + ".part", d); print("  ", name + ext)
    cfg["release"] = {"dir": dst_dir, "name": name, "version": cfg["version"]}; save(cfg)
    print("released", cfg["version"], "to", dst_dir, "\nNOTHING is scheduled or posted by this tool.")


def status(cfg):
    for f in ["norm.mp4", "audio.wav", "tr_large.json", "tr_medium.json", "picker/takes.json", "picker/picks.json",
              "build/edl.json", "build/cues.json", "build/cut.mp4", "build/final.mp4", "build/qa/qa_report.txt"]:
        print(f"  {'✓' if os.path.exists(P(cfg, f)) else '·'} {f}")
    rep = P(cfg, "build", "qa", "qa_report.txt")
    if os.path.exists(rep): print("  gate:", open(rep).readline().strip())
    if os.path.exists(P(cfg, "picker", "picks.json")) and os.path.exists(P(cfg, "picker", "takes.json")):
        pk = json.load(open(P(cfg, "picker", "picks.json"))); n = len(json.load(open(P(cfg, "picker", "takes.json")))["sentences"])
        print(f"  picks: {sum(1 for v in pk.values() if v.get('confirmed'))}/{n} confirmed")


if __name__ == "__main__":
    if CMD in (None, "-h", "--help", "help"): print(__doc__); sys.exit(0)
    if CMD == "doctor": doctor()
    elif CMD == "init": init()
    elif CMD == "capture": capture()
    elif CMD == "broll-scroll": broll_scroll()
    else:
        fn = {"prep": prep, "transcribe": prep, "takes": takes, "picker": picker, "build": build, "captions": captions,
              "gate": gate, "frames": frames, "cover": cover, "mg-preview": mg_preview, "deliver": deliver,
              "release": release, "status": status}.get(CMD)
        if not fn: sys.exit(__doc__)
        if len(A) < 2: sys.exit(f"usage: vedit.py {CMD} <slug>")
        fn(load_project(A[1]))
