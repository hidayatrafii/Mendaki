// Builds compositions/transitions.html: a transition on every cut in the footage, cycling
// four styles (brand wipe, flash + punch, slice, punch), plus the camera punch-ins on the
// root timeline and the whoosh cues for tools/build-audio.mjs.
// Run after changing the cuts in assets/character-track.json: node tools/build-transitions.mjs
import { readFileSync, writeFileSync } from "node:fs";

const track = JSON.parse(readFileSync(new URL("../assets/character-track.json", import.meta.url), "utf8")).shots;
const r = (x) => Math.round(x * 1000) / 1000;
// every cut, except the very start and end and doubles a frame apart
// photo sections (they bring their own card slams); cuts strictly inside them are skipped
const idxHtml = readFileSync(new URL("../index.html", import.meta.url), "utf8");
const photoWins = [...idxHtml.matchAll(/id="photos-[a-z]+"[^>]*data-start="([\d.]+)" data-duration="([\d.]+)"/g)].map((m) => [+m[1], +m[1] + +m[2]]);
const inPhotos = (t) => photoWins.some(([a, b]) => t > a + 0.1 && t < b - 0.1);
const cuts = [];
for (const s of track) {
  if (s.start < 0.5 || s.start > 127.2 || inPhotos(s.start)) continue;
  if (cuts.length && s.start - cuts[cuts.length - 1] < 0.3) continue;
  cuts.push(r(s.start));
}
// the photo stretches (60.2-91.93 s, 99.2-101.5 s) bring their own card slams; the cuts
// into and out of them still get a transition
const KINDS = ["wipe", "flash", "slice", "punch"];
const els = [];
const tweens = [];
const punch = [];
const whoosh = [];
cuts.forEach((c, i) => {
  const kind = KINDS[i % KINDS.length];
  const id = `tr-${String(i + 1).padStart(2, "0")}`;
  const s = r(c - 0.3);
  if (kind === "wipe") {
    els.push(
      `    <div id="${id}" class="clip tr" data-start="${s}" data-duration="0.7" data-track-index="${i % 2}">` +
        `<div class="band yellow" id="${id}-a"></div><div class="band teal" id="${id}-b"></div></div>`,
    );
    tweens.push(
      `      tl.fromTo("#${id}-a", { xPercent: -160 }, { xPercent: 160, duration: 0.5, ease: "power2.inOut" }, ${r(s + 0.05)});`,
      `      tl.fromTo("#${id}-b", { xPercent: -160 }, { xPercent: 160, duration: 0.5, ease: "power2.inOut" }, ${r(s + 0.12)});`,
    );
    whoosh.push([r(c - 0.2), "whoosh-short", 0.32]);
  } else if (kind === "flash") {
    els.push(`    <div id="${id}" class="clip tr" data-start="${s}" data-duration="0.7" data-track-index="${i % 2}"><div class="flash" id="${id}-f"></div></div>`);
    tweens.push(`      tl.fromTo("#${id}-f", { opacity: 0 }, { opacity: 0.85, duration: 0.06, ease: "none" }, ${r(s + 0.26)});`);
    tweens.push(`      tl.to("#${id}-f", { opacity: 0, duration: 0.3, ease: "power2.out" }, ${r(s + 0.32)});`);
    punch.push([c, 1.1]);
    whoosh.push([r(c - 0.12), "whoosh", 0.22]);
  } else if (kind === "slice") {
    const bars = [0, 1, 2].map((k) => `<div class="bar" id="${id}-s${k}" style="top: ${k * 360}px"></div>`).join("");
    els.push(`    <div id="${id}" class="clip tr" data-start="${s}" data-duration="0.7" data-track-index="${i % 2}">${bars}</div>`);
    [0, 1, 2].forEach((k) => {
      const dir = k % 2 ? 1 : -1;
      tweens.push(
        `      tl.fromTo("#${id}-s${k}", { xPercent: ${dir * 105} }, { xPercent: 0, duration: 0.2, ease: "power3.in" }, ${r(s + 0.1 + k * 0.02)});`,
        `      tl.to("#${id}-s${k}", { xPercent: ${-dir * 105}, duration: 0.26, ease: "power3.out" }, ${r(s + 0.32 + k * 0.02)});`,
      );
    });
    whoosh.push([r(c - 0.18), "whoosh-short", 0.3]);
  } else {
    punch.push([c, 1.16]);
    whoosh.push([r(c - 0.1), "whoosh", 0.2]);
  }
});

writeFileSync(
  new URL("../compositions/transitions.html", import.meta.url),
  `<template>
  <style>
    #root { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
    #root .tr { position: absolute; inset: 0; overflow: hidden; }
    #root .band { position: absolute; top: -20%; left: 0; width: 120%; height: 140%; transform-origin: 50% 50%; }
    #root .band.yellow { background: #fdd901; clip-path: polygon(30% 0, 70% 0, 50% 100%, 10% 100%); }
    #root .band.teal { background: #26b6c6; clip-path: polygon(46% 0, 58% 0, 38% 100%, 26% 100%); }
    #root .flash { position: absolute; inset: 0; background: #ffffff; opacity: 0; }
    #root .bar { position: absolute; left: 0; width: 1920px; height: 360px; background: #1a1b1e; }
  </style>
  <div id="root" data-composition-id="transitions" data-width="1920" data-height="1080">
${els.join("\n")}
  </div>
  <script>
    (function () {
      const tl = gsap.timeline({ paused: true });
${tweens.join("\n")}
      window.__timelines["transitions"] = tl;
    })();
  </script>
</template>
`,
);

const indexUrl = new URL("../index.html", import.meta.url);
let index = readFileSync(indexUrl, "utf8");
index = index.replace(
  /(<!-- transitions:start -->)[\s\S]*?(\s*<!-- transitions:end -->)/,
  `$1\n      <div id="transitions" data-composition-id="transitions" data-composition-src="compositions/transitions.html" ` +
    `data-start="0" data-duration="127.472" data-track-index="2" data-track-kind="graphics" ` +
    `data-width="1920" data-height="1080" data-layout-allow-occlusion style="z-index: 5"></div>$2`,
);
index = index.replace(/\/\*@punch\*\/[\s\S]*?\/\*@end-punch\*\//, () => `/*@punch*/ ${JSON.stringify(punch)} /*@end-punch*/`);
writeFileSync(indexUrl, index);
writeFileSync(new URL("../assets/transition-cues.json", import.meta.url), JSON.stringify({ cuts, whoosh }, null, 1));
console.log(`${cuts.length} transitions: ${KINDS.map((k) => `${cuts.filter((_, i) => KINDS[i % 4] === k).length} ${k}`).join(", ")}`);
