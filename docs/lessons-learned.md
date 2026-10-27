# Lessons learned: one real production, every mistake and fix

Source: a 20-minute storybook film made for a family milestone (see `case-study.md`), built over
four days by Claude end to end: archive research, story, storyboard, AI art, narration in the client's
cloned voice, sound design, Remotion render, grade, delivery to the client's PC, and a local hand-off.
Seven look tests and two full cuts. Every lesson below cost real time once. Each entry: what happened,
why, and the rule that prevents it. Rules marked ★ are non-negotiable in every CutForge project.

---

## A. Thinking and process

A1 ★ **The project folder is the memory.** Work crossed several sessions, a context compaction, a
container reboot and a hand-off between two models. What survived was what had been written down:
BRIEF, DESIGN, HANDOFF, script JSON, timeline, spend log, people map. What lived only in chat was lost
or re-derived. Rule: every decision, fact, correction and constraint goes into a file in the project
the moment it is made (`PROJECT.md`, `facts.md`, `decisions.md`, `NOTES_vN.md`, `spend.md`,
`sources.md`). Write as if the next session knows nothing.

A2 ★ **One brain end to end, or a hand-off that is a contract.** A "planning pass" by one model and a
"build pass" by another produced drift: the planner's notes said one thing, the builder assumed
another, and the client stopped trusting the second model. Rule: prefer one agent owning the whole
cut. If a hand-off is unavoidable, the hand-off doc lists exact files, exact commands, frame counts,
known-and-accepted issues, and hard rules, and the receiver re-verifies before building.

A3 **Look tests before scripts.** The client could not judge a written treatment. He judged a 30-second
render in seconds ("this feels primitive", "that's the wrong bike"). Rule: show a 20 to 60 s look test
of the hardest scene in week one. Iterate the look on a small piece, never on the whole film.

A4 **"Not a slideshow, a film."** Look test 1 put single photos on blurred backgrounds. The client
called it a slideshow. Rule: phone media is framed, never stretched or blurred-filled: prints that
land, triptychs, panels, pages, living photos with depth, real clip sound. See
`skills/storyboard-and-look/references/film-language.md`.

A5 **Homemade engine = primitive look.** Look test 2 used a custom renderer and code-synthesised sound
effects. Rebuilt on Remotion (React video) with real recordings and a real score, the same scenes
jumped a level. Rule: use the real tool stack from the first test; synthesise only what has no real
recording (drones, bells, abstract tones) and make those carefully.

A6 ★ **Budget gate before any paid call.** A spend cap was stated up front, paid calls were logged
one per line in `spend.md`, and scripts refused to call paid APIs unless a `GO_AHEAD.txt` existed.
Final spend: about two-thirds of the cap. Rule: estimate, cap, log every call, stop and report at the cap.
*Since 1.1.0 a file no longer counts as the go, because an agent can create one: a paid tool prints a quote and runs only with `--go` and `--quoted-providers` after the client's typed go.*

A7 **Back-plan from the event.** The premiere date was fixed and a festival ate the production week.
Rule: lock everything only the client can give (recordings, letters, photos, identity answers) by a
date well before the build, then the client only watches drafts.

A8 **Re-rendering is the bottleneck; design for partial re-renders.** Full renders took 5 to 6 hours on
a 2-CPU cloud box. Chapters as separate compositions, chunked resumable renders and per-chapter grade
meant a fix touched one chapter, not the film. Rule: never render the film as one composition.

A9 **Iteration speed decides quality.** The client finally asked for the whole project on his own PC
because cloud iteration was too slow. Rule: make the project portable from day one (config file for
paths, no hard-coded cloud paths, Windows-safe scripts) so it can move to the fastest machine.

## B. Context and facts (the most damaging class of mistakes)

B1 ★ **Never guess who is in a photo.** Wrong identities shipped in drafts: a man in a plaid shirt
labelled as the father (it was a cousin); a sky-lantern photo credited to the father (it was the
mother and a cousin); a relative's baby taken for the hero; another couple's celebration taken for the
parents'; a "three of us on the throne" photo that was two other children with the mother. Rule: build
a **people map** (who is who, how the hero addresses them) and a **photo map** (every asset used, shot
id, caption, who is in it) and get the client to tick it before the cut. Face clustering helps sort;
only the client confirms identity.

B2 ★ **Never guess an object's identity either.** The "father's bike" in look test 1 belonged to
another customer at the same showroom on the same day. The right one was in the key-handover photo an
hour later. Rule: for any hero object (vehicle, house, instrument), find the proof photo (receipt,
handover, plate) and lock its look in `facts.md`; every prompt and shot uses that.

