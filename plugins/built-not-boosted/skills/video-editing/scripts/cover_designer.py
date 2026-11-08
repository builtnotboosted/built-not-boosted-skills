#!/usr/bin/env python3
"""Pushed real-frame cover with hero type inside the grid-safe square.

Real frame -> gentle reframe (scale + offset, Lanczos + sharpen) -> warm grade -> soft dark zones
for type -> hero headline (condensed head font: ink top line, ACCENT punch lines, primary underline)
-> optional subhead chip -> optional small name tag (wordmark) bottom-left.
Every text box is checked against the grid-safe box, and against the face if OpenCV can find one;
exit 1 if anything is outside the box or over the face.

usage: cover_designer.py frame.png variant.json out.png
variant.json: {"top": "THREE THINGS", "hero": ["TO CHECK"], "hero_size": 300, "chip": ["BEFORE YOU", "SIGN ANYTHING"],
               "chip_size": 52, "reframe": {"scale": 1.12, "x": 0, "y": 64},
               "brand": {...}, "wordmark": ["Your Name", "What you do"], "format": "short"|"long"}
               (optional: hero_gap, line_gap, hero_dx, chip_gap, top_size; long-form: *_size_long)
"""
import sys as _sys
if len(_sys.argv) < 4 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcommon import BRAND_DEFAULT, hex2rgb

FRAME, VSPEC, OUT = sys.argv[1:4]
V = json.load(open(VSPEC))
_B = dict(BRAND_DEFAULT); _B.update({k: v for k, v in (V.get("brand") or {}).items() if v})
LIME, GREEN, WHITE, CHAR = hex2rgb(_B["accent"]), hex2rgb(_B["primary"]), hex2rgb(_B["ink"]), hex2rgb(_B.get("dark") or "#141619")
FONT_NARROW = os.path.expanduser(_B["head_ttf"] or "") or None
FONT_BOLD = os.path.expanduser(_B["body_ttf"] or "") or None
FONT_REG = os.path.expanduser(_B.get("reg_ttf") or "") or FONT_BOLD
if not (FONT_NARROW and FONT_BOLD):
    sys.exit("cover: no fonts found; run setup.sh (fetches Barlow Condensed + Inter) or set brand head_ttf/body_ttf")
CHIP_TEXT = WHITE

def stamp(img, size):
    """Optional small name tag bottom-left (variant "wordmark": ["Name", "What you do"]), then save at the exact size.
    Stamped here rather than generated, because image models misspell small fixed text."""
    W_, H_ = (int(x) for x in size.split("x"))
    im = img.convert("RGB")
    if im.size != (W_, H_):
        im = im.resize((W_, H_), Image.LANCZOS)
    lines = [l for l in (V.get("wordmark") or []) if l][:2]
    if lines and not V.get("unbranded"):
        d = ImageDraw.Draw(im); M = int(W_ * 0.045)
        f1 = ImageFont.truetype(FONT_BOLD, max(18, int(H_ * 0.030))); f2 = ImageFont.truetype(FONT_REG, max(14, int(H_ * 0.024)))
        tw = max(d.textlength(lines[0], font=f1), d.textlength(lines[1], font=f2) if len(lines) > 1 else 0)
        barw = max(6, int(W_ * 0.012)); bh = int(H_ * (0.092 if len(lines) > 1 else 0.06)); bx, by = M, H_ - int(H_ * 0.105)
        d.rounded_rectangle([bx - 10, by - 10, bx + barw + 18 + tw + 24, by + bh + 10], radius=14, fill=CHAR)
        d.rectangle([bx, by, bx + barw, by + bh], fill=LIME)
        d.text((bx + barw + 18, by + int(bh * 0.10)), lines[0], font=f1, fill=WHITE)
        if len(lines) > 1: d.text((bx + barw + 18, by + int(bh * 0.55)), lines[1], font=f2, fill=WHITE)
    im.save(OUT, "PNG")
    return 0

