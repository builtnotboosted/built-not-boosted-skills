---
name: image-generation
description: Produces finished social images with any image model (Google Gemini image, "Nano Banana", as the worked example) - feed statics, carousel slides, short-form video covers, YouTube and article thumbnails, local listing cards and animated statics. Bakes the headline into the scene instead of pasting text on top, keeps text inside the profile-grid safe zone, locks the likeness of real people to their reference photos, hits exact platform sizes, writes alt text and re-judges every re-roll on the filed file. Use when someone says "make an image for this post", "create a thumbnail", "make a cover from my video", "design a carousel", "animate this static", "the image model won't do 4:5", "my headline is getting cut off in the grid", or when a content pack needs its visuals.
---

# Image generation

This skill turns a post's message into a finished image file at the exact size each platform wants. It owns the production method: how the scene is chosen, how the headline gets into the picture, how a real person's face is kept real, how the aspect ratio is controlled, how the file is checked and how alt text is written. It defers to `brand/brand-profile.md` for the brand constants (palette, fonts, logo rules, likeness rules), to the `writing` skill for the words of the headline, to the `video-editing` skill for covers built inside a video edit, and to the `review-loop` skill for the independent check before anything ships.

Authority order: **brand-profile.md wins on brand constants and compliance wording; this skill owns the method.**

## Before you start

1. Find the marketing workspace (default `marketing/`). If there isn't one, say so in one line and offer to run the `brand-setup` skill; if the user wants to carry on, ask only for the palette (two or three hex codes), a headline font and whether a real person appears.
2. Read from `brand/brand-profile.md`: `## Visual identity` (palette, fonts, logo usage, image style), `## Likeness` (reference image paths and rules), `## Platforms` (where this is going), `## Compliance` (anything that must or must not appear in an image), `## Boundaries` and `## Tools` (which image model is available).
3. Read `brand/voice-learnings.md` before you lock any headline wording: headlines are copy, and copy should sound like the person.
4. Read `brand/performance-learnings.md` for anything the account has learned about which images earn reach.
5. Work in the piece's folder, `content/<yyyy-mm-dd>-<slug>/`. Images go in an `images/` subfolder there.
6. Know the format before producing: plain static, carousel, short-form cover, long-form cover, or animated static. If nobody has chosen, pick the simplest that fits and say why in one line.

## The standard

1. **The headline is baked into the scene by the image model, never pasted on top in code.** Ask the model to render the headline and subhead as part of the picture, lit and placed as a designer would. Why: text added afterwards with PIL, Canva-style overlays or HTML sits on a different plane from the photograph and reads as a cheap template, which is the single most common reason people reject AI images. The image model is now good at short display text; let it do the job.
2. **The headline is the hero.** Big, bold, condensed type, roughly 40% of the visible height and never less than a third, two or three short lines, one punch word in the accent colour. If it reads like a caption it fails. Why: the grid and the feed are judged at thumbnail size on a phone, and only a big headline survives that.
3. **All text lives in the grid-safe zone.** The centred 1:1 square of the canvas, inset a further 7 to 8% on every side, with clear space above the headline and nothing important in the bottom 12%. Why: profile grids, link previews and in-feed crops cut the edges off. Open `references/grid-safe-zone.md` for per-format numbers.
4. **Every image is a distinct, real-looking scene built for that message.** A person doing something in a real place, or one strong visual metaphor, in natural colour with the brand accent used sparingly. Never the same portrait on the same background with only the words changed. The one exception is a deliberate weekly series, which may repeat its layout on purpose.
5. **Real people stay real.** When a real person appears, their face comes from their reference photos, at their real age and build. Never invent a face, never post the reference photos themselves.
6. **Exact size, verified.** Every file is finished to the exact pixel size in `references/asset-sizes.md` and its dimensions are checked, not assumed.
7. **Never bodge the shape in code.** Do not pad, letterbox, mirror, stretch or composite a generated image to force an aspect ratio. Re-roll with an aspect anchor instead (below). Why: a padded image has dead space that looks unfinished, and it is obvious at a glance.
8. **One alt-text line per image.** Plain description of the scene and the baked headline, no hashtags, no links, no selling.

## The method

### 1. Decide the picture (fresh for every image)

