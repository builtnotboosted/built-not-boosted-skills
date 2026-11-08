#!/usr/bin/env python3
"""QA gate: re-transcribe the RENDERED edit and prove there's one clean read of each line.

FAIL if: any script line was read more than once; any kept read has an in-take restart or is abandoned;
a filler in the opening line or two in one line (a lone natural "um" elsewhere is a note); any 4-word phrase repeats that doesn't also repeat in the script.
usage: qa_gate.py video.mp4 script.txt out_dir [--until SECONDS]   (run with the venv python)
"""
import sys as _sys
if len(_sys.argv) < 4 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, os, re, subprocess, sys
from collections import Counter

V, SCRIPT, Q = sys.argv[1], sys.argv[2], sys.argv[3]
UNTIL = float(sys.argv[sys.argv.index("--until") + 1]) if "--until" in sys.argv else None
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from vcommon import WhisperModel  # noqa: E402
PY = sys.executable
os.makedirs(Q, exist_ok=True)
wav = os.path.join(Q, "v.wav"); tr = os.path.join(Q, "transcript.json")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", V, "-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", wav], check=True)
subprocess.run([PY, os.path.join(HERE, "transcribe_v.py"), wav, tr, "medium.en"], check=True, capture_output=True)
import wave, numpy as np
wv = wave.open(wav, "rb"); A = np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16).astype(np.float32) / 32768; wv.close()
db = 20 * np.log10(np.sqrt(np.convolve(A ** 2, np.ones(320) / 320, mode="same")[::160] + 1e-10)); thr = np.percentile(db, 10) + 9
voiced = lambda a, b: float((db[int(a * 100):max(int(a * 100) + 1, int(b * 100))] > thr).mean())
TR = json.load(open(tr)); halluc = []
for seg in TR["segments"]:
    keep = []
    for w in seg["words"]:
        if voiced(w["start"], min(w["end"], w["start"] + 0.6)) < 0.25: halluc.append(f"{w['word'].strip()}@{w['start']:.1f}")
        else: keep.append(w)
    seg["words"] = keep
json.dump(TR, open(tr, "w"))
subprocess.run([PY, os.path.join(HERE, "align_takes.py"), tr, SCRIPT, wav, Q], check=True, capture_output=True)

D = json.load(open(os.path.join(Q, "takes.json")))
fails, notes = [], []
# Second opinion on a flag: over a whole video, Whisper can REPEAT a word that was said once ("and it's
# It's worth" on the long pass, a single "and it's worth" from both models on a 5 s clip) or DROP a whole line ("I won't quote
# numbers…" missing). Re-listen to just the flagged stretch of the render with both models before failing.
_MODELS = {}
_cw = lambda x: re.sub(r"[^a-z0-9%']", "", x.lower())
def iso(a, b, name, prompt=None):
    if name not in _MODELS: _MODELS[name] = WhisperModel(name, device="cpu", compute_type="int8")
    segs, _ = _MODELS[name].transcribe(A[int(max(0.0, a) * 16000):int(b * 16000)], language="en", beam_size=5,
                                       word_timestamps=True, condition_on_previous_text=False, initial_prompt=prompt)
    return [_cw(w.word) for s in segs for w in s.words if _cw(w.word)]
def iso_t(a, b, name):                     # same, with each word's start in render seconds (for the seam skip check)
    if name not in _MODELS: _MODELS[name] = WhisperModel(name, device="cpu", compute_type="int8")
    segs, _ = _MODELS[name].transcribe(A[int(max(0.0, a) * 16000):int(b * 16000)], language="en", beam_size=5,
                                       word_timestamps=True, condition_on_previous_text=False)
    return [(_cw(w.word), max(0.0, a) + w.start) for s in segs for w in s.words if _cw(w.word)]
# Third opinion for a repeat both plain listens hear: Whisper splits an unfamiliar term into a "repeat" ("assured shorthold" ->
# "a short short hold": same 0.8 s as the clean read, and BOTH models write "assured shorthold" once
# they're given the term). So listen again with the project's vocab as the prompt; a real stumble still shows ("assured short-
# they're, they're" stayed a stumble when prompted). Only the prompted listen can clear a flag, and it goes to the presenter's ear.
_PJ = next((os.path.join(p, "project.json") for p in (os.path.dirname(os.path.dirname(os.path.abspath(Q))), os.path.dirname(os.path.abspath(Q)))
            if os.path.exists(os.path.join(p, "project.json"))), None)
