---
name: video-qc
description: "QC a video before anyone sees it: timing, story, stills, audio, frames and device. \"is the cut ready\""
user-invocable: true
---

# Video QC: verify before saying done

"Done" means checked, not rendered. Most of what clients noticed in a real production was detectable from data
before anyone watched: wrong people, chronology, a missing relative, abrupt stops, a line running past its shot.
Run the checks below in order; each is cheap compared to a client finding it.

## The layers

| # | Layer | Tool / method | Blocks delivery when |
|---|---|---|---|
| 1 | Timing | `python film/timeline.py` | any ERROR; unexplained WARN |
| 2 | Story data | `python tools/qc/qc_story.py` (CHRONOLOGY, CAST, REUSE, RUNTIME) | an asset outside its chapter span, a person the hero names with zero screen time, an unintended reuse, runtime > 5 % off |
| 3 | Facts | facts.md vs every caption, name tag, date note, stamp; sources.md for every quote | any unverified identity, date, ritual name or quote on screen |
| 4 | Picture | `python tools/qc/stills.py <chapter> --safe 0.86` and Read every sheet | text or faces outside the safe area, captions < 1/20 height, collisions, wrong person, misspelling, broken conjuncts |
| 5 | Sound | `python tools/qc/qc_audio.py`; mixer speech-over-bed report | DROP, CUT TAIL, DEAD AIR, loudness > 1 LU off target, narration buried |
| 6 | Render | `python tools/qc/verify.py --decode`; `verify.py --final <master>` | frame mismatch, decode errors, duration off |
| 7 | Watch-through | the 540p preview end to end, with sound, at speed | anything that makes you wince; note it with a timestamp |
| 8 | Device | the delivery device in its room (projector, TV, phone with platform UI) | unreadable text, cropped edges, inaudible narration, file will not play |
| 9 | Independent review | `film-qc-reviewer` agent (and `story-editor`, `compliance-reviewer` for brand/regulated work) | any ERROR they confirm |

Run 1-6 on every build; 7 on every cut shown to anyone; 8 before the first screening and the final; 9 on the
first full cut, the final, and any regulated deliverable. The reviewer must not be the one who built the cut:
it gets the files, not the build history.

## What to look for in stills (the sheet labels each frame with film time and shot)

- Every face that is named: is it that person (facts.md, people map)? Background faces are never named.
- Text: spelling in the language, complex-script conjuncts intact, no letter-spacing on Indic text, contrast.
- Safe area box: faces and words inside. Vertical: nothing important under platform UI.
- Collisions: prints over name tags, stamps over faces, captions over prints.
- Continuity: the hero object is the right one in every shot; costumes and places match the date.
- Page turns and transitions: no blank page, no flash frame, no black gap.

## How to listen

- Headphones for clicks, cuts and dead air; then the delivery speaker for balance.
- Every chapter boundary: is there a bridge? Every emotional line: is there a breath after it?
- Every name spoken: pronounced as the family says it?
- Music: unbroken inside a chapter, cuts on beats, no swell under words.

## The QC report (what the client or the next session reads)

```
QC v2 · 2026-10-16 · film 19:58 · checks 1-8 run, reviewer pass done
ERROR  8:26  e2/7D  name tag says "Grandad" over the grandfather the hero calls "Grandpa"   fix: facts.md + shots.json
ERROR 10:42  e2→interval  2.5 s dead air, then a sound cut 0.3 s in                  fix: bell ring-out + pre-lap
WARN   0:12  open/title  line runs 0.44 s past the fixed title shot                 fix: fixed 5.99 → 6.6
NOTE  12:39  e3/9H  print lands under the caption band for 0.5 s                     fix: printAt 0.6
```
Severity: ERROR blocks delivery; WARN is fixed or recorded as intended in decisions.md; NOTE is optional.
Write the report to `out/qc/QC_vN.md`; fixes become NOTES_vN rows (see `revision-round`).

## References

- `references/qc-checklist.md`: the full pre-delivery checklist, by layer, with tick boxes
- agents: `film-qc-reviewer`, `story-editor`, `compliance-reviewer` (in this plugin's agents/)
