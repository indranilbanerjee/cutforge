"""Small checks every setup path shares: Node, ffmpeg, Remotion, the Python floor, and how to print a command.

Stdlib only. Used by setup_local.py and install_deps.py; nothing here installs or downloads anything.
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import cli; cli.guard(__name__, __file__, __doc__)
import json, os, re, shutil, subprocess, sys

NODE_MIN = 22            # Node 18 and 20 are end of life
FFMPEG_WARN_BELOW = 6    # the tools were run on ffmpeg 8.1; older builds may lack a filter, so warn rather than fail
PYTHON_PREFERRED = (3, 11)


def python_notice(version=None):
    """A warning for Python 3.10 (end of life 2026-10-01), else None. It still runs; the notice never blocks."""
    v = tuple(version or sys.version_info[:2])
    if v < PYTHON_PREFERRED:
        return ('Python 3.10 reached end of life on 2026-10-01. CutForge still runs on it, and will move to 3.11 once Claude\'s '
                'Cowork environment does (it ran 3.10.12 when last checked). Use 3.11 or newer where you can.')
    return None


def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def node_version():
    """(major, 'v24.11.1') or None when node is missing."""
    if not shutil.which('node'):
        return None
    text = _run(['node', '--version']).strip()
    m = re.match(r'v?(\d+)', text)
    return (int(m.group(1)), text) if m else None


def ffmpeg_major(tool='ffmpeg'):
    """(major, first line) of `ffmpeg -version`, or None. Release builds say 'ffmpeg version 8.1.1'; git builds say 'N-12345-g...'."""
    if not shutil.which(tool):
        return None
    line = _run([tool, '-version']).splitlines()[:1]
    line = line[0] if line else ''
    m = re.search(r'version\s+n?(\d+)\.', line)
    return (int(m.group(1)) if m else None, line)


def remotion_pin_and_installed(root):
    """(pinned, installed) Remotion versions: from package.json and from node_modules; None for whichever is missing."""
    def version(path, key=None):
        try:
            data = json.load(open(path, encoding='utf-8-sig'))
        except (OSError, ValueError):
            return None
        return (data.get('dependencies', {}) if key else data).get(key or 'version')
    return (version(os.path.join(root, 'package.json'), 'remotion'),
            version(os.path.join(root, 'node_modules', 'remotion', 'package.json')))


def printed_command(*args):
    """A command line safe to paste into Git Bash and PowerShell: forward slashes, script paths double-quoted, the interpreter
    quoted only when its path has a space (a quoted first token is a string in PowerShell), and then a note to put & before it."""
    exe = sys.executable.replace('\\', '/')
    spaced = ' ' in exe
    words = [f'"{exe}"' if spaced else exe]
    for a in args:
        a = str(a).replace('\\', '/')
        words.append(f'"{a}"' if (' ' in a or a.endswith('.py')) else a)
    return ' '.join(words) + ('  # in PowerShell, put & before it' if spaced else '')
