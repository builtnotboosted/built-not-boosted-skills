#!/usr/bin/env python3
"""Script-anchored take finder.

Follows the spoken word stream through the script like a teleprompter (Viterbi alignment).
A backwards jump in script position = a restart, so every attempt at every script sentence
becomes a separately scored TAKE. Output: takes.json (+ a text report) for the take picker.

usage: align_takes.py transcript.json script.txt audio16k.wav out_dir
"""
import sys as _sys
if len(_sys.argv) < 5 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, re, sys, os, wave
from difflib import SequenceMatcher
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcommon import FILLERS, syn as _syn, clean as _clean

TR, SCRIPT, WAV, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)

SYN = _syn()
def clean(tok): return _clean(tok, SYN)

# ---------------- script -> sentences -> tokens ----------------
paras = [p.strip() for p in open(SCRIPT).read().split("\n") if p.strip()]
sentences = []      # {id, para, text, toks}
stoks, sent_of = [None], [None]       # index 0 = PRE (before the script)
def ntok(s): return len([c for c in (clean(x) for x in s.replace("-", " ").split()) if c])

def clauses(st):
    """Long sentences split into restartable clauses at ', and/so/but/before/because'."""
    if ntok(st) <= 16:
        return [st]
    parts = re.split(r',\s+(?=(?:and|so|but|before|because)\b)', st)
    out = []
    for p_ in parts:
        if out and (ntok(p_) < 5 or ntok(out[-1]) < 5):
            out[-1] = out[-1] + ", " + p_
        else:
            out.append(p_)
    return out

units = []
CHAPTER = re.compile(r"^\[\s*CHAPTER\b[^\]]*?(?:[•·:\-–]\s*(?P<title>[^\]]+))?\]$", re.I)
chapters, pending = [], []      # long-form [CHAPTER N • Title] markers: silent, never spoken
for pi, p in enumerate(paras):
    m = CHAPTER.match(p)
    if m:
        pending.append((m.group("title") or p.strip("[]")).strip()); continue
    if re.fullmatch(r"\[[^\]]*\]|<[^>]*>", p): continue   # shot reminder on its own line, <WALK IN> (PromptSmart tag) or [WALK IN]: never spoken
    p = re.sub(r"\s*(\[[^\]]*\]|<[^>]*>)\s*", " ", p).strip()   # an inline note is never spoken either
    if not p: continue
    if pending:
        for tt in pending: chapters.append({"title": tt, "unit": len(units)})
        pending = []
    for st in re.split(r'(?<=[.?!]["”])\s+|(?<=[.?!])\s+(?=[A-Z"“])', p):
        if st.strip():
            units += [(pi, c.strip()) for c in clauses(st.strip())]
for pi, st in units:
        if not st:
            continue
        t = st.replace("pre-set", "preset").replace("-", " ")
        toks = [c for c in (clean(x) for x in t.split()) if c]
        sid = len(sentences)
        sentences.append({"id": sid, "para": pi, "text": st, "toks": toks,
                          "q0": len(stoks), "q1": len(stoks) + len(toks) - 1})
        for tk in toks:
            stoks.append(tk); sent_of.append(sid)
N = len(stoks) - 1

# ---------------- spoken tokens (merge 3 / .5 / % etc.) ----------------
d = json.load(open(TR))
words = [w for s in d["segments"] for w in s["words"]]

# ---- gap-fill: one model can silently drop a whole retake. A long gap between words that is
#      full of speech energy = hidden words, so take them from the second transcript. ----
if len(sys.argv) > 5:
    _wv = wave.open(WAV, "rb"); _sr = _wv.getframerate()
    _A = np.frombuffer(_wv.readframes(_wv.getnframes()), dtype=np.int16).astype(np.float32) / 32768; _wv.close()
    _hop = int(_sr * 0.01)
    _db = 20 * np.log10(np.sqrt(np.convolve(_A ** 2, np.ones(_hop * 2) / (_hop * 2), mode="same")[::_hop] + 1e-10))
    _thr = np.percentile(_db, 10) + 9
    def speech_frac(a, b):
        i, j = int(a * 100), int(b * 100); return float((_db[i:j] > _thr).mean()) if j > i else 0.0
    alt = [w for s in json.load(open(sys.argv[5]))["segments"] for w in s["words"]]
    filled, nfill = [], 0
    for k, w in enumerate(words):
        filled.append(w)
        if k + 1 < len(words):
            a, b = min(w["end"], w["start"] + 0.6), words[k + 1]["start"]   # Whisper pads words over hidden speech
            if b - a > 0.7 and speech_frac(a + 0.05, b - 0.05) > 0.35:
                near = {re.sub(r"[^a-z0-9%']", "", y["word"].lower()) for y in words[max(0, k - 2):k + 3]}
                ins = [dict(x, filled=True) for x in alt if a + 0.02 < x["start"] < b - 0.05
                       and re.sub(r"[^a-z0-9%']", "", x["word"].lower()) not in near]   # never re-insert a word the primary already has
                filled += ins; nfill += len(ins)
    words = filled
    print(f"gap-fill: +{nfill} words recovered from the second transcript", file=sys.stderr)

