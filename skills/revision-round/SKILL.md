---
name: revision-round
description: "Turn client notes into a revision round: map, decode, fix minimally, report with timestamps. \"here are my notes on the video\""
user-invocable: true
---

# Revision round: every note mapped, fixed, re-checked, and reported with timestamps

Client notes arrive as voice notes, chat lines, timestamps, screenshots or one vague sentence ("abrupt stops in
many places"). Treat each as a precise bug report: find where it is, what mechanism causes it, and what the
smallest correct fix is. Never re-render the whole film for a list of local fixes.

## Workflow

1. **Capture every note** in `NOTES_vN.md` (template in the project) exactly as given, one row each:
   `| # | At | Note (client's words) | Shot | Class | Fix | Done |`. Split compound notes. Keep the client's
   words; your interpretation goes in Fix.
2. **Locate**: `python tools/qc/where.py 8:26 12:03 ...` maps film times to chapter, shot, the line being
   spoken and the media on screen. Times from the client may refer to a preview of an older version: check
   which file they watched.
3. **Classify** each note: fact (identity, name, date, relation, ritual), story (order, missing beat, tone,
   balance), picture (layout, timing, text), sound (abrupt, level, music), voice (pronunciation, delivery),
   technical (playback, file). Facts first: they are the most damaging and the cheapest to fix.
4. **Decode vague notes** into mechanisms (`references/feedback-decoder.md`): "abrupt" → tails, fades,
   bridges, fixed shots; "not in the right place" → chronology table, late insertions; "primitive" → engine,
   sound sources, motion design; "slideshow" → framing and transitions. Run the matching QC tool to find every
   instance, not only the one the client noticed.
5. **Ask only what cannot be resolved**: batch the remaining questions (one round) with stills of the shots in
   question. Do not ask what the data answers.
6. **Plan the smallest rebuild**: list the chapters touched, which narration lines regenerate, which cues
   change. Order: facts.md/decisions.md → script.json → `gen_vo.py <ids>` → `film/timeline.py` → shots.json /
   custom chapters → stills of changed shots → `FRESH=1 pipeline.sh <changed chapters>` → `film_mix.py
   <changed chapters>` (plus the chapter where any long cue starts; chapters that moved are re-mixed
   automatically) → `VER=v(N+1) assemble.sh` → QC.
7. **Fix the class, not just the instance.** When one name tag was wrong, re-check every name tag; when one
   chapter end had dead air, run qc_audio over the whole film.
8. **Verify** with the `video-qc` layers for the changed chapters plus the full-film checks (verify --final,
   qc_audio, qc_story). Mark each NOTES row Done only after its fix is seen in a still or heard in the mix.
9. **Report back** in short plain sentences: what changed, with new timestamps ("8:26 the family page now names
   Grandpa"), what was checked and how, anything not done and why, and the one question still open. Send the new
   preview and, when useful, the storyboard page for the changed shots.

## Rules

- A late insertion (a new photo, a new beat) re-runs the story-order table and the story editor re-reads the
  whole chapter, not only the new shot.
- Never overwrite the delivered version: a new `VER` per round; keep `NOTES_vN.md` for every round.
- A note that conflicts with an earlier decision is raised with the client, quoting the decision, not silently
  applied.
- Record every changed fact with its source in facts.md, every changed choice in decisions.md.
- If the notes are for a project that has moved to the client's machine, work in that copy (config.json
  folders), and follow the same order.

## References

- `references/feedback-decoder.md`: what clients say → the mechanism → where to look → the fix
- `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md` sections C7, E2, I5
