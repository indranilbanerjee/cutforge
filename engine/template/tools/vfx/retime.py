"""Slow down or conform a short clip (e.g. a 5 s AI motion plate that must fill 10 s) with motion interpolation,
and conform frame rate and size to the film. Dreamier than speeding up a still.
usage: python tools/vfx/retime.py in.mp4 out.mp4 --factor 2.0 [--fps 25] [--size 1920x1080]
Interpolation can smear fast motion or thin details: look at the result frame by frame before using it."""
import sys, subprocess

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
f = float(opt('--factor', 2.0)); fps = int(opt('--fps', 25)); size = opt('--size')
vf = f'setpts={f}*PTS,minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1'
if size: w, h = size.split('x'); vf += f',scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}'
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', a[0], '-vf', vf, '-an', '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', a[1]], check=True)
print('retimed', a[1])
