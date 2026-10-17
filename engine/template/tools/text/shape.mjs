// Shape Bengali text with HarfBuzz and export each glyph as an SVG path, positioned.
// Lets us animate letters one by one without breaking conjuncts.
import fs from 'fs';
import path from 'path';
import * as hb from 'harfbuzzjs';
const FONTS = path.resolve("public/fonts");
const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = {};
for (const j of jobs) {
  const data = fs.readFileSync(path.join(FONTS, j.font));
  const blob = new hb.Blob(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength));
  const face = new hb.Face(blob);
  const font = new hb.Font(face);
  const upem = face.upem;
  const buf = new hb.Buffer();
  buf.addText(j.text);
  buf.guessSegmentProperties();
  hb.shape(font, buf);
  const infos = buf.getGlyphInfos(), pos = buf.getGlyphPositions();
  let x = 0;
  const glyphs = infos.map((g, i) => {
    const p = pos[i];
    const o = {d: font.glyphToPath(g.codepoint), x: x + p.xOffset, y: p.yOffset, cl: g.cluster, ax: p.xAdvance};
    x += p.xAdvance;
    return o;
  });
  out[j.id] = {text: j.text, font: j.font, upem, width: x, glyphs};
}
fs.writeFileSync(process.argv[3], JSON.stringify(out));
console.log('shaped', Object.keys(out).length);
