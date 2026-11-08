#!/usr/bin/env python3
"""Cut one small proxy clip per take (with 0.4s handles) for the take picker."""
import sys as _sys
if len(_sys.argv) < 4 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

TAKES, NORM, PDIR = sys.argv[1:4]
SIZE = sys.argv[4] if len(sys.argv) > 4 else "540:960"     # 960:540 for long-form
H = 0.4
os.makedirs(os.path.join(PDIR, "clips"), exist_ok=True)
d = json.load(open(TAKES))
jobs, manifest = [], {}
for s in d["sentences"]:
    for t in s["takes"]:
        key = f"S{s['sid']:02d}_t{t['take']}"
        cs = max(0.0, t["in"] - H); ce = t["out"] + H
        manifest[key] = {"clip_start": round(cs, 3)}
        out = os.path.join(PDIR, "clips", key + ".mp4")
        jobs.append(["ffmpeg", "-y", "-v", "error", "-ss", f"{cs:.3f}", "-to", f"{ce:.3f}", "-i", NORM,
                     "-vf", f"scale={SIZE}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                     "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out])
with ThreadPoolExecutor(6) as ex:
    rc = list(ex.map(lambda c: subprocess.run(c).returncode, jobs))
manifest["_format"] = "long" if SIZE.startswith("960") else "short"
json.dump(manifest, open(os.path.join(PDIR, "clips.json"), "w"))
print(f"{len(jobs)} clips, failures: {sum(1 for r in rc if r)}")
