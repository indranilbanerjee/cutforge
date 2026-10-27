"""The film's sound, laid on the master timeline (film/timeline.json), mixed chapter by chapter into one master.

What is automatic:
  narration    every line from the timeline on bus 'vo' (polished, ducks everything else)
  clip sound   shots with "sound": true (or a dB number) get the real sound of their video media on bus 'dia'
  room tone    a quiet room bed under the whole film (config mix.room_tone, default on) so nothing drops to digital silence
What you write: film/cues.py -> build(S): music, ambience, effects, the client's own recordings, all placed with
  S.T(chapter, shot, sec) / S.VOAT(chapter, shot, line_index, sec) so they move when the timeline moves.

usage: python tools/mix/film_mix.py            all chapters -> out/mix/<chapter>.npy stems + out/film_mix.wav
       python tools/mix/film_mix.py e2          re-mix one chapter stem, then rebuild the master from all stems
                                                (chapters whose start or length moved since their last mix are re-mixed too)
Loudness: config mix.lufs (default -16 integrated, true peak -2 dBTP; small speakers/projectors). Online: -14. Broadcast: -23/-24.
After mixing: python tools/qc/qc_audio.py   (abrupt drops, dead air, speech-over-bed ratio)"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, json, importlib.util, numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, FILM, OUT, SOUND, VO_DIR, CFG, PUBLIC, load_json
from engine import SR, read, has_audio, Mix, master, VOFX, CLIPFX, chain, rev, lp, hp
from pedalboard import Pedalboard, HighpassFilter, LowpassFilter

TL = load_json(os.path.join(FILM, 'timeline.json'))
if TL is None: sys.exit('no film/timeline.json: run python film/timeline.py first')
MIXCFG = {'lufs': -16.0, 'tp': -2.0, 'room_tone': True, 'vo_gain': 4.0, 'music_bed_db': -9.0, **CFG.get('mix', {})}
MIN_FO = {'fx': 0.15, 'dia': 0.3, 'amb': 1.0, 'mus': 1.5, 'mus2': 1.5, 'voc': 0.5, 'song': 0.8}


class Sheet:
    """Cue sheet bound to the timeline. Times are global seconds on the film."""
    def __init__(self, tl):
        self.tl = tl; self.cues = []; self.warn = []
        self.CH = {c['name']: c for c in tl['chapters']}
        self.SH = {(c['name'], s['id']): s for c in tl['chapters'] for s in c['shots']}

    def T(self, ch, sid, sec=0.0):
        return self.CH[ch]['start'] + self.SH[(ch, sid)]['start'] + sec

    def VOAT(self, ch, sid, k, sec=0.0):
        return self.T(ch, sid, self.SH[(ch, sid)]['vo'][k][1] + sec)

    def VOEND(self, ch, sid, k, sec=0.0):
        v = self.SH[(ch, sid)]['vo'][k]; return self.T(ch, sid, v[1] + v[2] + sec)

    def dur(self, ch, sid=None):
        return self.SH[(ch, sid)]['dur'] if sid else self.CH[ch]['dur']

    def cue(self, bus, path, at, src=0.0, dur=None, gain=0.0, fi=0.02, fo=None, fx=None, pan=0.0, hard=False, required=True):
        if not os.path.isabs(path): path = os.path.join(ROOT, path)
        if not os.path.exists(path):
            msg = f'missing sound: {os.path.relpath(path, ROOT)}'
            if required: self.warn.append(msg)
            return
        fo = MIN_FO.get(bus, 0.1) if fo is None else fo
        if fo < MIN_FO.get(bus, 0.05) and not hard:
            self.warn.append(f'fade-out {fo}s on {bus} {os.path.basename(path)} at {at:.2f}s raised to {MIN_FO[bus]}s (pass hard=True for an intended cut)')
            fo = MIN_FO[bus]
        self.cues.append((bus, path, src, dur, at, gain, fi, fo, fx, pan))

    def sfx(self, path, at, src=0.0, dur=None, gain=-12.0, fi=0.005, fo=None, fx=None, pan=0.0, **k): self.cue('fx', path, at, src, dur, gain, fi, fo, fx, pan, **k)
    def amb(self, path, at, src=0.0, dur=None, gain=-22.0, fi=0.8, fo=None, fx=None, **k): self.cue('amb', path, at, src, dur, gain, fi, fo, fx, **k)
    def dia(self, path, at, src=0.0, dur=None, gain=-6.0, fi=0.15, fo=None, fx=CLIPFX, **k): self.cue('dia', path, at, src, dur, gain, fi, fo, fx, **k)
    def mus(self, path, at, src=0.0, dur=None, gain=-4.0, fi=0.6, fo=None, bus='mus', **k): self.cue(bus, path, at, src, dur, gain, fi, fo, None, **k)
    def voc(self, path, at, src=0.0, dur=None, gain=-6.0, fi=0.3, fo=None, fx=None, **k): self.cue('voc', path, at, src, dur, gain, fi, fo, fx, **k)

    def loop(self, bus, path, at, dur, gain, xfade=1.0, **k):
        """repeat a bed to cover dur seconds with crossfades (for drones, room tone, ambience)"""
        if not os.path.isabs(path): path = os.path.join(ROOT, path)
        if not os.path.exists(path): self.warn.append(f'missing sound: {path}'); return
        L = len(read(path)) / SR; t = 0.0
        while t < dur:
            seg = min(L, dur - t + xfade)
            self.cue(bus, path, at + t, 0.0, seg, gain, xfade if t > 0 else 1.5, xfade if t + seg < dur else 2.0, hard=True)
            t += max(1.0, L - xfade)


def auto(S):
    vids = ('.mp4', '.mov', '.m4v', '.webm')
    for c in TL['chapters']:
        for s in c['shots']:
            sp = s.get('spec', {})
            snd = sp.get('sound')
            if not snd: continue
            gain = snd if isinstance(snd, (int, float)) and not isinstance(snd, bool) else -10.0
            media = [m if isinstance(m, dict) else {'src': m} for m in sp.get('media', [])]
            media = [m for m in media if m['src'].lower().endswith(vids)]
            pans = {1: [0.0], 2: [-0.3, 0.3], 3: [-0.45, 0.0, 0.45]}.get(len(media), [0.0] * len(media))
            for k, m in enumerate(media):
                p = os.path.join(PUBLIC, m['src'])
                if os.path.exists(p) and has_audio(p):
                    S.dia(p, S.T(c['name'], s['id']), m.get('from', 0.0), s['dur'], gain - (4 if len(media) > 1 else 0), 0.25, 0.5, pan=pans[k])
    if MIXCFG['room_tone']:
        rt = os.path.join(SOUND, 'synth', 'room_tone_30s.wav')
        if os.path.exists(rt): S.loop('amb', rt, 0.0, TL['total'] + 2.0, 0.0, 2.0)
        else: S.warn.append('room tone missing: run python tools/mix/synth.py')


def mix_chapter(S, name):
    c = S.CH[name]
    last = TL['chapters'][-1]['name'] == name
    mine = [q for q in S.cues if (c['start'] - 0.01 <= q[4] < c['start'] + c['dur'] - 0.01) or (q[4] < 0.01 and c['start'] == 0)
            or (last and q[4] >= c['start'] + c['dur'] - 0.01)]
    w0, w1 = c['start'] - 2.0, c['start'] + c['dur'] + 14.0           # tails ring into the next chapter (stems overlap-add)
    for bus, path, src, dur, at, *_ in mine:                           # a long cue (a music bed across chapters) widens the
        w1 = max(w1, at + len(read(path, src, dur)) / SR + 0.5)        # window instead of being cut off at its edge
    m = Mix(w1 - w0)
    for cc in TL['chapters']:
        for s in cc['shots']:
            for p, at, d in s['vo']:
                g = cc['start'] + s['start'] + at
                if g + d < w0 or g > w1: continue
                f = os.path.join(VO_DIR, p + '.wav')
                if not os.path.exists(f): S.warn.append(f'no narration file for {p}'); continue
                a = read(f)
                if cc['name'] == name: m.add(a, g - w0, MIXCFG['vo_gain'], 0.01, 0.06, 'vo', fx=VOFX)
                m.add(a, g - w0, 0.0, 0.01, 0.06, 'key')
    for bus, path, src, dur, at, gain, fi, fo, fx, pan in mine:
        a = read(path, src, dur)
        m.add(a, at - w0, gain, fi, fo, bus, pan=pan, fx=fx)
    for b in ('mus', 'mus2'):
        if b in m.bus:
            m.bus[b] *= 10 ** (MIXCFG['music_bed_db'] / 20)
            m.duck(b, 'dia', -8, 0.05, 0.5, 0.015)
            m.duck(b, 'song', -30, 0.3, 1.0, 0.005)
            m.duck(b, 'key', -17, 0.08, 0.7, 0.01)              # music sits ~12+ dB under the narration
    for b, d in (('amb', -10), ('dia', -14), ('fx', -6), ('voc', -10), ('song', -12)):
        if b in m.bus: m.duck(b, 'key', d, 0.06, 0.5, 0.01)
    report = ''
    if 'vo' in m.bus and len(m.bus) > 2:
        bp = Pedalboard([HighpassFilter(200), LowpassFilter(4000)])
        others = sum(v for k, v in m.bus.items() if k not in ('vo', 'key'))
        rat = []
        for s_ in c['shots']:
            for pid, at, d in s_['vo']:
                i0 = int((c['start'] + s_['start'] + at - w0) * SR); i1 = i0 + int(d * SR)
                v = bp(m.bus['vo'][i0:i1].T.copy(), SR); o = bp(others[i0:i1].T.copy(), SR)
                rv, ro = np.sqrt((v ** 2).mean()), np.sqrt((o ** 2).mean())
                if rv > 1e-6: rat.append((20 * np.log10((rv + 1e-9) / (ro + 1e-9)), pid))
        if rat:
            rat.sort()
            report = 'speech over bed: median %.1f dB, lowest %s' % (np.median([r for r, _ in rat]), ', '.join(f'{p_} {r:.1f}' for r, p_ in rat[:3]))
    del m.bus['key']
    return w0, sum(m.bus.values()) if m.bus else np.zeros((m.n, 2), np.float32), report


def stale():
    """chapters whose saved stem was mixed against a different start or length than the current timeline"""
    out = []
    for c in TL['chapters']:
        j = os.path.join(OUT, 'mix', c['name'] + '.json')
        meta = json.load(open(j)) if os.path.exists(j) else {}
        if abs(meta.get('start', -1) - c['start']) > 1e-3 or abs(meta.get('dur', -1) - c['dur']) > 1e-3: out.append(c['name'])
    return out


def main(only=None):
    if only:                                   # a chapter whose start or length moved must be re-mixed too, or its audio drifts
        extra = [c for c in stale() if c not in only]
        if extra: print('  timeline moved since these were mixed, re-mixing them too:', ' '.join(extra)); only = list(only) + extra
    S = Sheet(TL)
    auto(S)
    cf = os.path.join(FILM, 'cues.py')
    if os.path.exists(cf):
        spec = importlib.util.spec_from_file_location('cues', cf); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        mod.build(S)
    for w in sorted(set(S.warn)): print('  !', w)
    md = os.path.join(OUT, 'mix'); os.makedirs(md, exist_ok=True)
    for name in (only or [c['name'] for c in TL['chapters']]):
        w0, out, rep = mix_chapter(S, name)
        np.save(os.path.join(md, name + '.npy'), out.astype(np.float32))
        json.dump({'w0': w0, 'start': S.CH[name]['start'], 'dur': S.CH[name]['dur']}, open(os.path.join(md, name + '.json'), 'w'))
        print(f'mixed {name:12} {len(out) / SR:7.1f}s peak {float(np.abs(out).max()):.2f}  {rep}', flush=True)
    n = int(TL['total'] * SR); M = np.zeros((n, 2), np.float32)
    for c in TL['chapters']:
        f = os.path.join(md, c['name'] + '.npy')
        if not os.path.exists(f): print('  (no stem yet)', c['name']); continue
        seg = np.load(f, mmap_mode='r'); w0 = json.load(open(f[:-4] + '.json'))['w0']
        i0 = int(round(w0 * SR)); j0 = 0
        if i0 < 0: j0 = -i0; i0 = 0
        i1 = min(n, i0 + len(seg) - j0)
        M[i0:i1] += seg[j0:j0 + i1 - i0]
    raw = os.path.join(OUT, 'film_mix_raw.wav'); sf.write(raw, M, SR, subtype='FLOAT'); del M
    final = os.path.join(OUT, 'film_mix.wav')
    master(raw, final, MIXCFG['lufs'], MIXCFG['tp']); os.remove(raw)
    print('master', final, f'(target {MIXCFG["lufs"]} LUFS, TP {MIXCFG["tp"]})')


if __name__ == '__main__':
    main(sys.argv[1:] or None)
