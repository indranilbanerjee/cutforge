---
name: story-design
description: "Design the story: arcs, hidden spine, plant-payoffs, beat map and the narration script. \"write the story for the film\""
user-invocable: true
---

# Story design: find the story in the material, then write it down so it can be built

A film is not "the best photos with music". It is one story with a point of view, told in an order that makes
the viewer feel something they could not get from the album. The story is already in the material (the library
statistics, the repeated moments, the sounds); the job is to find it, shape it, and write it so precisely that
picture, sound and narration can be built from it.

Prerequisites: the brief (`video-brief`) and the archive pass (`media-archive`): `brief.md`, `facts.md`,
`out/archive/stats.md`, `candidates.md`, the client's voice notes. Never write the story before reading the material.

## Workflow

1. **Read the material for its story.** From the stats and contact sheets, list: the peaks (big days), the
   silences (ask what they were; never narrate a reason not given), the recurring moments across years (same
   costume, same place, same object getting smaller), firsts, hero objects, real sounds, the client's own phrases
   in voice notes. Write a one-sentence logline that is about something ("a girl who collects stones, and the sound of
   her grandmother's sewing machine"), not a period ("four years of photos").
2. **Choose the frame.** Who tells it (a narrator character, the client's own voice, real interviews, captions
   only), from what point of view, in what language, with what title idea. A narrator character needs a casting
   brief (age, region, register, texture, rules) for `voice-and-narration`.
3. **Build the structure** (see `references/story-devices.md`):
   - chapters with a runtime budget each (sum = target runtime; leave 5 % slack);
   - three arcs running under the whole film: a place or group (empty → full), the hero (carried → leading),
     and the teller (dignified → charmed, or sceptic → convinced);
   - a hidden spine: a structure said aloud only once (five elements, four seasons, seven firsts);
   - motifs that carry time (a sound, an object, a colour) and running jokes that escalate;
   - a plant-payoff list: every plant, where it pays off, and the shot ids, so edits cannot orphan one;
   - an opening on the story's first image (no logos, idents, "presented by" in a personal film) and an ending
     that pays off the opening and looks forward.
4. **Map the room.** For each minute: what the youngest viewer gets (a face, a sound, a laugh, something to
   answer, sing or spot every 45-60 s) and what the adults get (the story underneath). For brand work: what the
   scroller gets in 3 seconds, and what the buyer remembers after 30 (see `marketing-video`).
5. **Order the story by evidence.** Build the story-order table (`references/treatment-template.md`): chapter,
   beat, assets, capture dates, people. Chronology comes from `out/archive/inventory.csv`, never memory. Set each
   chapter's `"span"` (and `"order": "chronological"` when it should be) in `film/shots.json` so
   `tools/qc/qc_story.py` checks it on every build.
6. **Write the treatment** (one to two pages, the template in references) and show it to the client with 3-5
   key lines in the narration language. Get a yes before the look test. Then run the `story-editor` agent on it.
7. **Write the script** into `film/script.json`: one entry per line, `{"id", "text", "dir", "en"}` (`en` is a
   working translation for reviewers, never shown). Line ids follow shot ids (`7D` → `7Da`, `7Db`). Write in the
   narration language first; translate for review, not the other way round.
8. **Verify every borrowed word.** Each verse, proverb, quote or song line gets a primary source URL in
   `sources.md`, its public-domain status (author's death year / first publication date) and the exact wording
   copied from the source, not recalled. A planning pass once "corrected" a correct Sanskrit spelling: a
   correction needs the same proof as the original.

## Narration rules (they held up in a 20-minute film)

- Never describe what is on screen. Say what the picture cannot: the before, the after, the inside joke, the
  meaning of a name, what nobody said out loud.
- Most of the film has no narration. ~100 short lines in 15 minutes, most a few words long.
- Silence after every emotional line (1.5 s at least, set as the shot's `post`). Music never swells under words.
- Every lump in the throat gets a laugh within ~20 s.
- Banned words: cute, adorable, precious, journey, blessed, unforgettable, magical (and their equivalents in the
  narration language). Specifics beat adjectives.
- Keep one person: third person ("our hero", the name) unless the client narrates as themself.
- The client's own words (letters, wishes) are set exactly as written, punctuation included, never edited, and
  usually not read aloud: let the room read them.
- Write for the ear: short sentences, one idea each, numbers spelled the way they are said, names the engine
  can pronounce (respell layer in `voice-and-narration`).
- Questions to children need 6-8 s of waiting room before the film moves on.

## Sensitive material

Identify sensitive periods in the brief (a loss, an illness, a separation, years the client excludes). Propose
the gentlest treatment: a metaphor (an empty nest, a drawer closing), one line at most, no medical, legal or
financial words. The people it belongs to decide (often both partners, not only the one briefing you). Record
the decision in `decisions.md`. Never fill a gap in the library with an invented reason.

## Outputs

- `treatment.md` (logline, frame, structure, arcs, spine, motifs, plant-payoff, beat map, 3-5 key lines)
- `story_order.md` (the evidence table) and chapter `span` / `order` in `film/shots.json`
- `film/script.json` (every line with id, text, dir, en); `sources.md` updated for every borrowed word
- `decisions.md` entries for sensitive chapters, exclusions and anything the client chose

## Mistakes this skill exists to prevent

- A structure imposed from a template instead of found in the material (it reads as generic).
- Opening on a studio ident or a colophon; two versions when the client wanted one film.
- Late insertions that break the order: every new beat re-runs the story-order table and the story editor
  re-reads the whole chapter, not just the new shot ("things not in the right places" was a real note).
- A misremembered quotation attributed to a famous poet; a ritual named from assumption; a relative left out
  (run `tools/qc/qc_story.py` CAST after the photo map).

## References

- `references/story-devices.md`: structures by genre, devices that worked (and why), the devices-not-material rule
- `references/treatment-template.md`: treatment and story-order table templates
- `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md` sections B and C