if V.get("format") == "long":
    # ---------- YouTube long-form thumbnail, 1280x720 (real frame) ----------
    W, H = 1280, 720
    R = {"scale": 1.0, "x": 0, "y": 0, **V.get("reframe", {})}
    src = Image.open(FRAME).convert("RGB")
    sw, sh = src.size
    big = src.resize((int(sw * R["scale"]), int(sh * R["scale"])), Image.LANCZOS)
    cx, cy = R["x"], R["y"]
    img = big.crop((cx, cy, cx + sw, cy + sh)).resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=80, threshold=2))
    r_, g_, b_ = img.split()
    img = Image.merge("RGB", (r_.point(lambda v: min(255, int(v * 1.035))), g_, b_.point(lambda v: int(v * 0.955))))
    img = img.point(lambda v: v if v < 196 else int(196 + (v - 196) * 0.55))
    img = ImageEnhance.Color(ImageEnhance.Contrast(img).enhance(1.07)).enhance(1.05).convert("RGBA")
    fx = V.get("face_x") or 960
    text_left = fx >= 960                       # text on the side away from the presenter's face
    IN_X, IN_Y = int(W * 0.06), int(H * 0.07)
    COLW = int(W * 0.50)
    X0 = IN_X if text_left else W - IN_X - COLW
    # even darkening under the whole text column, feathered 240 px into the picture (no hard edge)
    solid, feath = COLW + IN_X + 30, 240
    prof = [190] * solid + [int(190 * (1 - i / (feath - 1)) ** 1.4) for i in range(feath)]
    prof = (prof + [0] * W)[:W]
    m = Image.new("L", (W, 1)); m.putdata(prof if text_left else prof[::-1]); mask = m.resize((W, H))
    lay = Image.new("RGBA", (W, H), CHAR + (0,)); lay.putalpha(mask); img.alpha_composite(lay)
    draw = ImageDraw.Draw(img); boxes = []
    def fitw(t, maxw, start):
        z = start
        while z > 30 and draw.textlength(t, font=ImageFont.truetype(FONT_NARROW, z)) > maxw: z -= 2
        return z
    def text(xy, t, size, fill):
        f = ImageFont.truetype(FONT_NARROW, size)
        sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh_).text((xy[0] + 3, xy[1] + 5), t, font=f, fill=(0, 0, 0, 170))
        img.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(4))); draw.text(xy, t, font=f, fill=fill)
        bb = draw.textbbox(xy, t, font=f); boxes.append((t, bb)); return bb
    bb = text((X0, IN_Y), V["top"], fitw(V["top"], COLW, V.get("top_size_long", 96)), WHITE)
    y = bb[3] + 10; hb = []
    for ln in V["hero"]:
        hb.append(text((X0 - 3, y), ln, fitw(ln, COLW, V.get("hero_size_long", 200)), LIME)); y = hb[-1][3] + 8
    ub = (X0, hb[-1][3] + 12, max(x[2] for x in hb), hb[-1][3] + 24); draw.rectangle(ub, fill=GREEN); boxes.append(("underline", ub))
    if V.get("chip"):
        f = ImageFont.truetype(FONT_BOLD, V.get("chip_size_long", 30)); pad, tab, lh = 16, 9, int(V.get("chip_size_long", 30) * 1.22)
        tw = max(draw.textlength(l, font=f) for l in V["chip"]); cy0 = ub[3] + 18; ch = lh * len(V["chip"]) + pad * 1.4
        draw.rounded_rectangle([X0, cy0, X0 + tab + pad * 2 + tw, cy0 + ch], radius=10, fill=CHAR + (238,))
        draw.rectangle([X0, cy0, X0 + tab, cy0 + ch], fill=LIME)
        for i, l in enumerate(V["chip"]): draw.text((X0 + tab + pad, cy0 + pad * 0.7 + i * lh), l, font=f, fill=WHITE)
        boxes.append((" ".join(V["chip"]), (X0, cy0, int(X0 + tab + pad * 2 + tw), int(cy0 + ch))))
    SAFE = (IN_X, IN_Y, W - IN_X, H - int(H * 0.16))          # keep clear of the wordmark band at the foot
    TIMESTAMP = (W - 200, H - 70, W, H)                         # YouTube's duration badge
    bad = [(t, b_) for t, b_ in boxes if b_[0] < SAFE[0] - 6 or b_[2] > SAFE[2] + 6 or b_[1] < SAFE[1] - 10 or b_[3] > SAFE[3]
           or not (b_[2] < TIMESTAMP[0] or b_[3] < TIMESTAMP[1])]
    for t, b_ in boxes: print(f"  {t!r:28} {b_}")
    print("THUMBNAIL-SAFE:", "PASS" if not bad else f"FAIL {bad}")
    sys.exit(stamp(img, f"{W}x{H}") or (1 if bad else 0))

