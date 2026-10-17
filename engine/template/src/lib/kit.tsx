// CutForge kit: shots on the master timeline, captions, living pictures, prints, pages, stamps, notes,
// doodles, lower thirds and transitions. Design space W x H from core.tsx (1280x720 by default).
// Rules baked in (from real productions): phone media is framed, never stretched; faces stay still;
// zoom stays gentle (<= ~10 % over 5 s); captions appear only while their line is spoken.
import React from 'react';
import {useCurrentFrame, Sequence, OffthreadVideo, Img, staticFile, interpolate} from 'remotion';
import {FPS, W, H, s2f, clamp, ramp, EASE, spr, noise2D, random, Fill} from './core';
import {shotOf, TXT, MediaItem} from './timeline';
import {THEME} from '../theme';

const C = THEME.c;
export const INK = C.ink, ACCENT = C.accent, CREAM = C.cream, PAPER = C.paper;

// ---------- one shot of a chapter as a Sequence; children get shot-local frames ----------
// head/tail (frames) let a shot start early or run late, for cross-dissolves and sound-led cuts.
export const Shot: React.FC<{c: string; id: string; head?: number; tail?: number; children: React.ReactNode}> = ({c, id, head = 0, tail = 0, children}) => {
  const s = shotOf(c, id);
  return (
    <Sequence from={s2f(s.start) - head} durationInFrames={s2f(s.dur) + head + tail} name={id}>
      {children}
    </Sequence>
  );
};
// timing helpers inside a shot: vo(k) = frame line k starts, voEnd(k) = frame it ends (measured, never assumed)
export const useShot = (c: string, id: string, head = 0) => {
  const s = shotOf(c, id);
  const f = useCurrentFrame() - head;
  const vo = (k: number) => (s.vo[k] ? s2f(s.vo[k][1]) : 0);
  const voEnd = (k: number) => (s.vo[k] ? s2f(s.vo[k][1] + s.vo[k][2]) : 0);
  return {f, dur: s2f(s.dur), s, vo, voEnd};
};

// ---------- narration captions: shown only while the line is spoken (+ small lead/tail) ----------
export const Caps: React.FC<{c: string; id: string; mode?: 'film' | 'paper'; y?: number; head?: number; size?: number; hide?: number[]; maxW?: number}> = ({c, id, mode = 'film', y, head = 0, size = Math.max(THEME.caption.size, Math.round(H / 20)), hide = [], maxW}) => {
  const s = shotOf(c, id);
  const f = useCurrentFrame() - head;
  // The caption block's BOTTOM edge is anchored and extra lines grow upwards, so a long caption never drops out of the
  // safe area: landscape 91.5 % (inside the 86 % projector/TV safe area), square 90 %, vertical 64 % (above the ~35 %
  // that phone apps cover). An explicit y centres the block on y instead.
  const yy = y ?? (H > W ? H * 0.64 : H > W * 0.9 ? H * 0.9 : H * 0.915);
  const shift = y === undefined ? 'translateY(-100%)' : 'translateY(-50%)';
  const film = mode === 'film';
  return (<>{s.vo.map(([p, at, d], k) => {
    if (hide.includes(k) || !TXT[p]) return null;
    const a = s2f(at - 0.12), b = s2f(at + d + 0.35);
    if (f < a - 2 || f > b + 8) return null;
    const op = Math.min(ramp(f, a - 2, a + 5, EASE.soft), 1 - ramp(f, b, b + 7, EASE.soft));
    const side = (W - (maxW ?? W - 180)) / 2;
    return (
      <div key={p} style={{position: 'absolute', left: side, right: side, top: yy, transform: shift, textAlign: 'center', opacity: op}}>
        <span style={{fontFamily: THEME.caption.font, fontSize: size, lineHeight: 1.35, color: film ? CREAM : INK,
          textShadow: film ? '0 1px 2px rgba(0,0,0,0.9), 0 0 14px rgba(0,0,0,0.75), 0 0 32px rgba(0,0,0,0.5)' : '0 0 1px rgba(28,20,14,0.3)'}}>{TXT[p]}</span>
      </div>
    );
  })}</>);
};
// soft dark band under film captions, only while a line is up
export const CapBand: React.FC<{c: string; id: string; head?: number}> = ({c, id, head = 0}) => {
  const s = shotOf(c, id);
  const f = useCurrentFrame() - head;
  let a = 0;
  for (const [, at, d] of s.vo) a = Math.max(a, Math.min(ramp(f, s2f(at - 0.3), s2f(at), EASE.soft), 1 - ramp(f, s2f(at + d + 0.3), s2f(at + d + 0.7), EASE.soft)));
  return <Fill style={{opacity: a * 0.85, background: 'linear-gradient(180deg, rgba(0,0,0,0) 72%, rgba(8,5,2,0.55) 100%)'}} />;
};

