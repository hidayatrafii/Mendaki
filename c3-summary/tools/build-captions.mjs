// Builds compositions/captions.html (the subtitles) from assets/transcript.json.
// Fix a misheard word by editing the transcript or FIXES below, then: node tools/build-captions.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { presenterBox, track } from "./presenter.mjs";

// Each caption sits in the widest free stretch of the bottom band beside the presenter.
function placeCaption(start, end) {
  const b = presenterBox(start, end);
  if (!b) return { left: 160, width: 1600 };
  const spans = [
    [96, b[0] - 30],
    [b[2] + 30, 1920 - 96],
  ].map(([a, z]) => [a, Math.max(0, z - a)]);
  const [left, width] = spans.sort((x, y) => y[1] - x[1])[0];
  return { left: Math.round(left), width: Math.round(Math.min(width, 1600)) };
}

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
  // a caption that straddles a camera cut where the presenter moves hops to the free side at the cut
  let parts = [[start, end]];
  if (placeCaption(start, end).width < 600) {
    const cuts = track.map((t) => t.start).filter((c) => c > start + 0.05 && c < end - 0.05);
    const edges = [start, ...cuts, end];
    parts = edges.slice(1).map((e, k) => [edges[k], e]);
  }
  const words = g.map((w, wi) => `<span class="cw" id="${id}-PART-${wi}">${esc(w.text)}</span>`).join(" ");
  parts.forEach(([ps, pe], k) => {
    const pid = parts.length > 1 ? `${id}${"abcd"[k]}` : id;
    const pos = placeCaption(ps, pe);
    const narrow = pos.width < 760 ? " narrow" : "";
    html.push(
      `      <div class="cg${narrow}" id="${pid}" style="left: ${pos.left}px; width: ${pos.width}px"><span class="pill">` +
        words.replaceAll(`${id}-PART-`, `${pid}-`) +
        `</span></div>`,
    );
    data.push([pid, r(ps), r(pe), g.map((w) => [r(w.start), r(w.end)]), k > 0 ? 1 : 0]);
  });
});
const last = Math.max(...data.map((d) => d[2]));

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
      bottom: 92px;
      text-align: center;
      opacity: 0;
      visibility: hidden;
    }
    #root .pill {
      display: inline-block;
      max-width: 100%;
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
    #root .cg.narrow .pill {
      font-size: 36px;
      padding: 10px 24px 13px;
      border-radius: 30px;
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
      // [group id, show, hide, [[word start, word end], ...], continues-at-a-cut] from tools/build-captions.mjs
      const G = ${JSON.stringify(data)};
      const tl = gsap.timeline({ paused: true });
      G.forEach(([id, start, end, ws, cont]) => {
        const g = "#" + id;
        tl.set(g, { visibility: "visible" }, start);
        if (cont) tl.set(g, { opacity: 1, y: 0 }, start);
        else tl.fromTo(g, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.18, ease: "power2.out" }, start);
        ws.forEach(([s, e], i) => {
          if (e <= start || s >= end) return;
          // the spoken word lights up gold
          tl.fromTo(g + "-" + i, { color: "#ffffff" }, { color: "#fcd400", duration: 0.08, ease: "none" }, s);
          const back = Math.min(e, end - 0.14);
          if (back >= s + 0.09) tl.to(g + "-" + i, { color: "#ffffff", duration: 0.12, ease: "none" }, back);
        });
        if (!G.some((o) => o[4] && Math.abs(o[1] - end) < 0.001 && o[0].slice(0, 7) === id.slice(0, 7)))
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
