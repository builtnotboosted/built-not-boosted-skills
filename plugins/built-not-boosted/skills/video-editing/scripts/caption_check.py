"""Check the caption words against the script, and fix mishearings without overwriting the presenter's live rewordings.

usage: caption_check.py <cap.wav> <cap_tr.json> <edl.json> <report.txt>     (run by build.py's caps stage)

Why: the caption transcript is an unprompted listen of the finished cut, and it mishears sound-alikes (a short phrase heard as
nonsense, a hyphenated term split into the wrong words) and drops small words ("and", "the").

Three listens, and who wins:
  T0  the caption transcript (medium.en of the finished cut, unprompted)
  LV  the edit's large-v3 verbatim words (edl "words": the source transcript mapped to output time, unprompted)
  T1  a PROMPTED large-v3 re-listen of each line where T0 differs from the script, prompted with THAT line's script text
Rules, for each place the caption differs from the script:
  1. caption words that LV also heard (same word within 0.6 s) are what the presenter said: keep them (REWORD). A prompted
     listen parrots the script (with a long multi-line prompt it turned "directly" into "straight"), so unprompted
     agreement beats it. A short sound-alike the prompted listen hears as the script is listed as CHECK for the ear.
  2. otherwise, if T1 hears exactly the script here: use the script's words (FIX), BUT a word the caption does not have
     may only be added if T0 or LV heard it nearby (a prompt once added an unsaid "today").
  3. otherwise, if T1 is clearly closer to the script than the caption: use T1's words (FIX-HEARD), same add-rule.
  4. otherwise keep the caption and list it (CHECK) for a by-ear look.
Matching words also take the script's spelling (apostrophes, hyphens, proper-noun capitals: "customer's", "first-time", a
capitalised name); numbers are compared folded ("four percent" == "4%") and keep the caption's numerals. A word that starts a new
sentence right after a fixed block is kept. Keep prompts to one line each: longer prompts parrot more.
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

S = []                                   # script tokens of the kept lines, in edit order
for k, u in enumerate(units):
    for j, tok in enumerate(TOK.findall(u["text"])):
        S.append({"t": tok.replace("’", "'"), "first": j == 0, "u": k})

LV = [(w["o"], nt(w["w"])) for w in E.get("words", []) if w.get("o") is not None]
U = [(w["start"], nt(w["word"])) for w in T0] + LV
def lv_heard(w): return any(abs(t - w["start"]) <= 0.6 and n == nt(w["word"]) for t, n in LV)
def heard(tok, ta, tb): return any(ta - 1.0 <= t <= tb + 1.0 and n == nt(tok) for t, n in U)

ops = difflib.SequenceMatcher(None, [nt(w["word"]) for w in T0], [nt(s["t"]) for s in S], autojunk=False).get_opcodes()

# prompted re-listen, only of the lines where the caption differs from the script, one line per call
need = sorted({S[j]["u"] for op, i1, i2, j1, j2 in ops if op != "equal" for j in range(j1, j2)})
w_ = wave.open(cw, "rb"); sr = w_.getframerate(); A = np.frombuffer(w_.readframes(w_.getnframes()), np.int16).astype("float32") / 32768
dur = len(A) / sr
vocab = os.environ.get("VEDIT_VOCAB", "")
T1u = {}
if need:
    model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    for k in need:
        u = units[k]; a = max(0.0, u["o"] - 0.15); b = min(dur, (u.get("oe") or u["o"] + 5) + 0.35)
        if b - a < 0.2: continue
        # word_timestamps ON: decoding without timestamp tokens heard worse (it dropped short phrases)
        segs, _ = model.transcribe(A[int(a * sr):int(b * sr)], language="en", vad_filter=False, word_timestamps=True,
                                   initial_prompt=(vocab + ". " + u["text"]).strip(". "), condition_on_previous_text=False)
        T1u[k] = [{"word": w.word} for s in segs for w in s.words]
Sidx = {}                                 # unit -> list of global S indices
for j, s in enumerate(S): Sidx.setdefault(s["u"], []).append(j)
jmap = {}                                 # global S index -> (unit, position in T1u[unit]) where the prompted listen matches
for k, words in T1u.items():
    js = Sidx.get(k, [])
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, [nt(w["word"]) for w in words], [nt(S[j]["t"]) for j in js], autojunk=False).get_opcodes():
        if op == "equal":
            for q in range(a2 - a1): jmap[js[b1 + q]] = (k, a1 + q)

def t1_between(j1, j2):
    """what the prompted listen heard for script words j1..j2-1 (within one line): T1 words between the nearest anchors"""
    k = S[j1]["u"] if j1 < len(S) else None
    if k is None or k not in T1u or any(S[j]["u"] != k for j in range(j1, j2)): return None
    words = T1u[k]; js = Sidx[k]
    l = next((jmap[j][1] for j in range(j1 - 1, js[0] - 1, -1) if j in jmap), -1)
    r = next((jmap[j][1] for j in range(j2, js[-1] + 1) if j in jmap), len(words))
    return words[l + 1:r]

def adopt(t0w, s):
    """script spelling, caption punctuation; proper-noun capitals from the script, otherwise the caption's own case"""
    c0, sc = core(t0w["word"]), s["t"]
    if not (any(ch.isupper() for ch in sc) and not s["first"]):
        sc = sc.lower() if c0[:1].islower() else (sc[:1].upper() + sc[1:])
    lead = t0w["word"][:len(t0w["word"]) - len(t0w["word"].lstrip())]
    return lead + sc + tail(t0w["word"])

