// Register hand-built chapters here: {chapterName: Component}. Any chapter not listed renders with AutoChapter
// straight from film/shots.json. Start every film with AutoChapter; write a custom chapter only for scenes
// that need choreography (a lineage tree that grows, a sing-along, a page that turns mid-line).
import React from 'react';
import {Example} from './Example';

export const CUSTOM: Record<string, React.FC<any>> = {
  // 'opening': Opening,
  example: Example,
};
