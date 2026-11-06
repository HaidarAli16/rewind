#!/usr/bin/env python3
"""Score your render against the original, frame by frame.

Reports SSIM over the whole frame (mean, 5th percentile, minimum), the worst of a
4x4 grid of cells per frame (a small wrong element hides in a whole-frame mean),
the cuts the original has that yours misses and the extra ones, the duration,
and the worst moments as original | yours pictures. --sbs also writes a
side-by-side video.

Pass: mean >= 0.92, p05 >= 0.85, cell p05 >= 0.75 (change with --min-*).

usage: diff.py <original> <yours.mp4> [--range a,b] [--offset s] [--worst 4] [--sbs] [--out dir]

--range scores only a,b seconds of the same timeline (render the whole film, then
score the part you changed). --offset s compares the original at t with yours
at t+s. The duration check runs only on a whole-film comparison.
"""
import argparse
import json
import math
import os
import re
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ff import FFMPEG, probe, run, encoder, frame_time, first_frame, seek, square  # noqa: E402
import cuts as cutmod  # noqa: E402

GRID = 4


def pct(values, q):
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def inputs(ref, yours, w):
    """Both videos opened at their window's first frame (exact, by frame index)."""
    return ([FFMPEG, "-hide_banner", "-nostats"] + seek(w["rf0"], w["fps"]) + ["-i", ref]
            + seek(w["yf0"], w["qfps"]) + ["-i", yours])


