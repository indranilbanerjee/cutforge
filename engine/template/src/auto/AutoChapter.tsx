// AutoChapter: renders a whole chapter from film/shots.json, no code needed. Each shot picks a layout:
//   living    full-frame photo/clip with slow push (media[0])        portrait  phone photo/clip whole, on the page or black (bg)
//   prints    1 to 3 prints land on a paper page (media[0..2])      triptych  three vertical clips side by side
//   title     big title (+ sub) over page, black or media             card      handwritten lines on a page
//   page      empty paper page (for custom overlays later)            black     black frame (breath, act break)
// Common shot options: zoom [z0,z1], drift [x0,y0,x1,y1], bw, glow, date (torn-paper note), stamp {text, at},
// lower {name, role, at, until}, xfade (s, dissolve from previous shot), fadeIn / fadeOut (s, from/to black),
// caps (false hides narration captions), capsMode ('film' | 'paper').
// Write a custom component in src/chapters/ only for scenes that need choreography beyond these.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {W, H, s2f, clamp, EASE, spr, useFonts, Fill} from '../lib/core';
import {chap, ShotT, MediaItem} from '../lib/timeline';
import {Shot, Caps, CapBand, Living, PortraitFrame, Page, Print, Triptych, Hand, Stamp, StampDefs, DateNote, LowerThird, DissolveIn, FadeIn, FadeOut, Vignette, norm, Media, BW} from '../lib/kit';
import {InkDefs, InkText} from '../lib/ink';
import {THEME} from '../theme';

const sec = (x: any, d = 0) => (typeof x === 'number' ? x : d);

const printBoxes = (n: number, portraits: boolean[]) => {
  // prints stay inside the 86 % safe area: usable band = 84 % of the frame, split into n slots
  const vertical = H > W;
  const boxes: {x: number; y: number; w: number; h: number; rot: number}[] = [];
  const UW = W * 0.84, UH = H * 0.80, X0 = W * 0.08, Y0 = H * 0.08;
  for (let k = 0; k < n; k++) {
    const pt = portraits[k];
    const rot = n === 1 ? -1.5 : [-4, 3, -2][k];
    let w: number, h: number, x: number, y: number;
    if (vertical) {
      // vertical: prints stay in the platform-safe band above the captions (y 16-52 %), zigzag and overlap a little
      const VY0 = H * 0.16, VUH = H * 0.36, slotH = VUH / n;
      h = slotH * (n > 1 ? 1.08 : 0.95); w = pt ? h / 1.42 : h / 0.66;
      if (w > UW * 0.9) { w = UW * 0.9; h = pt ? w * 1.42 : w * 0.66; }
      x = X0 + (UW - w) / 2 + (n > 1 ? (k % 2 ? W * 0.07 : -W * 0.07) : 0); y = VY0 + k * slotH + (slotH - h) / 2;
    } else {
      const slotW = UW / n;
      w = Math.min(slotW * 0.9, (pt ? 0.5 : 0.9) * UW / Math.max(1, n === 1 ? 1.4 : 1)); h = pt ? w * 1.42 : w * 0.66;
      if (h > UH * 0.9) { h = UH * 0.9; w = pt ? h / 1.42 : h / 0.66; }
      x = X0 + k * slotW + (slotW - w) / 2; y = Y0 + (UH - h) / 2 - 14 + (k % 2 ? 22 : -8);
    }
    boxes.push({x, y, w, h, rot});
  }
  return boxes;
};

