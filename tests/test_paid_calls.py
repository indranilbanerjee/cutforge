"""1.1.0: a paid call needs a live quote, an approved provider list, the client's typed go and a cap, and takes its model from the registry.

CutForge's budget gate (1.0.x) took the estimate from whoever called it (`ai_gen.py --inr 8`, a rate typed into gen_vo.py as
`inr_per_1k_chars`), and its only approval was a GO_AHEAD.txt that an agent can create. The model ids were literals: a speech model
OpenAI shuts down on 2027-01-06, two transcription ids that were deprecated by the time anyone looked. The gate now works like
SocialForge's: no prices ship (price_book.py records one with the page it was read from, and it expires), a paid tool run WITHOUT
--go prints the quote and exits 4, a run with --go must name the quoted providers, and the cap is checked against spend.md.

Each rule is planted: a missing and a stale price, no go, an unquoted provider, the cap, and the old GO_AHEAD.txt file.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _helpers import ENGINE, PY, REPO, TEMPLATE

TOOLS = TEMPLATE / "tools"
sys.path.insert(0, str(TOOLS))

import price_book  # noqa: E402
import spend  # noqa: E402

SOURCE = "https://example.com/pricing"


class Isolated(unittest.TestCase):
    """price_book.json and spend.md go to a temporary folder, never into the template that ships."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cutforge-paid-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self._saved = (price_book.BOOK, spend.LOG, dict(price_book.CFG))
        price_book.BOOK = str(self.tmp / "price_book.json")
        spend.LOG = str(self.tmp / "spend.md")
        price_book.CFG.clear()
        self.addCleanup(self._restore)
        os.environ.pop("CUTFORGE_NOW", None)

    def _restore(self):
        price_book.BOOK, spend.LOG = self._saved[0], self._saved[1]
        price_book.CFG.clear()
        price_book.CFG.update(self._saved[2])
        os.environ.pop("CUTFORGE_NOW", None)

    def price(self, provider="sarvam", model="m", unit="1k-characters", price=30.0, currency="INR"):
        return price_book.record(provider, model, unit, price, currency, SOURCE)

    ITEM = {"provider": "sarvam", "model": "m", "unit": "character", "units": 2000}


class TestPriceBook(Isolated):
    def test_no_price_ships_and_none_is_assumed(self):
        self.assertEqual(price_book.quote("sarvam", "m", 1000, "character")["status"], "missing")
        self.assertFalse((TEMPLATE / "price_book.json").exists(), "a price book must never ship in the template")

    def test_a_price_needs_the_page_it_was_read_from(self):
        for bad in ("", "http://example.com", "pricing page"):
            with self.subTest(source=bad), self.assertRaises(ValueError):
                price_book.record("sarvam", "m", "second", 1, "INR", bad)
        with self.assertRaises(ValueError):
            price_book.record("sarvam", "m", "second", -1, "INR", SOURCE)

    def test_units_convert_inside_a_family(self):
        self.price(unit="1k-characters", price=30)
        q = price_book.quote("sarvam", "m", 2500, "character")
        self.assertEqual((q["status"], q["amount"], q["currency"]), ("ok", 75.0, "INR"))
        self.price(provider="stt", unit="minute", price=6)
        self.assertEqual(price_book.quote("stt", "m", 30, "second")["amount"], 3.0)

    def test_a_price_in_another_family_is_not_guessed(self):
        self.price(unit="1k-characters")
        q = price_book.quote("sarvam", "m", 10, "second")
        self.assertEqual(q["status"], "missing")
        self.assertIn("counted in second", q["look_up"])

    def test_a_stale_price_blocks_until_it_is_read_again(self):
        os.environ["CUTFORGE_NOW"] = "2026-10-27T00:00:00+00:00"
        self.price()
        os.environ["CUTFORGE_NOW"] = "2026-11-10T00:00:00+00:00"
        q = price_book.quote("sarvam", "m", 1000, "character")
        self.assertEqual(q["status"], "stale")
        self.assertGreater(q["age_hours"], 168)
        price_book.CFG["price_max_age_hours"] = 24 * 30
        self.assertEqual(price_book.quote("sarvam", "m", 1000, "character")["status"], "ok")

    def test_the_cli_exits_4_when_a_price_is_needed_and_2_for_a_bad_one(self):
        self.assertEqual(price_book.main(["quote", "--provider", "x", "--model", "y", "--units", "1", "--unit", "second"]), 4)
        self.assertEqual(price_book.main(["record", "--provider", "x", "--model", "y", "--unit", "second", "--price", "1",
                                          "--currency", "INR", "--source", "http://no-tls"]), 2)
        self.assertEqual(price_book.main(["record", "--provider", "x", "--model", "y", "--unit", "second", "--price", "1",
                                          "--currency", "INR", "--source", SOURCE]), 0)


