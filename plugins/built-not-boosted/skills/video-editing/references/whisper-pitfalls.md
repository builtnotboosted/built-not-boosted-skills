# Whisper pitfalls (and how the tool counters each)

Whisper is excellent at turning speech into readable text. That is exactly the problem for editing: it tidies. Every pitfall below has fooled a real edit, and every one has a counter in the tool. None of it replaces ears: anything flagged "check by ear" goes to a human.

## What it does wrong

| Pitfall | What you see | Counter |
|---|---|---|
| **Silently drops whole retakes** | A gap full of speech energy with no words, and neighbouring words stretched over the hole | Two models (large-v3 and medium.en) plus gap-fill where speech energy has no words; plausible word ends capped at start + 0.6 s |
| **Tidies stumbles away in context** | "the, the" becomes "the"; fillers vanish even with a filler-heavy prompt | The second listen re-hears every take on its own, with no surrounding context to smooth over |
| **Hallucinates words over silence** | Words where there is no sound | The gate drops words with under 25% voiced energy |
| **Restart part-way through a line** | Looks like one long clean take (no backwards jump) | Double-read detection in the second listen: two or more of the line's word pairs heard more often than the script says them |
| **Wrong names** | Names, places and brand words misspelt | `vocab` in the prompt, `syn` for alignment, `captions.fix` for display. Put the presenter's own name in every project's `vocab` |
| **Word ends run early on soft endings** (0.1 to 0.5 s), **word starts early after a restart** (up to 0.4 s) | A cut on a Whisper timestamp clips the word | Never cut on a timestamp alone: the build waits for the audio to go quiet and the cut check verifies it |
| **Drops a word when transcribing the render** | The gate reports a missing word that is clearly in the audio | Before blaming the cut, check the source range in `build/edl.json` covers the word |
| **Repeats a word said once, or drops a line, over a whole video** | A false fail | The gate re-listens to just the flagged stretch with both models before failing |

## Traps that look like the wrong problem

- **A hallucinated final word.** The large model added a plausible last word to a line the speaker never finished; only the medium model and the energy map showed the line stopped short. A last word that only one model hears, in a burst that is quieter or shorter than the rest, is suspect: use another take.
- **A split term.** An unfamiliar two-word term ("assured shorthold") heard by both models as a stumble ("a short short hold"). Check the duration against a clean read of the same words (0.80 s against 0.82 s) and re-listen with the term in the prompt (`vocab`). If both prompted models write one clean term, it is a clean read. The gate does this itself now (a prompted third opinion turns the fail into a note). A real stumble still shows when prompted.
- **A prompt makes Whisper parrot the script.** Prompting a re-listen with the script fixes real mishearings, but it also pulls the transcript towards the script: a long multi-line prompt turned a live "directly" into the script's "straight", and a one-line prompt added a word nobody said. Prompt one line at a time, let unprompted agreement beat the prompted listen, and never add a word only the prompted listen heard.
- **A restart hidden in a pause.** "The price is… [4 s] the price includes…" with the long pass stretching one word across the pause, so the second "the price" does not exist on paper. Before cutting a pause out of a line, listen to the stretch after the pause on its own: if it starts with the line's opening words, start the line there (`nin`).
- **Stop closures look like word ends.** A cut in the silent closure of a plosive inside a word ("de|posit": the p) passes every energy rule. Cut only at a closure where the large-v3 word boundary is, and add it to `cut_check.allow` with the reason. Never loosen the closure rule: a looser rule once waved through "dig|ging".
- **A faint opener at a splice.** A read spliced in can open with a near-whispered "and" or "so" (30 dB under speech). Whisper places it at the wrong time, which can look like a doubled word. Measure the energy before believing it, and if it is that faint, start the read after it.

## Verifying a restart flag

Whisper drops the repeated words of a false start **even on an isolated listen**. So an isolated listen that "sounds clean" is **not** evidence against a restart flag. This exact mistake (switching off a correct flag after a clean-sounding isolated listen) has been made several times, and the gate caught every one.

The test is the energy map: run `silencedetect` at -45, -38 and -30 dB over the take. A real restart is a burst of speech, a quiet gap, then the line again from its start. If the flag's placement looks wrong, do not switch it off: find the bursts and move the in-point into the quiet before the second burst (`nin`), or correct that take's `inner_cuts` in `takes.json` with one cut from inside the quiet after the last good word to inside the quiet before the clean restart (both points under -45 dB), and note it.

## "Speech with no words" from the gate

Walk the energy across the flagged gap before changing anything. Most flags are a word's own tail after Whisper's early end, room tone in a denoised render, or a near-silent murmur. A real hidden re-read sits at normal speech level. The gate measures from where the sound really ends and against max(floor + 9 dB, speech level - 30 dB).

## Stray words at a cut

The end of a dropped take can ride in on the next line's in-point: neither a repeat nor a skip. The gate fails it unless the words are the kept take's own edge words or were said in the same breath (under 1 s apart), which count as ad-libs. **Never accept an "ad-lib" note without checking where the words came from:** map each word to source time through `build/edl.json`. A word that sits in the previous piece's tail, past its last scripted word, is a stray: pull that line's `nout` back into the gap after its last word.
