// Builds compositions/montage.html: one minute of pictures, "hard work but fun too", cut to
// the song's "this adventure" outro (127.47-186.21 s, 110 beats). Then the logo end card.
//   b0-4    title  THE HARD WORK
//   b4-48   22 full-frame event photos, 2 beats each, pushing in on the beat, event label
//   b48-52  title  ...AND THE FUN!
//   b52-90  19 polaroids tossed onto a yellow table, 2 beats each, captioned
//   b90-100 a six-photo mosaic popping in on the beat
//   b100-110 THANK YOU, TEAM MENDAKI!
// Also writes assets/montage-cues.json (sound effects) for tools/build-audio.mjs.
// Usage: node tools/build-montage.mjs
import { readFileSync, writeFileSync, readdirSync } from "node:fs";

const r = (x) => Math.round(x * 1000) / 1000;
const M = JSON.parse(readFileSync(new URL("../assets/music/beats.json", import.meta.url), "utf8"));
const START = M.montage_start, END = M.drums_end;
const i0 = M.beats.findIndex((b) => Math.abs(b - START) < 0.05);
const at = (b) => r((M.beats[i0 + b] ?? START + b * 0.5341) - START); // beat b, scene time
const files = readdirSync(new URL("../assets/montage/", import.meta.url)).sort();
const HARD = files.filter((f) => f.startsWith("hard-"));
const FUN = files.filter((f) => f.startsWith("fun-"));
const LABEL = {
  symposium: "MENDAKI SYMPOSIUM 2026", connections: "MAKING CONNECTIONS", wacana: "WACANA KITA", youth: "YOUTH @ M3+",
  ri: "RAIKAN ILMU @ HEARTLANDS", potluck: "SRC Potluck", bbq: "SRC BBQ", relay: "SRC Relay Rumble", cny: "SRC CNY Tour",
};
const ev = (f) => f.replace(/\.jpg$/, "").split("-").slice(2).join("-");
const els = [], tw = [], cues = [];
const cue = (b, name, vol) => cues.push([r(START + at(b)), name, vol]);

// --- title 1
els.push(`    <div id="mt-t1" class="clip title dark" data-start="0" data-duration="${at(4)}" data-track-index="3">
      <div class="kicker" id="mt-t1k">2026 · BEHIND EVERY PROGRAMME</div>
      <div class="big" id="mt-t1w"><span id="mt-t1a">THE</span> <span class="y" id="mt-t1b">HARD WORK</span></div></div>`);
tw.push(`      tl.fromTo("#mt-t1k", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }, ${at(0) + 0.05});`,
  `      tl.fromTo("#mt-t1a", { opacity: 0, scale: 1.8, filter: "blur(12px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.3, ease: "expo.out" }, ${at(1)});`,
  `      tl.fromTo("#mt-t1b", { opacity: 0, scale: 1.8, filter: "blur(12px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.3, ease: "expo.out" }, ${at(2)});`);
cue(0, "impact-bass-1", 0.4);

// --- hard work: full-frame photos pushing in on the beat
let lastEv = "";
HARD.forEach((f, i) => {
  const b0 = 4 + i * 2, s = at(b0), e = at(b0 + 2) + 0.2;
  const id = `mt-h${String(i + 1).padStart(2, "0")}`;
  const kind = i % 3; // push from right, push from left, zoom punch
  els.push(`    <div id="${id}" class="clip ph" data-start="${s}" data-duration="${r(e - s)}" data-track-index="${i % 2}" style="z-index: ${10 + i}">` +
    `<img id="${id}-i" src="assets/montage/${f}" alt="" /></div>`);
  if (kind === 0) tw.push(`      tl.fromTo("#${id}-i", { xPercent: 100 }, { xPercent: 0, duration: 0.32, ease: "power3.out" }, ${s});`);
  if (kind === 1) tw.push(`      tl.fromTo("#${id}-i", { xPercent: -100 }, { xPercent: 0, duration: 0.32, ease: "power3.out" }, ${s});`);
  if (kind === 2) tw.push(`      tl.fromTo("#${id}-i", { scale: 1.35, opacity: 0 }, { scale: 1.06, opacity: 1, duration: 0.3, ease: "expo.out" }, ${s});`);
  tw.push(`      tl.fromTo("#${id}-i", { scale: ${kind === 2 ? 1.06 : 1.0} }, { scale: 1.1, duration: ${r(e - s)}, ease: "none", immediateRender: false }, ${r(s + 0.32)});`);
  cue(b0, i % 2 ? "whoosh-short" : "whoosh", 0.16);
  if (ev(f) !== lastEv) {
    // the event label slides in when the event changes and stays until the next one
    lastEv = ev(f);
    const n = HARD.slice(i).findIndex((g) => ev(g) !== lastEv);
    const until = at(4 + (n < 0 ? HARD.length : i + n) * 2);
    const lid = `mt-l${String(i + 1).padStart(2, "0")}`;
    els.push(`    <div id="${lid}" class="clip lbl-host" data-start="${s}" data-duration="${r(until - s)}" data-track-index="2" style="z-index: 60">` +
      `<div class="lbl" id="${lid}-t"><span class="dot"></span>${LABEL[lastEv]}</div></div>`);
    tw.push(`      tl.fromTo("#${lid}-t", { xPercent: -120, opacity: 0 }, { xPercent: 0, opacity: 1, duration: 0.45, ease: "expo.out" }, ${r(s + 0.1)});`);
  }
});

