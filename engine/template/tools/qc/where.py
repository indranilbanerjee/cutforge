"""Map a time in the film (from a client's note, e.g. "8:26 swap that face") to the shot, what is said, and what is shown.
usage: python tools/qc/where.py 8:26 [12:03 ...]      (m:ss, h:mm:ss or seconds)"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import FILM, load_json

TL = load_json(os.path.join(FILM, 'timeline.json'))


def secs(s):
    p = [float(x) for x in s.split(':')]
    return p[0] if len(p) == 1 else p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


for arg in sys.argv[1:]:
    t = secs(arg)
    for c in TL['chapters']:
        if c['start'] <= t < c['start'] + c['dur']:
            for s in c['shots']:
                g = c['start'] + s['start']
                if g <= t < g + s['dur']:
                    local = t - g
                    said = [f"{p} \"{TL['text'].get(p, '')[:70]}\"" for p, at, d in s['vo'] if at - 1 <= local <= at + d + 1]
                    media = [m if isinstance(m, str) else m['src'] for m in s['spec'].get('media', [])]
                    print(f"{arg}: {c['name']}/{s['id']} at {local:.1f}s of {s['dur']:.1f}s | layout {s['spec'].get('layout', 'custom')} | "
                          f"media {', '.join(media) or '-'} | said: {'; '.join(said) or '-'}")
            break
    else:
        print(f'{arg}: past the end ({TL["total"]:.1f}s)')
