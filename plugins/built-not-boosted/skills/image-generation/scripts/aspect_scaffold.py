#!/usr/bin/env python3
"""Make a plain single-colour canvas at an exact size, to use as the BASE image for an edit-based
image tool (the output usually keeps the base image's aspect ratio).

This is an input the model repaints completely, not padding on a finished image.

usage: aspect_scaffold.py WxH out.png [--colour "#1a1a1a"]
  e.g. aspect_scaffold.py 1080x1350 scaffold-4x5.png
       aspect_scaffold.py 1080x1920 scaffold-9x16.png --colour "#111111"
"""
import argparse
from PIL import Image


def main():
    ap = argparse.ArgumentParser(description="Plain canvas at an exact size, for aspect control with edit-based image tools.")
    ap.add_argument("size", help="WxH, e.g. 1080x1350")
    ap.add_argument("out")
    ap.add_argument("--colour", "--color", default="#1a1a1a", help="hex colour (a dark neutral works for most scenes)")
    a = ap.parse_args()
    w, h = (int(x) for x in a.size.lower().split("x"))
    Image.new("RGB", (w, h), a.colour).save(a.out)
    print(f"scaffold {w}x{h} ({w / h:.3f}) -> {a.out}")


if __name__ == "__main__":
    main()
