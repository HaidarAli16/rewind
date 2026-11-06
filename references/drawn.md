# Drawn layers

Titles, captions, cards, UI, stamps, counters, charts: everything drawn gets rebuilt, so it has to match on time, size, look and motion.

## Time

- Things appear and switch on exact frames. If a word is fully there on its first visible frame, `set` it there; tween only what visibly moves over several frames.
- For each caption or tag, take its first and last frame from the pixels of its band (`cuts.py --roi <band> --min 2 --ratio 3`, then a strip every 2-3 frames to read which word is which). Use the transcript only for the words themselves, and check names by eye: transcribers mishear them.
- Transitions at cuts (a blur, a dissolve, a wipe, a one-frame flash) are rebuilt over their measured frames, not replaced by a hard cut.

## Size and place

- Measure text by its ink: `fitwords.py` fits size, letter-spacing and position for whole lines at once, and `track.py ink --vs <render>` reports the difference after a render. Two passes usually get within 1-3 px.
- Choosing a font: compare candidates on the letters that differ most between families (a, g, y, t, v, numerals), at the measured size. Prefer free fonts you can ship with the project. Note every substitute in `REWIND.md`.
- Use source pixels everywhere: the canvas is the source's size, so measured boxes go straight in.

## Look

- Sample colours from the frame, not from memory, and sample gradients at both ends.
- Shadows, outlines, glows and bevels: zoom into a still at full size and name each effect before building it.
- Textures (dots, grids, grain): measure the spacing and offset, then generate them; grain will never match pixel for pixel, so match its strength.

## Through its whole life

Before building a large word or card, look at a strip over its box from first to last frame: how it arrives (drop, rise, pop, type-on, wipe, blur-in), what happens while it holds (a fill sweeping, a counter, a drift) and how it leaves. Build each phase from what you measured.

## Recipes that work on a seeked timeline

All of these render the same frame no matter where the timeline is sought to:

- sweeping fill: two copies of the word, the top one revealed by a tweened `clip-path: inset(...)`;
- gradient letters: `background-clip: text` with a transparent fill;
- outline letters: `-webkit-text-stroke`;
- directional blur: an SVG `feGaussianBlur` with a tweened one-axis `stdDeviation` (CSS `blur()` blurs both ways);
- displaced or glassy letters: an SVG filter (`feTurbulence` with a fixed seed into `feDisplacementMap`);
- glow: stacked shadows with tweened radius and opacity;
- flashes: a full-frame layer shown for exactly the measured frames;
- counters and typing: `set` the text on each frame from the measured values;
- moving grain: a fixed-seed noise filter stepped per frame.
