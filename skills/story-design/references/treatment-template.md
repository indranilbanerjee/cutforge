# Treatment template (one to two pages; the client reads this, so plain language)

```
# <Title>: treatment v1

Logline: <one sentence about something, not a period>
Runtime: <target> · Language: <narration / captions> · Plays on: <device, room, audience>

## The frame
Who tells it: <narrator character + casting brief | parent's voice | interviews | captions only>
Title idea: <what the title means; how and when it appears>
Two audiences: <what the children get> / <what the adults get>

## Structure
| # | Chapter | Runtime | What happens | First image | Last image | Music / sound |
|---|---|---|---|---|---|---|
| 0 | Open | 1:30 | ... | ... | ... | ... |

Hidden spine: <structure said aloud once, where>
Arcs: A <place/group: from → to> · B <hero: from → to> · C <teller: from → to>
Motifs: <sound / object / colour> · Running jokes: <joke: step 1 → step 2 → step 3>

## Plants and payoffs
| Plant (shot) | Payoff (shot) | Notes |
|---|---|---|

## Beat map (every 45-60 s something for the youngest viewer)
| Time | For kids | For adults |
|---|---|---|

## Key lines (narration language + working translation)
1. <line> / <translation>

## Sensitive material and exclusions
<what, proposed treatment, who decides>   (decisions go into decisions.md)

## Open questions (batched into the photo-map round)
- ...
```

# Story-order table (`story_order.md`; the evidence behind the order)

```
| Chapter | Beat | Shot | Asset | Capture date (source) | People (confirmed?) | Place | Notes |
|---|---|---|---|---|---|---|---|
| e1 | first steps | 6B | media/20230403_1230.jpg | 2023-04-03 12:30 (EXIF) | hero, grandmother (yes) | home | |
| e1 | the bike arrives | 6J | media/20230512_1800.mp4 | 2023-05-12 (container) | father? | showroom | proof photo: key handover |
```

Rules: dates from `out/archive/inventory.csv`; "?" for anything unconfirmed; every row's chapter span matches
the `span` in `film/shots.json`; any row that breaks order is either moved or marked as an intended
flashback in `decisions.md`.

# script.json line format

```json
{"id": "7Da", "text": "<line in the narration language>", "dir": "slow, tender", "en": "<working translation>"}
```
`dir` words the voice tool understands for pace: slow, tender, warm, plain, brisk, comic, list, whisper (see
`voice-and-narration`). One line per breath; split long sentences into `a`, `b` lines with a `gaps` value
between them in shots.json.
