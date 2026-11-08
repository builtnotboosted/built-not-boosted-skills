# The grid-safe zone

The feed shows a piece full-size, but the profile grid, link previews and many in-feed previews crop it to a squarer tile. Anything near an edge, or high or low in a tall frame, disappears exactly where a new visitor decides whether to follow. Typical failures: a headline sliced at the left or right edge ("[Y]OUR PLAN"), a subhead lost off the bottom, a 9:16 cover whose headline sat too near the top and vanished in the 3:4 grid tile.

So every image keeps **all** text (headline, subhead, labels, the accent word and its underline) inside one box.

## The rule

- **The zone is the centred 1:1 square of the canvas, inset a further 7 to 8% on every side.** Treat everything outside it as bleed that may vanish.
- **Top margin, always.** At least 8% clear above the headline. The crop and the platform's own username bar both eat the top.
- **Bottom band clear.** Nothing important in the bottom 12%: that is where play counts, pinned labels and caption previews sit (TikTok stacks them bottom-left), and where a small name tag goes if you use one.
- **Side margins.** Cap the widest headline line at about 85% of the safe-zone width, so a slightly tighter crop cannot shave the first or last letter.
- **Bigger with it, not smaller.** Safe does not mean small. Keep the wording short (two or three punchy lines) and set it large inside the square. Small and safe still fails.

## Per format

| Format | Canvas | Text box (approx. rows/cols) | Notes |
|---|---|---|---|
| 9:16 cover or animated static | 1080x1920 | central square rows 420 to 1500, inset ~80 px | Headline in the upper half of that square, subhead below; nothing in the top ~28% or bottom ~15% of the full frame |
| 4:5 feed static / carousel | 1080x1350 | central square rows 135 to 1215, inset ~80 px | The bottom ~160 px stays clear |
| 1:1 square | 1080x1080 | whole frame inset ~80 px | |
| 16:9 long-form / article cover | 1280x720 | out of the outer ~8% on every side | Rarely grid-cropped, but the margins keep link previews clean. Keep clear of the bottom-right duration badge |
| 4:3 local listing card | 1200x900 | inset 8% all round, with a top margin | |

## Every format is judged by its grid frame

For a still, the grid frame is the image. For any video (filmed talking head, designed cover, animated static) it is the **first frame** or the chosen cover. So the hero headline must be present, legible and inside this zone in that exact frame. A tile that shows a bare scene (feet under a table, someone's back) tells a new visitor nothing, and those tiles tend to be the weakest on reach. Nothing ships whose grid tile says nothing.

## How to check

Run `python3 scripts/check_image.py <file> --grid`. It writes a sheet with the centre 1:1 crop and the 3:4 crop at thumbnail size, with the safe box drawn on the full frame. Look at the thumbnails, not the full-size image: if a word is clipped or the headline does not punch at that size, re-place or re-roll.
