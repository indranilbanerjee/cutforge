"""Story-level QC from data, before anyone watches: the things clients notice first.
  CHRONOLOGY  an asset's capture date falls outside its chapter's date span (film/shots.json chapter "span": ["2023-01", "2023-10"])
              or runs backwards inside a chapter that declares "order": "chronological"
  CAST        screen-seconds per person from film/people_in_media.json ({"media/x.jpg": ["Name", ...]});
              everyone in facts.md's people map with zero seconds is listed (missing relatives were a real complaint)
  REUSE       the same asset used in more than one shot (fine for a callback, a mistake otherwise)
  RUNTIME     total more than 5 % away from config target_minutes
Dates come from out/archive/inventory.csv (tools/archive/inventory.py) matched by file name.
usage: python tools/qc/qc_story.py"""
import os, sys, csv, json, re, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import ROOT, OUT, FILM, CFG, load_json

TL = load_json(os.path.join(FILM, 'timeline.json'))
SH = load_json(os.path.join(FILM, 'shots.json'))
inv_p = os.path.join(OUT, 'archive', 'inventory.csv')
dates = {}
if os.path.exists(inv_p):
    for r in csv.DictReader(open(inv_p, encoding='utf-8')):
        if r.get('date'): dates[os.path.splitext(os.path.basename(r['path']))[0].lower()] = r['date'][:10]
people = load_json(os.path.join(FILM, 'people_in_media.json'), {})


def stem(src): return os.path.splitext(os.path.basename(src))[0].lower()


issues = []; uses = collections.defaultdict(list); cast = collections.Counter()
for c_tl, c_sh in zip(TL['chapters'], SH['chapters']):
    span = c_sh.get('span'); prev = None
    for s in c_tl['shots']:
        media = [m if isinstance(m, str) else m['src'] for m in s['spec'].get('media', [])]
        for m in media:
            uses[m].append(f"{c_tl['name']}/{s['id']}")
            for p in people.get(m, []): cast[p] += s['dur'] / max(1, len(media))
            d = dates.get(stem(m))
            if not d: continue
            if span and not (span[0] <= d[:len(span[0])] and d[:len(span[1])] <= span[1]):
                issues.append(f"CHRONOLOGY {c_tl['name']}/{s['id']}: {os.path.basename(m)} dated {d}, chapter span {span[0]}..{span[1]}")
            if c_sh.get('order') == 'chronological' and prev and d < prev[0] and not s['spec'].get('flashback'):
                issues.append(f"CHRONOLOGY {c_tl['name']}/{s['id']}: {os.path.basename(m)} ({d}) comes after {prev[1]} ({prev[0]}) (mark \"flashback\": true if intended)")
            prev = (d, os.path.basename(m))
for m, where in uses.items():
    if len(where) > 1: issues.append(f'REUSE {os.path.basename(m)} in {", ".join(where)}')
facts = open(os.path.join(ROOT, 'facts.md'), encoding='utf-8').read() if os.path.exists(os.path.join(ROOT, 'facts.md')) else ''
named = re.findall(r'^\s*-\s*\*\*(.+?)\*\*', facts, re.M)      # people map lines look like: - **Name**: relation, what the hero calls them
for p in named:
    if people and cast[p] == 0: issues.append(f'CAST {p} is in the people map but on screen for 0 s')
target = CFG.get('target_minutes')
if target: issues.append(f'RUNTIME {TL["total"] / 60:.1f} min vs target {target} min') if abs(TL['total'] / 60 - target) > 0.05 * target else None
for i in issues: print(i)
if cast:
    print('screen seconds:', ', '.join(f'{p} {t:.0f}s' for p, t in cast.most_common()))
print(f'{len(issues)} story issues' + ('' if dates else ' (no inventory dates: run tools/archive/inventory.py for chronology checks)'))
