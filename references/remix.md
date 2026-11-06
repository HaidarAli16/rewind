# Remix: their footage, their brand, the original's style

Most people don't want a copy. They want the original's structure, pacing and motion carrying
their own words, face and brand. A remix uses the rewind as its template. It is free, like
the rewind: their own footage, a local cut-out, local renders.

## 1. Rebuild first, then remix

Rewind the original first (or at least its scene list, layouts and motion), so every scene is
a measured component: the chip that zooms in, the card over the half-screen face, the word tag
on the seam, the comments-sheet ending. The remix reuses those components with new content.

## 2. Their take

- Probe it. An HDR take (HLG/PQ in the probe) is converted to SDR first, with the platform's own
  tone mapping where there is one, and everything is built on that plate. An untone-mapped HDR
  plate makes white cards read grey.
- Transcribe it and find each script line's clean take. Whisper's word times drift on long takes
  with pauses: get the line boundaries from the audio's silences (`ffmpeg -af silencedetect`),
  transcribe each spoken region on its own to label it, and keep the last clean take of each line.
  Cut only between takes, never inside one: cutting inside a take makes the face jump.
- Cut once, with the speed they use (often 1.1-1.2x), into the layouts the template needs: a
  half-screen face panel (bottom-anchored crop) and a full-frame version. Then transcribe the cut
  voice with word timestamps (`whisper-cli --dtw <model>`) for the word tags and entrances.
- A head that breaks out of a box: `npx hyperframes remove-background` on the face panel (local,
  free), stacked over the graphics and clipped to the head's width so background objects don't ride along.

## 3. Map the original's scenes onto the new script

Write one table: each new line, the original scene whose grammar it borrows, and what changes
on which word. Keep the original's rhythm: one change per spoken phrase, the same alternation
between full graphics and half-screen face, the same opening and ending devices. Give each list
item the original's item device (here: chip 01/02/03 + its name as a title).

## 4. Their brand in one stylesheet

Swap tokens, not components: ground (colour, texture, glow), accent colour and where it may
appear, headline / accent / label fonts, the word-tag style, card surfaces, the seam line.
Logos are the real marks, from each brand's own repo or site (README images, the org avatar,
the site's touch icon), never redrawn. Numbers on screen are what they say; where the live
figure differs (a star count), show the real one beside the spoken one.

## 5. Mock UI without impersonation

A mocked comment section or chat uses generic names and initials, not real companies' accounts.

## 6. Build rules learned

- Never nest a timed `<video>` inside a timed wrapper (`data-start` on both): show scenes from
  the timeline (`visibility`) and leave the videos as the only timed clips. `npx hyperframes check`
  flags it as `video_nested_in_timed_element`.
- Keep the person's face visible when a sheet or card covers the frame: punch in on the face so
  the eyes stay above it, as the original does.
- Mix: the voice chain they use, a music bed ducked under it, master about -14 LUFS.

## 7. Check

There is no original to diff against, so check by eye: a contact sheet every second or two,
every word tag on its word, `npx hyperframes check` clean, the face never covered, the ending
within half a second of the last word.

## A ready structure

`templates/list-reel/` builds a numbered list video (hook, "these N" chips, one chip zoom + real screen recording per item, a follow / comment / DM ending) from a `spec.json` of your words, times, logos and recordings, styled only by your `brand.css`. Start there when the original is a list, then adjust.