// --- title 2
els.push(`    <div id="mt-t2" class="clip title yellow" data-start="${at(48)}" data-duration="${r(at(52) - at(48) + 0.3)}" data-track-index="3" style="z-index: 70">
      <div class="big dark" id="mt-t2w"><span id="mt-t2a">...AND THE</span> <span id="mt-t2b" class="t">FUN!</span></div>
      ${[...Array(14)].map((_, k) => `<div class="conf c${k % 3}" id="mt-cf${k}" style="left: ${(k * 137) % 1820 + 40}px; top: ${(k * 271) % 980 + 40}px"></div>`).join("")}</div>`);
tw.push(`      tl.fromTo("#mt-t2", { clipPath: "circle(0% at 50% 50%)" }, { clipPath: "circle(80% at 50% 50%)", duration: 0.4, ease: "power3.out" }, ${at(48)});`,
  `      tl.fromTo("#mt-t2a", { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }, ${at(48) + 0.1});`,
  `      tl.fromTo("#mt-t2b", { opacity: 0, scale: 2.2, rotation: -12 }, { opacity: 1, scale: 1, rotation: -4, duration: 0.5, ease: "back.out(2.2)" }, ${at(50)});`);
[...Array(14)].forEach((_, k) => tw.push(`      tl.fromTo("#mt-cf${k}", { scale: 0, rotation: ${k * 40} }, { scale: 1, rotation: ${k * 40 + 160}, duration: 0.7, ease: "expo.out" }, ${r(at(50) + (k % 5) * 0.03)});`));
cue(48, "whoosh", 0.3); cue(50, "impact-bass-1", 0.42); cue(50, "sparkle", 0.25);

// --- fun: polaroids tossed onto a yellow table, piling up
els.push(`    <div id="mt-table" class="clip table" data-start="${at(52)}" data-duration="${r(at(90) - at(52) + 0.4)}" data-track-index="4" style="z-index: 80"></div>`);
const SPOT = [[560, 470], [1340, 430], [930, 560], [470, 640], [1430, 650], [980, 400], [700, 560], [1220, 560]];
FUN.forEach((f, i) => {
  const b0 = 52 + i * 2, s = at(b0), e = at(90) + 0.4;
  const id = `mt-f${String(i + 1).padStart(2, "0")}`;
  const [x, y] = SPOT[i % SPOT.length], rot = [-7, 6, -3, 8, -9, 4, -5, 7][i % 8];
  els.push(`    <div id="${id}" class="clip pol-host" data-layout-allow-overlap data-layout-allow-occlusion data-start="${s}" data-duration="${r(e - s)}" data-track-index="${5 + (i % 2)}" style="z-index: ${90 + i}">` +
    `<div class="pol" id="${id}-c" style="left: ${x - 380}px; top: ${y - 330}px"><img src="assets/montage/${f}" alt="" /><div class="cap">${LABEL[ev(f)]}</div></div></div>`);
  tw.push(`      tl.fromTo("#${id}-c", { opacity: 0, scale: 1.7, rotation: ${rot + (i % 2 ? 28 : -28)}, y: -120 }, { opacity: 1, scale: 1, rotation: ${rot}, y: 0, duration: 0.42, ease: "back.out(1.6)" }, ${s});`);
  cue(b0, "pop", 0.26);
});

// --- mosaic: six photos pop into a grid on the beat
els.push(`    <div id="mt-mosaic" class="clip mosaic" data-start="${at(90)}" data-duration="${r(END - START - at(90))}" data-track-index="3" style="z-index: 120">
${[0, 1, 2, 3, 4, 5].map((k) => `      <div class="tile" id="mt-m${k}" style="left: ${(k % 3) * 640}px; top: ${Math.floor(k / 3) * 540}px"><img src="assets/montage/${[HARD[0], FUN[9], HARD[16], FUN[0], HARD[4], FUN[14]][k]}" alt="" /></div>`).join("\n")}
      <div class="thanks" id="mt-thanks" data-layout-allow-occlusion><div class="k" id="mt-tk">HARD WORK. GREAT FUN.</div><div class="big" id="mt-tb">THANK YOU, <span class="y">TEAM MENDAKI!</span></div></div>
    </div>`);
