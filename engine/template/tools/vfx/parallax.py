"""2.5D camera moves on still photos, using a depth map (tools/vfx/depth.py makes <stem>.jpg + <stem>_depth.png).
Every pixel moves by its own depth: near things slide and grow more than far things, so a flat photo gets real
parallax. Optional rack focus blurs by distance from the focal plane. Output: an mp4 plate to use as a Living/Media
source (public/plates/<id>.mp4), rendered at the film's master size.

usage: python tools/vfx/parallax.py film/plates.json [id,id]
plates.json: a list of shot specs:
 {"id": "p_banyan", "src": "banyan", "dur": 6.0,      # src = stem of public/media/<stem>.jpg (+ _depth.png)
  "c0": [0.5, 0.4], "c1": [0.5, 0.42],                 # frame centre in the source (0..1)
  "z0": 1.0, "z1": 1.08,                               # zoom (1 = cover the frame)
  "dolly0": 0.0, "dolly1": 0.06,                       # depth-weighted push (the parallax); keep 0.02-0.08
  "sx0": 0.0, "sx1": 0.02, "sy0": 0, "sy1": 0,         # lateral camera shift (parallax)
  "f0": 0.8, "f1": 0.8, "dof": 0.0,                    # focus plane (0 far .. 1 near) and max blur px
  "ease": "inout"}
Rules: gentle (dolly <= 0.08, zoom <= 10 % over 5 s); avoid strong parallax on faces (they smear at depth edges).
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import sys, os, json, math, subprocess, numpy as np, cv2
R = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(R, '..'))
from paths import PUBLIC, FILM, load_json
P = os.environ.get('PDIR', os.path.join(PUBLIC, 'media'))
OUT = os.environ.get('PLOUT', os.path.join(PUBLIC, 'plates'))
_TL = load_json(os.path.join(FILM, 'timeline.json'), {}) or {}
_F = _TL.get('format', {'w': 1280, 'h': 720, 'fps': 25, 'scale': 1.5})
W, H, FPS = int(_F['w'] * _F.get('scale', 1)), int(_F['h'] * _F.get('scale', 1)), _F['fps']

def ease(t, kind):
    t = min(1, max(0, t))
    if kind == 'linear': return t
    if kind == 'out': return 1 - (1 - t) ** 3
    if kind == 'in': return t ** 3
    return t * t * (3 - 2 * t) if kind == 'smooth' else (4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2)

def lerp(a, b, t): return a + (b - a) * t

def load(src, ss=1.0):
    img = cv2.imread(os.path.join(P, src + '.jpg'))[:, :, ::-1].astype(np.float32) / 255
    d = cv2.imread(os.path.join(P, src + '_depth.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
    # push near edges outward a little so the background tears less at object borders
    d = cv2.dilate(d, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    d = cv2.GaussianBlur(d, (0, 0), 2.0)
    return img, d

def render(spec, out=None):
    global W, H
    W, H = spec.get('w', W), spec.get('h', H)
    img, dep = load(spec['src'])
    sh, sw = img.shape[:2]
    n = int(round(spec['dur'] * FPS))
    out = out or os.path.join(OUT, spec['id'] + '.mp4')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '13', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    # base scale: source pixels per output pixel so the 16:9 frame covers the photo at zoom 1
    base = min(sw / W, sh / H) / spec.get('inset', 1.12)
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    px = (gx - W / 2) / H; py = (gy - H / 2) / H          # output coords in "frame heights", centred
    blurs = None
    for i in range(n):
        u = ease(i / max(1, n - 1), spec.get('ease', 'inout'))
        cx = lerp(spec['c0'][0], spec['c1'][0], u) * sw; cy = lerp(spec['c0'][1], spec['c1'][1], u) * sh
        z = lerp(spec.get('z0', 1), spec.get('z1', 1), u)
        dl = lerp(spec.get('dolly0', 0), spec.get('dolly1', 0), u)
        sx = lerp(spec.get('sx0', 0), spec.get('sx1', 0), u); sy = lerp(spec.get('sy0', 0), spec.get('sy1', 0), u)
        f = lerp(spec.get('f0', .5), spec.get('f1', .5), u)
        # keep the whole view (incl. parallax of the far plane) inside the photo
        kmin = z * (1 - abs(dl) * max(f, 1 - f))
        hw = (W / 2 / H + abs(sx) * max(f, 1 - f) / max(kmin, .2)) * H * base / max(kmin, .2) * 1.01
        hh = (0.5 + abs(sy) * max(f, 1 - f) / max(kmin, .2)) * H * base / max(kmin, .2) * 1.01
        cx = min(max(cx, hw), sw - hw) if 2 * hw < sw else sw / 2
        cy = min(max(cy, hh), sh - hh) if 2 * hh < sh else sh / 2
        # solve source position s for output p:  p = (s - c) * z * (1 + dl*(d - f)) / base + shift*(d - f)
        qx, qy = px.copy(), py.copy()
        for _ in range(7):
            mx = cx + qx * H * base; my = cy + qy * H * base
            d = cv2.remap(dep, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            k = z * (1 + dl * (d - f))
            qx = (px - sx * (d - f)) / k; qy = (py - sy * (d - f)) / k
        mx = cx + qx * H * base; my = cy + qy * H * base
        fr = cv2.remap(img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        dof = spec.get('dof', 0)
        if dof > 0:
            d = cv2.remap(dep, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            coc = np.clip(np.abs(d - f) * dof, 0, dof)          # blur radius in px
            levels = [0, dof * .25, dof * .5, dof]
            stack = [fr] + [cv2.GaussianBlur(fr, (0, 0), max(.1, r / 2)) for r in levels[1:]]
            out_fr = np.zeros_like(fr)
            for a in range(len(levels) - 1):
                lo, hi = levels[a], levels[a + 1]
                wgt = np.clip((coc - lo) / (hi - lo + 1e-6), 0, 1)[..., None]
                inside = ((coc >= lo) & (coc < hi + (a == len(levels) - 2) * 1e6))[..., None]
                out_fr += np.where(inside, stack[a] * (1 - wgt) + stack[a + 1] * wgt, 0)
            fr = out_fr
        ff.stdin.write((np.clip(fr, 0, 1) * 255 + .5).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    return out

if __name__ == '__main__':
    specs = json.load(open(sys.argv[1], encoding='utf-8-sig'))
    only = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
    for s in specs:
        if only and s['id'] not in only: continue
        print('plate', s['id'], render(s), flush=True)
