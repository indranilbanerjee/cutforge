"""Group the faces in a library so the CLIENT can say who is who. This sorts; it never decides identity.
(Real productions shipped wrong names when a cousin was taken for the father: only the client labels people.)

step 1  python tools/archive/faces.py scan [--from 2023-01] [--to 2026-12] [--kind photo|video] [--min 60]
        detects faces (YuNet), embeds them (SFace), clusters by cosine similarity, writes
        out/archive/faces/clusters.json and one sheet per cluster: out/archive/faces/cluster_<k>.jpg
step 2  send the sheets to the client (or a photo-map page). Write film/face_labels.json: {"<k>": "Name", ...}
        ("?" or a missing key = unknown; never guess)
step 3  python tools/archive/faces.py apply
        writes film/people_in_media.json {media path: [names]} for screen-time counts (tools/qc/qc_story.py)
        and crops each labelled person's best face to public/faces/<name>_<n>.jpg for people pages
Thresholds: SFace cosine >= 0.363 is OpenCV's 'same person' bar; clustering uses 0.42 to stay conservative."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, csv, json, subprocess, io, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import OUT, FILM, PUBLIC, load_json, save_json
from fetch_models import path as model

a = sys.argv[1:]; cmd = a[0] if a else 'scan'
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
FD = os.path.join(OUT, 'archive', 'faces'); os.makedirs(FD, exist_ok=True)


def load_img(r):
    if r['kind'] == 'video':
        t = max(0.0, float(r.get('dur') or 0) / 2)
        jpg = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(t), '-i', r['path'], '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'], capture_output=True).stdout
        return cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR) if jpg else None
    from PIL import Image, ImageOps
    try:
        im = ImageOps.exif_transpose(Image.open(r['path'])).convert('RGB'); im.thumbnail((1600, 1600))
        return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


if cmd == 'scan':
    det = cv2.FaceDetectorYN.create(model('yunet'), '', (320, 320), 0.85, 0.3, 5000)
    rec = cv2.FaceRecognizerSF.create(model('sface'), '')
    rows = [r for r in csv.DictReader(open(os.path.join(OUT, 'archive', 'inventory.csv'), encoding='utf-8-sig'))
            if r['kind'] in ('photo', 'video') and (not opt('--kind') or r['kind'] == opt('--kind'))
            and (not opt('--from') or r['date'][:7] >= opt('--from')) and (not opt('--to') or r['date'][:7] <= opt('--to'))]
    faces, embs = [], []
    for i, r in enumerate(rows):
        img = load_img(r)
        if img is None: continue
        h, w = img.shape[:2]; det.setInputSize((w, h))
        _, f = det.detect(img)
        for row in (f if f is not None else []):
            if row[2] < int(opt('--min', 60)) or row[3] < int(opt('--min', 60)): continue      # skip tiny background faces
            al = rec.alignCrop(img, row); e = rec.feature(al).flatten(); e /= np.linalg.norm(e) + 1e-9
            faces.append({'path': r['path'], 'date': r['date'], 'box': [int(x) for x in row[:4]], 'score': float(row[-1])}); embs.append(e)
            cv2.imwrite(os.path.join(FD, f'f{len(faces) - 1}.jpg'), al)
        if i and i % 200 == 0: print(f'  {i}/{len(rows)} files, {len(faces)} faces', flush=True)
    E = np.array(embs, np.float32); lab = -np.ones(len(E), int); cents = []
    order = np.argsort([-f['score'] for f in faces])
    for i in order:                                    # greedy: join the most similar centroid above the bar, else start a cluster
        if cents:
            sims = np.array([c @ E[i] / (np.linalg.norm(c) + 1e-9) for c in cents]); k = int(np.argmax(sims))
            if sims[k] >= 0.42: lab[i] = k; cents[k] = cents[k] + E[i]; continue
        lab[i] = len(cents); cents.append(E[i].copy())
    sizes = np.bincount(lab) if len(lab) else []
    clusters = {str(k): [int(i) for i in np.where(lab == k)[0]] for k in np.argsort(-np.array(sizes))[:200] if sizes[k] >= 2}
    save_json(os.path.join(FD, 'clusters.json'), {'faces': faces, 'clusters': clusters})
    from PIL import Image, ImageDraw
    for k, idx in clusters.items():
        sub = idx[:40]; cols = 10; rows_ = (len(sub) + cols - 1) // cols
        S = Image.new('RGB', (cols * 112, rows_ * 112 + 24), (20, 20, 24)); d = ImageDraw.Draw(S)
        d.text((6, 4), f'cluster {k}: {len(idx)} faces. Who is this? (write film/face_labels.json)', fill=(255, 220, 120))
        for j, i in enumerate(sub): S.paste(Image.open(os.path.join(FD, f'f{i}.jpg')), ((j % cols) * 112, 24 + (j // cols) * 112))
        S.save(os.path.join(FD, f'cluster_{k}.jpg'), quality=82)
    print(f'{len(faces)} faces in {len(clusters)} clusters (2+ faces). Sheets: {FD}/cluster_*.jpg. Ask the client to label them.')

elif cmd == 'apply':
    C = load_json(os.path.join(FD, 'clusters.json')); L = load_json(os.path.join(FILM, 'face_labels.json'), {})
    people = {}
    best = {}
    for k, idx in C['clusters'].items():
        name = L.get(k)
        if not name or name.strip() in ('?', ''): continue
        for i in idx:
            f = C['faces'][i]; people.setdefault(f['path'], set()).add(name)
            if f['score'] > best.get(name, (0, None))[0]: best[name] = (f['score'], i)
    # media paths in the film are relative to public/: map by file stem
    stems = {}
    for dp, _, fs in os.walk(PUBLIC):
        for fn in fs: stems.setdefault(os.path.splitext(fn)[0].lower(), os.path.relpath(os.path.join(dp, fn), PUBLIC).replace('\\', '/'))
    out = {}
    for p, names in people.items():
        rel = stems.get(os.path.splitext(os.path.basename(p))[0].lower())
        if rel: out[rel] = sorted(names)
    save_json(os.path.join(FILM, 'people_in_media.json'), out)
    os.makedirs(os.path.join(PUBLIC, 'faces'), exist_ok=True)
    for name, (_, i) in best.items():
        cv2.imwrite(os.path.join(PUBLIC, 'faces', f'{name.replace(" ", "_")}_1.jpg'), cv2.imread(os.path.join(FD, f'f{i}.jpg')))
    print(f'people_in_media.json: {len(out)} media files with labelled people; best crops in public/faces/ (112 px: re-crop larger from the source for print)')
