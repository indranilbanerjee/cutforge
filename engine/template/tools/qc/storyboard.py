"""Storyboard and photo map as ONE self-contained HTML page, built from the same data the film is built from
(film/timeline.json + film/script.json), so the page the client reviews can never drift from the cut.

Per shot: film time, chapter/shot, length, layout, a picture (a QC still from out/qc if one exists inside the shot,
else a thumbnail of each media file), the narration lines with their direction, sound/text overlays, and, when the
data exists, each asset's capture date (out/archive/inventory.csv) and who is in it (film/people_in_media.json).
Anything not confirmed shows "?" so a belief is never presented as a fact. Use it for:
  - the storyboard review (phase 5) and the one-round photo map (every asset, who, when, open questions)
  - a revision round: send it with the new timestamps
usage: python tools/qc/storyboard.py [--chapters intro,e1] [--thumb 220] [--out out/storyboard/index.html]
Publish the HTML as an artifact or send the file; it embeds its thumbnails (no external files), so keep it private: it
shows the client's photos. The note column is saved in the viewer's browser; "Copy my notes" gives them a text block
(shot id + time + note) to paste back to you. For a team review, ask for "row id: note" replies instead."""
import os, sys, csv, json, html, base64, io, glob, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from paths import ROOT, FILM, OUT, PUBLIC, CFG, load_json

a = sys.argv[1:]
def opt(name, d=None):
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else d

TL = load_json(os.path.join(FILM, 'timeline.json'))
if TL is None: sys.exit('no film/timeline.json: run python film/timeline.py first')
SC = load_json(os.path.join(FILM, 'script.json'), {'lines': []})
LINES = {l['id']: l for l in SC.get('lines', [])}
PEOPLE = load_json(os.path.join(FILM, 'people_in_media.json'), {}) or {}
FPS = TL.get('format', {}).get('fps', 25)
TW = int(opt('--thumb', 220))
ONLY = set(opt('--chapters', '').split(',')) - {''}
OUTF = os.path.join(ROOT, opt('--out', os.path.join('out', 'storyboard', 'index.html')))

dates = {}
inv = os.path.join(OUT, 'archive', 'inventory.csv')
if os.path.exists(inv):
    for r in csv.DictReader(open(inv, encoding='utf-8')):
        if r.get('date'):
            dates[os.path.splitext(os.path.basename(r['path']))[0].lower()] = (r['date'][:16], r.get('date_src', ''))


def mmss(t):
    t = max(0.0, t); return f'{int(t // 60)}:{t % 60:04.1f}'


def b64img(im):
    from PIL import Image
    im = im.convert('RGB'); im.thumbnail((TW, TW))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=72)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def thumb(src, at=0.0):
    from PIL import Image, ImageOps
    p = os.path.join(PUBLIC, src)
    if not os.path.exists(p): return None
    try:
        if src.lower().endswith(('.mp4', '.mov', '.m4v', '.webm')):
            r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{at + 0.5:.2f}', '-i', p, '-frames:v', '1',
                                '-vf', f'scale={TW}:-2', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'], capture_output=True)
            if not r.stdout: return None
            return b64img(Image.open(io.BytesIO(r.stdout)))
        return b64img(ImageOps.exif_transpose(Image.open(p)))
    except Exception:
        return None


def qc_still(chapter, s):
    """the QC still (tools/qc/stills.py) nearest 60 % into the shot (past any fade-in), if one was rendered"""
    best, bd = None, 1e9
    f0, f1 = s['start'] * FPS, (s['start'] + s['dur']) * FPS
    mid = f0 + 0.6 * (f1 - f0)
    for f in glob.glob(os.path.join(OUT, 'qc', f'{chapter}_[0-9]*.jpg')):
        try: fr = int(os.path.splitext(os.path.basename(f))[0].rsplit('_', 1)[1])
        except ValueError: continue
        if f0 <= fr < f1 and abs(fr - mid) < bd: best, bd = f, abs(fr - mid)
    if not best: return None
    from PIL import Image
    return b64img(Image.open(best))


