# The HTML/CSS route

Use it when:

- no image model is connected (or the user does not want one used),
- the piece is a pure type layout: a verbatim quote or testimonial card, a stat card, text carousel slides, a profile banner or cover,
- exact text matters more than a scene (a review reproduced word for word, a legally required line).

This is a designed layout, not a photo with text dropped on it, so it does not break the "bake the headline into the scene" rule. It still follows the rest of the standard: hero headline, grid-safe zone, brand palette and fonts, exact size.

## Rules that stop it looking wrong

1. **Viewport = the true output size.** Set the browser viewport to exactly the target pixels (for example 1080x1350) with a device scale factor of 1, and design the page at that size in pixels.
2. **No CSS scale transforms** to fit a smaller design into the frame. They soften text and break layout maths. Design at full size instead.
3. **Load fonts before the screenshot.** Use `@font-face` with local font files (or Google Fonts), then wait for `document.fonts.ready`. A screenshot taken too early silently uses a fallback font.
4. **Fixed-size body**: `html, body { width: 1080px; height: 1350px; margin: 0; overflow: hidden; }` so nothing scrolls or reflows.
5. **Check the PNG afterwards** with `python3 scripts/check_image.py out.png --expect 1080x1350 --grid`. Do not trust the page; trust the file.
6. **Colour tokens from the brand profile** as CSS variables at the top of the file, so one change restyles every card.

## Render

```
node scripts/render_html.js card.html card.png --size 1080x1350
```

It opens the page at that viewport, waits for fonts and images, screenshots exactly the viewport and prints the PNG's real dimensions. Add `--wait 500` for pages with late-loading assets, or `--selector "#card"` to capture one element (its box must already be the target size).

## A minimal card

```html
<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: Head; src: url("fonts/BarlowCondensed-ExtraBold.ttf"); }
@font-face { font-family: Body; src: url("fonts/Inter.ttf"); }
:root { --bg: #111111; --ink: #EDE8E0; --accent: #C8102E; --bar: #F2A900; }
html, body { width: 1080px; height: 1350px; margin: 0; overflow: hidden; background: var(--bg); }
.safe { position: absolute; left: 80px; right: 80px; top: 215px; bottom: 215px;
        display: flex; flex-direction: column; justify-content: center; }
.bar { width: 120px; height: 14px; background: var(--bar); margin-bottom: 36px; }
h1 { font: 800 150px/0.9 Head, sans-serif; text-transform: uppercase; color: var(--ink); margin: 0; }
h1 em { font-style: normal; color: var(--accent); }
p { font: 400 44px/1.3 Body, sans-serif; color: var(--ink); margin-top: 40px; }
</style></head><body>
<div class="safe">
  <div class="bar"></div>
  <h1>Open <em>before</em><br>the school run</h1>
  <p>Fresh bread from 7am, Monday to Friday.</p>
</div>
</body></html>
```

The `.safe` box above is the grid-safe zone for a 4:5 canvas (the central square, inset). Keep every word inside it.

## Carousels

Build one HTML file per slide (or one file with a `?slide=N` switch), render each at the same size, and number the files in order (`<slug>-slide-01.png`). The first slide carries the hero headline and has to work alone in the grid; the last slide carries the call to action from `## CTA & contact`. For a LinkedIn document carousel, combine the slides into one PDF at 1080x1350 per page.
