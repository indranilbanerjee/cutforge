"""Procedural demo media so the template renders before any real material exists (no stock, no people, no licences).
usage: python tools/demo_assets.py      -> public/media/demo_*.jpg / demo_clip_*.mp4 (with a little sound each)"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import PUBLIC

D = os.path.join(PUBLIC, 'media'); os.makedirs(D, exist_ok=True)
rng = np.random.default_rng(5)


def grad(w, h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    return (np.array(top)[None, None] * (1 - t) + np.array(bot)[None, None] * t).repeat(w, 1)


def save(arr, name, blur=0):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    im.save(os.path.join(D, name), quality=92)


def lamp(w=2400, h=1600):
    a = grad(w, h, (28, 18, 12), (10, 6, 4))
    yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot(xx - w * 0.5, yy - h * 0.58)
    a += (np.exp(-r / 380)[..., None] * np.array([255, 160, 70]) * 0.9)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([w * 0.42, h * 0.62, w * 0.58, h * 0.70], fill=(120, 60, 30))                      # clay lamp
    d.ellipse([w * 0.485, h * 0.50, w * 0.515, h * 0.63], fill=(255, 210, 120))                  # flame
    im = im.filter(ImageFilter.GaussianBlur(2)); im.save(os.path.join(D, 'demo_lamp.jpg'), quality=92)


def sea(w=2400, h=1600):
    a = grad(w, h, (250, 200, 150), (120, 160, 190)); hz = int(h * 0.55)
    a[hz:] = grad(w, h - hz, (60, 110, 150), (20, 50, 80))
    yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot(xx - w * 0.62, yy - hz + 60)
    a += (np.clip(1 - r / 120, 0, 1) ** 0.5)[..., None] * np.array([255, 230, 180]) * 0.8
    a[hz:] += (np.sin(xx[hz:] / 18 + yy[hz:] / 6) * 8)[..., None]
    save(a, 'demo_sea.jpg', 1)


def hills(w=2400, h=1600):
    a = grad(w, h, (180, 210, 230), (240, 220, 190))
    im = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(im)
    for k, col in enumerate([(120, 150, 130), (90, 120, 95), (60, 90, 70), (40, 60, 45)]):
        base = h * (0.45 + 0.13 * k); pts = [(0, h)]
        for x in range(0, w + 40, 40): pts.append((x, base - 120 * np.sin(x / (300 + 90 * k) + k * 1.7) - 40 * np.sin(x / 90 + k)))
        pts.append((w, h)); d.polygon(pts, fill=col)
    im.filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(D, 'demo_hills.jpg'), quality=92)


def portrait(w=1200, h=1700):
    a = grad(w, h, (240, 200, 160), (200, 120, 90))
    im = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(im)
    d.rectangle([w * 0.47, h * 0.45, w * 0.53, h], fill=(50, 30, 25))
    for k in range(40):
        x, y, r = w * 0.5 + rng.normal(0, 160), h * 0.38 + rng.normal(0, 120), rng.uniform(60, 140)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(60 + k % 3 * 10, 80, 50))
    im.filter(ImageFilter.GaussianBlur(1.5)).save(os.path.join(D, 'demo_portrait.jpg'), quality=92)


def clip(name, hue, seconds=6, w=720, h=1280, fps=25, tone=220.0):
    out = os.path.join(D, name)
    wav = out + '.wav'
    t = np.arange(int(seconds * 48000)) / 48000
    s = 0.08 * np.sin(2 * np.pi * tone * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t)) + 0.02 * rng.standard_normal(len(t))
    import soundfile as sf; sf.write(wav, np.stack([s, s], 1).astype(np.float32), 48000)
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-',
                          '-i', wav, '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', out], stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for f in range(seconds * fps):
        k = f / fps
        v = 0.5 + 0.5 * np.sin(xx / 60 + k * 1.3) * np.cos(yy / 90 - k * 0.9)
        img = np.stack([v * hue[0], v * hue[1], v * hue[2]], -1) + 30
        cy = h * (0.5 + 0.25 * np.sin(k)); img += (np.exp(-np.hypot(xx - w / 2, yy - cy) / 90)[..., None] * 200)
        p.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)


if __name__ == '__main__':
    lamp(); sea(); hills(); portrait()
    clip('demo_clip_a.mp4', (220, 120, 60), tone=220); clip('demo_clip_b.mp4', (60, 140, 220), tone=277); clip('demo_clip_c.mp4', (120, 200, 90), tone=330)
    print('demo media in', D)
