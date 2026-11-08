---
name: voice-loop
description: Learns how a person actually talks and writes, so every future script and caption starts closer to them. After filming, diffs the delivered transcript or caption file (.srt) against the script: delivered words per minute, delivered-to-written ratio, and what survived verbatim, was deleted, was made plainer, or was added. Also diffs the person's hand-edits of captions, scripts and articles against the as-generated baselines. Logs findings to brand/voice-learnings.md, promotes durable patterns, flags conflicts instead of overwriting, and keeps a ledger so nothing is diffed twice. Includes a small Python diff script. Use when someone says "here's the SRT", "I filmed it, learn from it", "compare what I said to the script", "I've edited the captions", "learn my voice", "why do I keep rewriting your drafts", or on a nightly or weekly schedule.
---

# Voice loop

This skill closes the loop between what Claude writes and what the person actually says and keeps. A script is a proposal; the words they say on camera are the ground truth, and their hand-edits of a caption or article are the clearest signal of how they write. Diffing the two, regularly, turns those differences into rules in `brand/voice-learnings.md`, which every writing skill reads first. The aim is that their edits get smaller over time.

It owns the diff method, the voice-learnings log format, the ledger and the promotion rules. It never writes content itself; `video-scripting` and `writing` read what it learns.

## Before you start

1. Find the marketing workspace (default `marketing/`). If none, say so in one line and offer `brand-setup`. The loop needs `brand/voice-learnings.md` (create it from `references/voice-learnings-format.md` if missing) and the `baselines/` folder.
2. Read `brand/brand-profile.md` (`## Voice`, `## Compliance`) and the current `brand/voice-learnings.md`, so you know what is already a rule. Brand-profile wins on brand constants and compliance wording; this skill owns the method.
3. Read the ledger at `brand/voice-loop-ledger.json` (schema in `references/voice-learnings-format.md`). If it does not exist, start one.

## Two inputs, one method

**A. Filmed delivery.** A caption file (`.srt` or `.vtt`) exported from the video edit, auto-captions or a transcription tool such as Whisper. It holds the words actually said, with timings.

**B. Hand-edits.** A script, caption set or article that the person has edited after Claude wrote it. The `video-scripting` and `writing` skills save an untouched copy of everything they file to `baselines/<yyyy-mm-dd>/`; the live file in `content/<yyyy-mm-dd>-<slug>/` is compared with that copy.

Both go through the same diff, categorise, log, promote, flag-conflicts method.

## The method

1. **Find what is new.** Caption files in `content/**` (and wherever the person keeps exports), and any filed script or caption whose content has changed since its baseline or since it was last learned. Skip anything the ledger already holds at the same file hash or modified time. Process at most about five items per run and queue the rest, so a backlog never swamps one session.
2. **Match each to its script or baseline.** Match on slug and words, not just the date. No match: do not invent a "script side". Record it as `no-script` in the ledger, skim it for any standout lines worth logging as a raw voice sample, and move on.
3. **Only the person's edits count.** If a change was made by Claude or a tool (a compliance fix, a reviewer's correction, a sync), it is not a voice lesson: record it as learned without a finding. If you cannot tell whose change it is, log it as a candidate and ask.
4. **Run the diff.** Use the script: `python3 scripts/srt_diff.py <script-or-baseline> <srt-or-edited-file>` (add `--json` for structured output). It ignores shot reminders and chapter markers in brackets, and prints:
   - **Calibration** (filmed input only): delivered words, runtime, **delivered words per minute** (pauses included), and the **delivered-to-written ratio**. Also the share of script words that survived verbatim.
   - **Categories:** VERBATIM (survived word for word), DELETED (dropped, the strongest signal), PLAINER (replaced with something shorter or simpler), REWORDED (replaced with something different), ADDED (said or written but not scripted).
5. **Read it for the pattern, not the words.** The script's categories are mechanical; the judgement is yours. For each meaningful change ask what rule would have produced their version. Note anything **better than the page**, word for word. Ignore filler (um, you know) and do not learn from captioning errors: an auto-caption that mishears a word is a "caption watch" item for the `video-editing` skill to fix, not a voice lesson.
6. **Watch for meaning changes.** If a spoken fact, figure or claim came out materially different from the script, flag it as a **compliance watch** item for the person before the video is published. Voice freedom never extends to a changed claim.
7. **Log it** to `brand/voice-learnings.md` (format below), newest first, with the source files, the numbers and a real before/after example for each pattern.
8. **Promote or flag** (governance below).
9. **Update the ledger** for every item processed, including skipped and no-script ones, so the next run never diffs the same thing twice. For hand-edits, record the hash of the version you learned from; the next edit is diffed against that, and the original baseline stays untouched.
10. **Report** briefly: what was processed, the calibration numbers and trend, what was promoted, what is held for the person.

