---
name: cutforge
description: "Run the CutForge method end to end, brief to final cut, for any story-led video. \"make a film from our photos\""
user-invocable: true
---

# CutForge: make a story-led video, end to end

> **Script location.** If your host does not set `${CLAUDE_PLUGIN_ROOT}`, the plugin folder is the one that contains `skills/`
> (two levels above this file): the engine is in `engine/`, the docs in `docs/`. Run Python 3.10 or newer: `python`, or
> `python3` where `python` is not found (macOS, many Linux systems).

CutForge turns a client's material (photos, clips, documents, voice notes, brand assets) into a finished film:
real footage first, AI only where no camera was, narration in a chosen voice, a designed soundtrack, rendered
with code (Remotion + ffmpeg + Python) so any change is a re-run, not a re-edit. The method and every rule here
come from a real 20-minute production and its mistakes: read `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md`
once per project, and `${CLAUDE_PLUGIN_ROOT}/docs/case-study.md` for how it played out.

## Non-negotiables (every project)

1. **The project folder is the memory.** Every decision, fact, correction and constraint goes into a file the
   moment it is made (PROJECT.md, facts.md, decisions.md, sources.md, spend.md, NOTES_vN.md). Write as if the
   next session, model or machine knows nothing. Chat is not storage.
2. **Never guess identity.** People, objects, places, rituals, relations, dates and quotes are verified or asked
   in one batched round (the photo map). Face clustering sorts; only the client names people.
3. **No AI on real faces.** No generative motion, edits or invented faces on real people, children above all.
   Generate only what no camera captured; composite real people over generated backgrounds untouched.
