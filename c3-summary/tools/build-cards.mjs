// Generates one keyword scene per dimension (the dimension name itself is not shown) from tools/dimension.template.html and
// writes their hosts into index.html between the cards markers.
// Edit the table below (or a card's variables in Studio), then: node tools/build-cards.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { track, presenterBox } from "./presenter.mjs";

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
  ["Purpose & Mission", "Empowering Communities", "Meaningful Work", "Lasting Impact", 117.7, 122.2],
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
  if (!b) return { side: "left", width: 860, glow: 900 };
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
// Split a card at camera cuts when the presenter moves, so its keywords can move to
// the free side with the cut; trim slivers (< 0.6 s) of a new shot at either end.
function segmentCard(start, end) {
  let sh = shotsIn(start, end);
  while (sh.length > 1 && sh[0].end - start < 0.6) { start = sh[0].end; sh = sh.slice(1); }
  while (sh.length > 1 && end - sh[sh.length - 1].start < 0.6) { end = sh[sh.length - 1].start - 0.03; sh = sh.slice(0, -1); }
  const union = (list) => presenterBox(Math.max(start, list[0].start), Math.min(end, list[list.length - 1].end));
  const groups = [];
  for (const shot of sh) {
    const g = groups[groups.length - 1];
    if (g) {
      const merged = placeBox(union([...g, shot])).width;
      const alone = placeBox(union(g)).width;
      const next = placeBox(union([shot])).width;
      // keep together unless that costs real room on either side of the cut
      if (merged >= alone - 40 && merged >= next - 150) { g.push(shot); continue; }
    }
    groups.push([shot]);
  }
  if (!groups.length) return [{ start, end, ...placeBox(null) }];
  return groups.map((g, i) => ({
    start: +(i === 0 ? start : g[0].start).toFixed(3),
    end: +(i === groups.length - 1 ? end : g[g.length - 1].end).toFixed(3),
    ...placeBox(union(g)),
  }));
}

const tpl = readFileSync(new URL("./dimension.template.html", import.meta.url), "utf8");
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const attr = (s) => s.replace(/&/g, "&amp;").replace(/'/g, "&#39;");
const hosts = [];

cards.forEach(([label, k1, k2, k3, start, end], i) => {
  const segs = segmentCard(start, end);
  const layout = LAYOUT_CYCLE[i % LAYOUT_CYCLE.length];
  const vars = [
    { id: "k1", type: "string", label: "Keyword 1", default: k1 },
    { id: "k2", type: "string", label: "Keyword 2", default: k2 },
    { id: "k3", type: "string", label: "Keyword 3", default: k3 },
  ];
  segs.forEach((seg, j) => {
    const n = String(i + 1).padStart(2, "0") + (segs.length > 1 ? "abc"[j] : "");
    const id = `dim-${n}`;
    const p = `d${n}`;
    const dur = +(seg.end - seg.start).toFixed(2);
    const cfg = { dimension: label, layout, side: seg.side, width: seg.width, glow: seg.glow, edge: seg.edge, dur,
      cont: j > 0, last: j === segs.length - 1 };
    const s2 = tpl
      .replaceAll("__ID__", id)
      .replaceAll("__P__", p)
      .replace("__CFG__", JSON.stringify(cfg))
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
    console.log(id, seg.start, seg.end, seg.side, seg.width);
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
