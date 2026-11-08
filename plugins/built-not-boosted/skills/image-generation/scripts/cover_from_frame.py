#!/usr/bin/env python3
"""Build a video cover from a REAL frame of the footage: no generated face, no likeness risk.

Takes a still (--frame), a frame at a timestamp (--video + --time), or the sharpest face-forward frame in a
time range (--video + --auto START END). Cover-crops it to the exact size, adds a soft scrim, an auto-fitted
hero headline (one accent word + underline), an optional subhead ribbon and an optional small name tag, and
keeps all text inside the grid-safe zone (the centred 1:1 square, inset ~7%). Every text box is checked.

usage:
  cover_from_frame.py --video clip.mp4 --auto 0 30 --headline "OPEN BEFORE|THE SCHOOL RUN" --punch OPEN \\
      --subhead "FROM 7AM WEEKDAYS" --out cover.png --size 1080x1920
  cover_from_frame.py --frame still.png --headline "FIXED OR|FLEXIBLE?" --punch FLEXIBLE? --out c.png --size 1280x720
  cover_from_frame.py --video clip.mp4 --time 12.4 --headline "THREE|QUICK FIXES" --punch QUICK \\
      --brand brand.json --wordmark "Sam Jones|Corner Bakery" --out c.png

  --headline   1-3 lines separated by "|". Keep it to 2-5 words in total where you can.
  --punch      the ONE word or phrase shown in the accent colour (underlined).
  --brand      JSON with any of: accent, primary, ink, dark, head_ttf, body_ttf (hex colours, font file paths).
               Or pass --accent/--primary/--ink/--head-font/--body-font directly.
  --bias       0..1 vertical crop position when the frame is taller than needed (0 = top, 1 = bottom).
  --wordmark   optional small name tag, bottom-left, "Line one|Line two". Stamped here because image models
               misspell small fixed text. Omit for none.
  --size       WxH. 1080x1920 for 9:16 shorts, 1280x720 for 16:9 long-form, 1080x1350 for 4:5.

Exit 1 if any text box falls outside the safe zone. Needs Pillow + numpy; ffmpeg for --video;
OpenCV (opencv-python-headless) is optional and improves --auto and the face-clear check.
"""
import argparse, glob, json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- fonts
FONT_DIRS = [os.path.expanduser("~/.vedit/fonts"), os.path.expanduser("~/Library/Fonts"), "/Library/Fonts",
             "/System/Library/Fonts/Supplemental", "/System/Library/Fonts", os.path.expanduser("~/.local/share/fonts"),
             os.path.expanduser("~/.fonts"), "/usr/share/fonts", "/usr/local/share/fonts", "C:/Windows/Fonts"]
HEAD_CANDIDATES = ["BarlowCondensed-ExtraBold.ttf", "BarlowCondensed-Bold.ttf", "Arial Narrow Bold.ttf", "ARIALNB.TTF",
                   "LiberationSansNarrow-Bold.ttf", "DejaVuSansCondensed-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf",
                   "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
BODY_CANDIDATES = ["Inter-SemiBold.ttf", "Inter-SemiBold.otf", "Inter-Bold.otf", "Arial Bold.ttf", "arialbd.ttf",
                   "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"]


def find_font(candidates):
    for name in candidates:
        for d in FONT_DIRS:
            if not os.path.isdir(d):
                continue
            hit = os.path.join(d, name)
            if os.path.exists(hit):
                return hit
            deep = glob.glob(os.path.join(d, "**", name), recursive=True)
            if deep:
                return deep[0]
    return None


def font(path, size):
    if path:
        return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size)          # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

# ---------------------------------------------------------------- frames
def grab(video, t, out):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-q:v", "1", out, "-y"])
    return r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0


def sharpness(im):
    g = np.asarray(im.convert("L").resize((360, int(360 * im.height / im.width))), dtype=np.float32)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap.var())


_CASCADE = []


