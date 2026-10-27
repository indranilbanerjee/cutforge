"""Move big files over slow or fragile links (a remote bridge, a flaky upload) in small verified parts.
  split   python tools/deliver/parts.py split <file> [--mib 15] [--out dir]   -> <name>.000 ... + <name>.manifest.json
  join    python tools/deliver/parts.py join <manifest.json> [--budget 150]   resumable: run again until it says COMPLETE
  verify  python tools/deliver/parts.py verify <manifest.json>                md5 of every part present
The joiner never deletes anything: it truncates the output to the last verified part boundary and appends, so a
call that is cut off (time limits on remote shells) loses nothing. Checks every part's md5 before using it and the
whole file's md5 at the end. Ask first what the far side already has: often a big file can be rebuilt there instead
(tools/deliver/recover_chapters.py)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, json, hashlib, time


def md5(p, n=None):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        left = n
        while True:
            b = f.read(8 << 20 if left is None else min(8 << 20, left))
            if not b: break
            h.update(b)
            if left is not None:
                left -= len(b)
                if left <= 0: break
    return h.hexdigest()


a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
cmd, target = a[0], a[1]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d

if cmd == 'split':
    mib = int(opt('--mib', 15)); size = mib << 20; outd = opt('--out', os.path.dirname(os.path.abspath(target)))
    os.makedirs(outd, exist_ok=True); base = os.path.basename(target); parts = []
    with open(target, 'rb') as f:
        k = 0
        while True:
            b = f.read(size)
            if not b: break
            pn = f'{base}.{k:03d}'; open(os.path.join(outd, pn), 'wb').write(b)
            parts.append({'name': pn, 'bytes': len(b), 'md5': hashlib.md5(b).hexdigest()}); k += 1
    man = {'file': base, 'bytes': os.path.getsize(target), 'md5': md5(target), 'part_bytes': size, 'parts': parts}
    json.dump(man, open(os.path.join(outd, base + '.manifest.json'), 'w'), indent=1)
    print(f'{len(parts)} parts of {mib} MiB + {base}.manifest.json in {outd}')

elif cmd in ('join', 'verify'):
    man = json.load(open(target)); d = os.path.dirname(os.path.abspath(target)); out = os.path.join(d, man['file'])
    if cmd == 'verify':
        bad = [p['name'] for p in man['parts'] if not os.path.exists(os.path.join(d, p['name'])) or md5(os.path.join(d, p['name'])) != p['md5']]
        print('all parts OK' if not bad else f'missing or bad: {" ".join(bad)}'); sys.exit(1 if bad else 0)
    t0 = time.time(); budget = float(opt('--budget', 1e9)); PB = man['part_bytes']
    have = os.path.getsize(out) if os.path.exists(out) else 0
    k = have // PB
    if os.path.exists(out) and k * PB != have:
        with open(out, 'r+b') as f: f.truncate(k * PB)
    if not os.path.exists(out): open(out, 'wb').close()
    with open(out, 'ab') as fo:
        for p in man['parts'][k:]:
            if time.time() - t0 > budget: print(f'PAUSED at part {p["name"]} ({k}/{len(man["parts"])}); run again'); sys.exit(3)
            pp = os.path.join(d, p['name'])
            if not os.path.exists(pp): print('missing part', p['name']); sys.exit(2)
            b = open(pp, 'rb').read()
            if hashlib.md5(b).hexdigest() != p['md5']: print('BAD part (re-send it):', p['name']); sys.exit(2)
            fo.write(b); k += 1
    ok = md5(out) == man['md5']
    print('COMPLETE, md5 verified' if ok else 'joined but md5 MISMATCH: re-verify parts'); sys.exit(0 if ok else 1)
