---
name: render-and-assemble
description: "Render and assemble the video: timeline, stills, chunked chapters, grade, mix, verify. \"render the film\""
user-invocable: true
---

# Render and assemble: build in verifiable units, never the whole film for one fix

Rendering dominates the schedule: about 20 minutes of 1080p film took 5-6 hours on a 2-CPU cloud box; an
8-core desktop with a GPU is 3-5x faster. So the film is split into chapters (one composition each), each
chapter renders in resumable chunks, and a fix re-renders only the chapter it touches.

## Set up once per machine

```bash
cd <project> && npm install && python tools/setup_local.py      # node 18+, ffmpeg, python modules, UTF-8 mode
python tools/fetch_models.py                                      # only if face/depth tools are needed
python tools/mix/synth.py                                         # synth beds, bells and room tone
```
Windows: run `.sh` files in Git Bash, `setx PYTHONUTF8 1` once (Indic JSON crashes cp1252), GPU GL (`angle`)
is the default there; `python3` may be a Store stub (the scripts fall back to `python`). Keep the project on a
data drive with room (a 20-minute film needs ~15-25 GB working space).

## The build order (each step re-runnable)

1. **Timing**: `python film/timeline.py`. Fix every ERROR (narration longer than a fixed shot, a missing line);
   read every WARN (short tails, no breath before speech, unused lines).
2. **Stills**: `python tools/qc/stills.py <chapter>` → look at `out/qc/<chapter>_sheet*.jpg` (Read them):
   safe area, caption size, collisions, identity, spelling. Fix before rendering video.
3. **Render**: `CONC=<cores> PRESET=warm bash tools/render/pipeline.sh <chapter ...|all>`. Chunks of 750 frames
   (`out/ch/<chapter>/p_000.mp4` ...) are skipped if present, so a killed render resumes. After changing a
   chapter's code or timing use `FRESH=1` for that chapter, or old chunks are reused. Output:
   `out/ch/<chapter>_f.mp4` (graded, video only). Logs: `out/ch/queue.log`, `<chapter>.log`, `grade.log`.
4. **Mix**: `python tools/mix/film_mix.py` (or one chapter) → `out/film_mix.wav`; then
   `python tools/qc/qc_audio.py` (0 flags, or each one recorded as intended).
5. **Assemble**: `VER=v2 bash tools/render/assemble.sh` → `out/final/<slug>_v2.mp4` + a 540p preview. A new
   `VER` per cut, so nothing delivered is ever overwritten.
6. **Verify**: `python tools/qc/verify.py --decode` (every chapter has exactly the frames the timeline says and
   decodes cleanly) and `verify.py --final out/final/<file>` (duration, frames, audio). Then watch the preview.

## Partial re-renders (the normal case after the first cut)

- A narration change re-times only its chapter's picture (chapters are independent compositions); later
  chapters do not need re-rendering, only re-assembly, because the master is a concatenation.
- The mix is global: re-mix the changed chapter (`film_mix.py e2`) and the master rebuilds from stems; chapters
  whose start or length moved since their last mix are re-mixed automatically (their audio would drift otherwise).
- Splicing a re-rendered piece into a chapter with stream copy only works at keyframes; after any splice run
  `verify.py --decode`, else re-render the chapter.
- Keep chapters 1-3 minutes long so one fix costs minutes of render, not an hour.

## Long renders without surprises

- Cloud workspaces can be reclaimed when idle and background jobs die with them: run the pipeline as a
  tracked background job, keep a watcher on `out/ch/queue.log`, and never idle-wait on a 5-hour job.
- Disk: delete raw chunks after concat (the pipeline does), delete transfer parts after verification, keep only
  graded chapters and the master. A box at 93 % full mid-render is a real failure mode.
- Clear Remotion's temp bundles between chapters on small disks (the pipeline does).
- Estimate before starting: frames × seconds-per-frame / CONC from a stills or chunk timing; tell the client.

## Before calling a build done

- [ ] timeline 0 ERROR; stills of changed shots looked at
- [ ] `verify.py --decode` OK for every chapter; `--final` OK for the master
- [ ] `qc_audio.py` 0 flags (or intended ones recorded); loudness on target
- [ ] preview watched start to end with sound; changed timestamps listed for the client
- [ ] PROJECT.md status and next action updated; nothing delivered was overwritten

## References

- `references/troubleshooting.md`: symptom → cause → fix for render, font, GL, ffmpeg, Windows and disk problems
- `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md` sections A8, A9, G
