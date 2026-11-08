#!/usr/bin/env python3
"""Assemble the edit from the take picker's picks. Everything video-specific comes from the
project's project.json + graphics.json (see references/project-config.md).

stages:  plan  -> build/edl.json   pieces, framing, output-time word map, units
         cues  -> build/cues.json  graphics + B-roll anchored to lines/words (output time)
         cut   -> build/cut.mp4    talking head with framing changes + de-click fades at hard cuts
         mg    -> build/mg/*.mov   graphics rendered to exact durations (alpha ProRes 4444)
         caps  -> build/caps/*.png + build/final.srt  (captioned from the CUT's own audio)
         final -> build/final.mp4  B-roll + graphics + captions + cover poster frame, -14 LUFS
usage: build.py <project_dir> <plan|cues|cut|mg|caps|final|all> [--until SECONDS]
"""
import sys as _sys
if len(_sys.argv) < 2 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcommon import SCRIPTS, FONT_BOLD, load_project, project_env, frame_size, project_fps, brand, hex2rgb

CFG = load_project(sys.argv[1])
STAGE = sys.argv[2] if len(sys.argv) > 2 else "all"
UNTIL = float(sys.argv[sys.argv.index("--until") + 1]) if "--until" in sys.argv else None
PD = CFG["_dir"]
NORM = os.path.join(PD, "norm.mp4")
AUDIO = os.path.join(PD, "audio.wav")
TR_LARGE = os.path.join(PD, "tr_large.json")          # verbatim large-v3: primary word timings
TR_MED = os.path.join(PD, "tr_medium.json")           # medium.en: fills the words large-v3 drops
TAKES = os.path.join(PD, "picker", "takes.json")
PICKS = os.path.join(PD, "picker", "picks.json")
OUTD = os.path.join(PD, "build"); os.makedirs(OUTD, exist_ok=True)
GFX = os.path.join(PD, CFG.get("graphics", "graphics.json"))
BROLL = os.path.expanduser(CFG.get("broll_root") or "")
FD = 0.012                                            # de-click fade at hard cuts
W, H = frame_size(CFG); FPS = project_fps(CFG); LONG = CFG.get("format") == "long"
FR = {"face_x": W // 2, "eye_y": 430 if LONG else 900, "zoom": 1.14, **CFG.get("framing", {})}
# extra cameras that synced cleanly: [{"name": "B", "file": cam_B.mp4, "a": .., "b": .., "covers": [..]}]
CAMS = [{"name": c["name"], "file": os.path.join(PD, f"cam_{c['name']}.mp4"), **CFG["sync"][c["name"]]}
        for c in CFG.get("cameras", []) if c.get("name") in CFG.get("sync", {}) and "error" not in CFG["sync"][c["name"]]
        and os.path.exists(os.path.join(PD, f"cam_{c['name']}.mp4"))]
EXIT_TAIL = CFG.get("exit_tail")                      # [a, b] raw seconds of the soft exit (empty frame), or null
KEEP_PAUSE = [tuple(x) for x in CFG.get("build", {}).get("keep_pause", [])]   # source-time [a,b] ranges whose interior pause must NOT be trimmed
                                                      # (a soft word at the pause edge got clipped: "today. [pause] Look at" lost "Look at")

def sh(cmd, env=None):
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode: sys.exit("FAILED: " + " ".join(cmd[:6]) + "\n" + r.stderr[-1500:])
    return r

def words_of(path): return [w for sg in json.load(open(path))["segments"] for w in sg["words"]]

def silences(d, noise=-30):
    sd = subprocess.run(["ffmpeg", "-v", "info", "-i", AUDIO, "-af", f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    return [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([\d.]+)", sd), re.findall(r"silence_end: ([\d.]+)", sd))]

# ======================= PLAN =======================
def plan():
    D = json.load(open(TAKES))
    P = json.load(open(PICKS)) if os.path.exists(PICKS) else {}
    using_auto = not P
    segs = []                                    # one per kept script unit
    for s in D["sentences"]:
        p = P.get(str(s["sid"]))
        n = (p["take"] if p else (s["auto"] + 1 if s["auto"] is not None else 0))
        if not n or not s["takes"]: continue
        t = s["takes"][n - 1]
        def keep(ci, c):                      # explicit tick/untick wins; else the proposal's default
            ex = (p or {}).get("trims", {}).get(str(ci))
            return ex if ex is not None else c.get("default", True)
        trims = [c for ci, c in enumerate(t["inner_cuts"]) if keep(ci, c)]
        segs.append({"sid": s["sid"], "text": s["text"], "take": n, "run": t["run"],
                     "a": t["in"] + (p["nin"] if p else 0), "b": t["out"] + (p["nout"] if p else 0), "trims": trims})
    W, WM = words_of(TR_LARGE), words_of(TR_MED)
    U_ = sorted(W + WM, key=lambda w: w["start"])
    # ---- safe out-points: never cut inside the last word's tail ----
    # Soft endings (-ing, -s, -ty) keep sounding well below -30 dB: one early edit had six clipped words
    # that all sat inside a -30 dB "silence", and Whisper's word-ends ran 0.1-0.5 s early. So a tail ends at the first
    # DEEP quiet after the word (-45 dB), or -38 / -30 dB where outdoor background never gets that low before the next speech.
    TAIL = [silences(0.12, -45), silences(0.12, -38), silences(0.15, -30)]
    QIN = silences(0.04, -45)                     # short quiet patches: where a resume after a trimmed pause can start clean
    def tail_end(w_end, limit):
        for S in TAIL:
            if any(a < w_end - 0.10 and b > w_end for a, b in S): return w_end          # Whisper's end is already in quiet
            on = next((a for a, b in S if a >= w_end - 0.10), None)
            if on is not None and (limit is None or on < limit - 0.10): return on
        return None
    for sg in segs:
        inside = [w for w in U_ if sg["a"] <= w["start"] < sg["b"] - 0.02]
        if not inside: continue
        lw = max(inside, key=lambda w: w["start"])
        pe = min(lw["end"], lw["start"] + 0.9)                                  # Whisper's word-end (often early)
        nxt = next((w["start"] for w in U_ if w["start"] > lw["start"] + 0.25), None)
        ss = tail_end(pe, nxt)                                                   # where the sound has really died away
        target = (max(pe, ss) if ss is not None else pe) + 0.10                 # cut after the tail, then a short beat
        target = max(target, lw["start"] + 0.3)
        if nxt is not None: target = min(target, nxt - 0.05)                    # don't run into the next speech
        if target > sg["b"]: sg["b"] = round(target, 3)
    # merge script units read in one breath (same run, contiguous in raw time) -> never re-play audio
    groups = []
    for sg in segs:
        g = groups[-1] if groups else None
        # same read, close together: play it continuously (a cut there can only clip a tail: "exis(t)"). Longer
        # same-run pauses still merge up to 0.85 s; anything longer is shortened by the pause-trim below.
        if g and sg["run"] == g["run"] and -3.0 <= sg["a"] - g["b"] <= 0.85:
            g["b"] = max(g["b"], sg["b"]); g["sids"].append(sg["sid"]); g["trims"] += sg["trims"]
        else:
            groups.append({"run": sg["run"], "a": sg["a"], "b": sg["b"], "sids": [sg["sid"]], "trims": list(sg["trims"])})
    ranges = []                                   # group minus inner trims; hard cut before every range
    for g in groups:
        cur = g["a"]
        for c in sorted(g["trims"], key=lambda c: c["from"]):
            if c["from"] >= g["b"] or c["to"] <= cur: continue   # trim outside the kept range (e.g. past a pulled-in out-point): ignore it, never let it extend the range
            if c["from"] > cur + 0.05: ranges.append({"a": cur, "b": c["from"], "sids": g["sids"]})
            cur = max(cur, c["to"])
        if g["b"] > cur + 0.05: ranges.append({"a": cur, "b": g["b"], "sids": g["sids"]})
    # trim long interior pauses (cut lands in the silence, keeps a natural ~0.35s beat)
    sil = silences(0.3); split = []
    for r in ranges:
        cur = r["a"]
        for a, b in sil:
            if a > r["a"] + 0.3 and b < r["b"] - 0.3 and b - a > 0.85:
                if any(pa < b and a < pb for pa, pb in KEEP_PAUSE): continue    # hand-protected pause (soft word at its edge)
                # where the word before the pause has really died away (-45, else -38). If the pause is too short to reach that
                # with room to spare, LEAVE IT: a natural pause beats a clipped soft tail ("exis(t)")
                don = next((x for lv in (0, 1) for x, y in TAIL[lv] if a - 0.05 <= x < b - 0.35), None)
                if don is None: continue
                cut = max(a + 0.18, don + 0.10)
                if cut > b - 0.35: continue
                # a SOFT word inside the "pause" ("story, [it's] just not the point": 'it's' never rose above
                # -30 dB, the resume landed after it and the gate heard the line skip a word): resume just before that word.
                # Only a word well inside (0.3 s+ before the pause ends): Whisper often starts the NEXT word a little early,
                # and counting those stopped almost every pause trim (one edit grew 17 s).
                # Whisper often times the NEXT words early (a whole phrase can sit 0.4 s inside the pause over dead quiet), so a
                # word only counts with real SOUND under it: a break in the -45 dB quiet ("it's": sound 240.31-240.34, between
                # quiet 239.60-240.31 and 240.34-240.47; pause ends 240.48).
                def sound_in(x0, x1):
                    qs = sorted((x, y) for x, y in QIN if y > x0 and x < x1)
                    if not qs: return True
                    edge = x0
                    for x, y in qs:
                        if x - edge >= 0.02: return True
                        edge = max(edge, y)
                    return x1 - edge >= 0.02
                soft = min((w["start"] for w in U_ if cut + 0.1 < w["start"] < b - 0.3
                            and sound_in(max(cut + 0.1, w["start"] - 0.15), min(b - 0.12, w["start"] + 0.3))), default=None)
                if soft is not None and soft - 0.08 < cut + 0.15: continue          # nothing left worth trimming
                pend = soft - 0.08 if soft is not None else None
                if pend is not None:
                    sw = next((w for w in U_ if abs(w["start"] - soft) < 1e-6), {"word": "?"})
                    print(f"  pause {a:.2f}-{b:.2f}: soft word '{sw['word'].strip()}' at {soft:.2f} kept (resume {pend:.2f})")
                split.append({"a": cur, "b": cut, "sids": r["sids"]}); cur = b - 0.17
                # resume at the start of the LAST quiet patch before the next word, not on a breath. A breath
                # can sit right up to the word, so the patch needn't reach it (e.g. patch 98.83-98.91, word at 98.92)
                q = max(((x, y) for x, y in QIN if cut + 0.05 < x <= b + 0.02 and x > cur - 0.6), default=None)
                if q: cur = round(q[0] + 0.01, 3)
                if pend is not None: cur = round(min(cur, pend), 3)
        split.append({"a": cur, "b": r["b"], "sids": r["sids"]})
    ranges = split
    # soft exit: let the last line breathe (~0.45s after the last word), then the empty-frame tail to fade over
    if ranges:
        last_word_end = max((w["start"] + min(0.6, w["end"] - w["start"]) for w in W if w["start"] < ranges[-1]["b"]), default=ranges[-1]["b"])
        ranges[-1]["b"] = max(ranges[-1]["b"], round(last_word_end + 0.45, 3))
        if EXIT_TAIL: ranges.append({"a": EXIT_TAIL[0], "b": EXIT_TAIL[1], "sids": []})
    # breathing room: a cut right at the edge of a silence moves INTO the silence (only ever extends)
    for r in ranges:
        for a_, b_ in sil:
            if r["b"] - 0.12 <= a_ <= r["b"] + 0.05: r["b"] = max(r["b"], round(a_ + min(0.15, (b_ - a_) / 2), 3))
            if r["a"] - 0.05 <= b_ <= r["a"] + 0.12:
                na = round(b_ - min(0.12, (b_ - a_) / 2), 3)
                # only into real quiet: a -30 dB "silence" can hold a breath that this pull-back would start on
                if any(x <= na <= y for x, y in QIN): r["a"] = min(r["a"], na)
    # hard guard: no two ranges may overlap in source time (that would repeat speech)
    for prev, r in zip(ranges, ranges[1:]):
        if prev["a"] <= r["a"] < prev["b"]: r["a"] = prev["b"]
    ranges = [r for r in ranges if r["b"] - r["a"] > 0.1]
    # reframes inside long ranges, at a line boundary, roughly every 6-9 s; framing alternates on every cut
    unit_start = {sg["sid"]: sg["a"] for sg in segs}
    pieces = []; shot = 0
    cycle = [("A", 0), ("A", 1)] if not CAMS else [("A", 0), (CAMS[0]["name"], 0), ("A", 1), (CAMS[0]["name"], 0)] + [(c["name"], 0) for c in CAMS[1:]]
    def covered(cam, a, b):
        c = next((c for c in CAMS if c["name"] == cam), None)
        return c is not None and c["covers"][0] + 0.05 <= a and b <= c["covers"][1] - 0.05
    # per-line camera calls (picks "cam"): the presenter turns to camera B for some lines: show the camera they
    # is talking to. When any line has a call, lines without one stay on camera A (wide/tight alternating), never a blind B cycle.
    FORCE = {int(k): v["cam"] for k, v in P.items() if isinstance(v, dict) and v.get("cam")} if CAMS else {}
    # MEASURED calls (optional gaze.json from any head-direction tool: "if the subject is not looking at the main camera there is a good chance they
    # are talking to a different one"): show the camera he faces, cutting at the turn itself. A hand call (picks "cam") still
    # wins for its line. Glances under 1 s don't switch; moments with no reading keep the camera before them.
    GZ = None
    if CAMS:
        gp = os.path.join(PD, "gaze.json")
        if os.path.exists(gp): GZ = json.load(open(gp))
    def gaze_runs(a, b):
        """[(start, end, cam)] over raw [a, b]: the camera he faces, runs under 1 s folded into their neighbours."""
        if not GZ: return [(a, b, "A")]
        f, k0, k1 = GZ["facing"], int(a * GZ["fps"]), int(b * GZ["fps"]) + 1
        seq, last = [], next((x for x in reversed(f[max(0, k0 - 8):k0]) if x), "A")
        for k in range(k0, min(k1, len(f))):
            last = f[k] or last; seq.append(last)
        # majority over 1.25 s (ties -> A): half-second glances at B while talking to A don't count
        sm = []
        for k in range(len(seq)):
            w = seq[max(0, k - 2):k + 3]; top = max(set(w), key=lambda c: (w.count(c), c == "A")); sm.append(top)
        runs = []
        for k, c in enumerate(sm):
            t = max(a, (k0 + k) / GZ["fps"])
            if runs and runs[-1][2] == c: runs[-1][1] = t + 1 / GZ["fps"]
            else: runs.append([t, t + 1 / GZ["fps"], c])
        while len(runs) > 1:                       # fold the shortest run under 1 s into its longer neighbour
            i = min(range(len(runs)), key=lambda i: runs[i][1] - runs[i][0])
            if runs[i][1] - runs[i][0] >= 1.0: break
            nb = [j for j in (i - 1, i + 1) if 0 <= j < len(runs)]
            j = max(nb, key=lambda j: runs[j][1] - runs[j][0])
            runs[j][0], runs[j][1] = min(runs[j][0], runs[i][0]), max(runs[j][1], runs[i][1]); del runs[i]
            for q in range(len(runs) - 1, 0, -1):
                if runs[q][2] == runs[q - 1][2]: runs[q - 1][1] = runs[q][1]; del runs[q]
        if not runs: return [(a, b, "A")]
        runs[0][0] = a; runs[-1][1] = b
        for i in range(len(runs) - 1): runs[i][1] = runs[i + 1][0]
        return [tuple(x) for x in runs]
    a_tight = 0
    for r in ranges:
        sids = sorted((s for s in r["sids"] if unit_start.get(s) is not None), key=lambda s: unit_start[s])
        GR = gaze_runs(r["a"], r["b"])
        def call(t):                               # the camera for raw time t: the line's hand call, else the measured one
            on = [s for s in sids if unit_start[s] <= t + 0.05]
            sid = on[-1] if on else (sids[0] if sids else -1)
            if sid in FORCE: return FORCE[sid]
            return next((c for x, y, c in GR if x <= t < y), GR[-1][2])
        cuts = [r["a"]]
        if FORCE or GZ:                            # cut where the camera changes: at a hand-called line's start, or at the turn
            for s in sids:
                ta = unit_start[s]
                if r["a"] + 0.4 < ta < r["b"] - 0.4 and call(ta) != call(ta - 0.2): cuts.append(ta - 0.03)
            for x, _, _ in GR[1:]:
                if r["a"] + 0.4 < x < r["b"] - 0.4 and call(x + 0.05) != call(x - 0.2) and all(abs(x - c) > 0.3 for c in cuts): cuts.append(x)
        if r["b"] - r["a"] > 9.0:
            last = r["a"]
            for sid in sids:
                ta = unit_start.get(sid)
                if ta and ta - last > 6.0 and r["b"] - ta > 3.0 and all(abs(ta - 0.03 - c) > 0.3 for c in cuts): cuts.append(ta - 0.03); last = ta
        cuts = sorted(cuts) + [r["b"]]
        for k in range(len(cuts) - 1):
            if FORCE or GZ:
                cam = call(cuts[k] + 0.06)
                if cam == "A": tight = a_tight; a_tight ^= 1
                else: tight = 0
            else:
                cam, tight = cycle[shot % len(cycle)]; shot += 1
            if cam != "A" and not covered(cam, cuts[k], cuts[k + 1]): cam, tight = "A", 1   # camera B wasn't rolling
            pieces.append({"a": round(cuts[k], 3), "b": round(cuts[k + 1], 3), "cam": cam, "frame": tight, "hard": k == 0})
    for i in range(len(pieces) - 1):              # never flash a <1 s shot at one framing then jump to another on the same camera
        if pieces[i]["cam"] == pieces[i + 1]["cam"] and pieces[i]["b"] - pieces[i]["a"] < 1.0: pieces[i + 1]["frame"] = pieces[i]["frame"]
    # A/V SYNC (trimming video by timestamp and re-timing with fps= let the picture drift +151 ms behind the sound over 22 shots):
    # every piece starts and ends ON the frame grid, so its video (cut by frame index) and its audio (cut to the same
    # instants) are exactly the same length and the picture can never drift from the sound.
    for pc in pieces:
        pc["a"] = round(round(pc["a"] * FPS) / FPS, 6); pc["b"] = round(round(pc["b"] * FPS) / FPS, 6)
    pieces = [pc for pc in pieces if pc["b"] - pc["a"] >= 1.0 / FPS]
    for prev, pc in zip(pieces, pieces[1:]):
        if pc["a"] < prev["b"]: pc["a"] = prev["b"]
    t = 0.0
    for pc in pieces: pc["o"] = round(t, 3); t += pc["b"] - pc["a"]
    total = round(t, 3)
    def r2o(x):
        for pc in pieces:
            if pc["a"] - 1e-3 <= x <= pc["b"] + 1e-3: return round(pc["o"] + x - pc["a"], 3)
        return None
    def r2o_next(x):
        v = r2o(x)
        if v is not None: return v
        nxt = [pc for pc in pieces if pc["a"] > x]
        return round(nxt[0]["o"], 3) if nxt else None
    def r2o_prev(x):          # a line's end can fall in a trimmed pause (tail now waits for quiet): map it to the last kept moment
        v = r2o(x)
        if v is not None: return v
        prv = [pc for pc in pieces if pc["b"] <= x + 1e-3]
        return round(prv[-1]["o"] + prv[-1]["b"] - prv[-1]["a"], 3) if prv else None
    words = []
    for w in W:
        o = r2o(w["start"])
        if o is not None:
            oe = r2o(min(w["end"], next(pc["b"] for pc in pieces if pc["a"] - 1e-3 <= w["start"] <= pc["b"] + 1e-3)))
            words.append({"o": o, "oe": max(o + 0.08, oe or o + 0.2), "w": w["word"].strip()})
    chapters = []
    for ch in D.get("chapters", []):              # long-form: [CHAPTER] markers -> YouTube description timestamps
        u = next((sg for sg in segs if sg["sid"] >= ch["first_sid"]), None)
        o = r2o_next(u["a"] + 0.05) if u else None
        if o is not None: chapters.append({"title": ch["title"], "o": 0.0 if not chapters else round(max(0.0, o - 0.3), 1)})
    if chapters:
        ts = lambda x: f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{int(x % 60):02d}" if x >= 3600 else f"{int(x // 60)}:{int(x % 60):02d}"
        open(os.path.join(OUTD, "chapters.txt"), "w").write("\n".join(f"{ts(c['o'])} {c['title']}" for c in chapters) + "\n")
        short = [f"{a['title']} ({b['o'] - a['o']:.0f}s)" for a, b in zip(chapters, chapters[1:] + [{"o": total}]) if b["o"] - a["o"] < 10]
        if len(chapters) < 3 or short:
            print(f"chapters: WARNING YouTube needs 3+ chapters of 10 s+ each (have {len(chapters)}; too short: {short or 'none'})")
    edl = {"auto_picks": using_auto, "total": total, "pieces": pieces, "words": words, "chapters": chapters,
           "units": [{"sid": sg["sid"], "text": sg["text"], "take": sg["take"], "a": sg["a"], "b": sg["b"],
                      "trims": sg["trims"], "o": r2o_next(sg["a"] + 0.05), "oe": r2o_prev(sg["b"] - 0.05)} for sg in segs]}
    json.dump(edl, open(os.path.join(OUTD, "edl.json"), "w"), indent=1)
    hard = sum(p["hard"] for p in pieces)
    cams_used = {p["cam"] for p in pieces}
    print(f"plan: {len(segs)} lines -> {len(groups)} reads -> {len(pieces)} shots ({hard} hard cuts) | {total:.1f}s | {frame_size(CFG)[0]}x{frame_size(CFG)[1]} {FPS}fps"
          + (f" | cameras {sorted(cams_used)}" if CAMS else "") + (f" | {len(chapters)} chapters" if chapters else "")
          + ("  [MACHINE PICKS: preview only]" if using_auto else ""))
    return edl

# ======================= CUT (framing) =======================
def frame_vf(kind):
    if kind == 0: return f"scale={W}:{H},setsar=1"
    z = FR["zoom"]; sw, sh_ = int(W * z) // 2 * 2, int(H * z) // 2 * 2
    eye_target = int(H * (0.40 if LONG else 860 / 1920))             # eyes on the upper third
    x = max(0, min(sw - W, int(FR["face_x"] * z - W / 2))); y = max(0, min(sh_ - H, int(FR["eye_y"] * z - eye_target)))
    return f"scale={sw}:{sh_}:flags=lanczos,crop={W}:{H}:{x}:{y},unsharp=5:5:0.6,setsar=1"

def cut(edl):
    P = [p for p in edl["pieces"] if UNTIL is None or p["o"] < UNTIL]
    parts, lab = [], []
    cam_idx = {c["name"]: k + 1 for k, c in enumerate(CAMS)}
    for i, p in enumerate(P):
        # frame-exact: video by frame index with timestamps rebuilt from the frame count (no fps= rounding, which made every
        # shot up to a frame long), audio to exactly the same instants -> each shot's picture and sound are the same length
        fa, fb = round(p["a"] * FPS), round(p["b"] * FPS); n = fb - fa; d = n / FPS
        cam = p.get("cam", "A")
        if cam == "A":
            parts.append(f"[0:v]trim=start_frame={fa}:end_frame={fb},setpts=N/({FPS}*TB),{frame_vf(p['frame'])}[v{i}];")
        else:                                   # same moment on the other camera: tB = a*tA + b ; sound stays on camera A
            c = next(c for c in CAMS if c["name"] == cam); fbB = round((c["a"] * p["a"] + c["b"]) * FPS)
            parts.append(f"[{cam_idx[cam]}:v]trim=start_frame={fbB}:end_frame={fbB + n},setpts=N/({FPS}*TB),scale={W}:{H},setsar=1[v{i}];")
        nxt_hard = (i + 1 < len(P) and P[i + 1]["hard"]) or i + 1 == len(P)
        fades = (f",afade=t=in:st=0:d={FD}" if p["hard"] else "") + (f",afade=t=out:st={max(0, d - FD):.4f}:d={FD}" if nxt_hard else "")
        parts.append(f"[0:a]atrim=start={fa / FPS:.6f}:end={fb / FPS:.6f},asetpts=PTS-STARTPTS{fades}[a{i}];")
        lab.append(f"[v{i}][a{i}]")
    graph = "".join(parts) + "".join(lab) + f"concat=n={len(P)}:v=1:a=1[v][a]"
    out = os.path.join(OUTD, "cut.mp4")
    ins = ["-i", NORM] + [x for c in CAMS for x in ("-i", c["file"])]
    sh(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
    print("cut:", out)

# ======================= CUES (graphics + B-roll) =======================
# An ANCHOR finds a moment in OUTPUT time (see references/project-config.md):
#   {"t": 0.15}                                   fixed time
#   {"line": "regex on the script line"}          start of that line ("edge": "end" for its end)
#   {"line": "...", "words": ["eight|8", "raise"]} walk forward to each spoken word in turn
#   any of the above + "offset": seconds;  a LIST = first one that resolves
def _bare(w): return re.sub(r"[^\w%'-]", "", w).lower()

def anchor(spec, edl):
    if spec is None: return None
    if isinstance(spec, list):
        for s in spec:
            v = anchor(s, edl)
            if v is not None: return v
        return None
    if isinstance(spec, (int, float)): return float(spec)
    if "t" in spec: return spec["t"] + spec.get("offset", 0)
    u = next((u for u in edl["units"] if re.search(spec["line"], u["text"], re.I)), None)
    if not u: return None
    base = u["oe"] if spec.get("edge") == "end" else u["o"]
    if base is None: return None
    for wp in spec.get("words", []):
        base = next((w["o"] for w in edl["words"] if w["o"] >= base and re.fullmatch(wp, _bare(w["w"]))), None)
        if base is None: return None
    return round(base + spec.get("offset", 0), 3)

def _no_offset(spec):
    if isinstance(spec, list): return [_no_offset(s) for s in spec]
    if isinstance(spec, dict): return {k: v for k, v in spec.items() if k != "offset"}
    return spec

def _resolve_params(obj, start, edl):
    """Inside a cue's params, {"$at": ANCHOR, "min":.., "default":..} becomes seconds after the cue starts."""
    if isinstance(obj, list): return [_resolve_params(x, start, edl) for x in obj]
    if isinstance(obj, dict):
        if "$at" in obj:
            v = anchor(obj["$at"], edl)
            v = (v - start) if v is not None else obj.get("default", 0.3)
            return round(max(obj.get("min", 0.0), v), 2)
        return {k: _resolve_params(v, start, edl) for k, v in obj.items()}
    return obj

def cues(edl):
    C, B = [], []
    for cu in CFG.get("cues", []):
        if any(anchor({"line": r}, edl) is None for r in cu.get("requires", [])): continue
        start = anchor(cu["at"], edl)
        if start is None: continue
        if "dur" in cu: dur = cu["dur"]
        else:
            frm = anchor(cu.get("from", _no_offset(cu["at"])), edl)
            until = anchor(cu.get("until"), edl)
            lo, hi = cu.get("min", 2.0), cu.get("max", 6.0)
            dur = max(lo, min(hi, until - frm)) if (frm is not None and until is not None) else cu.get("default", lo)
        item = {"o": round(max(0.0, start), 3), "dur": round(dur, 2)}
        if "graphic" in cu:
            C.append({"id": cu["graphic"], **item, "params": _resolve_params(cu.get("params", {}), start, edl)})
        elif "broll" in cu:
            B.append({"clip": cu["broll"], "cin": float(cu.get("cin", 0.0)), **item})   # cin: start this far into the clip (the gesture, not the run-up)
    C.sort(key=lambda c: c["o"])
    for a, b in zip(C, C[1:]):                     # graphics never overlap: trim each to the next start
        if a["o"] + a["dur"] > b["o"] - 0.05: a["dur"] = round(max(1.2, b["o"] - 0.05 - a["o"]), 2)
    if UNTIL is not None:
        C = [c for c in C if c["o"] < UNTIL]; B = [b for b in B if b["o"] < UNTIL]
    missing = [cu.get("graphic") or cu.get("broll") for cu in CFG.get("cues", [])
               if (cu.get("graphic") or cu.get("broll")) not in {c["id"] for c in C} | {b["clip"] for b in B}]
    json.dump({"graphics": C, "broll": B}, open(os.path.join(OUTD, "cues.json"), "w"), indent=1)
    print(f"cues: {len(C)} graphics, {len(B)} B-roll cutaways" + (f" | NOT PLACED (anchor not found): {missing}" if missing else ""))
    return C, B

# ======================= MG (exact durations) =======================
def gfx_specs(): return {s["id"]: s for s in json.load(open(GFX))} if os.path.exists(GFX) else {}

def mg(C):
    base = gfx_specs(); specs = []
    for c in C:
        s = json.loads(json.dumps(base[c["id"]])); s["dur"] = c["dur"]; s["params"].update(c.get("params", {}))
        s["fps"] = FPS; s["previewAt"] = [round(min(c["dur"] - 0.45, max(1.5, c["dur"] * 0.55)), 2)]
        specs.append(s)
    if not specs: print("mg: no graphics"); return
    sp = os.path.join(OUTD, "mg_specs.json"); json.dump(specs, open(sp, "w"))
    bf = os.path.join(OUTD, "brand.json")                       # per-project brand for mg_render (colours + fonts); absent = house look
    if CFG.get("brand"):
        b = brand(CFG)
        json.dump({"accent": b["accent"], "primary": b["primary"], "ink": b["ink"],
                   "panel": b.get("panel"), "panel2": b.get("panel2"), "chip_text": b.get("chip_text"),
                   "head_ttf": b["head_ttf"], "body_ttf": b["body_ttf"]}, open(bf, "w"))
    elif os.path.exists(bf):
        os.remove(bf)
    mgdir = os.path.join(SCRIPTS, "mg")
    sh(["node", os.path.join(mgdir, "mg_render.js"), sp, os.path.join(OUTD, "mg")], env=project_env(CFG))
    if LONG:      # the kit is a vertical canvas: find each card's visible box so final() can place it in 16:9
        pv = os.path.join(OUTD, "mg_bbox"); sh(["node", os.path.join(mgdir, "mg_render.js"), sp, pv, "preview"], env=project_env(CFG))
        boxes = {}
        for s_ in specs:
            png = os.path.join(pv, f"{s_['id']}_t{s_['previewAt'][0]:.1f}.png")
            if not os.path.exists(png): continue
            im = Image.open(png).convert("RGBA")
            bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
            if bb and s_["tpl"] == "section":       # full-frame card: centre on the WORDS, the edit fills 16:9 with it
                lum = Image.composite(im.convert("L"), Image.new("L", im.size, 0), im.getchannel("A"))
                bb = lum.point(lambda v: 255 if v > 150 else 0).getbbox() or bb
                boxes[s_["id"]] = {"full": True, "cy": (bb[1] + bb[3]) // 2}
            elif bb: boxes[s_["id"]] = [max(0, bb[0] - 24), max(0, bb[1] - 24), min(1080, bb[2] + 24), min(1920, bb[3] + 24)]
        json.dump(boxes, open(os.path.join(OUTD, "mg", "bbox.json"), "w"))
    print("mg:", len(specs), "graphics rendered")

# ======================= CAPTIONS =======================
SIZE, CY, MAXW = (54, 935, 1500) if LONG else (63, 1558, 864)    # house caption box (vertical: from the reference edit)
LH = round(SIZE * 1.16)
BURN = CFG.get("captions", {}).get("burn", not LONG)              # long-form: SRT for YouTube, nothing burned in
_BR = brand(CFG)
LIME = hex2rgb(_BR["accent"]) + (255,)              # caption highlight word (brand accent)
WHITE = (255, 255, 255, 255)
CAP_FONT = _BR["body_ttf"]                           # caption face (brand body font)
def _capfont(sz):
    if not CAP_FONT:
        sys.exit("no caption font found: run setup.sh (it fetches Inter) or set brand.body_ttf in project.json")
    f = ImageFont.truetype(CAP_FONT, sz)
    try: f.set_variation_by_axes([600])              # variable bodies (Inter): caption weight 600; static faces ignore
    except Exception: pass
    return f
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DAYS = "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
BASE_FIX = [(r"\bi('ll|'m|'ve|'d)?\b", lambda m: "I" + (m.group(1) or "")),
            (rf"\b({MONTHS.lower()}|{DAYS.lower()})\b", lambda m: m.group(1).capitalize()),
            (r"\b(one|two|three|four|five|six|seven|eight|nine|ten) percent\b",
             lambda m: str(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"].index(m.group(1)) + 1) + "%"),
            (r"\b(\d+(?:\.\d+)?) ?percent\b", r"\1%")]
# UK spelling (Whisper's English models write US spelling). On by default; project.json "captions": {"locale": "en-US"} turns it off.
# "metres" only after a number, so a gas meter stays a meter.
UK_FIX = [(r"\bprogram(s?)\b", r"programme\1"), (r"\bcolor", "colour"), (r"\bfavor", "favour"), (r"\bcenter(s?)\b", r"centre\1"),
          (r"\b(reali|organi|recogni|apologi|priori)z(e|ed|es|ing)\b", r"\1s\2"), (r"\banalyz", "analys"), (r"\bgray\b", "grey"),
          (r"\btraveling\b", "travelling"), (r"\bmold\b", "mould"), (r"\bneighbor", "neighbour"),
          (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a few|few) meters?\b",
           lambda m: m.group(1) + (" metre" if m.group(0).endswith("meter") else " metres"))]
if CFG.get("captions", {}).get("locale", "en-GB").lower() in ("en-gb", "en-au", "en-nz", "en-ie", "uk"):
    BASE_FIX += UK_FIX
FIX = [(a, b) for a, b in CFG.get("captions", {}).get("fix", [])] + BASE_FIX     # project fixes run first
_key = CFG.get("captions", {}).get("key", [])
KEY = re.compile(r"^(" + "|".join(re.escape(k) for k in _key) + r")[,.?!]*$", re.I) if _key else None

def fixtext(s):
    for a, b in FIX: s = re.sub(a, b, s)
    s = re.sub(r"\s+([,.?!%])", r"\1", s); s = re.sub(r"(\d) \.(\d)", r"\1.\2", s)
    return re.sub(r"\s+", " ", s).strip()

def captions(edl, C):
    F = _capfont(SIZE); d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    # caption from the FINISHED cut's own transcription: exactly what is heard, already in output time
    cut_v = os.path.join(OUTD, "cut.mp4"); ct = os.path.join(OUTD, "cap_tr.json"); cw = os.path.join(OUTD, "cap.wav")
    if not os.path.exists(ct) or os.path.getmtime(ct) < os.path.getmtime(cut_v):
        sh(["ffmpeg", "-y", "-v", "error", "-i", cut_v, "-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", cw])
        sh([sys.executable, os.path.join(SCRIPTS, "transcribe_v.py"), cw, ct, "medium.en"], env=project_env(CFG))
        # a word stretched over a phrase hides the words under it ("But there are a a look."): re-listen those
        sh([sys.executable, os.path.join(SCRIPTS, "refill_words.py"), cw, ct], env=project_env(CFG))
        # check the caption words against the script ("baked your tig" for "baked it in", "saffering" for "sat on"): a prompted
        # re-listen of each kept line decides mishearing (use the script) vs the presenter's live reword (keep their words)
        sh([sys.executable, os.path.join(SCRIPTS, "caption_check.py"), cw, ct, os.path.join(OUTD, "edl.json"),
            os.path.join(OUTD, "caption_check.txt")], env=project_env(CFG))
    W0 = [{"o": w["start"], "oe": w["end"], "w": w["word"].strip()} for sg in json.load(open(ct))["segments"] for w in sg["words"]
          if UNTIL is None or w["start"] < UNTIL]
    NUMW = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
    W = []
    for w in W0:                                   # join "four" + "percent" -> "4%" BEFORE grouping, so a figure never splits
        if W and re.match(r"^[,.]\d", w["w"].strip()) and re.search(r"\d$", W[-1]["w"].strip()):   # "£296" + ",285," -> "£296,285,"
            W[-1]["w"] = W[-1]["w"].strip() + w["w"].strip(); W[-1]["oe"] = w["oe"]; continue
        bare = re.sub(r"[^\w.]", "", w["w"]).lower()
        if W and bare.startswith("percent"):
            prev = re.sub(r"[^\w.]", "", W[-1]["w"]).lower()
            num = NUMW.get(prev, prev if re.fullmatch(r"\d+(\.\d+)?", prev) else None)
            if num is not None:
                W[-1]["w"] = num + "%" + re.sub(r"^[\w]+", "", w["w"].strip()); W[-1]["oe"] = w["oe"]; continue
        W.append(w)
    tpl = {k: v["tpl"] for k, v in gfx_specs().items()}
    hide = set(CFG.get("captions", {}).get("hide_under", ["section"]))           # full-frame cards
    covered = [(c["o"], c["o"] + c["dur"]) for c in C if tpl.get(c["id"]) in hide]
    cues_, cur = [], []
    for i, w in enumerate(W):
        cur.append(w)
        txt = fixtext(" ".join(x["w"] for x in cur))
        end_sent = w["w"].endswith((".", "?", "!"))
        gap = (W[i + 1]["o"] - w["oe"]) if i + 1 < len(W) else 9
        if _wrap(txt, F, d0) is None:             # overflow -> close previous cue
            cur.pop(); cues_.append(cur); cur = [w]
            if end_sent or gap > 0.5: cues_.append(cur); cur = []    # a sentence-final word never runs on into the next sentence
        elif end_sent or gap > 0.5 or len(cur) >= 12:
            cues_.append(cur); cur = []
    if cur: cues_.append(cur)
    out, srt = [], []; cdir = os.path.join(OUTD, "caps"); os.makedirs(cdir, exist_ok=True)
    for k, cw_ in enumerate(cues_):
        a = cw_[0]["o"]; b = cues_[k + 1][0]["o"] if k + 1 < len(cues_) and cues_[k + 1][0]["o"] - cw_[-1]["oe"] < 0.6 else cw_[-1]["oe"] + 0.25
        txt = fixtext(" ".join(x["w"] for x in cw_)); lines = _wrap(txt, F, d0)
        srt.append({"a": round(a, 3), "b": round(b, 3), "lines": lines})       # the SRT carries every line (no card covers closed captions)
        for sa, sb in covered:                    # a full-frame card covers it: start the burned caption when the card clears
            if sa <= a < sb: a = sb + 0.05        # (dropping it once left three seconds with no captions)
        if b - a < 0.4: continue                  # wholly under the card
        png = os.path.join(cdir, f"c{k:03d}.png")
        if BURN: _render(lines, png, F)
        out.append({"a": round(a, 3), "b": round(b, 3), "png": png, "lines": lines})
    with open(os.path.join(OUTD, "final.srt"), "w") as f:
        ts = lambda s: f"{int(s//3600):02d}:{int(s%3600//60):02d}:{s%60:06.3f}".replace(".", ",")
        for n, c in enumerate(srt, 1): f.write(f"{n}\n{ts(c['a'])} --> {ts(c['b'])}\n" + "\n".join(c["lines"]) + "\n\n")
    json.dump(out, open(os.path.join(OUTD, "caps.json"), "w"), indent=1)
    print("caps:", len(out), "cues")
    return out

def _wrap(text, F, d):
    lines = [[]]
    for w in text.split():
        if d.textlength(" ".join(lines[-1] + [w]), font=F) <= MAXW or not lines[-1]: lines[-1].append(w)
        else: lines.append([w])
    return None if len(lines) > 2 else [" ".join(l) for l in lines]

def _render(lines, path, F):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    tw = max(d.textlength(l, font=F) for l in lines); boxw, boxh = tw + 80, LH * len(lines) + 40
    bx, by = (W - boxw) / 2, CY - boxh / 2
    d.rounded_rectangle([bx, by, bx + boxw, by + boxh], radius=26, fill=(0, 0, 0, 236))
    for i, l in enumerate(lines):
        x = (W - d.textlength(l, font=F)) / 2; y = by + 20 + i * LH
        for wd in l.split(" "):
            d.text((x, y), wd, font=F, fill=LIME if KEY and KEY.match(wd) else WHITE)
            x += d.textlength(wd + " ", font=F)
    img.save(path)

# ======================= FINAL =======================
def final(edl, C, B, caps):
    cut_v = os.path.join(OUTD, "cut.mp4")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", cut_v], capture_output=True, text=True).stdout)
    lead = CFG.get("cover", {}).get("lead", "A")
    cover = os.path.join(PD, "cover", f"cover_{lead}.png")
    ins = ["-i", cut_v]; idx = 1; parts = []; cur = "[0:v]"
    for k, b in enumerate(B):        # B-roll: full-frame cutaways, voice carries on underneath
        clip = os.path.join(BROLL, b["clip"]); ins += ["-i", clip]
        cw, ch = (int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                                  "-of", "csv=p=0", clip], capture_output=True, text=True).stdout.strip().split(",")[:2])
        if (cw > ch) == (W > H):     # same shape: fill the frame
            fit = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
            parts.append(f"[{idx}:v]trim=start={b.get('cin', 0.0):.2f}:duration={b['dur']:.2f},setpts=PTS-STARTPTS+{b['o']:.3f}/TB,fps={FPS},{fit},setsar=1,fade=t=in:st={b['o']:.3f}:d=0.12:alpha=1,format=yuva420p[br{k}];")
        else:                        # other shape (e.g. a vertical library clip in a 16:9 long-form): sharp clip over a blurred fill
            parts.append(f"[{idx}:v]trim=start={b.get('cin', 0.0):.2f}:duration={b['dur']:.2f},setpts=PTS-STARTPTS+{b['o']:.3f}/TB,fps={FPS},split[bx{k}][by{k}];"
                         f"[bx{k}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:2,eq=brightness=-0.08[bb{k}];"
                         f"[by{k}]scale=-2:{H}:force_original_aspect_ratio=decrease[bf{k}];"
                         f"[bb{k}][bf{k}]overlay=(W-w)/2:(H-h)/2,setsar=1,fade=t=in:st={b['o']:.3f}:d=0.12:alpha=1,format=yuva420p[br{k}];")
        parts.append(f"{cur}[br{k}]overlay=0:0:eof_action=pass:enable='between(t,{b['o']:.3f},{b['o'] + b['dur']:.3f})'[vb{k}];"); cur = f"[vb{k}]"; idx += 1
    boxes = json.load(open(os.path.join(OUTD, "mg", "bbox.json"))) if LONG and os.path.exists(os.path.join(OUTD, "mg", "bbox.json")) else {}
    tpl = {k: v["tpl"] for k, v in gfx_specs().items()}
    for k, c in enumerate(C):        # graphics (alpha ProRes, drawn on the vertical canvas)
        ins += ["-i", os.path.join(OUTD, "mg", c["id"] + ".mov")]
        if not LONG:
            parts.append(f"[{idx}:v]setpts=PTS-STARTPTS+{c['o']:.3f}/TB[gm{k}];")
            parts.append(f"{cur}[gm{k}]overlay=0:0:eof_action=pass[vg{k}];")
        else:                        # 16:9: crop the card, scale it down, place it beside the presenter (lower thirds bottom-left)
            t_ = tpl.get(c["id"]); bx_ = boxes.get(c["id"], [0, 0, 1080, 1920])
            if isinstance(bx_, dict):    # full-frame section card: scale to the frame width, crop H around the words
                sc = W / 1080; cy = int(bx_["cy"] * sc); y0 = max(0, min(int(1920 * sc) - H, cy - H // 2))
                parts.append(f"[{idx}:v]setpts=PTS-STARTPTS+{c['o']:.3f}/TB,scale={W}:{int(1920 * sc) // 2 * 2},crop={W}:{H}:0:{y0}[gm{k}];")
                parts.append(f"{cur}[gm{k}]overlay=0:0:eof_action=pass[vg{k}];"); cur = f"[vg{k}]"; idx += 1; continue
            x0, y0, x1, y1 = bx_; bw, bh = x1 - x0, y1 - y0
            sc = min(1.0, (0.62 if t_ == "section" else 0.44) * W / bw, (0.86 if t_ != "lower" else 0.24) * H / bh)
            sw, shh = int(bw * sc) // 2 * 2, int(bh * sc) // 2 * 2
            if t_ == "lower": px, py = 56, H - shh - 56
            elif t_ == "section": px, py = (W - sw) // 2, (H - shh) // 2
            else: px, py = (W - sw - 80, (H - shh) // 2) if FR["face_x"] < W / 2 else (80, (H - shh) // 2)
            parts.append(f"[{idx}:v]setpts=PTS-STARTPTS+{c['o']:.3f}/TB,crop={bw}:{bh}:{x0}:{y0},scale={sw}:{shh}[gm{k}];")
            parts.append(f"{cur}[gm{k}]overlay={px}:{py}:eof_action=pass[vg{k}];")
        cur = f"[vg{k}]"; idx += 1
    for k, c in enumerate(caps if BURN else []):
        ins += ["-i", c["png"]]
        parts.append(f"{cur}[{idx}:v]overlay=0:0:enable='between(t,{c['a']:.3f},{c['b']:.3f})'[vc{k}];"); cur = f"[vc{k}]"; idx += 1
    if os.path.exists(cover) and not LONG:   # shorts: cover = poster frame, so the grid tile is the designed cover
        ins += ["-i", cover]
        parts.append(f"{cur}[{idx}:v]overlay=0:0:enable='between(t,0,0.13)'[vp];"); cur = "[vp]"; idx += 1
    else:
        if not LONG: print("final: NOTE no cover yet (vedit.py cover) — first frame is the plain shot")
    parts.append(f"{cur}fade=t=out:st={dur - 0.25:.3f}:d=0.25[vout]")
    pre = os.path.join(OUTD, "final_pre.mp4")
    sh(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", "".join(parts), "-map", "[vout]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "copy", "-movflags", "+faststart", pre])
    dn = CFG.get("audio", {}).get("denoise")          # drone whine / steady background: "firm" (1.0), "gentle" (0.8) or a number
    if dn:
        strength = {"firm": 1.0, "gentle": 0.8}.get(dn, dn)
        w0, w1, pre2 = os.path.join(OUTD, "pre_a.wav"), os.path.join(OUTD, "pre_a_dn.wav"), pre + ".dn.mp4"
        sh(["ffmpeg", "-y", "-v", "error", "-i", pre, "-vn", "-ac", "1", "-ar", "48000", w0])
        sh([sys.executable, os.path.join(SCRIPTS, "denoise.py"), w0, w1, str(strength)], env=project_env(CFG))
        sh(["ffmpeg", "-y", "-v", "error", "-i", pre, "-i", w1, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
            "-movflags", "+faststart", pre2]); os.replace(pre2, pre); os.remove(w0); os.remove(w1)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    L = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", m, re.S).group(0))
    out = os.path.join(OUTD, "final.mp4")
    sh(["ffmpeg", "-y", "-v", "error", "-i", pre, "-c:v", "copy", "-af",
        f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={L['input_i']}:measured_TP={L['input_tp']}:measured_LRA={L['input_lra']}:measured_thresh={L['input_thresh']}:offset={L['target_offset']}:linear=true,afade=t=out:st={dur - 0.25:.3f}:d=0.25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out])
    os.remove(pre)
    print("final:", out, f"{dur:.1f}s")

if __name__ == "__main__":
    edl = plan()
    if STAGE == "plan": sys.exit(0)
    C, B = cues(edl)
    if STAGE == "cues": sys.exit(0)
    if STAGE in ("cut", "all"): cut(edl)
    if STAGE in ("mg", "all"): mg(C)
    if STAGE in ("caps", "all", "final"): caps = captions(edl, C)
    if STAGE in ("final", "all"): final(edl, C, B, caps)
