"""Voice audition: the same 6 representative lines in several voices/engines, plus an HTML page to listen on a phone.
Pick lines that stress the engine: one funny, one tender, one list, one name-heavy, one long sentence, the emotional peak.
usage: python tools/voice/audition.py film/audition.json
audition.json: {"lines": ["1A", "3B", ...] or [{"id": "x", "text": "..."}],
                "candidates": [{"name": "ratan v3", "provider": "sarvam", "voice": "ratan", "model": "bulbul:v3", "lang": "bn-IN"}, ...],
                "name_tests": ["<the hero's name in 3 spellings>"]}
writes out/audition/<candidate>/<line>.wav and out/audition/index.html. Paid providers pass the budget gate."""
import os, sys, json, html
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import FILM, OUT, load_json
import tts as T

A = load_json(sys.argv[1] if len(sys.argv) > 1 else os.path.join(FILM, 'audition.json'))
S = load_json(os.path.join(FILM, 'script.json'), {'lines': []})
by_id = {l['id']: l for l in S['lines']}
lines = [by_id[x] if isinstance(x, str) else x for x in A['lines']] + [{'id': f'name{k}', 'text': t, 'dir': 'plain'} for k, t in enumerate(A.get('name_tests', []))]
paid = [c for c in A['candidates'] if c.get('provider') in T.PAID]
if paid:
    from spend import gate, log
    est = sum(len(l['text']) for l in lines) / 1000 * 3.0 * len(paid)
    gate('audition', est)
root = os.path.join(OUT, 'audition'); os.makedirs(root, exist_ok=True)
rows = []
for c in A['candidates']:
    d = os.path.join(root, c['name'].replace(' ', '_')); os.makedirs(d, exist_ok=True)
    for l in lines:
        f = os.path.join(d, l['id'] + '.wav')
        if not os.path.exists(f):
            try: T.tts(f, l['text'], c, c.get('pace', 0.88), l.get('dir', ''))
            except Exception as e: print(c['name'], l['id'], 'failed:', str(e)[:120]); continue
        rows.append((c['name'], l, os.path.relpath(f, root)))
if paid: log('audition', ','.join(c['name'] for c in paid), f'{len(lines)} lines x {len(paid)} voices', est)
cells = {}
for name, l, rel in rows: cells.setdefault(l['id'], {})[name] = rel
names = [c['name'] for c in A['candidates']]
h = ['<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Voice audition</title>',
     '<style>body{font:15px system-ui;margin:16px;max-width:900px}td,th{padding:6px;border-bottom:1px solid #ddd;vertical-align:top}audio{width:150px}</style>',
     '<h2>Voice audition</h2><p>Listen on the device the film will play on. Pick by ear, then note the winner in decisions.md.</p><table><tr><th>line</th>']
h += [f'<th>{html.escape(n)}</th>' for n in names] + ['</tr>']
for l in lines:
    h.append(f'<tr><td><b>{l["id"]}</b><br>{html.escape(l["text"])}<br><i>{html.escape(l.get("dir", ""))}</i></td>')
    h += [f'<td>{"<audio controls src=" + json.dumps(cells.get(l["id"], {}).get(n)) + "></audio>" if cells.get(l["id"], {}).get(n) else "-"}</td>' for n in names]
    h.append('</tr>')
open(os.path.join(root, 'index.html'), 'w', encoding='utf-8').write('\n'.join(h + ['</table>']))
print('audition page:', os.path.join(root, 'index.html'))
