# Intake and hand-over

How a run starts and ends, as the person experiences it. Talk to them briefly in their language. They don't type commands; you run everything.

## Before you touch the video

- **Ask whose it is**, if it isn't obvious. Theirs, or one they have rights to: go ahead. Someone else's: tell them in one sentence that the rebuild stays private (study only), then go ahead.
- **Links.** Download only what they may download (their own upload, or a site whose terms allow it). `yt-dlp -f "bv*+ba/b" --merge-output-format mp4 -o source.mp4 <url>` works for most sites. Never log in to anything to get a video; ask for the file instead.
- **Tools.** Check `npx hyperframes --version` (0.9 or newer has `measure`, `snapshot` and `diff`) and `ffmpeg -version`. If a HyperFrames command is missing or refused, use the matching script from `SKILL.md`. Don't upgrade a plan or buy anything to get past a step.
- **Time.** Give a rough estimate after the first overview sheet: under an hour for a simple short clip, several hours for a dense motion-graphics reel. Long films go in sections of 20-40 seconds, split at cuts.

## Setting up

```bash
python3 <rewind>/scripts/probe.py source.mp4
npx hyperframes init <project> --video source.mp4 --keep-original --skip-transcribe --skip-skills
```

Run `init` into an empty folder, then set the root composition's canvas, rate and duration from the probe; the defaults are rarely right. Fix anything the probe flags first: HDR (compare against an SDR copy), variable frame rate or non-square pixels (convert first, with the line the probe prints).

## Handing over

Show, don't list files:

1. Render the final diff with `--sbs` and share the side-by-side video (original left, rebuild right).
2. Start `npx hyperframes preview` on the project so they can keep editing.
3. Give the result in one or two plain sentences: how close it is, and what still differs and why (grain that can't match pixel for pixel, a substitute font, a person kept as their own footage).
4. Leave `REWIND.md` in the project for whoever opens it next.

If a paid service would close a remaining gap (a regenerated shot, a different presenter), mention it once, name it, and do nothing unless they ask.
