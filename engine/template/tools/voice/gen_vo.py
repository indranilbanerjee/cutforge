"""Generate every narration line, trim it, loudness-match it, and verify it by speech-to-text.
Reads film/script.json ("voice" settings + lines with id/text/dir) and film/respell.json (engine-only spellings).
Writes sound/vo/<id>.wav (48 kHz mono), film/vo_durs.json (for film/timeline.py) and film/vo_check.json.

usage: python tools/voice/gen_vo.py [ids...]      no ids = every line missing or not yet verified
       python tools/voice/gen_vo.py --all         regenerate everything (old takes are copied to sound/vo_prev/)
Recorded human takes (tools/voice/import_vo.py) are never regenerated unless their id is named explicitly.
Rules this enforces (from real productions):
  - captions keep the correct spelling; the ENGINE gets the respelled text (names, loanwords, numerals)
  - pace comes from each line's "dir" (slow/tender ... brisk/comic), not one global speed
  - each line -18 LUFS, peak <= 0.95, silence trimmed with a small head and tail
  - every line is transcribed back and fuzzy-matched; below the threshold it is listed as CHECK (listen, respell, regenerate
    BY ID: a bare run skips lines that were generated, even with low similarity); a failed STT is listed as UNVERIFIED
  - voice.stt_provider: "sarvam" (default for Indian languages) or "openai" (default otherwise)
  - paid providers pass the budget gate first (GO_AHEAD.txt + config.budget_inr)"""
import os, sys, json, re, time, shutil, concurrent.futures as cf
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import FILM, VO_DIR, SOUND, load_json, save_json
import tts as T

S = load_json(os.path.join(FILM, 'script.json'))
V = S.get('voice', {'provider': 'placeholder'})
RESPELL = load_json(os.path.join(FILM, 'respell.json'), {})
CHK_F = os.path.join(FILM, 'vo_check.json'); CHK = load_json(CHK_F, {})
TARGET = float(V.get('lufs', -18.0))
THRESH = float(V.get('verify_threshold', 85))
COST_PER_1K_CHARS = float(V.get('inr_per_1k_chars', 3.0))     # set from the provider's price; used by the budget gate
INDIC = {'bn', 'hi', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'pa', 'or', 'od', 'as', 'ur'}
LANG = V.get('lang') or S.get('language') or 'en-IN'
STT_PROVIDER = V.get('stt_provider') or ('sarvam' if LANG.split('-')[0] in INDIC else 'openai')


def pace(d):
    """engine pace from the line's direction; voice.pace_scale nudges the whole voice faster or slower"""
    d = (d or '').lower(); k = float(V.get('pace_scale', 1.0))
    if any(w in d for w in ('slowest', 'whisper', 'hushed')): return round(0.78 * k, 3)
    if any(w in d for w in ('slow', 'tender', 'reverent', 'grave', 'awe', 'chant', 'quiet')): return round(0.84 * k, 3)
    if any(w in d for w in ('brisk', 'fast', 'lively', 'comic', 'rhythmic', 'excited')): return round(0.97 * k, 3)
    if any(w in d for w in ('list', 'proclaim', 'festive', 'bright', 'herald')): return round(0.93 * k, 3)
    return round(0.89 * k, 3)


def respell(t):
    for a, b in RESPELL.items():
        if not a.startswith('_'): t = t.replace(a, b)
    return t.replace('\u200c', '').replace('\u200d', '') if V.get('strip_joiners', True) else t


def norm(t):
    t = re.sub(r'[।,…!?\-–—"“”‘’\'.:;()]', ' ', t); return re.sub(r'\s+', ' ', t).strip().lower()


