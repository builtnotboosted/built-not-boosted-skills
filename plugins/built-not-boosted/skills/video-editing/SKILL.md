---
name: video-editing
description: Edits filmed talking-head footage into release-ready vertical shorts (1080x1920) and 16:9 YouTube long-forms with ffmpeg and Whisper. Keeps exactly one clean read of every script line (no stumbles, restarts or double reads), never leaves a flat single shot (punch-ins, reframes, B-roll, motion graphics), captions from the finished audio, normalises loudness to -14 LUFS, makes a real-frame cover and runs a QA gate that re-transcribes the render and refuses delivery until it passes. Syncs extra cameras by sound and writes YouTube chapters. Use when someone says "edit my video", "cut this clip", "remove my retakes", "edit out the fluffs", "add captions to my video", "make a short from this footage", "sync my two cameras", "make a thumbnail from my video", or hands over raw footage and a script.
---

# Video editing

This skill turns raw footage of someone talking to camera into a finished video, a matching SRT caption file and a cover, using a bundled command-line tool (`vedit.py`) built on ffmpeg, Whisper and Playwright. It owns the edit: choosing the clean takes, cutting cleanly, shot variety, graphics and B-roll placement, captions, loudness, the cover and the final QA. It defers to the `video-scripting` skill for the script and edit notes it edits to, to `brand/brand-profile.md` for colours, fonts and compliance lines, to the `image-generation` skill for still images, to the `review-loop` skill for the independent check, and to the `scheduling` skill for posting. **Nothing is posted or scheduled from here.**

Authority order: **brand-profile.md wins on brand constants and compliance wording; this skill owns the method.**

## Before you start

1. Find the marketing workspace (default `marketing/`). If there isn't one, say so in one line and offer the `brand-setup` skill; the tool still works with a neutral look.
2. Find the piece's folder, `content/<yyyy-mm-dd>-<slug>/`. It should hold `script.txt` (one spoken sentence per line; `[notes in brackets]` and `[CHAPTER N • Title]` markers are never spoken), and ideally `edit-notes.txt` (`HOOK ON SCREEN:`, `COVER:`, `OUTCOME:` lines) and `sources.txt` (the only figures allowed on screen). If the person filmed without a script, transcribe first and treat the cleaned transcript as the script.
3. Read `## Visual identity`, `## Compliance`, `## Boundaries` and `## CTA & contact` in the brand profile, and `brand/voice-learnings.md` for words and phrasing on graphics and covers.
4. Check the tool is ready: `python3 <skill>/vedit.py doctor`. If anything is missing, run `bash <skill>/setup.sh` once (ffmpeg, Node, Python venv, Whisper, Playwright, fonts). Whisper's large model is about 3 GB and transcribes at roughly one to two times the clip length on a laptop CPU, so start long steps in the background.

## The standard

1. **One clean read of every line.** The finished video contains exactly one read of each line: no restarts, no "the, the", no half-sentence from an abandoned take, no clipped word endings. This is a blocker, not polish. A lone natural "um" may stay (people should sound like themselves), but never in the opening line and never two in one line.
2. **Follow the spoken delivery, not the written script.** People improve lines as they speak. A live reword shows up as a missing or low-coverage line in the take finder; it is not a fluff. Keep their version, cut only genuine stumbles and restarts, and fix any graphic or hook card written from the script to match what was actually said.
3. **Keep the beats that earn the business.** If the script has an early "who I am" line or a closing call to action, it stays where it is.
4. **Never a flat single shot.** Alternate wide and tight on every cut, reframe inside long reads, cut away to B-roll, carry the story with motion graphics. The talking head is the spine, not the whole video.
5. **Captions come from the finished audio**, checked against the script, so they match what is heard exactly. Burned in on shorts; SRT only on long-form.
6. **Loudness -14 LUFS**, true peak -1.5 dB, so it sits right on every platform.
7. **A real-frame cover** with the headline inside the grid-safe square, offered as one or two variants.
8. **The QA gate passes before anything is delivered.** It re-transcribes the render, listens to every cut on its own, and checks every cut lands in quiet. `deliver` refuses without a fresh PASS.
9. **Honest about the ear.** Claude cannot hear. The gate checks words and energy, not tone, a cough under a word or a bad room-tone splice. Say so at hand-over, every time.

