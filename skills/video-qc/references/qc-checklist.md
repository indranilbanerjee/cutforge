# Pre-delivery checklist

Copy into `out/qc/QC_vN.md` and tick. Anything unticked is either fixed or written down as accepted.

## 1. Facts and story
- [ ] Every named person on screen confirmed by the client (photo map ticked; facts.md says who confirmed, when)
- [ ] Every name spelled as the family writes it; honorifics for the deceased as the family uses them
- [ ] Every date note / stamp matches capture metadata (inventory.csv) or a client statement
- [ ] Every ritual, place and relation named only if the client named it
- [ ] Every quote, verse or proverb has a primary source in sources.md and public-domain status
- [ ] The client's own letters/words set exactly as written
- [ ] Sensitive chapters as decided in decisions.md; no medical, legal or financial detail
- [ ] qc_story: no CHRONOLOGY flags (or flashbacks marked), CAST complete, REUSE intended, RUNTIME on target
- [ ] Plant-payoff list: every plant still pays off after the last edit
- [ ] One version (unless more were asked for); no studio ident or self-promotion in a personal film

## 2. Picture
- [ ] Stills sheets read for every chapter changed since the last QC
- [ ] Faces and text inside the safe area (86 % projector/TV; vertical platform zones)
- [ ] Smallest caption ≥ 1/20 of frame height; on screen long enough to read twice
- [ ] Complex scripts render correctly (conjuncts), no letter-spacing on Indic text
- [ ] No layout collisions; no blank page in page turns; no flash frames
- [ ] No stretched or blur-filled phone media; rotation correct on every clip
- [ ] AI art only where no camera was; no AI on real faces; likeness checks recorded
- [ ] Grade consistent across chapters; blacks lifted for projectors

## 3. Sound
- [ ] timeline.py: 0 ERROR, every short-tail WARN fixed or `hardcut`
- [ ] qc_audio: 0 DROP / CUT TAIL / DEAD AIR (or recorded as intended)
- [ ] Integrated loudness within 1 LU of target (qc_audio flags beyond that); true peak ≤ target
- [ ] Narration intelligible over the bed everywhere (speech-over-bed lowest lines checked by ear)
- [ ] Every chapter boundary bridged; every emotional line followed by a breath
- [ ] Names pronounced correctly; the gen_vo.py summary lists no CHECK or UNVERIFIED lines (or each was heard and accepted)
- [ ] Every sound and music file licensed for this use (sources.md)

## 4. Render and file
- [ ] verify.py --decode OK (frame counts, clean decode)
- [ ] verify.py --final OK (duration, frames, audio stream)
- [ ] Encoded per destination (encode.py preset); file system can hold it (FAT32 < 4 GB)
- [ ] md5 recorded for the master and every delivered copy

## 5. Device and room
- [ ] Played on the delivery device (or the same model) in a similar room, start to finish
- [ ] Edges not cropped after keystone/zoom; text readable from the back of the room
- [ ] Audio level right on that speaker; no hum from cables
- [ ] Backup copy on a second device; 720p backup encode for weak players

## 6. Brand and regulated work (with `compliance-reviewer`)
- [ ] Claims ledger: every claim substantiated and approved
- [ ] Mandatory supers/disclaimers present, legible, for the required duration (and in VO where required)
- [ ] Consent/releases on file for every identifiable person; music sync + master licences
- [ ] AI/synthetic content labelled where required; C2PA/provenance if the client wants it
- [ ] Sign-off recorded (who, role, date) in decisions.md
