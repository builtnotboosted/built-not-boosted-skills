# Likeness lock

For any image that shows a real person (the business owner, a team member, a presenter). The goal: someone who knows them looks at the image and says "that's them", not "who's that?".

The single most common failure is the model **flattering** the person: younger, slimmer, a thicker head of hair, smoother skin, a generic face. It is an automatic reject, however good the rest of the image is. People notice instantly, and an audience that knows the person reads it as fake.

## Inputs

- Reference photos live in `brand/reference-images/` (paths listed under `## Likeness` in the brand profile, with any rules the person set: clothing they never wear, glasses, a hat or no hat).
- The best edit base is a **clean, front-facing headshot** in good light, with their real glasses if they wear them.
- Use at least one **colour** photo to judge hair, beard and skin tone. A black-and-white photo is good for face shape but hides colour, which is exactly where models drift.
- Note any photo that throws the model (a hat, sunglasses, a strong tilt, heavy filters) in the profile so it is never used as a base.

## Method

1. **Edit from a real photo, do not describe the person.** Pass the headshot as the base (or the first reference) and describe the scene around it. A text-only description of a person produces a stranger.
2. **Feed identity as tight face crops.** Two or three crops of the head and shoulders from different photos. Whole scene selfies leak their backgrounds, rotation and lighting into the new image.
3. **Rotate phone photos upright** before using them; sideways EXIF orientation confuses some tools.
4. **Spell out the rubric in the prompt** (below), with the person's real features, so the model has words to hold on to.
5. **Ask for a warm, genuine expression** suited to the post: a friendly half-smile, eyes to camera, by default. Flat, stern or vacant faces read as cold.
6. **Keep their real clothing style** from the profile (for example "open collar, no tie, never a suit"). Wardrobe is part of recognisability.

## The rubric (check every item on the filed file)

Write one line per item from the person's real photos when you set up the brand profile, then check each against a provided colour photo, never against another AI image:

| Item | Example of a real rubric line |
|---|---|
| Hair colour | dark brown on top, grey at the temples (not fully grey, not jet black) |
| Hair style and line | short, tapered at the sides, receding at the temples |
| Facial hair | short salt-and-pepper beard |
| Face shape and build | fuller, rounder face; heavier build |
| Glasses | round thin-metal frames |
| Age | looks their real age |
| Skin | real texture, not airbrushed |

If any item is off, or you are not sure, it is a **fail**. "Looks like a plausible person of that age" is not the bar.

## Retry budget, then fall back

About three or four honest, reference-anchored re-rolls. Then:

1. Rebuild the piece as a **faceless scene**: the metaphor or setting plus the baked headline, no face needed. A good faceless image always beats a face that is not them.
2. If even that will not come clean, **hold** the piece and say what failed.

Never ship a stand-in face to fill a slot.

## Never post the reference photos

The reference photos are identity inputs. Do not crop them into an image, use them as a background or post them directly. If the person wants a real photo posted, that is a photo post, not a generated image, and it is their choice.

## Filmed video is easier

If the person has filmed the video the image is for, build the cover from a real frame instead (`scripts/cover_from_frame.py`). No likeness risk at all.

## Consent

Only generate likenesses of people who have agreed to it and whose photos are in `brand/reference-images/` for that purpose. Never generate a recognisable image of a client, a customer or a member of the public.
