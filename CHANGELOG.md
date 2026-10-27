# Changelog

All notable changes to CutForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-10-27

### Paid calls are quoted first, the speech models come from the registry, and the setup checks what it needs

From a review of CutForge against the guards the other three plugins in the suite carry (2026-10-27). Each fix below has a test that fails on 1.0.1.

**Changed: paid calls**

- A paid tool run without `--go` prints a quote and exits 4, spending nothing: `tools/voice/gen_vo.py`, `audition.py`, `import_vo.py --verify` and `tools/vfx/ai_gen.py`. The price comes from the new `tools/price_book.py`, which holds none: each price is recorded with the https page it was read from and expires after a week. A run with `--go` must also pass `--quoted-providers`, naming the providers in the quote; one that is not named never runs. The cap is checked per currency against `spend.md` (`budget_inr`, `budget_usd`). In 1.0.1 the estimate came from the caller (`ai_gen.py --inr 8`, an `inr_per_1k_chars` setting) and the only approval was a `GO_AHEAD.txt` that an agent can create; that file is no longer read, `--inr` is ignored with a note, and `inr_per_1k_chars` is gone.

**Changed: speech models**

- `tools/voice/tts.py` and `stt.py` took their model ids from literals. They now resolve `latest-tts-<vendor>` and `latest-stt-<vendor>` through `tools/resolve_model.py` and `tools/model_registry.json`, a copy of the suite's canonical registry (a sync from Digital Marketing Pro writes it). The resolver refuses a retired model, one past its shutdown date, a speech pin that has expired, and a model served at an endpoint the tool does not call; it warns on a deprecated model and on a registry not reviewed for 60 days.
- Sarvam transcription defaulted to `saarika:v2.5`, which the vendor's current reference no longer lists; it now sends the registry's model with `mode=transcribe`. OpenAI transcription defaulted to a model OpenAI shuts down on 2027-02-26.
- OpenAI speech: every `/v1/audio/speech` model shuts down on 2027-01-06 and the registry's replacement runs only on the Realtime API, which CutForge does not call. With no `model` in the voice settings the `openai` provider now refuses and says why; a `model` you name yourself still works, with a deprecation warning, until the shutdown.

**Changed: setup**

- `tools/setup_local.py` requires Node 22 or newer (18 and 20 are end of life), checks the ffmpeg version, checks that `node_modules` holds the Remotion version `package.json` pins, and prints the conditional Python 3.10 end-of-life note. The new `tools/install_deps.py` prints the exact pinned pip command for what is missing and installs only with `--install`; the unpinned `pip install` lines in the setup output and the archive and cut-out tools are gone.
- The four agent descriptions are one sentence each, with their examples moved into the agent body: always-on cost from about 2,212 tokens to about 825.

**Fixed**

- A Windows clone with `core.autocrlf=true` writes the `.sh` files with CRLF line ends, which bash rejects. `new_project.py` now writes them with LF whatever the checkout did, and `test_engine` checks that form with Git's bash (the bare name `bash` can resolve to Windows' WSL launcher, which made three shell-script checks fail on a machine without a WSL distribution).
- `new_project.py` refuses a target inside the plugin folder, where copying the template into itself would never end.
- Files a person may have written in Notepad or PowerShell 5.1 start with a byte-order mark: 23 reads in the engine (`config.json`, the key file, scripts and shot lists) and the two JSON reads in `render.mjs` now strip it. A key file with a mark used to hide its first key.
- `render/pipeline.sh` cleaned `/tmp/remotion-*`, which PowerShell resolves to `C:\tmp`; it uses the system temp folder. The skill's `new_project.py` command quotes the plugin path and the file carries the suite's script-location line.

**Added: tests (53 to 146)**

- `tests/test_paid_calls.py` (24): the price book, the gate (missing and stale price, no go, an unquoted provider, the cap, a legacy `GO_AHEAD.txt` that changes nothing), and the four paid tools from the command line.
- `tests/test_resolve_model.py` (17): each refusal, the exit-status contract and the request bodies the speech tools send, with the network replaced.
- `tests/test_suite_guards.py` (16): no model id or rate in code or skills, script-location lines and quoted plugin paths, no `/tmp`, byte-order-mark-safe reads, the listing budget for descriptions, no runtime file in the shipped template, and every host a tool contacts listed in `PRIVACY.md`. `tests/test_no_internal_references.py` (3) keeps session labels and private paths out of shipped files. `tests/test_new_project_safety.py` (4): a target inside the plugin is refused, and a project's shell scripts have LF line ends even when planted from a CRLF checkout. `tests/test_directory_readiness.py` (28) runs the Claude plugin directory's file-level rules on the repository (no system files, valid names, size and type limits, a complete icon, https listing URLs, no launcher, credential or machine path, no unpinned `pip install`), each planted on a synthetic tree; `claude plugin validate --strict --profile directory` passes. `test_counts` also checks the README test badge.

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
