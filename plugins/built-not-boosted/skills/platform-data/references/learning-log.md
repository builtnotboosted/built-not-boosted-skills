# The learning log: `brand/performance-learnings.md`

The learning log is how the workspace gets smarter. It records what this audience actually responds to, on each platform, with the evidence behind it and how sure we are. Other skills read it: `research` leans toward proven topics, `writing` and `video-scripting` lean toward proven hooks and formats, `scheduling` uses its timing reads.

The rule that makes it trustworthy: **a lesson is only as strong as its evidence, and the log says how strong.** Generic advice from the internet goes in as a hypothesis at most; our own repeated data is what turns something into a rule.

## Confidence levels

| Level | Means | Typical evidence | Who can set it |
|---|---|---|---|
| **hypothesis** | Something worth testing: outside advice, a hunch, a single post | one post, or external research | Claude |
| **watch** | Seen once in our own data, above the reach floor | one window, at least one readable post | Claude |
| **pattern** | Seen repeatedly in our own data | 3+ posts across 2+ separate windows, above the floor, no strong contradiction | Claude |
| **rule** | Settled enough to plan around by default | a pattern that has held for 4+ weeks, or a completed test | the person signs off |
| **retired** | No longer true or no longer relevant | contradicted by 2+ later windows, or the platform changed | Claude proposes, person confirms |

## Promotion and demotion

- **Promote** only when the bar above is met. Say in the entry what the new evidence was.
- **One window is never a rule,** however striking. A single breakout post is a watch-item until it repeats.
- **External research corroborated by our own data** can move faster, but still needs our own posts.
- **Contradictions are recorded, not hidden.** A pattern contradicted once gets a note; contradicted twice it drops a level.
- **Platform changes reset confidence.** If a platform changes how it ranks or reports, mark affected entries for re-check.
- **Rules are proposed, not imposed.** When something reaches rule level, ask the person to confirm before other skills treat it as the default.

## Sample-size cautions to carry in every entry

- Reach floor: engagement rates below about 50 reach are not evidence.
- One outlier can dominate a window; read the rest by median.
- Coverage varies between pulls; a missing platform is unmeasured.
- Posts keep accumulating; note the age of any post you cite.
- Format, slot and topic are often tangled in a single post. Say which you think did the work, and how sure you are, and look for a second post that separates them.
- Engagement evidence is not enquiry evidence. Say which one an entry is about.

## Entry format

```markdown
### <Short, specific claim>
**Platform:** TikTok | Instagram | all | ...
**About:** reach | engagement | enquiries | timing | format | topic
**Confidence:** hypothesis | watch | pattern | rule | retired
**First seen:** YYYY-MM-DD  **Last checked:** YYYY-MM-DD
**Evidence:**
- YYYY-MM-DD: <post or test>, <metric with denominator>, <window>, source `data/<file>`
- YYYY-MM-DD: ...
**Contradictions:** none | <dated note>
**So what:** the one-line planning implication.
**Next check:** what would strengthen or break it, and when.
```

Keep entries short. The diary lives in `data/`; the log keeps only the lesson and the evidence pointers.

## Template for a new `brand/performance-learnings.md`

```markdown
# Performance learnings

What actually works for <business name>, per platform, with evidence.
Maintained by the platform-data skill. Rules need the owner's sign-off.
Last updated: YYYY-MM-DD

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
Current best-time reads per platform, with the source and caveats. Live tests listed here.

## Retired
```

The three starter hypotheses are lessons that have held up well for other small accounts. They start as hypotheses because they are not yet this audience's evidence.
