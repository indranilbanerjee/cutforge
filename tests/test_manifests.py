"""Every manifest, the Hermes files, the README, AGENTS.md and the CHANGELOG must agree.

Nine surfaces read nine different files. A release that bumps eight of them ships a plugin whose version or
description differs by host, and nothing at install time says so.
"""
from __future__ import annotations

import json
import re
import unittest

from _helpers import REPO, load_json

JSON_MANIFESTS = [".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json",
                  ".github/plugin/plugin.json", ".grok-plugin/plugin.json", "gemini-extension.json",
                  "openclaw.plugin.json", "plugin.json", "package.json"]
SAME_DESCRIPTION = [".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json",
                    ".github/plugin/plugin.json", ".grok-plugin/plugin.json", "gemini-extension.json"]


def yaml_field(text: str, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else None


class TestVersionsAgree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = load_json(REPO / ".claude-plugin/plugin.json")["version"]

    def test_semver(self):
        self.assertRegex(self.canonical, r"^\d+\.\d+\.\d+$")

    def test_every_json_manifest(self):
        for rel in JSON_MANIFESTS:
            with self.subTest(manifest=rel):
                self.assertEqual(load_json(REPO / rel)["version"], self.canonical)

    def test_grok_marketplace_entry(self):
        doc = load_json(REPO / ".grok-plugin/marketplace.json")
        self.assertEqual(doc["plugins"][0]["version"], self.canonical)

    def test_hermes_yaml_and_adapter(self):
        self.assertEqual(yaml_field((REPO / "plugin.yaml").read_text(encoding="utf-8"), "version"), self.canonical)
        m = re.search(r'^PLUGIN_VERSION = "([^"]+)"', (REPO / "__init__.py").read_text(encoding="utf-8"), re.M)
        self.assertEqual(m.group(1), self.canonical)

    def test_readme_badge_lede_and_surfaces(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"badge/version-{self.canonical}-", readme)
        lede = re.search(r"^> 🆕.*$", readme, re.M)
        self.assertIsNotNone(lede, "README lost its '> 🆕' lede")
        self.assertIn(f"v{self.canonical}", lede.group(0))
        self.assertIn(f"## Supported surfaces (v{self.canonical})", readme)
        self.assertIn(f"## Current Release (v{self.canonical})", readme)

    def test_agents_md(self):
        self.assertIn(f"(v{self.canonical})", (REPO / "AGENTS.md").read_text(encoding="utf-8"))

    def test_changelog_top_entry(self):
        heads = re.findall(r"^## \[([^\]]+)\]", (REPO / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
        self.assertTrue(heads, "CHANGELOG has no release headings")
        self.assertEqual(heads[0], self.canonical, "the newest CHANGELOG entry must be the manifest version")


class TestIdentityAgrees(unittest.TestCase):
    def test_names(self):
        for rel in JSON_MANIFESTS:
            doc = load_json(REPO / rel)
            name = doc.get("id") or doc.get("name")
            with self.subTest(manifest=rel):
                self.assertIn(name, ("cutforge", "@indranilbanerjee/cutforge"))
        self.assertEqual(load_json(REPO / "openclaw.plugin.json")["id"], "cutforge")
        self.assertEqual(yaml_field((REPO / "plugin.yaml").read_text(encoding="utf-8"), "name"), "cutforge")

    def test_short_description_identical_where_hosts_show_it(self):
        descs = {rel: load_json(REPO / rel)["description"] for rel in SAME_DESCRIPTION}
        self.assertEqual(len(set(descs.values())), 1, f"descriptions differ between hosts: {descs}")
        grok = load_json(REPO / ".grok-plugin/marketplace.json")["plugins"][0]["description"]
        self.assertEqual(grok, descs[".claude-plugin/plugin.json"])

    def test_license_mit_everywhere(self):
        for rel in JSON_MANIFESTS:
            doc = load_json(REPO / rel)
            if "license" in doc:
                with self.subTest(manifest=rel):
                    self.assertEqual(doc["license"], "MIT")
        self.assertTrue((REPO / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"))

    def test_claude_manifest_hard_rules(self):
        doc = load_json(REPO / ".claude-plugin/plugin.json")
        self.assertNotIn("$schema", doc)
        self.assertIsInstance(doc["repository"], str)
        self.assertTrue((REPO / doc["icon"].lstrip("./")).is_file(), "the icon the manifest points at is missing")

    def test_manifest_paths_exist(self):
        for rel, key in ((".codex-plugin/plugin.json", "skills"), (".cursor-plugin/plugin.json", "skills"),
                         (".cursor-plugin/plugin.json", "agents"), (".grok-plugin/plugin.json", "skills")):
            with self.subTest(manifest=rel, key=key):
                self.assertTrue((REPO / load_json(REPO / rel)[key]).is_dir())
        self.assertTrue((REPO / ".github/plugin" / load_json(REPO / ".github/plugin/plugin.json")["skills"]).resolve().is_dir())
        self.assertTrue((REPO / load_json(REPO / "gemini-extension.json")["contextFileName"]).is_file())

    def test_codex_interface_is_complete(self):
        iface = load_json(REPO / ".codex-plugin/plugin.json")["interface"]
        for key in ("displayName", "shortDescription", "longDescription", "developerName", "category", "defaultPrompt"):
            with self.subTest(key=key):
                self.assertTrue(iface.get(key))
        self.assertLessEqual(len(iface["defaultPrompt"]), 4)


if __name__ == "__main__":
    unittest.main()
