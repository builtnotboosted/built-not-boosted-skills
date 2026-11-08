"""Check the caption words against the script, and fix mishearings without overwriting the presenter's live rewordings.

usage: caption_check.py <cap.wav> <cap_tr.json> <edl.json> <report.txt>     (run by build.py's caps stage)

Why: the caption transcript is an unprompted listen of the finished cut, and it mishears ("baked your tig" for
"baked it in", "saffering" for "sat on", "by to let" for "buy to let") and drops small words ("moving", "and", "the").

How: align the caption words with the script text of the lines kept in the edit. Where they differ, re-listen to that
line on its own with large-v3, prompted with the line's script text:
  - prompted re-listen == script  -> it was a mishearing: use the script's words (FIX)
  - re-listen still hears the caption words -> the presenter said it differently: keep their words (REWORD: follow the spoken delivery)
  - re-listen is clearly closer to the script than the caption -> use the re-listen's words (FIX-HEARD)
  - otherwise keep the caption and list it (CHECK) for a by-ear look
Matching words also take the script's spelling (apostrophes, hyphens, proper-noun capitals: "buyer's", "the Bank").
Numbers are compared folded ("four percent" == "4%"), and the caption keeps its numerals.
"""
import sys as _sys
if len(_sys.argv) < 5 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import sys, json, re, os, wave, difflib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcommon import WhisperModel  # noqa: E402

cw, ct, edlp, rep = sys.argv[1:5]
NUMW = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
        "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "twenty": "20", "thirty": "30", "fifty": "50", "hundred": "100"}
TOK = re.compile(r"[A-Za-z0-9£%'’]+(?:-[A-Za-z0-9'’]+)*")

def nt(t):
    t = t.lower().replace("’", "'")
    t = re.sub(r"[^a-z0-9%£']", "", t).replace("'", "")
    t = NUMW.get(t, t)
    return "%" if t == "percent" else t

def ns(toks): return "".join(nt(x) for x in toks)
def sim(a, b): return difflib.SequenceMatcher(None, a, b).ratio() if (a or b) else 1.0
def core(w):
    m = TOK.search(w); return m.group(0) if m else w.strip()
def tail(w):
    c = core(w); i = w.find(c); return w[i + len(c):] if i >= 0 else ""

D = json.load(open(ct))
T0 = [dict(w) for sg in D["segments"] for w in sg["words"]]
E = json.load(open(edlp))
units = sorted([u for u in E.get("units", []) if u.get("o") is not None], key=lambda u: u["o"])
if not T0 or not units:
    open(rep, "w").write("caption check: nothing to check\n"); print("caption check: nothing to check"); sys.exit(0)

# script tokens of the kept lines, in edit order (proper-noun capitals = capitalised and not the first word of its line)
S = []
for k, u in enumerate(units):
    for j, tok in enumerate(TOK.findall(u["text"])):
        S.append({"t": tok.replace("’", "'"), "u": k, "first": j == 0})

# prompted re-listen, one kept line at a time
w_ = wave.open(cw, "rb"); sr = w_.getframerate(); A = np.frombuffer(w_.readframes(w_.getnframes()), np.int16).astype("float32") / 32768
dur = len(A) / sr
vocab = os.environ.get("VEDIT_VOCAB", "")
model = WhisperModel("large-v3", device="cpu", compute_type="int8")
T1 = []
for k, u in enumerate(units):
    a = max(0.0, u["o"] - 0.15); b = min(dur, (u.get("oe") or u["o"] + 5) + 0.35)
    nxt = units[k + 1]["o"] if k + 1 < len(units) else dur + 1
    if b - a < 0.2: continue
    segs, _ = model.transcribe(A[int(a * sr):int(b * sr)], language="en", vad_filter=False, word_timestamps=True,
                               initial_prompt=(vocab + ". " + u["text"]).strip(". "), condition_on_previous_text=False)
    for sg in segs:
        for w in sg.words:
            st = a + w.start
            if (k == 0 or st >= u["o"] - 0.15) and st < nxt - 0.05:
                T1.append({"word": w.word, "start": round(st, 3), "end": round(a + w.end, 3)})
T1.sort(key=lambda w: w["start"])

def adopt(t0w, s):
    """script spelling, caption punctuation; proper-noun capitals from the script, otherwise the caption's own case"""
    c0, sc = core(t0w["word"]), s["t"]
    if not (any(ch.isupper() for ch in sc) and not s["first"]):
        sc = sc.lower() if c0[:1].islower() else (sc[:1].upper() + sc[1:])
    lead = t0w["word"][:len(t0w["word"]) - len(t0w["word"].lstrip())]
    return lead + sc + tail(t0w["word"])

