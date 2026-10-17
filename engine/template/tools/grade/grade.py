"""One consistent film look over everything (phone photos, clips, graphics, AI plates), done in ffmpeg:
tone curve + saturation + split tone + lifted blacks baked into a 3D LUT, then halation round highlights,
vignette and fine animated grain, and the final H.264 encode of a chapter.
usage: python tools/grade/grade.py in.mp4 out.mp4 [preset]
presets: warm (storybook, family), pop (brighter, kids/brand), neutral (corporate/explainer, minimal look),
         bw (silver black and white), doc (cool documentary). Lifted blacks protect small projectors and phones.
ffmpeg runs inside out/look so the LUT path has no drive letter (ffmpeg's filter parser breaks on 'D:' on Windows)."""
import sys, os, subprocess, numpy as np, cv2

P = {
    'warm':    dict(lift=0.028, sat=1.04, split=0.035, hal=0.16, grain=0.020, vig=0.16, curve=0.30, bw=False),
    'pop':     dict(lift=0.022, sat=1.08, split=0.020, hal=0.10, grain=0.014, vig=0.10, curve=0.25, bw=False),
    'neutral': dict(lift=0.015, sat=1.00, split=0.000, hal=0.00, grain=0.006, vig=0.05, curve=0.15, bw=False),
    'bw':      dict(lift=0.030, sat=0.00, split=0.000, hal=0.12, grain=0.024, vig=0.18, curve=0.35, bw=True),
    'doc':     dict(lift=0.020, sat=0.95, split=-0.02, hal=0.05, grain=0.012, vig=0.10, curve=0.22, bw=False),
}
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'out', 'look')


def curve_lut(k):
    x = np.linspace(0, 1.25, 1024)
    xc = np.clip(x, 0, 1)
    s = (1 - k) * xc + k * (xc * xc * (3 - 2 * xc))          # gentle S, mid-grey stays put
    s = s + np.clip(x - 1, 0, None) * 0.25
    t = 0.82; hi = s > t                                       # soft shoulder above 0.82
    s[hi] = t + (1 - t) * (1 - np.exp(-(s[hi] - t) / (1 - t) * 1.6)) / (1 - np.exp(-1.6))
    return np.clip(s, 0, 1).astype(np.float32)


def bake(preset, n=65):
    c = P[preset]; lut = curve_lut(c['curve'])
    os.makedirs(D, exist_ok=True)
    path = os.path.join(D, f'{preset}.cube')
    g = np.linspace(0, 1, n, dtype=np.float32)
    b, gg, r = np.meshgrid(g, g, g, indexing='ij')           # .cube order: r fastest
    img = np.stack([r, gg, b], -1).reshape(-1, 3)
    img = lut[np.clip(img / 1.25 * 1023, 0, 1023).astype(np.int32)]
    lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    img = lum[:, None] + (img - lum[:, None]) * c['sat']
    if c['bw']: img = np.repeat(lum[:, None], 3, 1) * np.array([1.0, 0.985, 0.95], np.float32)    # a hint of warmth in the silver
    sh = np.clip(1 - lum * 2, 0, 1)[:, None]; hl = np.clip(lum * 2 - 1, 0, 1)[:, None]
    img = img + c['split'] * (sh * np.array([-0.4, 0.15, 0.35], np.float32) + hl * np.array([0.45, 0.12, -0.35], np.float32))
    img = np.clip(c['lift'] + img * (1 - c['lift']), 0, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'LUT_3D_SIZE {n}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        f.write('\n'.join(f'{a:.6f} {b_:.6f} {c_:.6f}' for a, b_, c_ in img))
    return path


def vignette(preset, W, H):
    c = P[preset]
    path = os.path.join(D, f'vig_{preset}_{W}x{H}.png')
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    v = 1 - c['vig'] * np.clip(rr - 0.55, 0, None) ** 1.6
    cv2.imwrite(path, np.repeat((np.clip(v, 0, 1) * 65535).astype(np.uint16)[..., None], 3, 2))
    return path


def main(src, out, preset='warm'):
    c = P[preset]
    src, out = os.path.abspath(src), os.path.abspath(out)
    W, H = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', src],
                                   capture_output=True, text=True).stdout.strip().strip(',').split(',')[:2])
    k = min(W, H) / 720
    cube, vig = bake(preset), vignette(preset, W, H)
    hal = c['hal']; HI = 'pow(clip((val/255-0.72)/0.28\\,0\\,1)\\,1.5)*255'
    sig = 6 * k
    fc = (f"[0:v]format=gbrp,split[a][b];"
          f"[b]scale={W // 4}:{H // 4}:flags=area,colorchannelmixer=rr=0.2126:rg=0.7152:rb=0.0722:gr=0.2126:gg=0.7152:gb=0.0722:br=0.2126:bg=0.7152:bb=0.0722,"
          f"lutrgb=r='{HI}':g='{HI}':b='{HI}',gblur=sigma={sig:.2f},scale={W}:{H}:flags=bilinear,"
          f"colorchannelmixer=rr={hal:.4f}:gg={hal * 0.42:.4f}:bb={hal * 0.18:.4f}[h];"
          f"[a][h]blend=all_mode=addition,lut3d=file='{os.path.basename(cube)}':interp=trilinear[c];"
          f"[1:v]format=gbrp[v];[c][v]blend=all_mode=multiply:repeatlast=1,format=yuv420p,"
          f"noise=c0s={max(1, int(c['grain'] * 255 * 1.3))}:c0f=t,noise=c1s=2:c2s=2:c1f=t:c2f=t[out]")
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src, '-i', vig, '-filter_complex', fc, '-map', '[out]',
           '-c:v', 'libx264', '-preset', 'faster', '-tune', 'grain', '-crf', '17', '-maxrate', '22M', '-bufsize', '44M', '-g', '50', '-keyint_min', '25',
           '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level:v', '4.1', '-x264-params', 'nal-hrd=none',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-an', out]
    subprocess.run(cmd, check=True, cwd=os.path.dirname(cube))
    print('graded', os.path.basename(out), preset)


if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'warm')
