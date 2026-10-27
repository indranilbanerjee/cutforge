// CutForge renderer. One composition per chapter (ids = chapter names in film/shots.json).
// usage: node render.mjs <chapter> <out.mp4|out_%d.jpg> [video|still|chunks] [frames|chunkFrames] [scale]
//   video : whole chapter (or a frame range "a-b") to one file
//   still : frames "0,50,120" -> out_%d.jpg (QC stills)
//   chunks: out_000.mp4, out_001.mp4 ... of chunkFrames each (default 750); chunks already on disk are skipped,
//           so an interrupted render resumes where it stopped.
// Scale: 4th arg, else $SCALE, else timeline format.scale (design 1280x720 x 1.5 = 1920x1080 master).
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition, renderStill} from '@remotion/renderer';
import path from 'path';
import fs from 'fs';

const [,, id, out, mode = 'video', frameArg, scaleArg] = process.argv;
if (!id || !out) { console.error('usage: node render.mjs <chapter> <out> [video|still|chunks] [frames] [scale]'); process.exit(1); }
// PowerShell 5.1 and Notepad write JSON with a byte-order mark, which JSON.parse rejects: strip it.
const readJson = (p) => JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
const cfg = fs.existsSync('config.json') ? readJson('config.json') : {};
const tl = readJson('src/timeline.json');
const scale = Number(scaleArg || process.env.SCALE || tl.format?.scale || 1.5);
// Browser: $REMOTION_BROWSER > config.browser_executable > a known cloud headless shell > Remotion's own download.
const cloudShell = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const BROWSER = process.env.REMOTION_BROWSER || cfg.browser_executable || (fs.existsSync(cloudShell) ? cloudShell : null);
// GL: 'angle' (GPU) on Windows/macOS desktops; 'swiftshader' (CPU) on headless Linux boxes without a GPU.
const chromiumOptions = {gl: process.env.REMOTION_GL || cfg.gl || (process.platform === 'linux' ? 'swiftshader' : 'angle')};
const CONC = Number(process.env.CONC || cfg.concurrency || 2);
const CACHE = 1800 * 1024 * 1024;

const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts'), publicDir: path.resolve('public'),
  symlinkPublicDir: process.platform !== 'win32'});   // Windows copies public/ into the bundle: slow start with big media, normal
const composition = await selectComposition({serveUrl, id, browserExecutable: BROWSER, chromiumOptions});
const t0 = Date.now();
const common = {composition, serveUrl, browserExecutable: BROWSER, chromiumOptions};

if (mode === 'still') {
  for (const fr of (frameArg || '0').split(',').map(Number)) {
    await renderStill({...common, output: out.replace('%d', String(fr)), frame: Math.min(fr, composition.durationInFrames - 1),
      imageFormat: 'jpeg', jpegQuality: 88, scale});
  }
} else if (mode === 'chunks') {
  const N = composition.durationInFrames, CH = Number(frameArg || 750);
  for (let k = 0, a = 0; a < N; k++, a += CH) {
    const part = out.replace('.mp4', `_${String(k).padStart(3, '0')}.mp4`);
    if (fs.existsSync(part)) continue;
    const b = Math.min(N - 1, a + CH - 1), t1 = Date.now();
    await renderMedia({...common, codec: 'h264', outputLocation: part + '.tmp.mp4', concurrency: CONC, crf: 14, x264Preset: 'medium',
      muted: true, scale, frameRange: [a, b], offthreadVideoCacheSizeInBytes: CACHE});
    fs.renameSync(part + '.tmp.mp4', part);
    console.log(`chunk ${k} [${a}-${b}] ${((Date.now() - t1) / 1000).toFixed(0)}s`);
  }
} else {
  let last = -1;
  await renderMedia({...common, codec: 'h264', outputLocation: out, concurrency: CONC, crf: 14, x264Preset: 'medium', muted: true, scale,
    offthreadVideoCacheSizeInBytes: CACHE, frameRange: frameArg && frameArg !== '-' ? frameArg.split('-').map(Number) : undefined,
    onProgress: ({progress}) => { const p = Math.round(progress * 100); if (p !== last && p % 10 === 0) { last = p; console.log(`${p}% ${((Date.now() - t0) / 1000).toFixed(0)}s`); } }});
}
console.log('done', ((Date.now() - t0) / 1000).toFixed(1), 's');
