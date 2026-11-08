# Prompting and aspect-ratio control

Model-agnostic first, with Google's Gemini image models ("Nano Banana") as the worked example. Last checked: Nov 2026, verify before relying on it: image models and the tools that wrap them change quickly.

## Two moves usually beat one

1. **Scene first, no text.** Get the scene, the light, the framing and (if there is one) the person right. Reserve a darker, emptier zone inside the grid-safe square for the headline. Judge the face now, before anything else is locked in.
2. **Bake the text in with an edit pass.** Edit that scene so the model renders the headline and subhead into the reserved zone as part of the picture.

Why two moves: a likeness or composition problem found after the text is in means re-rolling the text too, and some tools do not preserve aspect on an edit. A one-shot prompt is fine for faceless scenes once you know the model behaves.

## A prompt that works

Structure it in this order, in plain sentences:

1. **Format and shape.** "A tall vertical 4:5 photograph that fills the whole frame edge to edge, no borders."
2. **Scene and action.** Who is doing what, where, and the one prop or metaphor that carries the message.
3. **Light and colour.** "Natural, realistic colour, soft window light, deep charcoal shadows. The brand accent (#hex) appears only as [the headline word / a rim light / a small prop]." Never ask for a full-frame colour wash.
4. **Reserved zone.** "Keep the upper-left third dark and uncluttered for a headline; keep the bottom eighth clear."
5. **The text, exactly.** "Render the headline in huge, bold, condensed white capitals, poster scale, filling the reserved zone, on two lines: 'OPEN BEFORE' / 'THE SCHOOL RUN'. The word 'OPEN' is in [accent colour] with a thick underline in the same colour. Below it, one short line in smaller white capitals: 'FROM 7AM, MONDAY TO FRIDAY'." Quote every word. Say the line breaks.
6. **What not to do.** "No other text, no logos, no watermark, no borders."

Garble guards: keep the subhead on one line (wraps duplicate words), keep the headline to five words or fewer where possible, never ask for small fixed text such as a name or web address (stamp it afterwards if you need it), and check spelling on the filed file every time.

## Getting the aspect ratio you asked for

The shape of the output is often **not** controlled by the words in the prompt. How it is controlled depends on the tool:

- **The tool has an aspect-ratio setting.** Use it. The Gemini API's image generation accepts an aspect-ratio setting in its image config (1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9 and 21:9 at the time of checking), and the newer Gemini 3 Pro Image model also offers higher output resolutions. Many other models have an equivalent.
- **The tool only takes a prompt.** Many MCP wrappers expose a text-only `generate_image` that always returns a square (for example 1024x1024) however hard the prompt says "vertical". Do not use it for non-square shapes.
- **The tool edits an input image.** An `edit_image` call usually keeps roughly the aspect of the **base** image you pass. That is the lever.

### The scaffold recipe (for edit-based tools)

1. Make a plain canvas at the exact target ratio: `python3 scripts/aspect_scaffold.py 1080x1350 scaffold.png --colour "#1a1a1a"`. This is an input the model repaints completely, not padding on a finished image, so it does not break the "never bodge the shape in code" rule.
2. Call the edit tool with the scaffold as the base image and a prompt that starts: "Paint a complete photograph that fills this entire tall vertical frame edge to edge. Keep its 4:5 proportions. No borders or letterboxing." Then the scene and the text as above.
3. **Do not pass a square reference image** in the same call: a square reference tends to snap the output back to square. Feed identity references as separate edits on the scene, or crop them to the target ratio first.
4. Avoid very heavy "ignore the base and recreate everything" wording; it can also snap to square.
5. Check the real output size (`python3 scripts/check_image.py out.png`). The model returns its own resolution near the base ratio (for 4:5, something like 896x1152); a light cover-crop and resize to the exact target is fine. If it came back square, lighten the prompt and re-roll.
6. After that, only light touch-ups (a gentle contrast or brightness pass). Another heavy repaint can snap the shape.

Landscape (16:9) usually comes out natively from scene prompts, so long-form covers rarely need a scaffold. Tall portrait (3:4, 4:5, 9:16) is where the fight is.

### When it still will not come out the right shape

Re-roll with the scaffold and a lighter prompt. If a wide image has a perfect face and you need it taller, a seamless outpaint (extend the canvas and have the model fill the new area) is a last resort; re-check likeness and text after. Never cover-crop a wide frame down to portrait if that slices the headline or the face, and never pad. After a few honest attempts, say so and offer a square or a different format instead.

## Worked example: Gemini image through an MCP server

A typical "nano-banana" style MCP server exposes `generate_image` (prompt only), `edit_image` (base image path, prompt, optional reference images) and `continue_editing`.

- Text-only `generate_image` returns a square. Use it only for 1:1 pieces.
- `edit_image` follows the base image's aspect. Use the scaffold recipe for 4:5, 3:4 and 9:16.
- Downscale large reference photos (about 1024 px on the long side) before passing them; huge phone photos slow calls and sometimes fail.
- The server saves outputs to its own folder. Find the newest file with a glob rather than hard-coding a session path.
- "No edited image was generated" is usually transient. Retry once or twice before changing the prompt.
- Face edits can be refused or drift on a heavily composed image. Get the face right on the plain scene (move 1) before the text goes on.
- An edit on a finished landscape thumbnail sometimes returns a different shape. Fix faces before the shape and text are locked, not after.

## Re-roll discipline

A re-roll is a brand-new image. Re-run every check on the new file. Keep the prompt that finally worked in the piece folder (`images/prompts.md`), with one line on what the failed attempts got wrong, so next time starts closer.
