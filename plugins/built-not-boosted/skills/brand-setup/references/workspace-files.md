# Starter contents for the living files

`brand-setup` creates three living files with empty but structured contents. Each one belongs to another skill, which adds to it over time. Use the owning skill's template so the headings match what that skill expects:

| File | Owning skill | Template |
|---|---|---|
| `brand/voice-learnings.md` | `voice-loop` | `voice-loop/references/voice-learnings-format.md` |
| `brand/performance-learnings.md` | `platform-data` | `platform-data/references/learning-log.md` (the "Template for a new" section) |
| `brand/sources.md` | `research` | `research/references/source-tiering.md` (the "Template" section) |

If those skills aren't installed, use the fallbacks below. Their headings match the owning templates, so the files carry on working when the skills are added later. Replace any placeholder in angle brackets with the business name and today's date.

## brand/voice-learnings.md (fallback)

```markdown
# Voice learnings: <name or brand>

Read this before writing anything in <name>'s voice. Working rules beat general skill guidance.
Fed by the voice-loop skill from filmed videos and hand-edits. Conflicts are held for <name>, never auto-applied.

## Working rules
(promoted: seen on 2+ pieces, or a direct instruction)

## Calibration
| Date | Piece | Type | Script words | Delivered words | Runtime | WPM | Ratio | Verbatim |
|------|-------|------|--------------|-----------------|---------|-----|-------|----------|

## Candidates (seen once, waiting for a second sighting)

## Held conflicts (waiting for <name>)

## Log (newest first)

## Retired
```

Seed the Log with the voice samples the user gave during setup, quoted verbatim, because they are the first real evidence of how this person writes:

```markdown
### <yyyy-mm-dd> · Voice samples from brand setup
Source: pasted by <name> during brand-setup.
> <sample 1, verbatim>
> <sample 2, verbatim>
- Observed: <one line per pattern you can see, e.g. "opens with a short question", "uses 'folks'">. Candidate.
```

Also add any direct instruction the user gave about their voice ("never call me an expert", "first names only") straight under Working rules, marked as a direct instruction with the date.

## brand/performance-learnings.md (fallback)

```markdown
# Performance learnings

What actually works for <business name>, per platform, with evidence.
Maintained by the platform-data skill. Rules need the owner's sign-off.
Last updated: <yyyy-mm-dd>

## How to read this
- Confidence: hypothesis < watch < pattern < rule. Plan around rules; test patterns; treat the rest as ideas.
- Every entry points to its evidence in data/.
- Reach floor for engagement rates: 50.

## Rules
(none yet)

## Patterns

## Watch

## Hypotheses to test
- Video out-reaches still images on most platforms; judge stills on saves and comments. (external, test on our data)
- Posts that ask a genuine question get more comments than posts that announce. (external, test on our data)
- Concrete "watch out for this" and "what actually happens when" pieces are good reach candidates. (external, test on our data)

## Timing

## Retired
```

## brand/sources.md (fallback)

```markdown
# Sources

Trusted research sources for <business name>, tiered. Maintained by the research skill.
Last reviewed: <yyyy-mm-dd>

## How to use this list
- Quote figures from tier 1. Use tier 2 for context. Use tier 3 as radar only.
- Every figure used in content is cited with its release and date.

## Tier 0: our own
| Source | What it gives us | Notes |
|---|---|---|

## Tier 1: primary and official
| Source | URL | Good for | Rhythm | Caveats | Fetch notes |
|---|---|---|---|---|---|

## Tier 2: reputable secondary
| Source | URL | Good for | Slant or caveat | Fetch notes |
|---|---|---|---|---|

## Tier 3: radar
| Source | URL | Good for | Slant or caveat | Fetch notes |
|---|---|---|---|---|

## Release and announcement calendar
| Release | Publisher | Usual timing | Kind (fast / dig-in) | Last checked |
|---|---|---|---|---|

## Demoted or retired
| Source | Why | Date |
|---|---|---|
```

If the user named their regulator, professional body or go-to industry sources during setup, add them under the right tier now.

## brand/reference-images/README.md

```markdown
# Reference images

Photos used only as likeness references for generated images. Never posted directly.

| File | Shows | Best for | Notes |
|---|---|---|---|

Consent: <note anyone else pictured and that they've agreed>
```
