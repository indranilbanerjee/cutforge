"""Find the real sounds hiding in the client's own clips: sustained tones (conch, bell, whistle, a held note),
loud transients (drums, claps, firecrackers), and lively voiced stretches (laughter, chatter). These beat any
library effect because they are the sound of that day.
usage: python tools/archive/sound_events.py [--from 2023-01] [--to 2026-12] [--files a.mp4 ...]
writes out/archive/sound_events.csv: file, time, kind, length, level. Listen before using; label in sources.md."""
import os, sys, csv, subprocess, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT

a = sys.argv[1:]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
if '--files' in a:
    files = a[a.index('--files') + 1:]
else:
    files = [r['path'] for r in csv.DictReader(open(os.path.join(OUT, 'archive', 'inventory.csv'), encoding='utf-8-sig'))
             if r['kind'] in ('video', 'audio') and (not opt('--from') or r['date'][:7] >= opt('--from')) and (not opt('--to') or r['date'][:7] <= opt('--to'))]
SR = 16000; HOP = 512; NF = 2048
rows = []
for p in files:
    pcm = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    y = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    if len(y) < NF * 4: continue
    n = (len(y) - NF) // HOP
    idx = np.arange(NF)[None, :] + HOP * np.arange(n)[:, None]
    fr = y[idx] * np.hanning(NF)[None, :]
    sp = np.abs(np.fft.rfft(fr, axis=1)) + 1e-9
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    flat = np.exp(np.log(sp).mean(1)) / sp.mean(1)                       # spectral flatness: low = tonal
    peakf = np.argmax(sp, 1) * SR / NF
    t = np.arange(n) * HOP / SR
    # thresholds relative to this file (phone clips are often recorded quietly)
    p50, p60, p75 = np.percentile(db, [50, 60, 75])
    # sustained tone: tonal, audible, steady pitch, for > 0.8 s
    tonal = (flat < 0.05) & (db > max(p50, -50))
    i = 0
    while i < n:
        if tonal[i]:
            j = i
            while j < n and tonal[j] and abs(peakf[j] - peakf[i]) < 40: j += 1
            if t[min(j, n - 1)] - t[i] > 0.8:
                rows.append({'file': p, 't': round(t[i], 2), 'kind': f'tone ~{peakf[i]:.0f} Hz', 'len': round(t[min(j, n - 1)] - t[i], 2), 'db': round(float(db[i:j].mean()), 1)})
            i = j
        else:
            i += 1
    # transients: a rise of > 12 dB within ~100 ms to an audible level (drums, claps, firecrackers)
    prev = np.minimum.reduce([np.roll(db, s_) for s_ in (1, 2, 3)]); prev[:3] = db[:3]
    jump = db - prev
    for k in np.where((jump > 12) & (db > max(p50, -45)))[0]:
        if not rows or rows[-1]['file'] != p or abs(rows[-1]['t'] - t[k]) > 0.5:
            rows.append({'file': p, 't': round(t[k], 2), 'kind': 'hit', 'len': 0.2, 'db': round(float(db[k]), 1)})
    # lively voice: speech-band energy, audible and variable for > 1.5 s (laughter, chatter); smoothed over ~0.5 s
    band = sp[:, int(250 * NF / SR):int(3000 * NF / SR)].sum(1) / sp.sum(1)
    raw = ((band > 0.5) & (db > max(p50, -50)) & (flat > 0.08)).astype(float)
    voiced = np.convolve(raw, np.ones(16) / 16, 'same') > 0.4
    k = 0
    while k < n:
        if voiced[k]:
            j = k
            while j < n and voiced[j]: j += 1
            if t[min(j, n - 1)] - t[k] > 1.5 and np.std(db[k:j]) > 3:
                rows.append({'file': p, 't': round(t[k], 2), 'kind': 'voice/laughter', 'len': round(t[min(j, n - 1)] - t[k], 2), 'db': round(float(db[k:j].mean()), 1)})
            k = j
        else:
            k += 1
    print(os.path.basename(p), sum(1 for r in rows if r['file'] == p), 'events', flush=True)
out = os.path.join(OUT, 'archive', 'sound_events.csv'); os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, ['file', 't', 'kind', 'len', 'db']); w.writeheader(); w.writerows(rows)
print('events:', out, len(rows))
