"""1.1.0: the guards the other three plugins in the suite already carry, each planted so a rule that cannot fail is not trusted.

  * no model id in code or skills (they come from tools/model_registry.json), no rate typed into code;
  * every file that runs a plugin script says where the scripts are and quotes the path; nothing uses /tmp;
  * a file a person or an agent writes is read with a byte-order-mark-safe encoding (PowerShell 5.1 and Notepad write one);
  * the descriptions the host lists in every session stay short;
  * the template that ships holds no runtime file (price book, spend log, config, approval file);
  * every host a tool talks to is one PRIVACY.md lists.
Stdlib only; a folder added tomorrow is covered by default.
"""
from __future__ import annotations

import re
import statistics
import unittest
from pathlib import Path

from _helpers import AGENTS, REPO, SKILLS, TEMPLATE, frontmatter

TOOLS = TEMPLATE / "tools"
SKIP_DIRS = {".git", "node_modules", "__pycache__", "tests", "evals", ".github"}


def walk(suffixes, extra_skip=()):
    for p in sorted(REPO.rglob("*")):
        rel = p.relative_to(REPO)
        if p.is_file() and p.suffix.lower() in suffixes and not (set(rel.parts) & (SKIP_DIRS | set(extra_skip))):
            yield p


# ----------------------------------------------------------------------------- model ids
MODEL_ID = re.compile(
    r"\b(gpt-[0-9][\w.-]*|eleven_[a-z0-9_]+|bulbul:v\d[\w-]*|saarika:v[\d.]+|saaras:v\d|whisper-1|scribe_v\d\w*|"
    r"claude-(?:opus|sonnet|haiku|fable|mythos)-[\w.-]+|gemini-[0-9][\w.-]*|veo-[0-9][\w.-]*|kling-v?\d[\w.-]*)")
# History and vendor-facing records may name models; code and instructions may not.
MODEL_ID_EXEMPT = {"CHANGELOG.md", "docs/lessons-learned.md", "docs/case-study.md", "docs/compliance-and-licensing.md",
                   "engine/template/tools/model_registry.json"}
RATE = re.compile(r"(inr_per_\w+|COST_PER_\w+|est_inr|rate_per_\w+)")


def model_id_problems(rel, text):
    return [f"{rel}:{n}: {m.group(0)}" for n, line in enumerate(text.splitlines(), 1) for m in MODEL_ID.finditer(line)]


class TestVendorNeutrality(unittest.TestCase):
    def test_no_code_or_instruction_file_names_a_model_id(self):
        scanned, bad = 0, []
        for p in walk({".py", ".mjs", ".md", ".json", ".yaml", ".ts", ".tsx", ".sh"}):
            rel = p.relative_to(REPO).as_posix()
            if rel in MODEL_ID_EXEMPT or rel.endswith("package-lock.json"):
                continue
            scanned += 1
            bad += model_id_problems(rel, p.read_text(encoding="utf-8-sig", errors="replace"))
        self.assertGreater(scanned, 100, "the scan saw too few files; the guard is vacuous")
        self.assertEqual(bad, [])

    def test_no_tool_carries_a_rate(self):
        hits = [f"{p.relative_to(REPO).as_posix()}: {m.group(0)}" for p in TOOLS.rglob("*.py")
                for m in RATE.finditer(p.read_text(encoding="utf-8-sig"))]
        self.assertEqual(hits, [])

    def test_plant_the_1_0_defaults_are_flagged(self):
        for old in ("'model': v.get('model', 'bulbul:v3'),", "model or 'saarika:v2.5'", "model or 'whisper-1'",
                    "v.get('model', 'gpt-4o-mini-tts')", "v.get('model', 'eleven_multilingual_v2')"):
            with self.subTest(old=old):
                self.assertTrue(model_id_problems("engine/template/tools/voice/x.py", old))
        self.assertFalse(model_id_problems("x.py", "model_for('latest-tts-sarvam', v.get('model'), 'https://api.sarvam.ai/')"))


# ----------------------------------------------------------------------------- script invocations
SENTENCE = ("If your host does not set `${CLAUDE_PLUGIN_ROOT}`, the plugin folder is the one that contains `skills/`")
RUNS_PLUGIN_SCRIPT = re.compile(r"(?<![\w/.-])(?:python3?|bash|node)\s+(?:-\w+\s+)*[\"']?\$\{CLAUDE_PLUGIN_ROOT\}")
UNQUOTED = re.compile(r"(?<![\w/.-])(?:python3?|bash|node)\s+(?:-\w+\s+)*\$\{CLAUDE_PLUGIN_ROOT\}/")
PYTHON3 = re.compile(r"(?<![\w/.-])python3(?=\s+[\w\"'$./-])")


