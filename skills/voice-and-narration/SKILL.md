---
name: voice-and-narration
description: "Cast, generate and verify voice narration with a respell layer and speech-to-text checks. \"the voice says the name wrong\""
user-invocable: true
---

# Voice and narration: cast it by ear, verify it by machine

Stock text-to-speech in Indian languages can sound flat; names, loanwords and numerals get mangled; and a single
wrong line in a 130-line script is easy to miss by ear. The method: cast from a written brief, let the client
choose by ear on the device they will watch on, feed the engine respelled text while captions keep the correct
spelling, direct pace per line, and verify every generated line by transcribing it back.

## Choose the approach (in the brief)

| Approach | When | Notes |
|---|---|---|
| A narrator character (designed TTS voice) | storybook, explainer, brand | casting brief → audition → pick by ear |
| The client's own voice, recorded | personal films, founder films | best authenticity; record line by line (see inbox guides) |
| The client's own voice, cloned | personal films when recording 100+ lines is impractical | **only the voice owner may authorise their clone**, in writing in decisions.md |
| Real interviews / voice notes | memorial, documentary, testimonial | clean with CLIPFX, caption from the script, never from STT |
| Captions only | short social, music-led films | sound design carries more |

Never clone a third party, a public figure, or someone who has died (use their real recordings). Brand work:
talent release for any human voice; disclose synthetic voices where the platform or regulator requires it
(`marketing-video`).

## Workflow

1. **Casting brief** (`references/voice-casting.md`): age, region and dialect, register, texture, pace, mic
   distance, and the narrator's rules from the treatment. Providers do not build a voice from a description:
   the brief is how you pick the closest voice and direct it.
2. **Audition.** Six lines that stress the engine (one funny, one tender, one list, one name-heavy, one long
   sentence, the emotional peak) plus the hero's name in 3 spellings. Write `film/audition.json`, run
   `python tools/voice/audition.py film/audition.json` (paid providers are quoted first: run it without `--go` to see the quote, and add `--go --quoted-providers <providers>` after the client's go) and send
   `out/audition/index.html` (publish it as an artifact) so the client listens on a phone. Real history: a
   five-voice audition, then a three-engine audition, then the client cloned his own voice and that won.
3. **Set the voice** in `film/script.json` `"voice"`: `provider` (`sarvam`, `sarvam_clone`, `elevenlabs`,
   `openai`, `placeholder`), `voice`, `lang`, `pace_scale`, `lufs` (-18), `verify_threshold` (85), `stt_provider`, and
   optionally `model`: leave it out and the registry's pick for that provider is used (`python tools/resolve_model.py
   --alias latest-tts-<provider>`), so a vendor's shutdown reaches you with a registry sync. OpenAI's speech models
   are being shut down on a date the registry records and its replacement runs only on a Realtime API this tool does not
   call, so the `openai` voice needs an explicit `model` until that is built. Prices are not a setting: record each
   one with `tools/price_book.py` from the provider's pricing page; the quote reads it.
4. **Pronunciation layer.** `film/respell.json` maps caption spellings to engine spellings (names, loanwords,
   numerals, abbreviations). Invisible joiners (ZWNJ/ZWJ) are stripped for the engine by default (one engine read
   a joiner as an extra syllable). Keys starting with `_` are comments.
5. **Generate**: `python tools/voice/gen_vo.py` (every line not yet generated with the current provider) or by id,
   `... gen_vo.py 7Da 7Db` (the only way to redo a line that was generated but failed the check).
   Each line: pace from its `dir` (slowest/whisper 0.78, slow/tender 0.84, default 0.89, list/festive 0.93,
   brisk/comic 0.97, times `pace_scale`), silence trimmed with a small head and tail, -18 LUFS, peak ≤ 0.95.
6. **Verify**: every line is transcribed back and fuzzy-matched to the script (`voice.stt_provider`: `sarvam` by
   default for Indian languages, `openai` otherwise). The run ends with a CHECK list (similarity under the
   threshold) and an UNVERIFIED list (speech-to-text failed: `stt_err` or `sim: null` in `film/vo_check.json`).
   Listen to both, fix the respell or the text, regenerate by id. No line from either list goes into the mix
   unheard.
7. **Re-time**: `python film/timeline.py` (narration lengths drive every shot), then stills for changed shots.
8. Before a full regeneration use `--all`: previous takes are copied to `sound/vo_prev/` so any line can be
   reverted. Keep the old `vo_durs.json` too.

Before a voice is chosen, the `placeholder` provider writes silence of the estimated length so timing, captions
and the mix can be built early. Recorded human takes go in with `python tools/voice/import_vo.py <folder>`
(trimmed, loudness-matched, measured, marked "recorded" so generation never overwrites them).

## Directing the voice

- One breath per line. Split long sentences into `a`/`b` lines with a `gaps` value in shots.json.
- Punctuation is direction: commas for small pauses, a full stop for a settle; avoid exclamation marks (engines
  overact them).
- For engines that take instructions (OpenAI), `dir` is sent as the instruction; for others it sets pace only,
  so rewrite the text when the delivery is wrong.
- Comic timing comes from the gap before the punchline (`gaps`), not from the voice.
- A chant, verse or sung line in the narrator's voice: generate several takes, pick by ear, and check the words
  against the sourced text.

## Mistakes to avoid

- The provider's standard endpoint rejected a cloned voice id; clones had a separate endpoint. Read the
  provider's current docs before assuming field names (they drift).
- Judging voices on a laptop speaker: the client chooses on the playback device or a phone.
- Captions generated from the speech-to-text: captions always come from the script (correct spelling).
- Re-recording one line without re-running the timeline: the picture then drifts from the voice.

## References

- `references/voice-casting.md`: casting brief template, audition.json example, provider notes, respell examples
- `${CLAUDE_PLUGIN_ROOT}/docs/compliance-and-licensing.md` section 1 (voice licences) and 3.4 (synthetic media)
