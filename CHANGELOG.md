# Changelog

## 1.0.1 (November 2026)
- video-editing: the caption check now uses three listens. Words both unprompted listens heard are kept as the speaker's own (live rewordings survive). Only lines that differ from the script are re-listened, one line per prompt, and a word the caption lacks is added only if an unprompted listen heard it too, because a prompted listen parrots the script. Short sound-alikes are flagged for a by-ear check. Faster, since matching lines are no longer re-listened.
- video-editing: `deliver` now ships the caption check report (`vN-caption-check.txt`), and the hand-over checklist asks for it to be read and every CHECK named.
- video-editing: new Whisper pitfall, "a prompt makes Whisper parrot the script".
- Tidy: no em dashes in tool output; README credit made brand-only.

## 1.0.0 (November 2026)
First public release: brand-setup, writing, research, scheduling, platform-data, video-scripting, image-generation, video-editing, review-loop, voice-loop.
