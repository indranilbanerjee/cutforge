# Contributing to CutForge

Thank you for your interest in improving CutForge. Contributions that make films better, safer or easier to make are
welcome: new layouts, voice providers, Indic and other complex-script typography, platform specs, delivery presets,
compliance rules with primary sources, and lessons from your own productions.

## Code of Conduct

Everyone is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting bugs

1. Check the existing [issues](https://github.com/indranilbanerjee/cutforge/issues) first.
2. Open a new issue with what happened, what you expected, steps to reproduce, your host (Claude Code, Cowork, Codex,
   Cursor, ...), OS, Node and Python versions, and the full error text (not a screenshot).
3. For a render or mix problem, attach the relevant log (`out/ch/<chapter>.log`, `out/ch/queue.log`) and the output
   of `python tools/setup_local.py`.

## Pull requests

1. Fork the repository and create a branch: `git checkout -b feature/your-feature`.
2. Make the change, following the standards below.
3. Run the test suite: `python tests/run_all.py` (stdlib only; engine tests skip cleanly when numpy or ffmpeg are
   missing).
4. For engine changes, scaffold the demo and render it: `python engine/new_project.py "<a new folder outside this repository>" --title Demo --demo`,
   then follow the README Quick Start inside it.
5. Open the PR with a clear description and the PR checklist filled in.

## Standards

### Skills
- A `description` of 60-150 characters: `<Verb> <object> <scope>. "<one phrase a user types>"`. It is the routing text
  in a shared listing budget, so longer is not better. Each quoted phrase belongs to one skill.
- The body is instructions for the agent, in the imperative, under 3,000 words; detail goes into `references/`.
- Every command, flag, path and default a skill states must match the engine code. The tests check paths and
  references; a reviewer checks behaviour.

### Engine
- Python 3.10+, no hard-coded paths (use `tools/paths.py` and `config.json`), `encoding='utf-8'` on every file read
  and write, `-nostdin` on every ffmpeg call, Windows-safe (no drive-letter colons in ffmpeg filter graphs).
- Never delete or overwrite a client's file. Paid calls go through `tools/spend.py` (`gate()` before, `log()` after).
- Keys come from `tools/keys.py`; never print or log one.

### The rules a change must not weaken
- No AI on real faces. The face guard stays on by default.
- Every time on the timeline is derived from measured narration, never typed.
- No abrupt stops: the minimum fade-outs and the timing and audio checks stay.
- Nothing identifying about the real production behind the case study enters the repository.

## Releases

A release bumps the version in every manifest (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`,
`.cursor-plugin/plugin.json`, `.github/plugin/plugin.json`, `.grok-plugin/plugin.json`, `.grok-plugin/marketplace.json`,
`gemini-extension.json`, `openclaw.plugin.json`, `plugin.json`, `plugin.yaml`, `package.json`, `__init__.py`), the
README badge and lede, and adds a CHANGELOG entry. `tests/test_manifests.py` fails if any of them disagree.

By contributing you confirm you have the right to contribute the content under the MIT license, and that any
AI-generated portions were reviewed by you before submission.
