#!/usr/bin/env python3
"""Refill words Whisper skipped in a caption transcript.

Whisper sometimes stretches one word over a whole phrase and drops the words under it (one caption read
"But there are a[25.9-29.3] a look." for "But there are a couple of old superstitions that get passed around like
gospel, so let's have a proper look"). The audio was fine; the CAPTION was missing 13 words. For every word longer than
1.0 s that sits over speech, re-transcribe that stretch on its own with both models and splice in the fuller result.

usage: refill_words.py audio.wav transcript.json        (edits transcript.json in place; run with the venv python)
"""
import sys as _sys
if len(_sys.argv) < 3 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, sys, wave
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcommon import WhisperModel  # noqa: E402

WAV, TR = sys.argv[1], sys.argv[2]
w = wave.open(WAV, "rb"); A = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; w.close()
db = 20 * np.log10(np.sqrt(np.convolve(A ** 2, np.ones(160) / 160, mode="same")[::160] + 1e-10))   # 10 ms
thr = float(np.percentile(db, 10)) + 12
D = json.load(open(TR))
_M = {}
def listen(a, b, name):
    if name not in _M: _M[name] = WhisperModel(name, device="cpu", compute_type="int8")
    segs, _ = _M[name].transcribe(A[int(max(0, a) * 16000):int(b * 16000)], language="en", beam_size=5,
                                  word_timestamps=True, condition_on_previous_text=False)
    return [{"word": " " + x.word.strip(), "start": round(max(0, a) + x.start, 3), "end": round(max(0, a) + x.end, 3),
             "probability": x.probability} for s in segs for x in s.words if x.word.strip()]
fixed = 0
# one flat word list: the words after a stretch are often in Whisper's NEXT segment
words = [x for seg in D["segments"] for x in seg["words"]]
D["segments"] = [{"start": words[0]["start"] if words else 0, "end": words[-1]["end"] if words else 0, "text": "", "words": words}]
for seg in D["segments"]:
    out = []; skip_to = -1.0
    for k, x in enumerate(words):
        if x["start"] < skip_to: continue                            # already covered by a refilled stretch
        dur = x["end"] - x["start"]
        voiced = float((db[int(x["start"] * 100):int(x["end"] * 100)] > thr).mean()) if dur > 0 else 0
        # a spoken figure is legitimately long ("£296" + ",285" = "two hundred and ninety-six thousand…"): leave numbers
        if dur > 1.0 and voiced > 0.4 and not any(ch.isdigit() for ch in x["word"]):
            # take over the next words up to 0.8 s past the stretch too: the stretch's real end is unknown, and the long pass
            # leaves a stray copy there ("…have a proper | a look": the refill ended on 'proper', the old 'a' doubled it)
            nxt = [y for y in words[k + 1:] if y["start"] < x["end"] + 0.8]
            a, b = x["start"] - 0.05, max([x["end"]] + [y["end"] for y in nxt]) + 0.05
            cands = [listen(a, b, m) for m in ("large-v3", "medium.en")]
            best = max(cands, key=len)
            if len(best) >= 2 + len(nxt):
                out += best; fixed += 1; skip_to = b - 0.05 + 1e-6
                print(f"refilled {x['start']:.1f}-{x['end']:.1f}s: '{x['word'].strip()}' -> '{' '.join(w['word'].strip() for w in best)}'")
                continue
        out.append(x)
    seg["words"] = out
json.dump(D, open(TR, "w"))
print(f"refill: {fixed} stretched word(s) re-listened")
