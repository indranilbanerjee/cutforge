# CutForge user guide

This guide walks through one project from the first request to the screening. You talk to your agent in plain words;
CutForge's skills decide what happens next and the engine does the heavy lifting on your machine.

## 1. Before you start

- Install the plugin (see the README), then make sure the machine has Node 22 or newer, Python 3.10 or newer (3.10 reached end of life on 2026-10-01 and still runs; use 3.11 or newer where you can) and ffmpeg.
- Prove the toolchain once with the demo: "start a CutForge demo project in D:/Films/demo". It scaffolds a project,
  renders a one-minute film from procedural media and verifies every frame. If anything is missing,
  `python tools/setup_local.py` inside the project says exactly what.
- Pick a folder with room. A 20-minute 1080p film needs 15-25 GB of working space.

## 2. The brief (10-20 minutes of your time)

Say what you want: "a 15-minute film for my parents' anniversary from our photos" or "a 60-second brand film for our
launch". CutForge asks one batch of questions: where it will play, who is in the room, the runtime and the deadline,
the language and who narrates, the people who must appear and how the hero addresses them, anything that stays out,
any sensitive period, where the material lives, and the budget for paid tools. Answer what you can; it marks a
recommendation on every choice.

It then creates an `inbox/` with numbered folders, each with a README saying what goes there, which scene it is for,
by when, and how to record it on a phone (hums, songs, ritual sounds, voice notes, location shots, letters).

## 3. The archive pass

CutForge reads your library before writing a word: real capture dates, monthly peaks and quiet stretches, the big days,
places that recur, duplicates, contact sheets of everything, strips of every clip, the real sounds inside the clips, and
face groups. **You name the people; it never guesses.** Everything it plans to use goes onto one photo map.

## 4. The story

You get a one-to-two page treatment: the logline, who tells it, the chapters with their runtimes, three arcs, a hidden
structure said aloud once, motifs, running jokes, and three to five key lines. Approve it or redirect it. An independent
story editor reviews it before you see it.

## 5. The look test

Before the full script, CutForge renders 30-60 seconds of the hardest scene with the real stack, real sound and your
material, and asks one question: is this the level? Iterate here, on a small piece. When the look is right it is written
down as the look bible.

## 6. The storyboard and photo map (one round)

A single page shows every shot with its film time, a still, the narration, the overlays, each photo's date and who is in
it. Anything unconfirmed shows "?". Type corrections into the note column, press "Copy my notes" and paste them back.
This one round replaces twenty scattered questions.

## 7. Voice, art and sound

- **Voice:** an audition page with the same six lines in several voices. Pick by ear on your phone. Every generated line
  is transcribed back and compared with the script; names that come out wrong get a respelling for the engine while the
  captions keep the right spelling. Your own voice can be cloned only with your consent, or recorded and imported.
- **Art:** only where no camera was, never on a real face. Paid generation shows you a quote first (priced from the provider's own page, never from memory), waits for your typed go, and stops at the cap.
- **Sound:** your own clips and recordings first, then licensed libraries, then synthesis. The music is chosen first and
  the picture is cut to its phrases. Every chapter boundary gets a sound bridge.

## 8. The build

The timeline is derived from the measured narration; still sheets are checked; chapters render in resumable chunks;
the grade, the mix and the assembly follow; frame counts and decoding are verified. On a 2-core cloud box 20 minutes of
film takes 5-6 hours; an 8-core desktop with a GPU is 3-5 times faster. A fix re-renders one chapter.

## 9. QC and delivery

Nine QC layers run before you watch: timing, story data, facts, stills, audio, render, a full watch-through, the
playback device, and an independent reviewer. You get a QC report with timestamps. Delivery encodes for the screen it
will play on (projector, YouTube, Reels, WhatsApp, broadcast), moves big files in verified parts, and can hand over the
whole project so any agent can continue on your own machine. A screening run sheet covers the room.

## 10. Revisions

Send notes any way you like: a voice note, a list of timestamps, "it feels abrupt". Each note becomes a row in a NOTES
table, mapped to its shot and its cause. The smallest rebuild is planned and verified, and you get the new timestamps
back. Nothing delivered is overwritten: each round is a new version.

## Marketing, brand and regulated work

For brand films, explainers and ads, CutForge adds the objective and CTA, a hook in the first three seconds, captions
inside each platform's safe zone, a claims ledger, consent and licences, AI labels, multi-format versions and a sign-off
sheet. Pharma and BFSI work runs through the compliance reviewer with UCPMP, DMR Act, SEBI, IRDAI and ASCI rules, with
sources. This is research, not legal advice: the client's compliance owner signs off.
