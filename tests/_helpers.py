"""Shared helpers: repository paths, frontmatter parsing, and ONE scaffolded demo project per test run."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
AGENTS = REPO / "agents"
ENGINE = REPO / "engine"
TEMPLATE = ENGINE / "template"
PY = sys.executable

_project: Path | None = None
_tmp: str | None = None


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    fields = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if mm:
            v = mm.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] == '"':
                v = v[1:-1].replace('\\"', '"')
            fields[mm.group(1)] = v
    return fields, m.group(2)


def skill_dirs() -> list[Path]:
    return sorted(d for d in SKILLS.iterdir() if (d / "SKILL.md").is_file())


def engine_tools() -> list[Path]:
    """Every runnable engine tool: the scaffold, the timeline, the renderer and the project tools."""
    tools = [p for p in (TEMPLATE / "tools").rglob("*") if p.suffix in (".py", ".sh", ".mjs") and "__pycache__" not in p.parts]
    return sorted(tools + [ENGINE / "new_project.py", TEMPLATE / "film" / "timeline.py", TEMPLATE / "render.mjs"])


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def has_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def demo_project() -> Path:
    """Scaffold the demo once per run (new_project.py --demo) and return its folder."""
    global _project, _tmp
    if _project is None:
        _tmp = tempfile.mkdtemp(prefix="cutforge-test-")
        target = Path(_tmp) / "demo"
        r = subprocess.run([PY, str(ENGINE / "new_project.py"), str(target), "--title", "Test Film", "--demo"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("new_project.py failed: " + r.stderr[-800:])
        _project = target
    return _project


def run_tool(project: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run([PY, *args], cwd=project, capture_output=True, text=True,
                          env={**__import__("os").environ, "PYTHONUTF8": "1"}, check=check)


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def cleanup() -> None:
    if _tmp:
        shutil.rmtree(_tmp, ignore_errors=True)
