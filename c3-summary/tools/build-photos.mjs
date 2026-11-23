// Builds the photo scenes that fill the stretches where the edit is black: each photo
// slams in on the beat as a tilted, white-framed card over a blurred copy of itself,
// leaving the previous card peeking out underneath.
// Edit the lists below, then: node tools/build-photos.mjs
import { readFileSync, writeFileSync } from "node:fs";

// Each scene: [id, start (s), end (s), photos as [file in assets/photos, from (s)]]
// Photo changes follow the narration line each photo illustrates.
const scenes = [
  // starts 2 frames before the footage goes black (60.267 s) so no black frame shows
  ["photos-awards", 60.2, 69.6, [
    ["01-awards-congratulations.jpg", 60.2], // "when our people reach new milestones, we celebrate them"
    ["02-awards-best-employee.jpg", 62.5],
    ["03-awards-handover-1.jpg", 64.43], // "recognising effort and progress"
    ["04-awards-handover-2.jpg", 66.4],
    ["05-awards-best-employee-2.jpg", 68.0], // "the people behind the work"
  ]],
  ["photos-wellbeing", 69.6, 78.17, [
    ["06-coffee-with-management-team.jpg", 69.6], // "the work matters, and so do the people doing it"
    ["07-health-screening-bp-1.jpg", 72.44], // "health and wellbeing initiatives"
    ["08-health-screening-bp-2.jpg", 73.5],
    ["09-health-screening-blood-test.jpg", 74.56], // "awareness around physical and digital safety"
    ["10-health-screening-briefing.jpg", 76.4],
  ]],
  ["photos-work", 78.17, 91.933, [
    ["11-coffee-with-management-fun.jpg", 78.17], // "supporting one another"
    ["12-coffee-with-management-chat.jpg", 80.0],
    ["13-satellite-centre-genogram.jpg", 81.55], // "the everyday work that keeps MENDAKI moving"
    ["14-satellite-centre-discussion.jpg", 83.4],
    ["15-cliftonstrengths-wall.jpg", 85.5], // "better ways of working, stronger processes"
    ["16-wsl-workshop-discussion.jpg", 87.4],
    ["17-wsl-mendaki-2030-group.jpg", 89.6], // "help our teams focus on what matters most"
  ]],
  // innovation (1:32-1:41): SUTD class, three "new ideas" photos on the beat, then the MENDAKI kiosk
  // footage (moved to 96.96-99.0 s in index.html, on "embracing digitalisation"), then the SUTD selfie
  ["photos-innovation-a", 91.933, 96.964, [
    ["19-innovation-ai-programme-cohort.jpg", 91.933], // "as the way we work continues to evolve, so do we"
    // Innovenge: longer on screen (2, 2 and 3 beats) and a gentle entrance
    ["21-innovation-new-ideas-img0142.jpg", 93.225],
    ["22-innovation-new-ideas-img0150.jpg", 94.293],
    ["23-innovation-new-ideas-img0153.jpg", 95.361], // "trying new ideas"
  ], "gentle"],
  ["photos-innovation-b", 98.998, 101.5, [
    ["20-innovation-ai-programme-selfie.jpg", 98.998, "portrait"], // "and finding better ways to serve our community"
  ], "gentle"],
];

