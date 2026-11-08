"""Measure audio-vs-picture sync: mouth-region motion vs speech envelope, cross-correlated.

usage: lipsync.py <video> <t0> <t1>      (use a 40-60 s stretch where the presenter faces camera; avoid walk-ins)
prints the offset in ms: + = audio is LATE. Reference: a phone-mic clip from the same shoot reads about +0..+20 ms;
a Bluetooth hands-free mic has read +285..+295 ms. Trust it only when the peak
correlation is >= 0.15 and two windows agree. Fix by building a corrected SOURCE (video copy + audio shifted with
`-ss <offset>` on the audio input) and starting the edit again, never by swapping audio into a half-built edit.
"""
import sys as _sys
if len(_sys.argv) < 4 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import sys, subprocess, numpy as np, cv2
vid, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
fps, W = 30, 270
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_side_data=rotation",
                        "-of", "default=nokey=1:noprint_wrappers=1", vid], capture_output=True, text=True).stdout.split()
w0, h0 = int(probe[0]), int(probe[1]); rot = abs(int(float(probe[2]))) if len(probe) > 2 else 0
if rot in (90, 270): w0, h0 = h0, w0
H = int(round(h0 * W / w0 / 2) * 2)
fr = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", vid, "-vf", f"fps={fps},scale={W}:{H}",
                                   "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout, np.uint8).reshape(-1, H, W)
_xml = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
if not __import__("os").path.exists(_xml): sys.exit("this OpenCV build has no face cascades: pip install opencv-python-headless==4.10.0.84")
casc = cv2.CascadeClassifier(_xml)
# edited renders: every hard cut / reframe is a whole-frame jump that fakes a mouth-motion spike just before the speech
# starts, which reads as "audio late". Find the cuts, re-detect the face right after each, and blank motion around them.
full = np.abs(np.diff(fr.astype(np.int16), axis=0)).mean(axis=(1, 2))
cuts = set((np.where(full > np.median(full) * 6)[0] + 1).tolist()) if len(full) else set()
near = {j for c in cuts for j in range(c - 3, c + 4)}
box, mot, prev = None, [], None
for i, f in enumerate(fr):
    if i in cuts: box, prev = None, None
    if i % 3 == 0 or box is None:
        fs = casc.detectMultiScale(f, 1.15, 5, minSize=(40, 40))
        if len(fs): box = max(fs, key=lambda b: b[2] * b[3])
    if box is None: mot.append(0); prev = None; continue
    x, y, w, h = box
    roi = cv2.resize(f[y + int(.62 * h):y + int(.98 * h), x + int(.22 * w):x + int(.78 * w)], (48, 24)).astype(float)
    mot.append(0 if (prev is None or i in near) else np.abs(roi - prev).mean()); prev = roi
print(f"  ({len(cuts)} cuts/reframes masked)", end="  ")
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", vid, "-vn", "-ac", "1", "-ar", "16000",
                                  "-f", "s16le", "-"], capture_output=True).stdout, np.int16).astype(float)
hop = 16000 // fps
env = np.array([np.sqrt((a[k * hop:(k + 1) * hop] ** 2).mean()) for k in range(len(a) // hop)])
n = min(len(env), len(mot)); m, e = np.array(mot[:n]), env[:n]
m = (m - m.mean()) / (m.std() + 1e-9); e = (e - e.mean()) / (e.std() + 1e-9)
lags = list(range(-15, 16))
c = np.array([np.dot(m[:n - L], e[L:]) / (n - L) if L >= 0 else np.dot(m[-L:], e[:n + L]) / (n + L) for L in lags])
k = int(c.argmax()); off = lags[k]
if 0 < k < len(c) - 1:
    y0, y1, y2 = c[k - 1], c[k], c[k + 1]; off = lags[k] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
print(f"{t0:.0f}-{t1:.0f}s: audio offset {off * 1000 / fps:+.0f} ms (peak corr {c.max():.2f}; corr at 0 ms {c[15]:.2f})")
