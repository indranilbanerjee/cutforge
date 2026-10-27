"""The engine must do what the skills say it does. These run real tools in a freshly scaffolded demo project.

Each test pins a behaviour a skill relies on, most of them a bug found in a real production or in review:
  - the timeline derives every time from narration and refuses a fixed shot shorter than its line
  - the mixer re-mixes chapters whose start or length moved (else later audio drifts)
  - the beat finder lands on the beat (a sing-along was 0.7 s late once)
  - the storyboard page keeps every shot and its notes feature works
Tests that need numpy, Pillow, pedalboard or ffmpeg skip when those are missing.
"""
from __future__ import annotations

import json
import math
import py_compile
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

from _helpers import ENGINE, REPO, TEMPLATE, demo_project, engine_tools, has_cmd, has_module, load_json, run_tool


class TestEngineSources(unittest.TestCase):
    def test_python_compiles(self):
        for p in engine_tools() + [REPO / "__init__.py"]:
            if p.suffix == ".py":
                with self.subTest(tool=str(p.relative_to(REPO))):
                    py_compile.compile(str(p), doraise=True)

    def test_shell_scripts(self):
        for p in engine_tools():
            if p.suffix == ".sh":
                with self.subTest(tool=p.name):
                    self.assertRegex(p.read_text(encoding="utf-8").splitlines()[0], r"^#!/bin/(ba)?sh$")
                    if has_cmd("bash"):
                        # new_project.py writes .sh files with LF whatever the checkout did (autocrlf), so check that form.
                        # shutil.which finds Git's bash; the bare name "bash" can resolve to Windows' WSL launcher, which fails.
                        lf = Path(tempfile.mkdtemp()) / p.name
                        lf.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
                        done = subprocess.run([shutil.which("bash"), "-n", str(lf)], capture_output=True, text=True)
                        self.assertEqual(done.returncode, 0, done.stderr)

    @unittest.skipUnless(has_cmd("node"), "node not installed")
    def test_node_scripts_parse(self):
        for p in engine_tools():
            if p.suffix == ".mjs":
                with self.subTest(tool=p.name):
                    r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, r.stderr)

    def test_ffmpeg_calls_never_read_stdin(self):
        """ffmpeg inside a shell loop eats stdin; every call passes -nostdin, unless stdin IS its input (a frame pipe,
        where ffmpeg turns interaction off by itself)."""
        for p in engine_tools():
            lines = p.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                code_call = "['ffmpeg'" in line if p.suffix == ".py" else line.strip().startswith("ffmpeg ")
                if not code_call:
                    continue
                window = " ".join(lines[i:i + 4])
                if "'-i', '-'" in window:
                    continue
                with self.subTest(tool=p.name, line=i + 1):
                    self.assertIn("nostdin", line)

    def test_tools_never_hardcode_a_drive(self):
        for p in engine_tools():
            text = p.read_text(encoding="utf-8")
            with self.subTest(tool=p.name):
                self.assertNotRegex(text, r"['\"][A-Z]:\\\\", "a hard-coded Windows path")


class TestScaffoldAndTimeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proj = demo_project()

    def test_scaffold_has_memory_files_and_glyphs(self):
        for f in ("PROJECT.md", "facts.md", "decisions.md", "sources.md", "CLAUDE.md", "config.json",
                  "src/glyphs.json", "film/shots.json", "film/script.json"):
            with self.subTest(file=f):
                self.assertTrue((self.proj / f).is_file())

    def test_refuses_a_non_empty_target(self):
        r = subprocess.run([__import__("sys").executable, str(ENGINE / "new_project.py"), str(self.proj), "--demo"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_timeline_derives_lengths_from_narration(self):
        r = run_tool(self.proj, "film/timeline.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tl = load_json(self.proj / "film/timeline.json")
        self.assertEqual([c["name"] for c in tl["chapters"]], ["intro", "example", "story"])
        self.assertAlmostEqual(tl["total"], sum(c["dur"] for c in tl["chapters"]), places=2)
        shot = tl["chapters"][0]["shots"][1]                          # 1A: pre 0.8 + line + post 1.2
        line = shot["vo"][0]
        self.assertAlmostEqual(shot["dur"], 0.8 + line[2] + 1.2, delta=0.05)
        self.assertEqual(load_json(self.proj / "src/timeline.json"), tl)

    def test_fixed_shot_shorter_than_narration_is_an_error(self):
        shots_p = self.proj / "film/shots.json"
        original = shots_p.read_text(encoding="utf-8")
        try:
            doc = json.loads(original)
            doc["chapters"][0]["shots"][1]["fixed"] = 1.0
            shots_p.write_text(json.dumps(doc), encoding="utf-8")
            r = run_tool(self.proj, "film/timeline.py")
            self.assertEqual(r.returncode, 2)
            self.assertIn("ERROR", r.stdout + r.stderr)
        finally:
            shots_p.write_text(original, encoding="utf-8")
            run_tool(self.proj, "film/timeline.py")

    def test_short_tail_is_warned(self):
        shots_p = self.proj / "film/shots.json"
        original = shots_p.read_text(encoding="utf-8")
        try:
            doc = json.loads(original)
            doc["chapters"][0]["shots"][1]["post"] = 0.2
            shots_p.write_text(json.dumps(doc), encoding="utf-8")
            r = run_tool(self.proj, "film/timeline.py")
            self.assertEqual(r.returncode, 0)
            self.assertIn("WARN", r.stdout + r.stderr)
        finally:
            shots_p.write_text(original, encoding="utf-8")
            run_tool(self.proj, "film/timeline.py")

    def test_where_maps_a_time_to_its_shot(self):
        run_tool(self.proj, "film/timeline.py")
        r = run_tool(self.proj, "tools/qc/where.py", "0:05")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1A", r.stdout)


@unittest.skipUnless(all(has_module(m) for m in ("numpy", "soundfile", "pedalboard")), "numpy/soundfile/pedalboard missing")
class TestMixer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proj = demo_project()
        run_tool(cls.proj, "film/timeline.py")

    def test_minimum_fade_outs_are_enforced(self):
        code = ("import sys; sys.path.insert(0,'tools/mix'); sys.path.insert(0,'tools'); import film_mix as F;"
                "import numpy as np, soundfile as sf, os; os.makedirs('sound/t',exist_ok=True);"
                "sf.write('sound/t/a.wav', np.zeros((4800,2),'float32'), 48000);"
                "S=F.Sheet(F.TL); S.mus('sound/t/a.wav', 1.0, fo=0.1); S.sfx('sound/t/a.wav', 2.0, fo=0.01, hard=True);"
                "print(S.cues[0][7], S.cues[1][7])")
        r = run_tool(self.proj, "-c", code)
        self.assertEqual(r.returncode, 0, r.stderr)
        mus_fo, hard_fo = map(float, r.stdout.split())
        self.assertEqual(mus_fo, 1.5)        # music is raised to its 1.5 s minimum
        self.assertEqual(hard_fo, 0.01)      # an intended hard cut is respected

    def test_stale_chapters_are_detected(self):
        tl = load_json(self.proj / "film/timeline.json")
        mix = self.proj / "out/mix"
        mix.mkdir(parents=True, exist_ok=True)
        for c in tl["chapters"]:
            (mix / f"{c['name']}.json").write_text(json.dumps({"w0": c["start"] - 2, "start": c["start"], "dur": c["dur"]}))
        moved = tl["chapters"][2]
        (mix / f"{moved['name']}.json").write_text(json.dumps({"w0": 0, "start": moved["start"] - 1.5, "dur": moved["dur"]}))
        r = run_tool(self.proj, "-c", "import sys; sys.path.insert(0,'tools/mix'); sys.path.insert(0,'tools');"
                                      "import film_mix as F; print(','.join(F.stale()))")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), moved["name"])


@unittest.skipUnless(has_module("numpy") and has_cmd("ffmpeg"), "numpy or ffmpeg missing")
class TestBeats(unittest.TestCase):
    def test_finds_tempo_and_downbeat(self):
        proj = demo_project()
        sr, bpm, off, dur = 22050, 96, 0.5, 30
        frames = [0.0] * (sr * dur)
        beat = 60 / bpm
        k = 0
        while off + k * beat < dur - 0.3:
            i = int((off + k * beat) * sr)
            amp = 0.9 if k % 4 == 0 else 0.35
            for n in range(int(0.2 * sr)):
                frames[i + n] += amp * math.sin(2 * math.pi * 55 * n / sr) * math.exp(-n / sr * 18)
            for n in range(int(0.03 * sr)):
                frames[i + n] += 0.3 * math.sin(n * 1.7) * math.exp(-n / sr * 90)
            k += 1
        p = proj / "sound" / "click96.wav"
        p.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(p), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32000)) for x in frames))
        r = run_tool(proj, "tools/mix/beats.py", str(p))
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [l.split(",") for l in (proj / "out/music/click96_beats.csv").read_text().splitlines()[1:]]
        beats = [float(t) for kind, t, *_ in rows if kind == "beat"]
        bars = [float(t) for kind, t, *_ in rows if kind == "bar"]
        tempo = 60 / ((beats[-1] - beats[0]) / (len(beats) - 1))
        self.assertAlmostEqual(tempo, bpm, delta=2)
        self.assertAlmostEqual(bars[0], off, delta=0.04)


@unittest.skipUnless(has_module("PIL"), "Pillow missing")
class TestStoryboard(unittest.TestCase):
    def test_page_lists_every_shot_and_notes_work(self):
        proj = demo_project()
        run_tool(proj, "film/timeline.py")
        r = run_tool(proj, "tools/qc/storyboard.py")
        self.assertEqual(r.returncode, 0, r.stderr)
        html = (proj / "out/storyboard/index.html").read_text(encoding="utf-8")
        for sid in ("1T", "1A", "1B", "E1", "E2", "2A", "2B", "2C", "3A"):
            with self.subTest(shot=sid):
                self.assertIn(f">{sid}</b>", html)
        self.assertIn("Copy my notes", html)
        self.assertIn("lines.join('\\n')", html, "the copy button's newline must be escaped in the page's JS")
        self.assertIn("localStorage", html)


if __name__ == "__main__":
    unittest.main()