// ---------- looks ----------
export const BW = 'grayscale(1) sepia(0.14) contrast(1.1) brightness(1.03)';
export const GLOW = 'saturate(1.5) brightness(0.62) contrast(2.4)';      // keep only bright coloured lights (B&W + glowing lamps)

// ---------- media (photo or clip; clips are always muted here: their sound goes through the mix) ----------
const isVid = (src: string) => /\.(mp4|mov|webm|m4v)$/i.test(src);
export const norm = (m: MediaItem) => (typeof m === 'string' ? {src: m} : m);
export const Media: React.FC<{src: string; from?: number; rate?: number; pos?: string; style?: React.CSSProperties; filter?: string; fit?: 'cover' | 'contain'}> = ({src, from = 0, rate = 1, pos = '50% 50%', style, filter, fit = 'cover'}) => {
  const st: React.CSSProperties = {width: '100%', height: '100%', objectFit: fit, objectPosition: pos, filter, ...style};
  return isVid(src)
    ? <OffthreadVideo src={staticFile(src)} trimBefore={Math.round(from * FPS)} playbackRate={rate} muted style={st} />
    : <Img src={staticFile(src)} style={st} />;
};

// full-frame living picture: slow push (z), drift (o = [x0,y0,x1,y1] px), optional B&W with glowing lights, gate weave
export const Living: React.FC<{src: string; from?: number; dur: number; z?: [number, number]; o?: [number, number, number, number]; pos?: string; bw?: boolean; glow?: boolean; grade?: string; rate?: number; rot?: number}> = ({src, from = 0, dur, z = [1.02, 1.1], o = [0, 0, 0, 0], pos, bw, glow, grade = '', rate, rot = 0}) => {
  const f = useCurrentFrame();
  const p = EASE.inOut(clamp(f / Math.max(1, dur)));
  const sc = interpolate(p, [0, 1], z), x = interpolate(p, [0, 1], [o[0], o[2]]), y = interpolate(p, [0, 1], [o[1], o[3]]);
  const wv = {x: noise2D('wx', f * 0.12, 1) * 0.6, y: noise2D('wy', f * 0.12, 4) * 0.6};
  const tf = `translate(${x + wv.x}px, ${y + wv.y}px) scale(${sc}) rotate(${rot}deg)`;
  return (
    <Fill style={{overflow: 'hidden', background: '#000'}}>
      <Fill style={{transform: tf}}>
        <Media src={src} from={from} rate={rate} pos={pos} filter={(bw ? BW : 'saturate(1.02) contrast(1.03)') + ' ' + grade} />
      </Fill>
      {bw && glow && <Fill style={{transform: tf, mixBlendMode: 'lighten'}}><Media src={src} from={from} rate={rate} pos={pos} filter={GLOW} /></Fill>}
    </Fill>
  );
};

// a portrait (phone) photo or clip shown whole, never stretched and never blur-filled: it sits on the paper page
// (bg 'page', default) or on black (bg 'black'), inside the safe area, with a soft shadow and a slow push.
export const PortraitFrame: React.FC<{src: string; from?: number; dur: number; bw?: boolean; z?: [number, number]; bg?: 'page' | 'black'}> = ({src, from = 0, dur, bw, z = [1.0, 1.03], bg = 'page'}) => {
  const f = useCurrentFrame();
  const sc = interpolate(EASE.inOut(clamp(f / Math.max(1, dur))), [0, 1], z);
  const pic = (
    <div style={{position: 'absolute', left: W * 0.1, top: H > W ? H * 0.16 : H * 0.1, width: W * 0.8, height: H > W ? H * 0.36 : H * 0.7, transform: `scale(${sc})`,
      filter: 'drop-shadow(0 10px 18px rgba(0,0,0,0.45))'}}>
      <Media src={src} from={from} fit="contain" filter={bw ? BW : undefined} />
    </div>
  );
  return bg === 'black' ? <Fill style={{background: '#000', overflow: 'hidden'}}>{pic}</Fill> : <Page dur={dur}>{pic}</Page>;
};

