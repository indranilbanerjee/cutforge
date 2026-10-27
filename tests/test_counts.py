"""The counts the README, AGENTS.md and the manifests advertise must be the counts the repository ships."""
from __future__ import annotations

import re
import unittest

from _helpers import AGENTS, REPO, engine_tools, load_json, skill_dirs

STATED_IN = ["README.md", "AGENTS.md", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "plugin.yaml",
             "package.json", "openclaw.plugin.json", "plugin.json", "CHANGELOG.md"]


class TestCounts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truth = {"skills": len(skill_dirs()), "reviewer agents": len(list(AGENTS.glob("*.md"))),
                     "tools": len(engine_tools())}

    def test_truth_is_what_we_think(self):
        self.assertEqual(self.truth, {"skills": 13, "reviewer agents": 4, "tools": 52})

    def test_every_stated_count(self):
        for rel in STATED_IN:
            text = (REPO / rel).read_text(encoding="utf-8")
            text = text.split("## [", 2)[1] if rel == "CHANGELOG.md" else text   # only the newest entry
            for noun, n in self.truth.items():
                for m in re.finditer(rf"(\d+) {noun}\b", text):
                    with self.subTest(file=rel, claim=m.group(0)):
                        self.assertEqual(int(m.group(1)), n)

    def test_the_test_badge_matches_the_number_of_tests(self):
        methods = sum(len(re.findall(r"(?m)^\s*def test_", p.read_text(encoding="utf-8"))) for p in (REPO / "tests").glob("test_*.py"))
        badge = re.search(r"tests-(\d+)%2F(\d+)%20passing", (REPO / "README.md").read_text(encoding="utf-8"))
        self.assertIsNotNone(badge, "the README test badge is missing")
        self.assertEqual((int(badge.group(1)), int(badge.group(2))), (methods, methods), "bump the README test badge")

    def test_readme_skill_table_lists_every_skill(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        for d in skill_dirs():
            with self.subTest(skill=d.name):
                self.assertIn(f"| `{d.name}` |", readme)

    def test_hermes_description_count(self):
        desc = (REPO / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn(f"{self.truth['skills']} skills", desc.replace("\n  ", " "))


if __name__ == "__main__":
    unittest.main()
