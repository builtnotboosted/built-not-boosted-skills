# voice-learnings.md and the ledger

## brand/voice-learnings.md layout

Every writing skill reads this file before drafting, so the top of it must be the current rules, short and clear. The evidence sits below.

```markdown
# Voice learnings: <name or brand>

Read this before writing anything in <name>'s voice. Working rules beat general skill guidance.
Fed by the voice-loop skill from filmed videos and hand-edits. Conflicts are held for <name>, never auto-applied.

## Working rules
(promoted: seen on 2+ pieces, or a direct instruction)
- **Hooks are one full spoken sentence, not a clipped question.** Seen: 2026-11-03 Gears video, 2026-11-10 Brakes video.
- **Audience switches use "if you're...", not one-word questions.** Seen: ...
- **Who-am-I:** "I'm Sam, I fix bikes at the workshop on the high street. Give me a follow and let's get into it." (vary only the tail)
- **Goodbye:** "Catch you soon."

## Calibration
| Date | Piece | Type | Script words | Delivered words | Runtime | WPM | Ratio | Verbatim |
|------|-------|------|--------------|-----------------|---------|-----|-------|----------|
| 2026-11-03 | Gears slipping | how-to short | 152 | 160 | 0:49 | 196 | 1.05 | 78% |

Current guidance for scripts: write at about <N> wpm, full length (ratio ~1.0).

## Candidates (seen once, waiting for a second sighting)
- Leads section changes with "Now". 2026-11-03 Gears.

## Held conflicts (waiting for <name>)
- CONFLICT: for <name>. Rule says pop-culture asides are welcome; on 2026-11-10 both scripted asides were cut. Keep, reduce, or drop?

## Log (newest first)
### 2026-11-03 · Gears slipping (filmed)
Source: content/2026-11-03-gears-slipping/script.txt vs content/2026-11-03-gears-slipping/gears.srt
Numbers: 196 wpm, ratio 1.05, 78% verbatim.
- DELETED: "for a living" from the who-am-I. Pattern: trims job descriptions to the plain verb. Candidate.
- PLAINER: "two-minute check worth doing" -> "really quick check". Pattern: drops writerly precision for the everyday phrase. Corroborates working rule.
- ADDED: "bless him" after the customer story. Pattern: warm aside after a human moment. Candidate.
- BETTER THAN THE PAGE: "it takes the expensive bits with it" came out as "and then it eats your gears as well". Use this kind of line.
- Caption watch: auto-captions wrote "cassette" as "cassie". For video-editing, not a voice lesson.
- Compliance watch: none.

## Retired
- 2026-10-01: "Write scripts at half length" (superseded when ratio settled near 1.0).
```

### Writing a good entry
- Name the source files and the numbers.
- One line per pattern: category, a real before -> after, the inferred rule, and whether it is a candidate, corroborates a rule, or promotes one.
- Be specific. "Sounds more natural" teaches nothing; "replaces one-word questions with 'if you're...'" does.

## brand/voice-loop-ledger.json

The memory that stops anything being learned twice. Load it every run; skip any item already present at the same hash or modified time; append after processing each item.

```json
{
  "entries": [
    {
      "input": "srt",
      "sourcePath": "content/2026-11-03-gears-slipping/gears.srt",
      "sourceHash": "sha256:...",
      "sourceModified": "2026-11-03T19:42:00+00:00",
      "comparedWith": "content/2026-11-03-gears-slipping/script.txt",
      "state": "learned",
      "wpm": 196,
      "ratio": 1.05,
      "processedAt": "2026-11-03T21:45:00+00:00",
      "note": "3 candidates, 1 corroboration"
    },
    {
      "input": "edit",
      "sourcePath": "content/2026-11-04-shop-hours/captions.md",
      "sourceHash": "sha256:...",
      "sourceModified": "2026-11-05T08:10:00+00:00",
      "comparedWith": "baselines/2026-11-04/shop-hours-captions.md",
      "state": "learned",
      "wpm": null,
      "ratio": 0.88,
      "processedAt": "2026-11-05T21:45:00+00:00",
      "note": "trimmed intro, dates written in full"
    }
  ]
}
```

- `input`: `srt` or `edit`.
- `state`: `learned`, `no-script`, `not-theirs` (change made by Claude or a tool), `held-conflict`, `skipped`.
- For edits, the next diff of the same file compares against the version recorded here (`sourceHash`), not the original baseline, so a second round of edits is not re-learned. Keep a copy of that learned version beside the baseline (for example `baselines/2026-11-04/shop-hours-captions.learned-2026-11-05.md`); never overwrite the original baseline.
- There is no time-based pruning. It is a permanent record of what has been learned.

## baselines/

`baselines/<yyyy-mm-dd>/<slug>-<kind>.<ext>`, written by `video-scripting` and `writing` at filing time. Immutable. If a filed piece has no baseline, the first run snapshots it as the baseline and records `skipped` (nothing has been edited yet).
