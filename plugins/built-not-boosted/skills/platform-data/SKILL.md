---
name: platform-data
description: Pulls and reads social and web analytics, writes a weekly performance review, and keeps a living log of what actually works per platform, with the evidence and a confidence level for every lesson. Recommends formats, posting times and topics for the next plan. Works with native exports (Meta Business Suite, LinkedIn, YouTube Studio, TikTok Studio), Google Search Console, GA4, or a scheduler's analytics such as Publer. Use when someone asks how their posts are doing, what is working, which post did best, when to post, why reach dropped, to run the weekly review, read an analytics export, compare formats or platforms, set up a posting-time test, or update their performance learnings. Trigger phrases include "weekly review", "how did this week go", "what's working", "best time to post", "pull my analytics" and "read this export".
---

# Platform data

This skill turns platform numbers into decisions. It pulls or reads analytics, saves a dated snapshot to `data/`, reads it honestly, writes a weekly review, and updates `brand/performance-learnings.md` so the whole workspace learns from what really happened rather than from hunches or generic advice. Its recommendations (format, timing, topics) feed planning in the `scheduling`, `research` and `writing` skills. It does not schedule anything, and it never changes the brand profile on its own; it proposes, and the person decides.

Authority order: `brand/brand-profile.md` wins on brand constants and goals; this skill owns the measurement method. Within the learnings file, a lesson marked as a rule outranks generic platform advice, because it is evidence from this audience.

## Before you start

Read from the marketing workspace (default `marketing/`):

- `brand/brand-profile.md`: `## Platforms` (which accounts count), `## Offer & goal` (what an enquiry or sale looks like, which is the real success measure) and `## Tools` (which analytics sources are connected).
- `brand/performance-learnings.md`: the current rules, patterns and watch-items. If it does not exist, create it from `references/learning-log.md`.
- The last weekly review in `data/reviews/`, so this week is read against last week.
- The `content/` folders for the period, especially each `PACKAGE.md`, to know each post's format, pillar, hook type and slot. Numbers mean little until you can join them to what the post was.

If there is no workspace, say so in one line and offer to run `brand-setup`. If the person just wants a quick read of one export, do it, and offer to set up the workspace so the lesson is kept.

## The standard: read it honestly

Most bad decisions from analytics come from reading noise as signal. These rules exist because each one has caught a real mistake.

1. **Every figure travels with its denominator, window and source.** "4.5% engagement" means nothing without "on 598 reach, TikTok, 28 days to 21 Jul, from the Publer pull". Never quote an engagement rate without its reach.
2. **Respect the reach floor.** Engagement rate is unreadable on tiny reach: below roughly 50 reach, one interaction is worth several percentage points, and it is often your own first comment. Rank by reach; read engagement rate only above the floor. *Why: a leaderboard of "best engagement" once turned out to be ten posts with reach under 35, each scored by the account's own comment.*
3. **Absent is unmeasured, not zero.** Pulls vary in completeness night to night and platform to platform. A platform missing from a board, or a sudden jump between two pulls, is a coverage change until proven otherwise. Note coverage in every snapshot.
4. **Medians, not means, and name the outlier.** One breakout post can be half a year's views. Report it separately, then read the rest by median.
5. **Reach and engagement come from different posts.** The pieces that reach new people (warnings, news, broad explainers) are rarely the ones that start conversations (questions, honest personal posts, community). Judge each piece on the job it was cast for, and plan both.
6. **Score each format on its job.** Video out-reaches still images several times over on most platforms, so judge stills on saves, comments, shares and profile taps, not reach.
7. **Compare like with like.** Same window length, same platforms, similar post age. A post published yesterday has not finished accumulating; some keep growing for weeks.
8. **Engagement is not an enquiry.** Track the goal in `## Offer & goal` (enquiries, bookings, sales, sign-ups, link clicks) separately, and say plainly when there is no attribution yet.
9. **Best-time heatmaps describe your posts, not your audience.** A scheduler's "best time" grid shows when your past posts happened to do well; one viral post can make its slot look magic. Cross-check with the platform's own "when your followers are online" data, and treat a best-time as a hypothesis to test.
10. **One window is a watch-item, not a rule.** Promotion to a rule needs repetition (see below).

## The method

