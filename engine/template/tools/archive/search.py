"""Search a photo/video library by meaning ("a red motorbike", "sky lanterns at night", "a child on a beach",
"birthday cake with candles") with an open CLIP model, and get a contact sheet of the best matches per query.
Finds objects and scenes across thousands of files in seconds once indexed. It never identifies people: use it
for things, places and moments, and confirm every hit by eye.

usage: python tools/archive/search.py index [--from 2023-01] [--to 2026-12]        (once; resumable, cached)
       python tools/archive/search.py "a red motorbike" "sky lanterns at night" [--k 24] [--from ...] [--to ...]
writes out/archive/clip_index.npz and out/archive/search/<query>.jpg (+ .csv with file, date, score)
Needs the archive-search group: python tools/install_deps.py --groups archive-search  (prints the pinned command; CPU is fine;
~10 min per 1,000 photos on 2 cores to index).
Model: ViT-B-32 laion2b_s34b_b79k (OpenCLIP, MIT code; weights downloaded from Hugging Face on first use)."""
import os, sys, csv, io, re, subprocess, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT

a = sys.argv[1:]
if not a: sys.exit(__doc__)
def opt(k, d=None):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
FROM, TO, K = opt('--from', '0000'), opt('--to', '9999'), int(opt('--k', 24))
flags = {'--from', '--to', '--k'}
words = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] not in flags)]
INV = os.path.join(OUT, 'archive', 'inventory.csv')
IDX = os.path.join(OUT, 'archive', 'clip_index.npz')
if not os.path.exists(INV): sys.exit('run tools/archive/inventory.py first')

import torch, open_clip
from PIL import Image, ImageOps, ImageDraw
torch.set_num_threads(max(1, (os.cpu_count() or 2)))
model, _, pre = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
model.eval(); tok = open_clip.get_tokenizer('ViT-B-32')

rows = [r for r in csv.DictReader(open(INV, encoding='utf-8-sig')) if r.get('kind') in ('photo', 'video')
        and FROM <= (r.get('date') or '')[:7] <= TO]


def frame(r):
    p = r['path']
    try:
        if r['kind'] == 'video':
            d = float(r.get('dur') or 2) / 2
            o = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{d:.2f}', '-i', p, '-frames:v', '1', '-vf', 'scale=320:-2',
                                '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'], capture_output=True).stdout
            return Image.open(io.BytesIO(o)).convert('RGB') if o else None
        im = ImageOps.exif_transpose(Image.open(p)); im.draft('RGB', (320, 320)); im.thumbnail((320, 320))
        return im.convert('RGB')
    except Exception:
        return None


def build_index():
    have = dict(np.load(IDX, allow_pickle=True)) if os.path.exists(IDX) else {'paths': np.array([]), 'emb': np.zeros((0, 512), np.float32)}
    done = set(have['paths'].tolist()); paths = list(have['paths']); embs = [have['emb']]
    todo = [r for r in rows if r['path'] not in done]
    print(f'indexing {len(todo)} files ({len(done)} cached)')
    batch, bp = [], []
    def flush():
        if not batch: return
        with torch.no_grad():
            e = model.encode_image(torch.stack(batch)); e = e / e.norm(dim=-1, keepdim=True)
        embs.append(e.numpy().astype(np.float32)); paths.extend(bp); batch.clear(); bp.clear()
        np.savez(IDX, paths=np.array(paths), emb=np.concatenate(embs))
    for i, r in enumerate(todo):
        im = frame(r)
        if im is None: continue
        batch.append(pre(im)); bp.append(r['path'])
        if len(batch) == 32: flush(); print(f'  {i + 1}/{len(todo)}', flush=True)
    flush()
    print('index:', IDX, len(paths), 'files')


if words and words[0] == 'index':
    build_index(); sys.exit()
if not os.path.exists(IDX): build_index()
Z = np.load(IDX, allow_pickle=True); P = Z['paths'].tolist(); E = Z['emb']
meta = {r['path']: r for r in rows}
keep = [i for i, p in enumerate(P) if p in meta]
os.makedirs(os.path.join(OUT, 'archive', 'search'), exist_ok=True)
for q in words:
    with torch.no_grad():
        t = model.encode_text(tok([q])); t = (t / t.norm(dim=-1, keepdim=True)).numpy()[0]
    sc = E[keep] @ t
    order = [keep[j] for j in np.argsort(-sc)[:K]]
    slug = re.sub(r'[^a-z0-9]+', '_', q.lower()).strip('_')[:50]
    with open(os.path.join(OUT, 'archive', 'search', slug + '.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['rank', 'score', 'date', 'kind', 'path'])
        for n, i in enumerate(order): w.writerow([n + 1, round(float(E[i] @ t), 3), meta[P[i]].get('date', ''), meta[P[i]]['kind'], P[i]])
    TW, TH, cols = 240, 200, 6
    sheet = Image.new('RGB', (cols * TW, ((len(order) + cols - 1) // cols) * (TH + 34) + 30), (18, 18, 22))
    d = ImageDraw.Draw(sheet); d.text((8, 8), f'"{q}"  top {len(order)}  (confirm every hit by eye)', fill=(255, 220, 140))
    for n, i in enumerate(order):
        im = frame(meta[P[i]])
        x, y = (n % cols) * TW, 30 + (n // cols) * (TH + 34)
        if im is not None:
            im.thumbnail((TW - 8, TH - 8)); sheet.paste(im, (x + 4, y + 4))
        d.text((x + 4, y + TH), f'{n + 1}. {os.path.basename(P[i])[:26]}', fill=(220, 220, 220))
        d.text((x + 4, y + TH + 14), f'{meta[P[i]].get("date", "")[:10]}  {float(E[i] @ t):.2f}', fill=(150, 150, 150))
    out = os.path.join(OUT, 'archive', 'search', slug + '.jpg'); sheet.save(out, quality=82)
    print(f'{q!r}: {out}')
