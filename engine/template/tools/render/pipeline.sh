#!/bin/bash
# Render chapters in resumable chunks, join them, drop the chunks, then grade + encode each chapter.
# usage: CONC=8 PRESET=warm bash tools/render/pipeline.sh <chapter> [chapter ...]     (or: all)
#   CONC   frames rendered in parallel (number of CPU cores to give it; 2 on a small cloud box)
#   PRESET grade preset (tools/grade/grade.py): warm | pop | neutral | bw | doc
#   FRESH=1 deletes a chapter's old chunks first (do this after you changed the chapter's code or timing)
# Output: out/ch/<chapter>_f.mp4 (graded, video only). Logs: out/ch/queue.log, out/ch/<chapter>.log, out/ch/grade.log
cd "$(dirname "$0")/../.." || exit 1
PY=${PY:-$(python3 -c "import sys" >/dev/null 2>&1 && echo python3 || echo python)}
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
PRESET=${PRESET:-warm}
CHS="$*"
[ "$CHS" = "all" ] || [ -z "$CHS" ] && CHS=$($PY -c "import json;print(' '.join(c['name'] for c in json.load(open('src/timeline.json',encoding='utf-8'))['chapters']))")
mkdir -p out/ch
for c in $CHS; do
  mkdir -p "out/ch/$c"
  if [ -n "$FRESH" ]; then rm -f "out/ch/$c"/p_*.mp4 "out/ch/$c.mp4" "out/ch/${c}_f.mp4"; fi
  echo "=== $c $(date +%H:%M:%S)" >> out/ch/queue.log
  ok=0
  for try in 1 2 3 4 5; do
    CONC=${CONC:-2} node render.mjs "$c" "out/ch/$c/p.mp4" chunks 750 >> "out/ch/$c.log" 2>&1 && ok=1 && break
    echo "    $c retry $try $(date +%H:%M:%S)" >> out/ch/queue.log; sleep 5
  done
  [ $ok = 1 ] || { echo "    $c FAILED, see out/ch/$c.log" >> out/ch/queue.log; continue; }
  (cd "out/ch/$c" && ls p_*.mp4 | sort | sed "s/^/file '/; s/$/'/" > list.txt && ffmpeg -nostdin -v error -y -f concat -safe 0 -i list.txt -c copy "../$c.mp4") \
    && rm -f "out/ch/$c"/p_*.mp4 && echo "    $c joined $(date +%H:%M:%S)" >> out/ch/queue.log
  RT="${TMPDIR:-$([ -n "$TEMP" ] && cygpath -u "$TEMP" 2>/dev/null || echo /tmp )}"   # the system temp folder, whichever shell this is
  rm -rf "$RT"/remotion-webpack-bundle-* "$RT"/remotion-v4.0.*-assets* 2>/dev/null
  ($PY tools/grade/grade.py "out/ch/$c.mp4" "out/ch/${c}_f.tmp.mp4" "$PRESET" >> out/ch/grade.log 2>&1 \
    && mv "out/ch/${c}_f.tmp.mp4" "out/ch/${c}_f.mp4" && echo "graded $c $(date +%H:%M:%S)" >> out/ch/queue.log) &
done
wait
$PY tools/qc/verify.py >> out/ch/queue.log 2>&1
echo "pipeline done $(date +%H:%M:%S)" >> out/ch/queue.log
tail -n 20 out/ch/queue.log
