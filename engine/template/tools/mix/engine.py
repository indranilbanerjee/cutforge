"""Mixing engine: decode any file with ffmpeg, place it on named buses with fades/gain/pan/effects,
automate and duck buses, render with loudness normalisation. 48 kHz stereo float32 throughout."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, subprocess, numpy as np, soundfile as sf
from pedalboard import (Pedalboard, Reverb, HighpassFilter, LowpassFilter, PitchShift, Compressor, Gain, LowShelfFilter,
                        HighShelfFilter, PeakFilter, Limiter)

SR = 48000
_cache = {}


def read(path, start=0.0, dur=None):
    """Decode path[start:start+dur] to (n, 2) float32 at 48 kHz. Any format ffmpeg reads (wav, mp3, m4a, mp4 video sound)."""
    k = (path, round(start, 4), None if dur is None else round(dur, 4))
    if k in _cache: return _cache[k].copy()
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0.0, start)}', '-i', path]
    if dur: cmd += ['-t', f'{dur}']
    cmd += ['-vn', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-']
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f'cannot decode {path}: {r.stderr.decode(errors="ignore")[:200]}')
    a = np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()
    _cache[k] = a
    return a.copy()


def has_audio(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', path],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


class Mix:
    def __init__(self, dur):
        self.n = int(dur * SR); self.bus = {}

    def add(self, a, at, gain_db=0.0, fi=0.01, fo=0.05, bus='fx', pan=0.0, fx=None):
        a = a.copy()
        if fx is not None: a = fx(a.T.copy(), SR).T.copy()
        n = len(a)
        if n == 0: return
        fi_n, fo_n = max(1, int(fi * SR)), max(1, int(fo * SR))
        env = np.ones(n, np.float32)
        env[:min(fi_n, n)] = np.linspace(0, 1, min(fi_n, n)) ** 1.5
        env[-min(fo_n, n):] *= np.linspace(1, 0, min(fo_n, n)) ** 1.5
        a *= env[:, None] * (10 ** (gain_db / 20))
        if pan:
            a[:, 0] *= np.sqrt(1 - pan) if pan > 0 else 1
            a[:, 1] *= np.sqrt(1 + pan) if pan < 0 else 1
        i0 = int(at * SR)
        if i0 < 0: a = a[-i0:]; i0 = 0
        i1 = min(self.n, i0 + len(a))
        if i1 <= i0: return
        buf = self.bus.setdefault(bus, np.zeros((self.n, 2), np.float32))
        buf[i0:i1] += a[:i1 - i0]

    def automate(self, bus, pts):
        """volume automation: pts = [(t, db), ...], linear in dB between points"""
        if bus not in self.bus: return
        t = np.arange(self.n) / SR; ts, ds = zip(*pts)
        self.bus[bus] *= (10 ** (np.interp(t, ts, ds) / 20))[:, None].astype(np.float32)

    def duck(self, bus, key_bus, depth_db=-7, attack=0.04, release=0.35, thresh=0.02):
        """lower `bus` while `key_bus` has signal (sidechain ducking)"""
        if bus not in self.bus or key_bus not in self.bus: return
        k = np.abs(self.bus[key_bus]).max(1)
        win = int(0.02 * SR); k = np.convolve(k, np.ones(win) / win, 'same')
        on = (k > thresh).astype(np.float32)
        a_c, r_c = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
        e = np.zeros_like(on); v = 0.0
        for i in range(0, len(on), 256):
            tgt = on[i:i + 256].max()
            c = a_c if tgt > v else r_c
            v = tgt + (v - tgt) * (c ** 256)
            e[i:i + 256] = v
        self.bus[bus] *= (10 ** ((depth_db * e) / 20))[:, None]


def master(raw_wav, out_wav, lufs=-16.0, tp=-2.0, lra=16):
    """Two-pass EBU R128 loudness normalisation (measure, then apply linearly when the true-peak budget allows,
    so the integrated loudness lands on target), then a limiter; 24-bit wav out."""
    import json, re
    lim = 10 ** ((tp - 0.1) / 20)
    probe = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', raw_wav, '-af',
                            f'highpass=f=28,loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json', '-f', 'null', '-'],
                           capture_output=True, text=True).stderr
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', probe, re.S)
    af = f'highpass=f=28,loudnorm=I={lufs}:TP={tp}:LRA={lra}'
    if m:
        j = json.loads(m.group(0))
        af += (f":measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
               f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', raw_wav, '-af', af + f',aresample=48000,alimiter=limit={lim:.3f}:level=false',
                    '-ar', '48000', '-c:a', 'pcm_s24le', out_wav], check=True)


def rev(room=0.6, wet=0.25, damp=0.5, width=1.0):
    return Pedalboard([Reverb(room_size=room, wet_level=wet, dry_level=1 - wet * 0.6, damping=damp, width=width)])
def lp(hz): return Pedalboard([LowpassFilter(cutoff_frequency_hz=hz)])
def hp(hz): return Pedalboard([HighpassFilter(cutoff_frequency_hz=hz)])
def chain(*p): return Pedalboard(list(p))
def pitch(st): return Pedalboard([PitchShift(semitones=st)])

# narration polish: rumble cut, a little body and presence, gentle compression, a touch of room
VOFX = Pedalboard([HighpassFilter(75), LowShelfFilter(cutoff_frequency_hz=180, gain_db=1.5), PeakFilter(cutoff_frequency_hz=3200, gain_db=1.5, q=0.8),
                   Compressor(threshold_db=-22, ratio=2.5, attack_ms=6, release_ms=120), Reverb(room_size=0.22, wet_level=0.06, damping=0.7)])
# phone-clip dialogue: cut rumble, even out levels, lift
CLIPFX = Pedalboard([HighpassFilter(100), Compressor(threshold_db=-28, ratio=3, attack_ms=5, release_ms=150), Gain(gain_db=6)])
