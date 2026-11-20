// A build-time estimate of a keyword card's size, mirroring tools/dimension.template.html,
// used to decide where a card must hop to a new spot at a cut to stay clear of faces.
// The card measures itself exactly with the real font when it loads; this only plans.
import { readFileSync } from "node:fs";

const src = readFileSync(new URL("./place-runtime.js", import.meta.url), "utf8");
const pure = src.slice(0, src.indexOf("function __fontsReady")) + src.slice(src.indexOf("// Places each keyword on its own"));
export const { placeBlock, placeItems } = new Function(pure + "; return { placeBlock: __placeBlock, placeItems: __placeItems };")();

export const LAYOUTS = {
  slam: [
    { cls: "solid", size: 132, indent: 0, gap: 0 },
    { cls: "tag", size: 56, indent: 110, gap: 26 },
    { cls: "outline", size: 104, indent: 30, gap: 22 },
  ],
  sticker: [
    { cls: "pill-gold", size: 66, indent: 0, gap: 0 },
    { cls: "pill-white", size: 66, indent: 210, gap: 34 },
    { cls: "pill-ink", size: 66, indent: 60, gap: 34 },
  ],
  marker: [
    { cls: "plain", size: 92, indent: 0, gap: 0 },
    { cls: "plain", size: 92, indent: 90, gap: 40 },
    { cls: "plain", size: 92, indent: 20, gap: 40 },
  ],
  hero: [
    { cls: "hero", size: 172, indent: 0, gap: 0 },
    { cls: "chip", size: 48, indent: 14, gap: 34 },
    { cls: "chip", size: 48, indent: 70, gap: 18 },
  ],
};
const PADS = { tag: [0.84, 0.24], "pill-gold": [1.24, 0.34], "pill-white": [1.24, 0.34], "pill-ink": [1.24, 0.34], chip: [1.2, 0.28] };
const CHAR = 0.66; // Poppins Bold/ExtraBold average advance, in em (slightly generous)

/** Estimated sizes(scale) for a card's three keywords at width W. */
export function estimator(layout, words, W, floor = 34) {
  const L = LAYOUTS[layout];
  const k = W / 860;
  const base = L.map((c, i) => {
    const indent = c.indent * k;
    const [ph] = PADS[c.cls] || [0, 0];
    const oneLine = !/solid|hero|outline/.test(c.cls);
    const probe = oneLine ? words[i] : words[i].split(/\s+/).reduce((a, b) => (b.length > a.length ? b : a), "");
    let fs = c.size;
    while (fs > 40 && probe.length * CHAR * fs + ph * fs > Math.max(W, 640) - 20 - indent) fs -= 2;
    return fs;
  });
  return (s) => L.map((c, i) => {
    const fs = Math.max(floor, base[i] * s), indent = c.indent * k * s;
    const [ph, pv] = PADS[c.cls] || [0, 0];
    const oneLine = !/solid|hero|outline/.test(c.cls);
    let lines = 1, tw = words[i].length * CHAR * fs;
    if (!oneLine) {
      const room = Math.max(W, 640) - indent;
      lines = 0;
      let cur = 0;
      tw = 0;
      for (const w of words[i].split(/\s+/)) {
        const ww = w.length * CHAR * fs, sp = 0.3 * fs;
        if (cur && cur + sp + ww > room) { lines++; tw = Math.max(tw, cur); cur = ww; } else cur = cur ? cur + sp + ww : ww;
      }
      lines++; tw = Math.max(tw, cur);
    }
    return { w: tw + ph * fs, h: lines * 1.06 * fs + pv * fs + 0.12 * fs, indent, gap: i ? c.gap * s : 0 };
  });
}
