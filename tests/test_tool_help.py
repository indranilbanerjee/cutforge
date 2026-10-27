"""1.1.1: `--help` on an engine tool prints its usage and runs nothing; an unknown option exits 2.

Before 1.1.1, `python tools/voice/gen_vo.py --help` RAN the tool ("generating 9 lines with placeholder" and wavs written),
`tools/mix/synth.py --help` wrote sound files, `tools/vfx/cutout.py --help` began downloading model weights, `film_mix.py --help`
re-mixed, and most of the rest crashed treating "--help" as a path. A survey of the 47 Python tools found 13 that exited 0 with
any output. Now every tool starts with `import cli; cli.guard(__name__, __file__, __doc__)`, which prints the docstring and
exits 0 before anything else runs, and exits 2 for an option the tool does not mention. The tools that use argparse already did.

The check runs every tool's --help in a fresh project with the network OFF (socket calls raise), stdin closed, and compares
the project's files before and after.
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import ENGINE, PY, REPO, TEMPLATE, has_cmd

TOOLS = TEMPLATE / "tools"
ARGPARSE_TOOLS = {"install_deps.py", "price_book.py", "resolve_model.py"}
GUARD_CALL = "cli.guard(__name__, __file__, __doc__"
OFFLINE = (
    "import socket\n"
    "def _blocked(*a, **k):\n    raise OSError('the network is off for this check')\n"
    "socket.socket.connect = _blocked\nsocket.create_connection = _blocked\nsocket.getaddrinfo = _blocked\n")


def python_tools(root: Path) -> list[Path]:
    found = sorted(p for p in (root / "tools").rglob("*.py") if "__pycache__" not in p.parts)
    return found + [root / "film" / "timeline.py"]


def first_statements_after_docstring(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    src = path.read_text(encoding="utf-8-sig").splitlines()
    body = tree.body[1:]
    return [src[n.lineno - 1] for n in body[:3]] if ast.get_docstring(tree) else []


def has_guard(path: Path) -> bool:
    return any(GUARD_CALL in line for line in first_statements_after_docstring(path))


class TestEveryToolHasTheGuard(unittest.TestCase):
    def test_discovery_every_python_tool_guards_or_uses_argparse(self):
        tools = python_tools(TEMPLATE)
        self.assertGreater(len(tools), 40, "the discovery found too few tools; the guard is vacuous")
        missing = []
        for p in tools:
            if p.name in ARGPARSE_TOOLS:
                self.assertIn("argparse", p.read_text(encoding="utf-8-sig"), p.name)
            elif p.name != "cli.py" and not has_guard(p):
                missing.append(p.relative_to(REPO).as_posix())
        self.assertEqual(missing, [], "a tool without the guard runs when someone asks for --help")

    def test_the_paid_tools_let_the_two_quote_flags_through(self):
        for rel in ("voice/gen_vo.py", "voice/audition.py", "voice/import_vo.py", "vfx/ai_gen.py"):
            with self.subTest(tool=rel):
                self.assertIn("extra=cli.SPEND_FLAGS", (TOOLS / rel).read_text(encoding="utf-8-sig"))

    def test_plant_a_new_tool_without_the_guard_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "new_tool.py"
            bad.write_text('"""A new tool."""\nimport os\nprint("ran")\n', encoding="utf-8")
            good = Path(tmp) / "ok_tool.py"
            good.write_text('"""A new tool."""\nimport cli; cli.guard(__name__, __file__, __doc__)\nprint("ran")\n', encoding="utf-8")
            self.assertFalse(has_guard(bad))
            self.assertTrue(has_guard(good))


class TestHelpRunsNothing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="cutforge-help-"))
        cls.proj = cls.tmp / "p"
        r = subprocess.run([PY, str(ENGINE / "new_project.py"), str(cls.proj), "--title", "Help", "--demo"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        site = cls.tmp / "site"
        site.mkdir()
        (site / "sitecustomize.py").write_text(OFFLINE, encoding="utf-8")
        cls.env = {**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": str(site)}
        cls.env.pop("CUTFORGE_CONFIG", None)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def snapshot(self):
        return {p.relative_to(self.proj).as_posix(): p.stat().st_mtime_ns for p in self.proj.rglob("*")
                if p.is_file() and "node_modules" not in p.parts and "__pycache__" not in p.parts}

    def run_cmd(self, *cmd, timeout=60):
        return subprocess.run(list(cmd), cwd=self.proj, capture_output=True, text=True, env=self.env, timeout=timeout,
                              stdin=subprocess.DEVNULL)

    def test_help_prints_usage_exits_0_and_changes_nothing_for_every_python_tool(self):
        problems = []
        for t in python_tools(self.proj):
            rel = t.relative_to(self.proj).as_posix()
            for flag in ("--help", "-h"):
                before = self.snapshot()
                r = self.run_cmd(PY, rel, flag)
                changed = sorted(k for k, v in self.snapshot().items() if before.get(k) != v)
                if r.returncode != 0 or not r.stdout.strip():
                    problems.append(f"{rel} {flag}: exit {r.returncode}, {len(r.stdout.strip())} chars of output")
                if changed:
                    problems.append(f"{rel} {flag}: wrote {changed[:3]}")
        self.assertEqual(problems, [])

    def test_an_unknown_option_exits_2_for_every_python_tool(self):
        problems = []
        for t in python_tools(self.proj):
            rel = t.relative_to(self.proj).as_posix()
            r = self.run_cmd(PY, rel, "--no-such-option-xyz")
            if r.returncode != 2:
                problems.append(f"{rel}: exit {r.returncode}")
        self.assertEqual(problems, [])

    def test_the_paid_tools_accept_go_and_quoted_providers(self):
        for rel in ("tools/voice/gen_vo.py", "tools/vfx/ai_gen.py", "tools/voice/audition.py", "tools/voice/import_vo.py"):
            with self.subTest(tool=rel):
                r = self.run_cmd(PY, rel, "--go", "--quoted-providers", "x")
                self.assertNotEqual(r.returncode, 2, r.stderr)
                self.assertNotIn("unknown option", r.stderr)

    @unittest.skipUnless(has_cmd("bash"), "bash is not installed")
    def test_shell_tools_print_usage_and_reject_unknown_options(self):
        bash = shutil.which("bash")
        for rel in ("tools/render/assemble.sh", "tools/render/pipeline.sh", "tools/text/shapeall.sh"):
            with self.subTest(tool=rel):
                before = self.snapshot()
                ok = self.run_cmd(bash, rel, "--help")
                self.assertEqual(ok.returncode, 0, ok.stderr)
                self.assertTrue(ok.stdout.strip())
                bad = self.run_cmd(bash, rel, "--no-such-option-xyz")
                self.assertEqual(bad.returncode, 2, bad.stderr)
                self.assertEqual(self.snapshot(), before)

    @unittest.skipUnless(has_cmd("node"), "node is not installed")
    def test_node_tools_print_usage_without_node_modules_and_reject_unknown_options(self):
        for rel in ("render.mjs", "tools/text/shape.mjs"):
            with self.subTest(tool=rel):
                ok = self.run_cmd("node", rel, "--help")
                self.assertEqual(ok.returncode, 0, ok.stderr)
                self.assertTrue(ok.stdout.strip())
                bad = self.run_cmd("node", rel, "--no-such-option-xyz")
                self.assertEqual(bad.returncode, 2, bad.stderr)
        no_args = self.run_cmd("node", "render.mjs")
        self.assertEqual(no_args.returncode, 2, "missing arguments are a bad argument")

    def test_new_project_help_and_its_refusals(self):
        ok = subprocess.run([PY, str(ENGINE / "new_project.py"), "--help"], capture_output=True, text=True, env=self.env, stdin=subprocess.DEVNULL)
        self.assertEqual(ok.returncode, 0)
        self.assertIn("usage", ok.stdout.lower())
        inside = subprocess.run([PY, str(ENGINE / "new_project.py"), str(ENGINE.parent / "nope-inside")], capture_output=True, text=True,
                                env=self.env, stdin=subprocess.DEVNULL)
        self.assertEqual(inside.returncode, 2, inside.stderr)
        self.assertFalse((ENGINE.parent / "nope-inside").exists())
        full = subprocess.run([PY, str(ENGINE / "new_project.py"), str(self.proj)], capture_output=True, text=True, env=self.env,
                              stdin=subprocess.DEVNULL)
        self.assertEqual(full.returncode, 2, full.stderr)
        bad = subprocess.run([PY, str(ENGINE / "new_project.py"), "--no-such-option-xyz"], capture_output=True, text=True, env=self.env,
                             stdin=subprocess.DEVNULL)
        self.assertEqual(bad.returncode, 2)

    def test_plant_the_1_1_0_behaviour_help_ran_the_tool(self):
        """A tool without the guard, run with --help in the same project: it does its work and exits 0 with no usage."""
        tool = self.proj / "tools" / "planted_unguarded.py"
        tool.write_text('"""Does work."""\nimport sys\nopen("planted-side-effect.txt", "w").write(" ".join(sys.argv))\n', encoding="utf-8")
        self.addCleanup(lambda: (tool.unlink(missing_ok=True), (self.proj / "planted-side-effect.txt").unlink(missing_ok=True)))
        r = self.run_cmd(PY, "tools/planted_unguarded.py", "--help")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")
        self.assertTrue((self.proj / "planted-side-effect.txt").exists(), "an unguarded tool runs on --help")
        self.assertFalse(has_guard(tool))


if __name__ == "__main__":
    unittest.main()
