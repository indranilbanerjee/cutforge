"""One-time setup check on any machine (Windows, macOS, Linux). Safe to re-run.
- checks node/npm/ffmpeg/ffprobe/python and the Python modules the tools need
- checks node_modules (run `npm install` once), Python UTF-8 mode on Windows, the key file if one is configured
- renders the synthesised sound set (sound/synth) and builds the timeline
usage: python tools/setup_local.py"""
import os, sys, shutil, subprocess, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, CFG

ok = True
for cmd in ['node', 'npm', 'ffmpeg', 'ffprobe']:
    p = shutil.which(cmd); print(f'  {cmd:8} {"ok  " + p if p else "MISSING"}'); ok &= bool(p)
if shutil.which('node'):
    v = subprocess.run(['node', '--version'], capture_output=True, text=True).stdout.strip()
    print(f'  node {v}' + ('' if int(v.lstrip('v').split('.')[0]) >= 18 else '  <- need Node 18+'))
need = {'numpy': 'numpy', 'soundfile': 'soundfile', 'pedalboard': 'pedalboard', 'pyloudnorm': 'pyloudnorm', 'rapidfuzz': 'rapidfuzz',
        'cv2': 'opencv-python', 'PIL': 'pillow', 'scipy': 'scipy'}
optional = {'onnxruntime': 'onnxruntime (depth maps, faces)', 'rembg': 'rembg (cut-outs)', 'open_clip': 'open_clip_torch + torch (archive search)'}
miss = [pkg for mod, pkg in need.items() if importlib.util.find_spec(mod) is None]
print('  python modules:', 'all present' if not miss else 'MISSING -> pip install ' + ' '.join(miss)); ok &= not miss
for mod, what in optional.items():
    if importlib.util.find_spec(mod) is None: print(f'  optional: {what} not installed')
if os.name == 'nt' and not sys.flags.utf8_mode:
    print('  !! Python is not in UTF-8 mode: run  setx PYTHONUTF8 1  and open a new terminal (Indic text needs it)')
if not os.path.exists(os.path.join(ROOT, 'node_modules')):
    print('  node_modules missing -> run: npm install'); ok = False
kf = CFG.get('api_keys_file')
if kf: print('  key file:', 'found' if os.path.exists(kf) else 'NOT FOUND at ' + kf)
for d in ['out/ch', 'out/final', 'out/qc', 'out/mix', 'sound/vo', 'sound/synth', 'inbox']:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)
if not miss:
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'mix', 'synth.py')], cwd=ROOT)
    subprocess.run([sys.executable, os.path.join(ROOT, 'film', 'timeline.py'), '--quiet'], cwd=ROOT)
print('setup', 'OK' if ok else 'INCOMPLETE (fix the lines above)')
