// Feeds the opening and outro titles the faces on screen and the presenter's box while
// each block shows, so they place themselves clear of both. Run after any timing change:
// node tools/build-titles.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { presenterBox } from "./presenter.mjs";
import { facesIn } from "./faces.mjs";

const RUNTIME = readFileSync(new URL("./place-runtime.js", import.meta.url), "utf8");
const MARGIN = 40;
const place = (start, end, prefY) => {
  const b = presenterBox(start, end);
  return { faces: facesIn(start, end), pres: b && [b[0] - MARGIN, b[1] - MARGIN, b[2] + MARGIN, b[3]], prefY };
};

const files = {
  "opening.html": { a: place(3.0, 6.7, 300) }, // scene starts at 0 s; "2026" shows until the crowd shot
  "outro.html": { a: place(125.6, 127.45, 250) }, // "One MENDAKI." shows 125.87-127.47 s
};

for (const [file, data] of Object.entries(files)) {
  const url = new URL(`../compositions/${file}`, import.meta.url);
  let s = readFileSync(url, "utf8");
  // the code and data live between marker comments, so this can run any number of times
  s = s.replace(/\/\*@runtime\*\/[\s\S]*?\/\*@end-runtime\*\//, () => `/*@runtime*/\n      ${RUNTIME.replace(/\n/g, "\n      ")}/*@end-runtime*/`);
  s = s.replace(/\/\*@place\*\/[\s\S]*?\/\*@end-place\*\//, () => `/*@place*/ ${JSON.stringify(data)} /*@end-place*/`);
  writeFileSync(url, s);
  console.log(file, Object.entries(data).map(([k, v]) => `${k}: ${v.faces.length} faces`).join(", "));
}