// ---------- paper page with a slow living camera ----------
export const Page: React.FC<{children?: React.ReactNode; dim?: number; drift?: number; tone?: string; dur?: number}> = ({children, dim = 0, drift = 1, tone, dur = 250}) => {
  const f = useCurrentFrame();
  const p = clamp(f / dur);
  const sc = 1.0 + 0.035 * drift * p;
  const x = noise2D('pgx', f * 0.004, 0) * 6 * drift, y = noise2D('pgy', f * 0.004, 3) * 4 * drift;
  return (
    <Fill style={{background: '#2a2018', overflow: 'hidden'}}>
      <Fill style={{transform: `translate(${x}px, ${y}px) scale(${sc})`}}>
        <Img src={staticFile('art/paper.jpg')} style={{position: 'absolute', inset: -20, width: W + 40, height: H + 40, objectFit: 'cover'}} />
        {tone && <Fill style={{background: tone, mixBlendMode: 'multiply'}} />}
        {children}
      </Fill>
      {dim > 0 && <Fill style={{background: `rgba(10,8,20,${dim})`}} />}
      <Fill style={{boxShadow: 'inset 0 0 140px rgba(60,35,10,0.45)'}} />
    </Fill>
  );
};

// ---------- a photographic print that lands on the page ----------
export type PrintP = {x: number; y: number; w: number; h: number; rot?: number; t0?: number; t1?: number; src: string; from?: number; rate?: number; pos?: string;
  enter?: 'drop' | 'left' | 'right' | 'up' | 'fade' | 'pop'; border?: number; bw?: boolean; glow?: boolean; tape?: boolean; corners?: boolean; zoom?: [number, number]; dur?: number; grade?: string; shadow?: number};
export const Print: React.FC<PrintP> = ({x, y, w, h, rot = 0, t0 = 0, t1, src, from = 0, rate, pos, enter = 'drop', border = 10, bw, glow, tape = false, corners = true, zoom = [1.0, 1.08], dur = 200, grade = '', shadow = 1}) => {
  const f = useCurrentFrame();
  if (f < t0 - 1) return null;
  const s = spr(f, t0, {damping: 15, stiffness: 140, mass: 0.9});
  const out = t1 !== undefined ? EASE.in(clamp((f - t1) / 9)) : 0;
  if (out >= 1) return null;
  const e = 1 - s;
  let tx = 0, ty = 0, sc = 1, op = 1, r2 = rot;
  if (enter === 'drop') { ty = -60 * e; sc = 1 + 0.12 * e; r2 = rot + 6 * e; op = clamp(s * 3); }
  if (enter === 'left') { tx = -420 * e; r2 = rot - 10 * e; }
  if (enter === 'right') { tx = 420 * e; r2 = rot + 10 * e; }
  if (enter === 'up') { ty = 300 * e; r2 = rot + 4 * e; }
  if (enter === 'fade') { op = clamp(s * 1.4); sc = 1 + 0.03 * e; }
  if (enter === 'pop') { sc = 0.6 + 0.4 * s; op = clamp(s * 3); }
  ty += out * 40; op *= 1 - out;
  const kb = interpolate(clamp((f - t0) / dur), [0, 1], zoom);
  const lift = 1 + 1.2 * e;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity: op, transform: `translate(${tx}px, ${ty}px) rotate(${r2}deg) scale(${sc})`,
      filter: `drop-shadow(0 ${6 * lift * shadow}px ${10 * lift * shadow}px rgba(30,18,6,${0.42 * shadow}))`}}>
      <div style={{position: 'absolute', inset: 0, background: '#F7F0E2', boxShadow: 'inset 0 0 0 1px rgba(80,60,30,0.25)'}} />
      <div style={{position: 'absolute', left: border, top: border, right: border, bottom: border, overflow: 'hidden', background: '#111'}}>
        <div style={{position: 'absolute', inset: 0, transform: `scale(${kb})`}}>
          <Media src={src} from={from} rate={rate} pos={pos} filter={(bw ? BW : 'saturate(1.02) contrast(1.03)') + ' ' + grade} />
        </div>
        {bw && glow && <div style={{position: 'absolute', inset: 0, transform: `scale(${kb})`, mixBlendMode: 'lighten'}}><Media src={src} from={from} rate={rate} pos={pos} filter={GLOW} /></div>}
        <Img src={staticFile('art/paper.jpg')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', mixBlendMode: 'multiply', opacity: 0.18}} />
      </div>
      {corners && [[0, 0, 0], [1, 0, 90], [1, 1, 180], [0, 1, 270]].map(([cx, cy, a], i) => (
        <svg key={i} width={34} height={34} viewBox="0 0 34 34" style={{position: 'absolute', left: cx ? w - 26 : -8, top: cy ? h - 26 : -8, transform: `rotate(${a}deg)`}}>
          <path d="M2 2 L32 2 L2 32 Z" fill="#2B1E15" opacity={0.92} />
        </svg>
      ))}
      {tape && <div style={{position: 'absolute', left: w / 2 - 40, top: -14, width: 80, height: 26, background: 'rgba(240,226,190,0.78)', transform: 'rotate(-3deg)', boxShadow: '0 1px 2px rgba(0,0,0,0.15)'}} />}
    </div>
  );
};