## Governance: auto-add, but flag conflicts

- **Always log the finding.** Every diffed item gets an entry, even if the only lesson is "on target".
- **Promote a pattern to a working rule** (the `## Working rules` section of voice-learnings, which the writing skills apply first) when it is clearly additive and does not contradict anything: seen on two or more separate pieces, or given as a direct instruction by the person. A single sighting stays in the log as a candidate until it is seen again. Why: one video can be a mood; two is a habit.
- **A conflict is held, never auto-resolved.** If a finding contradicts an existing working rule or anything in brand-profile (voice, the who-am-I line, the goodbye, compliance wording), do not change either. Mark it `CONFLICT: for <name>` in the log and the ledger (`held-conflict`), state the old rule, the new evidence and the exact choice, and ask the person. Their answer becomes the rule.
- **Never edit brand-profile automatically.** Propose the change; the person makes it (or asks `brand-setup` to).
- **Retire, do not pile up.** When a new rule supersedes an old one, move the old one to `## Retired` in voice-learnings with the date and reason, so generators do not apply both.

## Pace calibration

Track delivered wpm and the ratio across videos in the log's calibration table. They tell `video-scripting` how long to write:
- Ratio well above 1 (say 1.5 to 2x): the person expands the page a lot. Scripts should be shorter skeletons.
- Ratio near 1: they deliver roughly what is written. Write at full intended length.
- Pace usually varies by the shape of the piece (a deliberate single-point video is slower than a brisk round-up), so record the type alongside the number rather than averaging everything.

## What the patterns tend to look like

The kinds of thing this loop finds, so you know what to look for (examples are generic):
- **Openings:** staged scenes and riddles replaced by a plain statement of the topic; clipped questions turned into full spoken sentences, often with a run-in word.
- **Signposts:** one-word rhetorical questions ("Renting?") turned into conditionals ("if you're renting...").
- **Plainer words:** ornamental phrases swapped for everyday ones every time; jargon expanded on first use.
- **Hedges:** absolutes softened ("always" to "usually", "the same" to "virtually the same").
- **Additions:** the reason behind a rule, a concrete practitioner detail, their own week, a wry aside, a bigger "what this means for your life" near the close.
- **Deletions:** location arrivals in the hook, a segment that did not earn its place, hype signposts, scripted keyword asks.
- **Fixed phrases:** the who-am-I wording and the goodbye they actually say, which become the standard.
- **Format habits:** how they write dates, how they name organisations, where they like line breaks.
- **Deliberate roughness:** some people keep the odd typo or a bit of swearing on purpose because it reads human. If they say so, record it as a rule and stop "correcting" their published copy.

## Running it on a schedule

The loop is cheap when there is nothing new, so it suits a nightly or weekly scheduled task. The mechanical part (finding files, running the script) can go to a smaller, faster model; the judgement (inferring the pattern, deciding additive versus conflict, wording a rule) should stay with the main model. Read-only on everything except `brand/voice-learnings.md`, the ledger and new baseline snapshots.

## Checks before it ships

Before writing to voice-learnings: every finding cites its source files and a real before/after; nothing promoted from a single sighting unless the person instructed it; conflicts held, not applied; no captioning errors logged as voice; compliance-watch items raised; ledger updated. Hand anything promoted to `review-loop` if the person wants a second pair of eyes on new rules.

## Adapting it

- **Two presenters:** keep a section per person in voice-learnings (or separate files) if they talk differently; tag each ledger entry with who spoke.
- **No video yet:** run input B only. Hand-edits of captions and articles are a rich signal on their own.
- **Where captions come from:** any tool that exports `.srt` or `.vtt` works. Whisper (open-source) gives good word timings; the `video-editing` skill already produces captions as part of the edit.

## References

- `references/voice-learnings-format.md`: the voice-learnings file layout, a log entry template, and the ledger schema. Open when creating or writing to either file.
- `scripts/srt_diff.py`: the diff, standard-library Python, no installs.

Learn more: https://builtnotboosted.com/skills/voice-loop