W, H = 1080, 1920
SQ_TOP = (H - W) // 2                    # centred 1:1 grid square: y 420..1500
INSET = int(W * 0.07)                    # >=7% inset every side (§0e)
SAFE = (INSET, SQ_TOP + INSET, W - INSET, SQ_TOP + W - INSET)

# ---------- 1. reframe (keep scale <= 1.12 on 1080p phone footage: ears clip and detail goes soft) ----------
R = {"scale": 1.12, "x": 0, "y": 64, **V.get("reframe", {})}
src = Image.open(FRAME).convert("RGB")
big = src.resize((int(W * R["scale"]), int(H * R["scale"])), Image.LANCZOS)
# x/y are the crop's top-left in the zoomed frame: 0 .. (scale-1)*size. Outside that the crop runs off the picture and leaves a
# black bar (e.g. y=-55 to push the face down). y=0 puts the face as LOW as it goes; more y moves it up.
_cx = min(max(0, R["x"]), big.width - W); _cy = min(max(0, R["y"]), big.height - H)
if (_cx, _cy) != (R["x"], R["y"]): print(f"reframe x/y clamped to ({_cx}, {_cy}): allowed 0..{big.width - W} / 0..{big.height - H}")
R["x"], R["y"] = _cx, _cy
img = big.crop((R["x"], R["y"], R["x"] + W, R["y"] + H)).filter(ImageFilter.UnsharpMask(radius=2.2, percent=85, threshold=2))
# face zone (brow to chin) on the reframed frame: type may sit on hair or sky, never on the face (a chip over the face is the usual offender)
FACE = None
try:
    import cv2, numpy as _np
    _g = cv2.cvtColor(_np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    _xml = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"   # bundled with opencv-python-headless 4.x
    if not os.path.exists(_xml): raise RuntimeError("this OpenCV build has no face cascades (install opencv-python-headless==4.10.0.84)")
    _fs = cv2.CascadeClassifier(_xml).detectMultiScale(_g, 1.08, 4, minSize=(160, 160))
    if len(_fs):
        _x, _y, _w, _h = max(_fs, key=lambda f: f[2] * f[3]); FACE = (int(_x), int(_y + 0.18 * _h), int(_x + _w), int(_y + _h))
except Exception as _e: print("face check skipped:", _e)

# ---------- 2. grade: warmer, a touch more contrast, tame a white sky ----------
r, g, b = img.split()
img = Image.merge("RGB", (r.point(lambda v: min(255, int(v * 1.035))), g, b.point(lambda v: int(v * 0.955))))
img = img.point(lambda v: v if v < 196 else int(196 + (v - 196) * 0.55))
img = ImageEnhance.Contrast(img).enhance(1.07)
img = ImageEnhance.Color(img).enhance(1.05).convert("RGBA")

# ---------- 3. soft dark zones for type (top band + left column), no hard edges ----------
def ramp(n, a0, a1, g=1.3): return [int(a0 + (a1 - a0) * (i / (n - 1)) ** g) for i in range(n)]
def strip(vals, horizontal, w, h):
    im = Image.new("L", (len(vals), 1) if horizontal else (1, len(vals))); im.putdata(vals)
    return im.resize((w, h), Image.BILINEAR)
def feather(h, a, b, c, d):
    return [0 if y < a else int(255 * (y - a) / (b - a)) if y < b else 255 if y < c else int(255 * (d - y) / (d - c)) if y < d else 0 for y in range(h)]
def layer(mask):
    lay = Image.new("RGBA", (W, H), CHAR + (0,)); lay.putalpha(mask); return lay
top = Image.new("L", (W, H), 0); top.paste(strip(ramp(1200, 168, 0, 1.05), False, W, 1200), (0, 0)); img.alpha_composite(layer(top))
col = Image.new("L", (W, H), 0); col.paste(strip(ramp(660, 170, 0, 1.25), True, 660, H), (0, 0))
col = ImageChops.multiply(col, strip(feather(H, 420, 700, 1380, 1680), False, W, H)); img.alpha_composite(layer(col))
vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse((-260, -200, W + 260, H + 200), fill=255); vig = vig.filter(ImageFilter.GaussianBlur(160))
dark = Image.new("RGBA", (W, H), (0, 0, 0, 90)); dark.putalpha(Image.eval(vig, lambda v: int((255 - v) * 0.35))); img.alpha_composite(dark)

draw = ImageDraw.Draw(img); boxes = []
def text(xy, s, size, fill, font=FONT_NARROW):
    f = ImageFont.truetype(font, size)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + 5, xy[1] + 7), s, font=f, fill=(0, 0, 0, 170))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    draw.text(xy, s, font=f, fill=fill)
    bb = draw.textbbox(xy, s, font=f); boxes.append((s, bb)); return bb
