"""Manual kerning for shaped titles: tools/text/kern.json = {"<id>": {"<glyph index>": <font units shift>}}.
A shift moves that glyph and every glyph after it. Use when a display font sets two letters too far apart."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import json, os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
p = os.path.join(R, 'src', 'glyphs.json')
kf = os.path.join(R, 'tools', 'text', 'kern.json')
d = json.load(open(p, encoding='utf-8-sig'))
K = json.load(open(kf, encoding='utf-8-sig')) if os.path.exists(kf) else {}
for k, table in K.items():
    if k not in d: print('kern: no shaped string', k); continue
    shift = 0
    for i, g in enumerate(d[k]['glyphs']):
        shift += int(table.get(str(i), 0)); g['x'] += shift
    d[k]['width'] += shift
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
print('shaped', len(d), 'strings; kerned', len(K))
