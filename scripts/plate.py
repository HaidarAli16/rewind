#!/usr/bin/env python3
"""A clean backdrop plate, stitched from frames where nothing covers it.

Give frames in order of preference, each with the boxes its elements (and
their shadows) cover. Every pixel comes from the first frame that leaves it
free. It reports any pixel no frame leaves free: add a frame where that area
is clear (mid-transition frames often are). Only for a backdrop that holds
still on screen; check that first by comparing an empty corner across frames.

usage: plate.py <video> --frame N[:x0,y0,x1,y1[;x0,y0,x1,y1...]] [--frame ...] -o plate.png
example: plate.py src.mp4 --frame "0:130,170,1300,950;1340,170,1800,950" --frame "299:130,250,1070,840" -o plate.png
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ff import FFMPEG, probe, seek, square  # noqa: E402


def rgb(video, n, w, h, fps):
    out = subprocess.run([FFMPEG, "-loglevel", "error"] + seek(n, fps) + ["-i", video, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(out) != w * h * 3:
        sys.exit(f"could not read frame {n}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--frame", action="append", required=True)
    ap.add_argument("-o", "--out", default="plate.png")
    a = ap.parse_args()
    p = square(probe(a.video))
    W, H = p["width"], p["height"]
    srcs = []
    for spec in a.frame:
        n, _, boxes = spec.partition(":")
        rects = [tuple(int(v) for v in b.split(",")) for b in boxes.split(";") if b.strip()]
        srcs.append((int(n), rects, rgb(a.video, int(n), W, H, p["fps"])))
    # Per row, the covered x-ranges of each frame, so the inner loop stays cheap.
    out = bytearray(W * H * 3)
    missing, used = 0, {n: 0 for n, _, _ in srcs}
    for y in range(H):
        row_cov = [[(x0, x1) for x0, y0, x1, y1 in rects if y0 <= y <= y1] for _, rects, _ in srcs]
        for x in range(W):
            i = (y * W + x) * 3
            for k, (n, _, data) in enumerate(srcs):
                if not any(x0 <= x <= x1 for x0, x1 in row_cov[k]):
                    out[i:i + 3] = data[i:i + 3]
                    used[n] += 1
                    break
            else:
                out[i:i + 3] = srcs[0][2][i:i + 3]
                missing += 1
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                    "-i", "-", a.out], input=bytes(out), check=True)
    print({"plate": a.out, "pixels_from_frame": used, "covered_in_every_frame": missing})


if __name__ == "__main__":
    main()