sp = []             # {tok, w (word index)}
for wi, w in enumerate(words):
    raw = w["word"].strip()
    if sp and (re.match(r"^\.\d", raw) or raw.startswith("%")):
        sp[-1]["tok"] = sp[-1]["tok"] + raw.rstrip(".,?!").lower(); sp[-1]["w2"] = wi
        continue
    for part in raw.replace("-", " ").split():
        c = clean(part)
        if c:
            sp.append({"tok": c, "w": wi, "w2": wi})
T = len(sp)

# ---------------- emission matrix ----------------
def em_cost(a, b):
    if a == b: return 0.0
    if a in FILLERS: return 1.0
    if len(a) >= 4 and len(b) >= 4 and SequenceMatcher(None, a, b).ratio() >= 0.82: return 0.3
    return 1.0
EM = np.ones((T, N + 1))
for i, s in enumerate(sp):
    for q in range(1, N + 1):
        EM[i, q] = em_cost(s["tok"], stoks[q])

INS, INS_PRE, SKIP, JUMP, KMAX = 0.9, 0.6, 0.7, 3.0, 5
INF = 1e9
cost = np.full(N + 1, INF); bp_q = np.zeros((T, N + 1), dtype=np.int32); bp_t = np.zeros((T, N + 1), dtype=np.int8)
# types: 0=next/skip(match-or-sub) 1=insertion 2=jump
cost[0] = INS_PRE; bp_q[0, 0] = 0; bp_t[0, 0] = 1
cost[1:] = EM[0, 1:] + JUMP; cost[1] = EM[0, 1]; bp_t[0, 1:] = 2
for i in range(1, T):
    e = EM[i]; new = np.full(N + 1, INF); bq = np.zeros(N + 1, dtype=np.int32); bt = np.zeros(N + 1, dtype=np.int8)
    # insertion (stay)
    ins = cost + INS; ins[0] = cost[0] + INS_PRE
    new[:] = ins; bq[:] = np.arange(N + 1); bt[:] = 1
    # next / skip
    for k in range(1, KMAX + 1):
        cand = np.full(N + 1, INF)
        cand[k:] = cost[:-k] + (k - 1) * SKIP + e[k:]
        cand[0] = INF
        better = cand < new
        new[better] = cand[better]; bq[better] = (np.arange(N + 1) - k)[better]; bt[better] = 0
    # jump (restart backwards or big forward jump)
    g = int(np.argmin(cost)); cand = cost[g] + JUMP + e; cand[0] = INF
    better = cand < new
    new[better] = cand[better]; bq[better] = g; bt[better] = 2
    cost = new; bp_q[i] = bq; bp_t[i] = bt

# backtrace
q = int(np.argmin(cost)); path = [None] * T
for i in range(T - 1, -1, -1):
    path[i] = (q, int(bp_t[i, q]))
    q = int(bp_q[i, q])

# ---------------- audio energy for precise in/out ----------------
wv = wave.open(WAV, "rb"); sr = wv.getframerate()
A = np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16).astype(np.float32) / 32768; wv.close()
HOP = int(sr * 0.01)
rms = np.sqrt(np.convolve(A ** 2, np.ones(HOP * 2) / (HOP * 2), mode="same")[::HOP] + 1e-10)
db = 20 * np.log10(rms)
FLOOR = np.percentile(db, 10); THR = FLOOR + 9
def is_speech(t): return db[min(len(db) - 1, max(0, int(t * 100)))] > THR

