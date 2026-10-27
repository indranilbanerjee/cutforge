"""Paths and settings for this project, from config.json at the project root (the folder with package.json).
Every tool imports this instead of hard-coding paths, so the project runs unchanged in a cloud workspace,
on Windows or on a Mac.

config.json keys (all optional):
  title            film title (metadata)
  folders          {"<name>": "<path>"}  the client's own folders, e.g. {"Archive": "D:/Family/Photos"}
  api_keys_file    a text file with one NAME=value per line (never printed); env vars win over it
  budget_inr       spend cap for paid APIs (tools refuse to run past it)
  browser_executable, gl, concurrency   renderer settings (see render.mjs)
"""
import os, json, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(TOOLS, '..'))
CFG_PATH = os.environ.get('CUTFORGE_CONFIG') or os.path.join(ROOT, 'config.json')
CFG = json.load(open(CFG_PATH, encoding='utf-8-sig')) if os.path.exists(CFG_PATH) else {}

FILM = os.path.join(ROOT, 'film')
PUBLIC = os.path.join(ROOT, 'public')
OUT = os.path.join(ROOT, 'out')
SOUND = os.path.join(ROOT, 'sound')          # audio lives here, NOT in public/ (public/ is copied into every render bundle)
VO_DIR = os.path.join(SOUND, 'vo')


def folder(name, *parts):
    """A client folder from config.json 'folders', e.g. folder('Archive', '2024')."""
    base = CFG.get('folders', {}).get(name)
    if not base:
        raise KeyError(f'config.json has no folders.{name}; add it')
    return os.path.join(base, *parts)


def rel(*parts):
    return os.path.join(ROOT, *parts)


def load_json(path, default=None):
    return json.load(open(path, encoding='utf-8-sig')) if os.path.exists(path) else default


def save_json(path, obj, indent=1):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=indent)


def timeline():
    return load_json(os.path.join(FILM, 'timeline.json'))


if sys.platform == 'win32':          # Bengali/Hindi text on a cp1252 console would crash print()
    try:
        sys.stdout.reconfigure(encoding='utf-8'); sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
