#!/bin/sh
# Shape every on-screen string in tools/text/shape_jobs.json with HarfBuzz into src/glyphs.json, then apply
# manual kerning from tools/text/kern.json. Run after adding or changing any InkText string.
cd "$(dirname "$0")/../.." || exit 1
PY=${PY:-$(python3 -c "import sys" >/dev/null 2>&1 && echo python3 || echo python)}
node tools/text/shape.mjs tools/text/shape_jobs.json src/glyphs.json && PYTHONUTF8=1 $PY tools/text/kern.py
