---
name: marketing-video
description: "Make a marketing video: hook-proof-CTA, captions, claims ledger, pharma and BFSI rules. \"make a reel for the launch\""
user-invocable: true
---

# Marketing video: one message, provable claims, every format, signed off

Everything in the personal-film method still applies (story first, real material over AI, verified facts,
designed sound, QC before delivery). What changes: the viewer owes you nothing and scrolls in 2 seconds, every
claim must be provable, every face and voice needs consent, every sound needs a licence for this use, the
regulator has rules about words and durations, and one film ships as several formats.

## 1. Brief additions (with `video-brief`)

- **Objective and one message**: what the viewer should think, feel, do; one sentence. One CTA.
- **Audience and placement**: who, where (feed, pre-roll, LinkedIn, a doctor's tablet, a branch TV), sound on
  or off, paid or organic, lengths and aspect ratios needed.
- **Brand kit**: logo files, colours, fonts licensed for video, tone of voice, do's and don'ts, past ads.
- **Claims**: every claim the client wants made, with its substantiation and who approves it.
- **Category and regulator**: ASCI for all Indian advertising; pharma (UCPMP 2024, DMR Act, Schedule J); BFSI
  (SEBI, IRDAI, RBI); other markets need local review.
- **People and rights**: who appears or speaks (employees, customers, talent, doctors), consent status, music.
- **Approvals chain**: who signs off script, storyboard, rough cut, final, and compliance; turnaround per round.

## 2. Structure (with `story-design`)

- **Hook (0-3 s)**: the problem, the surprising fact, the outcome, or the customer's face and words; readable
  with sound off; brand cue early (colour, product, logo moment) for recall.
- **Proof**: show, don't claim: the product working, a real customer, a number with its source on screen.
- **Mechanism / why it works** (explainers): one idea per scene, a picture for every abstract word.
- **CTA**: one action, said once, shown long enough to read twice; the end card holds 2-3 s.
- Lengths: 6 s (one idea), 15 s (hook + proof + CTA), 30 s (a small story), 60-90 s (explainer, testimonial),
  2-3 min (brand film). Cut down from the long master; never stretch a short one.
- Write 2-3 hook variants for paid social; same body, different first 3 s.

## 3. Captions and text

Most feed video plays muted: burn in captions (≥ 1/20 of frame height, high contrast, inside the platform's
safe zone: on 1080×1920 keep text in x 108-972, y 288-1248). Language versions per market; complex scripts follow
the typography rules in `storyboard-and-look`. Legal supers: one per frame, max two lines, long enough to read
(ASCI guidance reported > 4 s each), in the language of the claim.

## 4. The claims ledger (`claims.md`, mandatory for any claim)

| # | Claim as said / shown | Shot | Substantiation (document, date) | Approved by (name, role, date) | Required super / disclaimer |
|---|---|---|---|---|---|
A claim without substantiation is cut, not softened. A disclaimer cannot cure a misleading claim.

## 5. Regulated verticals (India first; details and sources in the compliance doc)

- **Pharma, HCP-facing**: within the approved label; paired with full prescribing information (AV material
  supported by printed material); no HCP names or photos in promotion; never an unqualified "safe"; "new" only
  within a year; date of last review; gated distribution to registered practitioners.
- **Pharma, patient/public**: no prescription brand, drug name or product cues; no cure or prevent claims for
  DMR Act / Schedule J conditions; unbranded awareness ending in "consult your doctor"; watch surrogate recall
  (colours, mascots, taglines).
- **Mutual funds**: the exact SEBI risk statement on screen and read in voice-over over at least 5 seconds; no
  indicative yields; performance only in the prescribed format. Check the latest SEBI code before production.
- **IA/RA, brokers**: audible risk statement, registration name and number, no assured returns, no "best" or
  "No. 1", no SEBI logo; celebrities only with prior approval at entity level.
- **Insurance (IRDAI)**: ULIPs not "investment products"; bonuses "not guaranteed"; no ranking claims.
- **Lending (RBI)**: disclosed rates and fees (APR, KFS), no dark patterns.
Run the `compliance-reviewer` agent on script and final; the client's compliance officer signs off in writing
(record in decisions.md). Rules change often: re-check anything marked M or L in
`${CLAUDE_PLUGIN_ROOT}/docs/compliance-and-licensing.md` section 3 before relying on it.

## 6. People, voices, music, AI

- Written, purpose-specific consent from everyone identifiable (capture, AI processing, publication, term,
  territory, withdrawal); parental consent for children (DPDP Act). Talent releases for actors and voices.
- No real person's likeness or voice cloned without their written consent, even with a label.
- Music: licensed library with the licence on file, original, or AI with terms that allow commercial use; never
  a commercial song without sync + master licences. Shorts over 1 min with any Content ID claim are blocked.
- Sound effects: CC0 or commercially licensed only (no personal-use archives).
- AI: label realistic synthetic content (IT Rules in force since 20 Feb 2026; ASCI AI-content guidance effective
  about 29 Dec 2026; platform disclosure toggles; EU AI Act Art. 50 for EU audiences). Keep provider watermarks;
  re-sign C2PA on the final master if the client wants provenance (re-encoding strips it).
- Remotion: an agency or company of 4+ people needs a Company License before client work.

## 7. Brand kit, end cards, supers and exact lengths in the engine

- **Brand kit**: put the brand's licensed font files in `public/fonts/` and map them in `src/theme.ts` (`fonts`
  names `Serif`, `Sans`, `SansB`, `Hand`, `Display`; the template's defaults are Bengali-friendly storybook faces),
  set `c` (paper, ink, accent, ...) to the brand palette, put logos in `public/art/`, and pick the `neutral` or
  `pop` grade. Check one still of every layout before building.
- **End card / logo card**: a `title` shot with `"fixed": 3.0`, `"bg": "black"` or `"page"`, the logo as a
  hand-built component if it is an image (copy `src/chapters/Example.tsx`; `<Img src={staticFile('art/logo.png')}>`).
- **Legal super held N seconds**: a `card` shot (or a text layer in a custom chapter) with `"fixed": N` and
  `"caps": false`; for MF/IA risk statements also put the exact words in script.json so the narration reads them.
  Check the hold with `python tools/qc/where.py` on its start and end times.
- **Exact-length ads**: give every shot `fixed` (or `min`) so `film/timeline.py` prints `TOTAL 15.00 s` / `30.00 s`
  exactly; a timeline ERROR means narration does not fit: cut words, not breaths.
- **Screen recordings**: `"zoom": [1, 1]` (no push, no crop), `living` layout, captions on a band.

## 8. Multi-format delivery

Design the master for the narrowest frame or keep a centred safe zone; make vertical a separate project
(`new_project.py --format vertical`) sharing script, voice and sound; square via `--format square`. Encode with
`tools/deliver/encode.py` presets (`youtube`, `reels`, `broadcast`, `whatsapp`); platform specs in the
compliance doc section 2. Deliver a versions matrix (`references/marketing-formats.md`).

## References

- `references/marketing-formats.md`: hook patterns, lengths and aspect ratios by platform, versions matrix, sign-off sheet
- `${CLAUDE_PLUGIN_ROOT}/docs/compliance-and-licensing.md`: licences, platform specs, ASCI, pharma, BFSI, AI labels
- agent `compliance-reviewer`