4. **Quote gate.** Agree a cap, then run each paid tool WITHOUT `--go`: it prints the quote (a price you read on
   the provider's page and recorded with `tools/price_book.py`) and exits 4, spending nothing. Show the client that
   quote, and only after their typed go run the same command with `--go --quoted-providers <the quoted providers>`.
   Every paid call is logged in spend.md; stop at the cap and report.
5. **Never delete or overwrite the client's files.** Work on copies; add new files in a dedicated folder.
6. **Keys stay in files or env vars.** Never print, paste or commit a key. `tools/keys.py` reads them.
7. **Show, don't describe.** A 30-60 s look test of the hardest scene comes before the full script. Stills
   before renders. Short previews before masters.
8. **No abrupt stops.** Every shot breathes after its last line, every sound fades, chapters bridge with sound.
   The timeline and audio QC tools flag violations; fix every flag or record why it is intended.
9. **Verify before saying done.** Frame counts, decode check, loudness, stills looked at, facts re-checked.
10. **Sensitive chapters are decided by the people they belong to.** Propose the gentlest treatment; no medical,
    legal or financial detail; record the decision.
11. **One version** unless asked for more. No studio idents, logos or self-promotion in a personal film.
12. **Design for the slowest link.** Portable project (config.json, no hard-coded paths, Windows-safe), chapters
    rendered separately, transfers in verified parts.

## Phases, gates and the skill for each

| # | Phase | Output (in the project folder) | Gate before moving on | Skill |
|---|---|---|---|---|
| 0 | Set up | project from the engine template, PROJECT.md | folder exists, setup_local passes | this skill |
| 1 | Brief | brief.md, PROJECT.md filled, facts.md seeded, inbox/ | client confirms the one-screen brief | `video-brief` |
| 2 | Material | inventory, stats, contact sheets, clip strips, sound events, face clusters, candidate moments | library understood; gaps listed | `media-archive` |
| 3 | Story | treatment.md, story-order table, plant/payoff list, script.json draft | client approves treatment; story-editor agent pass | `story-design` |
| 4 | Look test | 30-60 s render of the hardest scene | client reacts ("yes, this level") | `storyboard-and-look` |
| 5 | Script + storyboard | shots.json, script.json final, photo map page | client ticks the photo map (one round) | `storyboard-and-look` |
| 6 | Voice | audition page → chosen voice → sound/vo/*.wav verified | every line STT-verified | `voice-and-narration` |
| 7 | Art + sound | AI plates (budget-gated), cues.py, client recordings | licences logged; spend under cap | `visuals-and-ai-art`, `sound-design` |
| 8 | Build | timeline → stills → chapters → mix → assemble | verify.py OK; qc flags fixed | `render-and-assemble` |
| 9 | QC | QC report; independent reviewer pass | no open ERROR; device test done | `video-qc` |
| 10 | Delivery | master + previews on the client's machine; project hand-off | md5 verified on the far side | `video-delivery` |
| 11 | Revisions | NOTES_vN.md → minimal re-render → v(N+1) | every note mapped, fixed, re-checked | `revision-round` |

Marketing, brand, ads and regulated verticals (pharma, BFSI): also follow `marketing-video` from phase 1.
No archive (an explainer from screens and graphics, an ad from a shoot): skip phase 2; the phase 5 gate becomes
the client's storyboard sign-off instead of the photo map.

Independent agents (they did not build the work, so they catch what the builder cannot):
`archive-scout` (phase 2, big libraries), `story-editor` (after the treatment, the script and any late
insertion), `film-qc-reviewer` (first full cut, final, after splices), `compliance-reviewer` (any public, client
or regulated release). The client-facing review page for phases 5 and 11 is `python tools/qc/storyboard.py`.

## Start a project (phase 0)

```bash
python "${CLAUDE_PLUGIN_ROOT}/engine/new_project.py" "<folder>" --title "<title>" --format landscape|vertical|square \
       --lang bn-IN --budget 400 --target-minutes 15 [--keys "<path to key file>"] [--demo]
cd "<folder>" && npm install && python tools/setup_local.py
```
`--demo` scaffolds a 1-minute demo film with procedural media; render it once on a new machine to prove the
toolchain before touching client material. The template's own `CLAUDE.md` lists the pipeline commands.
Put the project where the big files belong (a data drive, not a nearly full system drive). Record the client's
folders in `config.json` "folders"; never copy a whole archive into the project, only what the film uses.

## How to run each working session

1. Read PROJECT.md, facts.md, decisions.md and the latest NOTES_vN.md before doing anything.
2. Say in one sentence what this session will do; set up a task list when there are more than a couple of steps.
3. Work in the smallest verifiable unit: one shot's stills, one chapter, one mix. Look at outputs (Read the jpgs,
   run the QC scripts) before reporting.
4. Update PROJECT.md "Status" and "Next action" before stopping. Log decisions as they happen.
5. Report to the client in short, plain sentences with film timestamps ("8:26, the family page"), what changed,
   what was checked and how, and the one question that blocks the next step (if any).

## When to ask, when to proceed

- Ask (batched, once) about: identities, relations and what the hero calls people; dates and places that are
  not in metadata; sensitive periods; anything that costs money; the delivery device; red lines.
- Proceed without asking on: craft choices (layout, transitions, sound design), technical approach, fixes
  flagged by QC, anything cheap to redo. Show the result and let the client react.
- Working unattended: take the most reasonable reading, write it at the top of PROJECT.md "Status", continue;
  stop before anything irreversible or paid beyond the agreed cap.

## Time and compute reality

- Render cost dominates: a 2-CPU cloud box rendered ~20 min of 1080p film in 5-6 h (chunked, CONC=2); an
  8-core desktop with GPU is 3-5x faster. Budget renders, never re-render the whole film for one fix.
- Cloud workspaces can be reclaimed when idle: use the chunked, resumable pipeline, keep a watcher alive during
  long renders, and keep the project portable so it can move to the client's machine (see `video-delivery`).
- Back-plan from the event date; lock everything only the client can give (recordings, letters, identity
  answers, photos from other phones) well before the build.

## References

- `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md`: every mistake from a real production and the rule that prevents it
- `${CLAUDE_PLUGIN_ROOT}/docs/case-study.md`: the production, anonymised, phase by phase
- `${CLAUDE_PLUGIN_ROOT}/docs/compliance-and-licensing.md`: tool licences, platform specs, Indian ad compliance
- `${CLAUDE_PLUGIN_ROOT}/engine/`: the project template and all tools (render, mix, grade, QC, archive, VFX, delivery)
- `references/project-files.md`: what each project file holds and who updates it
