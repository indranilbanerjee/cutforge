"""Music-first editing: find the beats, bars, phrases and accents of a music file so picture cuts, bells, hits and
sing-along word highlights land ON the music instead of near it (a real fix: lyric highlights were 0.7 s late
until they were aligned to measured onsets).

usage: python tools/mix/beats.py music.wav [--bpm 96] [--meter 4] [--phrase 4] [--snap 12.3 40.1 ...]
writes out/music/<stem>_beats.csv (kind, time, strength, index) and prints tempo, bar length and phrase starts.
  --bpm     hint when the detector picks half or double tempo (listen and decide)
  --meter   beats per bar (4 for most film and pop music, 3 for waltz time; Indian taals: use the beat grid and
            count the cycle yourself, e.g. 8 for keherwa, 16 for teentaal)
  --phrase  bars per phrase (4 is common; cut picture on phrase starts for the strongest feel)
  --snap    print the nearest beat, bar and phrase start to each time (to place a cut or a cue)
The phrase grid counts from the first detected downbeat: if phrases sound one bar off, shift by ear.
Free-tempo music (an alap, rubato piano, a drone) has no grid: use the onsets only, and your ears.
Method: spectral-flux onset envelope -> tempo by autocorrelation with a prior near 100 BPM -> beats by dynamic
programming (Ellis 2007) -> downbeat phase = the beat position with the strongest low-frequency onsets.
Needs only numpy and ffmpeg."""
import os, sys, csv, subprocess, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT

SR, HOP, NFFT = 22050, 512, 2048
FR = SR / HOP                                             # envelope frames per second (~43)


def load(path):
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                       capture_output=True)
    if r.returncode: sys.exit(f'cannot decode {path}')
    return np.frombuffer(r.stdout, np.float32)


def envelopes(y):
    n = 1 + max(0, len(y) - NFFT) // HOP
    win = np.hanning(NFFT).astype(np.float32)
    frames = np.lib.stride_tricks.as_strided(y, (n, NFFT), (y.strides[0] * HOP, y.strides[0]))
    S = np.log1p(30 * np.abs(np.fft.rfft(frames * win, axis=1)))
    flux = np.maximum(0, np.diff(S, axis=0, prepend=S[:1]))
    low = flux[:, :int(250 / (SR / NFFT))].sum(1)            # kick / bass / dhol range: where downbeats live
    env = flux.sum(1)
    k = np.ones(3) / 3
    env, low = np.convolve(env, k, 'same'), np.convolve(low, k, 'same')
    env = (env - env.mean()) / (env.std() + 1e-9); low = (low - low.mean()) / (low.std() + 1e-9)
    return np.maximum(env, 0), np.maximum(low, 0)


def onsets(env, gap=0.1):
    m = np.convolve(env, np.ones(int(FR)) / int(FR), 'same')   # adaptive threshold (1 s moving mean)
    pk = [i for i in range(2, len(env) - 2) if env[i] == env[i - 2:i + 3].max() and env[i] > m[i] + 0.5]
    out, last = [], -1e9
    for i in pk:
        if (i - last) / FR >= gap: out.append(i); last = i
    return out


def tempo(env, hint=None):
    lags = np.arange(int(FR * 60 / 200), int(FR * 60 / 50))
    ac = np.array([np.dot(env[:-l], env[l:]) for l in lags])
    bpm = 60 * FR / lags
    centre = hint or 100.0
    w = np.exp(-0.5 * (np.log2(bpm / centre) / (0.35 if hint else 0.9)) ** 2)
    return float(bpm[np.argmax(ac * w)])


def beat_track(env, bpm, tight=100.0):
    P = 60 * FR / bpm
    n = len(env); score = env.astype(np.float64).copy(); back = np.full(n, -1)
    lo, hi = int(round(P / 2)), int(round(2 * P))
    for t in range(hi, n):
        p = np.arange(t - hi, t - lo)
        cost = score[p] - tight * np.log((t - p) / P) ** 2
        j = int(np.argmax(cost)); score[t] = env[t] + cost[j]; back[t] = p[j]
    t = int(np.argmax(score[-int(P):])) + n - int(P)
    beats = []
    while t >= 0:
        beats.append(t); t = back[t]
    beats = beats[::-1]
    while beats and beats[0] - P >= 0:                   # the DP cannot start before 2 beats: walk back to the top
        c = int(round(beats[0] - P)); r = max(1, int(P / 4))
        w = env[max(0, c - r):c + r + 1]
        beats.insert(0, max(0, c - r) + int(np.argmax(w)))
    return beats


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('--'): sys.exit(__doc__)
    path = a[0]
    def opt(k, d):
        return type(d)(a[a.index(k) + 1]) if k in a else d
    hint = float(a[a.index('--bpm') + 1]) if '--bpm' in a else None
    meter, phrase = opt('--meter', 4), opt('--phrase', 4)
    snaps = [float(x) for x in a[a.index('--snap') + 1:] if not x.startswith('--')] if '--snap' in a else []
    y = load(path)
    env, low = envelopes(y)
    bpm = tempo(env, hint)
    bt = beat_track(env, bpm)
    phase = int(np.argmax([sum(low[b] for b in bt[k::meter]) for k in range(meter)]))
    bars = bt[phase::meter]
    phr = bars[::phrase]
    on = onsets(env)
    acc = [i for i in on if env[i] > np.percentile(env[on], 85)] if on else []
    t = lambda i: round((i * HOP + NFFT / 2) / SR, 3)          # frame index -> time at the window centre
    stem = os.path.splitext(os.path.basename(path))[0]
    d = os.path.join(OUT, 'music'); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, stem + '_beats.csv')
    with open(f, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['kind', 'time', 'strength', 'index'])
        for k, b in enumerate(bt): w.writerow(['beat', t(b), round(float(env[b]), 2), k])
        for k, b in enumerate(bars): w.writerow(['bar', t(b), round(float(low[b]), 2), k + 1])
        for k, b in enumerate(phr): w.writerow(['phrase', t(b), '', k + 1])
        for i in on: w.writerow(['onset', t(i), round(float(env[i]), 2), ''])
        for i in acc: w.writerow(['accent', t(i), round(float(env[i]), 2), ''])
    dur = len(y) / SR
    print(f'{stem}: {dur:.1f} s, ~{bpm:.1f} BPM (beat {60 / bpm:.3f} s, bar of {meter} = {meter * 60 / bpm:.2f} s), '
          f'{len(bt)} beats, first downbeat {t(bars[0]) if bars else "?"} s')
    print('phrase starts:', ', '.join(f'{t(b):.2f}' for b in phr[:24]) + (' ...' if len(phr) > 24 else ''))
    print('strongest accents:', ', '.join(f'{t(i):.2f}' for i in sorted(acc, key=lambda i: -env[i])[:12]))
    for s in snaps:
        nb = min(bt, key=lambda b: abs(t(b) - s)) if bt else None
        nbar = min(bars, key=lambda b: abs(t(b) - s)) if bars else None
        nph = min(phr, key=lambda b: abs(t(b) - s)) if phr else None
        print(f'snap {s:.2f}: beat {t(nb)}  bar {t(nbar)}  phrase {t(nph)}')
    print('wrote', os.path.relpath(f))
    print('check by ear: if the tempo is half or double what you tap, re-run with --bpm <what you tap>')


if __name__ == '__main__':
    main()
