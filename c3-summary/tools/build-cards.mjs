// Generates one keyword scene per dimension (the dimension name itself is not shown) from tools/dimension.template.html and
// writes their hosts into index.html between the cards markers.
// Edit the table below (or a card's variables in Studio), then: node tools/build-cards.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { track, presenterBox } from "./presenter.mjs";
import { facesIn } from "./faces.mjs";
import { placeItems, estimator } from "./layout-estimate.mjs";
const RUNTIME = readFileSync(new URL("./place-runtime.js", import.meta.url), "utf8");

// [dimension, k1, k2, k3, start(s), end(s)]
// Times follow the voiceover lines each dimension matches. Each card goes on the side
// of the frame with the most room beside the presenter (assets/character-track.json).
const cards = [
  ["Communication", "Transparency", "Clarity", "Keeping You Informed", 12.8, 18.1],
  ["Senior Leadership: Strategic", "Clear Direction", "Decisive Leadership", "Community Impact", 18.15, 24.1],
  ["Senior Leadership: People", "Listening", "Caring", "Taking Action", 24.3, 30.75],
  ["Confidence in Organisation", "Your Voice Matters", "Positive Change", "Building Our Future", 30.8, 33.85],
  ["Diversity & Inclusion", "Respect", "Inclusion", "Equal Opportunities", 34.0, 40.0],
  ["Engagement", "Connection", "Appreciation", "Belonging", 40.1, 44.45],
  ["Teamwork / Collaboration", "One MENDAKI", "Collaboration", "Stronger Together", 44.5, 48.55],
  ["Development", "Learning", "Growth", "Opportunities", 49.1, 53.55],
  ["Immediate Manager Effectiveness", "Guidance", "Support", "Empowerment", 53.6, 60.25],
  ["Reward & Recognition", "Recognition", "Appreciation", "Celebrating Achievements", 60.4, 69.95],
  ["Well-Being", "Flexibility", "Work-Life Balance", "Your Well-Being Matters", 70.0, 74.5],
  ["Safety", "Safe Workplace", "Awareness", "Support", 74.55, 81.45],
  ["Performance Enablement", "Better Processes", "Right Resources", "Working Smarter", 81.5, 91.9],
  ["Agility & Innovation", "Innovation", "Digitalisation", "Continuous Improvement", 92.1, 101.4],
  ["Commitment to Sector", "Serving Communities", "Making a Difference", "Shared Commitment", 101.5, 113.35],
  ["Commitment to Organisation", "Shared Purpose", "Commitment", "Growing Together", 113.4, 117.6],
  ["Purpose & Mission", "Empowering Communities", "Meaningful Work", "Lasting Impact", 117.7, 124.9],
];

// Keyword layouts, cycled card by card: slam (huge word, gold tag, outline fill),
// sticker (tilted pills), marker (hand-drawn strokes), hero (giant word + chips).
const LAYOUT_CYCLE = ["slam", "sticker", "marker", "hero"];

// The presenter must never be covered: every card is laid out in the free space beside
// where he stands during that card, with a margin.
const MARGIN = 60;
const EDGE = 120;
function shotsIn(start, end) {
  return track.filter((s) => s.end > start && s.start < end && !(s.box_from && end <= s.box_from));
}
function placeBox(b) {
  if (!b) return { side: "left", width: 860, glow: 900, edge: EDGE };
  const leftW = b[0] - MARGIN - EDGE;
  const rightW = 1920 - EDGE - (b[2] + MARGIN);
  const side = leftW >= rightW ? "left" : "right";
  let width = Math.min(860, side === "left" ? leftW : rightW);
  // close-ups leave little room: let the text use the outer margin (still inside 90% action-safe)
  const edge = width < 560 ? 96 : EDGE;
  if (width < 560) width += EDGE - edge;
  const glow = Math.min(1100, Math.max(200, side === "left" ? b[0] - 10 : 1920 - b[2] - 10));
  return { side, width, glow, edge };
}
// Cuts in the picture: camera cuts in the footage and every photo change.
const photoCuts = (() => {
  const idx = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const cuts = [];
  for (const m of idx.matchAll(/data-composition-src="compositions\/(photos-[a-z]+)\.html" data-start="([\d.]+)"/g)) {
    const scene = readFileSync(new URL(`../compositions/${m[1]}.html`, import.meta.url), "utf8");
    for (const c of scene.matchAll(/class="clip photo" data-start="([\d.]+)"/g)) cuts.push(+m[2] + +c[1]);
  }
  return cuts;
})();
const CUTS = [...new Set([...track.map((t) => t.start), ...photoCuts].map((t) => +t.toFixed(3)))].sort((a, b) => a - b);

// How well can the card sit, clear of faces and the presenter, over [start, end)?
function plan(layout, words, start, end) {
  const pb = presenterBox(start, end);
  const pl = placeBox(pb);
  const pres = pb && [pb[0] - 40, pb[1] - 40, pb[2] + 40, pb[3]];
  const xMin = pl.side === "right" ? 1920 - pl.edge - pl.width : pl.edge;
  const opts = (floor) => ({ sizes: estimator(layout, words, pl.width, floor), faces: facesIn(start, end), pres, side: pl.side,
    xMin, xMax: xMin + pl.width, areaMin: 70, areaMax: 1850, yMin: 50, yMax: 890, prefY: 140, pad: 26 });
  let P = placeItems(opts(34));
  if (!P || P.cost !== 0) P = placeItems(opts(28));
  return { ...pl, good: !!P && P.cost === 0 && P.s >= 0.77, s: P ? P.s : 0, cost: P ? P.cost : -1 };
}

