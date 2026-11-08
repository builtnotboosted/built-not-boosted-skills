---
name: brand-setup
description: Interview-led onboarding that builds the marketing workspace every other Built Not Boosted skill reads. Asks short batches of questions (multiple choice where possible), drafts answers from material the user already has (website, bios, past posts), then writes brand/brand-profile.md plus starter voice-learnings, performance-learnings, sources and a reference-images folder. Re-run it to update a single section. Use when someone says "set up my brand", "onboard me", "create my brand profile", "set up the marketing workspace", "start the plugin", "update my brand profile", "change my voice/platforms/compliance section", or when another skill finds no marketing workspace.
---

# Brand setup

This skill creates the marketing workspace and its source of truth, `brand/brand-profile.md`. Every other skill in the pack (`writing`, `research`, `scheduling`, `platform-data`, `video-scripting`, `image-generation`, `video-editing`, `review-loop`, `voice-loop`) reads that file for the brand constants: who you are, who you serve, how you sound, where you post, what you never say and which compliance lines apply. Get it right once and every piece of content starts closer to finished.

It owns the interview, the workspace layout and the profile schema. It does not write content, choose formats or decide strategy beyond what the user tells it.

## Before you start

1. Look for an existing workspace. Default is `marketing/` in the working directory; the user may name another folder.
2. If `marketing/brand/brand-profile.md` already exists, switch to **re-run mode** (below). Never overwrite a filled profile wholesale.
3. Open `references/brand-profile-template.md`. Its headings are the exact schema the other skills read, so the output must keep them word for word.
4. Glance at `references/worked-example.md` if you want to see what a finished profile looks like at the right level of detail.

## The standard

- **Exact headings.** The twelve `##` headings in the template, in that order, spelled exactly. Other skills look them up by name, so a renamed heading is a broken link.
- **Nothing invented.** Every line in the profile is something the user said, confirmed, or approved from a draft. Anything unknown becomes a `TODO:` line, never a plausible guess. Why: a guessed audience or a made-up disclaimer gets copied into hundreds of posts before anyone notices.
- **Compliance wording is theirs.** If the business is regulated, the exact disclaimer text comes from the user, their regulator's published wording, or their compliance contact. You can suggest where to find it; you do not author it. Mark anything unconfirmed `TODO: confirm with compliance`.
- **Small batches.** Three or four questions at a time, so it feels like a chat over coffee rather than a form. Offer multiple-choice options (an AskUserQuestion-style picker where the client supports it) with an "other" escape hatch.
- **Short is fine.** A sharp two-line voice section beats a padded page. Write in the user's spelling locale.

## The method

### 1. Open and offer a head start

Explain in two or three sentences what you're building and that it takes about ten to fifteen minutes (or five for the quick version). Then ask, in one batch:

- Where should the workspace live? (default `marketing/`)
- Full setup or quick setup? Quick covers Identity, Audience, Offer & goal, Voice, Platforms and the regulated yes/no; the rest become TODOs to fill later.
- Is there existing material to draft from? Website URL, About page, LinkedIn or Instagram bio, a few past posts they're proud of, a brand guidelines PDF, a pitch deck.

If they give material, read it (fetch the URL, read the files or pasted text) and pre-draft as many sections as you can. Present drafts as "here's what I picked up from your site, is this right?" rather than asking questions you could have answered yourself. Label drafted lines so the user knows what to check.

### 2. Run the interview in batches

Work through `references/interview-guide.md`, one batch per turn. It has the questions, the multiple-choice options and the follow-ups for each schema section. Skip any question already answered by the material from step 1, and confirm the drafted answer instead.

Keep a running draft as you go. After each batch, reflect back the one or two lines you've written for that section so the user can correct it while it's fresh.

Things worth slowing down for:

