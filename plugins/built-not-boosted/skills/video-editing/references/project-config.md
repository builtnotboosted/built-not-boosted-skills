# project.json and graphics.json reference

Everything that changes from one video to the next lives in the project folder (`$VEDIT_HOME/work/<slug>/`, default `~/.vedit/work/<slug>/`), never in the scripts. `vedit.py init` writes `project.json` from `references/project-template.json` and fills what it can (paths, title, brand from the workspace's brand profile, edit notes).

## project.json

| Key | Meaning |
|---|---|
| `slug`, `title`, `version` | `title` + `version` name the delivered files (`<title> - v1.mp4`). Bump `version` for a re-cut. |
| `raw`, `pack`, `out_dir` | camera A's clip (its sound is used for the whole edit), the content folder holding the script, and where `deliver` writes (default `<pack>/video`). |
| `workspace` | the marketing workspace found at init (for the brand profile). |
| `format` | `"long"` for a 16:9 long-form (1920x1080); omit for a vertical short (1080x1920). Set by `init --long`. |
| `fps` | working frame rate, set by `prep` from camera A (24, 25 or 30). Never converted to a different rate. |
| `cameras` | extra cameras `[{"name": "B", "raw": "<clip>"}]`, set by `init --cam B=<clip>`. |
| `sync` | written by `prep`: per camera `a`, `b` (tB = a·tA + b), `confidence`, `covers` [start, end] in camera-A time. For a silent camera synced by motion, write `{"a": 1, "b": <lag>, "covers": [...], "method": "motion"}` by hand from `sync_cams_visual.py`. |
| `edit_notes` | from `edit-notes.txt` next to the script: `hook_on_screen` (3-5 words for frame 0), `cover` (cover words), `outcome` (what the viewer should do or feel). |
| `vocab` | every proper name in the script (people, places, products, the presenter's own name), fed to Whisper's prompt so it spells them right. |
| `syn` | Whisper spelling → script spelling, lower case, for alignment (`{"jon": "john"}`). |
| `whisper` | optional lighter models for slow machines: `{"large": "small.en", "medium": "base.en"}`. Accuracy drops; the gate still runs. |
| `brand` | the look of graphics, captions and covers (below). Absent keys fall back to a neutral default. |
| `framing` | `face_x`, `eye_y` (pixels in the master frame) and `zoom` (1.14) for the tight shot. Measure on one frame. |
| `exit_tail` | `[start, end]` raw seconds of empty frame after the presenter walks off (the soft exit), or `null`. |
| `broll_root` | the B-roll library folder; `broll` cue paths are relative to it (absolute paths also work). |
| `graphics` | graphics spec file (default `graphics.json`). |
| `cues` | when each graphic and B-roll cutaway appears (below). |
| `captions.fix` | `[regex, replacement]` pairs run before the built-in fixes (names Whisper mishears). |
| `captions.key` | words shown in the highlight colour in captions (figures, names). Exact tokens; trailing punctuation allowed. **Never a single letter**: "A" matches every "a". |
| `captions.burn` | burn captions into the picture (default: yes for shorts, no for long-form, where YouTube shows the SRT). |
| `captions.hide_under` | graphic templates that cover the frame, so burned captions wait for them to clear (default `["section"]`). |
| `captions.locale` | `en-GB` (default) applies UK spelling fixes to the captions; `en-US` leaves US spelling. |
| `cover` | `frame` (raw seconds), `reframe` (`scale` ≤1.12, `x`, `y`), `lead` (variant name), `variants` (below), `wordmark` (optional `["Name", "What you do"]` name tag), `unbranded` (true = no name tag). |
| `audio.denoise` | `"firm"`, `"gentle"` or a number 0-1: spectral noise gate on the finished audio for a steady hum or whine. Measure first; send a before/after to someone who can listen. |
| `gate.allow` | `[{"t": <output seconds>, "why": "..."}]` seams checked by hand (energy map + isolated listen + a reason). They become notes, never silent passes. |
| `cut_check.allow` | `[{"t": <raw seconds>, "why": "..."}]` cut points verified by hand that the energy rules cannot confirm. |
| `build.keep_pause` | `[[a, b]]` source-time ranges whose interior pause must not be shortened (a soft word sits at the pause edge and would be clipped). |
| `allow_low_audio` | `true` to edit call-quality audio anyway (say so in the hand-over). |

### brand

```json
"brand": {
  "highlight": "#C8102E",
  "underline": "#F2A900",
  "ink": "#EDE8E0",
  "dark": "#111111",
  "chip_text": "#111111",
  "head_ttf": "~/.vedit/fonts/BarlowCondensed-ExtraBold.ttf",
  "body_ttf": "~/.vedit/fonts/Inter.ttf"
}
```

- `highlight` (alias `accent`): the punch word, chips, bars and caption key words.
- `underline` (alias `primary`): the underline under the punch word.
- `ink`: text colour. `dark`: panels and scrims. `panel`/`panel2`: optional graphic panel fills (rgba).
- `head_ttf` / `body_ttf`: font files (`~` allowed). `setup.sh` downloads Barlow Condensed and Inter (open licence) into `~/.vedit/fonts/`.
- `init` maps the brand profile's `## Visual identity` table: Primary → `highlight`, Accent → `underline`, Base → `dark`, Light → `ink`, and looks for installed font files by family name. Check what it filled.

## Anchors (where in the FINISHED video something happens)

```
{"t": 0.15}                                        a fixed time
{"line": "regex on the script line"}               the start of that line in the edit
{"line": "...", "edge": "end"}                     the end of that line
{"line": "...", "words": ["seven|7", "am"]}        walk forward from the line start to each spoken word in turn
                                                   (each a full-match regex on the lower-cased word)
... + "offset": 0.2                                shift in seconds
[anchor, anchor, ...]                              the first one that resolves (fallbacks, e.g. if a line was cut)
```

Anchor numbers to the WORD (the graphic lands as it is said) and everything else to the line. Anchors follow the edit when picks change; fixed times do not, so use `t` only for frame 0.

## Cues

```json
{"graphic": "g03_price", "at": ANCHOR, "until": ANCHOR, "min": 3.0, "max": 4.5}
{"broll": "kitchen/hands-kneading_v916.mp4", "at": ANCHOR, "dur": 2.6, "cin": 0.8}
```

- Duration = `until` minus the `at` anchor without its offset (or minus `from` if given), clamped to `min`..`max`; `dur` fixes it; `default` is used if `until` does not resolve (else `min`).
- `requires`: a list of line regexes that must all be in the edit, or the cue is dropped.
- `params`: merged into the graphic's params. Inside, `{"$at": ANCHOR, "min": 1.4, "default": 1.4}` becomes "seconds after this graphic starts" (chips or quotes that pop in on a later word).
- `cin` on a B-roll cue skips a slow start of the clip.
- A cue whose anchor is not found is reported by `build cues` as NOT PLACED. Fix it; never ship with one missing.
- Graphics never overlap (each is trimmed to 0.05 s before the next).

## graphics.json: `[{"id", "tpl", "params", "previewAt"?}]`

Templates live in `scripts/mg/kit.html` (1080x1920, transparent, brand colours injected, shared exit animation). `top` (px) moves most cards vertically; `size` scales type where offered. `<span class="lime">` marks the highlight word in `html` fields (the class name is historical; it uses the brand highlight colour).

| tpl | params | use |
|---|---|---|
| `title` | `lines[]`, `punch`, `kicker`, `size`, `top` | the frame-0 hook card or an opening title |
| `lower` | `name`, `role` | lower third: who is speaking |
| `stat` | `label`, `from`, `to`, `toLabel`, `prefix`, `suffix`, `decimals`, `delta`, `sub`, `top` | count-up to a figure |
| `vote` | `label`, `forN`, `againstN`, `note`, `top` | a count of dots ("7 out of 10") |
| `stamp` | `html`, `size`, `top` | one big statement stamped in |
| `chart` | `label`, `v0`, `l0`, `v1`, `l1`, `l2`, `dir` (up/down/flat), `unit`, `source`, `top` | then → now → direction, with a source line; no invented future number |
| `chips` | `items[{t, html}]`, `top` | reasons popping in one by one (`t` = seconds after start) |
| `split` | `leftTitle`, `rightTitle`, `left[{who, quote, t}]`, `right[...]`, `top` | two sides of an argument |
| `banner` | `html`, `by`, `size`, `top` | a quoted line with attribution |
| `section` | `lines[]`, `punch`, `size` | full-frame chapter card (captions hide under it) |
| `audience` | `q`, `a`, `size`, `top` | "If you're X?" → a plain answer |
| `calendar` | `label`, `month`, `day`, `dow`, `top` | a date (deadline, event, opening) |
| `cta` | `a`, `b`, `c`, `top` | the closing question: option A OR option B, then the comment prompt |

Example (a café's short about early opening):

```json
[
 {"id": "g01_hook", "tpl": "title", "params": {"lines": ["Open before", "the school run"], "punch": "before", "size": 120, "top": 520}},
 {"id": "g02_lower", "tpl": "lower", "params": {"name": "Sam", "role": "Owner · Corner Bakery"}},
 {"id": "g03_time", "tpl": "stat", "params": {"label": "Doors open", "from": 9, "to": 7, "toLabel": "7am", "suffix": "am", "sub": "Mon to Fri"}},
 {"id": "g04_why", "tpl": "chips", "params": {"items": [{"t": 0.1, "html": "Fresh bread <span class=\"lime\">by 7</span>"}, {"t": 1.4, "html": "Coffee to go in under a minute"}]}},
 {"id": "g05_cta", "tpl": "cta", "params": {"a": "Croissant", "b": "Sourdough", "c": "Tell me in the comments"}}
]
```

New template: add a `T.<name> = P => {...}` block in `kit.html` following the others (build the DOM, push animation tracks with `inn(...)`), preview it with `vedit.py mg-preview`, and add a row here.

## Cover variants

```json
"cover": {
  "frame": 41.2, "lead": "A", "reframe": {"scale": 1.1, "x": 0, "y": 60},
  "wordmark": ["Sam", "Corner Bakery"],
  "variants": {
    "A": {"top": "OPEN", "hero": ["BEFORE", "SCHOOL"], "hero_size": 300},
    "B": {"top": "FRESH BREAD", "hero": ["BY 7AM"], "chip": ["MONDAY", "TO FRIDAY"], "chip_size": 48}
  }
}
```

`top` is the white first line, `hero` the highlight-colour lines (auto-shrunk to fit the safe width), `chip` an optional subhead. Long-form (1280x720) sizes: `top_size_long`, `hero_size_long`, `chip_size_long`. Any variant can use another camera's frame with `"camera": "B"` (its `frame` is still given in camera-A time). Optional: per-variant `frame`, `top_size`, `hero_gap`, `line_gap`, `hero_dx`, `chip_gap`.

## picks.json (written by the picker, or by Claude when asked to pick)

```json
{"4": {"take": 2, "nin": 0.0, "nout": -0.2, "trims": {"0": true, "1": false}, "cam": "B", "note": "take 1 had a restart mid-line", "confirmed": true}}
```

Keys are line ids (0-based). `take` 0 = leave the line out. `nin`/`nout` nudge the in/out point in seconds (+ = later). `trims` switches proposed inner cuts on or off by index. `cam` forces a camera for that line (multi-camera). `note` lands in the cut list.
