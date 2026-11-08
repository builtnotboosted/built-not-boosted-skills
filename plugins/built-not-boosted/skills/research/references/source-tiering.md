# Source tiering, and the sources.md template

Not every source deserves the same trust, and the trust a source earns depends on what you are using it for. A trade magazine can be brilliant for spotting a story and poor as the place a figure is quoted from. Tiering makes that explicit so the same judgement gets made every time.

## The tiers

**Tier 1: primary and official.** The organisation that produced the number or the rule. Official statistics bodies, regulators, government departments, central banks, the original study or report, the company's own published terms. Quote figures from here.
Illustrations (UK): the Office for National Statistics, the Bank of England, GOV.UK. Elsewhere the equivalents are the national statistics office, the central bank and the relevant regulator.

**Tier 2: reputable secondary.** Established consumer bodies, national news outlets, respected trade associations and well-run industry research. Good for context and for finding the tier 1 source. Use a figure from here only if the primary is genuinely unavailable, and say so in the brief.

**Tier 3: radar.** Trade press written for professionals, newsletters, blogs, commentators, company press releases, forums, social posts. Excellent for spotting stories early and hearing how people talk. Never the source a figure is quoted from: follow it back to tier 1 or 2.

**Tier 0: the person themselves.** Their own experience, their own customers' questions, their own data. Unbeatable for authenticity, and the only legitimate source of "a customer once told me". Record when they told you.

## Questions to ask of any source

- **Who made this and what do they want?** Trade bodies argue for their members, companies publish research that supports their product, campaign groups campaign. The data can still be good; use the finding, not the conclusion they draw from it.
- **Who was asked?** A survey of a company's own customers, a self-selected panel or a professional membership is not "all people". Report it as what it is ("owners who answered X's survey said...").
- **When was it published, and has it been superseded?** Some official guidance pages claim to be "frequently updated" and have not been touched in years. Check the date on the page every time, and mine stale guidance for structure and plain-English framing, never for a figure, threshold or scheme name.
- **Is it final?** Interim reports, consultations and drafts are provisional. Say so when you cite them.
- **Does the figure mean what the headline says?** Some numbers are accurate and still mislead stripped of context (an industry-economics ratio quoted as a consumer verdict, a figure that applies to one subgroup quoted as if it applies to all). Those go in "Handle with care", or stay out.
- **Is it aimed at professionals?** Trade and adviser-facing material is a rich seam, but it is written for insiders. Translate it into what it means for your audience; never lift the wording.

## Rules that keep it honest

- Quote figures from tier 1 wherever possible, and cite the specific release or report and its date, not just the publisher.
- Never lift text verbatim from a source into a post. Mine the fact and say it in the brand's own voice.
- Never present a citation as an endorsement. "Research from X found..." is fine; implying X recommends the business is not.
- Fetch only the sources the person has approved, plus whatever a specific search turns up for a specific claim. Do not browse aimlessly and then quote whatever you found.
- Every piece lists its sources at the end of its research brief so every claim can be checked.
- When a source turns out stale, wrong or unreliable, demote it in `sources.md` and note why in one line.

## Fetch notes are worth keeping

Record how a source behaves, so the next run does not rediscover it:

- Some sites render their listings in the browser and come back empty to a plain fetch. Try the RSS feed, the sitemap, or the direct document link. A browser tool can read the rendered page if one is available.
- Reports are often PDFs; download and read the document rather than a summary page.
- Some content sits behind a login. Use what is public and never infer past the wall.
- Note publication rhythm (monthly, quarterly, annual) so new editions can be checked for when due.

---

## Template: `brand/sources.md`

Create this file the first time the skill runs if it does not exist. Fill the headings with the person's industry; leave the illustrations out once real entries exist.

```markdown
# Sources

Trusted research sources for <business name>, tiered. Maintained by the research skill.
Last reviewed: YYYY-MM-DD

## How to use this list
- Quote figures from tier 1. Use tier 2 for context. Use tier 3 as radar only.
- Every figure used in content is cited with its release and date in that piece's research brief.
- Fetch only the sources listed here, plus specific searches for specific claims.

## Tier 0: our own
| Source | What it gives us | Notes |
|---|---|---|
| Customer questions (comments, DMs, emails, calls) | The audience's real wording | Ask the person; log date |
| Our own analytics (see data/) | What topics and formats worked | Read with platform-data |

## Tier 1: primary and official
| Source | URL | Good for | Rhythm | Caveats | Fetch notes |
|---|---|---|---|---|---|
| <national statistics office> | | official figures | monthly | | |
| <regulator or professional body> | | rules, consumer guidance | as needed | check page date | |

## Tier 2: reputable secondary
| Source | URL | Good for | Slant or caveat | Fetch notes |
|---|---|---|---|---|

## Tier 3: radar
| Source | URL | Good for | Slant or caveat | Fetch notes |
|---|---|---|---|---|

## Release and announcement calendar
Scheduled dates that move our audience. Pull dates live each time; do not trust a date written here more than a few months ago.
| Release | Publisher | Usual timing | Kind (fast / dig-in) | Last checked |
|---|---|---|---|---|

## Demoted or retired
| Source | Why | Date |
|---|---|---|
```
