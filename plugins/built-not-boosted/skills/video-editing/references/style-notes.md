# Style notes: what good short-form editing looks like

Distilled from studying the shorts and thumbnails of experienced broadcast-trained video creators, frame by frame. The lessons are about craft (format, pacing, shot and cover design), translated into the house method. The brand, the colours and the person on camera are always your own: never copy another creator's typeface, colours, phrasing, series titles or thumbnail text.

## What the professionals do

**Shape of a short**
- One idea. Often 25 to 50 s, rarely to 60. The payoff or the promise in the first second, no preamble.
- **Frame 0 carries a hook card:** 2 to 4 words in huge condensed capitals, soft shadow, over the opening shot. It reads in the grid and in the feed before a word is spoken. A repeated series hook is fine.
- A short spoken ending: a one-line follow invitation or question, then often a walk out of frame (a soft exit).

**One line, one shot**
- Short, simple sentences; each sentence recorded as one shot; the perfect version of each phrase kept. The edit is then "this, this and this", not a jigsaw. This is exactly the one-clean-read rule.
- Reading from a prompter while moving towards the lens beats memorising and jump-cutting, which looks like it was made under duress.

**Never static, and every change is motivated**
- Shot size changes by moving the camera or the person closer: wide for the first line, mid for most of it, close when it gets intense. Physical moves where the footage has them; the edit's punch-ins and reframes where it does not.
- **Every cutaway is motivated:** a look at a phone, then cut to the phone; a head turn towards something, then cut to it, or slide the B-roll in from the direction they looked.
- **A small close-up before a new scene** (hands, an object, a detail) hints at what is coming and makes the piece flow. Not every shot needs a face.
- **Doing something in each shot** (walking, sitting down, pouring, typing). Slightly unexpected is good: it drives comments.
- Useful B-roll types: slow-motion walking, a point-of-view of hands doing something, a wide walk-in with graphics over it, and wide / closer / keyboard / screen coverage at a desk.

**Captions**
- 1 to 3 words at a time, bold sans on a tight dark box, sometimes with the current word bright and the rest dimmed (a word-by-word reveal). Lower middle, clear of the face. Occasional single-word emphasis.

**Look**
- Bright natural light, clean uncluttered backgrounds, saturated wardrobe that pops against the background.
- Any voiceover recorded on location on the day, so it sounds the same as the on-camera audio.

**Covers**
- 2 to 4 words, huge condensed capitals with a soft dark edge. A claim or a feeling, not the title repeated. Occasionally one word in an accent colour.
- Mid shot, centred, high colour and contrast, instantly recognisable.
- **A prop that tells the story** (a phone on a tripod, a sign, a tool of the trade).
- Every cover is the same system, so the grid reads as one brand.

## How it lands in our edits

| Lesson | In the edit | Where |
|---|---|---|
| Hook card on frame 0 | 3 to 5 words from `edit_notes.hook_on_screen`, condensed head font, one highlight word, held 1.5 to 2.5 s. The cover may use the same words | `title` template, cue `{"t": 0}` |
| One line, one shot | Already the method (take picker + gate). Keep each kept line as its own shot when the speaker changes position; never stitch half-lines | takes, picks |
| Shot size by distance | Use real distance changes when the footage has them; otherwise the punch-ins and reframes make the variety | build |
| Motivated cutaways | B-roll right after a look or gesture (find it on the frames sheet), sliding in from the direction of the look; otherwise on the word it illustrates, never at random | cue anchors |
| Close-up before a new scene | A 1 to 2 s detail shot (hands, the product, the tool, a document with no private data) before each section | B-roll library, shot list |
| Doing something in each shot | Find the action in the footage (a sip, a gesture, a walk) and cut on it; B-roll covers the rest | edit |
| Word-reveal captions | Offer as an option against the house captions; never switch the house style unasked | not built yet |
| Length | Length follows the message. Take the discipline, not the runtime: one idea, no padding, every line earns its place, a change on screen every few seconds | edit, `video-scripting` |
| Soft exit and one-line CTA | Last line, a quick spoken question or follow, walk out, fade. An early "who I am" stays too if the script has one | `exit_tail` |
| Covers: fewer words, bigger | 2 to 4 words, one highlight word; drop the subhead chip unless it adds a fact; a frame where the person's colour pops and a prop tells the story | cover rules |
| Location voiceover | If a line needs re-recording, record it on the day in the same spot | shoot sheet |

## Tone wins over tempo

The energy in good editing comes from shot variety and motivated cuts, not from speed. Never make a person faster or more hyped than they are: their voice and pace come from `brand/brand-profile.md` and `brand/voice-learnings.md`.
