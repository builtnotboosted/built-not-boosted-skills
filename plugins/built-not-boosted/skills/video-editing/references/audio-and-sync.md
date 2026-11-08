# Audio, sync and noise

## Check the source before editing

`prep` stops on three things, because no edit can fix them later:

- **HDR footage** (HLG or PQ). Converted without tone-mapping it comes out washed-out grey. Re-shoot with HDR video off, or tone-map to SDR first.
- **The wrong shape** (landscape for a short, or vertical for `--long`).
- **Call-quality audio** (under 32 kHz). Phones drop to 8 to 16 kHz mono when a Bluetooth mic or earbuds connect in hands-free mode. Everything above 4 to 8 kHz is never recorded, so it sounds boxy and echoey. Set `"allow_low_audio": true` only if the person accepts it, and say so at hand-over.

## Bluetooth audio is also late

Hands-free Bluetooth audio usually arrives about 270 ms behind the lips, a constant offset. If a clip must be saved rather than re-recorded, fix the **source** and start the edit again. Never swap new audio into a half-built edit: it ships off-sync, and old picks no longer line up with the words.

1. Run speech enhancement on the raw audio (any good tool: Adobe Enhance Speech, iZotope RX, or similar) and keep the enhanced speech stem.
2. Measure the offset with `scripts/lipsync.py <clip> <t0> <t1>` on two 40 to 60 s stretches where the presenter faces the camera. It correlates mouth movement with the speech envelope; + means audio late. A phone's own mic reads about 0 to +20 ms; a Bluetooth hands-free mic around +285 ms. Trust it only when the peak correlation is 0.15 or more and two windows agree.
3. Build a corrected source: the original video stream-copied, plus the enhanced audio advanced by the offset:

```
ffmpeg -i raw.mp4 -ss 0.285 -i enhanced.wav -map 0:v -map 1:a -c:v copy -af apad -t <video duration> -c:a aac -b:a 192k fixed.mp4
```

4. Re-measure (target 0 to +20 ms), then `init` a fresh project on `fixed.mp4` and run prep, takes and picks from scratch.

## Lip sync on the finished render

Run `scripts/lipsync.py build/final.mp4 <t0> <t1>` on two or three face-to-camera windows of every final render; each should be within ±40 ms. It masks hard cuts and reframes (unmasked, the whole-frame jump at a cut fakes "+170 ms audio late"). Walk-ins and close-ups with the mouth out of frame give low correlation (under 0.15): do not trust those windows.

## Background noise

For a steady hum, fan or drone whine, set `"audio": {"denoise": "firm"}` (or `"gentle"`, or a number 0 to 1). The finished audio goes through a spectral gate fingerprinted from the take's own pauses before loudness normalisation.

- Measure first: compare the pause spectrum with a clean shoot. A drifting tonal whine (motors holding position) beats fixed notch filters and broadband denoisers; a spectral gate with a noise fingerprint took 11 to 13 dB off a drone whine for about 0.5 dB of voice.
- Never use an adaptive (non-stationary) mode: it took more noise off but ate 4 to 7 dB of voice.
- Claude cannot hear artefacts. Send the person a before/after of the same 25 s and let them decide.
- Denoising lowers the noise floor, so the gate's speech-with-no-words check becomes more sensitive (on one shoot it then found a real hidden "and").

## Loudness

Two-pass loudnorm to -14 LUFS integrated, -1.5 dB true peak, LRA 11, then AAC 192k at 48 kHz. -14 LUFS is where most platforms normalise speech-led video; louder gets turned down, quieter sounds weak next to other posts. Check the result with:

```
ffmpeg -i final.mp4 -af loudnorm=I=-14:print_format=summary -f null - 2>&1 | grep "Input Integrated"
```

Speech normally lands within half a dB of target. Material with long silences can read a little low; that is the measurement, not a fault.

## Shoot habits that save the edit

Worth printing on the shoot sheet (the `video-scripting` skill owns the full list):

- Restart a fluffed line from the start of the sentence, not mid-sentence.
- Hold a warm look at the lens for 2 to 3 seconds at the end: it is the cover frame.
- Record 30 s of B-roll at each location.
- Let a second camera roll the whole time, with its own mic on, so it can be synced by sound.
- Leave 2 s of empty frame after the last line before stopping.
- Wired or built-in mic, never Bluetooth hands-free.
