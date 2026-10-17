---
name: sound-design
description: "Design the sound: real sound first, music-first cuts, cue sheet, mix and loudness. \"it stops abruptly\""
user-invocable: true
---

# Sound design: sound leads, picture follows, nothing stops abruptly

Viewers forgive a soft picture; they do not forgive bad sound. In a real production the client's main note on
the final cut was "abrupt stops in many places", and an audit found the mechanisms: a title line longer than its
fixed shot, about 2.5 s of dead air at most chapter ends, then the next sound cut off 0.3 s in. Every rule below
exists to stop that class of problem, and the tools enforce most of them.

## Sources, in order of preference

1. **The client's own sound**: the real sound inside their clips (`python tools/archive/sound_events.py` finds
   sustained tones like a conch or a bell, hits like drums and claps, laughter and chatter), and recordings they
   make for the film (hums, lullabies, ritual sounds, blessings; recording guides in the `video-brief` inbox
   README). A family's own conch blown on the morning of a ceremony beats any library conch, which may be from
   another tradition and sound wrong.
2. **Licensed libraries**, chosen by use: CC0 packs (e.g. Kenney) for anything; personal/educational-only
   archives (e.g. BBC Sound Effects RemArc) for private family films only, never client work. Log every file's
   source and licence in `sources.md`.
3. **Music**: public-domain melodies played fresh (a traditional tune or a pre-1929 composition, new
   performance), licensed library music (keep the licence PDF), commissioned music, or AI music whose terms
   allow the use (some carry watermarks such as SynthID; check commercial terms per tool). Never a commercial
   song without sync and master licences, even in a private film that may later be posted.
4. **Synthesis** (`python tools/mix/synth.py`): drones (tanpura bed), bells, low thumps, risers, room tone,
   pen scratches. Only for what has no real recording; filter it (a Karplus-Strong tanpura was hashy until a
   ~2.8 kHz low-pass) and check the spectrum and your ears.

## Workflow

1. **Spot the film** with the storyboard page: per chapter, the music (or none), the real sounds, the effects,
   where the room should hear silence. Write it as comments in `film/cues.py` first.
2. **Music-first edit.** Pick one piece per chapter and keep it unbroken; cut picture to its phrases
   (`python tools/mix/beats.py <music> --snap <t>` gives beats, bars, phrase starts and accents). Land hits and
   bells on accents; tune bells to the key; edit music only on matching beats. A score chopped at every cut
   sounded broken in a look test; one piece with picture cut to it fixed it.
3. **Write the cue sheet** in `film/cues.py` → `build(S)`. Place every cue relative to the timeline so it
   moves when narration changes:
   - `S.T(chapter, shot, sec)`: a second inside a shot; `S.VOAT(chapter, shot, k, sec)` / `S.VOEND(...)`:
     relative to the start / end of line k; `S.dur(chapter[, shot])`.
   - `S.mus`, `S.amb`, `S.sfx`, `S.dia` (clip sound, with clip EQ), `S.voc` (sung or hummed voice),
     `S.loop(bus, path, at, dur, gain)` for beds. Each has a default gain and a minimum fade-out (effects
     0.15 s, dialogue 0.3 s, ambience 1 s, music 1.5 s) raised automatically; `hard=True` only for an intended
     hard stop.
   - Automatic: narration (polished, ducks everything), clip sound for shots with `"sound": true`, and a quiet
     room tone under the whole film so nothing drops to digital silence.
4. **Bridge every chapter boundary**: a ring-out (bell, reverb tail, held note) across the cut or a pre-lap of
   the next chapter's sound ~0.5 s early. Never silence-then-sound. Chapter stems are mixed with a window from
   -2 s to +14 s, so tails ring into the next chapter.
5. **Mix**: `python tools/mix/film_mix.py` (all) or `... film_mix.py e2` (one chapter, then the master is
   rebuilt from all stems; chapters whose start or length moved since their last mix are re-mixed too). Levels: narration on top; music bed -9 dB and ducked ~17 dB under narration;
   ambience -10, clip dialogue -14, effects -6 under narration. Two-pass loudness normalisation to the target
   in config `mix` (`lufs`, `tp`).
6. **Check**: `python tools/qc/qc_audio.py` flags DROP (audible to near-silent within 0.3 s, not at a line end),
   CUT TAIL (a drop right after a cut), DEAD AIR (> 1.5 s under -55 dBFS) and loudness > 1 LU off target; the
   mixer prints speech-over-bed per chapter (keep the lowest lines ≥ ~10 dB). Fix every flag or record why it is
   intended. Then listen on the delivery device, not only headphones.

## Loudness by destination

| Destination | Integrated | True peak |
|---|---|---|
| Small speaker, projector, TV in a room | -16 LUFS | -2 dBTP |
| YouTube, Instagram, most streaming | -14 LUFS | -1 dBTP |
| Broadcast EU (EBU R128); Indian broadcasters: ask for their spec | -23 LUFS | -1 dBTP |
| Broadcast US (ATSC A/85) | -24 LKFS | -2 dBTP |
`tools/deliver/encode.py` presets re-normalise per destination; mix once at the main target.

## Craft rules that held up

- Sound leads picture: the next shot's sound starts ~0.5 s before its cut.
- 1.5 s of quiet (room tone only) after an emotional line; music never swells under words.
- Real sound comes up full when the narrator is silent; let a laugh or a conch play out.
- Sing-alongs: word highlights aligned to measured onsets, not estimates (they were 0.7 s late once).
- Small speakers: nothing important below 120 Hz; presence around 2-4 kHz for narration; avoid harsh 6-8 kHz.
- A repeated sound motif (a heartbeat, an engine, a bell) at each chapter break ties the film together.

## References

- `references/cue-recipes.md`: cue sheet recipes (openings, bridges, sing-along, montage, interval, ending)
- `${CLAUDE_PLUGIN_ROOT}/docs/compliance-and-licensing.md` sections 1 and 3.4 (licences, music)
- `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md` section E
