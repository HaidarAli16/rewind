#!/usr/bin/env python3
"""Frames of a video as pictures, named by their frame number.

  --range a,b   consecutive native frames from a to b seconds, plus one strip
  --at t,t,...  one full-size picture per moment
  --every n     an overview sheet, one frame every n seconds
  --roi x,y,w,h crop to a region (video pixels); --width sets the picture width

usage: frames.py <video> (--range a,b | --at t,... | --every n) [--roi x,y,w,h] [--max 16] [--width 480] [--out dir]
"""
import argparse
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ff import FFMPEG, probe, run, seek, check_box, square  # noqa: E402


def crop_scale(roi, width):
    f = ["format=rgb24"]  # crop in RGB: a crop in 4:2:0 snaps odd coordinates to even
    if roi:
        x, y, w, h = roi
        f.append(f"crop={w}:{h}:{x}:{y}")
    if width:
        f.append(f"scale={width}:-2:flags=lanczos")
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--range")
    ap.add_argument("--at")
    ap.add_argument("--every", type=float)
    ap.add_argument("--roi")
    ap.add_argument("--max", type=int, default=16)
    ap.add_argument("--width", type=int, default=480, help="0 keeps the region's own size")
    ap.add_argument("--out", default="frames")
    a = ap.parse_args()
    p = square(probe(a.video))
    fps = p["fps"]
    roi = [int(v) for v in a.roi.split(",")] if a.roi else None
    if roi:
        check_box(roi, p["width"], p["height"])
    os.makedirs(a.out, exist_ok=True)
    result = {"video": a.video, "fps": p["fps_text"], "out": a.out}

    if a.range:
        s, e = (float(v) for v in a.range.split(","))
        f0, f1 = math.floor(s * fps + 1e-6), min(p["frames"], math.ceil(e * fps - 1e-6))
        if f1 <= f0:
            sys.exit(f"--range {a.range} holds no frames (the video has {p['frames']} frames at {p['fps_text']} fps)")
        total = f1 - f0
        step = max(1, math.ceil(total / a.max))
        # Seek to the range, then count frames from there: exact and fast on long videos.
        vf = [f"select='not(mod(n\\,{step}))'"] + crop_scale(roi, a.width)
        tag = f"r{f0:06d}-{f1:06d}"
        for old in glob.glob(os.path.join(a.out, f"{tag}_*.png")):
            os.remove(old)
        run([FFMPEG, "-hide_banner", "-loglevel", "error"] + seek(f0, fps) + ["-i", a.video, "-frames:v", str(math.ceil(total / step)),
             "-an", "-vf", ",".join(vf), "-fps_mode", "passthrough", os.path.join(a.out, f"{tag}_tmp%05d.png")])
        pics = []
        for k, tmp in enumerate(sorted(glob.glob(os.path.join(a.out, f"{tag}_tmp*.png")))):
            named = os.path.join(a.out, f"{tag}_{f0 + k * step:06d}.png")
            os.replace(tmp, named)
            pics.append(named)
        cols = min(len(pics), 4)
        rows = math.ceil(len(pics) / cols) if pics else 0
        strip = os.path.join(a.out, f"{tag}_strip.png")
        if pics:
            run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-pattern_type", "glob", "-i",
                 os.path.join(a.out, f"{tag}_0*.png"), "-vf", f"tile={cols}x{rows}:padding=4:color=white",
                 "-frames:v", "1", strip])
        result.update({"range_frames": [f0, f1], "every_nth_frame": step, "frames": len(pics),
                       "pictures": pics, "strip": strip if pics else None,
                       "note": "file names carry the frame number; the strip reads left to right, top to bottom"})
    elif a.at:
        pics = []
        for t in (float(v) for v in a.at.split(",")):
            fr = min(p["frames"] - 1, math.floor(t * fps + 1e-6))
            out = os.path.join(a.out, f"at{fr:06d}.png")
            vf = crop_scale(roi, a.width)
            run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y"] + seek(fr, fps) + ["-i", a.video, "-an", "-vf", ",".join(vf),
                 "-frames:v", "1", out])
            pics.append({"t": t, "frame": fr, "picture": out})
        result["pictures"] = pics
    elif a.every:
        n = max(1, round(a.every * fps))
        vf = [f"select='not(mod(n\\,{n}))'"] + crop_scale(roi, a.width or 320) + ["tile=6x4:padding=4:color=white"]
        pattern = os.path.join(a.out, f"every{a.every:g}s_%02d.png")
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", a.video, "-an", "-vf", ",".join(vf),
             "-fps_mode", "passthrough", pattern])
        result["sheets"] = sorted(glob.glob(os.path.join(a.out, f"every{a.every:g}s_*.png")))
        result["note"] = f"24 frames per sheet, one every {a.every:g}s, left to right, top to bottom"
    else:
        sys.exit("give --range, --at or --every")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
