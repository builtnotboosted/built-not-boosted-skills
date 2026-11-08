# Finding what your audience actually asks

Content pillars tell you what kind of post to make. Demand tells you which angle and which words, so a post earns search traffic and recognition ("that's exactly what I was wondering") instead of only feed reach. The audience's own phrasing is the best title you will ever find.

The specific volumes and trends decay within weeks. Treat any demand snapshot as live data: date it, save it to `data/` and re-pull before planning a fresh batch.

## Where the questions are (free first)

Work through these roughly in order. Most cost nothing.

1. **Your own comments, DMs, emails and calls.** The highest-value source there is, because it is your actual audience. Ask the person what they get asked most. Replying to a real commenter with a video is also one of the cheapest, best-performing formats going.
2. **Search suggestions.** Type the topic into Google, YouTube and TikTok search and note the autocomplete suggestions. Try the topic plus "how", "why", "can I", "should I", "what happens", "vs" and the current year.
3. **"People also ask" boxes** on a Google results page. Each expands into more questions. Note the exact wording.
4. **Platform search insights.** Some platforms show creators what people search for (TikTok has a creator search insights tool; YouTube Studio shows search terms that led to your videos). Last checked Nov 2026, verify availability.
5. **Google Search Console** for any site or channel the person owns. This shows the queries Google already shows them for, which is first-party evidence, much stronger than a keyword tool. See below.
6. **Forums and communities.** Reddit, Facebook groups, Mumsnet-style forums, niche communities, Quora. Search the topic and read how people describe the problem, what confuses them, what they are scared of.
7. **AI assistants.** Ask ChatGPT, Gemini, Claude or Perplexity the questions your audience would ask. Note what they say and which sources they cite. If you are not cited, a plain page whose heading matches the exact question is how you get there.
8. **Question-research tools** (AnswerThePublic and similar) group autocomplete data into question, preposition and comparison lists. Useful for a quick map of a topic. Free tiers are limited.
9. **Keyword tools** with volumes (paid). Optional. One worked example is below.

## Reading Search Console properly

Search Console tells you the queries your pages or videos appeared for, with impressions, clicks, click-through rate and average position. A few lessons that save a lot of wasted effort:

- **Split commercial from informational intent.** A short explainer can rank well for a head term ("home insurance", "running shoes") and get almost no clicks, because those searchers want a quote or a shop, not a lesson. That is not a failure and not worth chasing. The winnable queries are the questions ("what does X cover", "X vs Y"), so judge click-through on the question cluster, not the headline average.
- **Look for page-one queries with nothing built for them.** A query at average position 8-12 with no dedicated piece is the cheapest win available.
- **Retitling beats republishing.** If an existing piece already ranks for a question, rework its title, description and tags to match that question before making something new.
- **Check device split.** Mobile and desktop can rank and click very differently; optimise titles and thumbnails for where the clicks are.
- **Check local and brand queries.** Near-zero impressions for "<service> near <town>" means search is not yet a local discovery channel for this business; directories and the business profile may be doing that job instead.
- **One piece can dominate.** A single unplanned video can carry most of a channel's impressions. Note it before over-planning, and learn what made it travel.
- **YouTube is two surfaces.** Search Console shows Google web search; YouTube Studio shows search inside YouTube. They are different numbers.

Export monthly (or pull via the API or a connector) and compare against the previous month. Save the export to `data/`.

## Turning demand into topics

- **Group the questions** by pillar and by audience type.
- **Check what already exists.** Look through `content/` and the person's live channels. A gap is a question with real demand and nothing made for it.
- **Use the phrasing as the title.** Put the keyword in the first few words, and say it aloud in video (several platforms now read speech and on-screen text for search). Last checked Nov 2026, verify.
- **Rank by fit, not just volume.** A smaller question from exactly the right person beats a big one from people who will never buy.
- **Note seasonality.** Some questions spike every year at the same time; diarise them in the release calendar in `brand/sources.md`.
- **Record it in the brief.** The research brief's "The question" and "Words to use" sections carry the wording and where it came from.

---

## Worked example: DataForSEO (optional, paid)

DataForSEO is a pay-as-you-go API that returns Google search volumes, keyword suggestions, autocomplete and full results pages (including "People also ask"). It has an MCP connector, so Claude can query it directly once the person has an account. It is one option among several; anything that returns volumes and questions will do.

A typical session for a topic, say "dog grooming" for a local groomer in the UK:

1. **Read the docs first.** Use the connector's documentation search for the endpoint you need; parameters and endpoint names change. Last checked Nov 2026, verify.
2. **Search volume for seed terms.** The Google Ads search-volume endpoint takes a list of keywords, a location (UK has its own location code) and a language. Returns monthly volume and trend.
3. **Expand into related questions.** The DataForSEO Labs keyword-suggestion and related-keyword endpoints return longer phrases containing or near the seed. Filter for question words (how, why, can, should, what, vs).
4. **Pull "People also ask".** A live Google organic SERP request for the main question returns the results page, including any "People also ask" items with their exact wording.
5. **Autocomplete.** The SERP autocomplete endpoint returns the suggestions a person sees while typing.
6. **Save the pull** to `data/<yyyy-mm-dd>-search-demand-<topic>.md` with the date, location, language and the cost, and summarise the top questions in the research brief.

Keep requests small and specific: costs are per request, and a few well-chosen seeds tell you more than a thousand keywords. Volumes are estimates; use them to rank options, not as facts to quote in content.
