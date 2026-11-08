# Multi-camera shoots and long-form

Long-forms (16:9, 10 to 15 minutes, often with a full-size prompter) and any shoot with a second camera use the same method as shorts, with these differences.

## Find every camera first

A shoot folder can hold, per video: the main camera (camera A), sometimes a second phone, sometimes a drone, plus short clips and photos.

- **Second cameras with sound:** pair them by sound. Run `scripts/sync_cams.py A_16k.wav B_16k.wav` for every long take against every camera A and read the results as a matrix: a real match has a `confidence` of about 0.4 to 0.55, a non-match about 0.03. Do not trust file creation times on phones: they are often the import time, not the shoot time.
- **Silent cameras (drones, action cams with no mic):** pair by the time in the filename against camera A's start, then `scripts/sync_cams_visual.py A.mp4 drone.mp4 --box x0,y0,x1,y1` (motion match; the box is around the presenter in the drone's pixels). The motion peak alone can be weak, because a hovering drone adds its own motion: trust it only when it agrees with the timestamps **and** a visible event lines up (walking to the tripod, a wave). Write the result into `project.json` `sync` by hand with `"method": "motion"`.
- **A camera the person mentions that is not in the folder:** ask for it straight away. Build with what is there and fold it in when it arrives.
- **Silent cameras and crops:** make `cam_<N>.mp4` yourself (crop a 9:16 window around the presenter from 4K, no more than 1.35x upscale, at the project frame rate) and write `cameras` and `sync[N] = {a, b, covers, method}` into `project.json`.
- **B-roll:** contact-sheet every photo and short clip (apply EXIF rotation to photos), note what each shows, and file the usable ones in the B-roll library (`broll_root`) with a row in `broll-index.csv`. Stills become 4 s slow push-in clips first. Never use a photo with anyone who has not consented, half-faces or the backs of heads. B-roll the script asks for that the shoot lacks goes on the next shot list.

## Init and prep

`vedit.py init <slug> --raw <cameraA> --pack <content folder> --long --cam B=<second camera>`. Camera A's sound is used for the whole edit.

Prep keeps the camera's own frame rate (24, 25 or 30; a 25p camera is never converted to 30, which judders), makes every camera the same size, then lines each extra camera up with A by its sound: a whole-recording loudness match, then exact matches in several 20 s windows, fitted for clock drift. It prints the offset, the drift and the stretch of A each camera covers. "SYNC NOT TRUSTED" means that camera is left out of the cut: it needs clear sound of the presenter (its own mic on).

## Takes and chapters

`[CHAPTER N • Title]` lines in the script are silent markers: the take finder skips them and remembers where each chapter starts. `build` writes `chapters.txt` (first at 0:00) for the YouTube description and warns if YouTube would reject them (it needs 3 or more chapters, each at least 10 s). `deliver` files it as `<version>-youtube-chapters.txt`. The picker shows 16:9 clips.

## Camera calls

- With no calls, shots cycle A wide → B → A close-up (1.14x) → B, changing at line boundaries and every 6 to 9 s inside long reads. If camera B was not rolling at that moment, the shot falls back to the A close-up.
- **Show the camera the presenter is talking to.** If they turn to camera B for a line, put `"cam": "B"` on that line in `picks.json`; lines without a call stay on camera A. Judge it on a frame from the middle **and** the edges of the line: calling by eye from one mid-line frame has put a call a line early and missed half-turns (head 20° round, eyes doing the rest).
- **Measured calls (optional):** if you have a head-direction tool, write `gaze.json` into the project folder and the build will cut at the turn itself, and the gate will fail any 1.2 s+ stretch where the presenter faces one camera and the render shows another (B-roll covering it is fine). Format:

```json
{"fps": 4, "facing": ["A", "A", "B", null, "B", ...]}
```

Sample `k` is camera-A time `k / fps`; `null` means no reliable reading. A sensible rule: within about 12° of A's lens = A; 15° or more off A and no further (plus 5° slack, at most about 45°) from another camera's lens = that camera. Glances under 1 s should not switch. A hand `"cam"` in picks still wins for its line.
- A drone wide is an establishing angle: use it where the presenter talks to a camera you do not have, at section changes, and never for long.
- `framing.face_x` / `eye_y` are measured on a frame of camera A in 16:9 pixel space.

## Graphics, captions and covers in 16:9

- The same `graphics.json` templates. In 16:9 each card is cropped to its visible box and placed beside the presenter (on the side opposite `face_x`), lower thirds bottom-left, section cards full frame. Vertical library B-roll sits sharp over a blurred fill.
- Captions are **not** burned in on long-form (YouTube carries the SRT as closed captions); `captions.burn: true` overrides. The SRT still comes from the finished audio.
- The cover is a 1280x720 YouTube thumbnail from the same `cover.variants`: type on the side away from the presenter, clear of the duration badge bottom-right, the optional name tag bottom-left. A variant can take its frame from another camera with `"camera": "B"`. `grid_tiles.jpg` shows it at search-result size.
- No poster frame is burned into long-form (YouTube uses the uploaded thumbnail).

## Lip sync on camera B

After the first real multi-camera build, check lip sync on camera B shots with `scripts/lipsync.py` (pick windows where the presenter faces that camera). Sync by sound is usually within a frame; a camera with a delayed wireless mic is the usual exception.