VOCAB = ", ".join((json.load(open(_PJ)).get("vocab") or [])) if _PJ else ""
def has_repeat(ws):
    if any(len(w) > 30 for w in ws): return True          # degenerate output ("bethethethe...") = Whisper lost the thread
    if any(ws[i] == ws[i + 1] for i in range(len(ws) - 1)): return True
    for n in (2, 3):
        g = [tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)]
        if any(g[i] in g[i + 1:i + n + 4] for i in range(len(g))): return True
    return False
first_sid = min((s["sid"] for s in D["sentences"] if s["takes"]), default=0)   # the hook line
for s in D["sentences"]:
    n = len(s["takes"])
    if n == 0: continue
    if n > 1:
        fails.append(f"L{s['sid']+1} read {n} times: " + " || ".join(t["spoken"] for t in s["takes"]))
    for t in s["takes"]:
        if t["repeats"]:
            heard = {m: iso(t["in"] - 0.3, t["out"] + 0.3, m) for m in ("medium.en", "large-v3")}
            prompted = {m: iso(t["in"] - 0.3, t["out"] + 0.3, m, VOCAB) for m in heard} if VOCAB and any(has_repeat(w) for w in heard.values()) else {}
            if prompted and not any(has_repeat(w) for w in prompted.values()):
                notes.append(f"L{s['sid']+1} plain listens hear a repeat ('{' '.join(heard['large-v3'])}') but both vocab-prompted listens "
                             f"hear one clean read ('{' '.join(prompted['large-v3'])}'): a split term, CHECK BY EAR")
            elif any(has_repeat(w) for w in heard.values()): fails.append(f"L{s['sid']+1} stumble left in: {t['spoken']}")
            else: notes.append(f"L{s['sid']+1} long-pass Whisper heard a repeat that neither model hears on an isolated listen "
                               f"('{' '.join(heard['large-v3'])}'): CHECK BY EAR")
        elif t["fillers"]:   # the odd natural "um" may stay, never in the hook, never a cluster
            if s["sid"] == first_sid or t["fillers"] >= 2: fails.append(f"L{s['sid']+1} filler in the hook line or a cluster: {t['spoken']}")
            else: notes.append(f"L{s['sid']+1} natural 'um' kept (allowed): {t['spoken']}")
        if t.get("abandoned"): fails.append(f"L{s['sid']+1} abandoned start left in: {t['spoken']}")
        if t["disagree"]: notes.append(f"L{s['sid']+1} check by ear: {t['disagree']}")

# model-independent: speech energy with no transcribed words = a hidden (dropped) read
TW = [w for seg in json.load(open(tr))["segments"] for w in seg["words"]]
# threshold relative to the presenter's SPEECH as well as the floor: a denoised render's pauses sit near digital silence, so a
# floor-only threshold counted plain room tone as "voiced" ('happen. | So' was flagged). Room tone sits >30 dB under speech.
speech_lvl = float(np.percentile(db[db > np.percentile(db, 10) + 20], 50)) if (db > np.percentile(db, 10) + 20).any() else thr
gthr = max(thr, speech_lvl - 30)
def sound_end(t, limit):          # Whisper's word-ends run 0.1-0.5 s early ("twen-ty-THREE"): the gap starts where the sound has
    i, j = int(t * 100), int(limit * 100) - 10      # really stayed under the threshold for 0.1 s
    while i < j:
        if (db[i:i + 10] <= gthr).all(): return i / 100
        i += 1
    return limit
for a, b in zip(TW, TW[1:]):
    g0, g1 = sound_end(min(a["end"], a["start"] + 0.6), b["start"]), b["start"]
    if g1 - g0 > 0.9:
        frac = float((db[int(g0 * 100) + 5:int(g1 * 100) - 5] > gthr).mean())
        if frac > 0.5:
            ws = iso(g0 - 0.1, g1 + 0.1, "large-v3")
            nb = [_cw(w["word"]) for w in TW if g0 - 6 < w["start"] < g0] + [_cw(w["word"]) for w in TW if g1 <= w["start"] < g1 + 6]
            grams = {tuple(nb[i:i + 2]) for i in range(len(nb) - 1)}
            rereads = len(ws) >= 2 and any(tuple(ws[i:i + 2]) in grams for i in range(len(ws) - 1))
            if len(ws) >= 2 and not rereads:
                notes.append(f"{g0:.1f}-{g1:.1f}s: the long pass dropped words here; isolated listen hears '{' '.join(ws)}' (new words, not a re-read)")
            else:
                fails.append(f"speech with no words at {g0:.1f}-{g1:.1f}s ({frac:.0%} voiced) — possible hidden re-read"
                             + (f"; isolated listen: '{' '.join(ws)}'" if ws else ""))

