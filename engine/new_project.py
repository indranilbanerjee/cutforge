"""Start a CutForge project: copy the engine template into a new folder and write the project's memory files.
usage: python new_project.py <target folder> --title "Film title" [--format landscape|vertical|square] [--lang bn-IN]
                             [--budget 400] [--target-minutes 15] [--keys path/to/API_Keys.txt] [--demo]
Then: cd <target>; npm install; python tools/setup_local.py
--demo keeps the demo film (procedural media, English) in the chosen --format so the whole pipeline can be tested
end to end in minutes. Chapter names must be letters, digits and hyphens (they become Remotion composition ids).
Never point <target> at an existing folder with content: this refuses to overwrite anything."""
import os, sys, shutil, json, argparse, datetime, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('target'); ap.add_argument('--title', default='Untitled film'); ap.add_argument('--format', default='landscape')
ap.add_argument('--lang', default='en-IN'); ap.add_argument('--budget', type=float); ap.add_argument('--target-minutes', type=float)
ap.add_argument('--keys'); ap.add_argument('--demo', action='store_true')
a = ap.parse_args()
T = os.path.abspath(a.target)
PLUGIN = os.path.dirname(HERE)


def inside(child, parent):
    try:
        return os.path.commonpath([os.path.normcase(child), os.path.normcase(parent)]) == os.path.normcase(parent)
    except ValueError:                     # different drives on Windows
        return False


if inside(T, PLUGIN):
    print(f'{T} is inside the CutForge plugin folder ({PLUGIN}): copying the template into itself would never end. '
          'Pick a folder outside the plugin, for example next to your footage.', file=sys.stderr)
    sys.exit(2)
if os.path.exists(T) and os.listdir(T):
    print(f'{T} exists and is not empty: pick a new folder (CutForge never overwrites).', file=sys.stderr)
    sys.exit(2)
shutil.copytree(os.path.join(HERE, 'template'), T, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('node_modules', '__pycache__', 'out', '*.pyc'))
# A Windows clone with core.autocrlf=true writes the .sh files with CRLF line ends, which bash rejects ("syntax error near
# unexpected token"). The project always gets LF.
for dirpath, _dirs, files in os.walk(T):
    for f in files:
        if f.endswith('.sh'):
            sp = os.path.join(dirpath, f)
            data = open(sp, 'rb').read()
            if b'\r\n' in data:
                open(sp, 'wb').write(data.replace(b'\r\n', b'\n'))
for d in ['sound/vo', 'sound/music', 'sound/sfx', 'sound/own', 'inbox', 'out', 'public/media', 'public/art']:
    os.makedirs(os.path.join(T, d), exist_ok=True)
fmt = {'landscape': {'w': 1280, 'h': 720, 'fps': 25, 'scale': 1.5}, 'vertical': {'w': 720, 'h': 1280, 'fps': 30, 'scale': 1.5},
       'square': {'w': 1080, 'h': 1080, 'fps': 30, 'scale': 1}}[a.format]
slug = ''.join(ch if ch.isalnum() else '_' for ch in a.title).strip('_')[:40] or 'film'
cfg = {'title': a.title, 'slug': slug, 'folders': {}, 'api_keys_file': a.keys, 'budget_inr': a.budget, 'target_minutes': a.target_minutes,
       'mix': {'lufs': -16.0, 'tp': -2.0, 'room_tone': True}, 'gl': None, 'concurrency': 2, 'browser_executable': None}
json.dump(cfg, open(os.path.join(T, 'config.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
today = datetime.date.today().isoformat()
for f in os.listdir(os.path.join(HERE, 'templates')):
    s = open(os.path.join(HERE, 'templates', f), encoding='utf-8-sig').read().replace('{{TITLE}}', a.title).replace('{{DATE}}', today)
    open(os.path.join(T, f), 'w', encoding='utf-8').write(s)
if not a.demo:
    shots = {'title': a.title, 'format': fmt, 'chapters': [{'name': 'ch1', 'shots': [{'id': 'A1', 'fixed': 3.0, 'layout': 'title', 'bg': 'black', 'text': a.title, 'caps': False}]}]}
    json.dump(shots, open(os.path.join(T, 'film', 'shots.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump({'title': a.title, 'language': a.lang, 'voice': {'provider': 'placeholder', 'lang': a.lang}, 'lines': []},
              open(os.path.join(T, 'film', 'script.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(T, 'film', 'cues.py'), 'w', encoding='utf-8').write(
        open(os.path.join(HERE, 'template', 'film', 'cues.py'), encoding='utf-8-sig').read().split('SY = ')[0] + "SY = 'sound/synth/'\n\n\ndef build(S):\n    pass\n")
    open(os.path.join(T, 'src', 'chapters', 'index.ts'), 'w', encoding='utf-8').write(
        "// Register hand-built chapters here: {chapterName: Component}. Others render with AutoChapter from film/shots.json.\n"
        "import React from 'react';\n\nexport const CUSTOM: Record<string, React.FC<any>> = {\n};\n")
    os.remove(os.path.join(T, 'src', 'chapters', 'Example.tsx'))
else:
    sf = os.path.join(T, 'film', 'shots.json'); shots = json.load(open(sf, encoding='utf-8-sig'))
    shots['format'] = fmt                         # the demo follows --format (its hand-built example chapter is laid out for landscape)
    json.dump(shots, open(sf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
py = sys.executable
subprocess.run([py, os.path.join(T, 'film', 'timeline.py'), '--quiet'])
print(f'project ready: {T}\nnext:\n  cd "{T}"\n  npm install\n  python tools/setup_local.py\n  python tools/mix/synth.py      (beds, bells, room tone)\n  bash tools/text/shapeall.sh    (shaped titles from tools/text/shape_jobs.json)' + ('\n  python tools/demo_assets.py   (demo media)' if a.demo else ''))
