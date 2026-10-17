"""Run every test_*.py in this directory. Exit non-zero on failure.

Stdlib only; no pytest needed. Engine tests that need numpy, Pillow, pedalboard or ffmpeg skip cleanly when those
are missing, and say so.

Usage:
    python tests/run_all.py
    python tests/run_all.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))


def main() -> int:
    suite = unittest.TestLoader().discover(start_dir=str(TESTS_DIR), pattern="test_*.py", top_level_dir=str(TESTS_DIR))
    result = unittest.TextTestRunner(verbosity=2 if "-v" in sys.argv else 1).run(suite)
    import _helpers
    _helpers.cleanup()
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
