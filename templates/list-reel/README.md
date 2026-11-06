# list-reel template

A vertical (1080x1920) "N free tools / skills / libraries" video in your own footage and brand. It is a structure, not a look: every colour and font comes from `brand.css`, and every word, logo, time and recording from your `spec.json`.

| Part | What it shows |
|---|---|
| hook | your face full-screen, a headline card on top, caption pills |
| intro | "these N" + N chips with blurred logos, your face in an accent-ringed box |
| each item | a chip zooming in with the item's real logo and name, then its real screen recording in a browser frame over your half-screen face, captions on the seam |
| cta | Follow → Following, your keyword typed and posted in a comment, the N links landing in a DM card |

## Steps

1. **Your take.** Cut it to the best take of each line (at the speed you post at), then export two versions with the same timing: a half-screen face panel `face_half.mp4` (1080x960, face in the upper half) and a full-screen `face_full.mp4` (1080x1920). An HDR take: convert to SDR first. A long pause: cut it where a chip zoom covers the join.
2. **Times.** Transcribe the CUT voice word by word (`whisper-cli --dtw <model>`, or `npx hyperframes transcribe --engine whisper`) and take every start time from it: hook end, intro start/end, each item's chip / demo / end, each caption and title word, and the CTA beats.
3. **Material.** Each item's real logo (the repo's README image, the org avatar, or the site's touch icon) and a 5-8 s screen recording of its site or demo (any recorder; a headless browser screenshot loop at 30 fps works too).
4. **Brand.** Edit `brand.css` only: ground, accent, text, card, fonts, caption pill.
5. **Build.** Copy `spec.example.json` next to an empty HyperFrames project as `spec.json`, fill it in, then:

```bash
python3 <rewind>/templates/list-reel/build.py spec.json --out index.html
npx hyperframes check .
npx hyperframes snapshot . --at 1,5,9,13,22 --no-end
```

6. **Sound.** Mix your voice, an optional music bed under it and one quiet sound per visual change into `assets/mix.wav`; the composition plays it as one track. Then render locally (`npx hyperframes render --fps 30 --quality high -o out.mp4`) and check the render's loudness: put the mix file on the final with ffmpeg if the render comes out quieter than the mix.

Captions: `[text, start]` pairs, one accent word marked `*like this*`; each switches hard on its start time. Mock UI (profile card, comments) uses your own name and generic text, never real accounts.
