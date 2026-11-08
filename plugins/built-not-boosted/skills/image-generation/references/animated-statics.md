# Animated statics

An animated static is a short looping MP4 (4 to 6 seconds) that fills a still-image slot. Most feeds treat it as video, which often earns more reach than a flat image, and it costs far less than filming.

## Why it is the one exception to "no overlays"

On a still, the headline is baked into the scene by the image model. Text on an animated static has to be a separate layer so it can move. So this format, and only this format, carries designed kinetic type over a generated scene. It is not a licence for a lazy plate with words on it; it is held to the same bar:

- The background is a real, cinematic scene made per the main skill (distinct, natural colour, accent used sparingly). Never a flat card, never padded to shape.
- The headline is the hero: big, bold, condensed, one accent word, legible on a phone.
- All text inside the grid-safe zone.
- **The full headline is on screen in frame 0.** The profile grid posters a video from its first frame. A render that starts on a bare scene and brings the headline in later reaches the grid as a tile that says nothing, and those tiles are usually the weakest on reach. The bundled renderer holds the scrim, headline and underline from frame 0 and animates only the supporting lines.

## When to use one

Good fits: a single punchy hook, a myth busted in one line, a timely alert, a seasonal moment, a tip with one clear payoff, on platforms that reward video (Instagram first, then Facebook, TikTok, LinkedIn).

Skip it for: Google Business Profile (still images only), light-touch platforms such as Bluesky or X where one clean image is enough, and genuine human or local moments that should be a real photo. Do not animate everything: keep it to the posts where the motion adds something, and let `brand/performance-learnings.md` tell you whether it is paying off.

## Method

1. **Make the scene** with the image model at the target aspect (`aspect_scaffold.py` for 4:5 or 9:16). Reserve a darker zone for text, usually the lower half, inside the central square. Make the scene text-free and let the renderer carry the headline, so the words never appear twice.
2. **Write the config** (below) with the brand colours and font files from `## Visual identity`.
3. **Render**: `node scripts/animate_render.js config.json`.
4. **Review the poster frame** (`<out>.poster.png`, frame 0) with `python3 scripts/check_image.py <out>.poster.png --grid`, then watch the MP4 once through.

## Config

```json
{
  "bg": "/abs/path/content/2026-11-12-early-opening/images/scene-9x16.png",
  "aspect": "9x16",
  "kicker": "Local tip",
  "headline": ["Open before", "the school run"],
  "accent": "Open",
  "subhead": "Fresh bread from 7am,\nMonday to Friday.",
  "payoff": "Pre-order the night before.",
  "cta": "What would you order first?",
  "footer": "Sam · Corner Bakery · Anytown",
  "brand": {
    "accent": "#F2A900", "primary": "#C8102E", "ink": "#FFFFFF",
    "headFont": "/abs/path/fonts/BarlowCondensed-ExtraBold.ttf",
    "bodyFont": "/abs/path/fonts/Inter.ttf"
  },
  "durationMs": 5000,
  "fps": 30,
  "audio": "/abs/path/marketing/audio/cleared-track-01.mp3",
  "audioVolume": 0.18,
  "out": "/abs/path/content/2026-11-12-early-opening/images/early-opening-9x16.mp4"
}
```

- Required: `bg`, `headline`, `aspect` (`4x5`, `9x16` or `1x1`), `out`. Everything else is optional.
- `accent` colours one word or phrase in the headline. `brand` can instead point at a JSON file via `brandFile`.
- Keep each subhead line short enough not to wrap (use `\n` for a deliberate break).
- Fonts are loaded from the file paths you give; if none are given it falls back to Barlow Condensed, Inter or system sans fonts that are installed.
- `poster: false` skips writing frame 0 as a PNG. `gif: true` also writes a GIF preview.
- Scratch goes to `$ANIMATE_RENDER_DIR` (default a temp folder) and is cleaned up; only the MP4 (and the poster PNG) are written to `out`.

Encoding: H.264, yuv420p, CRF 18, faststart, 30 fps by default. Drop to 24 fps only if render time matters.

## Audio bed

Silent video tends to be held back on audio-first feeds, so a quiet music bed helps. The renderer loops or trims the track to the clip, fades it in (0.5 s) and out (0.6 s), sits it low (`audioVolume` 0.18 by default) and encodes AAC.

**Rights rule, no exceptions:** only tracks cleared for commercial social use (your own music, genuinely royalty-free, or licensed for social and commercial use). Never a commercial song: platforms mute or strike it, and on a business account it is a legal risk. Keep cleared tracks in one folder with a note of the licence for each, and rotate through them so every piece does not use the same tune.

Trending in-app audio on Reels and TikTok can only be added inside the app, so it is a manual step for the odd hero post, never part of an automated run.

## Review checklist

- Frame 0 (the poster): headline fully present, inside the grid-safe zone, on its scrim, legible at thumbnail size. A bare first frame is a reject.
- In motion: everything readable, nothing clipped at the edges, the loop does not jar.
- Spelling of every word (headline, subhead, payoff, CTA, footer); no duplicated words.
- Brand: palette and fonts right; the scene is a real moment, not a flat card or a padded image.
- Size exactly 1080x1920, 1080x1350 or 1080x1080; length 4 to 6 seconds.
- Any figure or claim on screen traces to a source; compliance lines present where the brand profile requires them.

Then hand it to the `review-loop` skill like any other piece.
