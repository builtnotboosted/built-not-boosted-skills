#!/usr/bin/env python3
"""Audio-cut check: does any cut land on sound?

The QA gate checks WORDS, so it misses two faults a listener hears straight away:
  - an OUT-point that clips the soft tail of the last word ("digging", "songs", "underneath", "property"...),
  - an IN-point that starts inside a word (the "any harm ... any harm" repeat; a "t-you" fragment).
Neither changes the transcript. Absolute loudness can't catch them either: soft endings (-ing, -s, -ty) keep
sounding below -30 dB, and outdoor background sits well above the quietest room tone. Calibrated on six
clipped words flagged by ear in a real edit: all six were cut inside a -30 dB "silence" but BEFORE the -45 dB one.

Rule, tried at -45 dB, then -38, then -30 (the deeper levels can be unreachable in a noisy outdoor spot):
  OUT b : PASS if b is inside a quiet run at that level (>= 50 ms past its onset);
          FAIL if a quiet run at that level starts within 0.6 s AFTER b  (the sound was still dying away: tail clipped);
          otherwise try the next level.  No quiet at any level near b -> WARN (continuous speech: check by ear).
  IN  a : PASS if a is inside a quiet patch (>= 40 ms) at that level;
          FAIL if a quiet patch at that level starts within 0.6 s after a (a clean gap was right there: started mid-word);
          otherwise try the next level.  No quiet near a -> WARN.
Reframes inside one continuous range are not audio cuts; the exit tail is skipped.

usage: cut_check.py <project_dir>      exit 1 on any FAIL (WARNs are printed, exit 0)
"""
import sys as _sys
if len(_sys.argv) < 2 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, os, re, subprocess, sys

PD = sys.argv[1]
AUDIO = os.path.join(PD, "audio.wav")
LEVELS = (-45, -38, -30)

def silences(d, noise):
    sd = subprocess.run(["ffmpeg", "-v", "info", "-i", AUDIO, "-af", f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    return [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([\d.]+)", sd), re.findall(r"silence_end: ([\d.]+)", sd))]

S_OUT = {lv: silences(0.12, lv) for lv in LEVELS}
S_IN = {lv: silences(0.04, lv) for lv in LEVELS}

cfg = json.load(open(os.path.join(PD, "project.json")))
tail = cfg.get("exit_tail")
E = json.load(open(os.path.join(PD, "build", "edl.json")))
ranges = []                                       # contiguous pieces = one continuous stretch of camera-A sound
for p in E["pieces"]:
    if ranges and abs(p["a"] - ranges[-1]["b"]) < 0.01: ranges[-1]["b"] = p["b"]
    else: ranges.append({"a": p["a"], "b": p["b"]})
if tail: ranges = [r for r in ranges if not (abs(r["a"] - tail[0]) < 0.05 and abs(r["b"] - tail[1]) < 0.05)]

words = []
for f in ("tr_large.json", "tr_medium.json"):
    fp = os.path.join(PD, f)
    if os.path.exists(fp): words += [x for sg in json.load(open(fp))["segments"] for x in sg["words"]]
def near(t):
    c = sorted(words, key=lambda x: min(abs(x["start"] - t), abs(x["end"] - t)))
    return c[0]["word"].strip() if c else ""

def judge(t, S, pad):
    for lv in LEVELS:
        if any(s + pad <= t <= e + 0.05 for s, e in S[lv]): return "PASS", lv
        if any(t < s <= t + 0.6 for s, e in S[lv]): return "FAIL", lv
    return "WARN", None

import wave
import numpy as np
_w = wave.open(AUDIO, "rb"); _SR = _w.getframerate(); _X = np.frombuffer(_w.readframes(_w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; _w.close()
LW = [x for sg in json.load(open(os.path.join(PD, "tr_large.json")))["segments"] for x in sg["words"]] if os.path.exists(os.path.join(PD, "tr_large.json")) else words
def closure_at_boundary(t):
    """Strict: a deep (< -50 dB) short dip with no large-v3 word straddling it and a word ending just before. It must stay strict:
    a looser version (any model's boundary + a shallow dip) waved through the mid-word "dig|ging", and the p-closure
    of "de|posit" looks exactly like a word end. A cut Claude has verified by hand goes in project.json cut_check.allow instead."""
    seg = _X[max(0, int((t - 0.03) * _SR)):int((t + 0.02) * _SR)]
    if not len(seg) or 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9) > -50: return False
    if any(x["start"] < t - 0.05 and x["end"] > t + 0.08 for x in LW): return False
    return any(t - 0.25 <= x["end"] <= t + 0.08 for x in LW)
# hand-verified cuts the energy rules can't confirm (e.g. a word-boundary cut inside connected speech): auditable, with a reason
ALLOW = (json.load(open(os.path.join(PD, "project.json"))).get("cut_check") or {}).get("allow", [])
def allowed(t):
    return next((a for a in ALLOW if abs(a["t"] - t) <= 0.03), None)

fails, warns = [], []
for i, r in enumerate(ranges):
    if i > 0:
        v, lv = judge(r["a"], S_IN, 0.0)
        if v == "FAIL" and allowed(r["a"]):
            warns.append(f"IN   {r['a']:8.2f}  allowed by hand: {allowed(r['a'])['why']} (check by ear)"); v = "PASS"
        if v == "FAIL":
            gap = next(((s, e) for s, e in S_OUT[lv] if r["a"] < s <= r["a"] + 0.6), None)   # first quiet run >= 0.12 s after the bad start
            sug = f"; suggest in-point ~{gap[1] - 0.12:.2f} (just before the next sound)" if gap else ""
            fails.append(f"IN   {r['a']:8.2f}  starts mid-sound (near '{near(r['a'])}'); a clean gap ({lv} dB) follows within 0.6 s{sug}")
        if v == "WARN": warns.append(f"IN   {r['a']:8.2f}  no quiet gap near the start (near '{near(r['a'])}'): check by ear")
    v, lv = judge(r["b"], S_OUT, 0.05)
    if v == "FAIL" and allowed(r["b"]):
        warns.append(f"OUT  {r['b']:8.2f}  allowed by hand: {allowed(r['b'])['why']} (check by ear)"); continue
    if v == "FAIL" and closure_at_boundary(r["b"]):   # a deep, short dip ON a word boundary: the closure of a final stop ("deposi(t) | is")
        warns.append(f"OUT  {r['b']:8.2f}  cut in a short closure at a word boundary (near '{near(r['b'])}'): unreleased final consonant, check by ear"); continue
    if v == "FAIL": fails.append(f"OUT  {r['b']:8.2f}  cuts while the word is still dying away (near '{near(r['b'])}'); quiet ({lv} dB) only starts after the cut: tail clipped")
    if v == "WARN": warns.append(f"OUT  {r['b']:8.2f}  no quiet after the cut (near '{near(r['b'])}'): check by ear")

print(f"cut check: {len(ranges)} audio ranges | {len(fails)} FAIL | {len(warns)} warn")
for b in fails: print("  FAIL " + b)
for b in warns: print("  warn " + b)
sys.exit(1 if fails else 0)