def fit(s, maxw, start, font=FONT_NARROW):
    sz = start
    while sz > 40 and draw.textlength(s, font=ImageFont.truetype(font, sz)) > maxw: sz -= 2
    return sz
def chip(x, y, lines, size=44):
    f = ImageFont.truetype(FONT_BOLD, size); pad, tab, lh = 24, 12, int(size * 1.22)
    tw = max(draw.textlength(l, font=f) for l in lines); h = lh * len(lines) + pad * 1.4
    draw.rounded_rectangle([x, y, x + tab + pad * 2 + tw, y + h], radius=14, fill=CHAR + (238,))
    draw.rectangle([x, y, x + tab, y + h], fill=LIME)
    for i, l in enumerate(lines): draw.text((x + tab + pad, y + pad * 0.7 + i * lh), l, font=f, fill=CHIP_TEXT)
    boxes.append((" ".join(lines), (x, y, int(x + tab + pad * 2 + tw), int(y + h))))

# ---------- 4. type: white top line (fitted), lime punch line(s), green underline, chip ----------
L, Rx = SAFE[0], SAFE[2]
bb = text((L, SAFE[1] - 8), V["top"], fit(V["top"], int((Rx - L) * 0.92), V.get("top_size", 190)), WHITE)
y, dx, hb = bb[3] + V.get("hero_gap", 22), V.get("hero_dx", -6), []
for ln in V["hero"]:
    sz = fit(ln, Rx - L, V.get("hero_size", 160))
    hb.append(text((L + dx, y), ln, sz, LIME)); y = hb[-1][3] + V.get("line_gap", 16)
ub = (L, hb[-1][3] + 18, max(x[2] for x in hb), hb[-1][3] + 40)
draw.rectangle(ub, fill=GREEN); boxes.append(("underline", ub))
if V.get("chip"): chip(L, ub[3] + V.get("chip_gap", 30), V["chip"], V.get("chip_size", 46))

# ---------- 5. grid-safe check, then the optional name tag ----------
bad = [(s, b_) for s, b_ in boxes if b_[0] < SAFE[0] - 8 or b_[2] > SAFE[2] + 8 or b_[1] < SAFE[1] - 12 or b_[3] > SAFE[3] + 8]
for s, b_ in boxes: print(f"  {s!r:28} {b_}")
print("GRID-SAFE:", "PASS" if not bad else f"FAIL {bad}")
def _depth(b_): return min(min(b_[2], FACE[2]) - max(b_[0], FACE[0]), min(b_[3], FACE[3]) - max(b_[1], FACE[1]))
over = [(s, b_) for s, b_ in boxes if FACE and _depth(b_) >= 16]      # a corner grazing the hairline is fine; ~90 px into the face is not
print("FACE-CLEAR:", ("PASS" if not over else f"FAIL type over the face {FACE}: {[s for s, _ in over]} (drop the chip, shrink the hero, or reframe y)") if FACE else "no face found: check by eye")
bad = bad + over
sys.exit(stamp(img, f"{W}x{H}") or (1 if bad else 0))