def new_words(stoks, span_t1, ta, tb, punct):
    """script tokens as caption words; timings from the re-listen when it has the same count, else spread over the gap"""
    out = []
    if len(span_t1) == len(stoks):
        for s, w in zip(stoks, span_t1): out.append({"word": " " + s["t"], "start": w["start"], "end": w["end"]})
    else:
        tb = max(tb, ta + 0.15 * len(stoks)); step = (tb - ta) / max(1, len(stoks))
        for i, s in enumerate(stoks): out.append({"word": " " + s["t"], "start": round(ta + i * step, 3), "end": round(ta + (i + 1) * step, 3)})
    if out and punct: out[-1]["word"] += punct
    return out

log, counts = [], {"FIX": 0, "FIX-HEARD": 0, "SPELL": 0, "REWORD": 0, "AD-LIB": 0, "NOT-SAID": 0, "CHECK": 0}
out = []
sm = difflib.SequenceMatcher(None, [nt(w["word"]) for w in T0], [nt(s["t"]) for s in S], autojunk=False)
for op, i1, i2, j1, j2 in sm.get_opcodes():
    t0s, ss = T0[i1:i2], S[j1:j2]
    if op == "equal":
        for w, s in zip(t0s, ss):
            nw = adopt(w, s)
            if core(nw) != core(w["word"]):
                counts["SPELL"] += 1; log.append(f"{w['start']:7.2f}s SPELL     '{core(w['word'])}' -> '{core(nw)}'")
                w = dict(w, word=nw)
            out.append(w)
        continue
    ta = T0[i1 - 1]["end"] if i1 > 0 else 0.0
    tb = T0[i2]["start"] if i2 < len(T0) else dur
    span1 = [w for w in T1 if ta - 0.05 <= w["start"] < tb + 0.05]
    cap_txt, scr_txt, rl_txt = " ".join(core(w["word"]) for w in t0s), " ".join(s["t"] for s in ss), " ".join(core(w["word"]) for w in span1)
    n0, nS, n1 = ns([w["word"] for w in t0s]), ns([s["t"] for s in ss]), ns([w["word"] for w in span1])
    punct = tail(t0s[-1]["word"]) if t0s else ""
    if not ss:                                          # caption words the script doesn't have: the presenter's own ad-lib
        counts["AD-LIB"] += 1; log.append(f"{ta:7.2f}s AD-LIB    '{cap_txt}' kept"); out.extend(t0s); continue
    if n0 == nS:                                        # same words, different tokenising/number form ("4%" / "four percent")
        out.extend(t0s); continue
    if n1 == nS:
        counts["FIX"] += 1
        log.append(f"{ta:7.2f}s FIX       '{cap_txt}' -> '{scr_txt}'   (prompted re-listen hears the script)")
        out.extend(new_words(ss, span1, ta if not t0s else t0s[0]["start"], tb if not t0s else t0s[-1]["end"], punct)); continue
    if not t0s:                                         # script words the captions don't have, and the re-listen doesn't hear them
        counts["NOT-SAID"] += 1; log.append(f"{ta:7.2f}s NOT-SAID  '{scr_txt}' (not in the audio: a live reword)"); continue
    r0, r1, r01 = sim(n0, nS), sim(n1, nS), sim(n0, n1)
    if n1 and r1 >= 0.8 and r1 > r0 + 0.15:
        counts["FIX-HEARD"] += 1
        log.append(f"{ta:7.2f}s FIX-HEARD '{cap_txt}' -> '{rl_txt}'   (script: '{scr_txt}')")
        nw = [dict(w) for w in span1]
        if nw and punct: nw[-1]["word"] = nw[-1]["word"].rstrip(".,?!") + punct
        out.extend(nw); continue
    if r01 >= 0.75:
        counts["REWORD"] += 1; log.append(f"{ta:7.2f}s REWORD    '{cap_txt}' kept   (script: '{scr_txt}'; re-listen agrees with the caption)")
    else:
        counts["CHECK"] += 1; log.append(f"{ta:7.2f}s CHECK     '{cap_txt}' kept   (script: '{scr_txt}'; re-listen: '{rl_txt}') - check by ear")
    out.extend(t0s)

D2 = {"segments": [{"words": out}]}
json.dump(D2, open(ct, "w"))
summary = "caption check: " + ", ".join(f"{v} {k}" for k, v in counts.items() if v)
open(rep, "w").write(summary + "\n" + "\n".join(log) + "\n")
print(summary + f"  (report: {rep})")