def ssim_run(ref, yours, p, w, out):
    W, H, fr, nf = p["width"], p["height"], p["fps_text"], w["n"]
    cw, ch = (W // GRID) // 2 * 2, (H // GRID) // 2 * 2
    n = GRID * GRID
    g = [f"[0:v]trim=end_frame={nf},setpts=PTS-STARTPTS,format=yuv420p,split={n + 1}[a]" + "".join(f"[a{i}]" for i in range(n)) + ";",
         f"[1:v]fps={fr},trim=end_frame={nf},setpts=PTS-STARTPTS,scale={W}:{H}:flags=bicubic,format=yuv420p,split={n + 1}[b]" + "".join(f"[b{i}]" for i in range(n)) + ";",
         f"[a][b]ssim=stats_file={os.path.join(out, 'ssim_full.log')}[o];"]
    for i in range(n):
        x, y = (i % GRID) * cw, (i // GRID) * ch
        g.append(f"[a{i}]crop={cw}:{ch}:{x}:{y}[ca{i}];[b{i}]crop={cw}:{ch}:{x}:{y}[cb{i}];"
                 f"[ca{i}][cb{i}]ssim=stats_file={os.path.join(out, f'ssim_c{i:02d}.log')},nullsink;")
    args = inputs(ref, yours, w) + ["-filter_complex", "".join(g).rstrip(";"),
                                                     "-map", "[o]", "-f", "null", "-"]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ssim failed:\n" + r.stderr[-2000:])

    def read(path):
        return [float(m) for m in re.findall(r"All:([\d.]+)", open(path).read())]
    full = read(os.path.join(out, "ssim_full.log"))
    cells = [read(os.path.join(out, f"ssim_c{i:02d}.log")) for i in range(n)]
    m = min([len(full)] + [len(c) for c in cells])
    worst_cell = [min(c[k] for c in cells) for k in range(m)]
    worst_cell_idx = [min(range(n), key=lambda i: cells[i][k]) for k in range(m)]
    return full[:m], worst_cell, worst_cell_idx


def picture(ref, yours, frame, w, p, path, cell=None):
    W, H = p["width"], p["height"]
    box = ""
    if cell is not None:
        cw, ch = (W // GRID) // 2 * 2, (H // GRID) // 2 * 2
        x, y = (cell % GRID) * cw, (cell // GRID) * ch
        box = f",drawbox=x={x}:y={y}:w={cw}:h={ch}:color=red@0.9:t=6"
    run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y"] + seek(frame, w["fps"]) + ["-i", ref]
        + seek(frame + w["off"], w["qfps"]) + ["-i", yours, "-filter_complex",
         f"[0:v]scale={W}:{H}{box}[l];[1:v]scale={W}:{H}{box}[r];[l][r]hstack,scale=1600:-2",
         "-frames:v", "1", path])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("yours")
    ap.add_argument("--range")
    ap.add_argument("--offset", type=float, default=0.0, help="compare the original at t with yours at t+offset")
    ap.add_argument("--worst", type=int, default=4)
    ap.add_argument("--min-mean", type=float, default=0.92)
    ap.add_argument("--min-p05", type=float, default=0.85)
    ap.add_argument("--min-cell", type=float, default=0.75)
    ap.add_argument("--sbs", action="store_true")
    ap.add_argument("--out", default="diff")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    p, q = square(probe(a.original)), square(probe(a.yours))
    fps = p["fps"]
    # The window in the original's frames, and the matching frames of yours (offset in whole frames).
    off = round(a.offset * fps)
    rf0, rf1 = 0, p["frames"]
    if a.range:
        s0, s1 = (float(v) for v in a.range.split(","))
        rf0, rf1 = first_frame(s0, fps), min(p["frames"], first_frame(s1, fps))
    rf0 = max(rf0, -off)                      # yours has no frames before its start
    rf1 = min(rf1, q["frames"] - off)         # nor after its end
    if rf1 - rf0 < 2:
        sys.exit("the window holds fewer than 2 frames of both videos: check --range and --offset")
    w = {"rf0": rf0, "yf0": rf0 + off, "n": rf1 - rf0, "off": off, "fps": fps, "qfps": q["fps"]}
    start, end = frame_time(rf0, fps), frame_time(rf1, fps)
    whole = not a.range and off == 0
    logs = os.path.join(a.out, "logs")
    os.makedirs(logs, exist_ok=True)
    full, cell, cell_idx = ssim_run(a.original, a.yours, p, w, logs)
    if not full:
        sys.exit("no frames were compared")
    f0 = rf0

    # Worst moments, at least half a second apart.
    order = sorted(range(len(cell)), key=lambda k: (cell[k] + full[k]) / 2)
    picked = []
    for k in order:
        if all(abs(k - j) > fps / 2 for j in picked):
            picked.append(k)
        if len(picked) >= a.worst:
            break
    worst = []
    for k in sorted(picked):
        t = frame_time(f0 + k, fps)
        path = os.path.join(a.out, f"worst_{f0 + k:06d}.png")
        picture(a.original, a.yours, f0 + k, w, p, path, cell_idx[k])
        worst.append({"t": t, "frame": f0 + k, "ssim": round(full[k], 4), "worst_cell": round(cell[k], 4),
                      "cell": {"col": cell_idx[k] % GRID, "row": cell_idx[k] // GRID}, "picture": path})

    # Long stretches below the bar, so a whole wrong shot shows as one span.
    spans, run_start = [], None
    for k, v in enumerate(full + [1.0]):
        bad = v < a.min_p05 or (k < len(cell) and cell[k] < a.min_cell)
        if bad and run_start is None:
            run_start = k
        if not bad and run_start is not None:
            if k - run_start >= max(3, fps / 5):
                spans.append([frame_time(f0 + run_start, fps), frame_time(f0 + k, fps)])
            run_start = None

    # Cuts on both sides.
    # Each side's spikes are measured against the quiet level of both, so a render that is perfectly
    # still between changes (no grain, no encoder noise) is not flagged for cuts the original also has.
    dr = cutmod.diffs(a.original, rf0, rf1, fps)
    dy = cutmod.diffs(a.yours, w["yf0"], w["yf0"] + w["n"], q["fps"])
    rc, rf = cutmod.find(dr, fps, rf0, video=a.original, other=dy)
    yc, yf = cutmod.find(dy, q["fps"], w["yf0"], video=a.yours, other=dr)
    rt = [c["t"] for c in rc]
    yt = [frame_time(c["frame"] - off, fps) for c in yc]
    tol = 1.5 / fps
    missing = [t for t in rt if not any(abs(t - u) <= tol for u in yt)]
    extra = [t for t in yt if not any(abs(t - u) <= tol for u in rt)]
    late = [{"original": t, "yours": u, "frames": round((u - t) * fps)} for t in rt for u in yt
            if 1e-6 < abs(t - u) <= tol]
    rft = [c["t"] for c in rf]
    yft = [frame_time(c["frame"] - off, fps) for c in yf]
    flashes_missing = [t for t in rft if not any(abs(t - u) <= tol for u in yft)]

    res = {
        "original": a.original, "yours": a.yours, "window": [start, end], "window_frames": [rf0, rf1],
        "offset_frames": off,
        "frames_compared": len(full),
        "ssim": {"mean": round(statistics.fmean(full), 4), "p05": round(pct(full, 0.05), 4),
                 "min": round(min(full), 4), "cell_p05": round(pct(cell, 0.05), 4)},
        "thresholds": {"mean": a.min_mean, "p05": a.min_p05, "cell": a.min_cell},
        "duration": {"original": p["duration"], "yours": q["duration"],
                     "off_by_frames": round((q["duration"] - p["duration"]) * fps)},
        "size": {"original": [p["width"], p["height"]], "yours": [q["width"], q["height"]]},
        "cuts": {"original": rt, "yours": yt, "missing": missing, "extra": extra, "off_by_a_frame": late},
        "flashes": {"original": rft, "yours": yft, "missing": flashes_missing},
        "bad_spans": spans, "worst": worst,
    }
    fails = []
    if res["ssim"]["mean"] < a.min_mean:
        fails.append("mean SSIM")
    if res["ssim"]["p05"] < a.min_p05:
        fails.append("p05 SSIM")
    if res["ssim"]["cell_p05"] < a.min_cell:
        fails.append("worst cell SSIM: a small element is wrong")
    if missing or extra:
        fails.append("cuts missing or extra")
    if late:
        fails.append("cuts a frame off")
    if flashes_missing:
        fails.append("flashes missing")
    if whole and res["duration"]["off_by_frames"] != 0:
        fails.append("duration")
    if res["size"]["original"] != res["size"]["yours"]:
        fails.append("frame size")
    res["fails"] = fails
    res["pass"] = not fails
    if a.sbs:
        sbs = os.path.join(a.out, "side_by_side.mp4")
        W, H = p["width"], p["height"]
        nf = w["n"]
        args = inputs(a.original, a.yours, w) + [
            "-filter_complex",
            f"[0:v]trim=end_frame={nf},setpts=PTS-STARTPTS,scale={W}:{H}[l];"
            f"[1:v]fps={p['fps_text']},trim=end_frame={nf},setpts=PTS-STARTPTS,scale={W}:{H}[r];[l][r]hstack[v]",
            "-map", "[v]", "-map", "0:a?", "-t", f"{nf / fps:.6f}"] + encoder() + ["-c:a", "aac", "-y", sbs]
        run(args)
        res["side_by_side"] = sbs
    json.dump(res, open(os.path.join(a.out, "diff.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
