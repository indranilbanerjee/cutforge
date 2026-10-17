// The project's look in one place. Pick the palette and fonts in the brief, then keep them for the whole film.
// Fonts: files in public/fonts (full files only: a subset font breaks complex scripts such as Bengali or Devanagari).
// Bundled (SIL OFL 1.1): Tiro Bangla, Hind Siliguri, Galada, Atma. All include Latin.
// For Hindi/Marathi add e.g. Tiro Devanagari Hindi or Noto Sans Devanagari; for Tamil, Noto Sans Tamil, etc.
export const THEME = {
  fonts: [
    ['Serif', 'TiroBangla-Regular.ttf'],      // captions, body text
    ['SerifI', 'TiroBangla-Italic.ttf'],
    ['Sans', 'HindSiliguri-Medium.ttf'],      // UI-like labels, lower thirds
    ['SansB', 'HindSiliguri-Bold.ttf'],
    ['Hand', 'Galada-Regular.ttf'],           // handwritten notes, titles
    ['Display', 'Atma-Bold.ttf'],             // stamps, playful titles
  ] as [string, string][],
  // palette: paper, ink, accent (stamps, highlights), second accent, gold
  c: {paper: '#F3E6C8', ink: '#1C140E', accent: '#B3261E', indigo: '#22306B', gold: '#E9B44C', cream: '#FFF6E2', night: '#0B1020'},
  // captions: size is a minimum; Caps uses at least 1/20 of the frame height (36 px at 720, 64 at 1280, 54 at 1080)
  caption: {font: 'Serif', size: 36, band: true},
};
