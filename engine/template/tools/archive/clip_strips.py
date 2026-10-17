"""Look inside every video without watching it: 8 frames across the clip plus its loudness curve, so you can pick
the exact seconds to use and see where the real sound (laughs, a conch, drums, speech) is.
usage: python tools/archive/clip_strips.py [--from 2023-01] [--to 2023-12] [--min 2] [--files a.mp4 b.mp4]
writes out/archive/strips/<name>.jpg and out/archive/clips.csv (duration, mean and peak loudness, loud moments)"""
import os, sys, csv, subprocess, io, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT, PUBLIC

a = sys.argv[1:]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
if '--files' in a:
    vids = [{'path': p, 'date': '', 'dur': ''} for p in a[a.index('--files') + 1:]]
else:
    vids = [r for r in csv.DictReader(open(os.path.join(OUT, 'archive', 'inventory.csv'), encoding='utf-8')) if r['kind'] == 'video'
            and (not opt('--from') or r['date'][:7] >= opt('--from')) and (not opt('--to') or r['date'][:7] <= opt('--to'))
            and float(r.get('dur') or 0) >= float(opt('--min', 0))]
d = os.path.join(OUT, 'archive', 'strips'); os.makedirs(d, exist_ok=True)
fp = os.path.join(PUBLIC, 'fonts', 'HindSiliguri-Medium.ttf')
font = ImageFont.truetype(fp, 14) if os.path.exists(fp) else ImageFont.load_default()
out_rows = []
for r in vids:
    p = r['path']
    dur = float(r.get('dur') or 0) or float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout or 0)
    if dur <= 0: continue
    frames = []
    for k in range(8):
        t = dur * (k + 0.5) / 8
        jpg = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t:.2f}', '-i', p, '-frames:v', '1', '-vf', 'scale=-2:150', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'], capture_output=True).stdout
        try: frames.append((t, Image.open(io.BytesIO(jpg)).convert('RGB')))
        except Exception: frames.append((t, Image.new('RGB', (84, 150), (40, 0, 0))))
    pcm = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', p, '-vn', '-ac', '1', '-ar', '8000', '-f', 's16le', '-'], capture_output=True).stdout
    y = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    hop = 800; n = len(y) // hop
    db = 20 * np.log10(np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-10)) if n else np.array([-90.0])
    fw = sum(im.width for _, im in frames) + 4 * 9
    S = Image.new('RGB', (max(fw, 800), 150 + 90 + 26), (16, 16, 20)); dr = ImageDraw.Draw(S); x = 4
    for t, im in frames:
        S.paste(im, (x, 4)); dr.text((x + 3, 6), f'{t:.1f}s', fill=(255, 230, 120), font=font); x += im.width + 4
    W = S.width - 8; base = 150 + 8 + 80
    for i in range(1, len(db)):
        x0, x1 = 4 + W * (i - 1) / len(db), 4 + W * i / len(db)
        h0, h1 = max(0, min(80, (db[i - 1] + 60) * 80 / 60)), max(0, min(80, (db[i] + 60) * 80 / 60))
        dr.line([(x0, base - h0), (x1, base - h1)], fill=(120, 200, 255), width=1)
    loud = [round(i / 10, 1) for i in np.argsort(-db)[:3]] if n else []
    dr.text((6, base + 4), f'{os.path.basename(p)}  {r.get("date", "")[:16]}  {dur:.1f}s  mean {np.mean(db):.0f} dB  peak {np.max(db):.0f} dB  loudest at {loud}', fill=(220, 220, 220), font=font)
    S.save(os.path.join(d, os.path.splitext(os.path.basename(p))[0] + '.jpg'), quality=80)
    out_rows.append({'path': p, 'date': r.get('date', ''), 'dur': round(dur, 2), 'mean_db': round(float(np.mean(db)), 1), 'peak_db': round(float(np.max(db)), 1), 'loudest_s': loud})
    print(os.path.basename(p), f'{dur:.1f}s', flush=True)
with open(os.path.join(OUT, 'archive', 'clips.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, ['path', 'date', 'dur', 'mean_db', 'peak_db', 'loudest_s']); w.writeheader(); w.writerows(out_rows)
print('strips in', d)
