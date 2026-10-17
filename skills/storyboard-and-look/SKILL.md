---
name: storyboard-and-look
description: "Storyboard every shot and lock the look with a test render, layouts and safe areas. \"it looks like a slideshow\""
user-invocable: true
---

# Storyboard and look: decide how it looks on a small piece, then plan every shot

Clients cannot judge a written treatment; they judge a 30-second render in seconds ("this feels primitive",
"that's the wrong bike"). So the look is decided on the hardest scene first, with the real stack, real sound and
real material, then every shot is planned as data in `film/shots.json`.

## 1. The look test (before the full script)

1. Pick the hardest 30-60 s: the scene with the most media types (phone portrait photos, clips with sound, a
   title, a transition, a sensitive beat). Easy scenes prove nothing.
2. Build it with the production stack from the first test: Remotion layouts, a real score or a real recording,
   the client's clip sound, the grade. A homemade renderer and code-made sound effects read as "primitive"
   (that was look test 2 of a real production); the same scenes rebuilt in Remotion with real sound jumped a level.
3. Frame phone media, never stretch it or fill bars with blur: blurred-background singles read as a slideshow.
   Use prints that land on a page, triptychs of vertical clips, panels, living photos with depth, real clip sound.
4. Render stills first (`python tools/qc/stills.py <chapter>`), look at them, then render the clip.
5. Show it on the delivery device or the closest thing (a phone, the projector) with sound, plus a still sheet.
   Ask one question: "is this the level?" Iterate on this piece only; never iterate the look on the whole film.
6. Record what was decided (layout family, palette, grade preset, fonts, caption style, transitions) in
   `decisions.md` as the look bible. Seven look tests is normal for a demanding client; each one is cheap.

## 2. The film language

Choose 2-4 references (films, painters, illustrators, a brand's world) and write for each: what it brings
(frame, light, drawing, voice), where it leads in the runtime, and what is never copied (scenes, characters,
music, lettering). Map them over the runtime: strong where a reference leads, pale where it only touches. The
client's real photos and clips fill almost every minute; the references only decide the frame, the light, the
drawings and the voice around them. Full vocabulary: `references/film-language.md`.

## 3. The shot plan (`film/shots.json`)

Every shot is data: timing keys (`vo`, `pre`, `gaps`, `post`, `min`, `fixed`, `hardcut`) plus a layout and its
options. `film/timeline.py` turns it into exact times from the measured narration, so picture, captions and mix
always agree. Schema and every option: `references/shots-schema.md`.

- Layouts with no code: `living`, `portrait`, `prints` (1-3), `triptych`, `title`, `card`, `page`, `black`.
- Options: `zoom`, `drift`, `bw`, `glow`, `date`, `stamp`, `lower`, `xfade`, `fadeIn`, `fadeOut`, `caps`,
  `capsMode`, `sound`, `printAt`/`printGap`, `lineAt`/`lineGap`, `titleAt`, `inkTitle`, `size`, `font`, `color`.
  Screen recordings and UI: `"zoom": [1, 1]` (the default slow push crops edges).
- Chapter keys: `name` (letters, digits, hyphens), `span`, `order`, `fadeIn`, `fadeOut`. A chapter is hand-built
  when `src/chapters/index.ts` registers a component under its name; otherwise AutoChapter renders it.
- A shot that needs choreography (a page turn carrying content, a drawn line that follows narration, a
  composite) gets a hand-built component in `src/chapters/` (pattern: `src/chapters/Example.tsx`), registered
  in `src/chapters/index.ts`. Anchor everything to `useShot().vo(k)` / `voEnd(k)`, never to guessed seconds.

Timing defaults that worked: `pre` 0.6-1.0 s (2.5 s+ for an opening), `post` ≥ 0.6 s and 1.5-2.5 s after an
emotional line, `xfade` 0.6-1.0 s between related shots, hard cuts only on purpose (`"hardcut": true`) and on a
beat. Picture follows music: cut on phrase starts (`python tools/mix/beats.py <music> --snap <t>`).

## 4. Frame rules (check every one in stills)

- **Safe area.** Keep faces and words inside 86 % of the frame for projectors (keystone crops edges) and TVs.
  Vertical video: platform UI covers the top ~15 % and bottom ~35 %; keep text in x 10-90 %, y 15-65 %
  (see `${CLAUDE_PLUGIN_ROOT}/docs/compliance-and-licensing.md` section 2). The engine's vertical defaults keep
  captions, prints, cards, date notes and name tags in that band, and stills draw it; triptychs do not suit
  vertical (use one clip per shot).
- **Readable text.** Smallest caption ≥ 1/20 of frame height (the engine sizes captions to at least that: 36 px
  landscape, 54 square, 64 vertical), on a band or a page, high contrast, at least 1.5 s on screen per short line, never over a busy face.
- **Complex scripts** (Bengali, Hindi, Tamil and other Indic, Arabic, Thai): full font files only (a subset font
  broke a conjunct), never letter-space them, shape animated titles into glyph paths with HarfBuzz
  (`tools/text/shape_jobs.json` → `bash tools/text/shapeall.sh` → `src/glyphs.json`, then `inkTitle`/`InkText`
  by id), and check every title by eye in a still. Fonts must be licensed for video (OFL is safe).
- **No layout collisions.** Prints, portraits, name tags, stamps and captions overlap only in stills you have
  not looked at. Render stills at every shot's start, line midpoints and end.
- **Page turns carry content.** A turning page must show the outgoing shot's finished state (a static copy of
  the last frame), never a blank page.
- **Rotation.** Probe every clip; phone clips stored sideways play sideways.
- **Faces stay still.** Depth parallax 2-4 % on wide shots; zoom ≤ 10 % over 5 s; no warping of faces.

## 5. The storyboard page (one review round)

`python tools/qc/storyboard.py` writes `out/storyboard/index.html`: every shot with its film time, still or
thumbnails, narration lines with direction, overlays, asset dates and who is in each asset ("?" when not
confirmed). Publish it as a private artifact (it shows the client's photos) or send the file, as both the storyboard and
the photo map: the client types corrections in the note column (kept in their browser), presses "Copy my notes"
and pastes them back, in one pass. Corrections go into `facts.md`, `decisions.md` and shots.json the same
day, then re-run `python tools/qc/qc_story.py`.

## 6. Grade

One grade over everything makes phone photos, clips, AI plates and graphics feel like one film. Presets in
`tools/grade/grade.py`: `warm` (storybook, family), `pop` (kids, bright brand), `neutral` (corporate,
explainer), `bw`, `doc`. Choose in the look test; projectors want lifted blacks and warmth, nothing thin or dark.

## Checklist before leaving this phase

- [ ] look test approved on the delivery device; look bible in decisions.md
- [ ] shots.json covers every script line; `python film/timeline.py` has 0 ERROR and every WARN read
- [ ] stills sheets looked at for every chapter (safe area, caption size, collisions, identities, spelling)
- [ ] storyboard / photo map ticked by the client in one round
- [ ] runtime within 5 % of the target (qc_story RUNTIME)

## References

- `references/film-language.md`: layouts, transitions, camera moves, typography, how to make stills feel alive
- `references/shots-schema.md`: every key in shots.json with defaults and examples
- `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md` sections A3-A5, F, G1-G3
