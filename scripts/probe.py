#!/usr/bin/env python3
"""Print what the rebuild's root composition must be: size, rate, frames, duration, sound.

usage: probe.py <video>
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ff import probe  # noqa: E402

if len(sys.argv) != 2:
    sys.exit(__doc__)
p = probe(sys.argv[1])
notes = []
if p["vfr"]:
    notes.append("variable frame rate: conform it first (ffmpeg -i in -r <fps_text> -c:a copy cfr.mp4) and rebuild against that copy")
if p["hdr"]:
    notes.append("HDR source: compare against an SDR tone-mapped copy, or SSIM will read low everywhere")
if p["anamorphic"]:
    notes.append(f"non-square pixels (SAR {p['sar']}): conform first (ffmpeg -i in -vf scale=iw*sar:ih,setsar=1 -c:a copy square.mp4) and rebuild against that copy")
if p["rotation"]:
    notes.append(f"rotated {p['rotation']} deg in its metadata: width/height above are as displayed")
if not p["audio"]:
    notes.append("no sound: the rebuild has no <audio>")
if p["fps_text"].endswith("/1001"):
    notes.append(f"NTSC rate: data-fps stays the fraction {p['fps_text']}, and render with --fps {p['fps_text']}")
p["canvas"] = {"data-width": p["width"], "data-height": p["height"], "data-fps": p["fps_text"],
               "data-duration": p["duration"]}
p["notes"] = notes
print(json.dumps(p, indent=1))
