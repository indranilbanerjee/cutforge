"""AI image and video generation through a hosted API (WaveSpeed by default), with the production rules built in:
  1. Budget gate: refuses without GO_AHEAD.txt or past config.budget_inr; logs every call to spend.md.
  2. Face guard: refuses to send an input image with a detectable face to an edit or image-to-video model.
     AI goes only where no camera was. To style-transfer a real photo (e.g. an oil-portrait look) pass
     --allow-face-likeness: then compare faces before/after by eye and reject any change of likeness.
  3. Style suffix: config.json "style_suffix" is appended to every prompt so art matches across tools and shots.
  4. Provenance: prompt, model, inputs, seed and output go to out/ai_log.jsonl (and sources.md by you).
Licences differ per model and per host (commercial use, watermarks, required credits): see the plugin's
docs/compliance-and-licensing.md before client work.

usage:
  python tools/vfx/ai_gen.py image  <model path> out.png "prompt" [--inr 8] [--param k=v ...]
  python tools/vfx/ai_gen.py edit   <model path> out.png "prompt" --image in.jpg [--allow-face-likeness]
  python tools/vfx/ai_gen.py video  <model path> out.mp4 "motion prompt" --image plate.png [--param duration=5]
  <model path> is the host's model route, e.g. "google/nano-banana/edit" or a Kling image-to-video route; check the
  host's model page for the exact path and parameters (they change). Key: WAVESPEED_API_KEY (or WAVE_SPEED_API_KEY)."""
import os, sys, json, time, base64, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT, CFG
from keys import key
from spend import gate, log

API = 'https://api.wavespeed.ai/api/v3/'


def data_url(p):
    mime = 'image/png' if p.lower().endswith('.png') else 'image/jpeg'
    return f'data:{mime};base64,' + base64.b64encode(open(p, 'rb').read()).decode()


def has_face(p):
    try:
        import cv2, numpy as np
        from fetch_models import path as model
        img = cv2.imread(p)
        if img is None: return False
        h, w = img.shape[:2]; s = 1280 / max(h, w)
        if s < 1: img = cv2.resize(img, (int(w * s), int(h * s))); h, w = img.shape[:2]
        det = cv2.FaceDetectorYN.create(model('yunet'), '', (w, h), 0.7, 0.3, 5000)
        _, f = det.detect(img)
        return f is not None and len(f) > 0
    except Exception as e:
        print('face guard could not run:', e, '-> treating as "may contain a face"'); return True


def run(model, body, out, inr, note=''):
    hdr = {'Authorization': 'Bearer ' + key('WAVESPEED_API_KEY', 'WAVE_SPEED_API_KEY'), 'Content-Type': 'application/json'}
    gate('ai_gen', inr)
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request(API + model, data=json.dumps(body).encode(), headers=hdr), timeout=180))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code}: {e.read()[:300]!r}') from None
    pid = r['data']['id']
    for _ in range(360):
        time.sleep(5)
        q = json.load(urllib.request.urlopen(urllib.request.Request(f'{API}predictions/{pid}/result', headers=hdr), timeout=60))['data']
        if q['status'] == 'completed':
            urllib.request.urlretrieve(q['outputs'][0], out)
            log('ai_gen', model, note or os.path.basename(out), inr)
            return out
        if q['status'] == 'failed': raise RuntimeError(q.get('error'))
    raise TimeoutError(pid)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 4: sys.exit(__doc__)
    mode, model, out, prompt = a[:4]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    params = {}
    for i, x in enumerate(a):
        if x == '--param':
            k, v = a[i + 1].split('=', 1)
            try: params[k] = json.loads(v)
            except ValueError: params[k] = v
    suffix = CFG.get('style_suffix', '')
    body = {'prompt': (prompt + ' ' + suffix).strip() if mode != 'video' else prompt, **params}
    img = opt('--image')
    if mode in ('edit', 'video'):
        if not img: sys.exit('--image is required for edit and video')
        if has_face(img) and '--allow-face-likeness' not in a:
            sys.exit(f'REFUSED: {img} contains a face. No AI on real faces. Cut the person out (tools/vfx/cutout.py), '
                     'animate only the background, and composite the untouched person back on top.')
        if mode == 'edit': body['images'] = [data_url(img)]
        else: body['image'] = data_url(img)
    inr = float(opt('--inr', 10))
    res = run(model, body, out, inr, opt('--note', ''))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'ai_log.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps({'t': time.strftime('%Y-%m-%d %H:%M'), 'mode': mode, 'model': model, 'prompt': body['prompt'], 'params': params,
                            'input': img, 'output': res, 'inr': inr}, ensure_ascii=False) + '\n')
    print('saved', res, '| log: out/ai_log.jsonl | add the licence line to sources.md')
