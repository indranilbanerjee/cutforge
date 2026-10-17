# AI art: prompts, style, plates and composites

## The style suffix (config.json "style_suffix")

One sentence of medium and mood plus five hex colours, appended to every image and edit prompt by `ai_gen.py`
(not to motion prompts):

```
"style_suffix": "Hand-painted storybook illustration, soft gouache on textured paper, warm lamp light, gentle
grain, no text, no people's faces. Palette: #F2E6CF #C8553D #2E4A62 #E8B04B #3B3A30."
```
Brand work: the brand's colours and illustration style; check it on three test prompts before any real one.

## Prompt pattern

```
<subject and place>, <composition: wide / low angle / from behind / centred with headroom>,
<time and light>, <movement implied>, <medium>, <what must NOT appear>
```
Examples (no real faces anywhere):
- "A country road at dusk seen from behind a motorbike, two riders as small dark silhouettes far ahead, paddy
  fields, wide, low sun, long shadows, painted" (the future the film looks forward to).
- "A great banyan tree whose aerial roots form a family tree, small blank leaf-shaped labels on branches, ink
  and wash" (names are added in the film, never generated as text).
- "A calm sea at golden hour with gentle waves, empty beach, wide, painterly" (the background plate for a
  composite).
Generated text is always wrong in complex scripts: generate blank labels and set text in the film.

## Motion prompts (image-to-video on a plate with no people)

Small, physical, slow: "waves roll in gently, light shimmers, clouds drift slowly; camera still". Avoid camera
moves the parallax tool can do better. 5 s clips are cheapest; `retime.py --factor 2` makes 10 s.

## The composite recipe (real person, painted world)

1. `python tools/vfx/cutout.py public/media/child_sea.jpg --model u2net_human_seg` → cut-out PNG (untouched).
2. Make the background without the person: an edit model asked to "remove the person and extend the sea" on a
   copy, or a new painted plate matched in light and horizon (`ai_gen.py edit ... --image bg_only.jpg`; the face
   guard blocks inputs that still contain a face).
3. Animate the background plate only (`ai_gen.py video ...`), retime to the shot length.
4. In a custom chapter: background video looped/slowed, then the cut-out `<Img>` on top, a soft shadow, the grade
   over both. Check the hair edge at full size; feather 1-2 px if it halos.

## Living photo plate spec (film/plates.json for tools/vfx/parallax.py)

```json
[{"id": "p_hills", "src": "hills", "dur": 6.0, "c0": [0.5, 0.45], "c1": [0.52, 0.45],
  "z0": 1.0, "z1": 1.06, "dolly0": 0.0, "dolly1": 0.05, "sx0": 0.0, "sx1": 0.015, "f0": 0.7, "f1": 0.7, "dof": 0.0,
  "ease": "inout"}]
```
`src` is the stem of `public/media/<stem>.jpg` with `<stem>_depth.png` beside it (from `depth.py`). Use the plate
as a `living` shot's media: `"media": ["plates/p_hills.mp4"]`.

## Style transfer on a real photo (only with consent and a likeness check)

`ai_gen.py edit <model> out.jpg "oil painting in the style of a 19th-century portrait, same pose, same face"
--image in.jpg --allow-face-likeness`, low strength if the model has one. Put original and result side by side
at full size; if eyes, nose, mouth, face shape or skin tone changed at all, reject. Tell the client it is a
painting of their photo.

## Spend discipline

Estimate per asset (images are cheap, video seconds are not), batch prompts so one approval covers a set, and
stop at the cap. A whole 20-minute film's art and voice stayed at about two-thirds of its cap because generation was
reserved for the shots with no camera.
