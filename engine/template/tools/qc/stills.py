"""QC stills at shot boundaries, as contact sheets you (and a reviewer agent) can look at before any full render.
For every shot: a frame just after it starts, one at each narration line's midpoint, and one just before it ends.
Sheets get the shot id, time, the caption line, and a safe-area box (projectors crop edges after keystone;
vertical frames get the platform-safe zone x 10-90 %, y 15-65 % instead;
phones put UI over the bottom of vertical video).
usage: python tools/qc/stills.py <chapter> [--shots 2A,2B] [--safe 0.86] [--scale 0.5] [--fresh]  (--fresh re-renders cached frames)
writes out/qc/<chapter>_<frame>.jpg and out/qc/<chapter>_sheet<k>.jpg"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, json, subprocess
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import ROOT, OUT, FILM, PUBLIC, load_json

args = sys.argv[1:]
if not args: sys.exit(__doc__)
ch = args[0]
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
only = set(opt('--shots', '').split(',')) - {''}
safe = float(opt('--safe', '0.86')); scale = opt('--scale', '0.5')
TL = load_json(os.path.join(FILM, 'timeline.json')); fps = TL['format']['fps']
c = next(c for c in TL['chapters'] if c['name'] == ch)
frames, labels = [], {}
for s in c['shots']:
    if only and s['id'] not in only: continue
    a = round(s['start'] * fps); d = round(s['dur'] * fps)
    pts = [(a + min(6, d - 1), 'start')] + [(a + round((at + dur / 2) * fps), f'line {p}') for p, at, dur in s['vo']] + ([] if s['vo'] else [(a + d // 2, 'mid')]) + [(a + d - 3, 'end')]
    for f, what in pts:
        if f not in labels: frames.append(f); labels[f] = (s['id'], what, f / fps, c['start'] + f / fps, next((TL['text'].get(p, '') for p, at, dur in s['vo'] if what == f'line {p}'), ''))
qc = os.path.join(OUT, 'qc'); os.makedirs(qc, exist_ok=True)
todo = frames if '--fresh' in args else [f for f in frames if not os.path.exists(os.path.join(qc, f'{ch}_{f}.jpg'))]   # --fresh after any change
if todo:
    subprocess.run(['node', 'render.mjs', ch, os.path.join(qc, f'{ch}_%d.jpg'), 'still', ','.join(map(str, todo)), scale], cwd=ROOT, check=True)
font_p = os.path.join(PUBLIC, 'fonts', 'TiroBangla-Regular.ttf')
font = ImageFont.truetype(font_p, 18) if os.path.exists(font_p) else ImageFont.load_default()
ims = []
for f in frames:
    im = Image.open(os.path.join(qc, f'{ch}_{f}.jpg')).convert('RGB')
    w, h = im.size; dr = ImageDraw.Draw(im)
    if safe < 1 and h > w:
        # vertical: the platform-safe zone (Reels/Shorts/TikTok UI covers the top ~15 %, bottom ~35 %, sides ~10 %)
        dr.rectangle([w * 0.10, h * 0.15, w * 0.90, h * 0.65], outline=(0, 255, 120), width=1)
    elif safe < 1:
        mx, my = w * (1 - safe) / 2, h * (1 - safe) / 2
        dr.rectangle([mx, my, w - mx, h - my], outline=(0, 255, 120), width=1)
    sid, what, t, g, txt = labels[f]
    band = Image.new('RGB', (w, 46), (16, 16, 20)); bd = ImageDraw.Draw(band)
    bd.text((8, 4), f'{sid}  {what}  film {int(g // 60)}:{g % 60:05.2f}  ({ch} {t:.2f}s, f{f})', fill=(255, 220, 120), font=font)
    bd.text((8, 24), txt[:90], fill=(220, 220, 220), font=font)
    sheet = Image.new('RGB', (w, h + 46)); sheet.paste(im, (0, 0)); sheet.paste(band, (0, h)); ims.append(sheet)
cols = 3
for k in range(0, len(ims), 12):
    sub = ims[k:k + 12]; w, h = sub[0].size; rows = (len(sub) + cols - 1) // cols
    S = Image.new('RGB', (w * cols, h * rows), (0, 0, 0))
    for i, im in enumerate(sub): S.paste(im, ((i % cols) * w, (i // cols) * h))
    S.save(os.path.join(qc, f'{ch}_sheet{k // 12}.jpg'), quality=82)
    print('sheet', os.path.join(qc, f'{ch}_sheet{k // 12}.jpg'))
