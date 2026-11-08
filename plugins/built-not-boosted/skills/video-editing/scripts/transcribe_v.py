#!/usr/bin/env python3
"""Verbatim (disfluency-keeping) transcription with word timestamps.
The initial_prompt full of fillers/restarts nudges Whisper to transcribe um/er, repeats and
false starts instead of tidying them away."""
import sys as _sys
if len(_sys.argv) < 3 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, sys, time, wave
import numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from vcommon import vocab_prompt, WhisperModel

WAV, OUT = sys.argv[1], sys.argv[2]
MODEL = sys.argv[3] if len(sys.argv) > 3 else "large-v3"
PROMPT = vocab_prompt()          # fillers + this video's names (VEDIT_VOCAB)

w = wave.open(WAV, "rb"); raw = w.readframes(w.getnframes()); w.close()
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
t0 = time.time()
model = WhisperModel(MODEL, device="cpu", compute_type="int8")
print(f"model {MODEL} loaded {time.time()-t0:.0f}s", flush=True)
segs, info = model.transcribe(
    audio, language="en", beam_size=5, word_timestamps=True,
    condition_on_previous_text=False, vad_filter=False,
    initial_prompt=PROMPT, suppress_tokens=[], suppress_blank=False,
)
out = {"model": MODEL, "verbatim": True, "duration": len(audio)/16000, "segments": []}
for s in segs:
    out["segments"].append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text,
        "words": [{"start": round(x.start, 3), "end": round(x.end, 3), "word": x.word,
                   "prob": round(x.probability, 3)} for x in (s.words or [])]})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", flush=True)
json.dump(out, open(OUT, "w"), indent=2)
print(f"DONE {time.time()-t0:.0f}s -> {OUT}", flush=True)
