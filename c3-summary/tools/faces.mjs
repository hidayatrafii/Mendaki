// Faces on screen, from assets/faces.json (YuNet face detection on the footage and the
// photos, padded for hair and chin). Text and glow are laid out to stay off every face.
import { readFileSync } from "node:fs";

const data = JSON.parse(readFileSync(new URL("../assets/faces.json", import.meta.url), "utf8"));

const overlap = (a, b) => Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
const area = (a) => (a[2] - a[0]) * (a[3] - a[1]);

/** Every face box seen during [start, end), near-duplicates merged. */
export function facesIn(start, end) {
  const boxes = [];
  // samples inside the window (0.2 s apart); a window shorter than that uses its nearest sample
  let inside = data.samples.filter(([t]) => t >= start - 0.05 && t <= end + 0.05);
  if (!inside.length) inside = [data.samples.reduce((a, s) => (Math.abs(s[0] - (start + end) / 2) < Math.abs(a[0] - (start + end) / 2) ? s : a))];
  for (const [, list] of inside) {
    for (const b of list) {
      const same = boxes.find((o) => overlap(o, b) > 0.5 * Math.min(area(o), area(b)));
      if (same) {
        same[0] = Math.min(same[0], b[0]); same[1] = Math.min(same[1], b[1]);
        same[2] = Math.max(same[2], b[2]); same[3] = Math.max(same[3], b[3]);
      } else boxes.push([...b]);
    }
  }
  return boxes;
}