class TestSpendGate(Isolated):
    def test_no_fresh_price_means_nothing_runs(self):
        with self.assertRaises(spend.NeedsQuote) as ctx:
            spend.plan("tts", [self.ITEM], quoted=["sarvam"], go=True)
        self.assertIn("nothing was spent", str(ctx.exception))
        self.assertIn("price_book.py record", str(ctx.exception))

    def test_without_go_the_quote_is_shown_and_nothing_runs(self):
        self.price()
        with self.assertRaises(spend.NeedsGo) as ctx:
            spend.plan("tts", [self.ITEM])
        text = str(ctx.exception)
        self.assertIn("60.00 INR", text)
        self.assertIn(SOURCE, text)
        self.assertIn("Nothing was spent", text)
        self.assertIn("--go --quoted-providers sarvam", text)

    def test_go_without_the_quoted_providers_is_refused(self):
        self.price()
        with self.assertRaises(spend.NeedsRequote):
            spend.plan("tts", [self.ITEM], go=True)
        with self.assertRaises(spend.NeedsRequote) as ctx:
            spend.plan("tts", [self.ITEM], quoted=["elevenlabs"], go=True)
        self.assertIn("sarvam is not in --quoted-providers", str(ctx.exception))

    def test_a_quoted_provider_with_go_may_run_and_is_logged(self):
        self.price()
        got = spend.plan("tts", [self.ITEM], quoted=["Sarvam"], go=True)
        self.assertEqual(got["totals"], {"INR": 60.0})
        totals = spend.log_plan("tts", got, "12 lines")
        self.assertEqual(totals, {"INR": 60.0})
        self.assertEqual(spend.total("INR"), 60.0)
        row = Path(spend.LOG).read_text(encoding="utf-8").splitlines()[-1]
        self.assertIn("| tts | sarvam | m | 12 lines | 60.00 | INR |", row)

    def test_the_cap_is_checked_against_what_is_already_spent(self):
        self.price()
        spend.CFG["budget_inr"] = 100
        try:
            first = spend.plan("tts", [self.ITEM], quoted=["sarvam"], go=True)
            spend.log_plan("tts", first, "first")
            with self.assertRaises(PermissionError) as ctx:
                spend.plan("tts", [self.ITEM], quoted=["sarvam"], go=True)
            self.assertIn("would pass the budget cap", str(ctx.exception))
        finally:
            spend.CFG.pop("budget_inr", None)

    def test_a_quote_in_another_currency_is_not_compared_to_an_inr_cap(self):
        self.price(currency="USD", price=1)
        spend.CFG["budget_inr"] = 1000
        try:
            with self.assertRaises(PermissionError) as ctx:
                spend.plan("tts", [self.ITEM], quoted=["sarvam"], go=True)
            self.assertIn("budget_usd", str(ctx.exception))
        finally:
            spend.CFG.pop("budget_inr", None)

    def test_plant_the_old_go_ahead_file_is_not_an_approval(self):
        """1.0.x let any agent create GO_AHEAD.txt and spend. A file of that name changes nothing now."""
        self.price()
        (self.tmp / "GO_AHEAD.txt").write_text("go", encoding="utf-8")
        with self.assertRaises(spend.NeedsGo):
            spend.plan("tts", [self.ITEM])
        self.assertNotIn("GO_AHEAD", (TOOLS / "spend.py").read_text(encoding="utf-8").split('"""', 2)[2],
                         "spend.py must not read a GO_AHEAD.txt")

    def test_legacy_rows_still_count_toward_the_cap(self):
        Path(spend.LOG).write_text("# Spend log\n\n| time | tool | model | for | ₹ | total | note |\n|---|---|---|---|---|---|---|\n"
                                   "| 2026-10-01 10:00 | ai_gen | m | x | ₹40.00 | total |  |\n", encoding="utf-8")
        self.assertEqual(spend.total("INR"), 40.0)

    def test_parse_flags_pulls_the_two_flags_out_and_keeps_the_rest(self):
        go, quoted, rest = spend.parse_flags(["3A", "--go", "--quoted-providers", "Sarvam,openai", "--all"])
        self.assertEqual((go, quoted, rest), (True, ["sarvam", "openai"], ["3A", "--all"]))
        go, quoted, rest = spend.parse_flags(["--quoted-providers=a", "x"])
        self.assertEqual((go, quoted, rest), (False, ["a"], ["x"]))


class TestNoStoredRates(unittest.TestCase):
    def test_no_tool_carries_a_rate_or_reads_the_old_approval_file(self):
        banned = ("inr_per_1k_chars", "COST_PER_1K_CHARS", "GO_AHEAD.txt", "est_inr")
        hits = []
        for p in TOOLS.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            code = p.read_text(encoding="utf-8-sig")
            for word in banned:
                if word in code:
                    hits.append(f"{p.relative_to(REPO).as_posix()}: {word}")
        # spend.py names GO_AHEAD.txt once, in the sentence that says it is no longer read
        self.assertEqual([h for h in hits if not h.startswith("engine/template/tools/spend.py: GO_AHEAD.txt")], [])


