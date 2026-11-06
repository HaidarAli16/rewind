#!/usr/bin/env python3
"""list-reel: a numbered "N tools / skills / libraries" vertical video (1080x1920) from a spec.

usage: python3 build.py spec.json [--out ../index.html]

Structure (a common short-form list format):
  hook   full-screen face + a headline card on top + caption pills
  intro  "these N" title + N chips (blurred logos) + the face in an accent-ringed box
  item   per item: a chip zooming in with the real logo and name, then the item's real
         screen recording in a browser frame over the half-screen face, captions on the seam
  cta    follow button -> following, the keyword typed and posted, the N links landing in a DM

Everything visual comes from brand.css (tokens) and base.css (components). Times are seconds
on YOUR cut voice; take them from a word-level transcript (whisper-cli --dtw, or
`npx hyperframes transcribe --engine whisper`). Captions are [text, start] pairs; mark the one
accent word with *stars*. Face videos: a half-screen panel (1080x960) and a full-screen one
(1080x1920) cut from the same take with the same timing; each item's demo is a short
screen recording. See README.md in this folder.
"""
import argparse, html as H, json, os, re

ap = argparse.ArgumentParser()
ap.add_argument("spec")
ap.add_argument("--out")
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(a.spec))
FPS, DUR = S.get("fps", 30), S["duration"]
FACE_HALF, FACE_FULL = S["face_half"], S["face_full"]
EPS = 0.001  # clips start 1 ms early: the renderer's time for frame n can land just under n/fps
out_html, IN, HARD, SCENES, ANIM = [], [], [], [], []


def esc(t): return H.escape(t, quote=False)
def accent(t): return re.sub(r"\*([^*]+)\*", r"<b>\1</b>", esc(t))


def scene(id_, t0, t1, inner):
    # scenes are shown by the timeline (visibility); only the videos inside are timed clips
    out_html.append(f'<div id="{id_}" class="scene" style="visibility:hidden">{inner}</div>')
    SCENES.append((id_, t0, t1))


