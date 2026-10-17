# Pull Request

## Summary

<!-- One or two sentences describing the change and why it is needed. -->

## Type of change

- [ ] Bug fix (wrong skill guidance, tool crash, broken render, mix or install)
- [ ] New skill, agent, layout or tool
- [ ] Platform, provider or compliance update (spec, model, regulation)
- [ ] Documentation only
- [ ] Repository hygiene (tests, templates, refactor)
- [ ] Other (explain):

## Which surface(s) are affected

- [ ] Claude Code / Cowork (`.claude-plugin/plugin.json`)
- [ ] OpenAI Codex (`.codex-plugin/plugin.json`)
- [ ] Cursor 2.5+ (`.cursor-plugin/plugin.json`)
- [ ] GitHub Copilot CLI (`.github/plugin/plugin.json`)
- [ ] Google Antigravity 2.0 (`gemini-extension.json`)
- [ ] Hermes Agent (`plugin.yaml` + `__init__.py`)
- [ ] OpenClaw (`openclaw.plugin.json` + `package.json`)
- [ ] Grok (`.grok-plugin/`)
- [ ] The engine (`engine/`), on every surface

## Checklist

- [ ] I read [`CONTRIBUTING.md`](../CONTRIBUTING.md) and the [Code of Conduct](../CODE_OF_CONDUCT.md)
- [ ] `python tests/run_all.py` passes
- [ ] For engine changes: the demo project renders, mixes, assembles and verifies
- [ ] Skill text matches the engine code (commands, flags, paths, defaults)
- [ ] For a release: the version is bumped in every manifest, the README badge and lede, and CHANGELOG.md
- [ ] No identifying detail from the real production, no API key, no client media in the diff

## Compliance or licence source (only if a rule or licence changes)

<!-- Link the primary source (regulation text, regulator circular, licence page). Blog posts are not acceptable. -->

## Testing notes

<!-- How you verified the change: the prompt you tried, the render you checked, the source you compared. -->
