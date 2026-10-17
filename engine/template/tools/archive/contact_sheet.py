"""Contact sheets: look at the whole library fast. One sheet per month (or per day / per list), thumbnails labelled
with file name and capture time; videos show their middle frame with a play mark and duration.
usage: python tools/archive/contact_sheet.py [--by month|day] [--from 2023-01] [--to 2023-12] [--kind photo|video]
       python tools/archive/contact_sheet.py --list files.txt --name picks
writes out/archive/sheets/<group>.jpg (48 thumbnails per sheet)"""
import os, sys, csv, subprocess, io
from PIL import Image, ImageDraw, ImageOps, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT, PUBLIC

a = sys.argv[1:]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
inv = os.path.join(OUT, 'archive', 'inventory.csv')
rows = list(csv.DictReader(open(inv, encoding='utf-8')))
if opt('--list'):
    want = [l.strip() for l in open(opt('--list'), encoding='utf-8') if l.strip()]
    by = {r['path']: r for r in rows}; groups = {opt('--name', 'list'): [by.get(p, {'path': p, 'kind': 'photo', 'date': '', 'dur': ''}) for p in want]}
else:
    n = 7 if opt('--by', 'month') == 'month' else 10
    groups = {}
    for r in rows:
        if opt('--kind') and r['kind'] != opt('--kind'): continue
        if r['kind'] == 'audio': continue
        g = r['date'][:n]
        if opt('--from') and g < opt('--from'): continue
        if opt('--to') and g > opt('--to'): continue
        groups.setdefault(g, []).append(r)
TW, TH = 240, 180
fp = os.path.join(PUBLIC, 'fonts', 'HindSiliguri-Medium.ttf')
font = ImageFont.truetype(fp, 13) if os.path.exists(fp) else ImageFont.load_default()


def thumb(r):
    p = r['path']
    try:
        if r['kind'] == 'video':
            t = max(0.0, float(r.get('dur') or 0) / 2)
            jpg = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(t), '-i', p, '-frames:v', '1', '-vf', f'scale={TW}:-2', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'],
                                 capture_output=True).stdout
            im = Image.open(io.BytesIO(jpg)).convert('RGB')
        else:
            im = ImageOps.exif_transpose(Image.open(p)).convert('RGB')
        im.thumbnail((TW, TH - 30)); return im
    except Exception:
        return Image.new('RGB', (TW, TH - 30), (60, 0, 0))


d = os.path.join(OUT, 'archive', 'sheets'); os.makedirs(d, exist_ok=True)
for g, items in sorted(groups.items()):
    for k in range(0, len(items), 48):
        sub = items[k:k + 48]; cols = 8; rws = (len(sub) + cols - 1) // cols
        S = Image.new('RGB', (cols * TW, rws * TH), (18, 18, 22)); dr = ImageDraw.Draw(S)
        for i, r in enumerate(sub):
            x, y = (i % cols) * TW, (i // cols) * TH; im = thumb(r)
            S.paste(im, (x + (TW - im.width) // 2, y + 2))
            if r['kind'] == 'video': dr.text((x + 6, y + 6), f'▶ {float(r.get("dur") or 0):.0f}s', fill=(255, 230, 120), font=font)
            dr.text((x + 4, y + TH - 28), os.path.basename(r['path'])[:30], fill=(220, 220, 220), font=font)
            dr.text((x + 4, y + TH - 14), (r.get('date') or '')[:16], fill=(160, 160, 170), font=font)
        f = os.path.join(d, f'{g}{"_" + str(k // 48) if len(items) > 48 else ""}.jpg'); S.save(f, quality=80); print(f)
