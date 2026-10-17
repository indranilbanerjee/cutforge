"""Extract a tar (or a tar split into parts) on a drive where deleting/overwriting by unlink is not allowed
(some remote mounts): writes by truncate+write, skips members already present with the same md5, resumable
under a time budget. Never deletes anything.
usage: python tools/deliver/xtar.py <dest> <budget_seconds> <archive.tar | part.000 part.001 ...>"""
import tarfile, os, sys, time, hashlib, io


class Cat(io.RawIOBase):
    def __init__(s, ps): s.ps = list(ps); s.f = open(s.ps.pop(0), 'rb')
    def readable(s): return True
    def readinto(s, b):
        while True:
            n = s.f.readinto(b)
            if n: return n
            if not s.ps: return 0
            s.f.close(); s.f = open(s.ps.pop(0), 'rb')


if len(sys.argv) < 4: sys.exit(__doc__)
dest, budget, parts = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
t0 = time.time(); w = k = 0
mode = 'r|gz' if parts[0].endswith('.gz') else 'r|*'
with tarfile.open(fileobj=io.BufferedReader(Cat(parts), 1 << 20), mode=mode) as tf:
    for m in tf:
        if time.time() - t0 > budget: print('PAUSED', w, 'written', k, 'already ok; run again'); sys.exit(3)
        p = os.path.join(dest, m.name)
        if not os.path.abspath(p).startswith(os.path.abspath(dest)): print('skip unsafe path', m.name); continue
        if m.isdir(): os.makedirs(p, exist_ok=True); continue
        if not m.isfile(): continue
        data = tf.extractfile(m).read()
        if os.path.exists(p) and os.path.getsize(p) == m.size and hashlib.md5(open(p, 'rb').read()).digest() == hashlib.md5(data).digest():
            k += 1; continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f: f.write(data)
        w += 1
print('COMPLETE written', w, 'already-ok', k)
