---
name: visuals-and-ai-art
description: "Add visuals, parallax and AI art only where no camera was, never on real faces. \"make the photo come alive\""
user-invocable: true
---

# Visuals, VFX and AI art: real first, AI only where no camera was

The client's real photos and clips are the film. Effects exist to make them feel alive and to show what no
camera captured: a painted sea behind a real child, a road years from now seen from behind, a banyan tree of
ancestors' names. Drawings must look like drawings, never like a fake memory.

## The rules (non-negotiable)

1. **No AI on real faces.** No generative motion, edits, de-ageing or invented faces on real people, children
   above all. Image-to-video services may refuse photos of children anyway. `tools/vfx/ai_gen.py` refuses edit
   and image-to-video inputs that contain a detectable face.
2. **Composite instead of generating over people.** Cut the person out untouched (`tools/vfx/cutout.py`),
   generate or animate only the background, put the untouched cut-out back on top.
3. **Style transfer keeps likeness or is rejected.** An oil-portrait look on a real photo is allowed only with
   `--allow-face-likeness`, then compare faces before/after by eye and reject any change; lower the strength.
4. **One style across every tool.** Config `style_suffix` (a style sentence + five hex colours) is appended to
   every image and edit prompt automatically (motion prompts stay short and physical), so art from different
   models and days matches.
5. **Quote gate and provenance.** A paid call prints its quote first (`ai_gen.py` without `--go` exits 4), runs with `--go --quoted-providers wavespeed` only after the client's go, and stays under `config.budget_inr`; every
   call is logged to `spend.md` and `out/ai_log.jsonl` (prompt, model, inputs, seed, output). Copy each used
   asset's model and licence into `sources.md`.
6. **Licences and labels.** Check commercial terms per model and host before client work (some image-to-video
   routes have unclear commercial rights; some outputs carry a SynthID watermark). Label synthetic content where
   platform rules, ASCI or the IT Rules require (see `${CLAUDE_PLUGIN_ROOT}/docs/compliance-and-licensing.md`
   sections 1, 3.4 and 4).

## Decision ladder (stop at the first rung that works)

1. **Frame it** with a layout (prints, triptych, portrait, living) and the grade. Most shots end here.
2. **Light and paper**: LampLight, LightLeak, vignette, page drift, ink marks that draw on with the narration.
3. **2.5D living photo**: `python tools/fetch_models.py depth` once, `python tools/vfx/depth.py photo.jpg`, then
   `python tools/vfx/parallax.py film/plates.json` (dolly ≤ 0.08, zoom ≤ 10 % over 5 s, faces still). Best on
   wide shots and landscapes; faces smear at depth edges.
4. **Fix the source**: `straighten.py` for framed portraits and documents shot at an angle; probe and fix
   rotation; use the best frame of a burst.
5. **Composite**: `cutout.py` (u2net_human_seg, Apache-2.0) + a painted or animated background.
6. **AI still** where no camera was: `python tools/vfx/ai_gen.py image <model> out.png "<prompt>" --inr 8`.
7. **AI motion on a plate with no people**: `ai_gen.py video <model> out.mp4 "<motion>" --image plate.png`,
   then `retime.py` (motion interpolation) to fill a longer shot: dreamier than speeding up a still. Look at it
   frame by frame; interpolation smears fast motion and thin lines.

## Prompting (see `references/ai-art-prompts.md`)

Describe medium, composition, light and mood, never "photorealistic memory of <real person>". Ask for 2-3
variants, pick by eye in a still at film size, log the winner. For a recurring object (the family's real
vehicle, house), lock its look from the proof photo in `facts.md` and say it in every prompt (model, colour,
details): a wrong bike in an early test was another customer's bike.

## Quality checks before an asset enters the film

- At film size in a still: edges of cut-outs (hair halo), seams, text artefacts, extra fingers, warped lines.
- Motion plates: watch at full speed and step through frames; no morphing, no flicker, no face.
- Matches the grade and palette; looks like art when it is art.
- Logged in `out/ai_log.jsonl` and `sources.md` with licence and cost.

## Tool notes

- Host model routes and parameters change: read the model page before a run (`<model path>` in ai_gen.py is
  the host's route, e.g. an edit model or an image-to-video model).
- Large uploads can fail with SSL EOF on some hosts: downscale the input (max side ~2048) and retry.
- Open models fetched by `tools/fetch_models.py` are verified by md5: YuNet (MIT) and SFace (Apache-2.0) for
  faces, Depth Anything V2 Small (Apache-2.0) for depth; the Base/Large/Giant depth models are non-commercial.
  Never use bria-rmbg without a commercial licence.

## References

- `references/ai-art-prompts.md`: prompt patterns, style suffix, plate specs, the composite recipe step by step
- `${CLAUDE_PLUGIN_ROOT}/docs/lessons-learned.md` section F
