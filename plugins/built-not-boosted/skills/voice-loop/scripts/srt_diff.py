#!/usr/bin/env python3
"""srt_diff.py: compare what was written with what was actually said (or kept).

Part of the built-not-boosted voice-loop skill. MIT licence. Standard library only.

Two modes, picked from the second file's extension:

  python3 srt_diff.py script.txt delivered.srt     # filmed video: script vs captions
  python3 srt_diff.py baseline.txt edited.txt      # hand edit: as-generated vs edited

Prints the calibration numbers (delivered words, runtime, words per minute,
delivered-to-written ratio, verbatim survival) and a categorised diff:

  VERBATIM  runs of the script that came through word for word
  DELETED   script text that was dropped
  ADDED     text that was said or written but not in the script
  PLAINER   script text replaced by something shorter or simpler
  REWORDED  script text replaced by something of similar or greater weight

The categories are a first pass. Deciding what a change MEANS (a pattern, a
one-off tic, a captioning error) is the judgement the skill keeps for Claude.

Lines in the script that are pure directions are ignored: anything wholly
inside <ANGLE BRACKETS> or [SQUARE BRACKETS], and lines starting with '#'.

Options:
  --min-verbatim N   shortest word run reported as VERBATIM (default 5)
  --join N           merge changes separated by fewer than N matching words (default 3)
  --json             machine-readable output instead of the text report
"""

import argparse
import difflib
import json
import re
import sys

TIMECODE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)
TAG = re.compile(r"<[^>]*>|\{[^}]*\}")
DIRECTION_LINE = re.compile(r"^\s*(<[^>]*>|\[[^\]]*\])\s*$")
WORD = re.compile(r"[A-Za-z0-9À-ɏ]+(?:['’][A-Za-z]+)*")


