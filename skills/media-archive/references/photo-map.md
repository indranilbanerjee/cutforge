# The photo map (one review round for every fact on screen)

Purpose: replace twenty scattered questions with one page the client can go through in fifteen minutes, before
the expensive build. Every asset the film uses appears once, with what we believe; the client ticks or corrects.

Format (an artifact page, a sheet, or a PDF contact sheet with numbered tiles):

| # | Thumbnail | Shot | Caption / line over it | Who is in it (our belief) | Date (source) | Question |
|---|---|---|---|---|---|---|
| 12 | (tile) | e2/7D | "the family page" | grandfather, grandmother (cluster 0, 3) | 2022-03-08 (EXIF) | (none) |
| 13 | (tile) | e3/9C | "the first sea" | child, mother, a man in the water? | 2025-02-11 (EXIF) | Is the man in the water the father? |

`python tools/qc/storyboard.py` generates this page from the project data (shot, film time, narration, every
asset with its capture date and the people labelled for it, "?" where unconfirmed) with an editable note column.

Rules
- Group by chapter, in film order, so the client also sees the chronology.
- Mark every belief that is not confirmed with "?"; never present a guess as a fact.
- Put every open question in the same round: unknown faces (with crops), undated files, missing people
  ("we have no photo of X: is there one?"), spellings, what the family calls a ceremony.
- After the round: update facts.md (with "confirmed by <client>, <date>"), decisions.md for corrections,
  film/face_labels.json, and re-run tools/qc/qc_story.py (chronology, cast, reuse).
- If a late photo arrives, it gets a row too; late placements are the commonest source of "things not in the
  right place".