[0, 1, 2, 3, 4, 5].forEach((k) => {
  tw.push(`      tl.fromTo("#mt-m${k}", { scale: 0.4, opacity: 0, rotation: ${k % 2 ? 8 : -8} }, { scale: 1, opacity: 1, rotation: 0, duration: 0.38, ease: "back.out(1.5)" }, ${at(90 + k)});`);
  cue(90 + k, "pop", 0.24);
});
tw.push(`      tl.fromTo("#mt-mosaic", { "--dim": 0 }, { "--dim": 0.62, duration: 0.5, ease: "power2.out" }, ${at(100) - 0.1});`,
  `      tl.fromTo("#mt-tk", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }, ${at(100)});`,
  `      tl.fromTo("#mt-tb", { opacity: 0, scale: 1.4, filter: "blur(12px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }, ${at(102)});`,
  `      tl.fromTo("#mt-mosaic", { scale: 1 }, { scale: 1.06, duration: ${r(at(110) - at(100))}, ease: "none", immediateRender: false }, ${at(100)});`);
cue(100, "whoosh", 0.25); cue(102, "impact-bass-1", 0.35);

writeFileSync(new URL("../compositions/montage.html", import.meta.url), `<template>
  <style>
    #root { position: absolute; inset: 0; overflow: hidden; font-family: "Poppins", sans-serif; background: #1a1b1e; }
    #root .ph { position: absolute; inset: 0; overflow: hidden; }
    #root .ph img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
    #root .title { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    #root .title.dark { background: #1a1b1e; }
    #root .title.yellow { background: #fdd901; }
    #root .kicker { font-size: 30px; font-weight: 600; letter-spacing: 0.32em; color: #26b6c6; margin-bottom: 18px; }
    #root .big { font-size: 150px; font-weight: 800; line-height: 1; color: #fff; text-align: center; white-space: nowrap; }
    #root .big.dark { color: #1a1b1e; }
    #root .big span { display: inline-block; }
    #root .y { color: #fdd901; }
    #root .t { color: #1a1b1e; background: #fff; padding: 0 0.25em; border-radius: 18px; box-shadow: 0 16px 0 #26b6c6; }
    #root .conf { position: absolute; width: 34px; height: 34px; border-radius: 8px; }
    #root .conf.c0 { background: #26b6c6; } #root .conf.c1 { background: #ffffff; border-radius: 50%; } #root .conf.c2 { background: #1a1b1e; }
    #root .lbl-host { position: absolute; inset: 0; pointer-events: none; }
    #root .lbl { position: absolute; left: 110px; bottom: 96px; display: flex; align-items: center; gap: 16px; padding: 14px 30px 16px 24px;
      background: #fdd901; color: #1a1b1e; font-size: 38px; font-weight: 700; border-radius: 999px; box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35); }
    #root .lbl .dot { width: 18px; height: 18px; border-radius: 50%; background: #26b6c6; }
    #root .table { position: absolute; inset: 0; background:
      radial-gradient(circle at 20% 25%, rgba(255,255,255,0.35) 0 60px, transparent 61px),
      radial-gradient(circle at 85% 75%, rgba(38,182,198,0.35) 0 90px, transparent 91px),
      repeating-linear-gradient(135deg, #fdd901 0 46px, #f6cf00 46px 92px); }
    #root .pol-host { position: absolute; inset: 0; }
    #root .pol { position: absolute; width: 760px; height: 660px; padding: 22px 22px 0; background: #fff; border-radius: 6px;
      box-shadow: 0 26px 60px rgba(0, 0, 0, 0.35); }
    #root .pol img { display: block; width: 716px; height: 537px; object-fit: cover; }
    #root .pol .cap { height: 101px; display: flex; align-items: center; justify-content: center; font-size: 38px; font-weight: 700; color: #1a1b1e; }
    #root .mosaic { position: absolute; inset: 0; --dim: 0; transform-origin: 50% 50%; background: #1a1b1e; }
    #root .tile { position: absolute; width: 640px; height: 540px; overflow: hidden; border: 6px solid #1a1b1e; }
    #root .tile img { width: 100%; height: 100%; object-fit: cover; }
    #root .mosaic::after { content: ""; position: absolute; inset: 0; background: #1a1b1e; opacity: var(--dim); }
    #root .thanks { position: absolute; inset: 0; z-index: 5; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    #root .thanks .k { font-size: 40px; font-weight: 600; letter-spacing: 0.28em; color: #26b6c6; margin-bottom: 20px; }
    #root .thanks .big { font-size: 96px; }
  </style>
  <div id="root" data-composition-id="montage" data-width="1920" data-height="1080">
${els.join("\n")}
  </div>
  <script>
    (function () {
      const tl = gsap.timeline({ paused: true });
${tw.join("\n")}
      window.__timelines["montage"] = tl;
    })();
  </script>
</template>
`);
writeFileSync(new URL("../assets/montage-cues.json", import.meta.url), JSON.stringify(cues));
console.log(`montage ${r(END - START)} s: ${HARD.length} hard-work photos, ${FUN.length} fun photos, ${cues.length} sound cues`);
