---
name: media-archive
description: "Mine a media archive for the film: real dates, best moments, faces to label, photo map. \"go through our photos\""
user-invocable: true
---

# Media archive: understand the material before writing a word

The library already contains the film: repeated moments across years (the same costume every festival, the same
helmet getting smaller), the big days (bursts of photos), the places that recur (GPS), the quiet stretches, and
the real sounds of those days inside the clips. Read it systematically; never pick from memory or file names.

All tools are in the project's `tools/archive/` (from the CutForge engine). They are read-only on the client's
folders and write to `out/archive/`.

## Workflow

For a big library, delegate steps 3-6 to the `archive-scout` agent and keep the shortlist, not the sheets.

1. **Inventory** every source folder (main library, other phones, pen drives, exported albums):
   `python tools/archive/inventory.py <folder> [<folder> ...]` → `out/archive/inventory.csv`
   Dates come from EXIF, then the video container, then the file name, then file time (flagged unreliable).
   It also records GPS, size, rotation (phone clips are often stored sideways), camera, and a quick hash.
2. **Statistics**: `python tools/archive/stats.py` → `out/archive/stats.md` + `monthly.png`.
   Read: files per month (peaks are events; near-empty stretches may be a hard period: ask, never assume, never
   narrate a reason not given), the biggest days, recurring places, duplicates, undated files.
3. **Look at everything once**: `python tools/archive/contact_sheet.py --by month` and Read every sheet.
   For videos: `python tools/archive/clip_strips.py` (8 frames + loudness curve per clip) and Read the strips.
   Note candidate moments with file, seconds, who/what, and why it matters, in `out/archive/candidates.md`.
   To find specific things across thousands of files ("a red motorbike", "sky lanterns", "a child on a beach"):
   `python tools/archive/search.py index` once, then `python tools/archive/search.py "<query>" ["<query>" ...]`
   → a contact sheet and a ranked csv per query in `out/archive/search/` (optional; needs open_clip_torch). It
   finds objects and scenes, never identities: confirm every hit by eye.
4. **Real sound**: `python tools/archive/sound_events.py` lists sustained tones (conch, bell, whistle, a held
   note), hits (drums, claps) and onsets. Listen to each candidate before using it; these beat any library effect.
5. **Faces** (sorting only): `python tools/fetch_models.py yunet sface` once, then
   `python tools/archive/faces.py scan` → cluster sheets. The client names the clusters in
   `film/face_labels.json`; then `python tools/archive/faces.py apply` writes `film/people_in_media.json` (screen-time
   counts for the cast check) and best face crops for people pages. Never label a cluster yourself.
   `apply` (and qc_story, storyboard) match media by file name stem and only see files already copied into
   `public/`: keep original file names when copying, rename clashes between phones (`IMG_0001` from two
   devices), and re-run `apply` after every new copy into `public/media/`.
6. **Patterns worth a scene**: the same activity in several years (match cuts: he grows up in one beat), a sound
   that recurs, a hero object, firsts (first photo, first steps, first words on video), festival timing.
7. **The photo map** (one question round): a page with every asset the film will use, its shot, its caption,
   who is in it, and the open questions (unknown people, undated files, missing photos). Once shots.json exists,
   `python tools/qc/storyboard.py` builds it from the project data; publish it as a private artifact (it shows
   family photos). The client types corrections in its note column and pastes them back with "Copy my notes";
   ticks and corrections come once; corrections go into facts.md and decisions.md immediately.

## Rules learned the hard way

- A face that looks like the father in a crowd may be a cousin; a "family celebration" may be another family's.
  Only the client confirms identity. Faces in the background are not the subject.
- A hero object needs proof (the showroom had another customer's bike of the same model that day).
- Rotation: probe every clip; normalise on import (a night-feed clip once played sideways in a draft).
- Copy only what the film uses into `public/media/`; keep originals untouched; record each source path in the
  photo map so the project can be rebuilt on another machine (a manifest maps media to the client's folders).
- Burst shoots (60 photos of one morning): pick by sharpness and expression; one or two, or a fast strip.
- Long clips: decide the exact seconds from the strip, not by guessing; note them in shots.json (`from`).
- Social media albums, other people's phones and old accounts often hold the missing years: ask, with permission.

## Outputs

`out/archive/inventory.csv`, `stats.md`, `monthly.png`, `sheets/`, `strips/`, `clips.csv`, `sound_events.csv`,
`search/`, `faces/cluster_*.jpg`, `candidates.md`; after the client's round: `film/face_labels.json`,
`film/people_in_media.json`, facts.md updated. See `references/photo-map.md` for the photo-map format.
