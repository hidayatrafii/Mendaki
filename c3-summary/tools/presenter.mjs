// Where the cartoon presenter stands, from assets/character-track.json (built by face
// tracking, one box per camera shot). Everything on screen is laid out around these
// boxes so the presenter is never covered.
import { readFileSync } from "node:fs";

export const track = JSON.parse(
  readFileSync(new URL("../assets/character-track.json", import.meta.url), "utf8"),
).shots;

/** Union of the presenter's boxes [x0, y0, x1, y1] over [start, end), or null if absent. */
export function presenterBox(start, end) {
  let box = null;
  for (const s of track) {
    if (!s.box || s.end <= start || s.start >= end) continue;
    if (s.box_from && end <= s.box_from) continue;
    box = box
      ? [Math.min(box[0], s.box[0]), Math.min(box[1], s.box[1]), Math.max(box[2], s.box[2]), Math.max(box[3], s.box[3])]
      : [...s.box];
  }
  return box;
}
