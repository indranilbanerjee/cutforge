"""Prepare photos for the film: upright (EXIF rotation applied), max side 2880, plus a 16-bit depth map from
Depth Anything V2 Small (Apache-2.0) for 2.5D parallax (tools/vfx/parallax.py).
usage: python tools/vfx/depth.py photo.jpg [...] [--out public/media]   -> <out>/<stem>.jpg + <stem>_depth.png
Depth parallax suits wide shots and landscapes. Keep faces still: small moves (2-4 %), never warp a face."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, numpy as np, cv2
from PIL import Image, ImageOps
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import PUBLIC
from fetch_models import path as model

a = sys.argv[1:]
OUTD = a[a.index('--out') + 1] if '--out' in a else os.path.join(PUBLIC, 'media')
files = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] != '--out')]
os.makedirs(OUTD, exist_ok=True)
_sess = None


def depth(rgb):
    global _sess
    if _sess is None:
        import onnxruntime as ort
        so = ort.SessionOptions(); so.intra_op_num_threads = max(1, (os.cpu_count() or 2) - 1)
        _sess = ort.InferenceSession(model('depth'), so)
    h, w = rgb.shape[:2]
    s = 518 / max(h, w); nh, nw = int(round(h * s / 14) * 14), int(round(w * s / 14) * 14)
    x = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
    d = _sess.run(None, {_sess.get_inputs()[0].name: x})[0].squeeze()
    d = cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)
    return (d - d.min()) / (d.max() - d.min() + 1e-6)


for p in files:
    stem = os.path.splitext(os.path.basename(p))[0]; o = os.path.join(OUTD, stem)
    if os.path.exists(o + '_depth.png'): print('have', stem); continue
    im = ImageOps.exif_transpose(Image.open(p)).convert('RGB'); im.thumbnail((2880, 2880), Image.LANCZOS)
    rgb = np.array(im); im.save(o + '.jpg', quality=94)
    cv2.imwrite(o + '_depth.png', (depth(rgb) * 65535).astype(np.uint16))
    print(stem, rgb.shape, flush=True)
