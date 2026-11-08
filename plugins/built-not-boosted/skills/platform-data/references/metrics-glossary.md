# Metrics glossary

Platforms use similar words for different things. This glossary says what each metric means, how far to trust it, and how to read it. Platform-specific definitions change; when a number matters, check the platform's own help page for its current definition. Last checked Nov 2026, verify.

## Exposure

**Impressions.** How many times the content was shown. One person can generate several. Good for scale, poor for comparing posts.

**Reach.** How many unique accounts saw it at least once. The default ranking measure for "how far did it travel". Some platforms estimate it.

**Views / plays.** For video, how many times it started playing. Definitions vary (some count any start, some require a few seconds, some count replays). Video "views" and photo "reach" are not the same metric, so treat cross-format comparisons as directional only.

**Reach rate.** Reach divided by followers. Shows whether content is escaping your existing audience.

## Attention

**Watch time / average view duration.** Total or average time watched. A core ranking signal for video on most platforms.

**Completion rate / watched full video.** Share of viewers who reached the end. The single most important short-video signal; platforms push videos that people finish.

**Retention curve.** Where viewers drop off. The first three seconds and the midpoint are where most are lost; use the curve to fix hooks and pacing.

**Replays / loops.** Repeat watches. Some platforms weight replay rate heavily, so a short, rewatchable cut can outrank a longer one.

**Dwell time.** Time spent on a post (LinkedIn and carousels especially). Not usually shown directly; carousels and long text raise it.

## Active engagement (the signals that move distribution)

**Saves / bookmarks.** Someone wants to come back to it. A strong usefulness signal, weighted well above a like on most platforms.

**Shares, sends, reposts.** Someone showed it to another person. Private shares (DMs, messaging apps) are among the most heavily weighted actions on several platforms.

**Comments.** Conversation. Thoughtful comments are weighted far above likes on LinkedIn and others. Your own comments do not count; strip them before reading.

**Likes / reactions.** The weakest signal. Easy to give, barely moves reach on most platforms now.

**Profile visits, follows from post.** The post made someone want more of you. Good bridge metric between reach and enquiry.

## Rates

**Engagement rate.** Interactions divided by reach (or by impressions, or by followers: platforms and tools differ, so always say which). Readable only above the reach floor. Always quote with its reach.

**Click-through rate (CTR).** Clicks divided by impressions. In search, judge it on informational (question) queries, not commercial head terms that were never going to click.

## Outcomes

**Link clicks.** Clicks on a link in the post, bio or profile. Many platforms now ration or penalise links, so this undercounts interest.

**Enquiries / leads / bookings / sales.** The real goal, as defined in `## Offer & goal`. Usually needs separate tracking: a form source field, a UTM tag on links, a "how did you hear about us" question, or DM keyword counts.

**Conversions (GA4).** Events marked as key events in GA4 (form submits, purchases, calls). Attribute by source/medium and campaign; social often shows up as "referral" or "(direct)" if links are not tagged.

## Search

**Search impressions / clicks / average position (Search Console).** How often pages or videos appeared in Google web search, how often they were clicked, and roughly where they ranked. Average position 1-10 is page one.

**Search terms (YouTube Studio, TikTok).** The queries people typed inside the platform before finding the content. A different surface from Google web search.

## Audience

**Followers / subscribers and net growth.** Gains minus losses over the window.

**Follower activity ("when your followers are online").** The platform's own count of when followers are active. More reliable for timing than a scheduler's best-time grid, which measures when your posts did well.

**New vs returning viewers.** A high new share means discovery is working; returning viewers have to be earned with series and recurring formats.

**Audience location, age, gender.** Check it matches `## Audience`. A big audience in the wrong country is reach that cannot convert.

## Reading rules (summary)

- Quote every figure with its denominator, window and source.
- Engagement rate only above the reach floor (default 50).
- Median over mean; name outliers separately.
- Absent from a pull means unmeasured, not zero.
- Video views and photo reach are not interchangeable.
- Engagement is not an enquiry.
