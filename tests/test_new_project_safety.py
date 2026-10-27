"""1.1.0: new_project.py never loops into the plugin and never hands a project a shell script bash cannot run.

* A target inside the plugin folder (the template copied into a folder inside itself) never ends; it is refused up front.
* A Windows clone with core.autocrlf=true writes the .sh files with CRLF line ends, and bash rejects them. The project gets LF
  whatever the checkout did. Planted by copying the engine with CRLF scripts and scaffolding from the copy.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import ENGINE, PY


class TestNewProjectSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cutforge-np-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def scaffold(self, script: Path, target: Path):
        return subprocess.run([PY, str(script), str(target), "--title", "Safe", "--demo"], capture_output=True, text=True, timeout=120)

    def test_a_target_inside_the_plugin_folder_is_refused(self):
        inside = ENGINE.parent / "should-not-exist"
        r = self.scaffold(ENGINE / "new_project.py", inside)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("inside the CutForge plugin folder", r.stderr + r.stdout)
        self.assertFalse(inside.exists(), "the refusal must come before anything is copied")
        template_inside = ENGINE / "template" / "nested"
        r = self.scaffold(ENGINE / "new_project.py", template_inside)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(template_inside.exists())

    def test_a_target_beside_the_plugin_is_fine(self):
        r = self.scaffold(ENGINE / "new_project.py", self.tmp / "ok")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_shell_scripts_in_a_project_have_lf_line_ends_even_from_a_crlf_checkout(self):
        engine = self.tmp / "plugin" / "engine"          # new_project.py treats the folder above engine/ as the plugin
        shutil.copytree(ENGINE, engine, ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
        crlf = 0
        for sh in engine.rglob("*.sh"):
            sh.write_bytes(sh.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            crlf += 1
        self.assertGreaterEqual(crlf, 3, "the plant found too few shell scripts")
        self.assertTrue(all(b"\r\n" in s.read_bytes() for s in engine.rglob("*.sh")))
        target = self.tmp / "proj"
        r = self.scaffold(engine / "new_project.py", target)
        self.assertEqual(r.returncode, 0, r.stderr)
        scripts = list(target.rglob("*.sh"))
        self.assertGreaterEqual(len(scripts), 3)
        for sh in scripts:
            with self.subTest(script=sh.name):
                self.assertNotIn(b"\r", sh.read_bytes())

    def test_plant_what_the_1_0_1_copy_would_have_done(self):
        """The old copy step: copytree alone keeps the CR. This is the failure the LF pass removes."""
        src = self.tmp / "a.sh"
        src.write_bytes(b"#!/bin/sh\r\necho hi\r\n")
        dst = self.tmp / "b.sh"
        shutil.copy2(src, dst)
        self.assertIn(b"\r", dst.read_bytes())


if __name__ == "__main__":
    unittest.main()
