# Security Policy

## Supported Versions

The latest minor release of CutForge receives security fixes. Please update before reporting.

| Version | Supported |
|---------|-----------|
| 1.1.x   | ✅ |
| 1.0.x   | ⚠️ Security fixes only when trivially backportable |
| < 1.0   | ❌ Please upgrade |

## Reporting a Vulnerability

**Do NOT open a public GitHub Issue for security vulnerabilities.** Public issues expose users before a fix exists.

Use GitHub's [Private Security Advisory](https://github.com/indranilbanerjee/cutforge/security/advisories/new) to
report privately. If you cannot, contact the maintainer through the email listed on [indranil.in](https://indranil.in)
with the subject line `[CutForge Security]`.

Please include: a description and its impact, steps to reproduce, the affected version and surface (Claude Code,
Cowork, Codex, Cursor, Copilot CLI, Antigravity, Hermes Agent, OpenClaw or Grok), a suggested fix if you have one, and
whether you would like credit.

What you can expect: acknowledgement within 48 hours, an initial assessment within 7 days, coordinated disclosure,
and credit in the advisory unless you prefer otherwise. There is no bug bounty: this is an open-source project
maintained by an individual, and responsible disclosure is deeply appreciated.

## Scope

In scope:
- The plugin itself: skills, agents, manifests and the Hermes adapter
- The engine in `engine/` (any path traversal, command injection or unsafe deserialization in the Python, shell or
  Node tools, including what a scaffolded project runs)
- The quote gate (`tools/spend.py`, `tools/price_book.py`) and the face guard (`tools/vfx/ai_gen.py`): a way to bypass either is in scope

Out of scope:
- Vulnerabilities in Claude Code, Cowork or other hosts (report to their vendors)
- Vulnerabilities in Remotion, ffmpeg, Chromium or upstream Python packages (report upstream, and tell us so we can
  pin a fixed version)
- Third-party provider APIs (Sarvam, ElevenLabs, OpenAI, WaveSpeed)
- Reports from automated scanners without proof of exploitability

## Hardening recommendations for operators

1. **Keep API keys out of projects you share.** Tools read keys from environment variables or the key file named in a
   project's `config.json`; keep that file outside the project folder and never commit it.
2. **Treat client material as personal data.** Projects hold family photos, children's faces, voices and documents.
   Apply the folder permissions you would to any client PII, and delete working copies when the job ends.
3. **Keep the quote gate on.** Run a paid tool with `--go` only after the client approves its quote, and keep `budget_inr` set.
4. **Review skill and tool changes in PRs** like production code: skills run with whatever permissions your host has.
5. **Pin the plugin version** for client work and update between jobs, not during one.
