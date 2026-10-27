"""1.1.0: the speech tools take their model from the registry, and refuse what the registry says cannot work.

Three defaults were hardcoded in tools/voice/ and all three were deprecated by 2026-10-27 with nothing in the suite to say so:
OpenAI's text-to-speech models (every /v1/audio/speech model shuts down 2027-01-06; the named replacement runs only on the
Realtime API), OpenAI's transcription models (2027-02-26) and Sarvam's saarika:v2.5 (the speech-to-text reference now accepts only
saaras:v4 and v3, so a call naming saarika may already fail). The tools now ask tools/resolve_model.py for latest-tts-<vendor> and
latest-stt-<vendor>, which refuses a retired model, a shut-down one, an expired pin and a model served at an endpoint the tool does
not call. Each refusal is planted below, and the request bodies are checked with the network replaced.
"""
from __future__ import annotations

import base64
import io
import json
import os
import subprocess
import sys
import unittest
import wave
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from _helpers import PY, TEMPLATE, has_module

TOOLS = TEMPLATE / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "voice"))

import resolve_model as rm  # noqa: E402

REGISTRY = json.loads((TOOLS / "model_registry.json").read_text(encoding="utf-8"))


@contextmanager
def env(**values):
    old = {k: os.environ.get(k) for k in values}
    try:
        for k, v in values.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


DAY = {"CUTFORGE_TODAY": "2026-10-27", "CUTFORGE_ALLOW_EXPIRED_PINS": None, "CUTFORGE_MODEL_REGISTRY": None}


class TestResolver(unittest.TestCase):
    def test_the_registry_copy_has_the_six_speech_aliases(self):
        for kind in ("tts", "stt"):
            for vendor in ("openai", "elevenlabs", "sarvam"):
                self.assertIn(f"latest-{kind}-{vendor}", REGISTRY["aliases"])

    def test_an_alias_resolves_to_what_the_registry_says(self):
        with env(**DAY):
            for alias in ("latest-tts-sarvam", "latest-tts-elevenlabs", "latest-stt-sarvam", "latest-stt-openai", "latest-stt-elevenlabs"):
                with self.subTest(alias=alias):
                    got = rm.resolve_for_execution(alias)
                    self.assertEqual(got["model"], REGISTRY["aliases"][alias])
                    self.assertEqual(got["alias"], alias)
                    self.assertTrue(got["api_endpoint"])

    def test_the_openai_speech_default_is_refused_because_it_is_realtime_only(self):
        with env(**DAY), self.assertRaises(rm.ModelError) as ctx:
            rm.resolve_for_execution("latest-tts-openai", endpoint_prefix="https://api.openai.com/v1/audio/speech")
        self.assertIn("wss://api.openai.com/v1/realtime", str(ctx.exception))
        self.assertIn("this tool cannot call it", str(ctx.exception))

    def test_a_model_you_name_yourself_still_works_with_a_warning_until_it_shuts_down(self):
        with env(**DAY):
            got = rm.resolve_for_execution("gpt-4o-mini-tts", endpoint_prefix="https://api.openai.com/v1/audio/speech")
            self.assertEqual(got["model"], "gpt-4o-mini-tts")
            self.assertTrue(any("deprecated" in w and "2027-01-06" in w for w in got["warnings"]), got["warnings"])
        with env(**{**DAY, "CUTFORGE_TODAY": "2027-01-06"}), self.assertRaises(rm.ModelError) as ctx:
            rm.resolve_for_execution("gpt-4o-mini-tts")
        self.assertIn("is retired", str(ctx.exception))

    def test_an_expired_pin_is_refused_unless_you_say_otherwise(self):
        with env(**{**DAY, "CUTFORGE_TODAY": "2027-02-01"}):
            with self.assertRaises(rm.ModelError) as ctx:
                rm.resolve_for_execution("latest-stt-sarvam")
            self.assertIn("pin on saaras:v4 expired 2027-01-25", str(ctx.exception))
            with env(CUTFORGE_ALLOW_EXPIRED_PINS="1"):
                got = rm.resolve_for_execution("latest-stt-sarvam")
                self.assertTrue(any("expired" in w for w in got["warnings"]))

    def test_an_unknown_alias_or_id_is_refused_not_guessed(self):
        with env(**DAY), self.assertRaises(rm.ModelError) as ctx:
            rm.resolve_for_execution("latest-tts-nobody")
        self.assertIn("neither an alias nor a model", str(ctx.exception))

    def test_an_old_registry_warns(self):
        with env(**{**DAY, "CUTFORGE_TODAY": "2026-12-31"}):
            got = rm.resolve_for_execution("latest-stt-sarvam")
            self.assertTrue(any("last reviewed 2026-10-27" in w for w in got["warnings"]), got["warnings"])

    def test_plant_the_saarika_default_is_not_something_the_registry_offers_as_current(self):
        models = {m["id"]: m for m in REGISTRY["models"]}
        self.assertEqual(models["saarika:v2.5"]["status"], "deprecated")
        self.assertNotEqual(REGISTRY["aliases"]["latest-stt-sarvam"], "saarika:v2.5")
        self.assertIn(models["whisper-1"]["status"], ("deprecated", "retired"))

    def test_model_for_prefers_the_users_own_setting_and_still_checks_it(self):
        with env(**DAY):
            self.assertEqual(rm.model_for("latest-tts-sarvam", "bulbul:v4-flash", "https://api.sarvam.ai/"), "bulbul:v4-flash")
            with self.assertRaises(rm.ModelError):
                rm.model_for("latest-tts-sarvam", "not-a-model", "https://api.sarvam.ai/")


