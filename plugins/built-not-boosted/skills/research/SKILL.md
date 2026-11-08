---
name: research
description: Finds and checks topics, stories, facts and figures for content, then hands over a sourced research brief that the writing and video-scripting skills build from. Use when someone asks what to post about, wants ideas or angles, asks to research a topic, check a fact or statistic, find out what their audience is searching for or asking, react to news or a data release in their industry, plan around a calendar of announcements, or build or tidy their list of trusted sources. Trigger phrases include "research this", "what should I post this week", "find me a story", "is this stat right", "what are people searching for", "react to today's news", "content ideas for", "fact-check this post" and "update my sources". Every claim it returns carries a named source and a date, and it never invents a figure, quote, review or story.
---

# Research

This skill finds things worth saying and proves they are true. It owns two jobs: choosing topics and angles the audience actually wants, and sourcing every fact that goes into a piece. Its output is a **research brief** that the `writing` and `video-scripting` skills consume, and it keeps the workspace's trusted-source list, `brand/sources.md`, in good order. It does not write the finished post (that is `writing`), script the video (`video-scripting`) or check the final piece (`review-loop`).

Authority order: `brand/brand-profile.md` wins on brand constants, boundaries and compliance wording; this skill owns the research method.

## Before you start

Read these from the marketing workspace (default `marketing/`):

- `brand/brand-profile.md`: `## Audience`, `## Content pillars`, `## Boundaries`, `## Compliance` and `## Platforms`. Audience and pillars tell you what to look for; boundaries and compliance tell you what never to bring back.
- `brand/sources.md`: the tiered list of sources this business trusts. If it does not exist, create it from the template in `references/source-tiering.md` and fill it as you go.
- `brand/performance-learnings.md` (if present): which topics and formats have worked. Research should lean toward proven seams and flag untested ones as tests.
- Recent `content/` folders: what has already been made, so you find gaps rather than repeats.

If there is no workspace, say so in one line and offer to run `brand-setup`. If the person wants to carry on anyway, ask only for the audience, the industry and the location (if local), and proceed.

## The standard: nothing invented, everything dated

This is the rule the whole skill exists to protect. A piece that is slightly less dramatic but true always beats a punchy one that is made up, because trust is the asset and one fabricated detail can spend all of it.

1. **Never invent a figure, quote, review, testimonial, story or named detail.** No made-up statistics, prices, averages or "9 in 10 people" claims. No imagined customer anecdotes presented as real. No invented product, person, place or event stated as fact.
2. **Stories come only from real material.** Use the person's own documented experiences (ask them; they are the only source for "a customer of mine once...") or published case studies from a named source. Reduce a real case to its anonymised shape and keep to what actually happened. Never add specifics to dramatise it. If no real story fits, teach the topic truthfully instead. *Why: an invented "real customer story" is the fastest way to lose an audience that trusts you, and in regulated industries it can also be a breach.*
3. **Every claim gets a source and a date.** The source is named specifically (publisher, title or release, and URL where there is one) and the date is both when it was published and when you checked it. Claims without a source do not go in the brief; they go in its open questions.
4. **Live figures carry a `VERIFY BEFORE PUBLISH` flag.** Any number that can move (prices, rates, averages, counts, rankings, policy thresholds, platform limits) is flagged so that whoever publishes re-checks it on the day.
5. **No vague quantifiers that imply data.** "Most people", "statistically", "studies show" and "nearly everyone" are either backed by a cited source or rewritten.
6. **When unsure, do not guess.** Leave it out and teach generally, or stop and ask the person. Say plainly what you could not verify.

## Evergreen or live: decide first

Every piece is one of three kinds, and the brief says which, because it changes what may go in it.

