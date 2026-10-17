---
name: video-brief
description: "Run the video brief intake: questions, people map, red lines, device, budget, inbox. \"what do you need from me for the video\""
user-invocable: true
---

# Video brief: get the context that decides the film

Most of the expensive mistakes in a story-led video are context mistakes, not craft mistakes: the wrong person
named, a ritual called by the wrong name, a relative left out, a sensitive year handled carelessly, a format the
playback device cannot play. The brief exists to catch these before anything is built.

## How to run the intake

1. Read whatever the client already sent (messages, folders, documents). Do not ask what you can find out.
2. Ask the decision questions below in ONE batch (AskUserQuestion for choices, a short list for facts). Mark
   your recommendation on each choice. Skip anything already answered.
3. Write `brief.md` (full) and the one-screen brief in `PROJECT.md`. Seed `facts.md` with every fact given, each
   with its source ("client, 13 Oct"). Copy the client's hard rules verbatim into PROJECT.md "Hard rules".
4. Create `inbox/` with numbered subfolders and a README in each saying what goes there, used in which scene,
   by when (template: `references/inbox-readme.md`).
5. Read back the one-screen brief to the client and get a yes before phase 2.

For a longer project, make the brief a live **show page** (a published artifact) instead of a long chat: the
one-screen brief, the plan and schedule, every open decision with your recommendation marked, the inbox map,
and an inputs form whose answers are stored where you can read them back (an artifact with a shared database).
Re-publish it as the project moves (treatment, audition, storyboard, previews) so the client always has one place
to look. Copy every answer into facts.md / decisions.md the day it arrives: the page is the interface, the
project folder is the memory.

## The decision questions (by project type in `references/question-bank.md`)

- **Purpose and audience**: who watches, where, together or alone, what they should feel or do after.
  Personal films often have two audiences (children follow faces, sound and jokes; adults follow the story).
- **Playback**: the exact device (projector model, TV, phone, platform), room, speaker. This sets resolution,
  safe areas, caption size, loudness and file system (FAT32 cannot hold files over 4 GB).
- **Runtime and deadline**: target length; the event date; when the client can still give material.
- **Language and voice**: narration language(s), caption language, who or what narrates (stock voice, a
  cloned voice of the client with their consent, the client recording, no narration).
- **Tone references**: two or three films, shows, artists or styles they love, and anything they dislike.
- **People map**: everyone who matters, how the hero addresses each (kinship terms are family-specific),
  correct on-screen spelling, who has passed away and the honorific the family uses, who must appear.
- **Hero objects and places**: the vehicle, house, instrument, school that recur; get the proof photo.
- **Red lines**: topics, years, people or images that stay out (e.g. a period the family wants left out).
- **Sensitive periods**: losses, illness, separations; who decides how they appear (often the partner too).
- **Material**: where every source lives (phone libraries, other family members' phones, pen drives, cloud
  accounts, social media albums with permission), roughly how much, and what is missing.
- **Money**: the cap for paid tools (voice, AI art, music), and whether the client's own subscriptions
  (e.g. an AI Pro plan) can be used. No paid call before an explicit "go ahead".
- **Rights and consent** (client and brand work): who appears and has consented, music licences, brand rules,
  regulated claims. Route to `marketing-video`.
- **Review process**: who approves, how notes come back (timestamps), how many rounds.
- **Their preferences for working**: how they want updates, language register, what annoys them.

## Things that are easy to get wrong (ask, never assume)

- Who is in a photo, even "obviously" the parent: cousins, friends and other families look alike in crowds.
- Which vehicle/house/object is theirs (showrooms, venues and neighbours have similar ones).
- The name of a ceremony or ritual: describe what happened unless the client names it.
- The meaning of a gap in the library: never narrate a reason the client has not given.
- Kinship names, nicknames and their spelling; how to write the hero's name (including invisible characters
  such as joiners in Indic scripts) and how it must be pronounced.
- Dates: use camera metadata, not memory; ask about undated files.
- Whether a quote, verse or proverb is real and in the public domain: verify, never recall.

## Output checklist

- [ ] brief.md written; PROJECT.md one-screen brief and hard rules filled; client said yes
- [ ] facts.md seeded with sources; open questions listed (to batch into the photo map round)
- [ ] inbox/ folders with READMEs; client knows the deadline for their inputs
- [ ] config.json folders set; budget cap recorded; GO_AHEAD.txt NOT created yet
- [ ] delivery device recorded with its limits (resolution, codecs, file system, speaker)

## References
- `references/question-bank.md`: question sets for family, memorial, wedding, brand, explainer, ad, pharma, BFSI
- `references/inbox-readme.md`: the README template for client drop folders, and phone recording guides
