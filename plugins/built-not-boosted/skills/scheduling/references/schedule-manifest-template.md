# Scheduling manifest template

One `SCHEDULE.md` per content pack, saved at `marketing/content/<yyyy-mm-dd>-<slug>/SCHEDULE.md`. It is three things at once: the plan you show the person before anything is created, the record of what actually got queued, and the first dedup net on the next run (a record you wrote yourself is more trustworthy than any single read of the scheduler).

Keep it plain markdown so the person can read and edit it. Update the State column as you go, never delete rows (change the state instead), and add a log line for anything that changed after creation.

## Template

```markdown
# Schedule: <pack title>

Pack: content/<yyyy-mm-dd>-<slug>/
Timezone: Europe/London (offset on each row below)
Scheduler: <tool name, or "browser" or "manual">
Approved by: <name> on <yyyy-mm-dd>   (blank until the person says yes)

## Posts

| # | Platform | Account | Type | When (ISO + offset) | Caption | Media | Alt text | First comment | Links | State | Ref |
|---|----------|---------|------|---------------------|---------|-------|----------|---------------|-------|-------|-----|
| 1 | Instagram | @handle | reel | 2026-11-12T18:15:00+00:00 | captions.md#instagram | video-9x16.mp4 | n/a (video) | none | none | planned | |
| 2 | LinkedIn | Name (profile) | photo | 2026-11-13T07:30:00+00:00 | captions.md#linkedin | image-4x5.png | PACKAGE.md#alt-text | none | allowed: article | planned | |
| 3 | Facebook | Personal profile | manual | 2026-11-12T19:00:00+00:00 | captions.md#facebook | image-4x5.png | PACKAGE.md#alt-text | none | none | manual | |

## Hand jobs
- [ ] Row 3: post by hand (personal profile, no tool can auto-publish). Caption and image are in the pack.
- [ ] YouTube: pin the first comment once live. Text: "<exact text>"

## Holds
- (none) | Row N: held because <reason>; needs <what> from <who>.

## Log
- yyyy-mm-dd hh:mm: created rows 1-2, verified by read-back.
- yyyy-mm-dd hh:mm: row 2 deleted and recreated at 08:00 (person asked to move it).
```

## Field notes

- **Type:** `photo`, `carousel`, `video`, `reel`, `short`, `story`, `document` (LinkedIn PDF), `text`, `listing` (business listing post with a button), `manual` (person posts it), `reminder` (tool sends a nudge, person taps publish).
- **When:** always with an offset. Check daylight saving for the post's own date.
- **Caption:** point at the caption file and section in the pack rather than pasting it, so there is one copy of the words. The scheduler gets the caption verbatim from that file.
- **Links:** `none`, `allowed: <reason>` (article, event booking, long-form release, or whatever brand-profile allows), `held: unmarked`, `rewritten: <date>`.
- **State:** `planned` → `approved` → `queued` (created) → `verified` (read back and checked) → `published` (seen live). Side states: `held`, `manual`, `reminder`, `cancelled`.
- **Ref:** the scheduler's post reference, kept so you can find the post again for a move or delete. It stays in this private workspace file; never paste it into chat or into anything published.

## Dedup rule of thumb

A row in state `queued`, `verified` or `published` in any manifest within the last few weeks means that piece is done on that platform. Do not recreate it because a live read cannot find it; investigate, then flag.
