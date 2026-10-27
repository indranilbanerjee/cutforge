"""Master timeline: every shot's length comes from its measured narration plus breathing room, so picture,
captions and the sound mix all read the same numbers. Never hand-type a time that can be derived.

inputs : film/shots.json   structure (format, chapters, shots, layouts)          <- you edit this
         film/script.json  narration lines {id, text, dir}                        <- you edit this
         film/vo_durs.json measured line lengths (written by tools/voice/gen_vo.py or tools/voice/import_vo.py)
output : film/timeline.json and src/timeline.json (identical; the renderer and the mixer read them)

shot timing keys: vo [line ids], pre (s before first line), gaps (s between lines: one number or a list),
                  post (s after the last line), min (minimum length), fixed (exact length; must fit the narration)
Every other key on a shot (layout, media, zoom, ...) is passed through untouched as the shot's "spec".

Checks (printed, and exit code 2 on errors so pipelines stop):
  ERROR  narration longer than a fixed shot (the line would be cut or spill into the next shot)
  ERROR  a vo id with no script line
  WARN   less than 0.6 s after the last line (abrupt cut) unless the shot sets "hardcut": true
  WARN   a line starting under 0.3 s into a shot (no breath before speech)
  WARN   a line id used twice, or a script line used nowhere
usage: python film/timeline.py [--quiet]
"""
import json, os, sys

R = os.path.dirname(os.path.abspath(__file__))
SH = json.load(open(os.path.join(R, 'shots.json'), encoding='utf-8-sig'))
SC = json.load(open(os.path.join(R, 'script.json'), encoding='utf-8-sig'))
DUR_F = os.path.join(R, 'vo_durs.json')
VO = json.load(open(DUR_F, encoding='utf-8-sig')) if os.path.exists(DUR_F) else {}
LINES = {l['id']: l for l in SC.get('lines', [])}
TIMING = {'id', 'vo', 'pre', 'gaps', 'post', 'min', 'fixed'}
# speaking rate for estimates before any voice exists (characters per second, conservative)
CPS = {'bn': 11.0, 'hi': 12.0, 'en': 14.0, 'ta': 10.0, 'te': 10.5, 'mr': 11.5, 'gu': 11.5, 'kn': 10.5, 'ml': 9.5}
LANG = (SC.get('language') or 'en').split('-')[0]
FPS = SH.get('format', {}).get('fps', 25)


def dur_of(lid, notes):
    if lid in VO:
        return float(VO[lid])
    text = LINES.get(lid, {}).get('text', '')
    est = round(max(1.0, len(text) / CPS.get(LANG, 12.0)) + 0.3, 2)
    notes.append(f'  est    {lid}: no measured length, estimated {est}s from text')
    return est


def build(quiet=False):
    errs, warns, notes = [], [], []
    fmt = {'w': 1280, 'h': 720, 'fps': 25, 'scale': 1.5, **SH.get('format', {})}
    out = {'format': fmt, 'title': SH.get('title', ''), 'chapters': [], 'text': {k: v.get('text', '') for k, v in LINES.items()}}
    used = {}
    g = 0.0
    for ch in SH['chapters']:
        t = 0.0; rows = []
        for s in ch['shots']:
            ids = s.get('vo', [])
            pre, post = s.get('pre', 0.6), s.get('post', 0.9)
            gaps = s.get('gaps', 0.5)
            gaps = gaps if isinstance(gaps, list) else [gaps] * max(0, len(ids) - 1)
            vo = []; at = pre
            for k, p in enumerate(ids):
                if p not in LINES: errs.append(f'  ERROR  {ch["name"]}/{s["id"]}: vo "{p}" has no line in script.json')
                used.setdefault(p, []).append(f'{ch["name"]}/{s["id"]}')
                d = dur_of(p, notes)
                vo.append([p, round(at, 3), round(d, 3)])
                at += d + (gaps[k] if k < len(gaps) else 0.5)
            natural = (vo[-1][1] + vo[-1][2] + post) if vo else 0.0
            if s.get('fixed') is not None:
                dur = float(s['fixed'])
                if vo and vo[-1][1] + vo[-1][2] > dur - 0.05:
                    errs.append(f'  ERROR  {ch["name"]}/{s["id"]}: narration ends at {vo[-1][1] + vo[-1][2]:.2f}s but the shot is fixed at {dur:.2f}s')
            else:
                dur = max(natural, float(s.get('min', 0.0)))
            dur = round(dur * FPS) / FPS
            if vo:
                tail = dur - (vo[-1][1] + vo[-1][2])
                if 0 <= tail < 0.6 and not s.get('hardcut'):
                    warns.append(f'  WARN   {ch["name"]}/{s["id"]}: only {tail:.2f}s after the last line (abrupt). Raise post or set "hardcut": true')
                if vo[0][1] < 0.3:
                    warns.append(f'  WARN   {ch["name"]}/{s["id"]}: speech starts {vo[0][1]:.2f}s into the shot (no breath)')
            spec = {k: v for k, v in s.items() if k not in TIMING}
            rows.append({'id': s['id'], 'start': round(t, 3), 'dur': dur, 'vo': vo, 'g': round(g + t, 3), 'spec': spec})
            t += dur
        cspec = {k: v for k, v in ch.items() if k not in ('name', 'shots')}
        out['chapters'].append({'name': ch['name'], 'start': round(g, 3), 'dur': round(t, 3), 'shots': rows, 'spec': cspec})
        g += t
    out['total'] = round(g, 3)
    for p, where in used.items():
        if len(where) > 1: warns.append(f'  WARN   line {p} is used {len(where)} times: {", ".join(where)}')
    unused = [k for k in LINES if k not in used]
    if unused: warns.append(f'  WARN   script lines not placed in any shot: {", ".join(unused)}')
    for p in (os.path.join(R, 'timeline.json'), os.path.join(R, '..', 'src', 'timeline.json')):
        json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if not quiet:
        for c in out['chapters']:
            print(f"{c['name']:12} start {c['start']:8.2f}  dur {c['dur']:7.2f}  ({len(c['shots'])} shots)")
        print(f"TOTAL {out['total']:.2f} s = {int(out['total'] // 60)} min {out['total'] % 60:.1f} s")
        for line in notes[:12]: print(line)
        if len(notes) > 12: print(f'  ... {len(notes) - 12} more estimated lines')
    for line in warns + errs: print(line)
    return out, errs


if __name__ == '__main__':
    _, errs = build('--quiet' in sys.argv)
    sys.exit(2 if errs else 0)
