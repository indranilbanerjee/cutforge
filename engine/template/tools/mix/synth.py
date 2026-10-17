"""Instruments and textures made from code, licence-free. Use them for what has no real recording:
drones, bells, abstract tones, a soft room tone. Real recordings (the client's own clips first, then a
licensed library) beat synthesis for anything physical (doors, vehicles, crowds, nature).

  tanpura(dur, sa=146.83)   Karplus-Strong tanpura drone, Pa-Sa-Sa-Sa' cycle (filtered: raw KS sounds hashy)
  bell(freq, dur)           temple/hand bell: inharmonic partials with their own decays
  thump(n, period)          soft low heartbeat-like thumps (lub-dub)
  riser(dur)                filtered-noise swell for transitions
  room(dur, db)             quiet pink room tone (keeps a projector speaker from sounding 'dead')
  pen(dur)                  dip-pen scratch on paper
usage: python tools/mix/synth.py   -> renders the default set into sound/synth/*.wav"""
import os, sys, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)


def _st(x): return np.stack([x, x], 1).astype(np.float32)
def _lp(x, hz, order=4): return sosfilt(butter(order, hz, 'low', fs=SR, output='sos'), x)
def _hp(x, hz, order=2): return sosfilt(butter(order, hz, 'high', fs=SR, output='sos'), x)
def _bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)


def ks_pluck(freq, dur, bright=0.5, decay=0.996):
    """Karplus-Strong string as one IIR comb (fast): y[n] = x[n] + decay/2 * (y[n-N] + y[n-N-1])"""
    from scipy.signal import lfilter
    n = int(dur * SR); N = max(2, int(SR / freq))
    x = np.zeros(n); burst = rng.uniform(-1, 1, N) * (0.5 + 0.5 * bright)
    x[:N] = _lp(np.concatenate([burst, burst]), 2000 + 6000 * bright)[:N]
    a = np.zeros(N + 2); a[0] = 1.0; a[N] = -decay / 2; a[N + 1] = -decay / 2
    return lfilter([1.0], a, x)


def tanpura(dur=60.0, sa=146.83, cycle=4.0, cutoff=2800):
    """four plucks per cycle: Pa (lower), Sa', Sa', Sa (lower); each string rings across the cycle"""
    notes = [sa * 0.75, sa * 2, sa * 2, sa]
    out = np.zeros(int(dur * SR) + SR * 6)
    t = 0.0; k = 0
    while t < dur:
        f = notes[k % 4]
        p = ks_pluck(f, cycle * 1.6, bright=0.35, decay=0.9993)
        p += 0.5 * ks_pluck(f * 1.003, cycle * 1.6, bright=0.3, decay=0.9993)     # jawari shimmer: a slightly detuned twin
        i = int(t * SR); out[i:i + len(p)] += p * (0.9 if k % 4 else 1.0)
        t += cycle / 4; k += 1
    out = _lp(out[:int(dur * SR)], cutoff)
    env = np.ones(len(out)); f = int(4 * SR); env[:f] = np.linspace(0, 1, f); env[-f:] = np.linspace(1, 0, f)
    out *= env
    return _st(out / (np.abs(out).max() + 1e-9) * 0.5)


def bell(freq=392.0, dur=9.0, bright=1.0):
    t = np.arange(int(dur * SR)) / SR
    parts = [(0.56, 0.6, 1.2), (1.0, 1.0, 1.0), (2.0, 0.6, 0.6), (2.76, 0.45, 0.45), (5.4, 0.25 * bright, 0.25), (8.93, 0.12 * bright, 0.15)]
    x = sum(a * np.sin(2 * np.pi * freq * r * t + rng.uniform(0, 6)) * np.exp(-t / (dur * d / 3)) for r, a, d in parts)
    x *= 1 + 0.15 * np.sin(2 * np.pi * 3.2 * t)                                     # slow beating
    att = int(0.004 * SR); x[:att] *= np.linspace(0, 1, att)
    return _st(x / np.abs(x).max() * 0.6)


def thump(n=4, period=0.8, freq=52.0):
    out = np.zeros(int((n * period + 1.0) * SR))
    def hit(amp):
        t = np.arange(int(0.35 * SR)) / SR
        f = freq * (1.6 * np.exp(-t * 30) + 1)
        return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
    for k in range(n):
        i = int(k * period * SR); a = hit(1.0); b = hit(0.6)
        out[i:i + len(a)] += a; j = i + int(0.24 * SR); out[j:j + len(b)] += b
    return _st(_lp(out, 180) * 0.8)


def riser(dur=2.5):
    n = int(dur * SR); x = rng.standard_normal(n)
    out = np.zeros(n); seg = int(0.05 * SR)
    for i in range(0, n, seg):
        p = i / n; lo = 300 + 3000 * p; out[i:i + seg] = _bp(x[i:i + seg], lo, min(lo * 2.2, 20000))
    env = np.linspace(0, 1, n) ** 2; env[-int(0.08 * SR):] *= np.linspace(1, 0, int(0.08 * SR))
    return _st(out * env / (np.abs(out).max() + 1e-9) * 0.5)


def room(dur=30.0, db=-48):
    n = int(dur * SR)
    l = _lp(rng.standard_normal(n), 900, 1) + 0.3 * _lp(rng.standard_normal(n), 3000, 1)
    r = _lp(rng.standard_normal(n), 900, 1) + 0.3 * _lp(rng.standard_normal(n), 3000, 1)
    g = 10 ** (db / 20) / (np.sqrt((l ** 2).mean()) + 1e-9)
    return np.stack([l * g, r * g], 1).astype(np.float32)


def pen(dur=0.25):
    n = int(dur * SR); x = _bp(rng.standard_normal(n), 1800, 9000)
    env = np.abs(np.sin(np.linspace(0, np.pi * rng.integers(2, 5), n))) * np.exp(-np.linspace(0, 3, n))
    return _st(x * env * 0.25)


DEFAULTS = {
    'tanpura_bed_60s': lambda: tanpura(60.0),
    'bell_g4': lambda: bell(392.0, 9.0),
    'bell_c4': lambda: bell(261.6, 11.0),
    'thump_x6': lambda: thump(6, 0.8),
    'riser_2s5': lambda: riser(2.5),
    'room_tone_30s': lambda: room(30.0),
    'pen_scratch': lambda: pen(0.25),
}

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from paths import SOUND
    d = os.path.join(SOUND, 'synth'); os.makedirs(d, exist_ok=True)
    for name, fn in DEFAULTS.items():
        f = os.path.join(d, name + '.wav')
        if os.path.exists(f) and '--force' not in sys.argv: continue
        sf.write(f, fn(), SR, subtype='PCM_24'); print('wrote', f)
