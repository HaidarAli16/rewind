#!/usr/bin/env python3
"""Find every hard cut by its frame, jump cuts and punch-ins included.

Scene scores miss cuts inside one take, so this reads the plain frame-to-frame
difference on a small grey copy and keeps the spikes that stand far above their
neighbourhood. A spike that is answered by a second spike within 3 frames is a
flash or a whip, listed under not_cuts: read those frames before trusting either.

usage: cuts.py <video> [--start s] [--end s] [--min 6] [--ratio 4] [--roi x,y,w,h]
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ff import FFMPEG, probe, frame_time, first_frame, seek, check_box, square  # noqa: E402


def diffs(video, f0, f1, fps, roi=None):
    """Mean absolute luma difference between frame i and i+1 for frames f0..f1-1; index 0 is f0->f0+1."""
    args = [FFMPEG, "-hide_banner", "-nostats"] + seek(f0, fps) + ["-i", video, "-frames:v", str(max(0, f1 - f0)),
            "-an", "-vf",
            (f"format=gray,crop={roi[2]}:{roi[3]}:{roi[0]}:{roi[1]}," if roi else "") +
            "scale=192:-2:flags=area,format=gray,tblend=all_mode=difference,"
            "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
            "-f", "null", "-"]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed reading {video}:\n{r.stderr[-1500:]}")
    return [float(m) for m in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", r.stdout)]


def gray(video, frame, fps):
    """One frame, by its index, as a small grey byte string, for comparing two frames directly.

    Seeks a second early, then counts frames from there, so the frame is exact
    whatever the container's start time or B-frame layout.
    """
    lead = min(frame, int(round(fps)))
    args = [FFMPEG, "-hide_banner", "-loglevel", "error"] + seek(frame - lead, fps)
    args += ["-i", video, "-an", "-vf",
             f"select='eq(n\\,{lead})',scale=192:108:flags=area,format=gray",
             "-frames:v", "1", "-f", "rawvideo", "-"]
    return subprocess.run(args, capture_output=True).stdout


def mad(a, b):
    n = min(len(a), len(b))
    return sum(abs(a[k] - b[k]) for k in range(n)) / n if n else 999.0


def find(d, fps, offset_frame=0, min_change=6.0, ratio=4.0, video=None, other=None):
    """Spikes in the difference signal, grouped into bursts.

    other: the same signal from the video this one is compared with, frame for frame.
    A spike must then stand above the quiet level of both, so a render that holds
    perfectly still between changes is judged on the same scale as a noisy original.

    One spike alone is a cut. A burst of spikes within 3 frames of each other is a
    flash, a whip or a cut with a transition: when the frame before the burst and
    the frame after it look alike, nothing changed shots (a flash), else it is a
    cut at the largest spike.
    """
    cuts, not_cuts, spikes = [], [], []
    n = len(d)
    for i, v in enumerate(d):
        lo, hi = max(0, i - 15), min(n, i + 16)
        around = [d[j] for j in range(lo, hi) if abs(j - i) > 3]
        base = statistics.median(around) if around else 0.0
        if other is not None:
            around_o = [other[j] for j in range(lo, min(hi, len(other))) if abs(j - i) > 3]
            if around_o:
                base = max(base, statistics.median(around_o))
        if v >= min_change and v >= ratio * base + 2:
            spikes.append((i, v, base))
    bursts = []
    for s in spikes:
        if bursts and s[0] - bursts[-1][-1][0] <= 3:
            bursts[-1].append(s)
        else:
            bursts.append([s])
    for b in bursts:
        i, v, base = max(b, key=lambda s: s[1])
        frame = offset_frame + i + 1  # tblend frame i compares i and i+1: the new shot starts at i+1
        entry = {"t": frame_time(frame, fps), "frame": frame, "change": round(v, 1),
                 "above_neighbours": round(v / (base + 0.01), 1)}
        if len(b) == 1:
            cuts.append(entry)
            continue
        first, last = offset_frame + b[0][0], offset_frame + b[-1][0] + 1
        same = None
        if video:
            same = mad(gray(video, first, fps), gray(video, last, fps))
        if same is not None and same < max(min_change, 0.35 * v):
            entry.update({"t": frame_time(first + 1, fps), "frame": first + 1,
                          "kind": "flash: the picture before and after match",
                          "frames": [first + 1, last - 1], "before_after_change": round(same, 1)})
            not_cuts.append(entry)
        else:
            entry["burst"] = [first + 1, last]
            entry["kind"] = "cut inside a burst (blur, whip or flash at the cut): read these frames"
            cuts.append(entry)
    return cuts, not_cuts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--min", type=float, default=6.0, help="smallest change that can be a cut (0-255 luma)")
    ap.add_argument("--ratio", type=float, default=4.0, help="how far above its neighbourhood a cut must stand")
    ap.add_argument("--roi", help="x,y,w,h: only watch this region (a caption band: --roi ... --min 2 --ratio 3)")
    a = ap.parse_args()
    p = square(probe(a.video))
    fps = p["fps"]
    f0 = first_frame(a.start, fps)
    f1 = min(p["frames"], first_frame(a.end, fps)) if a.end else p["frames"]
    if f1 - f0 < 2:
        sys.exit(f"nothing to read between {a.start}s and {a.end or p['duration']}s")
    start, end = frame_time(f0, fps), frame_time(f1, fps)
    roi = [int(v) for v in a.roi.split(",")] if a.roi else None
    if roi:
        check_box(roi, p["width"], p["height"])
    d = diffs(a.video, f0, f1, fps, roi)
    cuts, not_cuts = find(d, fps, f0, a.min, a.ratio, None if roi else a.video)
    bounds = [start] + [c["t"] for c in cuts] + [end]
    shots = [{"start": bounds[k], "end": bounds[k + 1], "seconds": round(bounds[k + 1] - bounds[k], 4)}
             for k in range(len(bounds) - 1)]
    print(json.dumps({"video": a.video, "fps": p["fps_text"], "start": start, "end": end,
                      "cuts": cuts, "not_cuts": not_cuts, "shots": shots}, indent=1))


if __name__ == "__main__":
    main()
