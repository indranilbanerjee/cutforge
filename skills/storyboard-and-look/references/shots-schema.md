# film/shots.json schema

```json
{
  "title": "Film title",
  "format": {"w": 1280, "h": 720, "fps": 25, "scale": 1.5},
  "chapters": [
    {"name": "e1", "span": ["2023-01", "2023-10"], "order": "chronological", "fadeIn": 0.6, "fadeOut": 1.2,
     "shots": [ { "id": "6A", "vo": ["6A"], "pre": 0.8, "post": 1.4, "layout": "living", "media": ["media/x.jpg"] } ]}
  ]
}
```
`format`: the design canvas (layouts are written for it) and `scale` (render multiplier: 1280×720 × 1.5 =
1920×1080). Landscape 1280×720@25, vertical 720×1280@30, square 1080×1080@30 (`new_project.py --format`).

## Chapter keys

| Key | Meaning |
|---|---|
| `name` | composition id: letters, digits and hyphens only; one render unit (keep chapters 1-3 minutes so a fix re-renders one) |
| `span` | `["YYYY-MM", "YYYY-MM"]` capture-date window; `qc_story.py` flags assets outside it |
| `order` | `"chronological"` makes `qc_story.py` flag dates that run backwards |
| `fadeIn`, `fadeOut` | seconds from/to black at the chapter's edges |
| `custom` | not needed: a chapter whose name is in `src/chapters/index.ts` is hand-built; others use AutoChapter |

## Shot timing keys (read by film/timeline.py)

| Key | Meaning | Default |
|---|---|---|
| `id` | shot id, unique in the chapter; narration ids usually derive from it | required |
| `vo` | list of script line ids spoken in this shot, in order | `[]` |
| `pre` | seconds before the first line | 0.6 |
| `gaps` | seconds between lines: one number or a list (one per gap) | 0.5 |
| `post` | seconds after the last line (≥ 0.6, longer after emotion) | 0.9 |
| `min` | minimum shot length (for slow pictures with short lines) | none |
| `fixed` | exact length; ERROR if the narration does not fit | none |
| `hardcut` | `true` silences the short-tail warning for an intended hard cut | false |
| `flashback` | `true` exempts the shot from the chapter's chronological-order check (read by qc_story.py) | false |

## Shot layout keys (AutoChapter; passed through as the shot's `spec`)

| Key | Layouts | Meaning |
|---|---|---|
| `layout` | all | `living`, `portrait`, `prints`, `triptych`, `title`, `card`, `page`, `black` |
| `media` | living, portrait, prints, triptych | list of paths under `public/` or objects `{"src", "from", "rate", "pos", "bw", "portrait"}` (`from` = start second in a clip, `pos` = CSS object-position, `portrait: true` = tall print) |
| `zoom` | living, portrait, title media bg | `[z0, z1]` scale over the shot (default `[1.02, 1.1]`; `[1, 1]` for screen recordings; keep ≤ 10 % per 5 s) |
| `drift` | living | `[x0, y0, x1, y1]` pixel offsets over the shot |
| `bw` | living, portrait, prints, triptych | black and white |
| `glow` | living, with `bw: true` | keeps only the bright coloured lights over the B&W picture (lamps at night) |
| `sound` | any with video media | `true` (or a dB number) lays the clip's own audio on the dialogue bus |
| `date` (+`dateAt`) | any | torn-paper date note top-left inside the safe area |
| `stamp` | any | `{"text", "at", "x", "y"}` rubber stamp |
| `lower` | any | `{"name", "role", "at", "until", "x", "y"}` name tag (position optional) |
| `xfade` | any | dissolve from the previous shot (s) |
| `fadeIn`, `fadeOut` | any | from/to black at this shot's edges (s) |
| `caps` | any | `false` hides narration captions |
| `capsMode` | any | `film` (band at the bottom) or `paper` (ink on the page); default by layout |
| `printAt`, `printGap` | prints | first print lands at (s), then every gap (s) |
| `dim` | prints, card, page | darken the page (0-1) |
| `text`, `sub` | title, card | title text (+ subtitle); card takes a list of lines |
| `bg` | title, portrait | `page` (default) or `black`; a title also takes a media path / object |
| `titleAt`, `inkTitle`, `size`, `font`, `color` | title (`size` and `font` also on card: default 40, 54 on vertical) | timing, shaped-glyph title id (`src/glyphs.json`), size, font family name from `src/theme.ts`, colour |
| `lineAt`, `lineGap` | card | first handwritten line at (s), then every gap (s) |

Unknown keys pass through to the spec, so hand-built chapters can read their own options.

## Examples

```json
{"id": "2A", "vo": ["2A"], "pre": 0.8, "post": 1.4, "layout": "prints",
 "media": ["media/hills.jpg", {"src": "media/portrait.jpg", "portrait": true}, "media/sea.jpg"],
 "stamp": {"text": "2024", "at": 2.6}}
{"id": "2B", "vo": ["2B"], "layout": "triptych", "sound": true,
 "media": [{"src": "media/a.mp4", "from": 3.2}, "media/b.mp4", "media/c.mp4"]}
{"id": "1T", "fixed": 4.0, "layout": "title", "bg": "black", "inkTitle": "demo_title", "size": 110, "caps": false}
{"id": "3A", "vo": ["3A"], "pre": 2.6, "post": 3.4, "layout": "card",
 "text": ["Law 1: shoes are optional.", "Law 2: so is sleep."], "lineAt": 0.4, "lineGap": 0.8, "capsMode": "paper"}
```

## Hand-built chapter pattern

```tsx
const {vo, voEnd, dur} = useShot('e2', '7D');        // frames, from the measured narration
<Print ... t0={vo(0)} />                               // lands as line 0 starts
<Doodle ... t0={voEnd(0) - 10} />                      // circles it as the line ends
<Stamp ... t0={vo(1) + 4} />
```
Register the component in `src/chapters/index.ts`; the chapter's shots still come from shots.json (timing),
only the picture is custom. Copy `src/chapters/Example.tsx` (including the static "final page" used by a page
turn) rather than starting from nothing.