// ---------- three vertical clips or photos side by side (phone video without black bars) ----------
export const Triptych: React.FC<{items: MediaItem[]; t0?: number; gap?: number; stagger?: number; bw?: boolean}> = ({items, t0 = 0, gap = 8, stagger = 6, bw}) => {
  const f = useCurrentFrame();
  const n = Math.max(1, Math.min(3, items.length));
  const w = (W - gap * (n + 1)) / n;
  return (
    <Fill style={{background: '#0d0a08'}}>
      {items.slice(0, 3).map((m, i) => {
        const it = norm(m);
        const p = spr(f, t0 + i * stagger, {damping: 16, stiffness: 120});
        return (
          <div key={i} style={{position: 'absolute', left: gap + i * (w + gap), top: gap, width: w, height: H - 2 * gap, overflow: 'hidden',
            opacity: clamp(p * 2), transform: `translateY(${(1 - p) * 40}px)`}}>
            <Media src={it.src} from={it.from} rate={it.rate} pos={it.pos} filter={bw || it.bw ? BW : undefined} />
          </div>
        );
      })}
    </Fill>
  );
};

// ---------- handwritten note that writes on left to right ----------
export const Hand: React.FC<{text: string; x: number; y: number; size?: number; color?: string; t0?: number; t1?: number; rot?: number; font?: string; align?: 'left' | 'center' | 'right'; w?: number}> = ({text, x, y, size = 30, color = INK, t0 = 0, t1, rot = 0, font = 'Hand', align = 'left', w = 600}) => {
  const f = useCurrentFrame();
  if (f < t0) return null;
  const p = ramp(f, t0, t0 + 10, EASE.out);
  const out = t1 !== undefined ? ramp(f, t1, t1 + 8) : 0;
  const ox = align === 'center' ? -w / 2 : align === 'right' ? -w : 0;
  return (
    <div style={{position: 'absolute', left: x + ox, top: y, width: w, textAlign: align, transform: `rotate(${rot}deg)`, opacity: p * (1 - out),
      clipPath: `inset(-20% ${100 - p * 100}% -20% -5%)`}}>
      <span style={{fontFamily: font, fontSize: size, color, lineHeight: 1.25, filter: 'url(#inkrough)'}}>{text}</span>
    </div>
  );
};