def refine_in(t):        # walk back to speech onset (max 0.35s)
    x = t
    while x > t - 0.35 and is_speech(x - 0.01): x -= 0.01
    return max(0.0, x - 0.06)
def first_onset(w):
    """Where a take's first word really starts. Whisper can start it straight after the PREVIOUS take's last word and stretch it
    over the pause (e.g. 'so' timed 231.70-233.82 when the real 'So' starts at 233.8): the in-point then keeps the end of the
    previous take and a stray word is heard at the cut. A first word over 0.8 s starts at the last onset after real quiet inside it."""
    if w["end"] - w["start"] <= 0.8: return w["start"]
    ons = [x for x in onsets(w["start"], w["end"] + 0.05, min_quiet=0.3) if x > w["start"] + 0.2]
    return ons[-1] if ons else w["start"]
def refine_out(start_of_last, whisper_end):
    # first 120ms of sustained silence after the last word starts (bounded by Whisper end + 0.3)
    x = start_of_last + 0.08; lim = whisper_end + 0.3; quiet = 0.0
    while x < lim:
        quiet = quiet + 0.01 if not is_speech(x) else 0.0
        if quiet >= 0.12: return x - 0.12 + 0.09
        x += 0.01
    return min(whisper_end, lim) + 0.05

def onsets(a, b, min_quiet=0.10):
    """Speech onsets (speech after >=min_quiet of non-speech) within [a, b]."""
    out = []; quiet = 0.0; x = a
    while x <= b:
        if is_speech(x):
            if quiet >= min_quiet: out.append(round(x, 2))
            quiet = 0.0
        else:
            quiet += 0.01
        x += 0.01
    return out

def trim_end(stumble_start, next_word, after_word):
    """Where the kept speech really restarts after a stumble: the last audible onset before
    the following kept words. Whisper often places the repeated word early, inside the pause."""
    lim = (after_word["start"] if after_word else next_word["end"] + 0.5)
    lim = max(lim, next_word["end"]) + 0.05
    ons = onsets(stumble_start + 0.25, lim)
    return round(ons[-1] - 0.04, 3) if ons else refine_in(next_word["start"])

# ---------------- runs -> attempts ----------------
runs = []; cur = []; prev_q = 0
for i, (qq, ty) in enumerate(path):
    restart = (ty == 2 and qq <= prev_q and qq > 0)
    if restart and cur:
        runs.append(cur); cur = []
    cur.append(i)
    if qq > 0: prev_q = qq
runs.append(cur)

