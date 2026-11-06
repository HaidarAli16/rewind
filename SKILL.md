---
name: rewind
description: Rewind any video into an editable HyperFrames project for free - motion graphics, UI demos, talking heads, live action or animated films. Measure it, watch it frame by frame, rebuild every layer in HTML, render locally and check the render against the original frame by frame until it matches. Use to reverse, rewind, recreate, replicate, remix or study a video, on any HyperFrames plan with no credits.
---

# Rewind

Rewind turns a finished video back into its parts: a HyperFrames project with every title, card, caption and move rebuilt in HTML and placed from measurements, plus the pieces that cannot be drawn (people, photos, painted shots) cut from the original. You render it locally and score it against the original frame by frame. The goal is a render you cannot tell apart at a glance, which you can then edit.

It costs nothing. It uses the free HyperFrames commands (`measure`, `snapshot`, `check`, `diff`, local `render`, local `transcribe --engine whisper`, local `remove-background`) and the scripts in `scripts/`, which need only ffmpeg and Python's standard library. Anything that bills (cloud renders, hosted reverse jobs, generated media, hosted transcription) is out of scope; if a better result would need one, say so after the free rebuild and let the person decide.

**Whose video.** Rewinding a video copies the work and the people in it. The person's own videos, or ones they hold the rights to, are fine. Anyone else's stays private: for study, never published or monetized, and downloaded only where the person may do that.

Read `references/intake.md` first. For people on screen read `references/people.md`; for drawn layers `references/drawn.md`; for painted or 3D films `references/painted.md`. When the person wants their own footage and brand in the video's structure, that is a remix: `references/remix.md`, and for "N free tools" style lists, `templates/list-reel/`.

## Tools

| To learn | Run |
|---|---|
| canvas, exact rate, frame count, sound, problems | `scripts/probe.py <video>` (or `npx hyperframes measure probe`) |
| every cut, by frame | `scripts/cuts.py <video>` (or `measure cuts`) |
| when something changes inside a region | `scripts/cuts.py <video> --roi x,y,w,h --min 2 --ratio 3` (or `measure events --roi`) |
| consecutive frames, a strip, overview sheets | `scripts/frames.py <video> --range a,b \| --at t,... \| --every s [--roi]` |
| an edge's position every frame | `scripts/track.py <video> edges --col x \| --row y --frames a,b` |
| a region's brightness every frame (fades, fills) | `scripts/track.py <video> level --box x,y,w,h --frames a,b` |
| a text's ink box; yours against the original | `scripts/track.py <video> ink --box ... --frames n [--dark] [--vs render]` |
| font size, spacing and position of title words | `scripts/fitwords.py <video> lines.json out.json --css style.css` |
| a layer's scale and offset per frame | `scripts/fit.py boxes.json --ref N` |
| a clean backdrop from several frames | `scripts/plate.py <video> --frame N:boxes ...` |
| your project next to the original, at moments | `npx hyperframes snapshot . --at t,... --against <video>` |
| the score | `scripts/diff.py <video> <render> [--range a,b] [--sbs]` and `npx hyperframes diff <video> <render>` |

The scripts refuse sources with non-square pixels or a variable frame rate and print the ffmpeg line that fixes them. `diff.py` fails a render for a cut one frame off, a missing one-frame flash, a duration one frame off (whole-film runs) or any badly wrong cell of a 4x4 grid.

## The run

1. **Measure the source.** Probe it and copy its width, height, rate (keep NTSC rates as fractions) and frame-exact duration (frames ÷ rate) into the root composition. Find the cuts. Look at the frames either side of each cut yourself: a light change is not a cut, and a blur or flash around a cut belongs to the transition.
2. **See it.** Make overview sheets, then strips of consecutive frames at every change: entrances, exits, transitions, caption switches. One frame per second hides most of what matters.
3. **Sort the layers.** For each shot, name every layer and decide how it comes back:
   - drawn (text, cards, UI, captions, charts, stamps, counters): rebuilt in HTML;
   - photographic inside a frame (a photo, a logo, a product shot, a screen recording): cut from the original on its own box, or the real asset from its owner;
   - a person: kept as their own footage (`references/people.md`);
   - a painted or 3D world: plates plus code (`references/painted.md`);
   - the backdrop: a plate or a model of it (below).
   Never use the original's whole frame as a layer, except for a presenter who fills the frame, and then judge that shot only on what you drew over them.
4. **Build from numbers.** Every size, position, colour and time comes from a measurement, noted beside it in the code. The original's soundtrack plays as one `<audio>` over the whole film; every video clip is muted. Put times on exact frames: write frame ÷ rate rounded down, and start clips about a millisecond early (`data-start` = n/rate − 0.001), because the renderer's clock for frame n can fall just short of n/rate and the previous scene then lingers a frame. Never nest a timed `<video>` inside a timed wrapper: show scenes from the timeline instead.
5. **Check moments while building** with `snapshot --against`, then render the whole film locally and run both diffs. Fix what they show, render again, and stop after three rounds at most.
6. **Hand over** (`references/intake.md`): a side-by-side video, the project, plain-words numbers and a short `REWIND.md` (what is rebuilt, what is cut from the original, what is approximate, the last scores).

One agent holding the whole film works better than several agents each watching part of it.

## Lessons that cost us a round each

- **The backdrop.** A backdrop fixed to the screen is one plate stitched from frames where each part is clear (`plate.py`). If the middle is never clear, model it: grid lines from their measured spacing and profile, the vignette as a smooth base from the clear cells. Layouts that put a presenter in the bottom half often reuse the same backdrop shifted up; test shifts that keep the grid aligned.
- **Fades start early.** A change detector fires mid-fade; `track.py level` shows the first frame that moves, often 5-10 frames earlier.
- **Still cards drift.** "Static" cards often grow 2-4% over a few seconds. Track two opposite edges; if both move out, fit a linear scale about a point.
- **Unknown easing.** Measure the edge every frame and set it every frame. It matches by construction.
- **Each layer has its own camera.** In a zoom, titles, numbers and cards scale at different rates: fit each one (`fit.py`), not the group.
- **Motion blur.** Fast moves are often sharp. Look before adding blur, and never blur symmetrically on a one-direction move.
- **Text.** Fit size from the ink height, spacing from the ink width, position from the ink's top-left (`fitwords.py`), then compare with `track.py ink --vs`. Single-letter spans ignore `letter-spacing` in Chrome: space them with margins. A wider original cut: `scaleX` to the measured width.
- **Two-tone lines.** A line crossing from a light card to a dark ground is two colours: a gradient stroke with a hard stop at the edge.
- **Captions.** Read each switch from the caption band's pixels, not the transcript; captions lead and trail speech. Measure one word's fade and settled brightness: pure white usually reads too bright.
- **Dense reels take hours.** A short reel with a new card or word every second is a multi-hour rebuild. Say so after the first overview sheet.
- **Static renders look like flicker to a cut detector.** A render with no grain or encoder noise makes small changes look like cuts. `diff.py` compares both sides against the same noise floor; if you use another detector, do the same.