rows, n_assets, n_open = [], 0, 0
for c in TL['chapters']:
    if ONLY and c['name'] not in ONLY: continue
    span = (c.get('spec') or {}).get('span')
    rows.append(f'<tr class="ch"><td colspan="6"><b>{html.escape(c["name"])}</b> · starts {mmss(c["start"])} · '
                f'{c["dur"]:.1f} s' + (f' · span {html.escape(" to ".join(span))}' if span else '') + '</td></tr>')
    for s in c['shots']:
        sp = s.get('spec') or {}
        media = [m if isinstance(m, dict) else {'src': m} for m in sp.get('media', [])]
        bg = sp.get('bg')
        if isinstance(bg, (str, dict)) and bg not in ('page', 'black'):
            media = [bg if isinstance(bg, dict) else {'src': bg}] + media
        pics = []
        still = qc_still(c['name'], s)
        if still: pics.append(f'<figure><img src="{still}"><figcaption>render still</figcaption></figure>')
        assets = []
        for m in media:
            n_assets += 1
            stem = os.path.splitext(os.path.basename(m['src']))[0].lower()
            d = dates.get(stem)
            who = PEOPLE.get(m['src']) or PEOPLE.get('media/' + os.path.basename(m['src']))
            if not who: n_open += 1
            info = (f'{html.escape(os.path.basename(m["src"]))}<br>'
                    f'date: {html.escape(d[0]) + (" (" + html.escape(d[1]) + ")" if d[1] else "") if d else "?"}<br>'
                    f'who: {html.escape(", ".join(who)) if who else "?"}'
                    + (f'<br>from {m["from"]} s' if m.get('from') else ''))
            assets.append(info)
            if not still:
                t = thumb(m['src'], float(m.get('from', 0) or 0))
                pics.append(f'<figure>' + (f'<img src="{t}">' if t else '<div class="miss">missing</div>') +
                            f'<figcaption>{html.escape(os.path.basename(m["src"]))}</figcaption></figure>')
        texts = []
        for k in ('text', 'sub'):
            v = sp.get(k)
            if v: texts.append(' / '.join(v) if isinstance(v, list) else str(v))
        for k in ('date', ):
            if sp.get(k): texts.append(f'date note: {sp[k]}')
        if sp.get('stamp'): texts.append(f'stamp: {sp["stamp"].get("text", "")}')
        if sp.get('lower'): texts.append(f'name tag: {sp["lower"].get("name", "")} {sp["lower"].get("role", "")}')
        vo = []
        for lid, at, d in s.get('vo', []):
            L = LINES.get(lid, {})
            vo.append(f'<div class="vo"><span class="t">{mmss(c["start"] + s["start"] + at)}</span> '
                      f'<b>{html.escape(lid)}</b> {html.escape(L.get("text", "?"))}'
                      + (f' <i>({html.escape(L["dir"])})</i>' if L.get('dir') else '')
                      + (f'<div class="en">{html.escape(L["en"])}</div>' if L.get('en') else '') + '</div>')
        flags = []
        if sp.get('sound'): flags.append('clip sound')
        if sp.get('bw'): flags.append('b&w')
        if sp.get('hardcut'): flags.append('hard cut')
        if sp.get('xfade'): flags.append(f'dissolve {sp["xfade"]} s')
        rows.append(
            f'<tr id="{html.escape(c["name"])}-{html.escape(s["id"])}"><td class="tm">{mmss(c["start"] + s["start"])}<br>'
            f'<small>{s["dur"]:.1f} s</small></td>'
            f'<td><b>{html.escape(s["id"])}</b><br><small>{html.escape(sp.get("layout") or ("custom" if not media else "living"))}</small>'
            f'{"<br><small>" + ", ".join(flags) + "</small>" if flags else ""}</td>'
            f'<td class="pics">{"".join(pics)}</td>'
            f'<td>{"".join(vo) or "<span class=dim>no narration</span>"}'
            f'{"<div class=txt>" + "<br>".join(html.escape(x) for x in texts) + "</div>" if texts else ""}</td>'
            f'<td class="as">{"<hr>".join(assets) or "<span class=dim>none</span>"}</td>'
            f'<td class="q" contenteditable="true" data-k="{html.escape(c["name"])}/{html.escape(s["id"])} {mmss(c["start"] + s["start"])}"></td></tr>')