def video(id_, t0, t1, src, x, y, w, h, media_start=None, track=2):
    ms = t0 if media_start is None else media_start
    return (f'<video id="{id_}" class="clip abs" src="{src}" muted playsinline data-start="{max(0, t0 - EPS):.4f}" '
            f'data-duration="{t1 - t0:.4f}" data-media-start="{max(0, ms - EPS):.4f}" data-track-index="{track}" '
            f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;object-fit:cover"></video>')


def half(id_, t0, t1):
    return '<div class="abs fhalf">' + video(id_, t0, t1, FACE_HALF, 0, 0, 1080, 960) + '</div><div class="abs seam"></div>'


def captions(prefix, cy, items, end):
    out = ""
    for i, (t, s) in enumerate(items):
        e = items[i + 1][1] if i + 1 < len(items) else end
        out += f'<div id="{prefix}{i}" class="tag" style="left:540px;top:{cy}px"><span>{accent(t)}</span></div>'
        HARD.append((f"#{prefix}{i}", s, e))
    return out


def line(id_, y, size, words):
    """words = [(word, accent?, id, start)]: each word enters on its own time."""
    sp = '<span style="display:inline-block;width:.26em"></span>'.join(
        f'<span id="{wid}" class="w{" acc" if acc else ""}" style="font-size:{size * (1.12 if acc else 1):.0f}px">{esc(w)}</span>' for w, acc, wid, _ in words)
    for w, acc, wid, t in words:
        IN.append((f"#{wid}", t, "drop", 0.2))
    return f'<div id="{id_}" class="line" style="top:{y}px;font-size:{size}px">{sp}</div>'


def chip(num, logo, name, x, y, s, blur=False, id_=""):
    pins = "".join(f'<i style="left:{70 + k * 42}px"></i>' for k in range(8))
    fb = "filter:blur(16px);" if blur else ""
    return (f'<div id="{id_}" class="chip abs" style="left:{x}px;top:{y}px;transform:scale({s})"><div class="pins">{pins}</div>'
            f'<div class="chip-body"><div class="chip-num">{esc(num)}</div><div class="chip-rule"></div>'
            f'<div class="chip-logo" style="{fb}"><img src="{logo}"></div>'
            f'<div class="chip-name" style="{"filter:blur(12px);opacity:.5;" if blur else ""}">{esc(name)}</div><div class="chip-dash"></div></div></div>')


def words_of(spec_words, prefix):
    return [(w["text"], w.get("accent", False), f"{prefix}{i}", w["t"]) for i, w in enumerate(spec_words)]


# ---------- hook ----------
hk = S["hook"]
scene("s_hook", 0, hk["end"], video("hook_face", 0, hk["end"], FACE_FULL, 0, 0, 1080, 1920)
      + '<div id="hook_card" class="hcard abs">' + "".join(f"<div>{re.sub(r'[*]([^*]+)[*]', r'<i>\1</i>', esc(l))}</div>" for l in hk["card"]) + "</div>"
      + captions("hook_t", 1320, hk["captions"], hk["end"]))
IN.append(("#hook_card", 0.0, "pop", 0.3))

# ---------- intro: these N ----------
it = S["intro"]
items = S["items"]
n = len(items)
s = min(0.6, (1080 - 120 - (n - 1) * 30) / n / 460)
cw = 460 * s
x0 = (1080 - (n * cw + (n - 1) * 30)) / 2
intro = line("in_l1", 140, 100, words_of(it["title"], "in_a"))
intro += "".join(chip(f"{i + 1:02d}", itm["logo"], itm["chip_label"], x0 + i * (cw + 30), 300, s, True, f"in_c{i}") for i, itm in enumerate(items))
intro += line("in_l2", 300 + 666 * s + 60, 84, words_of(it.get("subtitle", []), "in_b"))
intro += ('<div class="abs" style="left:0;top:1000px;width:1080px;height:960px;clip-path:inset(110px 57px 0 57px round 34px)">'
          + video("in_face", it["start"], it["end"], FACE_HALF, 0, 0, 1080, 960) + '</div>'
          '<div class="abs" style="left:57px;top:1110px;width:966px;height:860px;border:3px solid var(--accent);border-radius:34px"></div>')
scene("s_intro", it["start"], it["end"], intro)
for i in range(n):
    IN.append((f"#in_c{i}", it["start"] + 0.3 + i * 0.07, "cardrop", 0.4))

# ---------- items ----------
for k, itm in enumerate(items):
    p = f"i{k}"
    num = f"{k + 1:02d}"
    scene(f"s_{p}a", itm["t_chip"], itm["t_demo"],
          f'<div id="{p}_num" class="line" style="top:470px"><span class="w" style="font-size:150px">{num}</span></div>'
          + chip(num, itm["logo"], itm["chip_label"], 310, 650, 1.0, False, f"{p}_chip")
          + line(f"{p}_l", 1330, 120, words_of(itm["title"], f"{p}_t")))
    IN += [(f"#{p}_chip", itm["t_chip"], "zoomin", 0.22), (f"#{p}_num", itm["t_chip"] + 0.04, "drop", 0.2)]
    bw, bh = 900, round(900 * 750 / 1200)
    scene(f"s_{p}b", itm["t_demo"], itm["t_end"],
          f'<img src="{itm["logo"]}" id="{p}_ico" class="abs" style="left:90px;top:120px;width:76px;height:76px;border-radius:18px">'
          f'<div id="{p}_nm" class="abs" style="left:186px;top:126px;font:500 54px var(--font-head);letter-spacing:-.04em;color:var(--text)">{esc(itm["name"])}</div>'
          f'<div id="{p}_brw" class="brw abs" style="left:90px;top:230px;width:{bw}px;height:{bh + 52}px"><div class="bbar"><i></i><i></i><i></i><span>{esc(itm.get("domain", ""))}</span></div>'
          f'<div class="bview" style="height:{bh}px">' + video(f"{p}_demo", itm["t_demo"], itm["t_end"], itm["demo"], 0, 0, bw, bh, media_start=itm.get("demo_start", 0.3), track=3) + '</div></div>'
          + half(f"{p}_face", itm["t_demo"], itm["t_end"]) + captions(f"{p}_c", 962, itm["captions"], itm["t_end"]))
    IN += [(f"#{p}_brw", itm["t_demo"], "rise", 0.3), (f"#{p}_ico", itm["t_demo"] + 0.05, "pop", 0.2), (f"#{p}_nm", itm["t_demo"] + 0.08, "drop", 0.2)]

# ---------- cta ----------
c = S["cta"]
dm = "".join(f'<div id="cta_l{k}" class="abs" style="left:{40 + k * (760 // n)}px;top:84px;width:{760 // n - 16}px;height:130px;border-radius:18px;background:rgba(255,255,255,.04);box-shadow:0 0 0 1.5px var(--card-line) inset">'
             f'<img src="{itm["logo"]}" class="abs" style="left:50%;margin-left:-32px;top:16px;width:64px;height:64px;border-radius:16px">'
             f'<div class="abs" style="left:0;right:0;top:90px;text-align:center;font:500 22px var(--font-head);color:var(--text)">{esc(itm["name"])}</div></div>'
             for k, itm in enumerate(items))
cta = (f'<div id="cta_prof" class="card abs" style="left:120px;top:150px;width:840px;height:250px">'
       f'<div class="abs" style="left:44px;top:70px;font:500 56px var(--font-head);letter-spacing:-.04em;color:var(--text)">{esc(c["name"])}</div>'
       f'<div class="lab" style="left:46px;top:144px">{esc(c.get("tagline", ""))}</div>'
       '<div id="cta_fol" class="btn" style="right:36px;top:85px;width:230px;height:80px;background:var(--accent);color:var(--accent-ink);font-weight:700;font-size:34px;line-height:80px">Follow</div>'
       '<div id="cta_fold" class="btn" style="right:36px;top:85px;width:230px;height:80px;background:rgba(255,255,255,.08);color:var(--text);font-weight:600;font-size:32px;line-height:80px;opacity:0">Following ✓</div></div>'
       f'<div id="cta_dm" class="card abs" style="left:120px;top:150px;width:840px;height:250px;opacity:0"><div class="lab" style="left:40px;top:34px">DM · {n} LINKS SENT TO YOU</div>{dm}</div>'
       '<div id="cta_com" class="card abs" style="left:90px;top:440px;width:900px;height:470px">'
       '<div class="abs" style="left:0;width:900px;top:34px;text-align:center;font:600 38px var(--font-caption);color:var(--text)">Comments</div>'
       '<div class="abs" style="left:0;right:0;top:100px;height:1.5px;background:var(--card-line)"></div>'
       '<div id="cta_row" class="abs" style="left:40px;top:136px;width:820px;height:110px;opacity:0">'
       '<div class="abs" style="left:0;top:4px;width:84px;height:84px;border-radius:50%;background:rgba(255,255,255,.12);color:var(--text);font:700 36px/84px var(--font-caption);text-align:center">Y</div>'
       '<div class="abs" style="left:108px;top:2px;font:600 30px var(--font-caption);color:var(--text)">you <span style="color:var(--muted);font-weight:400;font-size:24px">now</span></div>'
       f'<div class="abs" style="left:108px;top:44px;font:700 40px var(--font-caption);color:var(--accent)">{esc(c["keyword"])}</div></div>'
       '<div class="abs" style="left:40px;top:306px;width:820px;height:104px;border-radius:52px;box-shadow:0 0 0 2px var(--card-line) inset">'
       '<span id="cta_ph" class="abs" style="left:40px;top:32px;font:400 36px var(--font-caption);color:var(--muted)">Add a comment…</span>'
       '<span id="cta_typ" class="abs" style="left:40px;top:26px;font:700 44px var(--font-caption);color:var(--text)"></span></div></div>'
       + half("cta_face", c["start"], DUR) + captions("cta_c", 962, c["captions"], DUR))
scene("s_cta", c["start"], DUR, cta)
IN += [("#cta_prof", c["start"] + 0.04, "rise", 0.3), ("#cta_com", c["t_comment"], "rise", 0.3)]
IN += [(f"#cta_l{k}", c["t_send"] + 0.06 + k * 0.12, "pop", 0.2) for k in range(n)]
kw = c["keyword"]
typing = "".join(f"tl.set('#cta_typ',{{textContent:{json.dumps(kw[:i + 1] + '|')}}},{c['t_type'] + i * 0.055:.3f});" for i in range(len(kw)))
ANIM.append(f"tl.set('#cta_fol',{{opacity:0}},{c['t_follow']});tl.fromTo('#cta_fold',{{opacity:0,scale:.85}},{{opacity:1,scale:1,duration:.18,ease:'back.out(2)'}},{c['t_follow']});"
            f"tl.set('#cta_ph',{{opacity:0}},{c['t_type']});{typing}"
            f"tl.set('#cta_typ',{{textContent:''}},{c['t_post']});tl.set('#cta_ph',{{opacity:1}},{c['t_post']});"
            f"tl.fromTo('#cta_row',{{opacity:0,y:30}},{{opacity:1,y:0,duration:.2}},{c['t_post']});"
            f"tl.to('#cta_prof',{{opacity:0,y:-20,duration:.15}},{c['t_send'] - 0.04});tl.to('#cta_dm',{{opacity:1,duration:.15}},{c['t_send']});")

# ---------- write ----------
css = open(os.path.join(HERE, "brand.css")).read() + open(os.path.join(HERE, "base.css")).read()
js = """
const tl = gsap.timeline({ paused: true });
const FROM = { drop:{opacity:0,y:-36,filter:'blur(12px)'}, rise:{opacity:0,y:34,filter:'blur(12px)'}, pop:{opacity:0,scale:.5},
  zoomin:{opacity:0,scale:.86,filter:'blur(16px)'}, cardrop:{opacity:0,y:-240,filter:'blur(18px)'} };
IN.forEach(([sel,t,kind,dur]) => { const f = FROM[kind], to = {opacity:1, duration:dur, ease: kind==='pop' ? 'back.out(2)' : 'power3.out'};
  if ('y' in f) to.y = 0; if ('scale' in f) to.scale = 1; if ('filter' in f) to.filter = 'blur(0px)'; gsap.set(sel, f); tl.to(sel, to, Math.max(0, t)); });
SCENES.forEach(([s,a,b]) => { tl.set('#'+s,{visibility:'visible'},Math.max(0,a-0.001)); tl.set('#'+s,{visibility:'hidden'},b-0.001); });
HARD.forEach(([s,a,b]) => { gsap.set(s,{opacity:0}); tl.set(s,{opacity:1},Math.max(0,a-0.001)); tl.set(s,{opacity:0},b-0.001); });
"""
audio = f'<audio id="mix" class="clip" src="{S["audio"]}" data-start="0" data-duration="{DUR}" data-track-index="9"></audio>' if S.get("audio") else ""
page = f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920" data-fps="{FPS}">
{audio}<div class="abs glow"></div>
{chr(10).join(out_html)}
</div>
<script>
const IN = {json.dumps(IN)}; const HARD = {json.dumps(HARD)}; const SCENES = {json.dumps(SCENES)};
{js}
{chr(10).join(ANIM)}
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
</script></body></html>"""
out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.spec)), "index.html")
open(out, "w").write(page)
print("wrote", out, f"({len(SCENES)} scenes, {len(HARD)} captions)")
