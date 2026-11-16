// Generates one keyword scene per dimension (the dimension name itself is not shown) from tools/dimension.template.html and
// writes their hosts into index.html between the cards markers.
// Edit the table below (or a card's variables in Studio), then: node tools/build-cards.mjs
import { readFileSync, writeFileSync } from "node:fs";

// [dimension, k1, k2, k3, start(s), end(s), side]
// Times follow the voiceover lines each dimension matches.
const cards = [
  ["Communication", "Transparency", "Clarity", "Keeping You Informed", 12.8, 18.1, "left"],
  ["Senior Leadership: Strategic", "Clear Direction", "Decisive Leadership", "Community Impact", 18.15, 24.1, "left"],
  ["Senior Leadership: People", "Listening", "Caring", "Taking Action", 24.3, 30.75, "right"],
  ["Confidence in Organisation", "Your Voice Matters", "Positive Change", "Building Our Future", 30.8, 33.85, "right"],
  ["Diversity & Inclusion", "Respect", "Inclusion", "Equal Opportunities", 34.0, 40.0, "left"],
  ["Engagement", "Connection", "Appreciation", "Belonging", 40.1, 44.45, "right"],
  ["Teamwork / Collaboration", "One MENDAKI", "Collaboration", "Stronger Together", 44.5, 48.55, "right"],
  ["Development", "Learning", "Growth", "Opportunities", 49.1, 53.55, "left"],
  ["Immediate Manager Effectiveness", "Guidance", "Support", "Empowerment", 53.6, 60.25, "left"],
  ["Reward & Recognition", "Recognition", "Appreciation", "Celebrating Achievements", 60.4, 69.95, "left"],
  ["Well-Being", "Flexibility", "Work-Life Balance", "Your Well-Being Matters", 70.0, 74.5, "left"],
  ["Safety", "Safe Workplace", "Awareness", "Support", 74.55, 81.45, "left"],
  ["Performance Enablement", "Better Processes", "Right Resources", "Working Smarter", 81.5, 91.9, "left"],
  ["Agility & Innovation", "Innovation", "Digitalisation", "Continuous Improvement", 92.1, 101.4, "right"],
  ["Commitment to Sector", "Serving Communities", "Making a Difference", "Shared Commitment", 101.5, 113.35, "left"],
  ["Commitment to Organisation", "Shared Purpose", "Commitment", "Growing Together", 113.4, 117.6, "left"],
  ["Purpose & Mission", "Empowering Communities", "Meaningful Work", "Lasting Impact", 117.7, 122.2, "left"],
];

// Keyword layouts, cycled card by card: slam (huge word, gold tag, outline fill),
// sticker (tilted pills), marker (hand-drawn strokes), hero (giant word + chips).
const LAYOUT_CYCLE = ["slam", "sticker", "marker", "hero"];

const tpl = readFileSync(new URL("./dimension.template.html", import.meta.url), "utf8");
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const attr = (s) => s.replace(/&/g, "&amp;").replace(/'/g, "&#39;");
const hosts = [];

cards.forEach(([label, k1, k2, k3, start, end, side], i) => {
  const n = String(i + 1).padStart(2, "0");
  const id = `dim-${n}`;
  const p = `d${n}`;
  const dur = +(end - start).toFixed(2);
  const vars = [
    { id: "k1", type: "string", label: "Keyword 1", default: k1 },
    { id: "k2", type: "string", label: "Keyword 2", default: k2 },
    { id: "k3", type: "string", label: "Keyword 3", default: k3 },
  ];
  const layout = LAYOUT_CYCLE[i % LAYOUT_CYCLE.length];
  let s = tpl
    .replaceAll("__ID__", id)
    .replaceAll("__P__", p)
    .replace("__CFG__", JSON.stringify({ dimension: label, layout, side, dur }))
    .replace(/data-composition-variables='[\s\S]*?'/, `data-composition-variables='${attr(JSON.stringify(vars))}'`)
    .replace(/(data-var-text="k1">)[^<]*/, `$1${esc(k1)}`)
    .replace(/(data-var-text="k2">)[^<]*/, `$1${esc(k2)}`)
    .replace(/(data-var-text="k3">)[^<]*/, `$1${esc(k3)}`);
  writeFileSync(new URL(`../compositions/${id}.html`, import.meta.url), s);
  hosts.push(
    `      <div id="${id}" data-composition-id="${id}" data-composition-src="compositions/${id}.html" ` +
      `data-start="${start}" data-duration="${dur}" data-track-index="3" data-track-kind="graphics" ` +
      `data-width="1920" data-height="1080" style="z-index: 6"></div>`,
  );
});

const indexUrl = new URL("../index.html", import.meta.url);
const index = readFileSync(indexUrl, "utf8");
const out = index.replace(
  /(<!-- cards:start -->)[\s\S]*?(\s*<!-- cards:end -->)/,
  `$1\n${hosts.join("\n")}$2`,
);
writeFileSync(indexUrl, out);
console.log(`wrote ${cards.length} cards`);
