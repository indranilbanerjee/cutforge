# CutForge: agent context

This file is auto-loaded by OpenAI Codex, Google Antigravity, GitHub Copilot CLI, Cursor (when in the agent context
chain) and other Agent Skills runtimes. It is the equivalent of `CLAUDE.md` for non-Claude surfaces.

## What this plugin is

CutForge is an open-source video creation and editing plugin: from raw footage to final cut. It turns a client's
photos, clips, voice notes, documents and brand assets into a finished, verified, story-led video: family and milestone
films, tributes, weddings, brand films, explainers, ads, and pharma or BFSI videos with India-first compliance.
**13 skills · 4 reviewer agents · a tested engine of 48 tools (Remotion, ffmpeg, Python) · 0 hooks · 0 MCP servers.**

**Supported surfaces (v1.0.0):** Claude Code (CLI + IDE extensions), Anthropic Cowork, OpenAI Codex (CLI + IDE + App),
Cursor 2.5+, GitHub Copilot CLI, Google Antigravity 2.0 (CLI + IDE), Hermes Agent, OpenClaw, Grok (xAI Build CLI, native
`.grok-plugin/` pair).

## Core principles

1. **Real footage first; AI only where no camera was,** and never on real faces.
2. **Every time is derived, never typed.** `film/timeline.py` turns measured narration into every shot's length, so
   picture, captions and sound always agree.
3. **The project folder is the memory.** Facts, decisions, sources, spend and notes live in files, not in chat.
4. **Never guess identity.** People, objects, rituals, dates and quotes are verified, or asked in one batched round.
5. **Verify before saying done.** Stills, audio QC, frame counts and decode checks run before anyone watches.

## How to use it as an agent

1. **Start with the `cutforge` skill.** It routes the phases (brief, archive, story, look test, storyboard, voice,
   sound, art, build, QC, delivery, revisions) to the specialist skills.
2. **Scaffold a project** with `python <plugin>/engine/new_project.py <folder> --title "<title>" [--demo]`, then
   `npm install` and `python tools/setup_local.py` inside it. `<plugin>` is this repository's folder (Claude hosts set
   `${CLAUDE_PLUGIN_ROOT}` to it).
3. **Project tools run inside the project**: `python film/timeline.py`, `python tools/qc/stills.py <chapter>`,
   `bash tools/render/pipeline.sh <chapter>`, `python tools/mix/film_mix.py`, `bash tools/render/assemble.sh`. The
   project's own `CLAUDE.md` lists the full pipeline.
4. **Paid calls are gated.** Voice and AI-art tools refuse to run without a `GO_AHEAD.txt` in the project and stop at
   `config.budget_inr`; every paid call is logged to `spend.md`. Keys come from environment variables or a key file,
   never from the chat.

## Canonical entry points

| User intent | Run skill |
|---|---|
| "Make a film from our photos" / "where are we on the video" | `cutforge` |
| "What do you need from me for the video" | `video-brief` |
| "Go through our photos and find the best moments" | `media-archive` |
| "Write the story" / "it feels flat" | `story-design` |
| "It looks like a slideshow" / "storyboard" / "vertical version" | `storyboard-and-look` |
| "Choose a narrator" / "it says the name wrong" | `voice-and-narration` |
| "Add music" / "it stops abruptly" | `sound-design` |
| "Make the photo come alive" / "AI image for this scene" | `visuals-and-ai-art` |
| "Render the film" / "the render failed" | `render-and-assemble` |
| "Is the cut ready" | `video-qc` |
| "Here are my notes" | `revision-round` |
| "Export it for YouTube" / "put it on my PC" | `video-delivery` |
| "Make a reel for the launch" / "pharma explainer" | `marketing-video` |

## Files in this repo

- `skills/<name>/SKILL.md`: 13 Agent Skills, each with `references/` for detail.
- `agents/<name>.md`: 4 reviewer agents (`story-editor`, `film-qc-reviewer`, `compliance-reviewer`, `archive-scout`).
- `engine/new_project.py` + `engine/template/`: the project scaffold and every tool (render, mix, grade, QC, archive,
  VFX, voice, delivery). `engine/templates/`: the project memory files.
- `docs/lessons-learned.md`: every mistake from a real 20-minute production and the rule that prevents it.
- `docs/case-study.md`: that production, anonymised. `docs/compliance-and-licensing.md`: licences, platform specs and
  Indian ad compliance with sources. `docs/USER-GUIDE.md`: a walkthrough.

## Cross-platform notes

- **Skills are portable** across all supported surfaces (Agent Skills open standard).
- **Subagents are Claude-only** as `agents/*.md`; on other surfaces run the same checks by asking for an independent
  review with the agent file's instructions.
- The engine needs Node 18+, Python 3.10+ and ffmpeg on PATH. Windows: run `.sh` files in Git Bash and set
  `PYTHONUTF8=1`.

## Identity / authority

Built and maintained by Indranil Banerjee (https://indranil.in). MIT-licensed. No telemetry. Part of the Neelverse
plugin suite.