# re-read rule: the same 2-4 word phrase starting again within 1.5 s of the first copy ending
cw = lambda x: __import__("re").sub(r"[^a-z0-9%']", "", x.lower())
TT = [(cw(w["word"]), w["start"], w["end"], w["word"].strip().endswith((".", "?", "!"))) for w in TW if cw(w["word"])]
# phrases the SCRIPT itself repeats inside one sentence are deliberate ("A bit more room to negotiate, a bit less panic"):
# never a re-read (an early gate failed on exactly that)
# Also across short spans and in any number form: "5% is £10,000. 10% is 20,000. 20% is 40" is scripted, but
# Whisper joins the sentences with commas and writes "%"/"10" where the script spells "percent"/"ten".
_NUMW = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "fifteen", "twenty",
         "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion", "nought", "zero"}
def nrm(t):
    t = t.replace("%", "percent") if t != "%" else "percent"
    return "#" if (t in _NUMW or re.fullmatch(r"[£$]?[\d.,]+(percent)?", t)) else ("#percent" if re.fullmatch(r"\d+percent", t) else t)
SCRIPT_REPEATS = set()
_sw = [nrm(cw(x)) for x in re.sub(r"<[^>]*>|\[[^\]]*\]", " ", open(SCRIPT).read()).split() if cw(x)]
for n in (2, 3, 4):
    for k in range(len(_sw) - n + 1):
        g = tuple(_sw[k:k + n])
        if g in {tuple(_sw[m:m + n]) for m in range(k + 1, min(len(_sw) - n + 1, k + 30))}: SCRIPT_REPEATS.add(g)
seen = set()
for n in (4, 3, 2):
    for i in range(len(TT) - n):
        for j in range(i + n, min(len(TT) - n + 1, i + n + 6)):
            crosses_stop = any(t[3] for t in TT[i:j])          # a full stop in between = two different sentences
            if tuple(nrm(t[0]) for t in TT[i:i + n]) in SCRIPT_REPEATS: continue
            if [t[0] for t in TT[i:i + n]] == [t[0] for t in TT[j:j + n]] and TT[j][1] - TT[i + n - 1][2] <= 1.5 and not crosses_stop and (i, n) not in seen:
                seen.add((i, n))
                fails.append(f"re-read at {TT[i][1]:.1f}s: '{' '.join(t[0] for t in TT[i:i + n])}' then again at {TT[j][1]:.1f}s")
