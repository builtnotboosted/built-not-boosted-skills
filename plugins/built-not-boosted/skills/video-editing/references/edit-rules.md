# Edit rules

What the build applies, and what to judge a result against. Each rule exists because the opposite was heard or seen in a real edit.

## Cuts

- **Frame-exact cuts keep picture and sound in sync.** Every piece starts and ends on the frame grid; video is cut by frame index and audio to the same instants, so each shot's picture and sound are exactly the same length. Why: trimming video by timestamp and re-timing it lets each shot run up to a frame long, and across twenty-odd shots the picture drifted about 150 ms behind the sound.
- **Out-points wait for the sound to die away**, not for Whisper's word end: the cut lands at the first deep quiet after the last word (-45 dB, falling back to -38 then -30 dB where the background never gets that low) plus 0.10 s, and never runs into the next speech. Why: soft endings (-ing, -s, -ty) keep sounding below -30 dB; six clipped word endings in one early edit all sat inside a -30 dB "silence".
- **In-points sit in the quiet gap** before the first word. The tail of the previous word, or of an abandoned attempt, is a bad in-point. The take finder often starts a restart inside the abandoned read, so trust the cut check, not the take's `in`.
- **A trim outside a line's kept range is ignored**; it must never extend the line (for example into chatter after the last word).
- **Second-listen trims can be wrong.** Read each proposed trim against the word timings; a trim whose times do not sit on the repeated words is switched off in `picks.json` (`"trims": {"0": false}`).
- **Same-run lines merge** into one continuous range (never replay audio), and an overlap guard means no two ranges share source time.
- **Interior pauses over 0.85 s are trimmed** to a natural ~0.35 s beat. A soft word inside the pause (real sound under it, a break in the -45 dB quiet) is kept by resuming just before it. A soft word right at a pause's edge can still be clipped; protect that pause with `build.keep_pause` `[[a, b]]`.
- **Before cutting a pause out of a line, listen to the stretch after the pause on its own.** If it starts with the line's opening words, the presenter restarted: start the line there (`nin`) instead of cutting inside it.
- **Hard cuts get 12 ms audio fades** (no clicks).
- **Framing alternates wide and tight (1.14x) on every cut**; ranges over 9 s get a reframe at a line boundary every 6 to 9 s. Do not push past about 1.15x on 1080p phone footage: it goes soft.
- **Soft exit:** the last line breathes about 0.45 s, then the empty-frame tail, then a 0.25 s fade. End no more than about 0.6 s after the presenter leaves the frame; anything said after that is off-camera and stays out.

## Natural fillers

Restarts, re-reads and stumbles always come out. A lone short "um" (under 0.45 s) outside the opening line is proposed in the picker but kept by default. Fillers in the hook line, long ones and clusters are cut. The gate fails only on a filler in the hook line or two in one line.

## Captions

- Transcribed from the finished cut (so they match exactly), then checked against the script (`scripts/caption_check.py`, run in the caps stage). Words that both unprompted listens heard are the speaker's and stay (REWORD: a live reword is not an error). Only the lines that differ from the script get a re-listen prompted with that one line; script words win only where that re-listen hears them (FIX), and a word the caption lacks is added only if an unprompted listen heard it too. Anything unclear is listed for a human (CHECK). The report ships with the video.
- A word Whisper stretched over a whole phrase is re-heard on its own and the missing words refilled.
- House style: bold sans in a dark rounded box, centred in the lower middle (y ≈ 1558 on 1080x1920), at most two lines, key words (figures, names) in the brand highlight colour, figures as numerals ("4%", "8 to 1"), hidden under full-frame section cards and resumed when the card clears. The SRT always carries every line.
- `captions.fix` corrects names Whisper mishears. `captions.key` is matched word by word: **never put a single letter in it** (an "A" category highlighted every article "a").
- UK spelling by default (`captions.locale`).

## Loudness and encoding

Two-pass loudnorm to -14 LUFS integrated, -1.5 dB true peak. H.264 CRF 18 high profile, AAC 48 kHz, faststart. Optional background-noise gate before loudness (see `audio-and-sync.md`).

## Graphics and B-roll

- Every figure on screen is in `sources.txt`, worded the way the source words it, with a source line on charts. No third-party logos, product names or rate tables unless the brand profile allows them.
- One graphic at a time (the build trims overlaps). Graphics land on the word they illustrate: anchor numbers to the spoken word, everything else to the line.
- B-roll is a cutaway under continuous voice, 2 to 4.5 s. Never client or customer data, never a recognisable person without consent, licence on file for anything not filmed in-house.
- A full-frame `section` card hides the burned captions while it is up.
- Check every graphic and hook card against what was actually said, not the script (live rewords).

## Covers

- Real frame, reframed at most 1.12x (beyond that ears clip and detail softens), warm grade, soft dark zones for type (no hard band edges).
- Hero headline inside the central 1:1 square (y 420 to 1500 on 1080x1920) with a 7% inset; the tool fails any box outside it. Check `grid_tiles.jpg`: the grid shows only that square.
- 2 to 4 words, big. A claim or a feeling, not the title repeated. One highlight word. Plain and true: a punchier line that is not accurate is rejected.
- Type never covers the face (the tool fails any text box 16 px or more into the brow-to-chin zone). The subhead chip is the usual offender: drop it first, then shrink the hero, then reframe.
- The lead cover is burned in as the first 0.13 s of a short (the poster frame the grid uses). Long-form uses the uploaded 1280x720 thumbnail instead, with type on the side away from the face and clear of the bottom-right duration badge.
- Offer one or two variants and let the person choose.

## Length

Length follows the message: never suggest a split just to hit a runtime. Make a longer cut hold instead: no padding, interior pauses trimmed, and a shot, graphic or cutaway change every few seconds.
