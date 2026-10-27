# Case study: a 20-minute storybook film for a family milestone (anonymised)

Every name, place, language detail, voice and photo of the family is left out on purpose. What remains is how the work
went, what broke, and what CutForge took from it.

## The job

A family asked for a film for a milestone celebration: about twenty minutes, narrated in their own language, built
from several years of phone photos and clips, premiering at home on a small projector in front of family and
children. A fixed date about nine days away, a major festival in the middle of it, a small cap for paid tools, and a
client busy with work. The material: over a thousand photos and videos in a cloud photo library, more on other
family members' phones, a few social-media albums, and nothing professionally shot. The finished film ran just under
twenty minutes in ten chapters.

## Phase by phase

**Brief.** Instead of a long questionnaire, one live "show page" (a published artifact) carried the plan, every open
decision with a recommendation marked, and an inputs form whose answers Claude could read back. Numbered inbox
folders on the client's drive each had a README: what goes here, used in which scene, by when, and how to record it on
a phone. The client's hard rules were copied word for word: never delete anything on their drives, keys stay in files,
no AI on real faces, some years left out.

**Archive.** Inventory and statistics first. Monthly counts showed the quiet stretches and the big peaks. GPS clusters
found the family home. Bursts found the big days. A semantic image search (OpenCLIP embeddings) found specific objects
across thousands of files. Face clustering (YuNet + SFace) grouped about 3,000 faces for the family to name. Clip
strips and a sound scan found a conch blown on the morning of a ceremony and festival drums inside the family's own
videos.

**Story.** A treatment with a narrator character (an unseen old storyteller who starts like a headmaster and ends
charmed), a hidden spine of five elements said aloud once, three arcs (the house: empty to full; the child: carried to
leading; the storyteller: dignified to charmed), a sound motif (a heartbeat in the dark that turns out to be a
motorbike at the gate), running jokes that grow year by year, and parody cards (a streaming-style rating card, "skip
intro: not today", "Laws of the house"). The film language took devices, never material, from a few classic films, an
illustrator's ink drawings and a painter's palette. A 66-shot, 13-scene storyboard and a screenplay view were generated
from one data file.

**Look tests.** Seven, each fixing one class of problem. Test 1 put single photos on blurred backgrounds and used the
wrong motorbike (another customer's, photographed at the same showroom an hour earlier): "a slideshow". Test 2 ran on a
homemade renderer with code-made sound effects: "primitive". The rebuild moved to Remotion with real recordings and a
real score, and the same scenes jumped a level. Later tests fixed music chopped at every cut (music-first editing),
broken conjuncts in animated Indic-script titles (HarfBuzz-shaped glyph paths), and a "famous poet's line" that turned
out not to exist in the collected works (replaced by a sourced public-domain verse).

**Voice.** Five stock voices were auditioned on the same lines, then three engines. The client then cloned their own
voice with the provider and asked for it. All 131 lines were regenerated in it, each transcribed back by
speech-to-text and fuzzy-matched to the script. A name containing an invisible joiner was read with an extra syllable:
a respell layer fixed it while the captions kept the correct spelling.

**Art.** AI only where no camera was: a painted sea that comes alive behind a real photo of the child (the child cut out
untouched and composited back on top), a road years from now seen from behind, flowers moving in the wind, a banyan
tree carrying the ancestors' names. Four photos became oil portraits only after a likeness check. Photos of framed
ancestor portraits on a wall were perspective-corrected. Spend stayed at about two-thirds of the cap, every call
logged.

**Sound.** A synthesised tanpura (hashy until a strong low-pass), bells tuned to the score, the family's own conch and
ululation recorded at home, festival drums from their clips, and a chant in the narrator's voice. Mixed to -16 LUFS for
a small projector speaker.

**Build.** Ten chapters as separate compositions. Chunked, resumable renders on a 2-CPU cloud box took 5-6 hours for
the film. A container reboot killed one long render (hence resumable chunks and a watcher). The disk hit 93 %
mid-render (hence deleting chunks after concatenation).

**Revisions.** The first full cut drew precise notes: open on the story, not a studio ident; add the family lineage with
the ancestors; handle a sensitive period the way the family chose; add relatives the child calls by name who were
missing; fix several wrong identities (a cousin labelled as a parent, another family's celebration taken for the
client's); a better voice; more art; one version, not two. A planning pass by one model and a build pass by another
drifted apart, so the client asked for one model to own the whole build.

**Delivery.** The 3.3 GB master crossed a slow link (a few hundred KB/s through a device bridge) in 15 MB verified parts
with a resumable joiner. The ten graded chapters were then cut losslessly out of the master already on the client's PC
instead of being uploaded again (verified frame by frame by decoded-frame hashes). The mix went as lossless FLAC, and
the whole project (code, assets, narration, chapters, mix, CLAUDE.md, README, config) was handed over so any agent on
the client's machine could continue with one-chapter re-renders.

**After delivery.** The client's notes on the final cut: things not in the right places at the beginning, chronology,
missed nuances, mix-and-match in places, abrupt stops. An automatic audit found the mechanisms: the title line ran
0.44 s past its fixed shot, and most chapter ends had about 2.5 s of dead air followed by a sound cut off 0.3 s into the
next chapter. Those findings became CutForge's timing checks, minimum fade-outs, chapter bridges and audio QC.

## What CutForge took from it

| What went wrong or right | Became |
|---|---|
| Facts lived in chat and were lost across sessions | the project folder is the memory (PROJECT, facts, decisions, NOTES) |
| Wrong identities and a wrong object shipped in drafts | the photo-map round; face clustering only sorts; proof photos for hero objects |
| A slideshow, then a primitive engine | look tests on the real stack; the layout library; the film-language reference |
| Narration timed by hand drifted | `film/timeline.py`: every time derived from measured narration |
| Abrupt stops | tail checks, fixed-shot errors, minimum fade-outs, bridges, `qc_audio.py` |
| Chronology and cast complaints | chapter spans, `qc_story.py` CHRONOLOGY and CAST |
| A misattributed quote | sources.md with primary sources and public-domain status for every borrowed word |
| A mispronounced name | the respell layer and speech-to-text verification of every line |
| Hours-long renders, reboots, full disks | chapters, resumable chunks, FRESH, cleanup, a watcher |
| Slow links | verified parts, rebuild on the far side, the project hand-off |
| Spend creep risk | the quote gate: a quote from a price read on the provider's own page, the client's typed go (`--go --quoted-providers ...`), a cap, spend.md |
