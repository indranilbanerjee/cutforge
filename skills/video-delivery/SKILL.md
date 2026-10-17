---
name: video-delivery
description: "Deliver the video: encodes per destination, verified transfers and the project hand-off. \"export it for YouTube\""
user-invocable: true
---

# Video delivery: the right file, verified on the far side, and a project anyone can continue

Delivery fails in boring ways: a 3.3 GB file on a FAT32 pen drive, a projector that cannot decode High@5.1, a
transfer that dies at 80 %, a hand-off nobody else can rebuild. Plan for the slowest link and verify on the far
side.

## 1. Encode per destination

`python tools/deliver/encode.py <master.mp4> <preset> [out.mp4]` (re-normalises loudness per preset):

| Preset | Use |
|---|---|
| `projector` | 1080p H.264 High@4.1 ~10 Mbps, -16 LUFS; small home projectors and TVs (bring `projector720` as backup) |
| `projector720` | 720p High@3.1 ~6 Mbps; weak players, old TVs |
| `youtube` | 1080p 12 Mbps, closed GOP, -14 LUFS, faststart |
| `reels` | 1080×1920 30 fps, -14 LUFS (source must already be vertical; captions inside the safe zone) |
| `whatsapp` | 720p ~2.5 Mbps; send as a document to avoid recompression |
| `broadcast` | 1080p 20 Mbps, -23 LUFS (EBU R128); US: `--lufs -24 --tp -2` |
| `archive` | the master's video copied, audio 320k |

Files over 4 GB do not fit FAT32: use exFAT/NTFS or play from a laptop (`--fat32` warns). Platform specs and
caption rules: `${CLAUDE_PLUGIN_ROOT}/docs/compliance-and-licensing.md` section 2; projector notes: section 5.

## 2. Move big files safely

- **Ask what the far side already has** before sending anything big. Real case: ten graded chapters (3.3 GB, 3.5
  hours over the link) were cut losslessly out of the master already on the client's PC with
  `tools/deliver/recover_chapters.py` (`ref` on the source machine, `cut` on the far side), verified by decoded-
  frame md5; the mix went over as lossless FLAC (204 MB instead of 340 MB), sample-identical.
- **Split, send, join, verify**: `parts.py split <file> --mib 15` → send the parts → `parts.py join
  <manifest.json>` on the far side (resumable: run again until COMPLETE; it never deletes, it truncates to the
  last verified part and appends) → whole-file md5 → decode check (`verify.py --final`).
- `rcopy.py` for resumable verified copies onto slow drives; `xtar.py` to extract archives on drives where
  delete/overwrite is not allowed, under a time budget.
- **Never delete or overwrite on the client's drives.** Write into a new dedicated subfolder; list leftovers
  (transfer parts) for the client to delete themselves.

## 3. Hand over the project, not only the film

The final hand-off is a folder anyone (or any agent) can continue with one-chapter re-renders:
- code (`src/`, `tools/`, `film/`, `render.mjs`, `package.json`), assets used (`public/`), narration
  (`sound/vo/`), cue sheet, graded chapters (`out/ch/*_f.mp4`), the mix, and the master
- `PROJECT.md`, `facts.md`, `decisions.md`, `sources.md`, `spend.md`, all `NOTES_vN.md`
- `CLAUDE.md` (pipeline commands and rules for any agent) + `README.md` (for a human) + `config.json` with the
  new machine's paths (`folders`, `api_keys_file`, `gl`, `concurrency`, `browser_executable`)
- excluded: `node_modules` (npm install), `models/` (fetch_models.py), raw chunks, transfer parts, keys
- on the far side: `npm install`, `python tools/setup_local.py`, render one chapter's stills to prove it

## 4. The screening (personal films and events)

Use `references/screening-run-sheet.md`. In short: test on the exact device in the room days before; carry the
master, a 720p backup and a phone copy; play from a laptop if the projector's player is unreliable; external
speaker; 2 s of black at both ends; offline (no autoplay, no notifications); one person owns play/pause, the
interval and the lights.

## 5. Archive

Master + project folder + sources.md (licences) + spend.md on two drives or a drive and a cloud account. Note
the md5 of the master in PROJECT.md.

## References

- `references/screening-run-sheet.md`: device test, run sheet, backups, what can go wrong in the room
- `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md` section H