- **Voice.** Ask for two or three real posts or messages they wrote themselves and like. Pull the traits from those, not from adjectives they pick off a list. Adjectives describe the voice they want; samples show the voice they have.
- **I or we, per channel.** People connect with a person, not a committee. A "we" post on a personal profile reads like a press release; an "I" post on a joint brand page leaves the partner out. Record the person per platform.
- **Boundaries.** Ask what they never want to be seen talking about, and what claims they never make. Side projects and second businesses often need a firm line so one brand doesn't bleed into another.
- **Compliance.** Ask whether the business is regulated. If yes or unsure, open the regulated-industries guidance in the `writing` skill (`references/regulated-industries-example.md`) to frame the questions about tiers. Ask about affiliate links and testimonials even for unregulated businesses, because advertising rules apply to everyone.
- **Likeness.** If the user wants to appear in generated images, ask for three to six real photos (clear face, natural light, current look, at least one in colour) and copy them into `brand/reference-images/`. These are for likeness reference only and are never posted directly. Ask about consent for anyone else pictured.

### 3. Write the workspace

Create this structure (skip folders that exist):

```
marketing/
  brand/brand-profile.md
  brand/voice-learnings.md
  brand/performance-learnings.md
  brand/sources.md
  brand/reference-images/
  content/
  baselines/
  data/
```

- `brand-profile.md`: from the template, filled with the confirmed answers, template comments removed, `TODO:` lines kept for gaps. Add a `Last updated: YYYY-MM-DD` line under the title.
- `voice-learnings.md`, `performance-learnings.md`, `sources.md`: empty but structured, using each owning skill's template (`voice-loop`, `platform-data`, `research`) so the headings match what those skills expect. `references/workspace-files.md` says which template to use and has fallbacks if those skills aren't installed. Seed `voice-learnings.md` with the voice samples the user gave (quoted verbatim, dated) because those are the first real evidence of how they write.
- `reference-images/`: the photos, plus a short `README.md` listing each file, what it shows and any rules (for example "colour photo, best for hair and skin tone").

### 4. Read it back

Show the user a compact summary: one line per section, plus the list of TODOs. Ask them to skim the profile itself. Offer the obvious next step (usually "want me to write your first post with the `writing` skill?").

### Re-run mode (updating one section)

When a profile already exists:

1. Read it and list the twelve sections with a one-line status each (filled, thin, or TODO).
2. Ask which section to update, or offer to work through the TODOs.
3. Run only that section's batch from the interview guide, showing the current text first so the user edits rather than starts again.
4. Replace only that section. Leave every other section byte for byte as it was. Update the `Last updated` line.
5. If the change affects other skills' behaviour (a new platform, a new disclaimer tier, a dropped boundary), say so in one line, for example "new platform added, so `scheduling` will need its posting route".

If the profile is missing headings or uses old names, offer to migrate it to the current schema, keeping all existing content under the right headings.

## When another skill finds no workspace

Other skills say so in one line and offer to run this. If the user wants to carry on without it, those skills ask only the essentials (business, audience, platform, voice in a sentence, regulated or not) and suggest running `brand-setup` afterwards so the next piece doesn't repeat the questions.

## Checks before it ships

Before handing over, check:

- All twelve headings present, exact spelling, in order.
- No invented facts: every line traces to something the user said, confirmed or approved.
- Compliance wording is either confirmed or marked `TODO: confirm with compliance`.
- Platforms table complete for each listed platform (handle, voice, route, links allowed).
- Content pillar percentages add up to roughly 100.
- Reference images copied and listed, consent noted for anyone else in them.
- No em dashes, and the user's spelling locale throughout.

For a profile that will drive regulated content, run it through the `review-loop` skill before the first post goes out.

## Adapting it

- **Agencies or multi-brand users:** one workspace per brand. Keep brands apart; a shared profile is how one brand's claims end up on another's posts.
- **Couples and partnerships:** record both people in Identity and set I/we per channel in Platforms.
- **Very small or brand-new businesses:** quick setup, then revisit Content pillars and Visual identity after a month of posting, when `platform-data` has something to say.
- **Translating:** set the spelling locale and language in Voice; every skill writes in it.

## Learn more

A longer walkthrough, with examples for different kinds of business, lives at https://builtnotboosted.com/skills/brand-setup
