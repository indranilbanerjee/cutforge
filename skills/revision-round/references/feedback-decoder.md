# Feedback decoder: what clients say, what it usually means

| They say | Usual mechanism | Where to look | Fix |
|---|---|---|---|
| "Abrupt", "stops suddenly", "jerky" | narration longer than a fixed shot; tails < 0.6 s; cues with short fade-outs; silence at chapter ends then a sound cut; a cue cut at a mix window edge | `timeline.py` WARN/ERROR, `qc_audio.py` DROP/CUT TAIL/DEAD AIR | raise `post`/`fixed`; bridges (ring-out, pre-lap); min fade-outs; room tone on |
| "Not in the right place", "mix-and-match", "confusing order" | chronology broken by late insertions; a scene placed by theme, not date; two styles intercut | `qc_story.py` CHRONOLOGY, story_order.md, the storyboard page | reorder by date or mark flashbacks; re-run story editor on the chapter |
| "Feels primitive", "cheap", "amateur" | homemade renderer; synth effects; no motion design; flat sound; no grade | the look test vs the cut | real stack (Remotion layouts), real recordings and score, grade, depth parallax, light |
| "Slideshow" | single photos full screen one after another; blur fills; pans on everything | layouts in shots.json | prints, triptychs, pages, living photos, real clip sound, transitions with reasons |
| "Wrong person", "that's not my uncle" | identity guessed from a face or context | facts.md, face clusters, photo map | correct facts.md; re-check every shot with that person; re-run the photo map for the chapter |
| "Wrong bike/house/thing" | hero object not proven | proof photo in facts.md | lock the object's look; replace every instance; fix AI prompts |
| "We don't call it that" | ritual or relation named from assumption | captions, narration, stamps | describe instead of naming, or use the family's word |
| "So-and-so is missing" | cast imbalance | `qc_story.py` CAST, people map | add a named moment for each person the hero addresses |
| "Too much of me", "father-heavy" | screen time skewed to the client's own photos | CAST counts | rebalance; ask for other phones' photos |
| "The voice sounds robotic/flat/grand" | wrong voice for the brief; pace; text written for the eye | audition page, `dir` per line | re-audition on 6 lines; rewrite lines for the ear; adjust pace_scale |
| "It says the name wrong" | engine reads the spelling, joiners, loanwords literally | vo_check.json, respell.json | respell layer; regenerate those lines; verify by STT |
| "Too long", "drags" | narration over-explains; holds too long without new information; a chapter without a beat for kids | runtime per chapter, beat map | cut lines (most of the film should have none), tighten `post` on non-emotional shots, add a beat |
| "Too fast", "can't take it in" | posts too short after emotion; captions too brief | `post` values, caption durations | 1.5-2.5 s after emotional lines; captions readable twice |
| "Can't read it" | caption size, contrast, safe-area crop, complex-script rendering | stills with `--safe` | ≥ 1/20 height, bands or pages, inside 86 %, shaped glyphs |
| "Music is too loud", "can't hear him" | bed level, ducking depth, music swelling under words | speech-over-bed report | lower bed, deeper duck, move the swell to a gap |
| "It doesn't feel like us" | library sounds and generic music instead of the family's own; generic narration | sources.md, cues.py | the family's own clips, hums, voices, rituals; specific lines |
| "Kids got bored" | long adult-only stretches | beat map | something to laugh at, sing or answer every 45-60 s |
| "The colours look off on the projector" | dark grade, crushed blacks, thin lines | the device test | warmer, lifted blacks, thicker lines and type |
| "It won't play" | codec/profile, file system, file size | encode preset, FAT32 limit | `encode.py projector` or `projector720`; exFAT/NTFS drive; play from a laptop |

When a note does not fit: ask for the timestamp and one sentence about what they expected instead.
