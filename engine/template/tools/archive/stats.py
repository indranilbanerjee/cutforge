"""What the library says on its own: photos and videos per month (silences and peaks are story), the big days
(bursts), places that recur (GPS clusters), duplicates and undated files. Output: out/archive/stats.md + monthly.png.
A near-empty stretch of months often marks something the family went through: ask, never assume, and never
narrate a reason the client has not given.
usage: python tools/archive/stats.py [out/archive/inventory.csv]"""
import os, sys, csv, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT

inv = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, 'archive', 'inventory.csv')
rows = list(csv.DictReader(open(inv, encoding='utf-8')))
dated = [r for r in rows if not r['date_src'].startswith('mtime')]
month = collections.Counter((r['date'][:7], r['kind']) for r in dated)
months = sorted({m for m, _ in month})
day = collections.Counter(r['date'][:10] for r in dated)
gps = collections.Counter((round(float(r['lat']), 2), round(float(r['lon']), 2)) for r in rows if r.get('lat') and r.get('lon'))
dups = collections.defaultdict(list)
for r in rows: dups[r['qhash']].append(r['path'])
dups = {k: v for k, v in dups.items() if len(v) > 1}
lines = [f'# Library statistics ({len(rows)} files, {len(dated)} with a real date)', '', '## Per month (photos / videos)', '']
if months:
    y0, m0 = map(int, months[0].split('-')); y1, m1 = map(int, months[-1].split('-'))
    y, m = y0, m0; peak = max(sum(month[(mm, k)] for k in ('photo', 'video')) for mm in months) or 1
    while (y, m) <= (y1, m1):
        key = f'{y}-{m:02d}'; p, v = month[(key, 'photo')], month[(key, 'video')]
        lines.append(f'`{key}` {p:5d} / {v:4d}  ' + '█' * int(40 * (p + v) / peak) + ('  ← nearly empty' if p + v < 0.05 * peak else ''))
        m += 1
        if m == 13: y, m = y + 1, 1
lines += ['', '## Biggest days (bursts usually mean an event)', ''] + [f'- {d}: {n} files' for d, n in day.most_common(25)]
lines += ['', '## Places that recur (GPS rounded to ~1 km)', ''] + [f'- {la}, {lo}: {n} files' for (la, lo), n in gps.most_common(15)]
lines += ['', f'## Duplicates: {len(dups)} groups', ''] + [f'- {" | ".join(os.path.basename(p) for p in v[:4])}' for v in list(dups.values())[:30]]
und = [r['path'] for r in rows if r['date_src'].startswith('mtime')]
lines += ['', f'## Undated (file time only, unreliable): {len(und)}', ''] + [f'- {os.path.basename(p)}' for p in und[:40]]
out = os.path.join(os.path.dirname(inv), 'stats.md'); open(out, 'w', encoding='utf-8').write('\n'.join(lines))
try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 3.5))
    ax.bar(range(len(months)), [month[(m, 'photo')] for m in months], color='#B3261E', label='photos')
    ax.bar(range(len(months)), [month[(m, 'video')] for m in months], bottom=[month[(m, 'photo')] for m in months], color='#22306B', label='videos')
    ax.set_xticks(range(0, len(months), max(1, len(months) // 24))); ax.set_xticklabels(months[::max(1, len(months) // 24)], rotation=60, fontsize=7)
    ax.legend(); ax.set_title('Files per month'); fig.tight_layout(); fig.savefig(os.path.join(os.path.dirname(inv), 'monthly.png'), dpi=110)
except Exception as e:
    print('(no chart:', e, ')')
print('stats:', out)
