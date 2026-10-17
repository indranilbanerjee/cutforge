"""The Hermes adapter must register every skill, survive a missing or broken context, and stay stdlib-only."""
from __future__ import annotations

import ast
import importlib.util
import re
import sys
import unittest

from _helpers import REPO, skill_dirs


def load_adapter():
    spec = importlib.util.spec_from_file_location("cutforge_hermes", REPO / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Ctx:
    def __init__(self):
        self.registered = []

    def register_skill(self, name, path):
        self.registered.append((name, path))


class TestHermes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_adapter()
        cls.yaml = (REPO / "plugin.yaml").read_text(encoding="utf-8")

    def test_yaml_policy(self):
        self.assertRegex(self.yaml, r"(?m)^name: cutforge$")
        self.assertRegex(self.yaml, r"(?m)^provides_hooks: \[\]$")
        self.assertRegex(self.yaml, r"(?m)^requires_env: \[\]$")
        for name in re.findall(r"- name: (\w+)", self.yaml):
            with self.subTest(env=name):
                self.assertTrue(name.isupper())

    def test_registers_every_skill_with_its_description(self):
        ctx = Ctx()
        self.mod.register(ctx)
        names = sorted(n for n, _ in ctx.registered)
        self.assertEqual(names, sorted(d.name for d in skill_dirs()))
        for s in self.mod._walk_skills():
            with self.subTest(skill=s["name"]):
                self.assertGreater(len(s["description"]), 50, "the adapter failed to read the description")
                self.assertNotIn('\\"', s["description"])

    def test_degrades_without_a_context(self):
        self.mod.register(None)
        self.mod.register(object())

    def test_stdlib_only(self):
        tree = ast.parse((REPO / "__init__.py").read_text(encoding="utf-8"))
        mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        mods |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        stdlib = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
        self.assertTrue(mods <= stdlib, f"non-stdlib imports: {mods - stdlib}")


if __name__ == "__main__":
    unittest.main()