B3 ★ **Never name a ritual, custom or relation from assumption.** A ceremony was labelled with a
common regional ritual name; the family does not follow that tradition. Rule: describe what is
visible ("blessings at dawn, the first rice") unless the client gives the name. Ask about kinship
terms; families use their own kinship terms and nicknames.

B4 ★ **Verify every quotation against a primary source.** A "Tagore line" in the script did not exist
in the collected works; it was a misremembered phrase. Replaced with a sourced Upanishad line. Rule:
every verse, quote, scripture or proverb gets a source URL in `sources.md`, public-domain status
checked (author death date / first publication), exact wording copied, not recalled.

B5 **Do not "fix" what you have not verified.** A planning pass "corrected" a Sanskrit spelling; the
original was correct sandhi. Rule: a correction needs the same proof as the original.

B6 **Chronology from metadata, not memory.** Events were placed out of order (a bike's arrival vs the
scenes that depend on it); later the client still found chronology issues. Rule: read EXIF
DateTimeOriginal (and GPS) for every asset into `out/archive/inventory.csv`; build the story order table with dates;
flag any shot whose asset date falls outside its chapter's span; ask about undated assets.

B7 ★ **Ask about sensitive chapters, and let the people involved decide.** A sensitive period was
handled as a metaphor (an empty nest, a drawer closing), no medical words, one line of narration,
and the people involved decided how much to show. Some years were excluded at the client's request.
Rule: identify sensitive periods early, propose the gentlest treatment, never add medical, legal or financial detail, and record the decision in `decisions.md`.

B8 **Balance the cast.** v1 felt "father-heavy" and missed several relatives the child calls by name.
Rule: count screen-seconds per person from the photo map; every person the hero addresses by name
gets at least one named moment unless the client excludes them.

B9 **Hidden data in the library tells the story.** Monthly photo counts showed the quiet stretches and
the peaks that shaped the structure. GPS clustering found the ancestral house. Burst
counts found the big days. Rule: always run the library statistics pass (see `media-archive` skill).

B10 **Real sound from the day beats any library.** A scan for long steady tones found a conch blown
on the morning of a ceremony and a drum at a festival, inside the family's own clips. Rule: extract
and catalogue the sound of every clip before buying or generating any effect.

## C. Story and structure

C1 **One story, three arcs, a hidden spine.** What worked: a narrator character with his own arc
(dignified, then charmed), the house (empty to full), the hero (carried to leading), and a quiet
structure (five elements) said aloud only once. Motifs carry time (a lamp, a heartbeat that turns out
to be the father's motorbike, a helmet that shrinks). Plant early, pay off later: list every
plant-payoff pair and check each survives every edit.

C2 **The opening must be story-first.** v1 opened with a studio ident and a colophon; the client cut
both. A personal film opens on the story's first image (here, a sound in the dark before any
picture). No self-promotion, no logos, no "presented by" in a family film.

C3 **One version.** Two cuts (party and family) plus a cake loop confused the delivery. The client
wanted one complete film. Rule: default to one master; extra versions only on request.

C4 **Narration rules that worked.** Never describe what is on screen; say what the photo cannot.
Silence after every emotional line (1.5 s). Every lump in the throat gets a laugh within ~20 s. Most of
the film has no narration. Banned words (cute, adorable, precious, journey, blessed). Third person.

C5 **Two audiences.** Kids follow sound, faces, jokes and call-and-response; adults follow the story.
Something to laugh at, sing or spot every 45 to 60 s. Waiting 6 to 8 s after a question to the room
lets children answer.

C6 **The client's own words are sacred.** The parents' letters were set exactly as written, including
their punctuation, and not read aloud. Rule: never edit a client's personal text; set it, animate it,
leave it.

C7 **Late placements break flow.** New photos and beats were added after the structure was set; the
client later found "things not in the right places at the beginning" and "mix-and-match" in places.
Rule: every insertion re-runs the story-order table and the chronology check, and the story editor
re-reads the whole chapter, not just the new shot.

## D. Voice and narration

D1 **Stock TTS voices sounded flat in the film's language; the client's own cloned voice won.** Path: five-voice
audition → three-engine audition → the client cloned his own voice and asked for it. Rule: audition on
6 representative lines (funny, tender, list, name-heavy, long sentence, emotional peak) before the full
script; let the client pick by ear on a phone.

