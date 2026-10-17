import React, {useEffect, useState} from 'react';
import {continueRender, delayRender, staticFile, interpolate, Easing, spring, random} from 'remotion';
import {noise2D} from '@remotion/noise';
import {TL} from './timeline';
import {THEME} from '../theme';

// Design space comes from film/shots.json "format" (default 1280x720 at 25 fps, rendered x1.5 = 1920x1080).
// Vertical: {"w": 720, "h": 1280}. Square: {"w": 1080, "h": 1080, "scale": 1}.
export const FPS = TL.format?.fps ?? 25;
export const W = TL.format?.w ?? 1280;
export const H = TL.format?.h ?? 720;
export const s2f = (s: number) => Math.round(s * FPS);

// ---------- fonts: every family in theme.ts is loaded before the first frame renders ----------
let fontsReady: Promise<void> | null = null;
export const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    if (!fontsReady) {
      fontsReady = Promise.all(THEME.fonts.map(([fam, file]) => {
        const f = new FontFace(fam, `url(${staticFile('fonts/' + file)})`);
        return f.load().then((ff) => { (document.fonts as any).add(ff); });
      })).then(() => undefined);
    }
    fontsReady.then(() => continueRender(handle)).catch((e) => { console.error('font load failed', e); continueRender(handle); });
  }, [handle]);
};

// ---------- easing helpers ----------
export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const ramp = (f: number, a: number, b: number, ease: (t: number) => number = Easing.bezier(0.33, 0, 0.2, 1)) =>
  interpolate(f, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
export const EASE = {
  out: Easing.bezier(0.16, 1, 0.3, 1),
  inOut: Easing.bezier(0.65, 0, 0.35, 1),
  in: Easing.bezier(0.55, 0, 1, 0.45),
  soft: Easing.bezier(0.33, 0, 0.2, 1),
};
export const spr = (f: number, start: number, cfg: {damping?: number; stiffness?: number; mass?: number} = {}) =>
  spring({frame: f - start, fps: FPS, config: {damping: 14, stiffness: 120, mass: 0.8, ...cfg}});
// squash and stretch from a spring's velocity
export const squash = (f: number, start: number, cfg = {}) => {
  const a = spr(f, start, cfg), b = spr(f - 1, start, cfg);
  const v = (a - b) * 6;
  return {s: a, sx: 1 + clamp(-v, -0.25, 0.35) * 0.6, sy: 1 + clamp(v, -0.3, 0.35) * 0.6};
};
export const shake = (f: number, start: number, amp = 10, decay = 0.18, seed = 1) => {
  const t = f - start;
  if (t < 0) return {x: 0, y: 0, r: 0};
  const k = amp * Math.exp(-t * decay);
  return {x: noise2D('sx' + seed, t * 0.9, 0) * k, y: noise2D('sy' + seed, t * 0.9, 3) * k, r: noise2D('sr' + seed, t * 0.7, 7) * k * 0.08};
};
// film-gate weave for photographic layers
export const weave = (f: number, amp = 0.6) => ({x: noise2D('wx', f * 0.15, 0) * amp, y: noise2D('wy', f * 0.15, 5) * amp});

export const Fill: React.FC<{style?: React.CSSProperties; children?: React.ReactNode}> = ({style, children}) => (
  <div style={{position: 'absolute', inset: 0, ...style}}>{children}</div>
);
export {random, noise2D, staticFile};