const ShotBody: React.FC<{c: string; s: ShotT; head: number; total: number}> = ({c, s, head, total}) => {
  const f = useCurrentFrame() - head;          // shot-local frame (0 = the shot's own start)
  const sp = s.spec || {};
  const media: MediaItem[] = sp.media || [];
  const lay: string = sp.layout || (media.length ? 'living' : 'black');
  const m0 = media.length ? norm(media[0]) : null;
  const zoom: [number, number] = sp.zoom || [1.02, 1.1];
  const drift: [number, number, number, number] = sp.drift || [0, 0, 0, 0];
  let body: React.ReactNode = null;
  let paper = false;

  if (lay === 'living' && m0) {
    body = <Living src={m0.src} from={m0.from} rate={m0.rate} pos={m0.pos} dur={total} z={zoom} o={drift} bw={sp.bw || m0.bw} glow={sp.glow} />;
  } else if (lay === 'portrait' && m0) {
    paper = (sp.bg || 'page') === 'page';
    body = <PortraitFrame src={m0.src} from={m0.from} dur={total} bw={sp.bw || m0.bw} z={sp.zoom || [1.0, 1.03]} bg={paper ? 'page' : 'black'} />;
  } else if (lay === 'triptych') {
    body = <Triptych items={media} t0={head} bw={sp.bw} />;
  } else if (lay === 'prints') {
    paper = true;
    const items = media.slice(0, 3).map(norm);
    const boxes = printBoxes(items.length, items.map((m) => !!m.portrait));
    body = <Page dur={total} dim={sp.dim || 0}>
      {items.map((m, k) => <Print key={k} {...boxes[k]} src={m.src} from={m.from} rate={m.rate} pos={m.pos} bw={sp.bw || m.bw}
        t0={head + s2f(sec(sp.printAt, 0.3) + k * sec(sp.printGap, 0.9))} enter={k % 2 ? 'right' : 'drop'} dur={total} />)}
    </Page>;
  } else if (lay === 'title') {
    const bg = sp.bg || 'page';
    paper = bg === 'page';
    const p = spr(f, s2f(sec(sp.titleAt, 0.4)), {damping: 18, stiffness: 90});
    const q = spr(f, s2f(sec(sp.titleAt, 0.4) + 0.8), {damping: 18, stiffness: 90});
    const ink = paper ? THEME.c.ink : THEME.c.cream;
    const title = sp.inkTitle
      ? <InkText id={sp.inkTitle} x={W / 2} y={H * 0.5} size={sp.size || 96} t0={head + s2f(sec(sp.titleAt, 0.4))} align="center" fill={sp.color || ink} />
      : <div style={{position: 'absolute', left: 60, right: 60, top: H * 0.42, textAlign: 'center', transform: `translateY(${(1 - p) * 24}px)`, opacity: clamp(p * 1.5),
          fontFamily: sp.font || 'Display', fontSize: sp.size || 88, lineHeight: 1.15, color: sp.color || (paper ? THEME.c.accent : THEME.c.cream),
          textShadow: paper ? 'none' : '0 4px 24px rgba(0,0,0,0.6)'}}>{sp.text}</div>;
    body = <>
      {bg === 'page' ? <Page dur={total} /> : bg === 'black' ? <Fill style={{background: '#000'}} />
        : <><Living src={norm(bg).src} from={norm(bg).from} dur={total} z={zoom} bw={sp.bw} /><Vignette amt={0.6} /></>}
      {title}
      {sp.sub && <div style={{position: 'absolute', left: 60, right: 60, top: H * 0.42 + (sp.size || 88) * 1.35, textAlign: 'center', opacity: clamp(q * 1.5),
        fontFamily: 'Serif', fontSize: (sp.size || 88) * 0.36, color: paper ? THEME.c.ink : THEME.c.cream}}>{sp.sub}</div>}
    </>;
  } else if (lay === 'card') {
    paper = true;
    const lines: string[] = Array.isArray(sp.text) ? sp.text : [sp.text || ''];
    const size = sp.size || (H > W ? 54 : 40);                       // vertical: bigger, and centred above the captions
    const lh = size * 1.6, top = (H > W ? H * 0.36 : H / 2) - (lines.length * lh) / 2;
    body = <Page dur={total} dim={sp.dim || 0}>
      {lines.map((t, k) => <Hand key={k} text={t} x={W / 2} y={top + k * lh} size={size} align="center" w={W - 160}
        t0={head + s2f(sec(sp.lineAt, 0.5) + k * sec(sp.lineGap, 1.1))} font={sp.font || 'Hand'} />)}
    </Page>;
  } else if (lay === 'page') {
    paper = true;
    body = <Page dur={total} dim={sp.dim || 0} />;
  } else {
    body = <Fill style={{background: '#000'}} />;
  }

  const capsMode = sp.capsMode || (paper ? 'paper' : 'film');
  return (
    <Fill>
      {body}
      {sp.date && <DateNote text={sp.date} t0={head + s2f(sec(sp.dateAt, 0.6))} />}
      {sp.stamp && <Stamp text={sp.stamp.text} x={sp.stamp.x ?? W * 0.78} y={sp.stamp.y ?? H * 0.22} t0={head + s2f(sec(sp.stamp.at, 1))} />}
      {sp.lower && <LowerThird name={sp.lower.name} role={sp.lower.role} x={sp.lower.x} y={sp.lower.y} t0={head + s2f(sec(sp.lower.at, 0.5))} t1={head + s2f(sec(sp.lower.until, 4.5))} />}
      {sp.caps !== false && capsMode === 'film' && <CapBand c={c} id={s.id} head={head} />}
      {sp.caps !== false && <Caps c={c} id={s.id} head={head} mode={capsMode} />}
      {sp.fadeIn ? <FadeIn dur={s2f(sp.fadeIn)} /> : null}
      {sp.fadeOut ? <FadeOut at={head + s2f(s.dur - sp.fadeOut)} dur={s2f(sp.fadeOut)} /> : null}
    </Fill>
  );
};

export const AutoChapter: React.FC<{name: string}> = ({name}) => {
  useFonts();
  const c = chap(name);
  const xf = (i: number) => (i > 0 && i < c.shots.length ? s2f(sec(c.shots[i].spec?.xfade, 0)) : 0);
  return (
    <Fill style={{background: '#000'}}>
      <InkDefs /><StampDefs />
      {c.shots.map((s, i) => {
        const head = xf(i), tail = xf(i + 1);
        return (
          <Shot key={s.id} c={name} id={s.id} head={head} tail={tail}>
            <DissolveIn dur={head}><ShotBody c={name} s={s} head={head} total={s2f(s.dur) + head + tail} /></DissolveIn>
          </Shot>
        );
      })}
      {c.spec?.fadeIn ? <FadeIn dur={s2f(c.spec.fadeIn)} /> : null}
      {c.spec?.fadeOut ? <FadeOut at={s2f(c.dur - c.spec.fadeOut)} dur={s2f(c.spec.fadeOut)} /> : null}
    </Fill>
  );
};
