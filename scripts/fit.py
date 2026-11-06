#!/usr/bin/env python3
"""Per-frame scale and offset for one layer, fitted from its measured boxes.

Layers in one shot often move at different rates (depth parallax): a title
grows 12% while the cards behind it grow 25%. Measure each layer's box every
frame (track.py ink, or edges), pick a reference frame where the layer sits at
its built position, and this prints, per frame, the [scale, x, y] that maps the
reference box onto that frame's box, about the screen's top-left. Put the layer
in a full-screen wrapper with transform-origin 0 0 and tl.set those values each
frame.

The fit uses the box's width for the scale, its left edge for x and its top for
y (--anchor center uses the centre instead, for a box whose edges blur).
Frames whose box is missing, or whose width jumps against its neighbours (a
fade or blur eating the edges), are dropped: fill them from a steadier layer.
Fit only frames where the whole layer is on screen: while text reveals letter
by letter its box grows with no move at all.

usage: fit.py <track-ink.json> --ref N [--key original] [--anchor left|center] [--max-jump 0.04]
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("boxes", help="JSON from track.py ink (uses its 'original' or --key boxes)")
    ap.add_argument("--ref", type=int, required=True)
    ap.add_argument("--key", default="original")
    ap.add_argument("--anchor", choices=["left", "center"], default="left")
    ap.add_argument("--max-jump", type=float, default=0.04, help="largest believable scale change per frame")
    a = ap.parse_args()
    boxes = {int(k): v for k, v in json.load(open(a.boxes))[a.key].items() if v}
    if a.ref not in boxes:
        raise SystemExit(f"no box at the reference frame {a.ref}")
    x0, y0, x1, y1 = boxes[a.ref]
    w0 = x1 - x0
    if w0 <= 0:
        raise SystemExit(f"the box at the reference frame {a.ref} has no width: pick a frame where the layer is whole")
    keys, dropped = {}, []
    frames = sorted(boxes)
    scale = {f: (boxes[f][2] - boxes[f][0]) / w0 for f in frames}
    for k, f in enumerate(frames):
        bx0, by0, bx1, by1 = boxes[f]
        s = scale[f]
        # A frame whose scale jumps away from both neighbours is a measuring glitch, not a move.
        nb = [scale[frames[j]] for j in (k - 1, k + 1) if 0 <= j < len(frames)]
        if nb and all(abs(s - n) > a.max_jump for n in nb):
            dropped.append(f)
            continue
        if a.anchor == "left":
            tx = bx0 - s * x0
        else:
            tx = (bx0 + bx1) / 2 - s * (x0 + x1) / 2
        ty = by0 - s * y0
        keys[f] = [round(s, 4), round(tx, 1), round(ty, 1)]
    print(json.dumps({"ref": a.ref, "ref_box": [x0, y0, x1, y1], "keys": keys, "dropped": dropped,
                      "use": "wrapper at 0,0 full screen, transform-origin 0 0; per frame tl.set({scale, x, y})"}))


if __name__ == "__main__":
    main()
