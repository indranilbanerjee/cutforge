"""Two things must never be named anywhere in the repository.

1. The methodology's source organization (a suite-wide product rule).
2. Anything that identifies the family behind the case study: names, places, the voice id, the exact runtime,
   the occasion. The case study is anonymised on purpose; one stray line undoes it.

The forbidden strings are assembled from fragments at runtime so this file itself stays grep-clean.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from _helpers import REPO

SKIP_DIRS = {".git", "__pycache__", "node_modules"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".ttf", ".woff", ".woff2", ".zip", ".pyc"}


def _needles() -> list[re.Pattern]:
    parts = [
        "tech" + "shu", "int" + "global", r"\bint\.?\s+" + "global" + r"\b",          # the source organization
        "maha" + "ksh", r"\bma" + r"ha\b", "bon" + "ita", "bi" + "ki", "ha" + "kola", "pan" + "chla", "how" + "rah",
        "ki" + "ku", "tha" + "am", "da" + "dun", "di" + "dun", "pon" + "tai", "lab" + "oni",
        r"svc-[0-9a-f]{6}", "19" + ":41", r"\b4th\s+" + "birth" + "day", r"\bfourth\s+" + "birth" + "day",
        "₹" + "272", "preg" + "nan", "miscar" + "riage", "ultra" + "sound",
        "মহাক্স",                                       # the name in Bengali script
    ]
    return [re.compile(p, re.I) for p in parts]


class TestSourceAnonymity(unittest.TestCase):
    def test_nothing_identifying_anywhere(self):
        needles = _needles()
        me = Path(__file__).resolve()
        hits = []
        for p in REPO.rglob("*"):
            if not p.is_file() or any(part in SKIP_DIRS for part in p.parts) or p.suffix.lower() in SKIP_SUFFIXES:
                continue
            if p.resolve() == me or p.name.startswith("OFL_"):
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for n in needles:
                m = n.search(text)
                if m:
                    hits.append(f"{p.relative_to(REPO)}:{text.count(chr(10), 0, m.start()) + 1} ({n.pattern})")
        self.assertEqual(hits, [], "identifying text found: " + ", ".join(hits))

    def test_no_key_like_strings(self):
        pat = re.compile(r"(sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{30,}|xox[bp]-[A-Za-z0-9-]{20,})")
        for p in REPO.rglob("*"):
            if p.is_file() and not any(part in SKIP_DIRS for part in p.parts) and p.suffix.lower() not in SKIP_SUFFIXES:
                with self.subTest(file=str(p.relative_to(REPO))):
                    self.assertIsNone(pat.search(p.read_text(encoding="utf-8", errors="ignore")))


if __name__ == "__main__":
    unittest.main()
