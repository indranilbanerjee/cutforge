// Ink: shaped text written on glyph by glyph (safe for complex scripts), self-drawing strokes, page turns, scraps.
// InkText needs the string pre-shaped by HarfBuzz: add it to tools/text/shape_jobs.json and run tools/text/shapeall.sh.
// Plain HTML text (Hand, Caps) is fine for static lines; never letter-space Indic text.
import React from 'react';
import {useCurrentFrame, staticFile} from 'remotion';
import {W, H, clamp, EASE, noise2D, random, Fill} from './core';
import G from '../glyphs.json';

type Glyph = {d: string; x: number; y: number; cl: number; ax: number};
type Shaped = {text: string; upem: number; width: number; glyphs: Glyph[]};
const GL = G as unknown as Record<string, Shaped>;
export const textWidth = (id: string, size: number) => (GL[id] ? (GL[id].width / GL[id].upem) * size : 0);

// one shared ink-texture filter (rough dip-pen edges); render <InkDefs/> once per composition
export const InkDefs: React.FC = () => (
  <svg width={0} height={0} style={{position: 'absolute'}}>
    <defs>
      <filter id="inkrough" x="-5%" y="-20%" width="110%" height="140%">
        <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="11" result="n" />
        <feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" xChannelSelector="R" yChannelSelector="G" />
      </filter>
    </defs>
  </svg>
);

/** Shaped text written on glyph by glyph: the pen draws the outline, then the ink floods in. */
export const InkText: React.FC<{
  id: string; x: number; y: number; size: number; t0: number; per?: number; draw?: number;
  fill?: string; stroke?: string; strokeW?: number; align?: 'left' | 'center' | 'right'; t1?: number; outline?: boolean;
  shadow?: string; flood?: number; tremble?: number;
}> = ({id, x, y, size, t0, per = 2.2, draw = 10, fill = '#1C140E', stroke, strokeW = 0, align = 'left', t1, outline = false, shadow, flood, tremble = 0}) => {
  const f = useCurrentFrame();
  const s = GL[id];
  if (!s || f < t0 - 1) return null;
  const sc = size / s.upem;
  const w = s.width * sc;
  const ox = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  const out = t1 !== undefined ? 1 - clamp((f - t1) / 12) : 1;
  if (out <= 0) return null;
  return (
    <svg width={W} height={H} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: out}}>
      <g transform={`translate(${ox} ${y})`} filter="url(#inkrough)">
        {s.glyphs.map((g, i) => {
          const p = clamp((f - (t0 + i * per)) / draw);
          if (p <= 0) return null;
          const fillA = flood !== undefined ? EASE.out(clamp((f - flood - i * 0.8) / 8)) : EASE.out(clamp((p - 0.35) / 0.65));
          const jx = tremble ? noise2D('tx' + i, f * 0.25, 0) * tremble : 0, jy = tremble ? noise2D('ty' + i, f * 0.25, 4) * tremble : 0;
          return (
            <g key={i} transform={`translate(${g.x * sc + jx} ${-g.y * sc + jy}) scale(${sc} ${-sc})`}>
              {shadow && <path d={g.d} fill={shadow} transform={`translate(${2.2 / sc} ${-3 / sc})`} opacity={fillA * 0.8} />}
              <path d={g.d} fill={fill} opacity={fillA} />
              {(outline || p < 1) && <path d={g.d} fill="none" stroke={stroke ?? fill} strokeWidth={(strokeW || 1.4) / sc} pathLength={1}
                strokeDasharray={1} strokeDashoffset={1 - EASE.inOut(p)} strokeLinecap="round" strokeLinejoin="round" opacity={outline ? 1 : 1 - fillA * 0.9} />}
            </g>
          );
        })}
      </g>
    </svg>
  );
};

/** A hand-drawn stroke (any SVG path in design pixels) that draws itself. */
export const InkStroke: React.FC<{d: string; t0: number; dur?: number; color?: string; width?: number; t1?: number}> = ({d, t0, dur = 12, color = '#1C140E', width = 3, t1}) => {
  const f = useCurrentFrame();
  const p = clamp((f - t0) / dur);
  if (p <= 0) return null;
  const out = t1 !== undefined ? 1 - clamp((f - t1) / 10) : 1;
  return (
    <svg width={W} height={H} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: out}}>
      <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - EASE.inOut(p)} filter="url(#inkrough)" />
    </svg>
  );
};

/** Torn paper scrap that lands with tape; put text or a small picture inside. */
export const Scrap: React.FC<{x: number; y: number; w: number; h: number; rot?: number; t0: number; t1?: number; children?: React.ReactNode; seed?: string}> = ({x, y, w, h, rot = -3, t0, t1, children, seed = 's'}) => {
  const f = useCurrentFrame();
  if (f < t0) return null;
  const p = EASE.out(clamp((f - t0) / 9));
  const out = t1 !== undefined ? 1 - clamp((f - t1) / 9) : 1;
  if (out <= 0) return null;
  const pts: string[] = []; const N = 18;
  for (let i = 0; i <= N; i++) pts.push(`${(i / N) * 100}% ${random(seed + 't' + i) * 5}%`);
  for (let i = 0; i <= N; i++) pts.push(`${100 - random(seed + 'r' + i) * 2.5}% ${(i / N) * 100}%`);
  for (let i = N; i >= 0; i--) pts.push(`${(i / N) * 100}% ${100 - random(seed + 'b' + i) * 6}%`);
  for (let i = N; i >= 0; i--) pts.push(`${random(seed + 'l' + i) * 2.5}% ${(i / N) * 100}%`);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity: out, transform: `translateY(${(1 - p) * 14}px) rotate(${rot + (1 - p) * 4}deg) scale(${0.96 + 0.04 * p})`, filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.35))'}}>
      <div style={{position: 'absolute', inset: 0, clipPath: `polygon(${pts.join(',')})`, background: `url(${staticFile('art/paper.jpg')}) center/600px`}} />
      <div style={{position: 'absolute', left: w / 2 - 34, top: -12, width: 68, height: 24, background: 'rgba(240,226,190,0.72)', transform: 'rotate(2deg)', boxShadow: '0 1px 2px rgba(0,0,0,0.15)'}} />
      <div style={{position: 'absolute', inset: 0}}>{children}</div>
    </div>
  );
};

/** The whole frame turns over like a book page (spine on the left). Wrap the OUTGOING content. */
export const PageTurn: React.FC<{children: React.ReactNode; t0: number; dur: number}> = ({children, t0, dur}) => {
  const f = useCurrentFrame();
  const p = EASE.inOut(clamp((f - t0) / dur));
  if (p >= 1) return null;
  const shade = Math.sin(Math.PI * p);
  return (
    <Fill style={{perspective: 2200, perspectiveOrigin: '0% 50%'}}>
      <Fill style={{transformOrigin: `0px ${H / 2}px`, transform: `rotateY(${-180 * p}deg)`, backfaceVisibility: 'hidden', boxShadow: `${-40 * shade}px 0 80px rgba(0,0,0,${0.5 * shade})`}}>
        {children}
        <Fill style={{background: `linear-gradient(90deg, rgba(0,0,0,0) 40%, rgba(0,0,0,${0.45 * shade}) 100%)`}} />
      </Fill>
    </Fill>
  );
};