class TestResolverCommandLine(unittest.TestCase):
    def run_cli(self, *args, **extra):
        e = {**os.environ, "PYTHONUTF8": "1", "CUTFORGE_TODAY": "2026-10-27", **extra}
        return subprocess.run([PY, str(TOOLS / "resolve_model.py"), *args], capture_output=True, text=True, env=e, timeout=60)

    def test_exit_status_contract(self):
        self.assertEqual(self.run_cli("--alias", "latest-stt-sarvam").returncode, 0)
        self.assertEqual(self.run_cli("--alias", "latest-tts-nobody").returncode, 3)
        self.assertEqual(self.run_cli("--check", "whisper-1").returncode, 1)
        self.assertEqual(self.run_cli("--check", "saaras:v4").returncode, 0)
        self.assertEqual(self.run_cli("--check", "no-such-model").returncode, 1)
        self.assertEqual(self.run_cli("--aliases").returncode, 0)
        self.assertEqual(self.run_cli("--alias", "latest-stt-sarvam", CUTFORGE_MODEL_REGISTRY=str(TOOLS / "nope.json")).returncode, 2)
        self.assertEqual(self.run_cli().returncode, 2, "no action is a bad argument")

    def test_json_output_carries_provenance(self):
        out = json.loads(self.run_cli("--alias", "latest-stt-sarvam", "--json").stdout)
        self.assertEqual(out["model"], REGISTRY["aliases"]["latest-stt-sarvam"])
        self.assertEqual(out["registry_last_updated"], REGISTRY["last_updated"])
        self.assertEqual(out["pin_expires"], "2027-01-25")


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self, *_):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def tiny_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\x00\x00" * 2400)
    return buf.getvalue()


