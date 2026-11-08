#!/usr/bin/env python3
"""Line up a second camera with the main camera (A) by their sound.

Cameras that were started separately disagree on time, and their clocks drift a little (a Canon and
an iPhone can drift tens of milliseconds over 15 minutes). So:
  1. coarse offset: cross-correlate 100 Hz loudness envelopes of the whole recordings;
  2. exact offset: cross-correlate the raw audio in several 20 s windows spread over the overlap;
  3. fit tB = a * tA + b through the windows (a != 1 is the drift).
Prints JSON: {"a", "b", "confidence", "windows", "covers": [tA_start, tA_end]}.

usage: sync_cams.py A_16k.wav B_16k.wav
"""
import sys as _sys
if len(_sys.argv) < 3 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, sys, wave
import numpy as np

SR = 16000

def load(p):
    w = wave.open(p, "rb"); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; w.close()
    return x

def env(x, hop=160):
    n = len(x) // hop
    e = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-9)
    e = np.log(e); e -= e.mean(); return e

def xcorr(a, b):
    """c[k] = sum a[n+k] * b[n]; returns (lags, c) with lags from -(len(b)-1) to len(a)-1."""
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    c = np.concatenate([c[-(len(b) - 1):], c[:len(a)]])
    return np.arange(-(len(b) - 1), len(a)), c

def main():
    A, B = load(sys.argv[1]), load(sys.argv[2])
    ea, eb = env(A), env(B)
    lags, c = xcorr(ea, eb)
    k = int(lags[np.argmax(c)]); off = k / 100.0            # tA = tB + off  (coarse, 10 ms)
    srt = np.sort(c); conf_env = float((srt[-1] - np.median(c)) / (np.std(c) + 1e-9))
    lo, hi = max(0.0, off), min(len(A) / SR, len(B) / SR + off)   # overlap in A time
    if hi - lo < 10: sys.exit(json.dumps({"error": "cameras barely overlap", "coarse_offset": off}))
    win = 20.0; pairs = []
    centres = np.linspace(lo + win, hi - win, num=max(1, min(5, int((hi - lo) // 60) + 1))) if hi - lo > 2 * win + 1 else [(lo + hi) / 2]
    for tc in centres:
        # window inside the overlap (short clips: the window shrinks to fit), with room for the +-0.3 s search either side
        a0 = int(max(lo + 0.35, tc - win / 2) * SR); a1 = int(min(hi - 0.35, tc + win / 2) * SR)
        if a1 - a0 < 2 * SR: continue
        seg_a = A[a0:a1]
        if np.sqrt((seg_a ** 2).mean()) < 1e-3: continue          # silent window, skip
        pad = int(0.3 * SR); b0 = int((a0 / SR - off) * SR) - pad; b1 = int((a1 / SR - off) * SR) + pad
        b0, b1 = max(0, b0), min(len(B), b1)
        if b1 - b0 < (a1 - a0): continue
        seg_b = B[b0:b1]
        lg, cc = xcorr(seg_b, seg_a)                              # where seg_a sits inside seg_b
        j = int(lg[np.argmax(cc)])
        tb = (b0 + j) / SR + (a1 - a0) / SR / 2                   # centre of the window in B time
        ta = (a0 + (a1 - a0) / 2) / SR
        peak = float(cc.max() / (np.sqrt((seg_a ** 2).sum() * (seg_b ** 2).sum()) + 1e-9))
        pairs.append((ta, tb, peak))
    if not pairs: sys.exit(json.dumps({"error": "no usable windows", "coarse_offset": off}))
    P = np.array(pairs)
    if len(P) >= 2 and np.ptp(P[:, 0]) > 30:
        a, b = np.polyfit(P[:, 0], P[:, 1], 1)
    else:
        a, b = 1.0, float(np.median(P[:, 1] - P[:, 0]))
    resid = float(np.abs(P[:, 1] - (a * P[:, 0] + b)).max()) if len(P) else 0
    covers = [max(0.0, -b / a), min(len(A) / SR, (len(B) / SR - b) / a)]
    print(json.dumps({"a": round(float(a), 8), "b": round(float(b), 5), "confidence": round(float(np.median(P[:, 2])), 3),
                      "envelope_peak": round(conf_env, 1), "max_residual_ms": round(resid * 1000, 1),
                      "windows": len(P), "covers": [round(covers[0], 3), round(covers[1], 3)]}))

if __name__ == "__main__":
    main()
