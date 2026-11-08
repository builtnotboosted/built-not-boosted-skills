# Worked example: scheduling with Publer

Last checked: Nov 2026. Tool names and behaviour below come from real use of both servers, but MCP servers change; check the tool list and descriptions in your session, and Publer's own docs, before relying on any detail. For questions about how Publer itself works (what each network supports, why a post failed), ask Publer's docs rather than memory: the official server has `search_publer_docs` and `search_publer_help` for exactly this.

There are two ways to connect Claude to Publer:

- **The official Publer MCP** (Publer's own cloud connector). Runs in Publer's cloud, so it works whether or not your computer is on. Tool names look like `select_publer_workspace`, `submit_publer_posts`, `list_publer_posts`.
- **The open-source publer-mcp-server** at https://github.com/pweightman/publer-mcp-server. Runs locally against the Publer API with your own API key. Tool names look like `publer_schedule_post`, `publer_list_posts`, `publer_delete_posts`. Useful as a fallback, and for jobs that need to run without an in-chat confirmation.

Pick one per job and stick to it within a run. If the official tools appear under an unfamiliar prefix, identify them by tool name, not prefix.

Never show workspace, account, media or post IDs in chat; they are tool arguments. Name things by account name, platform and caption.

## The shape of a run

1. **Select the workspace first.** Everything in Publer is workspace-scoped: accounts, media and posts. On the official server call `select_publer_workspace` before anything else, every conversation. If the person has more than one workspace, ask which.
2. **Find the accounts.** Official: `lookup_publer_accounts` (returns data; `list_publer_accounts` draws a card for the person instead). Open-source: `publer_list_accounts`. Match to the handles in brand-profile.
3. **Upload media from a URL.** Official: `upload_publer_media_from_url` (with `wait_for_completion`, and `direct_upload` for video). Open-source: `publer_upload_media_from_url`, then poll `publer_check_job_status` (pass the workspace, it errors without it). One import at a time; a second import while one runs is refused. A multi-image import can take a minute; keep waiting, do not resubmit. Local file upload on the open-source server returned "file not supported" in our testing, so host the file somewhere fetchable and use the URL route.
4. **Dedup read.** Official: `list_publer_posts` with a state and a one-day `from`/`to` range. Run it once for `scheduled` and once each for the published states. Open-source: `publer_list_posts` with `states: ["scheduled"]` plus a date range (a bare `state` returned a correct total with an empty list in our testing), and separately the published states, one day at a time.
5. **Create.** Official: `submit_publer_posts` with `when: "schedule"`, `scheduled_for` as ISO with offset, `post_type`, caption, media and network options. Open-source: `publer_schedule_post`.
6. **Verify.** Read the day back and check each post is there with the right time, account and media.

## Gotchas we hit (so you do not have to)

**Reads**
- Read one day (or one account and one day) at a time. A wide range returned padded, repeated rows in testing; dedupe rows by their post reference and treat a suspicious count as a low-confidence read.
- Wide published reads on the open-source server return huge media arrays and can blow the token limit. Pull per day and keep only the caption opening, date and reference.
- Platform names come back in different cases and spellings between the scheduled and published feeds (for example a business listing shown as "Google"). Compare case-insensitively and fold aliases before matching.
- The official list rows do not show every field (post type flags, YouTube title, first comments, listing buttons). Confirm those from the create response, and say "flag not verifiable by read" in the report if the response does not echo them.
- `get_best_times_to_post` (official) or `publer_get_best_times` (open-source) needs a `from` and `to`. It returns a weekday by hour grid per account; read each account separately, because an average across accounts hides each platform's own peak.

**Creating**
- Official `submit_publer_posts`: with more than one account or more than one post in a call, set `confirm_multiple: true`, otherwise it creates nothing and returns a confirmation request.
- Never use `when: "now"` (queue-only rule).
- On a timeout, poll `get_publer_job_status` before doing anything else. The same caption on the same account is blocked for about ten minutes; use `allow_duplicate: true` only for a deliberate delete-and-recreate.
- Post types on the official server: `post_type: "reel"` for an Instagram Reel, `"short"` plus a `title` for a YouTube Short, `"video"` for a plain video.
- On the open-source server: always pass `content_type: "video"` explicitly on a video post. Leaving it to infer from the media threw a misleading backend error on every platform in testing, which looked like an outage and was not. Put Reel and Short details, YouTube title and tags inside the `extra` object (`extra: { details: { type: "short" }, title, tags }`); top-level copies of those fields were silently dropped.
- Open-source `publer_create_posts_raw` returned success and stored nothing in our testing. Use `publer_schedule_post` and verify.
- Carousels: `content_type: "carousel"` failed on several networks on the open-source server in testing, while `"photo"` with several media items worked. If the carousel type errors, retry as photo with the same media list before holding.

**First comments**
- In Oct 2026 the official server's `first_comment` field did not persist on Facebook and Instagram posts (Instagram had worked earlier), while the open-source server's `comments: [{ text }]` did. Verify a first comment actually saved after creating; if it did not, delete and recreate via the route that works.
- First comments cannot be edited on an existing post by either route. To change one, delete and recreate.

**Editing and deleting**
- `reschedule_publer_post` (official) moves a time; `update_publer_post` changes fields. Media swaps and adding a listing button were unreliable through updates, so delete and recreate for those.
- Official deletes (`delete_publer_posts` then `confirm_delete_publer_posts`) need the person's yes in chat. Good for attended sessions; it means an unattended job cannot delete through the official server. The open-source `publer_delete_posts` has no such gate, so use it with care and only on posts you created.
- When recreating on a business listing, delete the old post first: the listing can refuse two posts in the same minute.

**Business listings (Google Business Profile)**
- Official: `platform: "google"`, `post_type: "photo"`, `title` set to the button type (`LEARN_MORE`, `BOOK`, `ORDER`, `BUY`, `SIGN_UP`, `CALL`), `network_options: { url }` for the button link (no URL for `CALL`, which uses the listing's phone number).
- Open-source: a `networks: { google: { type: "photo", title, url, text, media } }` block alongside the normal fields. The caption body stays clean; the link rides the button.
- You cannot add a button to an existing post with an update; delete and recreate.

**Personal Facebook profiles**
- Publer can only create these as reminder posts the person taps to publish. Mark them `reminder` in the manifest.

**YouTube comments**
- Publer cannot post or pin YouTube comments. Put the pinned comment text in the hand-jobs list.

## Paragraph spacing

Preview one multi-paragraph caption in Publer's composer on first use. If paragraphs run together on any network, add an empty line between blocks before submitting, and note it in your workspace tools notes.
