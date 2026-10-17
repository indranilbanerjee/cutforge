# Cue recipes for film/cues.py

All times through the timeline helpers, so cues follow narration changes. Paths are relative to the project root.

## Opening in the dark

```python
S.sfx('sound/synth/thump_x6.wav', S.T('open', '1T', 0.3), gain=-10, fo=0.8)          # a heartbeat before picture
S.sfx('sound/synth/bell_g4.wav', S.VOAT('open', '1A', 0, -0.4), gain=-20, fo=3.0)     # bell just before the first word
S.amb('sound/synth/tanpura_bed_60s.wav', S.T('open', '1A', -0.5), 0.0, S.dur('open') + 3.0, gain=-26, fi=2.0, fo=3.0)
```

## Chapter bridge (ring-out across the cut)

```python
S.sfx('sound/synth/bell_c4.wav', S.VOEND('e1', '6J', 0, 0.4), gain=-22, fo=4.0)   # rings into e2
S.amb('sound/lib/evening_birds.wav', S.T('e2', '7A', -0.5), 0.0, 12.0, gain=-24)   # e2's world pre-laps 0.5 s
```

## Riser into a reveal

```python
S.sfx('sound/synth/riser_2s5.wav', S.T('e3', '9C', -2.3), gain=-24, fo=0.3)       # peaks on the cut
```

## The client's real sound under a still

```python
# a conch found by sound_events.py in a clip at 12.4 s, 3.2 s long, under a photo of that morning
S.dia('public/media/20230403_0612.mp4', S.T('e1', '6E', 0.5), src=12.4, dur=3.2, gain=-8, fo=0.8)
```

## Music bed for a chapter, cut to its phrases

```python
# beats.py said: phrase starts at 0.49, 10.49, 20.48 s in the music; the chapter's big reveal (shot 9C) should
# land on phrase 3, so start the music 20.48 s before 9C begins
S.mus('sound/music/e3_theme.wav', S.T('e3', '9C', -20.48), 0.0, S.dur('e3') + 22.0, gain=-4, fi=1.0, fo=3.0)
```

## Montage of clips with their own sound

Set `"sound": true` on each shot in shots.json (the mixer lays each clip's audio, panned for triptychs) and keep
music out of the montage or very low; the real sound is the point.

## Sing-along

1. Record or source the song; run `beats.py` on it; list word onsets (`onset` rows) for the lyric lines.
2. Put the song on the `song` bus (music ducks under it): `S.cue('song', 'sound/voc/song.wav', S.T('court', '11E', 0.2))`.
3. Drive word highlights in the custom chapter from those onset times (convert to frames with the shot start),
   not from estimates.

## Interval and countdown (long films with children)

A short card + music bed + a ticking motif; resume with the same motif. Pause the narration; let the room talk.

## Ending

The motif returns (the engine, the heartbeat, the bell); the music resolves on a held chord with a 3-4 s
fade; 2 s of room tone on black before the file ends (projectors and TVs cut the last frames abruptly
otherwise).

## Room tone

Automatic (config `mix.room_tone`). For real rooms, record 30 s of the client's room or take a quiet stretch
from a clip and loop it with `S.loop('amb', path, 0.0, S.tl['total'] + 2.0, -30)`.

## Long cues across chapters

A music bed may start in one chapter and run into the next; the chapter's mix window widens to fit it, so it is
never cut at a chapter edge. Ducking still follows every narration line it plays under. If a chapter is later
re-mixed alone (`film_mix.py e3`), re-mix the chapter where the long cue STARTS too.
