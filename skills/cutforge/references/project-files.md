# Project files: what each holds

| File / folder | Holds | Updated when |
|---|---|---|
| `PROJECT.md` | status, one-screen brief, hard rules (client's words), where things are, known-and-accepted issues | every session start/end; every decision that changes scope |
| `brief.md` | the full brief from the intake (see video-brief) | phase 1, then only on scope changes |
| `facts.md` | verified facts: people map, hero objects, dates, spellings and pronunciations, sensitive periods, open questions | the moment a fact is confirmed or corrected |
| `decisions.md` | dated one-line decisions and corrections ("not X, it is Y") | as they happen |
| `treatment.md` | logline, frame, structure, arcs, spine, motifs, plant-payoffs, beat map, key lines | phase 3; after structural notes |
| `story_order.md` | the evidence table: beat, shot, asset, capture date, people, place | phase 3; after every insertion |
| `claims.md` | marketing claims with substantiation and approver (marketing-video) | script work; before release |
| `sources.md` | every quote, track, effect, stock clip, font, AI model: source and licence | when an item enters the film |
| `spend.md` | every paid call (written by tools/spend.py) | automatically |
| `price_book.json` | prices read from the providers' own pages, each with its source and date; a price expires after a week | when a paid tool asks for a quote |
| `NOTES_vN.md` | the client's review notes for version N, mapped to shots, with fixes | each review round |
| `config.json` | title, slug, client folders, key file path, budget, loudness, renderer settings | setup; when folders move |
| `film/shots.json` | structure: format, chapters, shots, layouts, media, timing knobs | story/storyboard work |
| `film/script.json` | narration lines {id, text, dir, en} and the voice settings | script work |
| `film/vo_durs.json`, `film/vo_check.json` | measured line lengths; per-line provider, similarity, recorded flag | written by gen_vo.py / import_vo.py |
| `film/respell.json` | engine-only spellings for the TTS | voice work |
| `film/cues.py` | the sound cue sheet (everything except automatic narration, clip sound and room tone) | sound work |
| `film/timeline.json` | generated master timeline (never edit) | `python film/timeline.py` |
| `film/people_in_media.json` | which labelled people appear in which media (from faces.py apply) | after the photo map round |
| `src/` | Remotion code: theme.ts, lib/ (kit, ink), auto/AutoChapter, chapters/ (hand-built scenes) | picture work |
| `public/` | everything the renderer loads: media/, plates/, faces/, art/, fonts/ (keep audio OUT of public/) | asset prep |
| `sound/` | vo/, vo_prev/, synth/, music/, sfx/, lib/ (licensed library), voc/ (sung or hummed voice), own/ (client recordings) | voice and sound work |
| `inbox/` | client drops, numbered subfolders with a README each | client side |
| `out/` | ch/ (graded chapters), mix/ (stems), final/, qc/ (stills, QC reports), storyboard/, audition/, music/ (beat grids), archive/ (inventory, sheets, strips, faces, search) | builds |