1. Name the single core message of the post in one sentence.
2. Decide the emotion: reassuring, clever, calm, funny, joyful, or a gentle warning. Default to warm. Never doom.
3. Invent one visual idea that carries it: a person in a real moment (on the phone on a busy street, at a kitchen table with a coffee, unpacking boxes), or a single readable metaphor (a safety net under a shop front, a chain with one cracked link, a calendar with one day ringed).
4. Write the headline (2 to 5 words is ideal, never more than three short lines) and an optional one-line subhead. Lead with the plain, literal line that says what it is; offer a cleverer hook as a labelled alternative. Why: plain headlines tend to win on clarity and on search, and people pick them when given the choice.
5. Plan the empty zone for the headline from the start, usually a darker area of sky, wall or shadow inside the grid-safe square.

### 2. Generate the scene with the headline in it

Write one prompt that describes the scene, the light, the framing and the text together. Spell the headline exactly, in quotes, say which word is the accent colour, ask for "huge, bold, condensed, poster-scale" type in the reserved zone, and keep the subhead short enough not to wrap. Leave the very bottom clear.

Garble guards, because image models fail in predictable ways:
- A subhead that wraps often gets a word duplicated at the wrap ("first first"). Keep it to one line.
- Small fixed text (a name, a handle, a web address) is often misspelt. If the brand uses a small name tag, stamp that one element afterwards (`scripts/cover_from_frame.py --wordmark` shows how) rather than asking the model for it.
- Long headlines shrink and garble. Fewer words, bigger.

Open `references/prompting-and-aspect.md` for prompt structure, the aspect-ratio tricks and the Gemini worked example. The short version: if your tool exposes an aspect-ratio setting, use it; if it only returns squares, edit onto a blank canvas of the target ratio (`scripts/aspect_scaffold.py`) and never pass a square reference image alongside it.

### 3. Likeness lock (any image with a real person)

Read `references/likeness-lock.md` before the first face-led image of a session. In brief:

- Build from the reference photos in `brand/reference-images/`: edit a clean, front-facing headshot into the scene rather than describing the person in words, and feed two or three tight face crops (not whole scene selfies, whose backgrounds bleed in) as identity references. Rotate sideways phone photos upright first.
- Check the result item by item against a provided colour photo (hair colour, hair style, facial hair, face shape and build, glasses, age). Never judge a likeness against another AI image.
- Budget about three or four honest re-rolls. If it still isn't them, rebuild the piece as a faceless scene (the metaphor plus the headline). If that won't work either, hold it and say so. A wrong face is worse than no image.
- Never post or crop the reference photos into the image directly. They are identity references only.

### 4. Real-frame covers for filmed video

When the person has filmed a talking-head video, the cover is built from a real frame of that footage, not a generated likeness. The face is genuinely theirs and the cover matches the video. This is the one place a designed headline overlay on a photo is the right call, because it is titling a real photograph, exactly as a thumbnail designer would.

1. Pull candidate frames (`ffmpeg -ss <t>`) or let the script find the sharpest face frame in a time range, and choose one with eye contact, a warm expression (not mid-word), sharp focus and no burned-in subtitles.
2. Run `scripts/cover_from_frame.py` (see its `--help`): it cover-crops to size, adds a soft scrim, auto-fits the hero headline with one accent word and an underline inside the grid-safe square, adds an optional subhead ribbon and optional name tag, then checks every text box against the safe zone.
3. Match the video's shape: a 9:16 short gets a 9:16 1080x1920 cover with the text in the central square; a 16:9 long-form gets a 1280x720 cover. If the edit is being made with the `video-editing` skill, its own cover step does this inside the edit.

### 5. Animated statics (the one exception to "no overlays")

An animated static is a 4 to 6 second looping MP4 that fills a still slot and is treated as video by most feeds. Text has to be a separate layer to move, so here, and only here, designed kinetic type sits over a generated scene. It is held to the same bar: a real scene, hero headline, brand colours, grid-safe placement, and **the full headline already visible in frame 0**, because the grid posters a video from its first frame. Open `references/animated-statics.md` for when to use one, the config for `scripts/animate_render.js`, the audio-bed rights rule and the review points.

### 6. No image model available: the HTML route

