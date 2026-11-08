---
name: scheduling
description: Gets finished posts into a social media scheduler (or posted by hand) safely. Queue-only with explicit timezone offsets, live dedup against scheduled and already-published posts, media readiness checks, correct post types (shorts, reels, carousels, first comments, manual-posting reminders), alt text, a link gate that sends copy back for a rewrite rather than stripping it, and confirmation before anything goes live. Writes and keeps a scheduling manifest for each pack. Works with any scheduler; Publer is the worked example. Use when someone says "schedule this", "queue these posts", "put this in Publer", "book in this week's content", "post this on Tuesday at 7", "move that post", "what's already scheduled", or hands over a finished content pack to go out.
---

# Scheduling

This skill owns the last mile: taking finished, reviewed posts and putting them in the queue at the right time, on the right account, in the right shape, exactly once. It owns the *how* of scheduling. It does not write copy (the `writing` skill does), choose images (`image-generation`), or read performance (`platform-data`). It decides nothing about *what* goes out; the content pack and the person decide that.

The whole skill rests on one idea: **a missed post can be caught tomorrow, a wrong or duplicate post goes live and cannot be taken back.** So when in doubt, it holds and asks rather than guessing.

## Before you start

1. Find the marketing workspace (default `marketing/`). If there is none, say so in one line and offer to run `brand-setup`; you can still schedule with the essentials (accounts, timezone, times) asked for directly.
2. Read `brand/brand-profile.md`, especially `## Platforms` (handles, posting route manual or scheduler, links allowed?), `## Tools` (which scheduler), `## Compliance` and `## CTA & contact`. Brand-profile wins on brand constants and compliance wording; this skill owns the method.
3. Read the pack: `content/<yyyy-mm-dd>-<slug>/PACKAGE.md` and any existing `SCHEDULE.md` in it.
4. Know the timezone. Use the one in brand-profile (or the person's location). If you cannot tell, ask once; never assume UTC.
5. Check which scheduler tools are actually connected this session. If none, use the browser route (below) or hand over a posting checklist.

## The standard (never break these)

1. **Queue only.** Every post is created as *scheduled* for a planned future time. Never call a publish-now path unless the person explicitly says "post it now" for that specific post. Why: publish-now skips every safety net, and a slip is public within seconds.
2. **Explicit timezone offset on every time.** Write times as ISO with an offset, e.g. `2026-11-12T18:00:00+00:00` in UK winter, `+01:00` in UK summer. Check daylight saving for the *post's* date, not today's. Why: a bare time gets read as UTC or the server's zone, and posts land an hour out around the clock change.
3. **Dedup live, every run, against scheduled AND published.** Before creating anything, read what is already queued *and* what has already gone out on that account. Why: a piece that went live yesterday no longer shows as "scheduled", so a scheduled-only check sees nothing and posts it again.
4. **Fail closed.** An empty, short, errored or obviously partial read is not proof a post is absent. Re-read narrower (one account, one day); if it still cannot be trusted, hold the post and say so.
5. **Never blind-retry.** If a create or upload call times out or hangs, read back what actually landed before trying again.
6. **Verify after creating.** Read each post back and confirm it exists with the right time, account, type flags and media. A success message is not proof; some tools return success and store nothing.
7. **Confirm before anything goes live.** Show the person the plan (the manifest table) and get a yes before creating posts, unless they have already approved this exact plan or set up a standing rule in brand-profile.

## The method

1. **Build the manifest.** One row per post per platform, in `content/<yyyy-mm-dd>-<slug>/SCHEDULE.md`, using `references/schedule-manifest-template.md`. Each row: platform, account, post type, time with offset, caption file, media files, alt text, first comment, link status, state. This is both the plan you show and the record of what you did.
2. **Place the times.** Use the times the pack or person gave. If none, use the posting rhythm in brand-profile, then best-time data from `brand/performance-learnings.md` or the scheduler. Platforms do not have to carry the same piece on the same day; each can run its own week. Place flexible pieces deterministically (same inputs, same slot) so a re-run lands them in the same place.
3. **Run the link gate** on every caption and comment (see below).
4. **Check media readiness.** Every post with media needs its file to exist, be the right shape for the platform (see `references/platform-posting-notes.md`), and be fetchable by the scheduler. Treat a successful upload into the scheduler as the real readiness test. Upload one file at a time if the tool queues imports, and wait for each to finish. No post ever goes out without its media; hold it instead.
5. **Attach alt text** to every image and carousel slide, from the pack. If the pack has none, write a plain description of what is in the image (not the caption again) and note it in the manifest. Why: screen-reader users are part of the audience, and some platforms use alt text for search.
6. **Check paragraph spacing.** Captions carry real blank lines between paragraphs. Some schedulers store captions as HTML paragraphs that render with no gap, so a nicely spaced caption arrives as one wall of text. On first use of a tool, preview one post; if paragraphs collapse, insert the tool's spacer (an empty paragraph or line) between blocks.
7. **Dedup** (standard 3 and 4). Check the manifest states of this pack and any recent packs first (a record you wrote beats a single live read), then read the scheduler: scheduled, and published, for each target account, one day at a time. Match on platform + account + caption opening (+ date for time-specific posts). If the manifest says done but the live read cannot find it, do not recreate; investigate and flag.
8. **Show the plan and get a yes.**
9. **Create each post** with the right type (below), the verbatim caption, media, alt text and first comment.
10. **Verify** each one (standard 6) and write the state and the scheduler's post reference into the manifest.
11. **Report** in a short table: what was queued, what was held and why, anything that needs the person's hand (manual posts, pinned comments).

## Post types

- **Short-form video** (YouTube Shorts, Instagram Reels, TikTok, Facebook Reels): mark the type explicitly; many schedulers default a video to a plain feed video, and an unflagged Reel or Short loses its reach lane. YouTube Shorts need a title. Confirm the flag persisted when you verify.
- **Carousels:** attach slides in order, alt text per slide. LinkedIn carousels are usually a PDF document post. Check whether the tool can mix video and images in one carousel before planning one.
- **First comments:** used where links or hashtags belong in a comment. Verify the comment actually saved; on some tools and platforms it silently drops. First comments often cannot be edited later, so get them right before creating.
- **Manual-posting reminders:** some accounts cannot be auto-published by any third-party tool, personal Facebook profiles being the common one. Create a reminder or notification post if the tool supports it, or add a row to the manual list in the report, with the caption and media ready to paste.
- **Pinned comments and anything the tool cannot do** (for example, YouTube pinned comments): list them in the report as hand jobs, with the exact text.
- **Local business listings** (such as Google Business Profile): usually one button per post, with a dedicated business page link, never a link shortener or link-in-bio page. Details in `references/platform-posting-notes.md`.

## The link gate (a backstop, not an editor)

Links behave differently by platform and change often (see `references/platform-posting-notes.md`). Brand-profile `## Platforms` says where links are allowed. For each post:

1. Scan caption and comments for anything link-shaped: `http`, `www.`, `.com/`, `.co.uk/`, shorteners, link-in-bio services. Also scan for comment-keyword asks ("Comment GUIDE and I'll send it"), which most platforms now demote as engagement bait.
2. **Allowed** (the platform and the post's purpose permit it): schedule as is.
3. **Looks like it should be allowed but is not marked** (a booking link on an event post, a link to a new article): hold and ask. Removing the link would make the post pointless.
4. **Not allowed:** do not strip the link and post. A post written around a link reads broken without it. Send it back to the `writing` skill for a link-free rewrite (point to the profile, name the piece, end on a genuine question), have the rewrite checked by `review-loop`, write the new copy back into the pack so pack and live post match, then schedule.
5. **No time to rewrite and review before the slot:** hold and flag. A missed slot beats a broken post.

If brand-profile sets a link budget (for example a monthly cap on Facebook link posts), count against it in the report and treat an over-budget post as "not allowed".

## Editing and moving posts

- **Prefer delete-and-recreate over editing a scheduled time in place** when the tool is flaky about edits (many are: times shift, media detaches, flags reset). Delete first, then recreate, then verify. Some platforms refuse two posts in the same minute on one account, so leave the old one gone before the new one goes in. Some tools block an identical caption for a few minutes after a delete; use the tool's "allow duplicate" option only for a deliberate recreate.
- Adding media to a text-only scheduled post, changing a first comment, or adding a listing button usually needs delete-and-recreate too.
- Move only what the person asked to move. Never delete a post you did not create without asking; never delete reminder posts.

## No scheduler? Post via the platform in a browser

If no scheduler is connected but a browser tool is (for example Claude in Chrome), you can use the platform's own composer. Most platforms have a native "schedule" option in the post composer (Meta Business Suite for Facebook and Instagram, LinkedIn's clock icon, YouTube Studio, TikTok's web uploader). The same rules apply: schedule rather than post now, check the timezone the platform shows, attach alt text, and take a screenshot of the confirmation for the manifest. Stop and hand over if a login, two-factor prompt or payment screen appears; those are the person's to handle. If no browser tool is available either, produce a posting checklist from the manifest so the person can do it in a few minutes.

## Checks before it ships

Before step 8 (showing the plan), run the manifest past `review-loop` or check it yourself: every row has a time with offset in the future, the right account, a post type, media present and fetchable, alt text, link status resolved, dedup done, caption matches the pack verbatim, and compliance lines from brand-profile are present where required.

## Adapting it

- **Your scheduler:** put it in brand-profile `## Tools`. For Publer, read `references/publer.md`. For any other tool, learn its quirks on a throwaway draft first and note them in your workspace (a short `brand/tools-notes.md` works).
- **Your rhythm:** posting days and times live in brand-profile, and `platform-data` refines them from your own results.
- **Unattended runs:** if scheduling runs on a timer with no one watching, keep the confirmation rule by approving a standing plan in brand-profile, and lean harder on fail-closed holds. Some tools require an in-chat yes for deletes; that is a feature, keep deletes for attended sessions.

## References

- `references/schedule-manifest-template.md`: the manifest format. Open when building or updating `SCHEDULE.md`.
- `references/platform-posting-notes.md`: per-platform post types, link behaviour, media shapes, known quirks. Time-sensitive; verify live when it matters.
- `references/publer.md`: worked example with the official Publer MCP and the open-source publer-mcp-server.

Learn more: https://builtnotboosted.com/skills/scheduling
