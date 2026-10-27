"""One-time setup check on any machine (Windows, macOS, Linux). Safe to re-run.
- checks node (22 or newer), npm, ffmpeg, ffprobe and python, and that node_modules holds the Remotion version package.json pins
- checks the Python modules the tools need (install_deps.py prints the exact pinned command for any that are missing)
- renders the synthesised sound set (sound/synth) and builds the timeline
usage: python tools/setup_local.py
Exit status: 0 everything required is present, 1 something is missing or too old."""
import os, sys, shutil, subprocess, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, CFG
import envcheck, install_deps

ok = True
notice = envcheck.python_notice()
if notice:
    print('  note:', notice)
for cmd in ['node', 'npm', 'ffmpeg', 'ffprobe']:
    p = shutil.which(cmd); print(f'  {cmd:8} {"ok  " + p if p else "MISSING"}'); ok &= bool(p)
node = envcheck.node_version()
if node:
    old = node[0] < envcheck.NODE_MIN
    print(f'  node {node[1]}' + (f'  <- need Node {envcheck.NODE_MIN} or newer (older lines are end of life)' if old else ''))
    ok &= not old
ff = envcheck.ffmpeg_major()
if ff and ff[0] is not None:
    print(f'  {ff[1]}' + ('' if ff[0] >= envcheck.FFMPEG_WARN_BELOW else
                         f'  <- older than {envcheck.FFMPEG_WARN_BELOW}.x: a filter the tools use may be missing; upgrade ffmpeg'))
pinned, installed = envcheck.remotion_pin_and_installed(ROOT)
if pinned and installed and pinned != installed:
    print(f'  remotion in node_modules is {installed} but package.json pins {pinned}: run  npm install'); ok = False
elif installed:
    print(f'  remotion {installed} (matches the pin)')
miss = [p for p in install_deps.GROUPS['core'] if not install_deps.present(p)]
print('  python modules:', 'all present' if not miss else 'MISSING -> ' + install_deps.install_command(miss)); ok &= not miss
optional = {'onnxruntime': 'onnxruntime (depth maps, faces)', 'rembg': 'rembg (cut-outs)', 'open_clip': 'open_clip_torch + torch (archive search)'}
for mod, what in optional.items():
    if importlib.util.find_spec(mod) is None: print(f'  optional: {what} not installed (python tools/install_deps.py --groups depth cutouts archive-search)')
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
sys.exit(0 if ok else 1)