If no image model is connected, or the piece is a pure type layout (a verbatim quote card, a stat card, a carousel of text slides, a profile banner), design it in HTML and CSS and render it with Playwright. Rules that matter: the viewport is the true output size, no CSS scale transforms, fonts loaded before the screenshot, and the PNG's dimensions checked afterwards. Open `references/html-fallback.md` and use `scripts/render_html.js`. A quote card is also the right route when a testimonial must be reproduced word for word, because generated text can drift.

### 7. Finish, file and describe

1. Finish to the exact size for each destination (`references/asset-sizes.md`). A 4:5 master usually serves Instagram, Facebook, LinkedIn and Threads; derive a 1:1 by centre crop only if all text sits inside the central square, otherwise generate a separate square.
2. Run `python3 scripts/check_image.py <file> --expect WxH --grid` to confirm dimensions and write a grid-preview sheet (the centre square and 3:4 crops at thumbnail size, with the safe box drawn on).
3. Save to `content/<yyyy-mm-dd>-<slug>/images/` with a name that says what it is (`<slug>-feed-4x5.png`, `<slug>-cover-9x16.png`).
4. Write one alt-text line per image into the piece's `PACKAGE.md`, for example: *"A woman in a flour-dusted apron flipping the sign on a bakery door to OPEN, with the headline 'Open before the school run' across the top."* Each carousel slide gets its own line. Video covers do not need alt text.
5. Keep the final prompt (and any re-roll notes) in the piece folder, so a future re-roll starts from what worked.

## Checks before it ships (the review loop)

Every generation and every re-roll is a new image, so it gets the full check on the **filed file**, opened and looked at, never judged from the prompt:

- Spelling of every word in the headline, subhead and any stamped tag; no duplicated words.
- Headline primacy: dominant, reads first, legible at profile-grid thumbnail size.
- Grid-safe: all text inside the centred square with the margins; nothing touching an edge; nothing in the bottom band. For any video, judge the first frame.
- Likeness (face-led pieces): the rubric against a provided colour photo. Unsure counts as a fail.
- Shape: true dimensions match the target; nothing padded or stretched.
- Brand: palette and fonts from the profile, accent used sparingly, natural colour.
- Distinct: not a near-copy of the last few images on the account.
- Truth and compliance: any figure or claim in the image traces to a source; required labels from `## Compliance` are present; nothing from `## Boundaries` appears.

If it fails, fix the cause and re-roll, then judge the new file the same way. Then hand the set to the `review-loop` skill for the independent pass. If a piece cannot be made clean, keep the prompt, say what failed and hold it. Never ship a stand-in face or a text-pasted fallback.

## Adapting it

- **No real person on camera?** Skip the likeness lock and lean on scenes and metaphors; the rest of the standard is unchanged.
- **A product business?** Treat the product as the "face": use real product photos as references so the model keeps its shape, label and colour honest.
- **Different image model?** The method holds. Only the mechanics in `references/prompting-and-aspect.md` change (how aspect ratio is set, whether reference images are accepted).
- **A series format** (weekly roundup, tip of the week): fix one composed layout for the series and vary everything else between series.
- **Regulated industries:** check `## Compliance` for anything that must appear on an image or must never appear (figures, guarantees, testimonials). When in doubt, keep claims out of the image and in the caption where the disclaimer sits.
- **Your own lessons:** when the user rejects or swaps an image, note what and why in `brand/performance-learnings.md` (visual lessons) or `brand/voice-learnings.md` (headline wording), so the next image starts closer.

## Files in this skill

| File | Open it when |
|---|---|
| `references/asset-sizes.md` | finishing any file; checking a platform's current size |
| `references/grid-safe-zone.md` | placing text on any format |
| `references/prompting-and-aspect.md` | writing a prompt, fighting the aspect ratio, using Gemini |
| `references/likeness-lock.md` | any image with a real person in it |
| `references/animated-statics.md` | making a looping MP4 for a still slot |
| `references/html-fallback.md` | no image model, or a pure type layout |
| `scripts/aspect_scaffold.py` | making a blank canvas at the target ratio for edit-based tools |
| `scripts/cover_from_frame.py` | building a cover from a real video frame |
| `scripts/animate_render.js` | rendering an animated static |
| `scripts/render_html.js` | rendering an HTML/CSS design to PNG at true size |
| `scripts/check_image.py` | verifying dimensions and previewing the grid crop |

## Learn more

A longer guide with examples lives at https://builtnotboosted.com/skills/image-generation
