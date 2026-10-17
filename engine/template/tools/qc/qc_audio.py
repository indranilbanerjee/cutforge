"""Audio QC on the master mix (or any wav/mp4), mapped back to shots on the timeline.
Finds what viewers call "abrupt":
  DROP      sound falls from audible (> -32 dBFS) to near-silence (< -48) within ~0.3 s, NOT at the end of a narration line
  DEAD AIR  more than 1.5 s under -55 dBFS (on a projector or TV this reads as a glitch)
  CUT TAIL  a drop within 0.4 s after a shot cut (a sound chopped by the edit)
Also prints integrated loudness and true peak (ffmpeg ebur128) against the target in config mix.lufs (flag: > 1 LU off).
usage: python tools/qc/qc_audio.py [out/film_mix.wav] [--quiet]     exit code 1 when anything is flagged"""
import os, sys, json, subprocess, re, numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT, FILM, CFG, load_json

src = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(OUT, 'film_mix.wav'))
TL = load_json(os.path.join(FILM, 'timeline.json'))
if src.lower().endswith(('.mp4', '.mov', '.mkv')):
    wav = os.path.join(OUT, '_qc_audio.wav')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', '48000', wav], check=True); src_wav = wav
else:
    src_wav = src
x, sr = sf.read(src_wav, dtype='float32', always_2d=True); x = x.mean(1)
hop = int(0.01 * sr); n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12) + 1e-9)
vo_ends = np.array([c['start'] + s['start'] + at + d for c in TL['chapters'] for s in c['shots'] for _, at, d in s['vo']]) if TL else np.array([])
cuts = [(c['name'], s['id'], c['start'] + s['start'] + s['dur']) for c in TL['chapters'] for s in c['shots']] if TL else []
chap_ends = {round(c['start'] + c['dur'], 2) for c in TL['chapters']} if TL else set()


def where(t):
    if not cuts: return ''
    c = min(cuts, key=lambda c: abs(c[2] - t))
    return f"near {c[0]}/{c[1]} cut at {fmt(c[2])} ({t - c[2]:+.2f}s){'  [chapter end]' if round(c[2], 2) in chap_ends else ''}"


def fmt(t): return f'{int(t // 60)}:{t % 60:05.2f}'


flags = []
last = -10
for i in range(50, n - 50):
    before = db[i - 25:i - 5].mean(); after = db[i + 3:i + 30].max()
    if before > -32 and after < -48:
        t = i / 100
        if len(vo_ends) and np.min(np.abs(vo_ends - t)) < 0.5: continue
        if i - last > 100:
            last = i
            near_cut = cuts and min(abs(c[2] - t) for c in cuts) < 0.4
            flags.append(('CUT TAIL' if near_cut else 'DROP', t, f'{before:.0f} dB -> {after:.0f} dB  {where(t)}'))
quiet = db < -55; i = 0
while i < n:
    if quiet[i]:
        j = i
        while j < n and quiet[j]: j += 1
        if j - i > 150: flags.append(('DEAD AIR', i / 100, f'{(j - i) / 100:.1f}s  {where(i / 100)}'))
        i = j
    else:
        i += 1
flags.sort(key=lambda f: f[1])
r = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', src_wav, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
target = CFG.get('mix', {}).get('lufs', -16.0)
if I and abs(float(I[-1]) - target) > 1.0:
    flags.append(('LOUDNESS', 0.0, f'integrated {I[-1]} LUFS is more than 1 LU from the target {target}: check for long silences or a single loud hit'))
if '--quiet' not in sys.argv:
    for kind, t, msg in flags: print(f'{kind:9} {fmt(t)}  {msg}')
print(f'{len(flags)} flags | integrated {I[-1] if I else "?"} LUFS (target {target}) | true peak {TP[-1] if TP else "?"} dBTP')
if TL:
    rep = {'flags': [{'kind': k, 't': round(t, 2), 'msg': m} for k, t, m in flags], 'lufs': float(I[-1]) if I else None, 'tp': float(TP[-1]) if TP else None}
    json.dump(rep, open(os.path.join(OUT, 'qc_audio.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
sys.exit(1 if flags else 0)