1. **Pull the data.** Open `references/data-sources.md` for what each source gives and how to get it: native exports, Search Console, GA4, and a scheduler's analytics (Publer is the worked example). Use one owner per source: pull once, save it, and have every other step read the saved copy.

2. **Save a snapshot to `data/`.** Name it `data/<yyyy-mm-dd>-<source>-<scope>.<ext>` (for example `data/2026-11-08-publer-28d.md`). Stamp the top with when it was pulled, the window, the accounts covered, anything missing, and whether it is partial. Keep raw exports as they came; never edit a snapshot after saving it.

3. **Join numbers to content.** Match each post to its content folder and tag it with platform, format, pillar, hook type, slot and age. This is what lets you say "question-led posts" rather than "that one post".

4. **Read the boards.** In this order: the reach board (top posts by reach, all platforms); the engagement board (rates above the floor); the active signals (saves, shares, sends, comments: see `references/metrics-glossary.md` for how each platform weights them); followers and growth; the real goal (enquiries, clicks, sales); search (Search Console, platform search terms). Note outliers, coverage gaps and anything still climbing.

5. **Compare against the learnings.** For each rule, pattern and watch-item in `brand/performance-learnings.md`: does this week confirm it, contradict it, or say nothing? Contradictions matter most; write them down even when inconvenient.

6. **Update `brand/performance-learnings.md`.** Add new observations as watch-items, strengthen or weaken existing ones, and propose promotions or retirements, using the format and promotion rules in `references/learning-log.md`. Every entry carries its evidence and a confidence level.

7. **Make recommendations for planning.** Three kinds, each tied to evidence: **format** (what to make more or less of, per platform), **timing** (slots to keep, test or drop), and **topics** (seams that are working, gaps that search or comments show). Include the **weekly pick**: the strongest few candidate pieces for each platform next week, ranked by the platform's own evidence, so each platform gets its best piece rather than the same piece everywhere. Recommendations that would change `## Platforms`, `## Content pillars` or posting rhythm are proposals for the person, not changes.

8. **Write the weekly review.** Use `references/weekly-review-template.md`; save it as `data/reviews/<yyyy-mm-dd>-weekly-review.md` and give a five-line summary in chat. Keep it short enough to actually read on a Monday morning.

## Running a test

When a question can only be answered by trying (does posting later help, does a carousel beat a reel for this topic), set up a proper test rather than reading tea leaves:

- Change **one variable**, keep everything else the same, and keep a control arm (the current way).
- **Rotate the arms** across days so the variable is not confounded with weekday (for example arm = (week number + weekday number) mod number of arms).
- Run it for **four to six weeks**, log each tested post to `data/tests/<test-name>.md`, and read the result by **median** first-hour and final figures per arm.
- Decide in advance what result would change the plan, and when the test ends if nobody renews it.

Posting time is a multiplier on content, never a substitute for it: completion and relevance dominate, so do not expect a slot change to rescue weak pieces.

## Platform behaviour changes fast

How each platform currently weights saves, shares, comments and watch time, link penalties, weekly caps and test windows are in `references/platform-signals.md`. It is labelled with when it was last checked. When a recommendation depends on one of those facts, verify it live (the platform's own help or creator pages) before relying on it.

## Checks before it ships

- Every figure in the review has its denominator, window and source.
- Engagement rates are only quoted above the reach floor, and outliers are named separately.
- Coverage gaps are stated, and no platform is called "down" just because it is missing.
- Every new or changed learning has evidence and a confidence level; nothing is promoted to a rule without meeting the promotion bar and the person's sign-off.
- Recommendations are labelled as tested evidence, pattern, or hypothesis.

Pieces planned from these recommendations still go through `review-loop` in the usual way.

## Adapting it

- **Your goal:** if the business sells online, conversions and revenue lead the review; if it is a local service, enquiries, calls and direction requests do. Set this in `## Offer & goal`.
- **Your floor:** 50 reach is a sensible default for small accounts. Raise it as the account grows (a useful rule of thumb is ten times the number of interactions you usually leave yourself).
- **Your sources:** start with whatever you already have (native exports are free). Add a scheduler's analytics or an API connector when the manual export becomes a chore.
- **Your cadence:** weekly is right for most. Monthly is fine for a slow posting rhythm; Search Console and long-form video are best read monthly anyway.

## Learn more

A longer guide with examples lives at https://builtnotboosted.com/skills/platform-data
