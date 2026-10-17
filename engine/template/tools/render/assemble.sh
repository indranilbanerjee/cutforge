#!/bin/bash
# Join the graded chapters (in timeline order) with the master mix into ONE film, plus a light 540p preview.
# usage: VER=v2 bash tools/render/assemble.sh      (default v1; a new VER per cut, so nothing delivered is overwritten)
set -e
cd "$(dirname "$0")/../.." || exit 1
PY=${PY:-$(python3 -c "import sys" >/dev/null 2>&1 && echo python3 || echo python)}
VER=${VER:-v1}
NAME=$($PY -c "import json,re;c=json.load(open('config.json',encoding='utf-8')) if __import__('os').path.exists('config.json') else {};print(re.sub(r'[^A-Za-z0-9_-]+','_',c.get('slug') or c.get('title') or 'film'))")
TITLE=$($PY -c "import json,os;c=json.load(open('config.json',encoding='utf-8')) if os.path.exists('config.json') else {};print(c.get('title','film'))")
ORDER=$($PY -c "import json;print(' '.join(c['name'] for c in json.load(open('src/timeline.json',encoding='utf-8'))['chapters']))")
mkdir -p out/final
: > out/final/list.txt
for c in $ORDER; do
  [ -f "out/ch/${c}_f.mp4" ] || { echo "missing graded chapter: $c (run tools/render/pipeline.sh $c)"; exit 1; }
  echo "file '../ch/${c}_f.mp4'" >> out/final/list.txt
done
[ -f out/film_mix.wav ] || { echo "missing out/film_mix.wav (run tools/mix/film_mix.py)"; exit 1; }
OUTF="out/final/${NAME}_${VER}.mp4"
ffmpeg -nostdin -v error -y -f concat -safe 0 -i out/final/list.txt -i out/film_mix.wav -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart -metadata title="$TITLE" "$OUTF"
ffmpeg -nostdin -v error -y -i "$OUTF" -vf scale=-2:540:flags=lanczos -c:v libx264 -preset medium -crf 25 -maxrate 2200k -bufsize 4M \
  -profile:v high -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart "out/final/${NAME}_${VER}_preview540.mp4"
$PY tools/qc/verify.py --final "$OUTF"
ls -la out/final
