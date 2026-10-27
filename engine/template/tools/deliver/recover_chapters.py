"""Rebuild the graded chapter files from a delivered master instead of transferring them again (a real case: 3.3 GB
that would have taken 3.5 hours over a slow link was cut out of the master on the client's machine in a minute).
Works because the master is the chapters joined with stream copy: every chapter starts on a keyframe.

on the machine that HAS the chapters:   python tools/deliver/recover_chapters.py ref  > chapters_ref.json
on the machine that has only the master: python tools/deliver/recover_chapters.py cut <master.mp4> chapters_ref.json [--out out/ch]
Checks: frame count per chapter and an md5 of every DECODED frame (packet bytes can differ by in-band headers at
keyframes; pictures must not). A chapter that fails is reported; transfer only that one."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, json, subprocess, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT, FILM, load_json


def frames(f):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-count_packets', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', f],
                              capture_output=True, text=True).stdout.strip().strip(',') or 0)


def decoded_md5(f):
    p = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', f, '-map', '0:v', '-f', 'framemd5', '-'], capture_output=True, text=True).stdout
    return hashlib.md5('\n'.join(l.split(',')[-1].strip() for l in p.splitlines() if l and not l.startswith('#')).encode()).hexdigest()


a = sys.argv[1:]
if not a: sys.exit(__doc__)
TL = load_json(os.path.join(FILM, 'timeline.json')); fps = TL['format']['fps']
if a[0] == 'ref':
    ref, start = [], 0
    for c in TL['chapters']:
        f = os.path.join(OUT, 'ch', c['name'] + '_f.mp4'); n = frames(f)
        ref.append({'name': c['name'], 'start_frame': start, 'frames': n, 'decoded_md5': decoded_md5(f)}); start += n
        print(c['name'], n, file=sys.stderr)
    print(json.dumps({'fps': fps, 'chapters': ref}, indent=1))
elif a[0] == 'cut':
    master, ref = a[1], json.load(open(a[2]))
    outd = a[a.index('--out') + 1] if '--out' in a else os.path.join(OUT, 'ch'); os.makedirs(outd, exist_ok=True)
    bad = []
    for c in ref['chapters']:
        o = os.path.join(outd, c['name'] + '_f.mp4'); t = c['start_frame'] / ref['fps']       # exact keyframe time: no offset
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{t:.6f}', '-i', master, '-map', '0:v', '-c', 'copy', '-frames:v', str(c['frames']), o], check=True)
        ok = frames(o) == c['frames'] and decoded_md5(o) == c['decoded_md5']
        print(f"{c['name']:12} {'verified' if ok else 'MISMATCH: transfer this chapter instead'}", flush=True)
        if not ok: bad.append(c['name'])
    sys.exit(1 if bad else 0)