class TestPaidToolsFromTheCommandLine(unittest.TestCase):
    """A fresh project with a paid voice: each paid tool must exit 4 and leave no audio behind, with and without a recorded price."""

    @classmethod
    def make(cls, name):
        proj = cls.tmp / name
        r = subprocess.run([PY, str(ENGINE / "new_project.py"), str(proj), "--title", "Paid", "--demo"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        script = json.loads((proj / "film" / "script.json").read_text(encoding="utf-8"))
        script["language"] = "bn-IN"
        script["voice"] = {"provider": "sarvam", "voice": "shubh", "lang": "bn-IN"}
        (proj / "film" / "script.json").write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
        cfg = json.loads((proj / "config.json").read_text(encoding="utf-8"))
        cfg["budget_inr"] = 50
        (proj / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        return proj

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="cutforge-paidcli-"))
        cls.bare = cls.make("bare")          # no price recorded
        cls.priced = cls.make("priced")      # prices recorded for the Sarvam voice and its transcription
        for model, unit in (("bulbul:v3", "1k-characters"), ("saaras:v4", "minute")):
            r = cls.run_in(cls.priced, "tools/price_book.py", "record", "--provider", "sarvam", "--model", model, "--unit", unit,
                           "--price", "1", "--currency", "INR", "--source", SOURCE)
            assert r.returncode == 0, r.stderr

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @staticmethod
    def run_in(proj, *args):
        env = {**os.environ, "PYTHONUTF8": "1", "SARVAM_API_KEY": "not-a-real-key"}
        return subprocess.run([PY, *args], cwd=proj, capture_output=True, text=True, env=env, timeout=120)

    @staticmethod
    def wavs(proj):
        return sorted((proj / "sound" / "vo").glob("*.wav"))

    def test_gen_vo_without_a_price_exits_4_and_spends_nothing(self):
        before = self.wavs(self.bare)
        r = self.run_in(self.bare, "tools/voice/gen_vo.py", "--all")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("no fresh price", r.stderr)
        self.assertEqual(self.wavs(self.bare), before)
        self.assertFalse((self.bare / "spend.md").exists())

    def test_with_prices_but_no_go_it_prints_the_quote_and_exits_4(self):
        before = self.wavs(self.priced)
        r = self.run_in(self.priced, "tools/voice/gen_vo.py", "--all")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("Nothing was spent", r.stdout)
        self.assertIn("--go --quoted-providers sarvam", r.stdout)
        self.assertIn(SOURCE, r.stdout)
        self.assertEqual(self.wavs(self.priced), before)
        self.assertFalse((self.priced / "spend.md").exists())

    def test_go_without_the_quoted_providers_exits_4(self):
        r = self.run_in(self.priced, "tools/voice/gen_vo.py", "--all", "--go")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("is not in --quoted-providers", r.stdout + r.stderr)

    def test_a_quoted_provider_that_is_not_the_voices_exits_4(self):
        r = self.run_in(self.priced, "tools/voice/gen_vo.py", "--all", "--go", "--quoted-providers", "elevenlabs")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertFalse((self.priced / "spend.md").exists())

    def test_a_quote_over_the_cap_exits_4_even_with_go(self):
        # the demo script's lines cost far more than the 50 INR cap at 1 INR per 1,000 characters only if it is long; force it
        r = self.run_in(self.priced, "tools/price_book.py", "record", "--provider", "sarvam", "--model", "bulbul:v3",
                        "--unit", "character", "--price", "5", "--currency", "INR", "--source", SOURCE)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_in(self.priced, "tools/voice/gen_vo.py", "--all", "--go", "--quoted-providers", "sarvam")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("would pass the budget cap", r.stderr)

    def test_ai_gen_without_go_exits_4(self):
        r = self.run_in(self.bare, "tools/vfx/ai_gen.py", "image", "vendor/model/text-to-image", "out.png", "a hill", "--inr", "8")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("--inr is ignored", r.stderr)
        self.assertFalse((self.bare / "out.png").exists())

    def test_audition_without_go_exits_4(self):
        (self.bare / "film" / "audition.json").write_text(json.dumps({
            "lines": [{"id": "x", "text": "a short line"}],
            "candidates": [{"name": "v", "provider": "sarvam", "voice": "shubh", "lang": "bn-IN"}]}), encoding="utf-8")
        r = self.run_in(self.bare, "tools/voice/audition.py", "film/audition.json")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)

    def test_spend_cli_reports_totals_and_caps(self):
        r = self.run_in(self.bare, "tools/spend.py")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("'INR': 50.0", r.stdout)


if __name__ == "__main__":
    unittest.main()
