# Rewind

![Rewind: turn any video into an editable HyperFrames project, free](assets/cover.png)

Rewind is an agent skill that rebuilds any video as an editable [HyperFrames](https://github.com/heygen-com/hyperframes) project, then checks its render against the original frame by frame until they match. It works on any HyperFrames plan and costs no credits.

Give your agent a video and say "rewind this". It measures every cut to the frame, reads consecutive frames at every change, rebuilds text, cards, UI, captions and motion in HTML, keeps people and painted footage as clips cut on their own box, renders locally, and scores the result.

## Remix it

After a rebuild, ask for a remix: your own footage, script and brand in the original's structure (`references/remix.md`). For a numbered list video ("N free tools"), start from `templates/list-reel/`: fill in `spec.json` and `brand.css`.

## Install

```bash
npx skills add HaidarAli16/rewind
```

Or copy this folder into your agent's skills folder as `rewind` (for Claude Code: `~/.claude/skills/rewind`).

You need [ffmpeg](https://ffmpeg.org), Python 3 and Node (for `npx hyperframes`). The scripts use only the Python standard library.

## What's inside

| | |
|---|---|
| `SKILL.md` | the method: probe, cuts, layers, check |
| `references/intake.md` | starting a run, setting up the project, handing it over |
| `references/drawn.md` | matching drawn layers: timing from pixels, text fitted to its ink, looks, seek-safe recipes |
| `references/people.md` | people kept as their own footage, burned-in captions removed, text behind a person, cut-out checks |
| `references/painted.md` | painted and 3D films: code layers over plates |
| `scripts/probe.py` | size, exact frame rate, frame count, sound, what to fix first |
| `scripts/cuts.py` | every hard cut by its frame, with flashes told apart from cuts |
| `scripts/frames.py` | consecutive native frames, single moments or overview sheets, cropped to a region |
| `scripts/diff.py` | SSIM per frame and per cell of a 4x4 grid, cuts and flashes compared, worst moments, side-by-side video |
| `scripts/track.py` | per-frame numbers: an element's edges as it moves, a fade's level, a text box against your render's |
| `scripts/plate.py` | a clean backdrop plate stitched from the frames where each part of it is clear |
| `scripts/fit.py` | a layer's per-frame scale and offset, fitted from its measured boxes, for zooms where layers move at their own rates |
| `scripts/fitwords.py` | each title word's font size, letter-spacing and position, fitted to its ink in the original |
| `references/remix.md` | your own footage, words and brand in a video's structure: cutting your take, matching your voice, swapping the brand |
| `templates/list-reel/` | a ready "N free tools" vertical video: `spec.json` (your words, times, logos, recordings) + `brand.css` (your colours and fonts) → `build.py` |

`diff.py` is strict: a cut one frame off, a missing one-frame flash or a duration one frame off is a fail.

## Use it fairly

Rebuilding someone else's video copies their work and the people in it. Use this on videos the person made or has the rights to. A rebuild of anyone else's video is for private study only: don't publish or monetize it, and download a link only when the person may (whether study use is allowed depends on where they live and the site's terms).

## License

Apache-2.0 (`LICENSE`). Rewind is an independent project built on the open-source [HyperFrames](https://github.com/heygen-com/hyperframes) tools; it is not affiliated with or endorsed by HeyGen.
