"""Cut a person (or object) out of a photo with an alpha matte, untouched, so the background can be animated or
painted behind them: the "painted sea comes alive behind the real child" composite. The person is never altered.
usage: python tools/vfx/cutout.py photo.jpg [--model u2net_human_seg|u2net|isnet-general-use] [--out public/media]
       -> <stem>_cut.png (RGBA) and <stem>_bg.jpg (the background with the person filled in, for animating)
Models: u2net / u2net_human_seg are Apache-2.0. Never use bria-rmbg (RMBG-2.0) without a commercial licence.
Needs the cutouts group: python tools/install_deps.py --groups cutouts  (prints the pinned command; the first run downloads the model)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, numpy as np, cv2
from PIL import Image, ImageOps
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import PUBLIC

a = sys.argv[1:]
if not a: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
model = opt('--model', 'u2net_human_seg'); outd = opt('--out', os.path.join(PUBLIC, 'media')); os.makedirs(outd, exist_ok=True)
from rembg import remove, new_session
sess = new_session(model)
for p in [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] not in ('--model', '--out'))]:
    stem = os.path.splitext(os.path.basename(p))[0]
    im = ImageOps.exif_transpose(Image.open(p)).convert('RGB')
    cut = remove(im, session=sess, post_process_mask=True)
    cut.save(os.path.join(outd, stem + '_cut.png'))
    m = (np.array(cut)[..., 3] > 20).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((15, 15), np.uint8))                       # fill a little beyond the edge
    bg = cv2.inpaint(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), m, 9, cv2.INPAINT_TELEA)
    cv2.imwrite(os.path.join(outd, stem + '_bg.jpg'), bg, [cv2.IMWRITE_JPEG_QUALITY, 93])
    print(stem, '-> _cut.png + _bg.jpg (inpainted: check it, or generate the background separately with no people in it)')
