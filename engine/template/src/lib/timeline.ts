// The generated master timeline (film/timeline.py writes src/timeline.json). Never edit timeline.json by hand:
// edit film/shots.json (structure) or film/script.json (narration) and re-run the timeline script.
import TLraw from '../timeline.json';

export type VOE = [string, number, number];            // [line id, start (s, shot-local), duration (s)]
export type MediaItem = string | {src: string; from?: number; rate?: number; pos?: string; portrait?: boolean; bw?: boolean};
export type ShotT = {id: string; start: number; dur: number; vo: VOE[]; g: number; spec: Record<string, any>};
export type ChapT = {name: string; start: number; dur: number; shots: ShotT[]; spec: Record<string, any>};
export type Format = {w: number; h: number; fps: number; scale: number};
export const TL = TLraw as unknown as {format: Format; chapters: ChapT[]; text: Record<string, string>; total: number; title?: string};
export const TXT = TL.text;
export const chap = (name: string) => {
  const c = TL.chapters.find((x) => x.name === name);
  if (!c) throw new Error(`chapter ${name} is not in timeline.json (run film/timeline.py)`);
  return c;
};
export const shotOf = (c: string, id: string) => {
  const s = chap(c).shots.find((x) => x.id === id);
  if (!s) throw new Error(`shot ${c}/${id} is not in timeline.json`);
  return s;
};
