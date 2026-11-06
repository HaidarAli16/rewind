"""Shared helpers: find ffmpeg/ffprobe, run them, read a video's clock.

Only the Python standard library and ffmpeg are needed.
"""
import json
import os
import shutil
import subprocess
import sys
from fractions import Fraction


def tool(name):
    env = os.environ.get(name.upper())
    if env:
        return env
    for p in (f"/opt/homebrew/opt/ffmpeg-full/bin/{name}", shutil.which(name)):
        if p and os.path.exists(p):
            return p
    sys.exit(f"{name} not found: install ffmpeg (brew install ffmpeg) or set {name.upper()}=/path/to/{name}")


FFMPEG = tool("ffmpeg")
FFPROBE = tool("ffprobe")


def run(args, capture=True):
    r = subprocess.run(args, capture_output=capture, text=True)
    if r.returncode != 0:
        sys.exit(f"command failed ({r.returncode}): {' '.join(args)}\n{(r.stderr or '')[-2000:]}")
    return r


def probe(video):
    """Size as displayed, exact frame rate, frame count, duration, sound."""
    out = run([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", video]).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        sys.exit(f"no video stream in {video}")
    audio = any(s["codec_type"] == "audio" for s in d["streams"])
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if "rotate" in (v.get("tags") or {}):
        rot = int(v["tags"]["rotate"])
    if abs(rot) % 180 == 90:
        w, h = h, w
    # Pixels as decoded. A non-square-pixel (anamorphic) source is flagged, not resized here:
    # every tool decodes storage pixels, so conform it first (probe.py prints how).
    sar = v.get("sample_aspect_ratio", "1:1")
    anamorphic = sar not in ("1:1", "0:1", "N/A", None)

    def rate(text):
        try:
            f = Fraction(text or "0/1")
        except (ZeroDivisionError, ValueError):
            return Fraction(0)
        return f

    r_rate = rate(v.get("r_frame_rate"))
    a_rate = rate(v.get("avg_frame_rate"))
    fps = r_rate or a_rate
    if not fps:
        sys.exit(f"no frame rate in {video}: conform it first (ffmpeg -i in -r 30 out.mp4)")
    dur = float(v.get("duration") or d["format"].get("duration") or 0)
    frames = int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else 0
    if not frames:
        c = run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-count_packets",
                 "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", video]).stdout.strip()
        frames = int(c.split(",")[0]) if c else round(dur * float(fps))
    # Variable rate: the two rates disagree, or the frame count does not fit the clock.
    vfr = bool(r_rate and a_rate and abs(float(r_rate) - float(a_rate)) > 0.01)
    if dur and abs(frames - dur * float(fps)) > 1.5:
        vfr = True
    hdr = v.get("color_transfer") in ("smpte2084", "arib-std-b67")
    return {
        "video": video, "width": w, "height": h, "rotation": rot,
        "fps": float(fps), "fps_text": f"{fps.numerator}/{fps.denominator}" if fps.denominator != 1 else str(fps.numerator),
        "frames": frames, "duration": round(frames / float(fps), 6),
        "container_duration": dur, "audio": audio, "vfr": vfr, "hdr": hdr, "anamorphic": anamorphic, "sar": sar,
        "codec": v.get("codec_name"),
    }


def frame_time(frame, fps):
    """Frame index to seconds, rounded DOWN to 6 places so it never lands a frame late."""
    import math
    return math.floor(frame / fps * 1e6) / 1e6


def encoder():
    """Hardware H.264 on a Mac when available, else libx264."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-encoders"], capture_output=True, text=True)
    if "h264_videotoolbox" in r.stdout:
        return ["-c:v", "h264_videotoolbox", "-b:v", "12M"]
    return ["-c:v", "libx264", "-crf", "16", "-preset", "fast"]


def first_frame(t, fps):
    """The first frame shown at or after t seconds (what ffmpeg's -ss lands on)."""
    import math
    return max(0, math.ceil(t * fps - 1e-6))


def seek(frame, fps):
    """Input-seek arguments that start decoding exactly at this frame index."""
    return ["-ss", f"{(frame - 0.5) / fps:.6f}"] if frame > 0 else []


def check_box(box, w, h):
    x, y, bw, bh = box
    if x < 0 or y < 0 or bw <= 0 or bh <= 0 or x + bw > w or y + bh > h:
        sys.exit(f"box {x},{y},{bw},{bh} is not inside the {w}x{h} frame")


def square(p):
    """Stop on sources the frame tools cannot measure as they are."""
    if p.get("anamorphic"):
        sys.exit(f"{p['video']} has non-square pixels (SAR {p['sar']}): conform it first, see probe.py")
    return p
