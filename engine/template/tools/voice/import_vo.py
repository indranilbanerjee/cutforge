"""Import RECORDED narration (the client, family, talent reading the script) as narration lines: decode any format,
trim silence, -18 LUFS, peak 0.95, write sound/vo/<id>.wav (48 kHz mono), measure it into film/vo_durs.json, and mark
it "recorded" in film/vo_check.json so tools/voice/gen_vo.py never overwrites it.

usage: python tools/voice/import_vo.py <file or folder> [...] [--verify]
File names start with the script line id: 7Da.wav, 7Da_take2.m4a, 7Da-final.mp3 (text after _ or - is ignored).
With several takes for one id, the file listed last (or sorted last in a folder) wins: pass exact files to choose.
--verify transcribes each take back and fuzzy-matches it to the script like generated lines (paid STT: budget gate).
Then: python film/timeline.py"""
import os, sys, re, subprocess, numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import FILM, VO_DIR, save_json
from gen_vo import S, CHK, CHK_F, TARGET, THRESH, V, LANG, STT_PROVIDER, trim, norm

AUD = ('.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.webm', '.mp4', '.mov')
ids = {l['id']: l for l in S['lines']}
a = sys.argv[1:]
files = []
for x in [x for x in a if not x.startswith('--')]:
    if os.path.isdir(x):
        files += sorted(os.path.join(x, f) for f in os.listdir(x) if f.lower().endswith(AUD))
    elif os.path.exists(x):
        files.append(x)
if not files: sys.exit(__doc__)
pick = {}
for f in files:
    stem = os.path.splitext(os.path.basename(f))[0]
    lid = stem if stem in ids else re.split(r'[_\-\s]', stem)[0]
    if lid not in ids: print('  ? no script line for', os.path.basename(f)); continue
    pick[lid] = f
os.makedirs(VO_DIR, exist_ok=True)
for lid, f in pick.items():
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', f, '-vn', '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'], capture_output=True)
    if r.returncode or not r.stdout: print('  ! cannot decode', f); continue
    y = trim(np.frombuffer(r.stdout, np.float32).copy(), 48000)
    try:
        import pyloudnorm as pyln
        L = pyln.Meter(48000).integrated_loudness(y)
        if np.isfinite(L): y = y * 10 ** ((TARGET - L) / 20)
    except Exception:
        L = float('nan')
    pk = np.abs(y).max()
    if pk > 0.95: y = y * (0.95 / pk)
    out = os.path.join(VO_DIR, lid + '.wav')
    sf.write(out, y, 48000, subtype='PCM_16')
    res = {'ok': True, 'provider': 'recorded', 'source': os.path.basename(f), 'dur': round(len(y) / 48000, 3),
           'lufs': None if not np.isfinite(L) else round(float(L), 1), 'sim': None, 'heard': 'RECORDED'}
    if '--verify' in a:
        try:
            from spend import gate, log
            gate('stt', 0.5)
            import stt as STT
            from rapidfuzz import fuzz
            heard = STT.stt(out, LANG, STT_PROVIDER) or ''
            res.update({'heard': heard, 'sim': fuzz.ratio(norm(ids[lid]['text']), norm(heard))})
            log('stt', STT_PROVIDER, f'verify recorded {lid}', 0.5)
        except Exception as e:
            res['stt_err'] = str(e)[:120]
    CHK[lid] = res
    sim = res.get('sim')
    print(f"{lid:8} {res['dur']:>6}s  from {res['source']}" + (f'  sim {sim}' + ('  CHECK' if sim is not None and sim < THRESH else '') if sim is not None else ''))
save_json(CHK_F, CHK)
durs = {l['id']: CHK[l['id']]['dur'] for l in S['lines'] if CHK.get(l['id'], {}).get('ok')}
save_json(os.path.join(FILM, 'vo_durs.json'), durs, indent=0)
print(f'imported {len(pick)} recorded lines; next: python film/timeline.py')
