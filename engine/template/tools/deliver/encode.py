"""Deliverables from the master, one preset per destination (see docs/compliance-and-licensing.md section 2 and 5).
usage: python tools/deliver/encode.py <master.mp4> <preset> [out.mp4]
presets
  projector    1080p H.264 High@4.1, ~10 Mbps, AAC 256k, -16 LUFS (small speaker); bring a 720p backup too
  projector720 720p H.264 High@3.1, ~6 Mbps
  youtube      1080p H.264 High, 12 Mbps, closed GOP, AAC 384k, -14 LUFS, faststart
  reels        1080x1920 30 fps, 10 Mbps, -14 LUFS (source must already be vertical; captions inside the safe zone)
  whatsapp     720p, ~2.5 Mbps, AAC 128k (send as a document to avoid recompression)
  broadcast    1080p, 20 Mbps, -23 LUFS / -1 dBTP (EBU R128); use -24 LKFS / -2 dBTP for US (ATSC A/85) with --lufs -24 --tp -2
  archive      the master's video copied, audio re-encoded 320k (a safe-keeping copy)
options: --lufs N --tp N override loudness (two-pass loudnorm + limiter). Files over 4 GB get a FAT32 warning automatically.
AAC can add up to ~0.5 dB of true-peak overs at low bitrates: for strict broadcast specs measure the delivered file
(ffmpeg -i out.mp4 -af ebur128=peak=true -f null -) and re-encode with a lower --tp if needed."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, subprocess

PRESETS = {
    'projector':    dict(scale='1920:1080', fps=None, v=['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-level:v', '4.1', '-b:v', '10M', '-maxrate', '14M', '-bufsize', '20M'], a='256k', lufs=-16, tp=-2),
    'projector720': dict(scale='1280:720', fps=None, v=['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-level:v', '3.1', '-b:v', '6M', '-maxrate', '8M', '-bufsize', '12M'], a='256k', lufs=-16, tp=-2),
    'youtube':      dict(scale='1920:1080', fps=None, v=['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-b:v', '12M', '-maxrate', '16M', '-bufsize', '24M', '-bf', '2', '-flags', '+cgop'], a='384k', lufs=-14, tp=-1),
    'reels':        dict(scale='1080:1920', fps=30, v=['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-b:v', '10M', '-maxrate', '14M', '-bufsize', '20M'], a='256k', lufs=-14, tp=-1),
    'whatsapp':     dict(scale='1280:720', fps=None, v=['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'main', '-b:v', '2500k', '-maxrate', '3M', '-bufsize', '5M'], a='128k', lufs=-15, tp=-1.5),
    'broadcast':    dict(scale='1920:1080', fps=None, v=['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-level:v', '4.1', '-b:v', '20M', '-maxrate', '25M', '-bufsize', '30M'], a='320k', lufs=-23, tp=-1),
    'archive':      dict(scale=None, fps=None, v=['-c:v', 'copy'], a='320k', lufs=None, tp=None),
}

a = sys.argv[1:]
if len(a) < 2 or a[1] not in PRESETS: sys.exit(__doc__)
src, name = a[0], a[1]; P = dict(PRESETS[name])
out = a[2] if len(a) > 2 and not a[2].startswith('--') else os.path.splitext(src)[0] + f'_{name}.mp4'
if '--lufs' in a: P['lufs'] = float(a[a.index('--lufs') + 1])
if '--tp' in a: P['tp'] = float(a[a.index('--tp') + 1])
vf = []
if P['scale']:
    w, h = P['scale'].split(':'); vf.append(f'scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2')
if P['fps']: vf.append(f'fps={P["fps"]}')
af = 'aresample=48000'
if P['lufs'] is not None:                       # two-pass loudnorm: measure, then apply linearly so the file lands on target
    import json, re
    probe = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', src, '-vn', '-af',
                            f'loudnorm=I={P["lufs"]}:TP={P["tp"]}:LRA=14:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', probe, re.S)
    af = f'loudnorm=I={P["lufs"]}:TP={P["tp"]}:LRA=14'
    if m:
        j = json.loads(m.group(0))
        af += (f":measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
               f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    af += f',aresample=48000,alimiter=limit={10 ** ((P["tp"] - 0.4) / 20):.3f}:level=false'   # margin for the AAC encoder's overs
cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src] + (['-vf', ','.join(vf)] if vf else []) + P['v'] + \
      (['-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709'] if P['v'][1] != 'copy' else []) + \
      ['-af', af, '-c:a', 'aac', '-b:a', P['a'], '-ar', '48000', '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
size = os.path.getsize(out)
print(f'{name}: {out}  {size / 1e6:.0f} MB' + ('  WARNING: over 4 GB, will not fit FAT32 (use exFAT/NTFS)' if size > 4 * 1024 ** 3 else ''))
