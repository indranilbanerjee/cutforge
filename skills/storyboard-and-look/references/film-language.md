# Film language for photo-and-clip films

The difference between a slideshow and a film is not the effects; it is that every frame is composed, every
cut is motivated, and sound carries the viewer across. These are the patterns that held up.

## Framing phone media

| Material | Do | Never |
|---|---|---|
| Landscape photo | `living`: full frame, slow push or drift; depth parallax for wide scenes | zoom > 10 % in 5 s; Ken Burns on every shot |
| Portrait photo | `portrait` (framed on the page or black), or a `prints` print, or one of a triptych | stretch to 16:9; blurred copy behind it |
| Several photos of one moment | `prints` (1-3 land on a paper page, staggered `printGap` ~0.9 s) | a grid of tiny thumbnails |
| Vertical phone clips | `triptych` of three related clips, or a print that plays | pillarbox with blur |
| A clip with real sound | `sound: true` (the mixer lays its audio), hold long enough to hear the moment | mute it under music |
| Documents, letters | straighten (`tools/vfx/straighten.py`), a page with the letter as a print; set typed words in hand lettering exactly as written | edit the client's words |
| Ancestor wall portraits | straighten, then frame as prints or a family-tree page | colourise or animate the faces |
| Black and white | `bw` for the past, a prelude, or memory; `glow` keeps only bright coloured lights (lamps at night) | B&W as decoration on random shots |

## Composition rules

- One subject per frame. If three photos matter equally, make it a triptych or prints; if one matters, give it
  the whole frame.
- Leave headroom for captions (bottom 12 % of the frame) or put captions on the page.
- Eyes in the upper third. Faces never cut by a frame edge or a print border.
- Consistent light direction across a sequence (the grade helps; choose photos that agree).

## Transitions (each one needs a reason)

| Transition | Use for |
|---|---|
| Cut on a beat | energy, comedy, lists; the default inside a scene |
| Dissolve (`xfade` 0.6-1.0 s) | time passing within one place; tenderness |
| Dip to black (`fadeOut`/`fadeIn`, chapter fades) | act breaks, before and after sensitive beats |
| Page turn (custom, `PageTurn`) | chapter change in a storybook film; must carry the outgoing page's content |
| Ink wipe (`InkWipe`) | into a memory or an illustrated scene |
| Match cut | the same pose, costume or place across years: growth in one beat |
| Sound pre-lap | the next scene's sound starts ~0.5 s before its picture; the best transition of all |

## Making stills feel alive (no AI on faces)

- Depth parallax: `tools/vfx/depth.py` → `parallax.py` plates (dolly ≤ 0.08, faces still).
- Light: `LampLight`, `LightLeak`, a slow vignette breathing, halation and grain from the grade.
- Paper: pages that drift slightly (`Page drift`), prints with shadow and a small settle on landing.
- Hand-made marks: doodles, stamps, date notes, ink strokes that draw on as the narrator speaks.
- Real sound under a still: the room tone of that day from a clip, a bird, a bell.
- Composites: a real cut-out person (untouched) over a painted or animated background (see `visuals-and-ai-art`).

## Typography

- Two families at most: one for titles/hand lettering, one for captions. A display face for running gags.
- Captions: serif or humanist sans, ≥ 1/20 frame height, on a soft band (film) or directly on the page (paper).
- Indic and other complex scripts: full fonts, no letter-spacing, shaped glyph paths for animation
  (`tools/text/`), and `kern.json` for display fonts that set two letters too far apart.
- Numbers and dates in the narration language's numerals if the film is in that language; be consistent.
- Every on-screen string is checked in a still by someone who reads the language.

## Kids in the room (when children watch)

- Their own face big, their own voice, animals, vehicles, silly sounds, things to count or shout.
- Call-and-response cards, a question with 6-8 s to answer, a sing-along with word highlights on the beat.
- Pace: something new every 4-6 s in kids' segments; adults tolerate long holds, kids do not.

## Vertical and square versions

Design for the narrowest frame the film will ship in, or keep a centred safe zone. Prints stack in the band
above the captions; triptychs become one clip per shot; captions sit with their bottom at 64 % of the height and
name tags at 30 %, clear of platform UI. Square frames anchor captions at 90 % and name tags at 62 %; every format
grows a long caption upwards from its anchor, so it never leaves the safe area. Make vertical a separate project (`--format vertical`) sharing script and sound, not a crop.
