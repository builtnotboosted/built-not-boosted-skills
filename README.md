# Built Not Boosted: the skill pack

Ten Claude skills for small businesses, freelancers and creators who want social content that actually brings in work, without paying to boost it.

We built these for our own businesses first. They run the content for a mortgage practice, a networking group and this channel, with every post, script, image and edit written, checked and scheduled with Claude. This is the public version, with the private bits taken out and the methods left in. It won't get you all the way to where we are on day one, but it'll get you a long way, and it gets better the more you use it.

Free, MIT licensed. Guides and walkthroughs live at **[builtnotboosted.com](https://builtnotboosted.com)**.

## What's inside

| Skill | What it does |
|---|---|
| `brand-setup` | Interviews you and builds your marketing workspace: a brand profile (voice, audience, platforms, boundaries, compliance, visuals) that every other skill reads. Start here. |
| `writing` | Posts, captions, first comments, alt text and articles in your voice. Hook, value, one genuine question. Per-platform packaging, link-free profile-first writing, right-sized disclaimers, proper ad labelling. |
| `research` | Finds topics your audience actually asks about and backs every claim with a dated source. Never invents a figure, quote or story. Produces a research brief the other skills use. |
| `scheduling` | Gets content into your scheduler safely: queue only, explicit time zones, duplicate checks against live and published posts, media checks. Works with any tool; Publer is the worked example. |
| `platform-data` | Pulls your analytics, runs a weekly review and keeps a learning log of what works, with evidence and sample-size caution, so planning gets smarter. |
| `video-scripting` | Teleprompter-ready scripts for shorts and long-form: a warm hook, early who-am-I, a retention shape, a soft close, and edit notes for the editor. |
| `image-generation` | Platform-sized images with the headline baked in by the image model, likeness-locked to your real face from reference photos, grid-safe, with alt text. Animated statics and an HTML fallback included. |
| `video-editing` | Turns raw talking-head footage into finished shorts and long-form: finds the clean take of every line, syncs cameras by sound, punch-ins and B-roll, captions, -14 LUFS, and a QA gate that re-transcribes the render before it lets it out. Python + ffmpeg + Whisper. |
| `review-loop` | Every piece gets a self-critique and an independent review before it ships. Only a clean pass goes out. |
| `voice-loop` | Compares what you actually said on camera (the captions file) and how you edited our drafts against what we wrote, and turns the differences into voice rules. This is how it ends up sounding like you. |

## How it fits together

```
brand-setup ──► brand/brand-profile.md  (the single source of truth)
                     │
research ──► writing / video-scripting ──► image-generation / video-editing
                     │                               │
                     └──────────► review-loop ◄──────┘
                                       │
                                  scheduling ──► platform-data ──► performance-learnings
                                                                        │
            voice-loop ◄── your edits and what you actually said ──► voice-learnings
```

Everything lives in one folder you own (`marketing/` by default): your brand profile, your research sources, your learning logs, and a folder per piece of content. The skills hold the method; your workspace holds the rules and the facts. Change a rule once in your brand profile and every skill follows it.

## Install

**Claude Code**
```
/plugin marketplace add builtnotboosted/built-not-boosted-skills
/plugin install built-not-boosted@built-not-boosted
```

**Claude (desktop, Cowork or claude.ai)**: download this repo as a zip, then add each folder under `plugins/built-not-boosted/skills/` as a skill (Settings → Capabilities → Skills), or install the plugin from the zip where plugins are supported.

Then say: *"Set up my brand profile"*. That runs `brand-setup`, and you're away.

## What you'll need

- Claude with skills enabled. Everything text-based works out of the box.
- For images: access to an image model (we use Google's Gemini image model, "Nano Banana"). Without one, the HTML fallback still produces clean graphics.
- For video editing: Python 3.10+, ffmpeg and Whisper on your own computer. Run `skills/video-editing/setup.sh` once, then `python3 vedit.py doctor` to check.
- For scheduling and analytics: a scheduler with a Claude connector helps (we use Publer, and [built our own open-source Publer MCP server](https://github.com/pweightman/publer-mcp-server)), but native platform exports work too.

## A few honest notes

- Platform rules change constantly. Anything time-sensitive is marked with when we last checked it. Verify before you rely on it.
- If you're in a regulated industry, these skills will carry your required wording, but they don't know it. You (or your compliance team) put it in your brand profile. There's a UK financial services example included as a reference.
- The video tools have been run hard on our own footage on a Mac. They're written to be cross-platform, but Windows and Linux have had less mileage. Issues and pull requests welcome.

## Keeping up to date

These skills are a snapshot of the private ones we use every day. As ours improve, we bring the lessons across here. Watch the repo or check the changelog on the site.

Made by Anna & Patrick at [Built Not Boosted](https://builtnotboosted.com). Built, not boosted.
