# People on screen

A person can't be drawn, so they stay as their own footage: cut on their own box, shot by shot, with everything around and over them rebuilt.

## Cutting their footage

- One clip per shot. Cuts inside a take (jump cuts, punch-ins) end a clip too.
- Crop each clip to the smallest box that holds the person for the whole shot, with a margin. When they fill the frame, the whole frame is that shot's layer; judge the shot by what you draw over it.
- Keep camera moves and punch-ins that happen inside a shot: they are in the footage already. Graphics that live in the shot's world follow the measured camera.
- Clips are muted; the original soundtrack plays once over the whole film.

## Text burned into the footage

Captions and stickers baked into the original come along with the person.

- Where your rebuilt text lands exactly on top, it hides the burned copy.
- Where it doesn't, remove the burned text first. For word-by-word captions, paint each word out only from its own first frame, so earlier frames stay untouched:

  ```bash
  ffmpeg -i shot.mp4 -vf "delogo=x=..:y=..:w=..:h=..:enable='gte(n,FIRST1)',delogo=...:enable='gte(n,FIRST2)'" -an clean.mp4
  ```

  Find each word's box and first frame with `track.py level` on the word's box. Elsewhere, a median of the clip's other frames works where the person holds still.
- When the original zooms or blurs a shot with its captions in it, stop painting from that frame and let the burned captions move with the picture.

## Text in front of and behind people

When a title passes behind a person (or a head breaks out of a frame), cut the person out with `npx hyperframes remove-background <clip> -o cut.webm` (local and free) and stack: footage, title, cut-out. Check 3-4 frames of the cut-out first: mattes often keep chairs, plants or shelves next to the head. If they do, mask the cut-out to the head (an oval that follows the head's measured position), or keep the head inside the frame instead.

## Privacy

The kept footage is still that person's face and voice. A rewind of someone else's video stays private. Never clone a voice or build an avatar of anyone without their consent; if the person wants themselves in the video instead, that is a remix with their own footage (`remix.md`).
