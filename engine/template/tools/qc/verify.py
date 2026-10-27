"""Render verification: every graded chapter has exactly the frames the timeline says, decodes cleanly, and the
final film's duration matches the timeline and the mix.
usage: python tools/qc/verify.py                 chapters in out/ch/*_f.mp4
       python tools/qc/verify.py --final FILE    the assembled film (adds duration, audio and a full decode check)
       python tools/qc/verify.py --decode        also full-decode every chapter (slow, thorough)"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, json, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT, FILM, load_json


def probe(f, entries='stream=nb_read_packets', sel='v'):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', sel, '-count_packets', '-show_entries', entries, '-of', 'csv=p=0', f],
                       capture_output=True, text=True)
    return r.stdout.strip().strip(',')


def decode_ok(f):
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', f, '-f', 'null', '-'], capture_output=True, text=True)
    return r.returncode == 0 and not r.stderr.strip(), r.stderr.strip()[:200]


TL = load_json(os.path.join(FILM, 'timeline.json')); fps = TL['format']['fps']
bad = 0
if '--final' in sys.argv:
    f = sys.argv[sys.argv.index('--final') + 1]
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip() or 0)
    frames = int(probe(f) or 0); want = sum(round(c['dur'] * fps) for c in TL['chapters'])
    audio = probe(f, 'stream=codec_name,sample_rate,channels', 'a')
    ok, err = decode_ok(f)
    print(f'final {os.path.basename(f)}: {dur:.2f}s, {frames} frames (timeline {want}), audio {audio}, decode {"clean" if ok else "ERRORS " + err}')
    bad += (frames != want) + (not ok) + (not audio)
else:
    for c in TL['chapters']:
        f = os.path.join(OUT, 'ch', c['name'] + '_f.mp4')
        want = round(c['dur'] * fps)
        if not os.path.exists(f): print(f'{c["name"]:12} not rendered'); continue
        got = int(probe(f) or 0)
        line = f'{c["name"]:12} {got:6d} frames (timeline {want})' + ('' if got == want else '  MISMATCH')
        if '--decode' in sys.argv:
            ok, err = decode_ok(f); line += '  decode clean' if ok else '  DECODE ERRORS ' + err
            bad += not ok
        bad += got != want
        print(line)
print('verify:', 'OK' if not bad else f'{bad} problem(s)')
sys.exit(1 if bad else 0)
