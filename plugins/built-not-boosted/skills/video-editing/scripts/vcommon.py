"""Shared bits for the video-editing tool: where things live, fonts, brand, project config, token cleaning,
and one Whisper interface over faster-whisper (preferred) or openai-whisper."""
import glob, json, os, re

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SKILL, "scripts")
VH = os.environ.get("VEDIT_HOME", os.path.expanduser("~/.vedit"))
VENV_PY = os.path.join(VH, "venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(VH, "venv", "bin", "python")
NODE_PATH = os.path.join(VH, "node", "node_modules")
WORK = os.path.join(VH, "work")
FONTS_HOME = os.path.join(VH, "fonts")

# ---------------------------------------------------------------- fonts (cross-platform search)
FONT_DIRS = [FONTS_HOME, os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts/Supplemental",
             "/System/Library/Fonts", os.path.expanduser("~/.local/share/fonts"), os.path.expanduser("~/.fonts"),
             "/usr/share/fonts", "/usr/local/share/fonts", "C:/Windows/Fonts"]
HEAD_FONTS = ["BarlowCondensed-ExtraBold.ttf", "BarlowCondensed-Bold.ttf", "Arial Narrow Bold.ttf", "ARIALNB.TTF",
              "LiberationSansNarrow-Bold.ttf", "DejaVuSansCondensed-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf",
              "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
BOLD_FONTS = ["Inter.ttf", "Inter-SemiBold.ttf", "Inter-SemiBold.otf", "Arial Bold.ttf", "arialbd.ttf",
              "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
REG_FONTS = ["Inter.ttf", "Inter-Regular.ttf", "Inter-Regular.otf", "Arial.ttf", "arial.ttf", "LiberationSans-Regular.ttf",
             "DejaVuSans.ttf"]


def find_font(candidates):
    for name in candidates:
        for d in FONT_DIRS:
            if not os.path.isdir(d):
                continue
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
            deep = glob.glob(os.path.join(d, "**", name), recursive=True)
            if deep:
                return deep[0]
    return None


FONT_NARROW = find_font(HEAD_FONTS)      # condensed headline face
FONT_BOLD = find_font(BOLD_FONTS)        # captions, chips, labels
FONT_REG = find_font(REG_FONTS) or FONT_BOLD

# ---------------------------------------------------------------- brand (project.json "brand" over these defaults)
# A neutral default so nothing looks like anyone else's brand. vedit.py init fills "brand" from the workspace's
# brand-profile.md (## Visual identity) when it can; edit project.json to change it.
BRAND_DEFAULT = {"accent": "#FFD166", "primary": "#FFD166", "ink": "#FFFFFF", "dark": "#141619",
                 "head_ttf": FONT_NARROW, "head_family": "Barlow Condensed",
                 "body_ttf": FONT_BOLD, "body_family": "Inter", "reg_ttf": FONT_REG,
                 "chip_text": "#111111"}


def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def brand(cfg):
    """Resolved brand. Friendlier aliases are accepted in project.json: "highlight" = accent (punch word, chips, bars,
    caption key words) and "underline" = primary (the underline under the punch word)."""
    raw = dict(cfg.get("brand") or {})
    if raw.get("highlight"): raw["accent"] = raw.pop("highlight")
    if raw.get("underline"): raw["primary"] = raw.pop("underline")
    b = dict(BRAND_DEFAULT); b.update({k: v for k, v in raw.items() if v})
    for k in ("head_ttf", "body_ttf", "reg_ttf"):
        if b.get(k): b[k] = os.path.expanduser(b[k])
    return b


def font_for_family(family, weights=("ExtraBold", "Bold", "SemiBold", "Regular", "")):
    """Find an installed font file for a family name ("Barlow Condensed" -> BarlowCondensed-ExtraBold.ttf)."""
    key = re.sub(r"[^a-z0-9]", "", family.lower())
    files = []
    for d in FONT_DIRS:
        if os.path.isdir(d):
            files += glob.glob(os.path.join(d, "**", "*.[ot]tf"), recursive=True)
    named = [f for f in files if re.sub(r"[^a-z0-9]", "", os.path.basename(f).lower()).startswith(key)]
    for w in weights:
        for f in named:
            stem = re.sub(r"[^a-z0-9]", "", os.path.splitext(os.path.basename(f))[0].lower())
            if stem == key + w.lower() or (w == "" and stem.startswith(key)):
                return f
    return named[0] if named else None


def brand_from_profile(path):
    """Read the workspace's brand/brand-profile.md "## Visual identity" table into a project.json brand block.
    Profile Primary -> highlight (punch word), Accent -> underline, Base -> dark, Light -> ink. Fonts by family name."""
    try:
        txt = open(path, encoding="utf-8").read()
    except OSError:
        return {}
    m = re.search(r"^## Visual identity\s*$(.*?)(?=^## |\Z)", txt, re.M | re.S)
    if not m:
        return {}
    sec = m.group(1); roles = {}
    for row in re.findall(r"^\|([^\n]+)\|\s*$", sec, re.M):
        cells = [c.strip() for c in row.split("|")]
        hx = next((c for c in cells if re.fullmatch(r"#[0-9a-fA-F]{6}", c)), None)
        if hx and cells: roles[cells[0].lower()] = hx.upper()
    out = {}
    if roles.get("primary"): out["highlight"] = roles["primary"]
    if roles.get("accent"): out["underline"] = roles["accent"]
    elif roles.get("primary"): out["underline"] = roles["primary"]
    if roles.get("base"): out["dark"] = roles["base"]
    if roles.get("light"): out["ink"] = roles["light"]
    fl = re.search(r"^-\s*Fonts:\s*(.+)$", sec, re.M)
    if fl:
        fams = re.findall(r"([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*)", fl.group(1))
        fams = [f for f in fams if f.lower() not in ("headline", "headlines", "body", "sub", "subheads", "labels")]
        if fams:
            h = font_for_family(fams[0]); out.update({"head_ttf": h} if h else {})
        if len(fams) > 1:
            b_ = font_for_family(fams[-1], ("SemiBold", "Bold", "Regular", "")); out.update({"body_ttf": b_} if b_ else {})
    return out


# ---------------------------------------------------------------- tokens
FILLERS = {"um", "umm", "uh", "uhm", "er", "erm", "ah", "hmm", "mm", "eh"}
# Whisper spellings -> script spellings, for alignment only. Projects add their own names via "syn" in project.json.
BASE_SYN = {"gonna": "going", "wanna": "want", "gotta": "got", "neighbors": "neighbours", "color": "colour",
            "favor": "favour", "center": "centre"}


def syn():
    s = dict(BASE_SYN)
    s.update({k.lower(): v.lower() for k, v in json.loads(os.environ.get("VEDIT_SYN", "{}")).items()})
    return s


def clean(tok, _syn=None):
    _syn = _syn if _syn is not None else syn()
    tok = tok.replace("\u2019", "'").replace("\u2018", "'").lower()
    tok = re.sub(r"(?<!\d)\.|\.(?!\d)", "", tok)
    tok = re.sub(r"[^a-z0-9%'.]", "", tok).strip("'")
    return _syn.get(tok, tok)


def vocab_prompt():
    """Filler-heavy prompt so Whisper keeps um/er, repeats and false starts; plus this video's names."""
    names = os.environ.get("VEDIT_VOCAB", "")
    return ("Umm, so, uh, so the, the thing is. Er, I mean, the, the first, the first step. "
            "Hmm, right, so, so let's, let's start. " + names).strip()


# ---------------------------------------------------------------- project
def load_project(slug_or_dir):
    d = os.path.join(WORK, slug_or_dir)                      # a slug first; a project folder path also works
    if not os.path.exists(os.path.join(d, "project.json")) and os.path.exists(os.path.join(slug_or_dir, "project.json")):
        d = slug_or_dir
    p = os.path.join(d, "project.json")
    if not os.path.exists(p):
        raise SystemExit(f"no project.json in {d} (run: vedit.py init ...)")
    cfg = json.load(open(p)); cfg["_dir"] = d
    return cfg


def frame_size(cfg):
    """(W, H): vertical shorts 1080x1920, long-form ("format": "long") 1920x1080."""
    return (1920, 1080) if cfg.get("format") == "long" else (1080, 1920)


def project_fps(cfg):
    return int(cfg.get("fps", 30))


def project_env(cfg):
    env = dict(os.environ)
    env["VEDIT_VOCAB"] = ", ".join(cfg.get("vocab", []))
    env["VEDIT_SYN"] = json.dumps(cfg.get("syn", {}))
    for k, v in (cfg.get("whisper") or {}).items():
        if k in ("large", "medium") and v: env["VEDIT_MODEL_" + k.upper()] = v
    env["NODE_PATH"] = NODE_PATH + (os.pathsep + env["NODE_PATH"] if env.get("NODE_PATH") else "")
    return env


# ---------------------------------------------------------------- Whisper (one interface, two backends)
class _W:
    """A word or segment with attribute access, shaped like faster-whisper's objects."""
    def __init__(self, **kw): self.__dict__.update(kw)


class WhisperModel:
    """faster-whisper if installed (fast, CPU int8); otherwise openai-whisper with the same call shape.
    model.transcribe(audio_float32_16k, language=, beam_size=, word_timestamps=, condition_on_previous_text=,
    initial_prompt=, ...) -> (segments iterable with .start .end .text .words[.start .end .word .probability], info)."""
    def __init__(self, name, device="cpu", compute_type="int8"):
        # lighter machines can swap the two models via project.json "whisper": {"large": "small.en", "medium": "base.en"}
        name = os.environ.get({"large-v3": "VEDIT_MODEL_LARGE", "medium.en": "VEDIT_MODEL_MEDIUM"}.get(name, "_none_"), name)
        try:
            from faster_whisper import WhisperModel as FW
            self.backend, self.m = "faster", FW(name, device=device, compute_type=compute_type)
        except ImportError:
            try:
                import whisper
            except ImportError:
                raise SystemExit("No Whisper backend: run setup.sh, or pip install faster-whisper (or openai-whisper)")
            self.backend, self.m = "openai", whisper.load_model(name, device="cpu" if device == "cpu" else device)

    def transcribe(self, audio, language="en", beam_size=5, word_timestamps=True, condition_on_previous_text=False,
                   initial_prompt=None, **kw):
        if self.backend == "faster":
            return self.m.transcribe(audio, language=language, beam_size=beam_size, word_timestamps=word_timestamps,
                                     condition_on_previous_text=condition_on_previous_text, initial_prompt=initial_prompt, **kw)
        r = self.m.transcribe(audio, language=language, beam_size=beam_size, word_timestamps=word_timestamps,
                              condition_on_previous_text=condition_on_previous_text, initial_prompt=initial_prompt, fp16=False)
        segs = [_W(start=s["start"], end=s["end"], text=s["text"],
                   words=[_W(start=w["start"], end=w["end"], word=w["word"], probability=w.get("probability", 1.0))
                          for w in s.get("words", [])]) for s in r["segments"]]
        return segs, _W(language=r.get("language", language))
