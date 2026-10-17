# Changelog

All notable changes to CutForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-10-17

### Clean install on Hermes Agent

**Fixed**

- `engine/template/tools/voice/gen_vo.py` held two invisible joiner characters (U+200C, U+200D) in its source.
  Hermes Agent's install-time security scanner reads invisible characters in a shipped file as hidden text and can
  refuse the plugin. They are now written as escape codes; the behaviour is unchanged.

**Added**

- `tests/test_host_scanner_compat.py`: every shipped text file is checked against the install-scanner patterns the
  rest of the suite already guards (destructive home-folder deletes, instructions to hide things from the user,
  uploads to a URL, echo piped into an interpreter, invisible characters). 53 tests.

---

## [1.0.0] - 2026-10-17

### The first public release: from raw footage to final cut

CutForge turns a client's photos, clips, voice notes, documents and brand assets into a finished, verified, story-led
video, and was distilled from a real 20-minute production built end to end by Claude.

**Added**

- **13 skills:** `cutforge` (the orchestrator), `video-brief`, `media-archive`, `story-design`,
  `storyboard-and-look`, `voice-and-narration`, `sound-design`, `visuals-and-ai-art`, `render-and-assemble`,
  `video-qc`, `revision-round`, `video-delivery` and `marketing-video`, each with references. Descriptions follow the
  60-150 character routing rule so they fit Claude Code's shared skill listing.
- **4 reviewer agents:** `story-editor`, `film-qc-reviewer`, `compliance-reviewer` and `archive-scout`.
- **The engine:** `engine/new_project.py` and a Remotion 4 + Python project template with 48 tools: the derived
  timeline, `AutoChapter` layouts, chunked resumable renders, an ffmpeg grade, a Python mixer with ducking, minimum
  fade-outs and two-pass loudness, voice generation with speech-to-text verification, recorded-take import, archive
  inventory, stats, contact sheets, clip strips, real-sound events, face clusters and semantic search, depth parallax,
  cut-outs, straightening, a budget-gated AI generator with a face guard, a beat finder, a storyboard and photo-map
  page with saved notes, QC stills, audio and story checks, encode presets and verified transfers.
- **Docs:** a lessons ledger from the real production, an anonymised case study, a licensing and India-first
  compliance reference with sources, and a user guide.
- **Manifests for 9 surfaces:** Claude Code, Cowork, Codex, Cursor, Copilot CLI, Antigravity, Hermes Agent (native
  adapter), OpenClaw and Grok.
- **A stdlib test suite** covering manifest agreement, skill routing rules, references, counts, anonymity, the Hermes
  adapter and the engine's timing, mixing and beat logic, plus trigger evals for every skill.

**Fixed before release** (found by an independent review)

- Re-mixing one chapter could desync every later chapter after a timing change: the mixer now records each stem's
  start and length and re-mixes any chapter that moved.
- The `portrait` layout used a blurred background, which the skills forbid: it now sits on the paper page or black.
- A long music cue was cut off 14 s after its chapter ended: the chapter's mix window now widens to fit it.
- Captions were too small on vertical and square frames, and name tags and prints ran into the platform UI zone on
  vertical: captions are at least 1/20 of the frame height in every format, and vertical defaults stay in the
  platform-safe band, which the still sheets now draw.
- Speech-to-text failures were reported as "all verified": a run now lists CHECK and UNVERIFIED lines separately and
  picks a sensible speech-to-text provider for the language.
- Encodes used one-pass loudness: every preset now measures first and limits true peak.