attempts = []
for ri, run in enumerate(runs):
    groups = {}            # sentence -> token idx list (in order)
    order = []
    for i in run:
        qq, ty = path[i]
        if qq == 0: continue
        sid = sent_of[qq]
        if sid not in groups: groups[sid] = []; order.append(sid)
        groups[sid].append(i)
    # boundary words that aren't in the script (ad-libbed tails / lead-ins) go to whichever
    # sentence they're spoken closest to: split the boundary run at its biggest pause
    def ws_(i): return words[sp[i]["w"]]["start"]
    def we_(i): return words[sp[i]["w2"]]["end"]
    for a, b in zip(order, order[1:]):
        ga, gb = groups[a], groups[b]
        tail = []
        while len(ga) > 1 and path[ga[-1]][1] == 1: tail.insert(0, ga.pop())
        head = []
        while len(gb) > 1 and path[gb[0]][1] == 1: head.append(gb.pop(0))
        X = tail + head
        if not X: continue
        seq_end = [we_(ga[-1])] + [we_(i) for i in X]
        seq_start = [ws_(i) for i in X] + [ws_(gb[0])]
        gaps = [seq_start[k] - seq_end[k] for k in range(len(X) + 1)]
        k = int(np.argmax(gaps))
        ga.extend(X[:k]); groups[b] = X[k:] + gb
    for sid in order:
        idx = groups[sid]; S = sentences[sid]
        matched = sorted({path[i][0] for i in idx if path[i][1] != 1 and EM[i, path[i][0]] < 1.0})
        toks = []
        for i in idx:
            qq, ty = path[i]; tok = sp[i]["tok"]
            if ty == 1:
                kind = "filler" if tok in FILLERS else "ins"
            else:
                kind = "match" if EM[i, qq] < 1.0 else "sub"
            toks.append({"i": i, "tok": tok, "kind": kind})
        # in-take restarts: an immediately repeated 1-5 word phrase -> mark the FIRST copy
        nf = [k for k, t in enumerate(toks) if t["kind"] != "filler"]
        seq = [toks[k]["tok"] for k in nf]
        for n in range(5, 0, -1):
            j = 0
            while j + 2 * n <= len(seq):
                if seq[j:j + n] == seq[j + n:j + 2 * n] and not any(toks[nf[m]]["kind"] == "repeat" for m in range(j, j + 2 * n)):
                    for m in range(j, j + n): toks[nf[m]]["kind"] = "repeat"
                    j += 2 * n
                else:
                    j += 1
        # proposed inner trims: each run of repeat/filler tokens, cut from its onset to the next kept word's onset
        inner = []; k = 0
        while k < len(toks):
            if toks[k]["kind"] in ("repeat", "filler"):
                k2 = k
                while k2 + 1 < len(toks) and toks[k2 + 1]["kind"] in ("repeat", "filler"): k2 += 1
                if k2 + 1 < len(toks):
                    a_t = refine_in(words[sp[toks[k]["i"]]["w"]]["start"])
                    nxt = words[sp[toks[k2 + 1]["i"]]["w"]]
                    aft = words[sp[toks[k2 + 2]["i"]]["w"]] if k2 + 2 < len(toks) else None
                    b_t = trim_end(a_t, nxt, aft)
                    if b_t - a_t > 0.12:
                        inner.append({"from": round(a_t, 3), "to": round(b_t, 3),
                                      "words": " ".join(t["tok"] for t in toks[k:k2 + 1])})
                k = k2 + 1
            else:
                k += 1
        wlist = sorted({w for i in idx for w in range(sp[i]["w"], sp[i]["w2"] + 1)})
        ws = [words[w] for w in wlist]
        gaps = [round(ws[k+1]["start"] - ws[k]["end"], 2) for k in range(len(ws) - 1)]
        stretched = [w["word"].strip() for w in ws if w["end"] - w["start"] > 0.9]
        lowp = [w["word"].strip() for w in ws if w["prob"] < 0.5]
        cover = len(matched) / max(1, len(S["toks"]))
        reached_end = any(m >= S["q1"] - 1 for m in matched)
        missing = [S["toks"][m - S["q0"]] for m in range(S["q0"], S["q1"] + 1) if m not in matched]
        attempts.append({
            "sid": sid, "run": ri, "w0": wlist[0], "w1": wlist[-1],
            "t0": ws[0]["start"], "t1": ws[-1]["end"],
            "in": round(refine_in(first_onset(ws[0])), 3),
            "out": round(refine_out(ws[-1]["start"], ws[-1]["end"]), 3),
            "spoken": " ".join(w["word"].strip() for w in ws),
            "toks": [{"tok": t["tok"], "kind": t["kind"]} for t in toks],
            "missing": missing, "cover": round(cover, 2), "reached_end": reached_end,
            "fillers": sum(t["kind"] == "filler" for t in toks),
            "repeats": sum(t["kind"] == "repeat" for t in toks),
            "ins": sum(t["kind"] == "ins" for t in toks),
            "subs": sum(t["kind"] == "sub" for t in toks),
            "inner_cuts": inner,
            "long_gaps": [g for g in gaps if g > 0.6], "stretched": stretched, "lowprob": lowp,
            "mean_prob": round(float(np.mean([w["prob"] for w in ws])), 3),
        })

# second-opinion transcript: where two ASR models disagree inside a take = likely mumble/garble
if len(sys.argv) > 5:
    d2 = json.load(open(sys.argv[5]))
    w2 = [w for s in d2["segments"] for w in s["words"]]
    NUM = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
           "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
    def ntoks(ws_):
        t = []
        for w in ws_:
            for part in w["word"].strip().replace("-", " ").split():
                c = clean(part)
                if not c: continue
                c = NUM.get(c, c)
                if c in ("percent", "%") and t and t[-1].isdigit(): t[-1] += "%"; continue
                t.append(c)
        return t
    for a in attempts:
        ours = ntoks(words[a["w0"]:a["w1"] + 1])
        theirs = ntoks([w for w in w2 if a["t0"] + 0.05 <= w["start"] <= a["t1"] - 0.05])
        dis = []
        for op, i1, i2, j1, j2 in SequenceMatcher(None, ours, theirs, autojunk=False).get_opcodes():
            # keep only short, interior disagreements (edges = window artefacts; long = retake timing)
            if i1 == 0 or i2 >= len(ours) or j1 == 0 or j2 >= len(theirs): continue
            if max(i2 - i1, j2 - j1) > 3: continue
            if op != "equal":
                x, y = " ".join(ours[i1:i2]), " ".join(theirs[j1:j2])
                if x.replace(" ", "") != y.replace(" ", ""):
                    dis.append(f"{x or '∅'} / {y or '∅'}")
        a["disagree"] = dis
