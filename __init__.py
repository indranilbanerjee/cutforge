"""
Hermes Agent native plugin adapter for CutForge.

This file is read ONLY by Hermes Agent (Nous Research). Every other platform
ignores it: Claude Code / Cowork / Codex / Cursor / Copilot CLI / Antigravity
all read their own manifest files. OpenClaw reads openclaw.plugin.json (and
falls back to the .claude-plugin/ bundle).

When Hermes loads us via `hermes plugins install indranilbanerjee/cutforge`,
it clones the repo into ~/.hermes/plugins/cutforge/, reads plugin.yaml at
the root, then calls register(ctx) below. The register() walks the skills/
directory and exposes each one to Hermes via ctx.register_skill().

Defensive coding throughout — stdlib only, no third-party Python dependencies;
if Hermes API surface differs from the documented spec, the adapter logs and
degrades gracefully rather than crashing.

Spec source: https://hermes-agent.nousresearch.com/docs/guides/build-a-hermes-plugin
Tested against: Hermes Desktop v0.15.2 (June 2026 public preview)
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger("cutforge")

PLUGIN_ROOT = Path(__file__).resolve().parent
SKILLS_DIR = PLUGIN_ROOT / "skills"
PLUGIN_VERSION = "1.1.2"


def _parse_skill_frontmatter(skill_md_path: Path) -> dict:
    try:
        text = skill_md_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.debug("could not read %s: %s", skill_md_path, exc)
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    fm_text = match.group(1)

    fields: dict = {}
    for key in ("name", "description"):
        m = re.search(rf"^{key}:[ \t]*(.*)$", fm_text, re.MULTILINE)
        if not m:
            continue
        value = m.group(1).strip()
        if value in (">", "|", ">-", "|-"):
            # folded or literal block scalar: the indented lines that follow
            block = re.match(r"((?:[ \t]+\S.*\n?)+)", fm_text[m.end() + 1:])
            value = " ".join(line.strip() for line in block.group(1).splitlines()) if block else ""
        elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1].replace('\\"', '"')
        fields[key] = value.strip()
    return fields


def _walk_skills() -> list[dict]:
    discovered: list[dict] = []
    if not SKILLS_DIR.exists():
        logger.warning("skills/ directory not found at %s", SKILLS_DIR)
        return discovered
    for entry in sorted(SKILLS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            continue
        meta = _parse_skill_frontmatter(skill_md)
        discovered.append({
            "dir_name": entry.name,
            "name": meta.get("name") or entry.name,
            "description": meta.get("description") or "",
            "skill_md_path": skill_md,
        })
    return discovered


def register(ctx) -> None:
    logger.info("cutforge v%s registering with Hermes", PLUGIN_VERSION)
    skills = _walk_skills()
    if not skills:
        logger.warning(
            "cutforge found 0 skills in %s — plugin will be inert. "
            "Confirm the plugin was cloned with its full skills/ tree.",
            SKILLS_DIR,
        )
        return
    if not hasattr(ctx, "register_skill"):
        logger.error(
            "cutforge: Hermes ctx is missing register_skill(). "
            "Check Hermes version (targets v0.15.2+). Plugin will be inert. "
            "Found %d skills that could not be registered.",
            len(skills),
        )
        return
    registered = failed = 0
    for skill in skills:
        try:
            ctx.register_skill(skill["name"], skill["skill_md_path"])
            registered += 1
        except Exception as exc:  # pragma: no cover
            failed += 1
            logger.warning("cutforge: failed to register %r: %s", skill["name"], exc)
    logger.info(
        "cutforge v%s: registered %d skills (failed: %d) under namespace 'cutforge:'.",
        PLUGIN_VERSION, registered, failed,
    )


def audit() -> dict:
    skills = _walk_skills()
    return {
        "plugin_root": str(PLUGIN_ROOT),
        "plugin_version": PLUGIN_VERSION,
        "skills_dir": str(SKILLS_DIR),
        "skills_dir_exists": SKILLS_DIR.exists(),
        "skill_count": len(skills),
        "first_5_skills": [
            {"name": s["name"], "description": s["description"][:80]}
            for s in skills[:5]
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