def face_box(im):
    """Largest front-on face (x0, y0, x1, y1), or None. Needs OpenCV with its bundled Haar cascades
    (opencv-python-headless 4.x; some 5.x builds ship without them, and then this quietly returns None)."""
    try:
        import cv2
        if not _CASCADE:
            xml = os.path.join(getattr(getattr(cv2, "data", None), "haarcascades", ""), "haarcascade_frontalface_alt2.xml")
            _CASCADE.append(cv2.CascadeClassifier(xml) if os.path.exists(xml) else None)
        casc = _CASCADE[0]
        if casc is None:
            return None
        g = cv2.cvtColor(np.asarray(im.convert("RGB")), cv2.COLOR_RGB2GRAY)
        fs = casc.detectMultiScale(g, 1.08, 4, minSize=(max(60, im.width // 12),) * 2)
        if len(fs):
            x, y, w, h = max(fs, key=lambda f: f[2] * f[3])
            return (int(x), int(y), int(x + w), int(y + h))
    except Exception:
        pass
    return None


def auto_pick(video, a, b, step, tmp):
    """Sharpest frame with a front-on face in [a, b]; falls back to sharpest overall."""
    scored = []
    t = a
    while t <= b:
        p = os.path.join(tmp, f"c_{t:08.2f}.png")
        if grab(video, t, p):
            im = Image.open(p)
            s = sharpness(im)
            f = face_box(im)
            score = s * (1.6 if f else 1.0)
            scored.append((score, t, p, bool(f)))
        t += step
    if not scored:
        sys.exit("ERROR: could not read any frames from the video")
    scored.sort(reverse=True)
    print("auto: best candidates (time, sharpness score, face found):")
    for sc, tt, _, f in scored[:5]:
        print(f"   {tt:7.2f}s  {sc:9.1f}  {'face' if f else '-'}")
    return scored[0][2], scored[0][1]


def cover_crop(im, W, H, bias):
    w, h = im.size
    s = max(W / w, H / h)
    im = im.resize((int(w * s + .5), int(h * s + .5)), Image.LANCZOS)
    w, h = im.size
    left = (w - W) // 2
    top = int((h - H) * max(0.0, min(1.0, bias)))
    return im.crop((left, top, left + W, top + H))

# ---------------------------------------------------------------- design
def build(base, W, H, a, br):
    img = cover_crop(base.convert("RGB"), W, H, a.bias).filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    side = min(W, H)
    landscape = W > H * 1.2
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    if landscape:
        # 16:9 long-form: a text column on the side away from the face, clear of the outer ~7% and the bottom band
        # (the duration badge sits bottom-right, a name tag bottom-left)
        side_ = a.side
        if side_ == "auto":
            fb = face_box(img)
            side_ = "left" if (fb is None or (fb[0] + fb[2]) / 2 >= W / 2) else "right"
        colw = int(W * 0.52)
        sx0 = int(W * 0.06) if side_ == "left" else W - int(W * 0.06) - colw
        sx1, sy0, sy1 = sx0 + colw, int(H * 0.08), H - int(H * 0.17)
        for x in range(W):                       # feathered darkening under the column, no hard edge
            k = (x if side_ == "left" else W - 1 - x) / (colw + int(W * 0.18))
            if k < 1:
                od.line([(x, 0), (x, H)], fill=br["dark"] + (int(190 * (1 - k) ** 1.4),))
    else:
        inset = int(side * 0.07)
        sx0, sy0 = (W - side) // 2 + inset, (H - side) // 2 + inset
        sx1, sy1 = (W - side) // 2 + side - inset, (H - side) // 2 + side - inset
        # soft scrim over the top part of the safe square (no hard band edge)
        top = max(0, sy0 - int(side * 0.12)); depth = int(side * 0.62)
        for y in range(top, min(H, top + depth)):
            k = (y - top) / depth
            fade_in = min(1.0, k / 0.18)            # no hard top edge
            od.line([(0, y), (W, y)], fill=br["dark"] + (int(185 * fade_in * (1 - k) ** 1.3),))
    SAFE = (sx0, sy0, sx1, sy1)
    maxw = int((sx1 - sx0) * 0.92)
    img = Image.alpha_composite(img.convert("RGBA"), over)
    d = ImageDraw.Draw(img)
    boxes = []

    def shadow_text(xy, t, f, fill):
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + 4, xy[1] + 6), t, font=f, fill=(0, 0, 0, 170))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
        d.text(xy, t, font=f, fill=fill)

    lines = [ln.strip() for ln in a.headline.split("|") if ln.strip()][:3]
    size = int(side * (0.22 if landscape else 0.16))
    while size > 30 and max(d.textlength(ln, font=font(br["head"], size)) for ln in lines) > maxw:
        size -= 2
    hf = font(br["head"], size)
    lh = int(size * 1.02)
    y = sy0
    punch = (a.punch or "").strip()
    under = None
    for ln in lines:
        x = sx0
        i = ln.upper().find(punch.upper()) if punch else -1
        if i >= 0:
            pre, mid, post = ln[:i], ln[i:i + len(punch)], ln[i + len(punch):]
            if pre:
                shadow_text((x, y), pre, hf, br["ink"]); x += d.textlength(pre, font=hf)
            shadow_text((x, y), mid, hf, br["accent"])
            mw = d.textlength(mid, font=hf)
            under = (int(x), y + lh, int(x + mw), y + lh + max(8, int(size * 0.09)))
            x += mw
            if post:
                shadow_text((x, y), post, hf, br["ink"])
        else:
            shadow_text((x, y), ln, hf, br["ink"])
        bb = d.textbbox((sx0, y), ln, font=hf)
        boxes.append((ln, bb))
        y += lh
    if under:
        d.rectangle(under, fill=br["primary"]); boxes.append(("underline", under))
        y = max(y, under[3])

    if a.subhead and a.subhead.strip():
        t = a.subhead.strip()
        ss = int(side * 0.05)
        while ss > 18 and d.textlength(t, font=font(br["body"], ss)) > maxw - int(side * 0.08):
            ss -= 1
        sf = font(br["body"], ss)
        pad, tab = int(side * 0.022), max(6, int(side * 0.009))
        rh = int(ss * 1.8); tw = d.textlength(t, font=sf)
        rx, ry = sx0, (y + int(side * 0.05)) if landscape else sy1 - rh
        if ry < y + int(side * 0.04):           # tall headline: put the ribbon just under it instead
            ry = y + int(side * 0.04)
        box = (rx, ry, int(rx + tab + pad * 2 + tw), ry + rh)
        d.rounded_rectangle(box, radius=max(8, rh // 5), fill=br["dark"] + (235,))
        d.rectangle((rx, ry, rx + tab, ry + rh), fill=br["accent"])
        d.text((rx + tab + pad, ry + rh // 2), t, font=sf, fill=br["ink"], anchor="lm")
        boxes.append((t, box))

    if a.wordmark:                               # small name tag in the bottom band, outside the safe square on purpose
        parts = [p for p in a.wordmark.split("|") if p.strip()][:2]
        f1, f2 = font(br["body"], max(16, int(H * 0.026))), font(br["body"], max(13, int(H * 0.02)))
        m = int(W * 0.045); bh = int(H * (0.075 if len(parts) > 1 else 0.05)); by = H - int(H * 0.035) - bh
        tw = max(d.textlength(parts[0], font=f1), d.textlength(parts[1], font=f2) if len(parts) > 1 else 0)
        barw = max(5, int(W * 0.01))
        d.rounded_rectangle((m - 10, by - 10, int(m + barw + 18 + tw + 20), by + bh + 10), radius=12, fill=br["dark"] + (240,))
        d.rectangle((m, by, m + barw, by + bh), fill=br["accent"])
        d.text((m + barw + 16, by + int(bh * (0.08 if len(parts) > 1 else 0.5))), parts[0], font=f1, fill=br["ink"],
               anchor=None if len(parts) > 1 else "lm")
        if len(parts) > 1:
            d.text((m + barw + 16, by + int(bh * 0.56)), parts[1], font=f2, fill=br["ink"])
    return img.convert("RGB"), boxes, SAFE


def main():
    ap = argparse.ArgumentParser(description="Video cover from a real frame, text kept grid-safe.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--frame"); ap.add_argument("--video"); ap.add_argument("--time", type=float)
    ap.add_argument("--auto", nargs=2, type=float, metavar=("START", "END"), help="pick the sharpest face frame in this range")
    ap.add_argument("--step", type=float, default=0.5, help="sampling step for --auto (s)")
    ap.add_argument("--headline", required=True); ap.add_argument("--punch", default="")
    ap.add_argument("--subhead", default=""); ap.add_argument("--wordmark", default="")
    ap.add_argument("--out", required=True); ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--bias", type=float, default=0.4)
    ap.add_argument("--side", choices=["auto", "left", "right"], default="auto", help="16:9 only: which side the text column sits")
    ap.add_argument("--brand"); ap.add_argument("--accent"); ap.add_argument("--primary"); ap.add_argument("--ink")
    ap.add_argument("--head-font"); ap.add_argument("--body-font")
    a = ap.parse_args()
    W, H = (int(x) for x in a.size.lower().split("x"))

    b = json.load(open(a.brand)) if a.brand else {}
    accent = a.accent or b.get("accent") or "#FFD166"
    br = {"accent": hex2rgb(accent), "primary": hex2rgb(a.primary or b.get("primary") or accent),
          "ink": hex2rgb(a.ink or b.get("ink") or "#FFFFFF"), "dark": hex2rgb(b.get("dark") or "#111111"),
          "head": a.head_font or (os.path.expanduser(b["head_ttf"]) if b.get("head_ttf") else None) or find_font(HEAD_CANDIDATES),
          "body": a.body_font or (os.path.expanduser(b["body_ttf"]) if b.get("body_ttf") else None) or find_font(BODY_CANDIDATES)}
    if not br["head"]:
        print("note: no condensed headline font found; using Pillow's default. Install Barlow Condensed or pass --head-font.")

    tmp = tempfile.mkdtemp(prefix="cover_")
    try:
        if a.frame:
            src = a.frame
        elif a.video and a.auto:
            src, t = auto_pick(a.video, a.auto[0], a.auto[1], a.step, tmp)
            print(f"auto: using the frame at {t:.2f}s")
        elif a.video and a.time is not None:
            src = os.path.join(tmp, "frame.png")
            if not grab(a.video, a.time, src):
                sys.exit(f"ERROR: could not grab a frame at {a.time}s")
        else:
            sys.exit("provide --frame, or --video with --time or --auto START END")
        img, boxes, SAFE = build(Image.open(src), W, H, a, br)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    img.save(a.out)
    shutil.rmtree(tmp, ignore_errors=True)

    bad = [(t, bb) for t, bb in boxes if bb[0] < SAFE[0] - 8 or bb[2] > SAFE[2] + 8 or bb[1] < SAFE[1] - 12 or bb[3] > SAFE[3] + 8]
    for t, bb in boxes:
        print(f"  {t!r:30} {tuple(int(v) for v in bb)}")
    print("GRID-SAFE:", "PASS" if not bad else f"FAIL {[t for t, _ in bad]} (shorten the words, or re-run with a different --bias)")
    fb = face_box(img)
    if fb:
        f2 = (fb[0], fb[1] + (fb[3] - fb[1]) // 5, fb[2], fb[3])      # brow to chin; hair is fair game
        over = [t for t, bb in boxes if min(bb[2], f2[2]) - max(bb[0], f2[0]) > 16 and min(bb[3], f2[3]) - max(bb[1], f2[1]) > 16]
        print("FACE-CLEAR:", "PASS" if not over else f"WARN text over the face: {over} (change --bias, shorten, or drop the subhead)")
    print(f"cover written: {a.out} {img.size[0]}x{img.size[1]}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