else:
    for a in attempts: a["disagree"] = []

# abandoned: incomplete attempt followed (later in time) by another attempt of the same sentence
by_s = {}
for a in attempts: by_s.setdefault(a["sid"], []).append(a)
for sid, lst in by_s.items():
    lst.sort(key=lambda a: a["t0"])
    for k, a in enumerate(lst):
        a["complete"] = a["cover"] >= 0.7 and a["reached_end"]
        a["abandoned"] = (not a["complete"]) and k < len(lst) - 1

def score(a):
    s = 100.0
    if not a["complete"]: s -= 40
    if a["abandoned"]: s -= 20
    # stumbles that an inner trim can remove cost less than ones it can't
    fixable = len(a["inner_cuts"])
    s -= 4 * fixable + 10 * max(0, a["fillers"] + a["repeats"] - fixable) + 1.5 * a["ins"] + 2 * a["subs"]
    s -= 6 * len(a["lowprob"]) + 6 * max(0, len(a["long_gaps"])) + 5 * len(a["stretched"])
    s -= 25 * (1 - a["cover"]) if a["complete"] else 0
    s -= 5 * min(3, len(a["disagree"]))
    return round(max(0, s), 1)

result = []
for S in sentences:
    lst = sorted(by_s.get(S["id"], []), key=lambda a: a["t0"])
    for k, a in enumerate(lst):
        a["take"] = k + 1; a["score"] = score(a)
    full = [a for a in lst if a["complete"]]
    pick = None
    if full:
        best = max(a["score"] for a in full)
        pick = max((a for a in full if a["score"] >= best - 5), key=lambda a: a["t0"])   # tie -> latest
    elif lst:
        pick = max(lst, key=lambda a: a["score"])
    status = "missing" if not lst else ("red" if (pick is None or not pick["complete"] or pick["score"] < 60)
             else "amber" if (pick["score"] < 85 or len(full) > 1 and sorted(a["score"] for a in full)[-2] >= pick["score"] - 8)
             else "green")
    result.append({"sid": S["id"], "para": S["para"], "text": S["text"], "takes": lst,
                   "auto": lst.index(pick) if pick else None, "status": status})

json.dump({"source": TR, "sentences": result, "chapters": [{"title": c["title"], "first_sid": c["unit"]} for c in chapters]},
          open(os.path.join(OUT, "takes.json"), "w"), indent=1)

# ---------------- report ----------------
with open(os.path.join(OUT, "takes_report.txt"), "w") as f:
    for r in result:
        f.write(f"\n[{r['status'].upper():7s}] S{r['sid']:02d} {r['text']}\n")
        for k, a in enumerate(r["takes"]):
            mark = "*" if k == r["auto"] else " "
            flags = []
            if not a["complete"]: flags.append("INCOMPLETE")
            if a["abandoned"]: flags.append("abandoned")
            if a["fillers"]: flags.append(f"filler×{a['fillers']}")
            if a["repeats"]: flags.append(f"repeat×{a['repeats']}")
            if a["long_gaps"]: flags.append(f"gaps{a['long_gaps']}")
            if a["lowprob"]: flags.append(f"lowconf{a['lowprob']}")
            if a["stretched"]: flags.append(f"drawn{a['stretched']}")
            f.write(f"   {mark} take{a['take']} {a['in']:7.2f}-{a['out']:7.2f} score {a['score']:5.1f} "
                    f"cov {a['cover']:.2f} | {a['spoken']}\n")
            if flags: f.write(f"            {'; '.join(flags)}  missing={a['missing'][:8]}\n")
cnt = {k: sum(r["status"] == k for r in result) for k in ("green", "amber", "red", "missing")}
print(f"{len(sentences)} script sentences | {T} spoken tokens | {len(runs)} runs | {len(attempts)} takes | {cnt}")