# Seam re-listen: every audio cut, heard on its own (2 s each side, both models). Over the whole video Whisper smooths a repeat
# that straddles a cut into one phrase: one edit kept "The deposit | the deposit makes up part" (a 4 s pause cut out of
# "The deposit is… the deposit makes…") and passed; a listener heard it at once. A repeat the script itself makes is fine.
_EDL = os.path.join(os.path.dirname(os.path.abspath(Q)), "edl.json")
if os.path.exists(_EDL):
    seams, o = [], 0.0
    _P = json.load(open(_EDL))["pieces"]
    for p, nx in zip(_P, _P[1:]):
        o += p["b"] - p["a"]
        if abs(nx["a"] - p["b"]) > 0.01: seams.append(o)            # a real audio cut (reframes inside one range aren't)
    if UNTIL: seams = [s for s in seams if s < UNTIL]
    def _rep(wt, s=None):
        """A repeated 1-3 word run the script doesn't make. With s: only one that STRADDLES the cut (first copy starts before it,
        second copy after it): a repeat a second or two away from the cut is the line check's job (e.g. the split term
        'assured shorthold' -> 'short short' flagged three nearby cuts)."""
        if wt and not isinstance(wt[0], tuple): wt = [(w, None) for w in wt]
        ws = [nrm(w) for w, _ in wt]
        for n in (3, 2, 1):
            for i in range(len(ws) - 2 * n + 1):
                if ws[i:i + n] == ws[i + n:i + 2 * n] and tuple(ws[i:i + n]) not in SCRIPT_REPEATS and not (n == 1 and ws[i] == "#"):
                    if s is not None and wt[i][1] is not None and not (wt[i][1] < s + 0.25 and wt[i + n][1] > s - 0.25): continue
                    return " ".join(ws[i:i + 2 * n])
        return None
    # EITHER model is enough to fail: on that seam large-v3 smoothed it away again and only medium.en heard "the deposit the
    # deposit". A seam Claude has checked by hand goes in project.json gate.allow [{t (output seconds), why}] -> a note.
    _ALLOW = ((json.load(open(_PJ)).get("gate") or {}).get("allow", [])) if _PJ else []
    # SKIPS ("a final QA that checks for all those little skips and repeats"): the words either side of a cut
    # must join up in the script. Script = the kept lines' text in order; whole lines left out on purpose don't count as a skip.
    _TK = os.path.join(os.path.dirname(_PJ), "picker", "takes.json") if _PJ else None
    _units = json.load(open(_EDL)).get("units", [])
    KEPT = {u["sid"] for u in _units}
    STOK = []                                                         # (normalised word, sid) through the whole script
    if _TK and os.path.exists(_TK):
        for sn in json.load(open(_TK))["sentences"]:
            STOK += [(nrm(_cw(x)), sn["sid"]) for x in sn["text"].split() if _cw(x)]
    # one number = one token, however it's written: "ten thousand pounds" / "£10,000", "five percent" / "5%" (
    # a false "skip" of 'pounds' because Whisper folds the word into "£")
    def _fold(seq, key=lambda x: x):
        out = []
        for x in seq:
            w = key(x)
            if out and key(out[-1]) == "#" and (w == "#" or w in ("pounds", "pound", "percent", "per", "cent", "p")): continue
            out.append(x)
        return out
    STOK = _fold(STOK, key=lambda x: x[0])
    NEVER = {}                                                        # sid -> script words the chosen take never contained
    SPOKEN = {}                                                       # sid -> the chosen take's own words (normalised)
    _pk = os.path.join(os.path.dirname(_PJ), "picker", "picks.json") if _PJ else None
    if _TK and os.path.exists(_TK) and _pk and os.path.exists(_pk):
        _picks = json.load(open(_pk))
        for sn in json.load(open(_TK))["sentences"]:
            p = _picks.get(str(sn["sid"])); n = (p or {}).get("take") or ((sn.get("auto") or 0) + 1)
            if sn["takes"] and 0 < n <= len(sn["takes"]):
                NEVER[sn["sid"]] = {nrm(_cw(x)) for x in sn["takes"][n - 1].get("missing", [])}
                SPOKEN[sn["sid"]] = _fold([nrm(_cw(x)) for x in sn["takes"][n - 1].get("spoken", "").split() if _cw(x)])
    SW = [w for w, _ in STOK]
    def _find(seq, lo, hi):                                           # script index of the end of seq, searching [lo, hi)
        n = len(seq)
        for k in range(max(0, lo), min(len(SW), hi) - n + 1):
            if SW[k:k + n] == seq: return k + n - 1
        return None
    _first = {}
    for k, (_, sid) in enumerate(STOK): _first.setdefault(sid, k)
    def _here(s):                                                     # script index of the line playing just before the cut
        u = max((u for u in _units if u.get("o") is not None and u["o"] <= s - 0.2), key=lambda u: u["o"], default=None)
        return _first.get(u["sid"], 0) if u else 0
    def _skip(words, s):
        BT = _fold([(nrm(w), t) for w, t in words if t < s - 0.05], key=lambda x: x[0])
        AT = _fold([(nrm(w), t) for w, t in words if t >= s - 0.05], key=lambda x: x[0])
        B, A = [w for w, _ in BT], [w for w, _ in AT]
        r = _join(B[-3:], A[:3], s)
        if r is not None: return r
        # STRAY words at the cut ("…done it already. | deposit. So if you've been": the end of a dropped take rode
        # in on the next line's in-point; neither a repeat nor a skip, so the seam was "can't judge"). If dropping 1-2 words
        # right at the cut makes the two sides join up with nothing missing, those words are stray.
        for db_, da in ((0, 1), (0, 2), (1, 0), (2, 0)):
            b, a = (B[:len(B) - db_] if db_ else B)[-3:], A[da:da + 3]
            if _join(b, a, s, exact=True) == "":
                # (a MISHEARD script word can't land here: its script slot would be missing, so the exact join fails)
                ex = B[len(B) - db_:] if db_ else A[:da]
                # an AD-LIB is the kept take's own word ("Now there are…", "…gone, wasted money"): a stray one comes
                # from a take that was dropped, so it isn't at that edge of the kept take
                ub = max((u for u in _units if u["o"] < s - 0.3), key=lambda u: u["o"], default=None)
                ua = min((u for u in _units if u["o"] >= s - 0.3), key=lambda u: u["o"], default=None)
                own = SPOKEN.get(ub["sid"], [])[-len(ex):] if db_ and ub else (SPOKEN.get(ua["sid"], [])[:len(ex)] if ua else [])
                if own == ex: return "ADLIB: " + " ".join(ex)
                # said in the same breath as the kept line = his own ad-lib ("Now, a quick scene setter": the take
                # finder's text starts at the script's "Quick"). A stray sits across a pause from it ("deposit… [2 s] So").
                gap = (AT[da][1] - AT[da - 1][1]) if da else (BT[len(BT) - db_][1] - BT[len(BT) - db_ - 1][1])
                if gap < 1.0: return "ADLIB: " + " ".join(ex)
                return "STRAY: " + " ".join(ex)
        return None
    def _join(before, after, s, exact=False):
        if len(before) < 2 or len(after) < 2: return None
        # a phrase can occur many times ("…% is £…" x3): try the occurrence nearest the line being played first
        here = _here(s)
        # inside the line being played first (from its start onwards), then the nearest before it (e.g. "…up to a thousand
        # pounds a year" also ends the previous line "…up to four thousand pounds a year")
        hits_b = sorted((k for k in range(len(SW)) if _find(before, k, k + len(before)) is not None), key=lambda k: (k < here, abs(k - here)))
        for kb in hits_b:
            i = kb + len(before) - 1                                  # last script word heard before the cut
            # where the words after the cut pick up; a number either side of the cut is one folded token in the script
            # ("twenty thousand. | Twenty percent" -> '#'), so then they may share it
            st = i if (after[0] == "#" and SW[i] == "#") else i + 1
            j = _find(after, st, st + 60)
            if j is None: continue
            j0 = j - len(after) + 1
            if exact and j0 != st: continue
            missed = [(w, sid) for w, sid in STOK[i + 1:j0] if sid in KEPT]
            # words the chosen take never had (the presenter didn't read them: "That's a handy bonus[, wizard style]") weren't
            # lost at the cut: report them as not read, not as a skip
            lost = [w for w, sid in missed if w not in NEVER.get(sid, set())]
            if missed and not lost: return "NOT READ: " + " ".join(w for w, _ in missed)
            return " ".join(w for w, _ in missed) if missed else ""
        return None                                                    # ad-lib / no match: can't judge this seam
    for s in seams:
        heard = {m: iso_t(s - 2.0, s + 2.0, m) for m in ("large-v3", "medium.en")}
        hits = {m: _rep(v, s) for m, v in heard.items()}
        h = next((v for v in hits.values() if v), None)
        ok = next((a for a in _ALLOW if abs(a["t"] - s) <= 0.3), None)
        # only a repeat made of pieces of a vocab term ('short' of 'assured shorthold') can be cleared by a prompted listen: a
        # prompt can smooth a real repeat away too ("the deposit | the deposit": large-v3 missed it even unprompted)
        _vt = VOCAB.lower()
        _cw2 = [w for w in set((h or "").split()) if w not in ("the", "and", "a", "an", "of")]
        _split = bool(_cw2) and all(len(w) >= 3 and w in _vt for w in _cw2)
        if _split and not any(_rep(iso(s - 2.0, s + 2.0, m, VOCAB)) for m in heard):
            notes.append(f"plain listens hear '{h}' across the cut at {s:.1f}s; both vocab-prompted listens hear no repeat (a split term): CHECK BY EAR")
            h = None
        if h:
            if ok: notes.append(f"repeat heard across the cut at {s:.1f}s ('{h}') allowed by hand: {ok['why']} (check by ear)")
            else: fails.append(f"REPEAT across the cut at {s:.1f}s: '{h}' ({', '.join(m for m, v in hits.items() if v)}, isolated listen of the seam)")
        sk = {m: _skip(v, s) for m, v in heard.items()}
        ad = next((v[7:] for v in sk.values() if v and v.startswith("ADLIB")), None)
        if ad: notes.append(f"extra word(s) at the cut at {s:.1f}s ('{ad}') are the kept take's own ad-lib, not a stray")
        sk = {m: (None if v and v.startswith("ADLIB") else v) for m, v in sk.items()}
        st_ = {m: v[7:] for m, v in sk.items() if v and v.startswith("STRAY")}
        _said = " | ".join(f"{m}: '{' '.join(w for w, t in v if t < s - 0.05)} ‖ {' '.join(w for w, t in v if t >= s - 0.05)}'" for m, v in heard.items())
        if st_:
            # one model is enough (as for repeats): medium.en heard a stray 'deposit' as 'composite'
            if ok: notes.append(f"stray word(s) at the cut at {s:.1f}s ('{next(iter(st_.values()))}') allowed by hand: {ok['why']}")
            else: fails.append(f"STRAY word(s) at the cut at {s:.1f}s: '{next(iter(st_.values()))}' ({', '.join(st_)})  [{_said}]")
            sk = {m: (None if v and v.startswith("STRAY") else v) for m, v in sk.items()}
        nr =next((v for v in sk.values() if v and v.startswith("NOT READ")), None)
        if nr:
            notes.append(f"script words never read in the chosen take, at the cut at {s:.1f}s ('{nr[10:]}'): an ad-lib, not a skip")
            sk = {m: (None if v and v.startswith("NOT READ") else v) for m, v in sk.items()}
        said = " | ".join(f"{m}: '{' '.join(w for w, t in v if t < s - 0.05)} ‖ {' '.join(w for w, t in v if t >= s - 0.05)}'" for m, v in heard.items())
        if all(sk.values()):                                          # both models agree words are missing (one alone often mishears)
            if ok: notes.append(f"words missing across the cut at {s:.1f}s ('{sk['large-v3']}') allowed by hand: {ok['why']}")
            else: fails.append(f"SKIP across the cut at {s:.1f}s: script words not heard: '{sk['large-v3']}'  [{said}]")
        elif any(sk.values()):
            notes.append(f"one model hears words missing across the cut at {s:.1f}s ('{next(v for v in sk.values() if v)}'): CHECK BY EAR  [{said}]")
    notes.append(f"final QA: listened to all {len(seams)} cuts on their own for repeats and skips")
    # WRONG CAMERA (optional; "if the subject is not looking at the main camera there is a good chance they are talking to a
    # different one"): if a gaze.json exists (see references/multicam-and-long-form.md) it says which camera he faces at each moment; a
    # stretch of 1.2 s+ where he faces one camera and the render shows another fails, unless B-roll covers it.
    _GZ = os.path.join(os.path.dirname(_PJ), "gaze.json") if _PJ else None
    if _GZ and os.path.exists(_GZ):
        G = json.load(open(_GZ)); gf, gfps = G["facing"], G["fps"]
        _cues = os.path.join(os.path.dirname(os.path.abspath(Q)), "cues.json")
        _cov = [(c["o"], c["o"] + c["dur"]) for c in (json.load(open(_cues)).get("broll", []) if os.path.exists(_cues) else [])]
        bad = []
        for p in _P:
            run = None
            for k in range(int(p["a"] * gfps) + 1, int(p["b"] * gfps)):
                w = [x for x in gf[max(0, k - 2):k + 3] if x]
                face = max(set(w), key=w.count) if len(w) >= 3 else None
                o = p["o"] + k / gfps - p["a"]
                wrong = face is not None and face != p["cam"] and not any(x <= o <= y for x, y in _cov)
                if wrong and run is None: run = [o, o, face]
                elif wrong: run[1] = o
                if (not wrong or k == int(p["b"] * gfps) - 1) and run:
                    if run[1] - run[0] + 1 / gfps >= 1.2: bad.append(run)
                    run = None
        for a_, b_, f_ in bad:
            if UNTIL and a_ > UNTIL: continue
            fails.append(f"WRONG CAMERA {int(a_ // 60)}:{a_ % 60:04.1f}-{int(b_ // 60)}:{b_ % 60:04.1f}: the presenter is talking to camera {f_}, the edit shows another (gaze.json)")
        notes.append(f"final QA: camera check against measured head direction ({len(bad)} wrong-camera stretch(es))")
if halluc: notes.append(f"ignored {len(halluc)} word(s) heard over silence (Whisper hallucination): {', '.join(halluc[:6])}")

rep = os.path.join(Q, "qa_report.txt")
with open(rep, "w") as f:
    f.write(("PASS" if not fails else "FAIL") + f" — {len(fails)} problem(s)\n")
    for x in fails: f.write("  FAIL " + x + "\n")
    for x in notes: f.write("  note " + x + "\n")
print(open(rep).read()); sys.exit(1 if fails else 0)
