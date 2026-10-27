"""Resumable verified copy of big files onto a slow or remote drive: resumes each file from a 16 MiB boundary,
md5-checks source vs copy, marks finished files with <name>.copied next to the SOURCE. Never deletes.
usage: python tools/deliver/rcopy.py <src_dir> <dst_dir> <budget_seconds> file [file ...]"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, time, hashlib
if len(sys.argv) < 5: sys.exit(__doc__)
src_dir, dst_dir, budget = sys.argv[1], sys.argv[2], float(sys.argv[3]); names = sys.argv[4:]
t0 = time.time(); CH = 16 << 20


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''): h.update(b)
    return h.hexdigest()


os.makedirs(dst_dir, exist_ok=True)
for n in names:
    s, d, ok = os.path.join(src_dir, n), os.path.join(dst_dir, n), os.path.join(src_dir, n + '.copied')
    if os.path.exists(ok): continue
    size = os.path.getsize(s); have = os.path.getsize(d) if os.path.exists(d) else 0
    have = min(have, size) // CH * CH
    with open(s, 'rb') as fi, open(d, 'r+b' if os.path.exists(d) else 'wb') as fo:
        fo.truncate(have); fi.seek(have); fo.seek(have)
        while True:
            if time.time() - t0 > budget: print('PAUSED in', n, have >> 20, 'of', size >> 20, 'MiB; run again'); sys.exit(3)
            b = fi.read(CH)
            if not b: break
            fo.write(b); have += len(b)
    if md5(s) == md5(d): open(ok, 'w').write('ok'); print('copied+verified', n, size >> 20, 'MiB')
    else: print('MD5 MISMATCH', n); os.truncate(d, 0)
print('COMPLETE')