## The method

Every command is `python3 <skill>/vedit.py <command> <slug>`. Read `references/project-config.md` before editing `project.json` by hand.

1. **Gather everything first.** List every clip in the batch. Pair second cameras by sound (`scripts/sync_cams.py`; a real match scores about 0.4 to 0.55, a non-match about 0.03) and silent cameras such as drones by motion and timestamps (`scripts/sync_cams_visual.py`). Contact-sheet every photo and short clip, note what is usable as B-roll, and ask at once for any camera the person mentions that is not in the folder. Open `references/multicam-and-long-form.md` for the details.
2. **Init.** `vedit.py init <slug> --raw <cameraA clip> --pack <content folder> [--long] [--cam B=<clip>]`. It copies the script, reads the edit notes and maps the brand profile's palette and fonts into `project.json`. Then fill `vocab` with every proper name in the script, including the presenter's own name.
3. **Prep** (slow, background): `vedit.py prep <slug>`. Upright master at the camera's own frame rate, 16 kHz audio, extra cameras synced, and two transcripts (large-v3 verbatim plus medium.en). It stops on HDR footage, footage the wrong shape, and call-quality audio from a Bluetooth mic; `references/audio-and-sync.md` has the rescue route.
4. **Takes.** `vedit.py takes <slug>` aligns the speech to the script like a teleprompter: a backwards jump is a restart, so every attempt at every line becomes a scored take. A second listen re-hears each take on its own to find fillers, repeats and double reads. Read `picker/takes_report.txt`. Then verify before you trust it: open `references/whisper-pitfalls.md`, because Whisper drops repeated false starts, invents final words and splits unfamiliar terms. A proposed restart trim stands unless the energy map shows no second burst of speech.
5. **Picks.** Either the person picks in the browser (`vedit.py picker <slug>` in the background, then open `http://localhost:8765`), or, if they ask Claude to pick, write `picker/picks.json` yourself with a `note` on every change from the machine pick. Tell them which lines are red or amber and why. Prefer reads from the same run as the neighbouring lines: they flow with no cut. Never deliver from machine picks.
6. **Choreograph** (design work, read `references/style-notes.md` first). From the script, `sources.txt` and what is in the footage: a hook card on frame 0 from `edit_notes.hook_on_screen` (3 to 5 words, a promise not the answer); `graphics.json` cards for the beats that need them, with only figures that are in `sources.txt`; `cues` anchored to lines or spoken words, never fixed times; motivated B-roll cutaways (on the word they illustrate, or right after a look or gesture); `framing.face_x`/`eye_y` measured on one frame; `exit_tail` for the walk-out. Preview graphics as stills with `vedit.py mg-preview <slug>`.
7. **Build.** `vedit.py build <slug> plan` is instant and prints the cut summary; `build cues` lists any cue it could not place (fix it, never ignore it). Iterate on `build cut` plus `scripts/cut_check.py` until clean, make the cover (step 9) so the poster frame bakes in, then `build all`. Rules the build applies are in `references/edit-rules.md`.
8. **Gate.** `vedit.py gate <slug>`. It fails on a line read twice, a stumble or abandoned start left in, speech energy with no words (a hidden re-read), a repeat or skip across any cut (heard on its own by both models), stray words from a dropped take at a cut, a cut that lands on sound, and (multi-camera, if a `gaze.json` exists) the wrong camera. Fix the cause, rebuild, re-gate. Then the human-proxy pass: watch a contact sheet of the render, read every caption (`vedit.py captions <slug>`), and for every line you changed write down what was there and what is kept.
9. **Cover.** `vedit.py frames <slug> --every 5` for a contact sheet; choose a frame with eye contact, a warm expression (not mid-word), sharp focus and a prop that tells the story. Set `cover.frame` and one or two `variants` (2 to 4 words, big, one highlight word, plain and true), then `vedit.py cover <slug>`. It checks every text box against the grid-safe square and the face, and writes `grid_tiles.jpg` showing what the profile grid will show.
10. **Review.** Hand the render's contact sheet, the covers, the SRT and the cut list to the `review-loop` skill. Figures on screen are checked against `sources.txt`, not taken on trust.
11. **Deliver and release.** `vedit.py deliver <slug>` writes the video, SRT, covers, cut list (every line: take, source range, trims, every change with its reason), QA report and, for long-form, `youtube-chapters.txt` into `content/<date>-<slug>/video/`. `vedit.py release <slug> --to <folder>` copies the video, the SRT and a JPG thumbnail under one filename, which is what schedulers and YouTube expect.

