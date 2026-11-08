#!/usr/bin/env python3
"""Check a finished image: true dimensions, file size, and what the profile grid will show.

usage: check_image.py IMAGE [--expect WxH] [--grid] [--max-mb 2]

  --expect WxH   exit 1 if the real size differs (catches "the model returned 896x1152" and padded files)
  --grid         write IMAGE.grid.jpg: the full frame with the grid-safe box drawn on, plus the centred
                 1:1 crop and the 3:4 crop at thumbnail size (360 px), which is how the profile grid
                 and most previews show it. Judge headline size and clipping on the thumbnails.
  --max-mb N     warn if the file is larger than N MB (YouTube thumbnails must be under 2 MB)

Needs Pillow (pip install pillow).
"""
import argparse, os, sys
from PIL import Image, ImageDraw


def safe_box(w, h, inset=0.075):
    """Centred 1:1 square of the canvas (or the whole frame if it is wider than tall), inset on every side."""
    side = min(w, h)
    x0, y0 = (w - side) // 2, (h - side) // 2
    i = int(side * inset)
    return (x0 + i, y0 + i, x0 + side - i, y0 + side - i)


def centre_crop(im, rw, rh):
    w, h = im.size
    if w / h > rw / rh:
        nw = int(h * rw / rh); x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = int(w * rh / rw); y = (h - nh) // 2
    return im.crop((0, y, w, y + nh))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("image")
    ap.add_argument("--expect")
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--max-mb", type=float, default=None)
    a = ap.parse_args()
    if not os.path.exists(a.image):
        sys.exit(f"no such file: {a.image}")
    im = Image.open(a.image)
    w, h = im.size
    mb = os.path.getsize(a.image) / 1e6
    print(f"{a.image}: {w}x{h} {im.mode} {mb:.2f} MB (ratio {w / h:.3f})")
    rc = 0
    if a.expect:
        ew, eh = (int(x) for x in a.expect.lower().split("x"))
        if (w, h) != (ew, eh):
            print(f"SIZE: FAIL expected {ew}x{eh}"); rc = 1
        else:
            print("SIZE: PASS")
    if a.max_mb and mb > a.max_mb:
        print(f"FILE SIZE: WARN {mb:.2f} MB is over {a.max_mb} MB (save as JPG at quality ~90)")
    if a.grid:
        rgb = im.convert("RGB")
        full = rgb.copy(); d = ImageDraw.Draw(full)
        b = safe_box(w, h)
        lw = max(3, w // 300)
        d.rectangle(b, outline=(255, 0, 80), width=lw)
        d.rectangle((0, int(h * 0.88), w, h), outline=(255, 200, 0), width=lw)     # bottom band to keep clear
        th = 540
        full_t = full.resize((int(w * th / h), th))
        sq = centre_crop(rgb, 1, 1).resize((360, 360))
        t34 = centre_crop(rgb, 3, 4).resize((270, 360))
        sheet = Image.new("RGB", (full_t.width + 360 + 270 + 60, th + 40), (245, 245, 245))
        sheet.paste(full_t, (10, 30)); sheet.paste(sq, (full_t.width + 30, 30)); sheet.paste(t34, (full_t.width + 410, 30))
        sd = ImageDraw.Draw(sheet)
        sd.text((10, 8), "full frame: red = grid-safe box, yellow = bottom band", fill=(0, 0, 0))
        sd.text((full_t.width + 30, 8), "1:1 grid tile", fill=(0, 0, 0))
        sd.text((full_t.width + 410, 8), "3:4 grid tile", fill=(0, 0, 0))
        out = os.path.splitext(a.image)[0] + ".grid.jpg"
        sheet.save(out, quality=88)
        print(f"grid preview: {out}  (red box: safe zone {b[0]},{b[1]} to {b[2]},{b[3]})")
    sys.exit(rc)


if __name__ == "__main__":
    main()