def as_words(toks, ta, tb, punct, cap):
    """tokens as caption words, timings spread over the replaced block, the block's own closing punctuation"""
    tb = max(tb, ta + 0.15 * len(toks)); step = (tb - ta) / max(1, len(toks)); out = []
    for i, t in enumerate(toks):
        if i == 0 and cap: t = t[:1].upper() + t[1:]
        out.append({"word": " " + t, "start": round(ta + i * step, 3), "end": round(ta + (i + 1) * step, 3)})
    if out and punct: out[-1]["word"] += punct
    return out

def add_ok(toks, t0s, ta, tb):
    """drop words the caption doesn't have unless an unprompted listen heard them; None if that leaves too few"""
    if len(toks) <= len(t0s): return toks, []
    keep = [t for t in toks if heard(t, ta, tb)]; dropped = [t for t in toks if t not in keep]
    return (keep if keep and len(keep) >= len(t0s) else None), dropped

log, counts = [], {"FIX": 0, "FIX-HEARD": 0, "SPELL": 0, "REWORD": 0, "AD-LIB": 0, "NOT-SAID": 0, "CHECK": 0}
out = []
for op, i1, i2, j1, j2 in ops:
    t0s, ss = T0[i1:i2], S[j1:j2]
    if op == "equal":
        for w, s in zip(t0s, ss):
            nw = adopt(w, s)
            if core(nw) != core(w["word"]):
                counts["SPELL"] += 1; log.append(f"{w['start']:7.2f}s SPELL     '{core(w['word'])}' -> '{core(nw)}'")
                w = dict(w, word=nw)
            out.append(w)
        continue
    carry = []                                          # a new sentence starting at the end of the block belongs to the next line
    while len(t0s) > 1 and re.search(r"[.?!]$", t0s[-2]["word"].strip()):
        carry.insert(0, t0s[-1]); t0s = t0s[:-1]
    ta = t0s[0]["start"] if t0s else (T0[i1 - 1]["end"] if i1 > 0 else 0.0)
    tb = t0s[-1]["end"] if t0s else (T0[i1]["start"] if i1 < len(T0) else dur)
    cap_txt, scr_txt = " ".join(core(w["word"]) for w in t0s), " ".join(s["t"] for s in ss)
    punct = tail(t0s[-1]["word"]) if t0s else ""
    capfirst = bool(t0s) and core(t0s[0]["word"])[:1].isupper()
    def done(words):
        out.extend(words); out.extend(carry)
    if not ss:                                          # caption words the script doesn't have: the presenter's own ad-lib
        counts["AD-LIB"] += 1; log.append(f"{ta:7.2f}s AD-LIB    '{cap_txt}' kept"); done(t0s); continue
    n0, nS = ns([w["word"] for w in t0s]), ns([s["t"] for s in ss])
    if n0 == nS:                                        # same letters, different tokenising ("first time" / "first-time")
        if t0s and not re.search(r"\d", n0):            # take the script's form; numbers keep the caption's numerals ("4%")
            counts["SPELL"] += 1; log.append(f"{ta:7.2f}s SPELL     '{cap_txt}' -> '{scr_txt}'")
            done(as_words([s["t"] for s in ss], ta, tb, punct, capfirst))
        else: done(t0s)
        continue
    span1 = t1_between(j1, j2)
    if t0s and all(lv_heard(w) for w in t0s):           # both unprompted listens heard the caption's words: the presenter's words
        if span1 is not None and ns([w["word"] for w in span1]) == nS and (sim(n0, nS) >= 0.5 or max(len(n0), len(nS)) <= 4):
            # ...but a short sound-alike the prompted listen hears as the script ("to/of", "their/the")
            counts["CHECK"] += 1; log.append(f"{ta:7.2f}s CHECK     '{cap_txt}' kept   (script: '{scr_txt}'; prompted listen hears the script) - check by ear")
        else:
            counts["REWORD"] += 1; log.append(f"{ta:7.2f}s REWORD    '{cap_txt}' kept   (script: '{scr_txt}')")
        done(t0s); continue
    if span1 is None:
        if not t0s: counts["NOT-SAID"] += 1; log.append(f"{ta:7.2f}s NOT-SAID  '{scr_txt}'"); done([]); continue
        counts["CHECK"] += 1; log.append(f"{ta:7.2f}s CHECK     '{cap_txt}' kept   (script: '{scr_txt}'; no re-listen) - check by ear"); done(t0s); continue
    n1, rl_txt = ns([w["word"] for w in span1]), " ".join(core(w["word"]) for w in span1)
    if n1 == nS:                                        # the prompted listen hears exactly the script here
        toks, dropped = add_ok([s["t"] for s in ss], t0s, ta, tb)
        if dropped: log.append(f"{ta:7.2f}s NOT-ADDED '{' '.join(dropped)}' (only the prompted listen heard it)")
        if toks is None:
            if not t0s: counts["NOT-SAID"] += 1; log.append(f"{ta:7.2f}s NOT-SAID  '{scr_txt}'"); done([]); continue
            counts["CHECK"] += 1; log.append(f"{ta:7.2f}s CHECK     '{cap_txt}' kept   (script: '{scr_txt}') - check by ear"); done(t0s); continue
        counts["FIX"] += 1; log.append(f"{ta:7.2f}s FIX       '{cap_txt or '(missing)'}' -> '{' '.join(toks)}'")
        done(as_words(toks, ta, tb, punct, capfirst)); continue
    if not t0s:
        counts["NOT-SAID"] += 1; log.append(f"{ta:7.2f}s NOT-SAID  '{scr_txt}' (not heard: a live reword)"); done([]); continue
    r0, r1 = sim(n0, nS), sim(n1, nS)
    if n1 and r1 >= 0.75 and r1 > r0 + 0.15:
        toks, dropped = add_ok([core(w["word"]) for w in span1], t0s, ta, tb)
        if toks is not None:
            counts["FIX-HEARD"] += 1; log.append(f"{ta:7.2f}s FIX-HEARD '{cap_txt}' -> '{' '.join(toks)}'   (script: '{scr_txt}')")
            done(as_words(toks, ta, tb, punct, capfirst)); continue
    counts["CHECK"] += 1; log.append(f"{ta:7.2f}s CHECK     '{cap_txt}' kept   (script: '{scr_txt}'; re-listen: '{rl_txt}') - check by ear")
    done(t0s)

json.dump({"segments": [{"words": out}]}, open(ct, "w"))
summary = "caption check: " + ", ".join(f"{v} {k}" for k, v in counts.items() if v) + f"  ({len(need)} of {len(units)} lines re-listened)"
open(rep, "w").write(summary + "\n" + "\n".join(log) + "\n")
print(summary + f"  (report: {rep})")
