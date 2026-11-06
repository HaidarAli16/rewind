#!/usr/bin/env python3
"""Fit each title word's font size, letter-spacing and position to its ink in the original.

Give each line of text as it sits in one settled frame: its words, the box that holds
the line's ink and nothing else, and how to tell ink from ground. The script splits the
line's ink into its words at the widest gaps, renders the same words in your page's
font (your stylesheet, at 100 px, in headless Chrome), measures their ink, and solves:

  size  from the ink height (same letters, so same proportions),
  ls    the letter-spacing in px that makes the ink width match,
  left, top  where the element's box goes so the ink lands on the original's.

usage: fitwords.py <video> lines.json out.json --css style.css [--cls w]

lines.json: [{"id": "t1", "words": ["Don't", "use"], "frame": 49, "box": [x, y, w, h],
              "dark": true, "thr": 150, "kind": "red", "size": 120, "top": 300}, ...]
  dark  true: ink is darker than thr (dark or red text on a light ground, the default);
        false: ink is brighter than thr (light text on a dark ground)
  kind  extra classes for the element (its colour classes), as in your page
  size, top  optional: hold these and solve only spacing and left (for a word whose
        top or bottom is hidden behind something)

The element is rendered as <div class="<cls> <kind>" style="position:absolute;line-height:1">,
so your CSS for that class must set the font family, weight, style and line-height.
Font URLs in the CSS are resolved from the CSS file's folder. Needs ffmpeg and the
Chrome that HyperFrames downloads (~/.cache/hyperframes/chrome).
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ff import FFMPEG, probe, seek, square  # noqa: E402


def chrome():
    hits = glob.glob(os.path.expanduser("~/.cache/hyperframes/chrome/**/chrome-headless-shell"), recursive=True)
    hits = [h for h in hits if os.path.isfile(h)]
    if not hits:
        sys.exit("no headless Chrome found: run any `npx hyperframes snapshot` once so HyperFrames downloads it")
    return hits[0]


def gray_frame(video, n, fps):
    r = subprocess.run([FFMPEG, "-loglevel", "error"] + seek(n, fps) + ["-i", video, "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    if r.returncode != 0:
        sys.exit(f"could not read frame {n}: {r.stderr[-500:].decode(errors='replace')}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("lines")
    ap.add_argument("out")
    ap.add_argument("--css", required=True)
    ap.add_argument("--cls", default="w")
    a = ap.parse_args()
    p = probe(a.video)
    square(p)
    W, H, fps = p["width"], p["height"], p["fps"]
    lines = json.load(open(a.lines))
    frames, targets = {}, {}
    for L in lines:
        f = L["frame"]
        if f not in frames:
            frames[f] = gray_frame(a.video, f, fps)
        g = frames[f]
        x, y, w, h = L["box"]
        thr, dark = L.get("thr", 150), L.get("dark", True)
        on = (lambda v: v < thr) if dark else (lambda v: v > thr)
        cols = [any(on(g[yy * W + xx]) for yy in range(y, y + h)) for xx in range(x, x + w)]
        runs, s = [], None
        for i, c in enumerate(cols + [False]):
            if c and s is None:
                s = i
            if not c and s is not None:
                runs.append([s, i - 1]); s = None
        n = len(L["words"])
        if len(runs) < n:
            sys.exit(f"{L['id']}: found {len(runs)} ink runs for {n} words; check the box and threshold")
        cuts = sorted(sorted(range(len(runs) - 1), key=lambda k: runs[k + 1][0] - runs[k][1], reverse=True)[:n - 1])
        start = 0
        for wd, c in zip(L["words"], cuts + [len(runs) - 1]):
            a0, b0 = runs[start][0], runs[c][1]
            start = c + 1
            rows = [yy for yy in range(y, y + h) if any(on(g[yy * W + xx]) for xx in range(x + a0, x + b0 + 1))]
            targets[(L["id"], wd)] = [x + a0, rows[0], x + b0, rows[-1]]

    items = list(targets)
    CW, CH = 1600, 300
    css_dir = os.path.dirname(os.path.abspath(a.css))
    cells = []
    for i, (lid, wd) in enumerate(items):
        L = next(l for l in lines if l["id"] == lid)
        cells.append(f'<div class="{a.cls} {L.get("kind", "")}" style="position:absolute;left:60px;top:{i * CH + 70}px;'
                     f'font-size:100px;letter-spacing:0;line-height:1">{wd}</div>')
    page = (f'<html><head><base href="file://{css_dir}/"><link rel="stylesheet" href="file://{os.path.abspath(a.css)}">'
            f'<style>html,body{{margin:0;width:{CW}px;height:{len(items) * CH}px;background:#fff;overflow:hidden}}'
            f'.{a.cls}{{color:#000 !important;-webkit-text-fill-color:#000 !important;background:none !important;'
            f'text-shadow:none !important;transform:none !important;filter:none !important;opacity:1 !important}}</style></head>'
            f'<body>{"".join(cells)}</body></html>')
    tmp = tempfile.mkdtemp()
    html, png = os.path.join(tmp, "fit.html"), os.path.join(tmp, "fit.png")
    open(html, "w").write(page)
    subprocess.run([chrome(), "--headless", "--disable-gpu", "--allow-file-access-from-files", "--hide-scrollbars",
                    f"--window-size={CW},{len(items) * CH}", "--virtual-time-budget=3000", f"--screenshot={png}", f"file://{html}"],
                   capture_output=True)
    G = subprocess.run([FFMPEG, "-loglevel", "error", "-i", png, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    res = {}
    for i, key in enumerate(items):
        y0 = i * CH
        rows = [yy for yy in range(y0, y0 + CH) if any(G[yy * CW + xx] < 128 for xx in range(CW))]
        cs = [xx for xx in range(CW) if any(G[yy * CW + xx] < 128 for yy in range(y0, y0 + CH))]
        if not rows:
            sys.exit(f"{key}: nothing rendered; check the CSS class and fonts")
        mx0, my0, mx1, my1 = cs[0] - 60, rows[0] - (y0 + 70), cs[-1] - 60, rows[-1] - (y0 + 70)
        tx0, ty0, tx1, ty1 = targets[key]
        L = next(l for l in lines if l["id"] == key[0])
        s = L["size"] / 100 if "size" in L else (ty1 - ty0) / (my1 - my0)
        ls = ((tx1 - tx0) - (mx1 - mx0) * s) / max(1, len(key[1]) - 1)
        res[f"{key[0]}:{key[1]}"] = {"size": round(100 * s, 1), "ls": round(ls, 2), "left": round(tx0 - mx0 * s, 1),
                                     "top": L["top"] if "top" in L else round(ty0 - my0 * s, 1), "ink": targets[key]}
        print(f"{key[0]}:{key[1]}", res[f"{key[0]}:{key[1]}"])
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