// Split a card at cuts only where one spot can't stay clear of every face (and the
// presenter) for the whole card: the keywords then hop to a clear spot with the cut.
// Slivers (< 0.6 s) of a new shot at either end are trimmed off instead.
function segmentCard(layout, words, start, end) {
  let cuts = CUTS.filter((c) => c > start + 0.05 && c < end - 0.05);
  while (cuts.length && cuts[0] - start < 0.6) { start = cuts[0]; cuts = cuts.slice(1); }
  while (cuts.length && end - cuts[cuts.length - 1] < 0.6) { end = cuts[cuts.length - 1] - 0.03; cuts = cuts.slice(0, -1); }
  const edges = [start, ...cuts, end];
  const groups = [[edges[0], edges[1]]];
  for (let i = 1; i < edges.length - 1; i++) {
    const g = groups[groups.length - 1];
    const piece = [edges[i], edges[i + 1]];
    const together = plan(layout, words, g[0], piece[1]).good;
    const tooShort = piece[1] - piece[0] < 0.9 || g[1] - g[0] < 0.9;
    if (together || (tooShort && !plan(layout, words, ...piece).good)) g[1] = piece[1];
    else groups.push(piece);
  }
  return groups.map(([s, e]) => ({ start: +s.toFixed(3), end: +e.toFixed(3), ...plan(layout, words, s, e) }));
}

const tpl = readFileSync(new URL("./dimension.template.html", import.meta.url), "utf8");
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const attr = (s) => s.replace(/&/g, "&amp;").replace(/'/g, "&#39;");
const hosts = [];

cards.forEach(([label, k1, k2, k3, start, end], i) => {
  const layout = LAYOUT_CYCLE[i % LAYOUT_CYCLE.length];
  // a piece where no spot clears every face is skipped: the keywords step off for that shot
  const all = segmentCard(layout, [k1, k2, k3], start, end);
  const segs = all.filter((g) => g.cost === 0);
  all.filter((g) => g.cost !== 0).forEach((g) => console.log(`  (keywords step off ${g.start}-${g.end}: no face-free spot)`));
  const vars = [
    { id: "k1", type: "string", label: "Keyword 1", default: k1 },
    { id: "k2", type: "string", label: "Keyword 2", default: k2 },
    { id: "k3", type: "string", label: "Keyword 3", default: k3 },
  ];
  segs.forEach((seg, j) => {
    const n = String(i + 1).padStart(2, "0") + (segs.length > 1 ? "abcdefghij"[j] : "");
    const id = `dim-${n}`;
    const p = `d${n}`;
    const dur = +(seg.end - seg.start).toFixed(2);
    const pb = presenterBox(seg.start, seg.end);
    const cfg = { dimension: label, layout, side: seg.side, width: seg.width, edge: seg.edge, dur,
      cont: j > 0 && Math.abs(segs[j - 1].end - seg.start) < 0.01,
      last: !(segs[j + 1] && Math.abs(segs[j + 1].start - seg.end) < 0.01),
      pres: pb && [pb[0] - 40, pb[1] - 40, pb[2] + 40, pb[3]],
      faces: facesIn(seg.start, seg.end) };
    const s2 = tpl
      .replaceAll("__ID__", id)
      .replaceAll("__P__", p)
      .replace("__CFG__", JSON.stringify(cfg))
      .replace("__PLACE_RUNTIME__", RUNTIME.replace(/\n/g, "\n      "))
      .replace(/data-composition-variables='[\s\S]*?'/, `data-composition-variables='${attr(JSON.stringify(vars))}'`)
      .replace(/(data-var-text="k1">)[^<]*/, `$1${esc(k1)}`)
      .replace(/(data-var-text="k2">)[^<]*/, `$1${esc(k2)}`)
      .replace(/(data-var-text="k3">)[^<]*/, `$1${esc(k3)}`);
    writeFileSync(new URL(`../compositions/${id}.html`, import.meta.url), s2);
    hosts.push(
      `      <div id="${id}" data-composition-id="${id}" data-composition-src="compositions/${id}.html" ` +
        `data-start="${seg.start}" data-duration="${dur}" data-track-index="3" data-track-kind="graphics" ` +
        `data-width="1920" data-height="1080" style="z-index: 6"></div>`,
    );
    console.log(id, seg.start, seg.end, seg.side, seg.width, seg.good ? "clear" : "TIGHT", "scale", seg.s, "faceArea", Math.round(seg.cost));
  });
});

const indexUrl = new URL("../index.html", import.meta.url);
const index = readFileSync(indexUrl, "utf8");
const out = index.replace(
  /(<!-- cards:start -->)[\s\S]*?(\s*<!-- cards:end -->)/,
  `$1\n${hosts.join("\n")}$2`,
);
writeFileSync(indexUrl, out);
console.log(`wrote ${cards.length} cards`);