def read_text(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        return fh.read().replace("\r\n", "\n").replace("\r", "\n")


def seconds(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000.0


def parse_srt(raw):
    """Return (spoken_text, start_seconds, end_seconds). Works for .srt and simple .vtt."""
    lines_out = []
    first_start = None
    last_end = 0.0
    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.isdigit() or stripped.upper().startswith("WEBVTT"):
            continue
        tc = TIMECODE.search(stripped)
        if tc:
            g = tc.groups()
            start = seconds(*g[0:4])
            end = seconds(*g[4:8])
            if first_start is None:
                first_start = start
            last_end = max(last_end, end)
            continue
        if stripped.startswith(("NOTE", "STYLE", "REGION")):
            continue
        lines_out.append(TAG.sub("", stripped))
    return " ".join(lines_out), (first_start or 0.0), last_end


def clean_script(raw):
    keep = []
    for line in raw.split("\n"):
        if DIRECTION_LINE.match(line) or line.lstrip().startswith("#"):
            continue
        keep.append(TAG.sub(" ", line))
    return "\n".join(keep)


def tokens(text):
    """Display words plus a normalised form used for matching."""
    shown = WORD.findall(text)
    norm = [w.lower().replace("’", "'") for w in shown]
    return shown, norm


def merge_ops(opcodes, join):
    """Fold short 'equal' gaps between changes into the change, so the diff reads in phrases."""
    merged = []
    for op in opcodes:
        tag, i1, i2, j1, j2 = op
        if (
            merged
            and tag != "equal"
            and len(merged) >= 2
            and merged[-1][0] == "equal"
            and (merged[-1][2] - merged[-1][1]) < join
            and merged[-2][0] != "equal"
        ):
            gap = merged.pop()
            prev = merged.pop()
            merged.append(("replace", prev[1], i2, prev[3], j2))
            del gap
            continue
        if merged and tag != "equal" and merged[-1][0] != "equal":
            prev = merged.pop()
            merged.append(("replace", prev[1], i2, prev[3], j2))
            continue
        merged.append(op)
    # A replace with one empty side is really a delete or an insert.
    fixed = []
    for tag, i1, i2, j1, j2 in merged:
        if tag == "replace" and j1 == j2:
            tag = "delete"
        elif tag == "replace" and i1 == i2:
            tag = "insert"
        fixed.append((tag, i1, i2, j1, j2))
    return fixed


def avg_len(words):
    return sum(len(w) for w in words) / len(words) if words else 0.0


def classify_replace(old, new):
    # Plainer: fewer words, or about the same count but shorter words.
    if len(new) < len(old) * 0.85:
        return "PLAINER"
    if len(new) <= len(old) * 1.15 and avg_len(new) < avg_len(old) - 0.3:
        return "PLAINER"
    return "REWORDED"


def analyse(script_raw, delivered_raw, delivered_is_srt, min_verbatim, join):
    script_text = clean_script(script_raw)
    if delivered_is_srt:
        delivered_text, start, end = parse_srt(delivered_raw)
        runtime = end  # from 00:00:00 to the last caption, pauses included
    else:
        delivered_text, start, end, runtime = clean_script(delivered_raw), 0.0, 0.0, 0.0

    s_show, s_norm = tokens(script_text)
    d_show, d_norm = tokens(delivered_text)

    sm = difflib.SequenceMatcher(a=s_norm, b=d_norm, autojunk=False)
    ops = merge_ops(sm.get_opcodes(), join)

    items = []
    verbatim_words = 0
    for tag, i1, i2, j1, j2 in ops:
        old = s_show[i1:i2]
        new = d_show[j1:j2]
        if tag == "equal":
            verbatim_words += len(old)
            if len(old) >= min_verbatim:
                items.append({"category": "VERBATIM", "script": " ".join(old), "delivered": ""})
        elif tag == "delete":
            items.append({"category": "DELETED", "script": " ".join(old), "delivered": ""})
        elif tag == "insert":
            items.append({"category": "ADDED", "script": "", "delivered": " ".join(new)})
        else:
            items.append({"category": classify_replace(old, new),
                          "script": " ".join(old), "delivered": " ".join(new)})

    written = len(s_show)
    delivered = len(d_show)
    metrics = {
        "mode": "srt" if delivered_is_srt else "text",
        "script_words": written,
        "delivered_words": delivered,
        "runtime_seconds": round(runtime, 1) if delivered_is_srt else None,
        "wpm": round(delivered / (runtime / 60.0), 1) if delivered_is_srt and runtime > 0 else None,
        "ratio": round(delivered / written, 2) if written else None,
        "verbatim_survival": round(verbatim_words / written, 2) if written else None,
    }
    counts = {}
    for it in items:
        counts[it["category"]] = counts.get(it["category"], 0) + 1
    metrics["counts"] = counts
    return metrics, items


def report(metrics, items, out):
    w = out.write
    w("== Calibration ==\n")
    w("mode:               %s\n" % metrics["mode"])
    w("script words:       %d\n" % metrics["script_words"])
    w("delivered words:    %d\n" % metrics["delivered_words"])
    if metrics["mode"] == "srt":
        rt = metrics["runtime_seconds"] or 0
        w("runtime:            %d:%02d (%.1fs)\n" % (int(rt // 60), int(rt % 60), rt))
        w("delivered wpm:      %s\n" % metrics["wpm"])
    w("delivered/written:  %sx\n" % metrics["ratio"])
    w("verbatim survival:  %d%% of script words\n" % round((metrics["verbatim_survival"] or 0) * 100))
    w("counts:             %s\n\n" % ", ".join("%s %d" % kv for kv in sorted(metrics["counts"].items())))
    w("== Diff, in script order ==\n")
    for it in items:
        cat = it["category"]
        if cat == "VERBATIM":
            w("[VERBATIM] %s\n" % it["script"])
        elif cat == "DELETED":
            w("[DELETED]  - %s\n" % it["script"])
        elif cat == "ADDED":
            w("[ADDED]    + %s\n" % it["delivered"])
        else:
            w("[%s] - %s\n%s+ %s\n" % (cat.ljust(8), it["script"], " " * 11, it["delivered"]))
    w("\nCategories are mechanical. Read them for the pattern; do not log a captioning error as a voice lesson.\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Diff a script against delivered captions (.srt/.vtt) or an edited text.")
    ap.add_argument("script", help="the as-written script or as-generated baseline (.txt or .md)")
    ap.add_argument("delivered", help="the .srt/.vtt of the filmed video, or the hand-edited text")
    ap.add_argument("--min-verbatim", type=int, default=5)
    ap.add_argument("--join", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    script_raw = read_text(args.script)
    delivered_raw = read_text(args.delivered)
    is_srt = args.delivered.lower().endswith((".srt", ".vtt")) or bool(TIMECODE.search(delivered_raw))

    metrics, items = analyse(script_raw, delivered_raw, is_srt, args.min_verbatim, args.join)
    if args.json:
        json.dump({"metrics": metrics, "diff": items}, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        report(metrics, items, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
