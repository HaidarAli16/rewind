# Painted and 3D films

In a painted or rendered film the character, the set and the camera are baked into one picture. Split each shot into what code can carry and what has to stay a picture, and tell the person up front that some shots will be clips from their video rather than editable layers.

## Code or plate

| Becomes code | Stays a plate (cut from the original) |
|---|---|
| titles, handwriting, logos, end cards | characters acting |
| light added on top: flashes, glows, rings, lens effects | shapes that morph |
| UI, charts, diagrams | fine flowing detail (water, smoke, streamlines) |
| a camera move over a still world | anything code would redraw in the wrong shape |

A mixed shot uses both: the plate underneath, code on top. Clean any text or logo out of a plate before using it (a median of other frames where it holds still, `delogo` for small marks).

## Cuts in animation

Lighting changes inside a shot often register as cuts; check the frames on both sides by eye. A dissolve's blended frames belong to the transition: rebuild the dissolve over its measured frames.

## A camera over a still world

Pick a shape that doesn't move in the world, measure its box at the start, the end and two moments between, and fit scale and position for each (`fit.py`). Rebuild the world from the shot's widest frame, cleaned and split into layers at their own depths, and move those layers with the fitted camera.

## Note it

List in `REWIND.md` which shots are plates and which layers are code, so whoever edits it next knows what can change.
