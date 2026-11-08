#!/usr/bin/env python3
"""Background-noise gate for the finished audio (drone whine, steady hum, hiss).

Calibrated on a shoot with a small drone hovering beside the presenter: the drone adds TONAL whine
(~200-290 Hz, ~1 kHz, ~3 kHz) that drifts as the motors hold position, so fixed notches miss it and
ffmpeg afftdn (broadband) only took 1-4 dB off. Spectral gating with a noise fingerprint from the take's
own pauses (noisereduce, stationary) took 11-13 dB off the whine for ~0.5 dB of voice; the adaptive
(non-stationary) mode took 18 dB but ate 4-7 dB of voice, so it is never used.

usage: denoise.py in.wav out.wav [strength]     strength: 1.0 "firm" (default), 0.8 "gentle"
"""
import sys as _sys
if len(_sys.argv) < 3 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import re, subprocess, sys, wave
import numpy as np
import noisereduce as nr

src, dst = sys.argv[1], sys.argv[2]
strength = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
w = wave.open(src, "rb"); sr, ch = w.getframerate(), w.getnchannels()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; w.close()
if ch > 1: x = x.reshape(-1, ch).mean(axis=1)
sd = subprocess.run(["ffmpeg", "-v", "info", "-i", src, "-af", "silencedetect=noise=-38dB:d=0.4", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
gaps = [(float(a) + 0.05, float(b) - 0.05) for a, b in zip(re.findall(r"silence_start: ([\d.]+)", sd), re.findall(r"silence_end: ([\d.]+)", sd))]
noise = np.concatenate([x[int(a * sr):int(b * sr)] for a, b in gaps if b - a > 0.1]) if gaps else None
if noise is None or len(noise) < sr:              # under 1 s of pause: not enough to fingerprint, leave the audio alone
    print("denoise: not enough pause to fingerprint the background, audio left as is"); y = x
else:
    y = nr.reduce_noise(y=x, sr=sr, y_noise=noise, stationary=True, prop_decrease=strength, n_fft=2048)
    print(f"denoise: fingerprint from {len(noise) / sr:.1f}s of pauses, strength {strength}")
o = wave.open(dst, "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
o.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()