- **Evergreen:** true for months. Safe to batch, film ahead or schedule weeks out. Carries **no live figures at all**; use principles, processes and illustrative examples clearly labelled as illustrative.
- **Live:** built around something current (a figure, a release, a rule change, today's news). Every current figure is flagged `VERIFY BEFORE PUBLISH` and the brief records an expiry date after which the piece must not go out unrevised.
- **Dated:** evergreen in shape but tied to a known date (a deadline, a season, a scheme opening). Record the "use by" date so it does not lapse unplaced or go out stale.

*Why: a pre-filmed video quoting last month's number is wrong the day it airs, and nobody notices until a viewer does.*

## The method

1. **Frame the ask.** Is the person handing you a topic to research, or asking what to make? For a topic, go to step 3. For "what should I post", start at step 2. Note the platforms and the date the piece will go out, because that decides evergreen or live.

2. **Find the demand.** Work out what the audience is actually asking, in their own words, before deciding what to say. Open `references/audience-demand.md` for the methods: search suggestions and "People also ask", the person's own Search Console queries, platform search insights, forums and community threads, and the questions sitting in their own comments and DMs. Pillars set the kind of post; demand sets the angle and the exact words. Prefer topics that are:
   - a concrete problem most people do not know about until it bites (the warning or "gotcha" shape)
   - a "what actually happens when..." walkthrough of a moment people worry about
   - a clear either/or decision the viewer is facing
   - a question already being typed into a search bar, which you can use almost verbatim as the title
   Check each candidate against `brand/performance-learnings.md` and against what has already been made. Mark untested seams as tests, not certainties.

3. **Gather from tiered sources.** Use `brand/sources.md` and the tiering method in `references/source-tiering.md`. Go to the primary source for anything that will carry a number (the statistics body, the regulator, the original study), and treat trade press, blogs and commentators as radar that points you to it. Note who is behind each source and what they want, because partisan and commercial sources still have good data but come with a slant.

4. **Verify.** For every claim:
   - trace a headline figure back to its primary source and read it there
   - check the publication date and whether it has been superseded (official guidance pages can look current and be years out of date)
   - check the sample: who was surveyed, how many, and whether the panel is skewed (a survey of one company's own customers is not "all customers")
   - check that the figure means what the headline says it means; some figures mislead once stripped of their context, and those stay out
   - if a page will not load properly (client-rendered sites often come back empty), try the site's RSS feed, sitemap or a direct document link before giving up, and never fill the gap from memory
   If you cannot verify it, it does not go in as fact.

5. **Find the angle.** Translate the facts into what they mean for the person watching. For news and data, hook on the stakes and the freshness, give the number once, then turn straight to "what this means for you", split by the two or three types of people in the audience. Keep the tension in the fact, never in a promised outcome ("this clause could cost you" is fine when true; "you will save" is not). Offer two or three hook seeds; the `writing` and `video-scripting` skills choose and polish.

6. **Write the brief.** Use `references/research-brief-template.md` and save it to `content/<yyyy-mm-dd>-<slug>/research-brief.md`. The claims table is the heart of it: one row per claim, with source, dates and flags. If the person only wanted a quick fact-check, give the answer in chat with the source and date, and offer to file a brief.

7. **Update `brand/sources.md`.** Add any new source you leaned on, with its tier, what it is good for, any slant or caveat, and fetch notes. Demote a source that turned out stale or unreliable, and say why in one line.

## Reacting to news and scheduled releases

When something happens in the industry, or a known data release is due, open `references/reactive-content.md`. In short: keep a calendar of the scheduled releases and announcements that matter to this audience, leave a deliberate gap in the plan on those days, prepare the angle in advance, then verify the actual figure on the day and turn it round fast. Simple numeric releases reward speed; complex policy changes reward reading the primary document first, because "first and wrong" is worse than "a few hours later and right".

## Regulated industries

If `## Compliance` says the business is regulated, the sourcing bar is higher and some claims are not allowed at all, however well sourced. Follow the brand profile's compliance lines. `references/regulated-industries-example.md` shows how this works in one industry (UK financial services) as a worked example, not as the default.

## Checks before it ships

Before handing the brief on, confirm:

- every row in the claims table has a named source, a published date and a checked date
- every live figure is flagged `VERIFY BEFORE PUBLISH`, and the brief says evergreen, live or dated (with expiry)
- no story, quote or review appears that the person has not supplied or a named source has not published
- nothing touches a topic in `## Boundaries`
- the sources list at the end is complete enough that someone else could check every claim

The finished piece goes through the `review-loop` skill, which re-checks the claims against this brief. Keep the brief with the content so it can.

## Adapting it

- **Your sources:** the tiers are a method; `brand/sources.md` is where your industry's names go. A café's tier 1 might be the local council and the food standards body; a coach's might be peer-reviewed research and the professional body.
- **Your release calendar:** list the dates that move your audience (industry reports, official statistics, seasonal peaks, trade shows, policy deadlines) in `brand/sources.md` under the calendar heading.
- **Your demand tools:** start free (search suggestions, your own comments, Search Console). Paid keyword tools are optional; one worked example is in `references/audience-demand.md`.
- **Your appetite for reactive work:** if filming on the day is unrealistic, keep the reactive lane to quick posts and let the weekly round-up carry the rest.

## Learn more

A longer guide with examples lives at https://builtnotboosted.com/skills/research
