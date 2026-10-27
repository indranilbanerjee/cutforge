// Shape Bengali text with HarfBuzz and export each glyph as an SVG path, positioned.
// Lets us animate letters one by one without breaking conjuncts.
// usage: node tools/text/shape.mjs <jobs.json> <out.json>     (tools/text/shapeall.sh runs it with the project's files)
import fs from 'fs';
import path from 'path';

const argv = process.argv.slice(2);
if (argv.some((a) => a === '-h' || a === '--help')) {
  console.log(fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').filter((l) => l.startsWith('//')).map((l) => l.replace(/^\/\/ ?/, '')).join('\n').trim());
  process.exit(0);
}
if (argv.find((a) => a.startsWith('--'))) { console.error(`shape.mjs: unknown option ${argv.find((a) => a.startsWith('--'))}; run it with --help`); process.exit(2); }
if (argv.length < 2) { console.error('usage: node tools/text/shape.mjs <jobs.json> <out.json>'); process.exit(2); }
const hb = await import('harfbuzzjs');
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
