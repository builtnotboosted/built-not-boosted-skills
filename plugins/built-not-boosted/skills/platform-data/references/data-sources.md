# Data sources: what each gives, and how to pull it

Start with what the person already has. Native exports are free and usually the most complete. A scheduler's analytics are convenient because they cover several platforms in one place, but they can be partial. Read the `## Tools` section of the brand profile to see what is connected, and ask if it is unclear.

Interfaces and export menus change often. Paths below were last checked Nov 2026; verify in the product before giving step-by-step instructions.

## One owner per source, everyone else reads the snapshot

If more than one task needs the same data (a nightly check, the weekly review, a scheduling run), only one of them should pull it. It saves the result to `data/` with a header, and the others read that file. A reader may pull live only if the snapshot is missing, stale or partial, and should say so.

*Why: several jobs each pulling the same analytics within minutes wastes tokens and rate limits, and they end up disagreeing because each pull saw a slightly different picture.*

Snapshot header (top of every file in `data/`):

```
source: publer | meta | linkedin | youtube | tiktok | gsc | ga4 | ...
pulled_at: YYYY-MM-DDTHH:MM (with timezone)
window: YYYY-MM-DD to YYYY-MM-DD
accounts: <which accounts or properties>
coverage: complete | partial (<what is missing>)
notes: <anything odd about this pull>
```

The one exception: anything that **writes** (scheduling a post) must check the live queue at the moment of writing, never a snapshot, so it cannot double-post. That belongs to the `scheduling` skill.

## Native platform analytics

**Meta Business Suite (Facebook and Instagram).** Insights covers reach, views, interactions, follows, and per-post detail including saves and shares. Content and audience data can be exported as CSV from the Insights area. Instagram's in-app professional dashboard shows per-post saves, shares and sends, and follower activity by hour.

**LinkedIn.** Personal profiles: post analytics on each post (impressions, members reached, reactions, comments, reposts, saves) and a creator analytics page with an export. Company pages: the page analytics tab exports content, visitors and followers as spreadsheets.

**YouTube Studio.** Analytics covers views, watch time, average view duration, retention curves, traffic sources (including YouTube search terms) and audience ("when your viewers are on YouTube"). Export from the advanced analytics view. Shorts and long-form are reported separately; read them separately.

**TikTok Studio.** Overview, content, followers and live tabs. Per-video watch time, completion ("watched full video"), traffic sources and search terms; follower activity by hour. Data can be downloaded for a date range (longer ranges have been available for some accounts). A full-year export is worth pulling once: it shows how concentrated reach is and which months carry the year.

**Google Business Profile.** Performance shows searches, views, calls, direction requests and website clicks, increasingly split by surface (classic panel, Maps, AI summaries). Often not available through schedulers; read it natively.

## Google Search Console

Shows how pages or videos appear in Google web search: queries, impressions, clicks, CTR, average position, by page, device and country. Export from the Performance report (28 days or three months is a sensible window), or pull through the API or a connector. If the person's YouTube channel or site is verified, include it. Read it monthly. The `research` skill uses it for demand; this skill uses it for performance. See the research skill's `references/audience-demand.md` for how to read intent.

## GA4

Shows what happens after the click: sessions by source and medium, landing pages, and key events (form submissions, bookings, purchases). This is where enquiries from social become measurable, but only if links are tagged. Recommend UTM parameters on every link the business controls (for example `utm_source=instagram&utm_medium=social&utm_campaign=<content-slug>`). Export from Reports or Explore, or pull via the Data API or a connector.

## Scheduler analytics: Publer as the worked example

A scheduler that posts to several platforms usually reports on them too. Publer has an official MCP connector, and there is also an open-source Publer MCP server at github.com/pweightman/publer-mcp-server. Either lets Claude read analytics directly. Tool names differ slightly between them; the recipes are the same. Last checked Nov 2026, verify tool names and parameters before use.

**Useful reads (official connector names, open-source equivalents in brackets):**
- workspace selection first (`select_publer_workspace`); every read happens inside one workspace
- account lookup (`lookup_publer_accounts`; open-source `publer_list_accounts`)
- per-post insights sorted by reach or engagement (`get_post_insights`; `publer_get_post_insights`)
- best times to post, with a day-by-hour grid (`get_best_times_to_post`; `publer_get_best_times`)
- chart data for followers, reach and engagement over time (`list_analytics_charts`, `get_analytics_chart_data`; `publer_list_charts`, `publer_get_chart_data`)
- post lists by state and date (`list_publer_posts`; `publer_list_posts`)
- a quick written summary (`analyze_recent_performance`) and exports (`export_publer_analytics`)

**Pull recipes learned the hard way:**
- **Best times need a date range.** Pass `from` and `to` (a 28-day window works). Pull per account; never average across accounts, because an all-account average hides each platform's own peak.
- **Insights: top handful only.** Sort by reach, then separately by engagement, and take the first page. Reading every post is slow and expensive and adds little.
- **Published post lists are heavy.** Full post objects can include large media and thumbnail data, and a wide date range can exceed the response limit. Pull one day at a time, keep only id, date, platform, format and the first line of the caption, and merge into the previous snapshot by post id (published records do not change), dropping anything older than your window.
- **Scheduled post lists:** pass the state as a list plus a date range. A bare state filter has returned a correct count with an empty list, which looks like an empty queue.
- **Dedupe by post id.** Wide reads have returned padded repeats; treat a suspicious count as low confidence.
- **Some accounts return no per-post insights** (permissions or API limits). Record them as unmeasured and fall back to the native export.
- **Read the reach board for engagement too.** On some connectors the engagement sort returns the same order as reach; the rates on the reach board are the reliable read.

## Manual exports

If the person exports a CSV or screenshot and drops it in, save it unchanged to `data/` with a header file alongside, then read it. Screenshots are fine for a quick read; ask for the CSV when a number will be carried into the learnings.