D2 ★ **Cloned voices only with the voice owner's consent.** The "no cloned voices" rule was lifted only
because the owner cloned his own voice and asked for it. Never clone a third party.

D3 **Pronunciation needs a respell layer.** The engine read a name with an invisible joiner (ZWNJ) as an
extra syllable; loanwords and numerals were mangled. Rule: keep captions in correct spelling and feed
the engine a respelled copy (`respell()`); test the hero's name in 3 spellings first.

D4 ★ **Verify every line by speech-to-text.** Each generated line was transcribed back (Sarvam saarika)
and fuzzy-matched to the script (rapidfuzz); mismatches regenerate. Rule: no line enters the mix
unverified. Store results in `vo_check.json`.

D5 **Pace by direction.** A `dir` field per line ("slow, tender", "brisk, comic") mapped to engine pace
(0.78 to 0.97). Loudness-matched each line to −18 LUFS, peak ≤ 0.95, trimmed silence.

D6 **Keep the previous narration.** The previous takes were kept when regenerating, so any line could be
reverted (the engine copies them to `sound/vo_prev/`).

## E. Sound

E1 **Sound leads picture.** Next shot's sound starts ~0.5 s early (pre-lap). Music ducks ~12-17 dB under
narration. Real sound comes up full when the narrator is silent.

E2 ★ **No abrupt stops.** The client's main v7 note. An automatic audit of the v7 mix found: the title
line ran 0.44 s past its shot (a `fixed` shot length shorter than its narration), and most episode
endings had ~2.5 s of dead air followed by a sound cut off 0.3 s into the next chapter. Rules: every
shot's tail ≥ 0.6 s after its last line unless a hard cut is intended; `fixed` shots assert the
narration fits; every cue has a fade-out ≥ 0.15 s (music ≥ 1.5 s); chapter boundaries get a sound
bridge (ring-out or pre-lap), never silence; run `film/timeline.py` and `tools/qc/qc_audio.py` before
every render. See `video-qc` skill.

E3 **Keep the score unbroken.** Look test 3 chopped the music at every cut; look test 4 played one
piece and cut picture to its beats. Rule: edit music only on matching beats; picture follows music.

E4 **Sing-alongs must be on the beat.** Word highlights were 0.7 s late until aligned to measured
onsets. Rule: align lyric/caption timing to detected onsets, not estimates.

E5 **Synthesised instruments need filtering.** A Karplus-Strong tanpura sounded hashy until a strong
low-pass (≈2.8 kHz) was added; verify harmonic peaks by spectrum, and listen.

E6 **Licensing per use.** BBC Sound Effects archive is licensed for personal/educational use: fine for a
home film, not for client work. Kenney packs are CC0. AI music (Lyria) carries a SynthID watermark.
Copyrighted songs were avoided; public-domain melodies and the family's own singing were used. Rule:
log the licence of every sound in `sources.md` and pick sources by the project's use (see
`compliance-and-licensing.md`).

E7 **Loudness by destination.** Mixed to −16 LUFS integrated, true peak −2 dBTP for a small projector
speaker. Online platforms normalise around −14; broadcast −23/−24. Check with `ebur128`.

## F. Visuals, VFX and AI

