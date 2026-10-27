"""Inventory a media library: every photo, video and audio file with its real capture date, GPS, size, rotation,
duration and a quick fingerprint for duplicates. The first step of any archive-based film: chronology comes from
here, never from memory or file names alone.

usage: python tools/archive/inventory.py <folder> [<folder> ...] [--out out/archive/inventory.csv] [--threads 8]
       (folders may also be names from config.json "folders")
Dates, best source first: EXIF DateTimeOriginal (photos) > container creation_time (videos) > a date in the file
name (20230403_123019, IMG-20250304-WA0009, IMG20201115204842, Screenshot_2024...) > file modified time (marked).
Re-running only reads files that changed. Read-only: never writes into the scanned folders."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, re, csv, json, hashlib, subprocess, datetime, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT, CFG

PHOTO = ('.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.tif', '.tiff', '.dng', '.gif', '.bmp')
VIDEO = ('.mp4', '.mov', '.m4v', '.3gp', '.mkv', '.avi', '.webm', '.mts')
AUDIO = ('.m4a', '.mp3', '.wav', '.aac', '.ogg', '.opus', '.flac', '.amr')
FIELDS = ['path', 'kind', 'bytes', 'mtime', 'date', 'date_src', 'lat', 'lon', 'w', 'h', 'dur', 'rot', 'camera', 'qhash']
NAME_PATS = [
    (re.compile(r'(20\d\d)(\d\d)(\d\d)[_-]?(\d\d)(\d\d)(\d\d)'), lambda m: f'{m[1]}-{m[2]}-{m[3]} {m[4]}:{m[5]}:{m[6]}'),
    (re.compile(r'(20\d\d)-(\d\d)-(\d\d)[ _-](\d\d)[.-](\d\d)[.-](\d\d)'), lambda m: f'{m[1]}-{m[2]}-{m[3]} {m[4]}:{m[5]}:{m[6]}'),
    (re.compile(r'(20\d\d)(\d\d)(\d\d)'), lambda m: f'{m[1]}-{m[2]}-{m[3]} 00:00:00'),
]


def qhash(p, size):
    h = hashlib.md5(str(size).encode())
    with open(p, 'rb') as f:
        h.update(f.read(1 << 20))
        if size > 2 << 20: f.seek(-(1 << 20), 2); h.update(f.read(1 << 20))
    return h.hexdigest()[:16]


def gps_deg(v, ref):
    try:
        d, m, s = [float(x) for x in v]
        x = d + m / 60 + s / 3600
        return round(-x if ref in ('S', 'W') else x, 6)
    except Exception:
        return ''


def photo_meta(p):
    from PIL import Image
    r = {}
    try:
        im = Image.open(p)
        r['w'], r['h'] = im.size
        ex = im.getexif()
        sub = ex.get_ifd(0x8769) if ex else {}
        dt = sub.get(36867) or sub.get(36868) or ex.get(306)
        if dt: r['date'] = str(dt).replace(':', '-', 2)[:19]; r['date_src'] = 'exif'
        ori = ex.get(274)
        if ori in (6, 8): r['w'], r['h'] = r['h'], r['w']; r['rot'] = {6: 90, 8: 270}[ori]
        mk, md = ex.get(271), ex.get(272)
        if mk or md: r['camera'] = f'{mk or ""} {md or ""}'.strip()
        g = ex.get_ifd(0x8825) if ex else {}
        if g and 2 in g and 4 in g:
            r['lat'], r['lon'] = gps_deg(g[2], g.get(1)), gps_deg(g[4], g.get(3))
    except Exception:
        pass
    return r


def video_meta(p):
    r = {}
    q = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', p], capture_output=True, text=True)
    try:
        j = json.loads(q.stdout)
    except Exception:
        return r
    fmt = j.get('format', {}); tags = {k.lower(): v for k, v in fmt.get('tags', {}).items()}
    r['dur'] = round(float(fmt.get('duration', 0) or 0), 2)
    ct = tags.get('creation_time') or tags.get('com.apple.quicktime.creationdate')
    if ct and not ct.startswith('1970') and not ct.startswith('1904'):
        r['date'] = ct.replace('T', ' ')[:19]; r['date_src'] = 'container'
    loc = tags.get('location') or tags.get('com.apple.quicktime.location.iso6709')
    if loc:
        m = re.match(r'([+-]\d+\.\d+)([+-]\d+\.\d+)', loc)
        if m: r['lat'], r['lon'] = float(m[1]), float(m[2])
    for s in j.get('streams', []):
        if s.get('codec_type') == 'video':
            w, h = s.get('width'), s.get('height')
            rot = int(float(s.get('tags', {}).get('rotate', 0) or 0))
            for sd in s.get('side_data_list', []) or []:
                if 'rotation' in sd: rot = int(float(sd['rotation']))
            rot = rot % 360
            r['rot'] = rot
            r['w'], r['h'] = (h, w) if rot in (90, 270) else (w, h)
            break
    mk = tags.get('com.apple.quicktime.make') or tags.get('make'); md = tags.get('com.apple.quicktime.model') or tags.get('model')
    if mk or md: r['camera'] = f'{mk or ""} {md or ""}'.strip()
    return r


def one(p):
    st = os.stat(p); ext = os.path.splitext(p)[1].lower()
    kind = 'photo' if ext in PHOTO else 'video' if ext in VIDEO else 'audio' if ext in AUDIO else None
    if not kind: return None
    r = {'path': p, 'kind': kind, 'bytes': st.st_size, 'mtime': datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}
    r.update(photo_meta(p) if kind == 'photo' else video_meta(p))
    if not r.get('date'):
        base = os.path.basename(p)
        for pat, f in NAME_PATS:
            m = pat.search(base)
            if m:
                try:
                    d = f(m); datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S'); r['date'] = d; r['date_src'] = 'filename'; break
                except ValueError:
                    pass
    if not r.get('date'): r['date'], r['date_src'] = r['mtime'], 'mtime (unreliable)'
    r['qhash'] = qhash(p, st.st_size)
    return r


if __name__ == '__main__':
    args = sys.argv[1:]
    out = args[args.index('--out') + 1] if '--out' in args else os.path.join(OUT, 'archive', 'inventory.csv')
    th = int(args[args.index('--threads') + 1]) if '--threads' in args else 8
    roots = [a for i, a in enumerate(args) if not a.startswith('--') and (i == 0 or args[i - 1] not in ('--out', '--threads'))]
    roots = [CFG.get('folders', {}).get(r, r) for r in roots]
    if not roots: sys.exit(__doc__)
    old = {}
    if os.path.exists(out):
        for r in csv.DictReader(open(out, encoding='utf-8-sig')): old[(r['path'], r['bytes'], r['mtime'])] = r
    files = [os.path.join(dp, f) for root in roots for dp, _, fs in os.walk(root) for f in fs if not f.startswith('.')]
    rows, todo = [], []
    for p in files:
        try:
            st = os.stat(p)
        except OSError:
            continue
        k = (p, str(st.st_size), datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
        (rows.append(old[k]) if k in old else todo.append(p))
    print(f'{len(files)} files, {len(rows)} unchanged, reading {len(todo)}', flush=True)
    with cf.ThreadPoolExecutor(th) as ex:
        for i, r in enumerate(ex.map(one, todo)):
            if r: rows.append(r)
            if i and i % 500 == 0: print(f'  {i}/{len(todo)}', flush=True)
    rows.sort(key=lambda r: (r.get('date') or '', r['path']))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, FIELDS, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    by = {}
    for r in rows: by[r['kind']] = by.get(r['kind'], 0) + 1
    und = sum(1 for r in rows if r.get('date_src', '').startswith('mtime'))
    print(f'inventory: {out}  {by}  undated (mtime only): {und}')
