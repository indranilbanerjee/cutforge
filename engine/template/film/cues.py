"""The project's cue sheet. Narration, clip sound (shots with "sound": true) and room tone are placed automatically
by tools/mix/film_mix.py; this file adds everything else. Place every cue relative to the timeline:
    S.T(chapter, shot, sec)          a second inside a shot
    S.VOAT(chapter, shot, k, sec)    relative to the start of line k in that shot   (S.VOEND: its end)
so cues follow when narration or shot lengths change.

Cue helpers (bus, default gain, minimum fade-out enforced so nothing stops abruptly):
    S.mus(path, at, src, dur, gain)      music bed, ducks ~17 dB under narration, fade-out >= 1.5 s
    S.amb(path, at, src, dur, gain)      ambience, fade-out >= 1 s
    S.sfx(path, at, src, dur, gain)      effects, fade-out >= 0.15 s
    S.dia(path, at, src, dur, gain)      the client's clip sound / dialogue, fade-out >= 0.3 s
    S.voc(path, at, ...)                 sung or hummed voice (the client's own recordings)
    S.loop(bus, path, at, dur, gain)     repeat a bed with crossfades
Pass hard=True only for an intended hard stop. Paths are relative to the project root.
Sound sources, in order of preference: the client's own clips and recordings > licensed library (log the licence in
sources.md) > synthesised (tools/mix/synth.py) for drones, bells and abstract tones only.

Craft rules: sound leads picture (start the next shot's sound ~0.5 s before the cut); 1.5 s of quiet after an
emotional line; never let a chapter end in silence: ring out (bell, reverb tail) or pre-lap the next chapter."""
from pedalboard import Pedalboard, LowpassFilter, HighpassFilter, Reverb, PitchShift

SY = 'sound/synth/'


def build(S):
    # ---- intro: a heartbeat in the dark under the title, a bell as the first picture lands, a drone bed ----
    S.sfx(SY + 'thump_x6.wav', S.T('intro', '1T', 0.3), gain=-10, fo=0.8)
    S.sfx(SY + 'bell_g4.wav', S.VOAT('intro', '1A', 0, -0.4), gain=-20, fo=3.0)
    S.amb(SY + 'tanpura_bed_60s.wav', S.T('intro', '1A', -0.5), 0.0, S.dur('intro') - S.SH[('intro', '1T')]['dur'] + 3.0, gain=-26, fi=2.0, fo=3.0)
    # ---- into the hand-built chapter: a riser that peaks on the cut (sound leads picture) ----
    S.sfx(SY + 'riser_2s5.wav', S.T('example', 'E1', -2.3), gain=-24, fo=0.3)
    for k in range(6):
        S.sfx(SY + 'pen_scratch.wav', S.VOAT('example', 'E1', 1, 0.1 + 0.14 * k), gain=-30, pan=-0.2 + 0.08 * k)
    S.sfx(SY + 'bell_c4.wav', S.VOEND('example', 'E2', 0, 0.4), gain=-22, fo=4.0)     # rings across the chapter cut
    # ---- story: drone returns under the black-and-white picture, a low bell on the last card ----
    S.amb(SY + 'tanpura_bed_60s.wav', S.T('story', '2C', -1.0), 0.0, S.dur('story', '2C') + S.dur('story', '3A') + 1.0, gain=-27, fi=2.5, fo=2.5)
    S.sfx(SY + 'bell_c4.wav', S.VOEND('story', '3A', 0, 0.6), gain=-18, fo=4.0)