// ---------- rubber stamp (needs <StampDefs/> once in the composition) ----------
export const Stamp: React.FC<{text: string; x: number; y: number; t0: number; size?: number; rot?: number; color?: string; font?: string; t1?: number}> = ({text, x, y, t0, size = 40, rot = -8, color = ACCENT, font = 'Display', t1}) => {
  const f = useCurrentFrame();
  if (f < t0) return null;
  const k = f - t0;
  const sc = k < 3 ? 1.6 - 0.2 * k : 1 + 0.04 * Math.exp(-(k - 3) * 0.5);
  const out = t1 !== undefined ? ramp(f, t1, t1 + 8) : 0;
  return (
    <div style={{position: 'absolute', left: x, top: y, transform: `translate(-50%,-50%) rotate(${rot}deg) scale(${sc})`, opacity: clamp(k / 2) * 0.9 * (1 - out)}}>
      <div style={{fontFamily: font, fontSize: size, color, padding: '2px 16px 0', border: `${Math.max(2, size * 0.07)}px solid ${color}`, borderRadius: 8,
        mixBlendMode: 'multiply', filter: 'url(#stampwear)', whiteSpace: 'nowrap', lineHeight: 1.3}}>{text}</div>
    </div>
  );
};
export const StampDefs: React.FC = () => (
  <svg width={0} height={0} style={{position: 'absolute'}}>
    <defs>
      <filter id="stampwear" x="-10%" y="-20%" width="120%" height="140%">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4" result="n" />
        <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.35" result="holes" />
        <feComposite in="SourceGraphic" in2="holes" operator="in" />
      </filter>
    </defs>
  </svg>
);

// ---------- torn-paper date note ----------
// default position sits inside the 86 % safe area (projectors crop edges after keystone correction)
export const DateNote: React.FC<{text: string; x?: number; y?: number; t0?: number; t1?: number; rot?: number; size?: number; color?: string; w?: number}> = ({text, x = H > W ? W * 0.1 : W * 0.08, y = H > W ? H * 0.16 : H * 0.08, t0 = 6, t1, rot = -2.5, size = 28, color = INK, w}) => {
  const f = useCurrentFrame();
  if (f < t0) return null;
  const p = spr(f, t0, {damping: 16, stiffness: 150});
  const out = t1 !== undefined ? ramp(f, t1, t1 + 8) : 0;
  const ww = w ?? Math.max(150, text.length * size * 0.5 + 50);
  const pts: string[] = []; const N = 14; const sd = text;
  for (let i = 0; i <= N; i++) pts.push(`${(i / N) * 100}% ${random(sd + 't' + i) * 7}%`);
  for (let i = 0; i <= N; i++) pts.push(`${100 - random(sd + 'r' + i) * 3}% ${(i / N) * 100}%`);
  for (let i = N; i >= 0; i--) pts.push(`${(i / N) * 100}% ${100 - random(sd + 'b' + i) * 8}%`);
  for (let i = N; i >= 0; i--) pts.push(`${random(sd + 'l' + i) * 3}% ${(i / N) * 100}%`);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: ww, height: size * 1.9, opacity: clamp(p * 2) * (1 - out),
      transform: `translateY(${(1 - p) * -16}px) rotate(${rot + (1 - p) * 5}deg)`, filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.38))'}}>
      <div style={{position: 'absolute', inset: 0, clipPath: `polygon(${pts.join(',')})`, background: `url(${staticFile('art/paper.jpg')}) center/500px`}} />
      <div style={{position: 'absolute', left: ww / 2 - 30, top: -10, width: 60, height: 20, background: 'rgba(240,226,190,0.75)', transform: 'rotate(3deg)'}} />
      <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Hand', fontSize: size, color, paddingTop: size * 0.12}}>{text}</div>
    </div>
  );
};

