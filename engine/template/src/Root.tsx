import React from 'react';
import {Composition} from 'remotion';
import {FPS, W, H, s2f} from './lib/core';
import {TL} from './lib/timeline';
import {CUSTOM} from './chapters';
import {AutoChapter} from './auto/AutoChapter';

// One composition per chapter. A chapter renders with its custom component if src/chapters/index.ts
// registers one, otherwise with AutoChapter, which builds every shot from its layout in film/shots.json.
export const Root: React.FC = () => <>
  {TL.chapters.map((c) => {
    const Comp = CUSTOM[c.name];
    return Comp
      ? <Composition key={c.name} id={c.name} component={Comp} durationInFrames={Math.max(1, s2f(c.dur))} fps={FPS} width={W} height={H} />
      : <Composition key={c.name} id={c.name} component={AutoChapter} defaultProps={{name: c.name}}
          durationInFrames={Math.max(1, s2f(c.dur))} fps={FPS} width={W} height={H} />;
  })}
</>;
