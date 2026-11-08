---
name: review-loop
description: The quality gate every piece of content passes before it is filed, scheduled or posted. Runs a self-critique, then an independent review by a fresh subagent that sees only the finished work and the criteria (never the builder's reasoning), then fix and re-judge until there is a clean pass. Covers what to do when a piece can't pass unattended (hold, flag, ship the rest). Use when someone says "review this", "check this before it goes out", "QA the pack", "is this ready to post", "get a second pair of eyes on this", "proofread the captions", or when any other Built Not Boosted skill hands work over for checks.
---

# Review loop

This skill owns the process for checking work before it ships: self-critique, an independent review, fix and re-judge, and the clean-pass gate. It does not own the criteria. Those live in the skills that make the work (`writing` for copy, `image-generation` for images, `video-scripting` for scripts, `video-editing` for finished video, `scheduling` for posting mechanics) and in the brand profile. This skill runs the loop over them.

The one rule: **nothing is filed, scheduled or posted until it's a clean pass.** Speed never lowers the bar. Reactive, rushed and "just a quick one" pieces go through the same loop.

## Before you start

1. Read `marketing/brand/brand-profile.md`, especially Voice, Boundaries, Compliance, Likeness and Platforms. These are the hard rules every reviewer checks against.
2. Read `brand/voice-learnings.md` for what "sounds like them" means in practice.
3. Collect the criteria for each kind of artefact in the piece: the "Checks before it ships" section of each skill that produced it.
4. Gather the artefacts themselves from the piece folder `content/<yyyy-mm-dd>-<slug>/`: `captions.md`, `PACKAGE.md`, scripts, image files, video files.

No workspace? Review against the producing skill's checks and general good practice, and say in the result that brand-specific checks couldn't run.

## Stage 1: Self-critique

Before anyone else sees it, review your own work as a demanding editor, designer and compliance reader would. Fix as you go.

- **Copy:** run the `writing` checklist line by line.
- **Images:** open every image file at its final size and check it against the `image-generation` checks: spelling of every word baked in, no duplicated words, true aspect ratio with nothing clipped, legible at thumbnail size. For carousels, every slide. For animated pieces, the final video file.
- **Likeness:** for any image of a real person, open it next to a real reference photo from `brand/reference-images/` (a colour one, for hair and skin tone) and compare feature by feature against the profile's Likeness section. Never compare against another generated image. If you're not sure it's genuinely them, it fails.
- **Truth:** every story, figure, quote and review traces to something real: the user's own account, a source in `sources.md`, or the approved review store.
- **Voice:** read every line aloud, image headlines included. Does it sound like this person, or like generic marketing? A technically correct but soulless line is a fail.
- **Completeness:** every platform in the plan has its version; every still has alt text; first comments are there; the format is tagged.

A rewrite or re-roll is a new artefact. It gets the same self-critique before it counts.

## Stage 2: Independent review

Spawn a subagent as an independent reviewer. Independence is the whole point: the builder knows what they meant, so they read what they meant. A fresh reader only sees what's actually there.

Give the reviewer:

- The finished artefacts (copy text in full, file paths for images and video).
- The criteria: the relevant checks sections, plus the brand profile's Voice, Boundaries, Compliance and Likeness sections, and the disclaimer tier each piece should carry.
- Reference photo paths, if any image shows a real person.

Do **not** give it your reasoning, your drafts, the brief's back-story or why you made each choice. That context is exactly what stops a reviewer seeing the problems.

Ask it to **find, not fix**, and to report each fault with a severity, the file and section, the exact offending text quoted, and a suggested fix. Use the template in `references/reviewer-prompt.md`; open it every time you spawn a reviewer.

Severities:

- **Blocker:** must be fixed before it ships. Compliance and truth faults, a wrong likeness, a broken link rule, a platform limit breach, a missing required element.
- **Should-fix:** fix unless there's a good reason. Weak hook, off-voice line, limp ask, missing first comment.
- **Nice-to-have:** judgement call.

Tell the reviewer to be adversarial on two things in particular. **Likeness:** open every image with a face and compare against the real reference photo; "a plausible person of that age" is not the bar, and unsure means fail. Why: reviews have passed generic stand-in faces before, because a reviewer that doesn't open the file can't catch it. **Truth:** any figure, story or quote without a traceable source is a blocker, however plausible it sounds.

If your environment can't spawn subagents (some chat clients), say so, then do the closest honest thing: a separate cold pass reading only the artefacts and criteria, as if seeing them for the first time, or ask the user to paste the reviewer prompt into a fresh chat. Note in the result that the review wasn't independent.

## Stage 3: Fix and re-judge

1. Fix every blocker and should-fix. Decide on each nice-to-have and note the call.
2. Re-run the affected checks. Re-review any re-rolled image on its new file, not the old one.
3. Re-judge the whole piece, because fixes can break other things (a shorter caption can lose the disclaimer; a new image can clip a headline).
4. If the fixes changed anything substantial, run Stage 2 again with a fresh reviewer.

Only a genuinely clean pass ships. If three full rounds haven't produced one, stop looping: the problem is usually in the brief or the approach, not the polish. Hold the piece and flag it with what keeps failing.

## Recording the result

Write a short `REVIEW.md` in the piece folder: date, what was reviewed, the reviewer's findings by severity, what was fixed, any nice-to-haves declined and why, and the verdict (clean pass, shipped with gaps flagged, or held). This is what the user reads when they want to know why something was held, and what `voice-loop` and `platform-data` can learn from later.

## When it can't pass unattended

In a scheduled or unattended run there's no one to ask. Never ship something substandard to hit a slot, and never invent a fact or fake an image to force a pass.

- **An image that won't come right** after genuine re-rolls: file nothing broken, keep the prompt, ship the rest of the pack and flag the gap.
- **An image of a real person that won't reach a genuine likeness:** a wrong face is worse than no image. In order: re-roll anchored on a real reference photo with the likeness features spelled out; rebuild the piece without a face (a scene plus the headline); only if neither works, hold the piece. Never ship a stand-in face.
- **A compliance or truth problem** that can't be resolved from the profile and sources: hold the piece and flag it clearly.
- **Something the skills and profile don't settle:** make the conservative choice and note it, or stop and flag. Don't guess.

Put every hold and flag in `REVIEW.md` and in the run's summary to the user, so nothing is silently dropped.

## Adapting it

- **Light-touch content** (a reply, a story frame) can skip Stage 2 if the user chooses, but never skip it for anything carrying compliance wording, a real person's face, a figure or an affiliate link.
- **Teams:** the independent reviewer can be a person. Hand them the same prompt and criteria.
- **New criteria:** add them to the producing skill's checks or the brand profile, not here. This skill runs whatever checks exist.

## Learn more

https://builtnotboosted.com/skills/review-loop