def trim(y, sr, head=0.12, tail=0.25, thr=-45):
    a = np.abs(y); w = max(1, int(sr * 0.01)); env = np.convolve(a, np.ones(w) / w, 'same')
    idx = np.where(env > 10 ** (thr / 20) * max(env.max(), 1e-9))[0]
    if len(idx) == 0: return y
    y = y[max(0, idx[0] - int(sr * head)):min(len(y), idx[-1] + int(sr * tail))].copy()
    f = int(sr * 0.02); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def one(line):
    lid, text = line['id'], line['text']
    out = os.path.join(VO_DIR, lid + '.wav'); raw = os.path.join(VO_DIR, '_raw', lid + '.wav')
    p = float(line.get('pace') or pace(line.get('dir', '')))
    for attempt in range(3):
        try:
            T.tts(raw, respell(text), V, p, line.get('dir', '')); break
        except Exception as e:
            if attempt == 2: return lid, {'ok': False, 'err': str(e)[:200]}
            time.sleep(3 + 4 * attempt)
    y, sr = sf.read(raw, dtype='float32')
    if y.ndim > 1: y = y.mean(1)
    if V.get('provider') != 'placeholder':
        y = trim(y, sr)
        try:
            import pyloudnorm as pyln
            L = pyln.Meter(sr).integrated_loudness(y)
            if np.isfinite(L): y = y * 10 ** ((TARGET - L) / 20)
        except Exception:
            L = float('nan')
        pk = np.abs(y).max()
        if pk > 0.95: y = y * (0.95 / pk)
    else:
        L = float('nan')
    sf.write(out, y, sr, subtype='PCM_16')
    r = {'ok': True, 'provider': V.get('provider'), 'pace': p, 'dur': round(len(y) / sr, 3), 'lufs': None if not np.isfinite(L) else round(float(L), 1)}
    if V.get('provider') == 'placeholder':
        r.update({'sim': None, 'heard': 'PLACEHOLDER'}); return lid, r
    if V.get('verify', True):
        try:
            import stt as STT
            from rapidfuzz import fuzz
            heard = STT.stt(out, LANG, STT_PROVIDER) or ''
            r.update({'heard': heard, 'sim': fuzz.ratio(norm(text), norm(heard))})
        except Exception as e:
            r.update({'heard': '', 'sim': None, 'stt_err': str(e)[:120]})
    return lid, r


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    os.makedirs(os.path.join(VO_DIR, '_raw'), exist_ok=True)
    if '--all' in sys.argv and os.listdir(VO_DIR):
        prev = os.path.join(SOUND, 'vo_prev'); os.makedirs(prev, exist_ok=True)
        for f in os.listdir(VO_DIR):
            if f.endswith('.wav'): shutil.copy2(os.path.join(VO_DIR, f), os.path.join(prev, f))
    rec = {k for k, v in CHK.items() if v.get('provider') == 'recorded'}      # human takes (import_vo.py): never overwritten
    lines = [l for l in S['lines'] if (l['id'] in args) or ('--all' in sys.argv and l['id'] not in rec) or
             (not args and l['id'] not in rec and not (CHK.get(l['id'], {}).get('ok') and (CHK[l['id']].get('provider') == V.get('provider'))))]
    if V.get('provider') in T.PAID and lines:
        from spend import gate, log
        chars = sum(len(l['text']) for l in lines); est = chars / 1000 * COST_PER_1K_CHARS * (2 if V.get('verify', True) else 1)
        gate('tts:' + V['provider'], est)
    print('generating', len(lines), 'lines with', V.get('provider'))
    with cf.ThreadPoolExecutor(int(V.get('threads', 3))) as ex:
        for lid, r in ex.map(one, lines):
            CHK[lid] = r; save_json(CHK_F, CHK)
            sim = r.get('sim')
            flag = '' if (sim is None or sim >= THRESH) else f'CHECK heard: {r.get("heard", "")[:80]}'
            print(f"{lid:8} {r.get('dur', '-'):>6}s  sim {sim}  {flag or r.get('err', '')}")
    if V.get('provider') in T.PAID and lines:
        log('tts:' + V['provider'], V.get('model', ''), f'{len(lines)} lines', est)
    durs = {l['id']: CHK[l['id']]['dur'] for l in S['lines'] if CHK.get(l['id'], {}).get('ok')}
    save_json(os.path.join(FILM, 'vo_durs.json'), durs, indent=0)
    low = [k for k, v in CHK.items() if v.get('ok') and v.get('sim') is not None and v['sim'] < THRESH]
    unver = [k for k, v in CHK.items() if v.get('ok') and v.get('sim') is None and v.get('provider') not in ('placeholder', 'recorded')]
    print('done:', len(durs), 'lines measured')
    if low: print('  CHECK (low similarity): listen, fix respell.json or the text, then regenerate by id:', ' '.join(low))
    if unver: print('  UNVERIFIED (speech-to-text failed or off): listen to these yourself or fix stt_provider:', ' '.join(unver))
    if not low and not unver: print('  all lines verified (placeholder and recorded lines are not machine-checked)')
    print('next: python film/timeline.py')
