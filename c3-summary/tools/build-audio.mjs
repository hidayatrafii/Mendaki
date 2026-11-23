// Writes the music track (with its volume envelope) and the sound effects into index.html.
// Music: full for the beat intro, ducked under the narration, lifted in the pauses, full
// for the logo. SFX: transition whooshes (assets/transition-cues.json), a pop as each
// sticker keyword lands, a bass hit and sparkle on the logo.
// Run after tools/build-transitions.mjs and tools/build-cards.mjs: node tools/build-audio.mjs
import { readFileSync, writeFileSync, readdirSync } from "node:fs";

const r = (x) => Math.round(x * 1000) / 1000;
const words = JSON.parse(readFileSync(new URL("../assets/transcript.json", import.meta.url), "utf8"));
// speaking stretches: words merged across gaps under 0.45 s
const speech = [];
for (const w of words) {
  const last = speech[speech.length - 1];
  if (last && w.start - last[1] < 0.45) last[1] = Math.max(last[1], w.end);
  else speech.push([w.start, w.end]);
}
// under the voice the music sits ~15 dB below it (voice -16 LUFS, music -13.6 LUFS at full)
const DUCK = 0.13, GAP = 0.3, FULL = 0.95, RAMP = 0.25;
const pts = [{ t: 0, v: FULL }, { t: 2.9, v: FULL }];
for (const [s, e] of speech) {
  pts.push({ t: r(Math.max(s - RAMP, pts[pts.length - 1].t + 0.01)), v: pts[pts.length - 1].v });
  pts.push({ t: r(s), v: DUCK });
  pts.push({ t: r(e), v: DUCK });
  pts.push({ t: r(e + RAMP), v: GAP });
}
// the article's music break (after "serve our community"): music comes up to full
const M = JSON.parse(readFileSync(new URL("../assets/music/beats.json", import.meta.url), "utf8"));
const BRK = [M.break_at + 0.05, M.break_at + M.break_len - 0.15];
for (let i = pts.length - 1; i >= 0; i--) if (pts[i].t > BRK[0] - 0.3 && pts[i].t < BRK[1] + 0.3) pts.splice(i, 1);
pts.push({ t: r(BRK[0] - 0.25), v: GAP }, { t: r(BRK[0] + 0.35), v: FULL }, { t: r(BRK[1] - 0.35), v: FULL }, { t: r(BRK[1] + 0.05), v: DUCK });
pts.sort((a, b) => a.t - b.t);
// clean up overlapping ramps (a gap shorter than two ramps stays ducked)
const env = [];
for (const p of pts) {
  while (env.length && env[env.length - 1].t >= p.t) env.pop();
  env.push(p);
}
// full for the montage and the end card (the track fades itself out)
env.push({ t: 135.568, v: env[env.length - 1].v }, { t: 136.038, v: FULL }, { t: 202.818, v: FULL });
const automation = { version: 1, lanes: [{ target: "volume", points: env.filter((p, i) => i === 0 || p.t > env[i - 1].t) }] };
if (automation.lanes[0].points.length > 512) throw new Error("too many volume points");

// sound effects
const cues = JSON.parse(readFileSync(new URL("../assets/transition-cues.json", import.meta.url), "utf8")).whoosh;
cues.push([2.55, "whoosh-short", 0.3], [135.618, "whoosh", 0.3], [194.768, "impact-bass-1", 0.55], [194.888, "sparkle", 0.32]);
cues.push([101.2, "whoosh-short", 0.3], [102.45, "pop", 0.22], [106.0, "sparkle", 0.3]); // the article: in, headline highlight, "ready within an hour"
cues.push(...JSON.parse(readFileSync(new URL("../assets/montage-cues.json", import.meta.url), "utf8")));
// a pop for each sticker keyword as it lands (same timing as tools/dimension.template.html)
for (const f of readdirSync(new URL("../compositions/", import.meta.url)).filter((f) => /^dim-\d\d[a-z]?\.html$/.test(f))) {
  const html = readFileSync(new URL(`../compositions/${f}`, import.meta.url), "utf8");
  const cfg = JSON.parse(html.match(/const v = (\{.*?\});/)[1]);
  if (cfg.layout !== "sticker" || cfg.cont) continue;
  const idx = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const id = f.replace(".html", "");
  const start = +idx.match(new RegExp(`id="${id}"[^>]*data-start="([\\d.]+)"`))[1];
  const gap = Math.min(1.0, Math.max(0.4, (cfg.dur - 2.0) / 3.2));
  [0, 1, 2].forEach((i) => cues.push([r(start + 0.25 + i * gap + 0.08), "pop", 0.22]));
}
cues.sort((a, b) => a[0] - b[0]);
const DUR = { whoosh: 0.57, "whoosh-short": 0.57, pop: 0.72, "impact-bass-1": 2.12, sparkle: 1.8 };
// two lanes so overlapping effects never share one
const laneEnd = [0, 0, 0];
const sfx = cues.map(([t, name, vol], i) => {
  const lane = laneEnd[0] <= t ? 0 : laneEnd[1] <= t ? 1 : 2;
  laneEnd[lane] = t + DUR[name];
  return `      <audio id="sfx-${String(i + 1).padStart(3, "0")}" class="clip" src="assets/sfx/${name}.mp3" data-start="${r(Math.max(0, t))}" ` +
    `data-duration="${DUR[name]}" data-track-index="${8 + lane}" data-volume="${vol}"></audio>`;
});

const music = `      <audio
        id="music"
        class="clip"
        src="assets/music/adventure-edit.m4a"
        data-start="0"
        data-duration="202.818"
        data-media-start="0"
        data-track-index="7"
        data-timeline-role="music"
        data-volume="1"
        data-automation='${JSON.stringify(automation)}'
      ></audio>`;
const url = new URL("../index.html", import.meta.url);
let index = readFileSync(url, "utf8");
index = index.replace(/(<!-- music:start -->)[\s\S]*?(\s*<!-- music:end -->)/, `$1\n${music}$2`);
index = index.replace(/(<!-- sfx:start -->)[\s\S]*?(\s*<!-- sfx:end -->)/, `$1\n${sfx.join("\n")}$2`);
writeFileSync(url, index);
console.log(`music envelope: ${automation.lanes[0].points.length} points; ${sfx.length} sound effects`);