def invocation_problems(files: dict) -> list:
    out = []
    for rel, text in files.items():
        lines = text.splitlines()
        if any(RUNS_PLUGIN_SCRIPT.search(l) for l in lines) and SENTENCE not in text:
            out.append(f"{rel}: runs a plugin script but has no script-location line")
        for n, l in enumerate(lines, 1):
            if UNQUOTED.search(l):
                out.append(f"{rel}:{n}: the ${{CLAUDE_PLUGIN_ROOT}} script path is not quoted")
            if PYTHON3.search(l):
                out.append(f"{rel}:{n}: runs python3 (it often does not resolve on Windows; the script-location line says when to fall back to it)")
    return out


class TestScriptInvocations(unittest.TestCase):
    @staticmethod
    def instruction_files() -> dict:
        files = {}
        for p in list(SKILLS.rglob("*.md")) + list(AGENTS.glob("*.md")) + [REPO / "AGENTS.md", REPO / "README.md"] + list((REPO / "docs").glob("*.md")):
            files[p.relative_to(REPO).as_posix()] = p.read_text(encoding="utf-8-sig", errors="replace")
        return files

    def test_every_file_that_runs_a_plugin_script_invokes_it_robustly(self):
        files = self.instruction_files()
        running = [r for r, t in files.items() if any(RUNS_PLUGIN_SCRIPT.search(l) for l in t.splitlines())]
        self.assertGreaterEqual(len(running), 1, "the discovery found no file that runs a plugin script; the guard is vacuous")
        self.assertGreater(len(files), 30)
        self.assertEqual(invocation_problems(files), [])

    def test_nothing_uses_a_tmp_path(self):
        bad = []
        for p in walk({".md", ".py", ".mjs", ".sh", ".json", ".yaml"}):
            rel = p.relative_to(REPO).as_posix()
            if rel == "CHANGELOG.md":
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
                if re.search(r"(?<![\w.])/tmp/", line):
                    bad.append(f"{rel}:{n}")
        self.assertEqual(bad, [], "PowerShell resolves /tmp to C:\\tmp; Git Bash rewrites it to the temp folder; tests in Git Bash alone miss it")

    def test_plants(self):
        base = "> **Script location.** " + SENTENCE + "\n\n"
        self.assertEqual(invocation_problems({"a.md": base + 'python "${CLAUDE_PLUGIN_ROOT}/engine/new_project.py" x'}), [])
        self.assertTrue(invocation_problems({"a.md": 'python "${CLAUDE_PLUGIN_ROOT}/engine/new_project.py" x'}))          # no location line
        self.assertTrue(invocation_problems({"a.md": base + "python ${CLAUDE_PLUGIN_ROOT}/engine/new_project.py x"}))       # unquoted
        self.assertTrue(invocation_problems({"a.md": base + 'python3 "${CLAUDE_PLUGIN_ROOT}/engine/new_project.py" x'}))   # python3


# ----------------------------------------------------------------------------- byte-order marks
READ_OPEN = re.compile(r"open\(([^\n]*?)encoding\s*=\s*['\"]utf-8['\"]([^\n]*?)\)")
WRITE_MODE = re.compile(r"['\"][wa]b?\+?['\"]")


