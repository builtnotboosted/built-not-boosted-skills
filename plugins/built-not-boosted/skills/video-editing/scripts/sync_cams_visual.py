#!/usr/bin/env python3
"""Line up a SILENT second camera (e.g. a small drone that records no audio) with camera A by MOTION.

Head turns, gestures and steps show in both cameras at the same moment, so the frame-to-frame motion
of the presenter in camera A and inside a box around them in camera B correlate like two sound tracks:
  1. motion envelope (mean abs frame difference, 10 fps, light blur) of A (whole frame) and of B (box);
  2. coarse lag: normalised cross-correlation over the whole recordings (any sign: B may start first);
  3. fine lag: re-correlate +-1 s around the coarse peak at 30 fps;
  4. clocks are both real-time containers, so tB = tA + lag (a = 1).
Prints JSON: {"a": 1.0, "b": lag, "confidence": peak_ncc, "second": second-best peak, "covers": [tA_start, tA_end]}.
A trustworthy sync has a clear single peak: confidence well above `second` (ratio printed as "clarity").

usage: sync_cams_visual.py A.mp4 B.mp4 --box x0,y0,x1,y1   (box in B pixel space, around the presenter)
"""
import sys as _sys
if len(_sys.argv) < 3 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, subprocess, sys
import numpy as np

A, B = sys.argv[1], sys.argv[2]
box = [int(v) for v in sys.argv[sys.argv.index("--box") + 1].split(",")] if "--box" in sys.argv else None

def probe(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                          "-of", "default=nw=1", p], capture_output=True, text=True).stdout
    kv = dict(l.split("=") for l in out.split() if "=" in l)
    return int(kv["width"]), int(kv["height"]), float(kv["duration"])

def envelope(p, fps, crop=None, w=96, h=96):
    vf = (f"crop={crop[2]-crop[0]}:{crop[3]-crop[1]}:{crop[0]}:{crop[1]}," if crop else "") + f"fps={fps},scale={w}:{h},gblur=sigma=1,format=gray"
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", p, "-vf", vf, "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    m = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    m = np.concatenate([[m[0]], m]); return (m - m.mean()) / (m.std() + 1e-9)

def xcorr(a, b, lo, hi):
    """normalised correlation for lags L in [lo,hi] (samples), where b[i+L] ~ a[i]."""
    best = []
    for L in range(lo, hi + 1):
        i0, i1 = max(0, -L), min(len(a), len(b) - L)
        if i1 - i0 < 0.3 * min(len(a), len(b)): continue
        x, y = a[i0:i1], b[i0 + L:i1 + L]
        best.append((float((x * y).mean() / (x.std() * y.std() + 1e-9)), L))
    return sorted(best, reverse=True)

_, _, dA = probe(A); wB, hB, dB = probe(B)
F = 10
ea, eb = envelope(A, F), envelope(B, F, box)
c = xcorr(ea, eb, -len(ea) + 30, len(eb) - 30)
top, L0 = c[0]
second = next((v for v, L in c if abs(L - L0) > 3 * F), 0.0)
F2 = 30
ea2, eb2 = envelope(A, F2), envelope(B, F2, box)
c2 = xcorr(ea2, eb2, int(L0 / F * F2) - F2, int(L0 / F * F2) + F2)
lag = c2[0][1] / F2
covers = [max(0.0, -lag), min(dA, dB - lag)]
print(json.dumps({"a": 1.0, "b": round(lag, 3), "confidence": round(c2[0][0], 3), "second": round(second, 3),
                  "clarity": round(top / max(second, 1e-3), 2), "covers": [round(covers[0], 3), round(covers[1], 3)], "method": "motion"}))
