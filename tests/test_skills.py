"""Skill frontmatter must fit Claude Code's shared skill listing and still route.

The listing budget is characters (about 1% of the context window), shared by every installed plugin; past it,
descriptions are dropped first. The sibling plugins measured the rule with trigger evals: 60-150 characters, median
at most 120, the decisive words first, one or two quoted user phrases, each phrase owned by one skill.
"""
from __future__ import annotations

import re
import statistics
import unittest

from _helpers import AGENTS, frontmatter, skill_dirs


class TestSkillFrontmatter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = {d.name: frontmatter(d / "SKILL.md") for d in skill_dirs()}

    def test_name_matches_folder(self):
        for folder, (fm, _) in self.skills.items():
            with self.subTest(skill=folder):
                self.assertEqual(fm.get("name"), folder)

    def test_description_length(self):
        lengths = []
        for folder, (fm, _) in self.skills.items():
            d = fm.get("description", "")
            lengths.append(len(d))
            with self.subTest(skill=folder):
                self.assertGreaterEqual(len(d), 60, d)
                self.assertLessEqual(len(d), 150, d)
        self.assertLessEqual(statistics.median(lengths), 120)

    def test_quoted_phrases(self):
        owners = {}
        for folder, (fm, _) in self.skills.items():
            phrases = re.findall(r'"([^"]+)"', fm.get("description", ""))
            with self.subTest(skill=folder):
                self.assertIn(len(phrases), (1, 2), "one or two quoted user phrases")
                self.assertNotIn("/cutforge", fm.get("description", ""), "no slash alias in a description")
            for p in phrases:
                self.assertNotIn(p.lower(), owners, f"'{p}' is quoted by both {owners.get(p.lower())} and {folder}")
                owners[p.lower()] = folder

    def test_name_token_early(self):
        for folder, (fm, _) in self.skills.items():
            head = fm.get("description", "")[:100].lower()
            tokens = [t for t in re.split(r"[-]", folder) if len(t) > 2] + [folder]
            with self.subTest(skill=folder):
                self.assertTrue(any(t[:5] in head for t in tokens), f"no token of '{folder}' in: {head}")

    def test_user_invocable_and_no_when_to_use(self):
        for folder, (fm, _) in self.skills.items():
            with self.subTest(skill=folder):
                self.assertEqual(fm.get("user-invocable"), "true")
                self.assertNotIn("when_to_use", fm)

    def test_body_size(self):
        for folder, (_, body) in self.skills.items():
            with self.subTest(skill=folder):
                self.assertLess(len(body.split()), 3000, "move detail into references/")
                self.assertGreater(len(body.split()), 300, "a skill body this short cannot carry the method")


class TestAgents(unittest.TestCase):
    def test_agent_frontmatter(self):
        agents = sorted(AGENTS.glob("*.md"))
        self.assertEqual(len(agents), 4)
        for a in agents:
            text = a.read_text(encoding="utf-8").replace("\r\n", "\n")
            head, body = text.split("\n---\n", 1)
            with self.subTest(agent=a.name):
                self.assertIn(f"name: {a.stem}", head)
                for key in ("description:", "model:", "color:", "tools:"):
                    self.assertIn(key, head)
                # The host lists every agent's description in every session, so it is one short sentence; the long form
                # and its examples live in the body, where they cost nothing until the agent runs.
                self.assertNotIn("<example>", head, "examples in the description cost ~400 tokens per agent in every session")
                description = re.search(r'^description: "(.*)"$', head, re.M)
                self.assertIsNotNone(description, "description must be one quoted line")
                self.assertTrue(100 <= len(description.group(1)) <= 146, len(description.group(1)))
                self.assertIn("## When to delegate", body)
                for key in ("<example>", "<commentary>"):
                    self.assertIn(key, body)


if __name__ == "__main__":
    unittest.main()
