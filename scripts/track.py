#!/usr/bin/env python3
"""Measure things per frame, to set keyframes from the original's own numbers.

  edges  --col x | --row y   where bright (or dark) runs start and end along one
                             column or row, every frame: a card's top and bottom
                             as it slides, a bar as it grows
  level  --box x,y,w,h       the mean brightness of a box every frame: when a fade
                             starts and ends, a fill's ramp, a flash
  ink    --box x,y,w,h       the bounds of the ink (pixels brighter than --thr, or darker with --dark) in
                             a box; with --vs <render>, the same box in your render
                             and the difference, edge by edge

usage: track.py <video> edges (--col x | --row y) --frames a,b [--thr 60] [--min 8]
       track.py <video> level --box x,y,w,h --frames a,b
       track.py <video> ink --box x,y,w,h --frames a[,b] [--thr 150] [--dark] [--vs render.mp4]
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ff import FFMPEG, probe, seek, check_box, square  # noqa: E402


def gray(video, a, b, crop, fps):
    """Grey pixels of frames a..b inside crop=(x,y,w,h), as one bytes per frame."""
    x, y, w, h = crop
    r = subprocess.run([FFMPEG, "-loglevel", "error"] + seek(a, fps) + ["-i", video, "-frames:v", str(b - a + 1),
                        "-vf", f"format=gray,crop={w}:{h}:{x}:{y}", "-fps_mode", "passthrough",
                        "-f", "rawvideo", "-"], capture_output=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed reading {video}:\n{r.stderr[-1500:].decode(errors='replace')}")
    out = r.stdout
    n = w * h
    return [out[i * n:(i + 1) * n] for i in range(len(out) // n)]


def runs(vals, thr, dark=False, min_len=8):
    out, s = [], None
    for i, v in enumerate(list(vals) + [None]):
        on = v is not None and ((v < thr) if dark else (v > thr))
        if on and s is None:
            s = i
        if not on and s is not None:
            if i - s >= min_len:
                out.append([s, i - 1])
            s = None
    return out


def ink_box(px, w, h, thr, dark=False):
    if dark:  # dark or coloured ink on a light ground: pixels darker than thr
        rows = [r for r in range(h) if min(px[r * w:(r + 1) * w]) < thr]
        cols = [c for c in range(w) if min(px[c::w]) < thr]
    else:
        rows = [r for r in range(h) if max(px[r * w:(r + 1) * w]) > thr]
        cols = [c for c in range(w) if max(px[c::w]) > thr]
    return [cols[0], rows[0], cols[-1], rows[-1]] if rows and cols else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("what", choices=["edges", "level", "ink"])
    ap.add_argument("--frames", required=True, help="a,b (inclusive) or one frame")
    ap.add_argument("--col", type=int)
    ap.add_argument("--row", type=int)
    ap.add_argument("--box")
    ap.add_argument("--thr", type=float)
    ap.add_argument("--dark", action="store_true", help="edges: track dark runs; ink: ink darker than --thr (dark or red text on a light ground)")
    ap.add_argument("--min", type=int, default=8)
    ap.add_argument("--vs")
    a = ap.parse_args()
    p = square(probe(a.video))
    W, H, fps = p["width"], p["height"], p["fps"]
    fr = [int(v) for v in a.frames.split(",")]
    f0, f1 = max(0, fr[0]), min(p["frames"] - 1, fr[-1])
    if f1 < f0:
        sys.exit(f"--frames {a.frames} is outside the video's {p['frames']} frames")
    res = {"video": a.video, "what": a.what, "frames": [f0, f1]}

    if a.what == "edges":
        if a.col is not None:
            cx = a.col - a.col % 2
            crop, step, along = (cx, 0, 2, H), 2, "y"
        elif a.row is not None:
            cy = a.row - a.row % 2
            crop, step, along = (0, cy, W, 2), 1, "x"
        else:
            sys.exit("edges needs --col or --row")
        thr = a.thr if a.thr is not None else 60
        per = {}
        if a.col is not None and not 0 <= a.col < W or a.row is not None and not 0 <= a.row < H:
            sys.exit("--col/--row is outside the frame")
        for k, px in enumerate(gray(a.video, f0, f1, crop, fps)):
            line = px[0::step][:H] if a.col is not None else px[:W]
            per[f0 + k] = runs(line, thr, a.dark, a.min)
        res.update({"along": along, "threshold": thr, "runs": per})
    elif a.what == "level":
        x, y, w, h = (int(v) for v in a.box.split(","))
        check_box((x, y, w, h), W, H)
        res["box"] = [x, y, w, h]
        res["mean"] = {f0 + k: round(sum(px) / len(px), 2) for k, px in enumerate(gray(a.video, f0, f1, (x, y, w, h), fps))}
    else:
        x, y, w, h = (int(v) for v in a.box.split(","))
        check_box((x, y, w, h), W, H)
        thr = a.thr if a.thr is not None else 150
        def boxes(v):
            return {f0 + k: (lambda b: [b[0] + x, b[1] + y, b[2] + x, b[3] + y] if b else None)(ink_box(px, w, h, thr, a.dark))
                    for k, px in enumerate(gray(v, f0, f1, (x, y, w, h), fps))}
        o = boxes(a.video)
        res.update({"box": [x, y, w, h], "threshold": thr, "original": o})
        if a.vs:
            m = boxes(a.vs)
            res["yours"] = m
            res["delta"] = {f: ([mm - oo for oo, mm in zip(o[f], m[f])] if o.get(f) and m.get(f) else None) for f in o}
            res["note"] = "delta is yours minus original: left, top, right, bottom in pixels"
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