def bom_problems(rel, text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in READ_OPEN.finditer(line):
            if not WRITE_MODE.search(m.group(1) + m.group(2)):
                out.append(f"{rel}:{n}: reads with utf-8, which keeps a byte-order mark as part of the first key")
    return out


class TestByteOrderMarks(unittest.TestCase):
    def test_every_read_of_a_file_a_person_may_have_written_is_bom_safe(self):
        scanned, bad = 0, []
        for p in walk({".py"}, extra_skip=("tests",)):
            if "engine" not in p.relative_to(REPO).parts:
                continue
            scanned += 1
            bad += bom_problems(p.relative_to(REPO).as_posix(), p.read_text(encoding="utf-8-sig"))
        self.assertGreater(scanned, 40)
        self.assertEqual(bad, [])

    def test_render_mjs_strips_a_bom(self):
        text = (TEMPLATE / "render.mjs").read_text(encoding="utf-8")
        self.assertIn("replace(/^\\uFEFF/, '')", text)
        self.assertNotIn("JSON.parse(fs.readFileSync(", text.replace("const readJson = (p) => JSON.parse(fs.readFileSync(p, 'utf8')", ""))

    def test_plants(self):
        self.assertTrue(bom_problems("x.py", "cfg = json.load(open(path, encoding='utf-8'))"))
        self.assertTrue(bom_problems("x.py", "for line in open(f, encoding=\"utf-8\", errors='ignore'):"))
        self.assertFalse(bom_problems("x.py", "cfg = json.load(open(path, encoding='utf-8-sig'))"))
        self.assertFalse(bom_problems("x.py", "open(path, 'w', encoding='utf-8').write(text)"))
        self.assertFalse(bom_problems("x.py", "open(path, encoding='utf-8', mode='w')"))

    def test_a_config_and_a_key_file_with_a_bom_still_load(self):
        import json, os, subprocess, sys, tempfile
        from _helpers import ENGINE, PY
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            r = subprocess.run([PY, str(ENGINE / "new_project.py"), str(proj), "--title", "Bom", "--demo"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            keys = Path(tmp) / "keys.txt"
            keys.write_bytes(b"\xef\xbb\xbfSARVAM_API_KEY=abc123\r\n")
            cfg = json.loads((proj / "config.json").read_text(encoding="utf-8"))
            cfg["api_keys_file"] = str(keys)
            (proj / "config.json").write_bytes(b"\xef\xbb\xbf" + json.dumps(cfg).encode("utf-8"))
            r = subprocess.run([PY, "tools/keys.py", "SARVAM_API_KEY"], cwd=proj, capture_output=True, text=True,
                               env={**os.environ, "PYTHONUTF8": "1", "SARVAM_API_KEY": ""})
            self.assertIn("SARVAM_API_KEY: found (6 chars)", r.stdout + r.stderr)
            r = subprocess.run([PY, "tools/spend.py"], cwd=proj, capture_output=True, text=True, env={**os.environ, "PYTHONUTF8": "1"})
            self.assertEqual(r.returncode, 0, r.stderr)


# ----------------------------------------------------------------------------- what the host lists in every session
class TestListingBudget(unittest.TestCase):
    def descriptions(self):
        out = {}
        for d in sorted(SKILLS.iterdir()):
            if (d / "SKILL.md").exists():
                out[f"skills/{d.name}"] = frontmatter(d / "SKILL.md")[0].get("description", "")
        for a in sorted(AGENTS.glob("*.md")):
            out[f"agents/{a.stem}"] = frontmatter(a)[0].get("description", "")
        return out

    def test_every_description_is_short_and_the_median_is_shorter(self):
        d = self.descriptions()
        self.assertEqual(len(d), 17)
        lengths = {k: len(v) for k, v in d.items()}
        for k, n in lengths.items():
            with self.subTest(component=k):
                self.assertTrue(60 <= n <= 150, n)
        self.assertLessEqual(statistics.median(lengths.values()), 115)

    def test_the_total_stays_under_the_budget(self):
        total = sum(len(v) for v in self.descriptions().values())
        self.assertLessEqual(total, 2200, "descriptions are listed in every session; trim before raising this")

    def test_plant_an_agent_with_embedded_examples_is_caught(self):
        long = "Use this agent to survey a large photo/video library. <example>Context: a new project. user: find the best moments.</example>" * 3
        self.assertFalse(60 <= len(long) <= 150)


# ----------------------------------------------------------------------------- shipped template and privacy table
RUNTIME_FILES = ("price_book.json", "spend.md", "GO_AHEAD.txt", "config.json", "ai_log.jsonl")
HOST = re.compile(r"https://([a-z0-9.-]+\.[a-z]{2,})")
BARE_HOST = re.compile(r"\b((?:[a-z0-9-]+\.)+(?:ai|io|com|org|net|co))\b")


def hosts_in(text):
    return {m.group(1).lower() for m in HOST.finditer(text)}


def privacy_hosts(text):
    """PRIVACY.md writes the endpoints as bare host names in backticks (api.example.com)."""
    return {m.group(1).lower() for m in BARE_HOST.finditer(text)}


class TestShippedTemplateAndPrivacy(unittest.TestCase):
    def test_the_template_ships_no_runtime_file(self):
        found = [p.relative_to(REPO).as_posix() for p in TEMPLATE.rglob("*") if p.name in RUNTIME_FILES]
        self.assertEqual(found, [], "a test or a tool wrote into the shipped template instead of a project")

    def test_every_host_a_tool_talks_to_is_in_the_privacy_table(self):
        privacy = privacy_hosts((REPO / "PRIVACY.md").read_text(encoding="utf-8-sig"))
        code_hosts = set()
        for p in TOOLS.rglob("*.py"):
            text = p.read_text(encoding="utf-8-sig")
            code_hosts |= {h for h in hosts_in(text)
                           if h not in {"example.com", "github.com", "huggingface.co", "docs.sarvam.ai"}
                           and not h.endswith(("w3.org", "python.org"))}
        # model_registry.json names vendors' docs; tools talk to the API hosts only
        missing = sorted(h for h in code_hosts if not any(h == x or h.endswith("." + x) or x.endswith("." + h) for x in privacy))
        self.assertEqual(missing, [], "add the host to PRIVACY.md (what it receives and when) or remove the call")

    def test_plant_an_unlisted_host_is_caught(self):
        self.assertEqual(hosts_in("urlopen('https://telemetry.example.net/ping')"), {"telemetry.example.net"})


if __name__ == "__main__":
    unittest.main()