F1 ★ **No AI on real faces.** No AI motion, edits or invented faces on real people, especially
children. AI only where no camera was (a painted sea behind a real photo, a road years from now seen
from behind, a banyan of ancestors' names). Drawings look like drawings. Image-to-video services may
refuse photos of children anyway.

F2 **Composite instead of generating over people.** The "painted sea comes alive" shot: remove the
child with a person-segmentation cut-out (rembg u2net_human_seg), animate only the backdrop (Kling
image-to-video), put the untouched cut-out back on top.

F3 **Style transfer must keep likeness, verified by eye.** Oil-portrait versions of four photos were
accepted only after checking faces were unchanged; reject and lower strength otherwise.

F4 **One palette suffix on every prompt.** Every generation prompt ended with the same style sentence
and five hex colours, so art matched across tools. Log prompt, model, seed, cost.

F5 **2.5D living photos.** Depth Anything V2 depth map + a small parallax (2 to 4 %) on wide shots only;
faces stay still. Max ~10 % zoom over 5 s.

F6 ★ **Complex scripts break in naive text rendering.** A cut-down font file broke an Indic-script conjunct;
letter-spacing broke words. Rule: full font files only; never letter-space Indic text; shape animated
text with HarfBuzz into glyph paths (`shape.mjs`) so conjuncts survive stroke-by-stroke animation;
check every title by eye in a still.

F7 **Rotation metadata.** A night-feed clip played sideways. Rule: probe rotation for every clip;
normalise on import.

F8 **Ancestor wall photos need straightening.** Photos of framed portraits taken at an angle were
perspective-corrected (OpenCV four-point warp) before use.

F9 **Projector reality.** Mini projectors crop edges after keystone; keep faces and words inside ~86 %;
smallest caption ≥ 1/20 of screen height; lifted blacks, warm grade, nothing thin or dark.

## G. Engineering (technical mistakes)

G1 **Timeline drives everything.** `timeline.py` computed every shot's length from measured narration
plus pre/gaps/post, wrote `timeline.json` for both picture (React) and mix (Python). A narration change
re-flows the whole film consistently. Rule: never hand-type a time that can be derived.

G2 **Use `voEnd()`, not assumed durations.** A label appeared after its shot ended because the line was
shorter than assumed. Rule: anchor on-screen events to measured narration times.

G3 **Layout collisions show only in stills.** Portraits overlapped name tags; a print sat under circles
(z-order). Rule: render stills at every shot's start, middle and last line before any full render.

G4 **Cloud boxes die when idle.** A container reboot killed a 5-hour render. Rule: chunked resumable
renders (750-frame chunks skipped if present), a keep-alive while rendering, a queue log, and never
idle-wait on a long job without a watcher.

G5 **Disk fills up.** A 252 GB box had a small per-session allowance; 93 % full mid-render. Rule:
delete raw chunks after concat, delete transfer parts after verification, keep only graded chapters.

G6 **Splicing at keyframes.** Re-rendered pieces spliced into a chapter with stream copy only work at
keyframes; verify frame counts and full-decode after any splice, else re-render the chapter.

G7 **Shell pitfalls.** `ffmpeg` inside a `while read` loop eats stdin (use `-nostdin`); `pgrep -f` matches
itself; `rm -rf` with globs may be blocked by safety checks (use explicit paths); background processes
die when a remote shell call ends.

G8 **Windows portability.** Indic-script JSON written with Python's default cp1252 crashes (always
`encoding='utf-8'`, `PYTHONUTF8=1`); ffmpeg filter graphs break on `D:` drive-letter colons (run ffmpeg
with cwd at the LUT); `python3` is a Store stub on Windows (detect, fall back to `python`); Remotion
copies `public/` on Windows (no symlinks); GPU GL (`angle`) on Windows, `swiftshader` on headless Linux.

G9 **Missing models and blocked hosts.** OpenCV's Haar cascade was missing in a new wheel (switched to
YuNet); GitHub raw was blocked by the proxy but `media.githubusercontent.com` worked; a large upload to
an AI host failed with SSL EOF until the image was downscaled.

G10 **Know the API surface.** The cloned-voice id was rejected by the standard TTS endpoint; the
provider had a separate clone endpoint. Rule: read the provider's current docs before assuming.

## H. Delivery and hand-off

H1 **Slow links need small verified parts.** The PC link moved ~250 KB/s through the device bridge.
Rule: split into 15 MiB parts, md5 every part, join resumably on the device (truncate to a part
boundary, append), md5 the whole, then decode-check.

H2 **Don't re-send what the client already has.** The ten graded chapters (3.3 GB) were cut losslessly
out of the delivered master on the client's machine and verified frame-for-frame by decoded-frame
hashes, instead of uploading them. The mix went over as lossless FLAC (204 MB instead of 340 MB),
sample-identical. Rule: before any big transfer, ask what can be reconstructed on the far side.

H3 **Never delete on the client's drives.** The client's rule: only add, in a dedicated subfolder.
Transfer leftovers were listed for the client to delete himself.

H4 **Ship the project, not only the film.** The final hand-off was the whole project (code, assets,
narration, graded chapters, mix) with `CLAUDE.md` + `README.md` + `config.json`, so any agent on the
client's machine can continue with one-chapter re-renders.

## I. Working with the client

I1 Short, plain, specific updates; timestamps for every new scene ("8:26 the family page").
I2 One question round, not twenty: batch identity questions into the photo map.
I3 Show, don't describe: a still or a 30 s clip answers what a paragraph cannot.
I4 Say what was checked and how ("grouped ~3,000 faces, read the camera date of every event").
I5 When the client says "it feels primitive" or "abrupt", treat it as a precise bug report and find
the mechanism (engine, sound, timing), not as taste.