// ---------- ink doodles that draw themselves ----------
export const Doodle: React.FC<{kind: 'star' | 'heart' | 'swirl' | 'arrow' | 'circle' | 'sun' | 'wave' | 'crown'; x: number; y: number; s?: number; t0: number; color?: string; rot?: number; dur?: number; t1?: number; width?: number}> = ({kind, x, y, s = 1, t0, color = ACCENT, rot = 0, dur = 12, t1, width = 3}) => {
  const f = useCurrentFrame();
  if (f < t0) return null;
  const p = EASE.inOut(clamp((f - t0) / dur));
  const out = t1 !== undefined ? ramp(f, t1, t1 + 8) : 0;
  const D: Record<string, string> = {
    star: 'M0 -26 L7 -8 L26 -8 L11 4 L17 23 L0 12 L-17 23 L-11 4 L-26 -8 L-7 -8 Z',
    heart: 'M0 22 C -30 0, -26 -26, -8 -24 C 0 -23, 0 -14, 0 -12 C 0 -14, 2 -23, 10 -24 C 28 -26, 30 0, 0 22',
    swirl: 'M0 0 C 8 -2, 10 -12, 2 -16 C -10 -22, -22 -10, -18 4 C -14 20, 8 26, 22 14 C 34 4, 32 -18, 20 -28',
    arrow: 'M-40 10 C -14 -4, 10 -6, 34 -2 M 34 -2 L 20 -12 M 34 -2 L 22 10',
    circle: 'M-50 0 C -50 -30, 50 -34, 52 -2 C 54 28, -40 34, -52 4 C -54 -10, -40 -22, -20 -26',
    sun: 'M0 -10 A10 10 0 1 1 -0.1 -10 M0 -18 L0 -28 M0 18 L0 28 M18 0 L28 0 M-18 0 L-28 0 M13 13 L20 20 M-13 -13 L-20 -20 M13 -13 L20 -20 M-13 13 L-20 20',
    wave: 'M-60 0 C -45 -14, -30 -14, -15 0 C 0 14, 15 14, 30 0 C 45 -14, 60 -14, 75 0',
    crown: 'M-30 14 L-34 -14 L-16 2 L0 -20 L16 2 L34 -14 L30 14 Z',
  };
  return (
    <svg width={200} height={200} viewBox="-100 -100 200 200" style={{position: 'absolute', left: x - 100, top: y - 100, transform: `rotate(${rot}deg) scale(${s})`, opacity: 1 - out, overflow: 'visible'}}>
      <path d={D[kind]} fill="none" stroke={color} strokeWidth={width / s} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} filter="url(#inkrough)" />
    </svg>
  );
};

// ---------- lower third (name + role) for interviews, brand and explainer videos ----------
export const LowerThird: React.FC<{name: string; role?: string; t0: number; t1: number; x?: number; y?: number; color?: string}> = ({name, role, t0, t1, x, y, color = ACCENT}) => {
  const f = useCurrentFrame();
  if (f < t0 || f > t1 + 10) return null;
  const p = EASE.out(clamp((f - t0) / 12)), q = 1 - EASE.in(clamp((f - t1) / 10));
  const yy = y ?? (H > W ? H * 0.3 : H > W * 0.9 ? H * 0.62 : H * 0.66);  // clear of two-line captions in every format
  const xx = x ?? (H > W ? W * 0.1 : 70);
  return (
    <div style={{position: 'absolute', left: xx, top: yy, opacity: q}}>
      <div style={{width: 6, height: 74, background: color, position: 'absolute', left: 0, top: 0, transform: `scaleY(${p})`, transformOrigin: 'top'}} />
      <div style={{marginLeft: 22, clipPath: `inset(0 ${100 - p * 100}% 0 0)`}}>
        <div style={{fontFamily: 'SansB', fontSize: 34, color: '#fff', textShadow: '0 2px 8px rgba(0,0,0,0.6)'}}>{name}</div>
        {role && <div style={{fontFamily: 'Sans', fontSize: 22, color: 'rgba(255,255,255,0.85)', textShadow: '0 2px 8px rgba(0,0,0,0.6)'}}>{role}</div>}
      </div>
    </div>
  );
};