const r = (x) => Math.round(x * 1000) / 1000;
// Photo changes land on the music's beat: each change moves to the nearest beat within
// 0.28 s, i.e. always (the first photo of a scene stays where the footage goes black).
const BEATS = JSON.parse(readFileSync(new URL("../assets/music/beats.json", import.meta.url), "utf8")).beats;
const onBeat = (t) => {
  const b = BEATS.reduce((a, x) => (Math.abs(x - t) < Math.abs(a - t) ? x : a), Infinity);
  return Math.abs(b - t) <= 0.28 ? b : t;
};
for (const scene of scenes) scene[3].forEach((ph, i) => { if (i > 0) ph[1] = r(onBeat(ph[1])); });
// Card geometry, shared with the face detector (assets/photos/layout.json): every card is
// the photo at K of full size, centred a little above middle (clear of the subtitles).
const K = 0.72;
const TILT = [-3.2, 2.6, -1.8, 3.0, -2.4, 1.6, -2.9];
const NUDGE = [[-40, -6], [36, 10], [-18, -14], [44, 4], [-30, 12], [20, -10], [-44, 0]];
const layout = {};
const hosts = [];
let k = 0;
for (const [id, start, end, photos, mode] of scenes) {
  const pre = id.replace("photos-", "p").slice(0, 6);
  const els = [];
  const tweens = [];
  photos.forEach(([file, from, shape], i) => {
    const s = r(from - start);
    const e = r((photos[i + 1] ? photos[i + 1][1] : end) - start);
    const d = r(e - s);
    const n = String(i + 1).padStart(2, "0");
    const rot = TILT[k % TILT.length], [nx, ny] = NUDGE[k % NUDGE.length];
    k++;
    const cx = 960 + nx, cy = 490 + ny;
    // landscape cards are the photo at K of full frame; portrait (3:4) cards are as tall
    const cw = shape === "portrait" ? Math.round(1080 * K * 0.75) : Math.round(1920 * K), chh = Math.round(1080 * K);
    layout[file] = { cx, cy, w: cw, h: chh, rot, start: r(from), end: r(from + d) };
    // the blurred backdrop changes with the photo; the card stays until the scene ends,
    // so the previous one peeks out from under the next
    els.push(
      `    <div id="${pre}-b${n}" class="clip backdrop" data-start="${s}" data-duration="${d}" data-track-index="0">\n` +
        `      <img id="${pre}-bi${n}" src="assets/photos/backdrop/${file}" alt="" />\n    </div>`,
    );
    els.push(
      `    <div id="${pre}-p${n}" class="clip card-host" data-start="${s}" data-duration="${r(end - start - s)}" data-track-index="${1 + (i % 2)}" style="z-index: ${10 + i}">\n` +
        `      <div class="card" id="${pre}-c${n}" style="left: ${cx - cw / 2 - 16}px; top: ${cy - chh / 2 - 16}px; width: ${cw + 32}px; height: ${chh + 32}px">` +
        `<img id="${pre}-i${n}" src="assets/photos/${file}" alt="" /></div>\n    </div>`,
    );
    const first = i === 0;
    tweens.push(
      mode === "gentle"
        ? // glides in: a small settle, no bounce
          `      tl.fromTo("#${pre}-c${n}", { opacity: 0, scale: 1.06, rotation: ${r(rot + (i % 2 ? -2.5 : 2.5))}, y: -18 },` +
            ` { opacity: 1, scale: 1, rotation: ${rot}, y: 0, duration: 0.75, ease: "power3.out" }, ${s});`
        : `      tl.fromTo("#${pre}-c${n}", { opacity: 0, scale: ${first ? 1.18 : 1.32}, rotation: ${r(rot + (i % 2 ? -9 : 9))}, y: ${first ? 0 : -70} },` +
            ` { opacity: 1, scale: 1, rotation: ${rot}, y: 0, duration: 0.42, ease: "back.out(1.5)" }, ${s});`,
      `      tl.fromTo("#${pre}-i${n}", { scale: 1 }, { scale: 1.05, duration: ${d + 0.6}, ease: "none" }, ${s});`,
      `      tl.fromTo("#${pre}-bi${n}", { scale: 1.08 }, { scale: 1.16, duration: ${d}, ease: "none" }, ${s});`,
      // a quick white flash on the card as it lands
      `      tl.fromTo("#${pre}-c${n}", { "--flash": ${mode === "gentle" ? 0.3 : 0.75} }, { "--flash": 0, duration: ${mode === "gentle" ? 0.5 : 0.28}, ease: "power2.out" }, ${r(s + 0.08)});`,
    );
  });
  writeFileSync(
    new URL(`../compositions/${id}.html`, import.meta.url),
    `<template>
  <style>
    #root { position: absolute; inset: 0; overflow: hidden; background: #1a1b1e; }
    #root .backdrop { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: hidden; }
    #root .backdrop img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
    #root .card-host { position: absolute; inset: 0; }
    #root .card {
      position: absolute;
      padding: 16px;
      background: #ffffff;
      border-radius: 6px;
      box-shadow: 0 30px 70px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(0, 0, 0, 0.08);
      overflow: hidden;
      --flash: 0;
    }
    #root .card img { display: block; width: 100%; height: 100%; object-fit: cover; }
    #root .card::after { content: ""; position: absolute; inset: 0; background: #ffffff; opacity: var(--flash); }
  </style>
  <div id="root" data-composition-id="${id}" data-width="1920" data-height="1080">
${els.join("\n")}
  </div>
  <script>
    (function () {
      const tl = gsap.timeline({ paused: true });
${tweens.join("\n")}
      window.__timelines["${id}"] = tl;
    })();
  </script>
</template>
`,
  );
  hosts.push(
    `      <div id="${id}" data-composition-id="${id}" data-composition-src="compositions/${id}.html" ` +
      `data-start="${start}" data-duration="${r(end - start)}" data-track-index="1" data-track-kind="graphics" ` +
      `data-width="1920" data-height="1080" style="z-index: 2"></div>`,
  );
}
writeFileSync(new URL("../assets/photos/layout.json", import.meta.url), JSON.stringify(layout, null, 1));

const indexUrl = new URL("../index.html", import.meta.url);
const index = readFileSync(indexUrl, "utf8");
if (!index.includes("<!-- photos:start -->")) throw new Error("index.html has no photos markers");
writeFileSync(
  indexUrl,
  index.replace(/(<!-- photos:start -->)[\s\S]*?(\s*<!-- photos:end -->)/, `$1\n${hosts.join("\n")}$2`),
);
console.log(`wrote ${scenes.length} photo scenes, ${scenes.reduce((n, s) => n + s[3].length, 0)} photos`);
