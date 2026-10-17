// A hand-built chapter, as a pattern to copy. Everything is anchored to the measured narration
// (useShot().vo / voEnd), never to guessed seconds, so a re-recorded line re-times the scene by itself.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {W, H, s2f, useFonts, Fill} from '../lib/core';
import {Shot, useShot, Caps, CapBand, Living, Page, Print, Hand, Stamp, StampDefs, Doodle, LampLight, FadeIn} from '../lib/kit';
import {InkDefs, InkStroke, PageTurn} from '../lib/ink';
import {THEME} from '../theme';

const C = 'example';

// shot E1: a page; a print lands as the first line starts, a doodle circles it as the line ends, a stamp lands on line 2
const E1: React.FC = () => {
  const {vo, voEnd, dur} = useShot(C, 'E1');
  return (
    <Page dur={dur}>
      <Hand text="A pattern, not a template" x={W / 2} y={70} size={42} align="center" w={900} t0={6} />
      <Print x={W / 2 - 300} y={150} w={600} h={380} rot={-2} t0={vo(0)} src="media/demo_sea.jpg" />
      <Doodle kind="circle" x={W / 2} y={340} s={5.4} t0={voEnd(0) - 10} dur={16} />
      <Stamp text="ANCHORED" x={W - 230} y={H - 150} t0={vo(1) + 4} />
      <InkStroke d={`M ${W / 2 - 280} ${H - 120} C ${W / 2 - 100} ${H - 150}, ${W / 2 + 100} ${H - 100}, ${W / 2 + 280} ${H - 130}`} t0={vo(1)} dur={20} color={THEME.c.accent} />
    </Page>
  );
};

// E1's finished page, static, so E2 can turn it away (a page turn must carry the outgoing content, not a blank page)
const E1Final: React.FC = () => (
  <Page dur={1} drift={0}>
    <Hand text="A pattern, not a template" x={W / 2} y={70} size={42} align="center" w={900} t0={-100} />
    <Print x={W / 2 - 300} y={150} w={600} h={380} rot={-2} t0={-100} src="media/demo_sea.jpg" />
  </Page>
);

// shot E2: a living photo under lamp light; E1's page turns away over it
const E2: React.FC = () => {
  const {dur} = useShot(C, 'E2');
  return (
    <Fill>
      <Living src="media/demo_lamp.jpg" dur={dur} z={[1.04, 1.12]} />
      <LampLight x={W * 0.5} y={H * 0.55} amt={0.6} />
      <PageTurn t0={2} dur={20}><E1Final /></PageTurn>
    </Fill>
  );
};

export const Example: React.FC = () => {
  useFonts();
  return (
    <Fill style={{background: '#000'}}>
      <InkDefs /><StampDefs />
      <Shot c={C} id="E1"><E1 /><Caps c={C} id="E1" mode="paper" /></Shot>
      <Shot c={C} id="E2"><E2 /><CapBand c={C} id="E2" /><Caps c={C} id="E2" /></Shot>
      <FadeIn dur={12} />
    </Fill>
  );
};
