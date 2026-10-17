"""Every file, tool and path the docs promise must exist.

The worst skill bug is a confident instruction to run a tool that is not there. The skills name project tools
(tools/..., film/...) that live in engine/template, plugin paths under ${CLAUDE_PLUGIN_ROOT}, and reference files.
"""
from __future__ import annotations

import re
import unittest

from _helpers import REPO, SKILLS, TEMPLATE, skill_dirs

# Files the pipeline GENERATES inside a project (they cannot exist in the template).
GENERATED = {"film/plates.json", "film/audition.json", "film/face_labels.json", "film/people_in_media.json",
             "film/vo_durs.json", "film/vo_check.json", "film/timeline.json", "src/timeline.json", "src/glyphs.json"}


def markdown_files():
    return [p for p in REPO.rglob("*.md") if ".git" not in p.parts and "evals" not in p.parts]


class TestReferences(unittest.TestCase):
    def test_skill_reference_files_exist(self):
        for d in skill_dirs():
            body = (d / "SKILL.md").read_text(encoding="utf-8")
            for ref in re.findall(r"`(references/[\w.-]+)`", body):
                with self.subTest(skill=d.name, ref=ref):
                    self.assertTrue((d / ref).is_file())

    def test_every_reference_file_is_used(self):
        for d in skill_dirs():
            refs = d / "references"
            if not refs.is_dir():
                continue
            body = (d / "SKILL.md").read_text(encoding="utf-8")
            for f in refs.iterdir():
                with self.subTest(skill=d.name, file=f.name):
                    self.assertIn(f"references/{f.name}", body, "an orphan reference file nobody reads")

    def test_project_tool_paths_exist(self):
        for md in markdown_files():
            text = md.read_text(encoding="utf-8")
            for path in set(re.findall(r"((?:tools|film|src)/[\w/.-]+\.(?:py|sh|mjs|tsx|ts|json))", text)):
                if path in GENERATED:
                    continue
                with self.subTest(doc=str(md.relative_to(REPO)), path=path):
                    self.assertTrue((TEMPLATE / path).is_file(), f"{path} is named but not in engine/template")

    def test_plugin_root_paths_exist(self):
        for md in markdown_files():
            text = md.read_text(encoding="utf-8")
            for path in set(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w/.-]+[\w])", text)):
                with self.subTest(doc=str(md.relative_to(REPO)), path=path):
                    self.assertTrue((REPO / path).exists(), f"${{CLAUDE_PLUGIN_ROOT}}/{path} does not exist")

    def test_skills_named_in_docs_exist(self):
        names = {d.name for d in skill_dirs()} | {a.stem for a in (REPO / "agents").glob("*.md")}
        for md in [*(SKILLS.rglob("*.md")), REPO / "README.md", REPO / "AGENTS.md"]:
            text = md.read_text(encoding="utf-8")
            for name in set(re.findall(r"`((?:video|story|sound|media|voice|visuals|render|revision|marketing|film|compliance|archive)-[a-z-]+)`", text)):
                with self.subTest(doc=md.name, name=name):
                    self.assertIn(name, names)

    def test_readme_links_resolve(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        for link in set(re.findall(r"\]\(((?!https?:|#)[^)\s]+)\)", readme)):
            with self.subTest(link=link):
                self.assertTrue((REPO / link).exists(), f"README links to missing {link}")


if __name__ == "__main__":
    unittest.main()