## Checks before it ships

The hand-over to the person always includes:

- Gate PASS, fresh (newer than the render).
- Lip sync measured on the final render: `scripts/lipsync.py build/final.mp4 <t0> <t1>` on two or three face-to-camera stretches, each within ±40 ms.
- Runtime and loudness stated.
- Every change to their picks, with the reason, and the lines worth listening to.
- Cover A versus B, and the grid preview.
- "Nothing has been posted or scheduled."
- "I can't hear it: please listen before it goes out."

## Adapting it

- **No script?** Transcribe first (`prep` makes both transcripts), clean the transcript into one sentence per line, save it as `script.txt`, then run `takes`.
- **Different look:** everything visual reads `project.json` `brand` (colours, fonts) and `cover.wordmark` (an optional small name tag). Change it there, never in the scripts.
- **Different spelling:** `captions.locale` `en-GB` (default) or `en-US`.
- **Slower machine:** `"whisper": {"large": "small.en", "medium": "base.en"}` in `project.json` trades accuracy for speed; the gate still runs.
- **Regulated business:** put the required on-screen wording from `## Compliance` into a graphic or the end card, and keep every on-screen figure to `sources.txt`.
- **New graphic templates:** add them to `scripts/mg/kit.html` and document them in `references/project-config.md`.
- **Learning:** when the person reports a skip or repeat the gate missed, note the case before fixing the video, and add what you learned about their editing taste to `brand/performance-learnings.md`. The SRT is transcribed from their own voice, so the `voice-loop` skill may learn from it.

## Known gaps

- The take finder can miss a restart that changes the wording a lot; the gate's re-read rule is the backstop. After any hand `nin` or trim change, read `build/edl.json` and check every seam you touched.
- The stray-word check matches the kept take's edge words by text, so an abandoned take's word that sounds like the kept take's first word can pass as an "ad-lib" note. Map each such note to source time through `build/edl.json` by hand.
- No automatic lip-sync check in the gate: run `lipsync.py` on every final render.
- Camera calls on multi-camera shoots are by hand (`"cam"` in picks) unless you supply a `gaze.json`; see `references/multicam-and-long-form.md`.
- Word-by-word "karaoke" captions are not built; offer them as an idea, never switch the caption style unasked.

## Files in this skill

| File | Open it when |
|---|---|
| `references/project-config.md` | editing `project.json`, `graphics.json`, cues, cover variants or picks |
| `references/edit-rules.md` | judging a cut, a caption, a graphic or a cover |
| `references/whisper-pitfalls.md` | verifying takes, trims and gate notes |
| `references/style-notes.md` | choreographing an edit (shot variety, cutaways, hook card, covers) |
| `references/multicam-and-long-form.md` | a second camera, a drone, a 16:9 long-form, chapters |
| `references/audio-and-sync.md` | bad audio, late audio, background noise, loudness |
| `references/project-template.json` | the starting `project.json` |
| `setup.sh`, `vedit.py doctor` | first run on a machine |

## Learn more

A longer guide with examples lives at https://builtnotboosted.com/skills/video-editing
