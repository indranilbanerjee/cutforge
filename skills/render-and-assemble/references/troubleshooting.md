# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `timeline.py` exit 2: narration longer than fixed shot | a `fixed` shot shorter than its measured line (a real v7 bug: the title line ran 0.44 s past its shot) | raise `fixed`, or drop `fixed` and use `min`; re-run |
| WARN short tail < 0.6 s | `post` too small; a line ends as the shot cuts | raise `post` (1.5-2.5 s after emotion) or set `"hardcut": true` if intended |
| Caption appears after the shot ended | a label timed to an assumed duration | anchor to `voEnd(k)` in custom chapters; never hand-type seconds |
| Bengali/Indic conjunct broken in a title | subset font, or letter-spacing on Indic text | full font file; no `letterSpacing`; shape with `tools/text/shapeall.sh`; check a still |
| Two letters too far apart in a shaped title | display font kerning | `tools/text/kern.json` shift for that glyph index; re-run `kern.py` |
| Remotion: "browser not found" / download blocked | no Chrome Headless Shell on the machine or proxy blocks the download | set `browser_executable` in config.json (an installed Chrome/Chromium) or `REMOTION_BROWSER` |
| Remotion GL errors, black frames, very slow | wrong GL backend | Windows/macOS `angle`; headless Linux `swiftshader`; set `gl` in config.json or `REMOTION_GL` |
| `delayRender` timeout | huge media decode, a font not found, a network asset | downscale media (max side 2880), keep fonts local in `public/fonts`, no remote URLs |
| A clip plays sideways | rotation metadata ignored | probe rotation (inventory.csv); transpose on import |
| Render stops mid-way | box reclaimed, OOM, a chunk crashed | re-run the same command: finished chunks are skipped; lower `CONC` if OOM |
| Changed code but the render looks old | old chunks reused | `FRESH=1` for that chapter |
| Frame count mismatch in verify.py | partial chunk, a splice off a keyframe | delete that chapter's chunks (`FRESH=1`) and re-render |
| Final film audio drifts or ends early | mix shorter/longer than picture | re-run film_mix after the last timeline change; assemble uses `-shortest`, check verify `--final` |
| ffmpeg filter error with a `D:` path (Windows) | the colon in the drive letter breaks the filter parser | run ffmpeg with cwd at the file (grade.py does this for LUTs) |
| `UnicodeEncodeError` / mojibake (Windows) | cp1252 default encoding | `setx PYTHONUTF8 1`, new terminal; all tools write `encoding='utf-8'` |
| `python3` opens the Microsoft Store (Windows) | Store stub | scripts fall back to `python`; or set `PY=python` |
| Windows render slow to start | Remotion copies `public/` into the bundle (no symlinks on Windows) | normal; keep `public/` to what the film uses |
| ffmpeg inside a shell loop eats input | ffmpeg reads stdin | always `-nostdin` (all tools do) |
| `pgrep -f` finds itself / kills the wrong job | pattern matches the pgrep command | use a pid file or a more specific pattern |
| "No space left on device" | chunks, parts and bundles pile up | delete chunks after concat, transfer parts after verify, `/tmp/remotion-*`; keep graded chapters only |
| Model download fails (GitHub raw blocked) | proxy rules | `tools/fetch_models.py` uses media.githubusercontent.com and Hugging Face URLs, verified by md5 |
| OpenCV Haar cascade missing | new wheels drop data files | the tools use YuNet (downloaded model), not Haar |
| Upload to an AI host fails with SSL EOF | input too large | downscale to max side ~2048 and retry |
| Paid tool refuses to run | no `GO_AHEAD.txt` or cap reached | that is the budget gate working: ask the client, then create the file / raise the cap in config |
| Audio QC: DEAD AIR at a chapter end | silence between a sound ending and the next chapter | add a ring-out or pre-lap; room tone must be on |
| Audio QC: CUT TAIL after a cut | a cue's fade-out shorter than the minimum, or `hard=True` | remove `hard=True`, lengthen `fo` |
| Audio early or late in later chapters after a fix | stems mixed against an old timeline | film_mix re-mixes chapters whose start/length moved; if in doubt run `film_mix.py` with no args |
| Loudness 3-4 LU under target | one-pass normalisation on dynamic material | the mixer uses two-pass loudnorm; re-run the mix |
