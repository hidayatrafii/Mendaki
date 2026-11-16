// Builds compositions/captions.html (the subtitles) from assets/transcript.json.
// Fix a misheard word by editing the transcript or FIXES below, then: node tools/build-captions.mjs
import { readFileSync, writeFileSync } from "node:fs";

const MAX_WORDS = 5;
const PAUSE = 0.15; // a pause this long (s) starts a new caption
const FIXES = { mendaki: "MENDAKI", "mendaki,": "MENDAKI,", "mendaki.": "MENDAKI.", program: "programme", "program,": "programme," };

const words = JSON.parse(readFileSync(new URL("../assets/transcript.json", import.meta.url), "utf8"))
  .map((w) => ({ ...w, text: FIXES[w.text.toLowerCase()] ?? w.text }))
  .filter((w) => w.text.trim());

const groups = [];
let cur = [];
words.forEach((w, i) => {
  cur.push(w);
  const next = words[i + 1];
  const sentenceEnd = /[.!?]$/.test(w.text);
  const comma = /,$/.test(w.text) && cur.length >= 3;
  const pause = next && next.start - w.end >= PAUSE;
  if (!next || sentenceEnd || comma || pause || cur.length >= MAX_WORDS) {
    groups.push(cur);
    cur = [];
  }
});

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const r = (x) => Math.round(x * 1000) / 1000;
const html = [];
const data = [];
groups.forEach((g, gi) => {
  const id = `cap-${String(gi + 1).padStart(3, "0")}`;
  const start = Math.max(0.15, g[0].start - 0.05);
  const nextStart = groups[gi + 1] ? Math.max(0.15, groups[gi + 1][0].start - 0.05) : Infinity;
  const end = Math.min(g[g.length - 1].end + 0.3, nextStart - 0.02);
  html.push(
    `      <div class="cg" id="${id}"><span class="pill">` +
      g.map((w, wi) => `<span class="cw" id="${id}-${wi}">${esc(w.text)}</span>`).join(" ") +
      `</span></div>`,
  );
  data.push([id, r(start), r(end), g.map((w) => [r(w.start), r(w.end)])]);
});
const last = data[data.length - 1][2];

const out = `<template>
  <style>
    #root {
      position: absolute;
      inset: 0;
      overflow: visible;
      font-family: "Montserrat", sans-serif;
    }
    #root .cg {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 92px;
      text-align: center;
      opacity: 0;
      visibility: hidden;
    }
    #root .pill {
      display: inline-block;
      max-width: 1500px;
      padding: 12px 30px 15px;
      border-radius: 999px;
      background: rgba(16, 10, 46, 0.74);
      box-shadow: 0 10px 30px rgba(10, 6, 30, 0.3);
      font-size: 42px;
      font-weight: 700;
      line-height: 1.2;
      letter-spacing: -0.005em;
      color: #fff;
    }
    #root .cw {
      display: inline-block;
    }
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
${html.join("\n")}
  </div>
  <script>
    (function () {
      // [group id, show, hide, [[word start, word end], ...]] from tools/build-captions.mjs
      const G = ${JSON.stringify(data)};
      const tl = gsap.timeline({ paused: true });
      G.forEach(([id, start, end, ws]) => {
        const g = "#" + id;
        tl.set(g, { visibility: "visible" }, start);
        tl.fromTo(g, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.18, ease: "power2.out" }, start);
        ws.forEach(([s, e], i) => {
          // the spoken word lights up gold
          tl.fromTo(g + "-" + i, { color: "#ffffff" }, { color: "#fcd400", duration: 0.08, ease: "none" }, s);
          const back = Math.min(e, end - 0.14);
          if (back >= s + 0.09) tl.to(g + "-" + i, { color: "#ffffff", duration: 0.12, ease: "none" }, back);
        });
        tl.to(g, { opacity: 0, duration: 0.12, ease: "power2.in" }, end - 0.12);
        tl.set(g, { opacity: 0, visibility: "hidden" }, end);
      });
      window.__timelines["captions"] = tl;
    })();
  </script>
</template>
`;
writeFileSync(new URL("../compositions/captions.html", import.meta.url), out);
console.log(`wrote ${groups.length} caption groups, last ends ${last}s`);