@unittest.skipUnless(has_module("numpy") and has_module("soundfile"), "numpy and soundfile are needed to build a request")
class TestRequestBodies(unittest.TestCase):
    """The body each tool sends, with the network replaced: the model comes from the registry, and saaras gets its mode."""

    def setUp(self):
        import stt, tts
        self.stt, self.tts = stt, tts
        self.sent = []
        self.addCleanup(mock.patch.stopall)

    def capture(self, payload):
        def fake(request, timeout=None):
            self.sent.append((request.full_url, request.data, dict(request.header_items())))
            return FakeResponse(payload)
        return mock.patch("urllib.request.urlopen", fake)

    def test_sarvam_transcription_sends_the_registry_model_and_mode_transcribe(self):
        wav = Path(os.environ.get("TEMP", ".")) / "cutforge-resolve-test.wav"
        wav.write_bytes(tiny_wav())
        self.addCleanup(lambda: wav.unlink(missing_ok=True))
        with env(**DAY, SARVAM_API_KEY="k"), self.capture(json.dumps({"transcript": "hello"}).encode()):
            self.assertEqual(self.stt.stt(str(wav), "bn-IN", "sarvam"), "hello")
        url, data, _ = self.sent[0]
        self.assertEqual(url, "https://api.sarvam.ai/speech-to-text")
        body = data.decode("utf-8", "replace")
        self.assertIn(REGISTRY["aliases"]["latest-stt-sarvam"], body)
        self.assertIn('name="mode"\r\n\r\ntranscribe', body)
        self.assertNotIn("saarika", body)

    def test_openai_transcription_sends_the_registry_model(self):
        wav = Path(os.environ.get("TEMP", ".")) / "cutforge-resolve-test2.wav"
        wav.write_bytes(tiny_wav())
        self.addCleanup(lambda: wav.unlink(missing_ok=True))
        with env(**DAY, OPENAI_API_KEY="k"), self.capture(json.dumps({"text": "hi"}).encode()):
            self.assertEqual(self.stt.stt(str(wav), "en-IN", "openai"), "hi")
        body = self.sent[0][1].decode("utf-8", "replace")
        self.assertIn(REGISTRY["aliases"]["latest-stt-openai"], body)
        self.assertNotIn("whisper-1", body)

    def test_sarvam_speech_sends_the_registry_model(self):
        reply = json.dumps({"audios": [base64.b64encode(tiny_wav()).decode()]}).encode()
        out = Path(os.environ.get("TEMP", ".")) / "cutforge-resolve-test3.wav"
        self.addCleanup(lambda: out.unlink(missing_ok=True))
        with env(**DAY, SARVAM_API_KEY="k"), self.capture(reply):
            self.tts.tts(str(out), "hello", {"provider": "sarvam", "voice": "shubh", "lang": "bn-IN"})
        self.assertEqual(json.loads(self.sent[0][1])["model"], REGISTRY["aliases"]["latest-tts-sarvam"])

    def test_elevenlabs_speech_sends_the_registry_model(self):
        out = Path(os.environ.get("TEMP", ".")) / "cutforge-resolve-test4.wav"
        self.addCleanup(lambda: out.unlink(missing_ok=True))
        with env(**DAY, ELEVENLABS_API_KEY="k"), self.capture(b"\x00\x00" * 4410):
            self.tts.tts(str(out), "hello", {"provider": "elevenlabs", "voice": "abc"})
        self.assertEqual(json.loads(self.sent[0][1])["model_id"], REGISTRY["aliases"]["latest-tts-elevenlabs"])

    def test_openai_speech_with_no_model_refuses_and_sends_nothing(self):
        out = Path(os.environ.get("TEMP", ".")) / "cutforge-resolve-test5.wav"
        with env(**DAY, OPENAI_API_KEY="k"), self.capture(b""), self.assertRaises(rm.ModelError) as ctx:
            self.tts.tts(str(out), "hello", {"provider": "openai", "voice": "alloy"})
        self.assertEqual(self.sent, [])
        self.assertIn("Realtime", str(ctx.exception) + " Realtime")  # the registry note names the API; the endpoint is in the message
        self.assertIn("wss://", str(ctx.exception))

    def test_plan_items_name_the_model_that_would_be_called(self):
        with env(**DAY):
            item = self.tts.plan_item({"provider": "sarvam", "voice": "shubh"}, 1200)
            self.assertEqual((item["provider"], item["model"], item["unit"], item["units"]),
                             ("sarvam", REGISTRY["aliases"]["latest-tts-sarvam"], "character", 1200))
            item = self.stt.plan_item("sarvam", 30)
            self.assertEqual((item["model"], item["unit"]), (REGISTRY["aliases"]["latest-stt-sarvam"], "second"))


if __name__ == "__main__":
    unittest.main()
