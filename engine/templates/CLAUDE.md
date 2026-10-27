# {{TITLE}}: guide for any AI agent working in this folder

Read PROJECT.md first (status, hard rules, where things are), then facts.md before touching anything with people in it.
This is a CutForge project (Remotion + Python). If the CutForge plugin is installed, its skills apply.

## The pipeline (each step re-runnable)
1. Narration text: film/script.json → `python tools/voice/gen_vo.py [ids]` (paid voices are quoted first: a run without --go prints the quote and spends nothing) → sound/vo/
2. Timing: `python film/timeline.py` (re-run after any narration or shots.json change; fix every ERROR, read every WARN)
3. Picture: film/shots.json layouts (AutoChapter) or src/chapters/*.tsx for hand-built scenes
   Stills first: `python tools/qc/stills.py <chapter>` → look at out/qc/<chapter>_sheet*.jpg
   Review page: `python tools/qc/storyboard.py` → out/storyboard/index.html (storyboard + photo map, one file)
   Music-first cuts: `python tools/mix/beats.py <music.wav> --snap <t>` → beats, bars, phrases to cut and cue on
4. Render: `CONC=<cores> bash tools/render/pipeline.sh <chapter>` (FRESH=1 after code/timing changes) → out/ch/<chapter>_f.mp4
5. Sound: `python tools/mix/film_mix.py` (all) or `... film_mix.py <chapter>` → out/film_mix.wav, then `python tools/qc/qc_audio.py`
6. Assemble: `VER=v2 bash tools/render/assemble.sh` → out/final/<slug>_v2.mp4 + 540p preview
7. QC: `python tools/qc/verify.py --decode`, `python tools/qc/qc_story.py`, watch the preview, log notes in NOTES_vN.md

## Rules
- Never delete or overwrite the client's files. Write new files next to them or in this project.
- Never print or commit API keys (tools/keys.py reads them; the quote gate in tools/spend.py gates paid calls; spend.md logs them).
- No AI generation on real people's faces. AI only where no camera was, and it must look like art, not a memory.
- Every fact about people, places, dates, rituals and quotes is verified (facts.md) before it goes on screen.
- Windows: run .sh files in Git Bash; set PYTHONUTF8=1 once (`setx PYTHONUTF8 1`).