title = html.escape(CFG.get('title') or TL.get('title') or 'Film')
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} storyboard</title><style>
:root{{--bg:#f6f1e7;--fg:#2a2420;--dim:#8a8178;--line:#d9cfbf;--ch:#ebe2d2;--acc:#a0522d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#1d1a17;--fg:#ece4d8;--dim:#9a9086;--line:#3a332c;--ch:#2a251f;--acc:#e0a070}}}}
:root[data-theme=dark]{{--bg:#1d1a17;--fg:#ece4d8;--dim:#9a9086;--line:#3a332c;--ch:#2a251f;--acc:#e0a070}}
body{{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,"Noto Sans Bengali","Noto Sans Devanagari",sans-serif;margin:0;padding:16px}}
h1{{font-size:20px;margin:0 0 4px}} p.meta{{color:var(--dim);margin:0 0 14px}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;min-width:860px}}
td{{border-top:1px solid var(--line);padding:8px;vertical-align:top}} tr.ch td{{background:var(--ch);font-size:15px}}
.tm{{white-space:nowrap;color:var(--acc);font-variant-numeric:tabular-nums}} .pics{{width:{TW + 16}px}}
figure{{margin:0 0 6px}} img{{max-width:{TW}px;border-radius:4px;display:block}} figcaption,small,.dim{{color:var(--dim);font-size:12px}}
.miss{{width:{TW}px;height:80px;display:grid;place-items:center;border:1px dashed var(--line);color:var(--dim)}}
.vo{{margin-bottom:6px}} .vo .t{{color:var(--dim);font-size:12px;font-variant-numeric:tabular-nums}} .en{{color:var(--dim);font-size:12px}}
.txt{{margin-top:6px;padding:6px;border-left:3px solid var(--acc);font-size:13px}} .as{{font-size:12px;width:190px}}
.q{{min-width:150px;background:rgba(160,82,45,.06)}} .bar{{margin:0 0 10px}}
button{{font:inherit;padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--ch);color:var(--fg);cursor:pointer}}
#out{{display:none;width:100%;min-height:90px;margin:0 0 10px;font:13px ui-monospace,monospace;background:var(--bg);color:var(--fg);border:1px solid var(--line)}} .q:empty:before{{content:"note / correction";color:var(--dim);font-size:12px}}
</style></head><body><h1>{title}: storyboard and photo map</h1>
<p class="meta">{len([r for r in rows if 'class="ch"' not in r])} shots · {mmss(TL["total"])} · {n_assets} assets ·
{n_open} assets with no confirmed people (marked ?). Built from film/timeline.json; times are film times.</p>
<div class="bar"><button id="cp">Copy my notes</button> <span id="st" class="dim">Type corrections in the last column; they stay in
this browser. Then press the button and paste the notes back in the chat.</span></div>
<textarea id="out" readonly></textarea>
<div class="wrap"><table>{"".join(rows)}</table></div>
<script>
const K = 'ff-notes:' + location.pathname;
let saved = {{}}; try {{ saved = JSON.parse(localStorage.getItem(K) || '{{}}'); }} catch (e) {{}}
document.querySelectorAll('td.q').forEach(td => {{
  if (saved[td.dataset.k]) td.textContent = saved[td.dataset.k];
  td.addEventListener('input', () => {{ saved[td.dataset.k] = td.textContent.trim();
    try {{ localStorage.setItem(K, JSON.stringify(saved)); }} catch (e) {{}} }});
}});
document.getElementById('cp').onclick = () => {{
  const lines = [...document.querySelectorAll('td.q')].filter(td => td.textContent.trim())
    .map(td => td.dataset.k + ': ' + td.textContent.trim());
  const txt = lines.length ? lines.join('\\n') : '(no notes yet)';
  const o = document.getElementById('out'); o.value = txt; o.style.display = 'block'; o.select();
  try {{ navigator.clipboard.writeText(txt).then(() => document.getElementById('st').textContent = 'Copied ' + lines.length + ' notes.'); }} catch (e) {{}}
}};
</script></body></html>'''
os.makedirs(os.path.dirname(OUTF), exist_ok=True)
open(OUTF, 'w', encoding='utf-8').write(page)
print(f'storyboard: {os.path.relpath(OUTF, ROOT)} ({len(page) // 1024} KB, {n_assets} assets, {n_open} without confirmed people)')