// ---------- transitions ----------
export const InkWipe: React.FC<{t0: number; dur?: number; children: React.ReactNode; cx?: number; cy?: number; seed?: string}> = ({t0, dur = 14, children, cx = W / 2, cy = H / 2, seed = 'iw'}) => {
  const f = useCurrentFrame();
  if (f < t0) return null;
  const p = EASE.inOut(clamp((f - t0) / dur));
  if (p >= 1) return <>{children}</>;
  const r = p * Math.hypot(W, H) * 0.7;
  const id = 'iwm' + seed;
  return (
    <Fill>
      <svg width={0} height={0} style={{position: 'absolute'}}>
        <defs>
          <filter id={id + 'f'}><feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3" seed={7} /><feDisplacementMap in="SourceGraphic" scale={120} /></filter>
          <mask id={id} maskUnits="userSpaceOnUse" x="0" y="0" width={W} height={H}>
            <rect width={W} height={H} fill="black" />
            <circle cx={cx} cy={cy} r={r} fill="white" filter={`url(#${id}f)`} />
          </mask>
        </defs>
      </svg>
      <Fill style={{mask: `url(#${id})`, WebkitMask: `url(#${id})`} as React.CSSProperties}>{children}</Fill>
    </Fill>
  );
};
export const Dip: React.FC<{t0: number; dur?: number; color?: string; peak?: number}> = ({t0, dur = 12, color = '#000', peak = 1}) => {
  const f = useCurrentFrame();
  const a = Math.min(ramp(f, t0, t0 + dur / 2, EASE.inOut), 1 - ramp(f, t0 + dur / 2, t0 + dur, EASE.inOut));
  if (a <= 0) return null;
  return <Fill style={{background: color, opacity: a * peak}} />;
};
export const FadeIn: React.FC<{dur?: number; color?: string}> = ({dur = 10, color = '#000'}) => {
  const f = useCurrentFrame();
  const a = 1 - ramp(f, 0, dur, EASE.soft);
  return a > 0 ? <Fill style={{background: color, opacity: a}} /> : null;
};
export const FadeOut: React.FC<{at: number; dur?: number; color?: string}> = ({at, dur = 10, color = '#000'}) => {
  const f = useCurrentFrame();
  const a = ramp(f, at, at + dur, EASE.soft);
  return a > 0 ? <Fill style={{background: color, opacity: a}} /> : null;
};
// cross-dissolve in: wrap a shot's content; the shot must start `dur` frames early (Shot head = dur)
export const DissolveIn: React.FC<{dur: number; children: React.ReactNode}> = ({dur, children}) => {
  const f = useCurrentFrame();
  return <Fill style={{opacity: dur > 0 ? ramp(f, 0, dur, EASE.inOut) : 1}}>{children}</Fill>;
};

// ---------- light ----------
export const Vignette: React.FC<{amt?: number; color?: string}> = ({amt = 0.55, color = '0,0,0'}) => (
  <Fill style={{background: `radial-gradient(ellipse 75% 70% at 50% 48%, rgba(${color},0) 55%, rgba(${color},${amt}) 100%)`, pointerEvents: 'none'}} />
);
export const LampLight: React.FC<{x: number; y: number; r?: number; amt?: number}> = ({x, y, r = 700, amt = 0.55}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const k = 0.82 + noise2D('ll1', t * 3, 0) * 0.12 + noise2D('ll2', t * 9, 1) * 0.06;
  return (<>
    <Fill style={{background: `radial-gradient(circle at ${x}px ${y}px, rgba(255,170,80,${0.5 * amt * k}) 0%, rgba(255,120,40,${0.18 * amt * k}) ${r * 0.35}px, rgba(0,0,0,0) ${r}px)`, mixBlendMode: 'screen'}} />
    <Fill style={{background: `radial-gradient(circle at ${x}px ${y}px, rgba(0,0,0,0) ${r * 0.4}px, rgba(10,4,0,${0.45 * amt}) ${r * 1.3}px)`, mixBlendMode: 'multiply'}} />
  </>);
};
export const LightLeak: React.FC<{t0: number; dur: number; seed?: string; strength?: number; warm?: boolean}> = ({t0, dur, seed = 'll', strength = 1, warm = true}) => {
  const f = useCurrentFrame();
  const p = (f - t0) / dur;
  if (p < 0 || p > 1) return null;
  const env = Math.sin(Math.PI * p) ** 1.5 * strength;
  return <Fill>{[0, 1, 2].map((k) => {
    const x = interpolate(p, [0, 1], [-200 + random(seed + k) * 500, 700 + random(seed + 'e' + k) * 700]);
    const y = 150 + random(seed + 'y' + k) * 420 + noise2D(seed + 'n' + k, p * 2, 0) * 120;
    const r = 420 + random(seed + 'r' + k) * 380;
    const col = warm ? ['255,120,40', '255,190,90', '230,60,40'][k] : ['255,220,170', '255,180,120', '255,240,210'][k];
    return <div key={k} style={{position: 'absolute', left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: '50%',
      background: `radial-gradient(circle, rgba(${col},0.85) 0%, rgba(${col},0.35) 35%, rgba(${col},0) 70%)`, mixBlendMode: 'screen', opacity: env}} />;
  })}</Fill>;
};

export {Fill, s2f, clamp, ramp, EASE, spr, noise2D, random, FPS, W, H};
