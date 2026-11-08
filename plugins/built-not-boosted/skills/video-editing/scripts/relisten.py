#!/usr/bin/env python3
"""Second listen: re-transcribe EVERY take on its own (no surrounding context for Whisper to
tidy over) and add what it hears as flags + proposed trims:
  - fillers (um / er ...)
  - immediate 1-4 word repeats ("the, the")
  - a DOUBLE READ inside one take: the line restarted part-way through without going back to
    its first word ("...can come with, if you're planning on moving, see if your deal...").
    The aligner can't see these as a backwards jump, so they look like one long clean take.
    Rule: two or more of the line's own word-pairs heard more often than the script says them.
    Proposed trim: everything before the restart (keep the last read).

usage: relisten.py takes.json audio16k.wav   (updates takes.json in place)
"""
import sys as _sys
if len(_sys.argv) < 3 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, os, sys, wave
from collections import Counter, defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcommon import FILLERS, clean as _clean, syn, vocab_prompt, WhisperModel

TK, WAV = sys.argv[1:3]
SYN = syn(); clean = lambda s: _clean(s, SYN)
w = wave.open(WAV, "rb"); A = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; w.close()
SR = 16000
model = WhisperModel("medium.en", device="cpu", compute_type="int8")
D = json.load(open(TK)); added = 0


def double_read(toks, script):
    """Index in toks where a mid-line restart begins, or None."""
    sb = Counter(zip(script, script[1:]))
    occ = defaultdict(list)
    for k in range(len(toks) - 1):
        bg = (toks[k][0], toks[k + 1][0])
        if bg in sb: occ[bg].append(k)
    extra = {bg: ks for bg, ks in occ.items() if len(ks) > sb[bg]}
    if len(extra) < 2: return None
    first = min(extra, key=lambda bg: extra[bg][0])          # earliest phrase that comes round again
    return extra[first][sb[first]]                           # where its first surplus copy starts


for s in D["sentences"]:
    script = [clean(x) for x in s["text"].replace("pre-set", "preset").replace("-", " ").split()]
    script = [x for x in script if x]
    for t in s["takes"]:
        a, b = max(0, t["in"] - 0.05), t["out"] + 0.05
        segs, _ = model.transcribe(A[int(a * SR):int(b * SR)], language="en", beam_size=5, word_timestamps=True,
                                   condition_on_previous_text=False, initial_prompt=vocab_prompt(), vad_filter=False)
        ws = [x for sg in segs for x in (sg.words or [])]
        t["relisten"] = " ".join(x.word.strip() for x in ws)
        toks = [(clean(x.word), a + x.start) for x in ws if clean(x.word)]
        seq = [k for k, _ in toks]
        cuts = []
        for k, (tok, st) in enumerate(toks):                      # fillers
            if tok in FILLERS and k + 1 < len(toks): cuts.append((st - 0.03, toks[k + 1][1] - 0.03, tok))
        j = 0
        while j < len(seq):                                       # immediate 1-4 word repeats -> cut the first copy
            hit = False
            for n in range(4, 0, -1):
                if j + 2 * n <= len(seq) and seq[j:j + n] == seq[j + n:j + 2 * n] and seq[j] not in FILLERS:
                    cuts.append((toks[j][1] - 0.03, toks[j + n][1] - 0.03, " ".join(seq[j:j + n]))); j += 2 * n; hit = True; break
            if not hit: j += 1
        k2 = double_read(toks, script)                            # restart part-way through the line
        if k2 is not None and k2 > 1:
            t["double_read"] = True
            cuts.append((t["in"], toks[k2][1] - 0.03, "first read (restarted mid-line): " + " ".join(seq[:k2])))
        for c0, c1, wtxt in cuts:
            if c1 - c0 < 0.15: continue
            if any(not (c1 <= e["from"] or c0 >= e["to"]) for e in t["inner_cuts"]): continue   # already proposed
            t["inner_cuts"].append({"from": round(c0, 3), "to": round(c1, 3), "words": wtxt, "src": "second listen"})
            t["repeats"] += 1; t["score"] = round(max(0, t["score"] - 6), 1); added += 1
    # re-flag the line if its pick gained a stumble
    if s["auto"] is not None and any(c.get("src") == "second listen" for c in s["takes"][s["auto"]]["inner_cuts"]) and s["status"] == "green":
        s["status"] = "amber"
# Natural "um"s stay (people sound like themselves): a lone short filler outside the opening line is proposed
# but OFF by default; fillers in the hook, long ones (>=0.45 s) and every repeat/restart stay ON.
first_sid = min((s["sid"] for s in D["sentences"] if s["takes"]), default=0)
for s in D["sentences"]:
    for t in s["takes"]:
        for c in t["inner_cuts"]:
            if c.get("words", "").strip().lower() in FILLERS and c["to"] - c["from"] < 0.45 and s["sid"] != first_sid:
                c["default"] = False; c["why"] = "natural um: kept unless you tick it"
                if c.get("src") == "second listen":          # undo the stumble penalty: it isn't one
                    t["repeats"] = max(0, t["repeats"] - 1); t["score"] = round(min(100, t["score"] + 6), 1)
json.dump(D, open(TK, "w"), indent=1)
print(f"second listen: {sum(len(s['takes']) for s in D['sentences'])} takes re-heard, {added} new stumble(s) found")
for s in D["sentences"]:
    for t in s["takes"]:
        for c in t["inner_cuts"]:
            if c.get("src") == "second listen": print(f"  L{s['sid']+1} take{t['take']}: “{c['words'][:70]}” {c['from']:.2f}-{c['to']:.2f}")
