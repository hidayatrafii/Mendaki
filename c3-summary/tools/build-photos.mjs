// Builds the photo scenes that fill the stretches where the original edit was black.
// The presenter is keyed in front of them (presenter-a/b.webm in index.html).
// Edit the lists below, then: node tools/build-photos.mjs
import { readFileSync, writeFileSync } from "node:fs";

// Each scene: [id, start (s), end (s), photos as [file in assets/photos, from (s)]]
// Photo changes follow the narration line each photo illustrates.
const scenes = [
  ["photos-awards", 60.267, 69.6, [
    ["01-awards-congratulations.jpg", 60.267], // "when our people reach new milestones, we celebrate them"
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
    ["16-wsl-workshop-table.jpg", 87.4],
    ["17-wsl-mendaki-2030-group.jpg", 89.6], // "help our teams focus on what matters most"
  ]],
  ["photos-community", 99.2, 101.5, [
    ["18-satellite-centre-cck-mural.jpg", 99.2], // "finding better ways to serve our community"
  ]],
];

const r = (x) => Math.round(x * 1000) / 1000;
const hosts = [];
for (const [id, start, end, photos] of scenes) {
  const pre = id.replace("photos-", "p").slice(0, 6);
  const els = [];
  const tweens = [];
  photos.forEach(([file, from], i) => {
    const s = r(from - start);
    const e = r((photos[i + 1] ? photos[i + 1][1] : end) - start);
    const d = r(e - s);
    const n = String(i + 1).padStart(2, "0");
    els.push(
      `    <div id="${pre}-p${n}" class="clip photo" data-start="${s}" data-duration="${d}" data-track-index="${i % 2}">\n` +
        `      <img id="${pre}-i${n}" src="assets/photos/${file}" alt="" />\n    </div>`,
    );
    // slow push-in, drifting the other way on every other photo
    const x = i % 2 ? 1.6 : -1.6;
    tweens.push(
      `      tl.fromTo("#${pre}-i${n}", { scale: 1.04, xPercent: 0 }, { scale: 1.12, xPercent: ${x}, duration: ${d}, ease: "none" }, ${s});`,
    );
  });
  writeFileSync(
    new URL(`../compositions/${id}.html`, import.meta.url),
    `<template>
  <style>
    #root { position: absolute; inset: 0; overflow: hidden; background: #100a2e; }
    #root .photo { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: hidden; }
    #root .photo img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
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

const indexUrl = new URL("../index.html", import.meta.url);
const index = readFileSync(indexUrl, "utf8");
if (!index.includes("<!-- photos:start -->")) throw new Error("index.html has no photos markers");
writeFileSync(
  indexUrl,
  index.replace(/(<!-- photos:start -->)[\s\S]*?(\s*<!-- photos:end -->)/, `$1\n${hosts.join("\n")}$2`),
);
console.log(`wrote ${scenes.length} photo scenes, ${scenes.reduce((n, s) => n + s[3].length, 0)} photos`);
