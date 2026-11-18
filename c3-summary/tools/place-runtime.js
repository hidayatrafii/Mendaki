// Inlined into the keyword and subtitle scenes by the build scripts.
// Finds where a block of text can sit without touching any face or the presenter.
function __hit(a, b) {
  return Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
}
// o: { measure(scale) -> {w, h}, faces, pres, side: "left"|"right"|"center",
//      xMin, xMax, yMin, yMax, prefY, pad, scales, step }
// Returns { x, y, s, cost, W, H }: the padded rectangle's top-left, the scale used, and
// how much face area it still covers (0 = clear). Prefers the largest scale that is clear.
function __placeBlock(o) {
  const scales = o.scales || [1, 0.88, 0.77, 0.67, 0.58];
  const step = o.step || 12;
  let best = null;
  for (const s of scales) {
    const m = o.measure(s);
    const W = m.w + 2 * o.pad, H = m.h + 2 * o.pad;
    let found = null;
    for (let y = o.yMin; y + H <= o.yMax; y += step) {
      const xs = [];
      if (o.side === "center") xs.push((o.xMin + o.xMax) / 2 - W / 2);
      else for (let k = 0; ; k++) {
        const x = o.side === "left" ? o.xMin + k * 24 : o.xMax - W - k * 24;
        if (x < o.xMin - 0.5 || x + W > o.xMax + 0.5) break;
        xs.push(x);
      }
      xs.forEach((x, k) => {
        if (x < o.xMin - 0.5 || x + W > o.xMax + 0.5) return;
        const r = [x, y, x + W, y + H];
        if (o.pres && __hit(r, o.pres) > 0) return;
        let cost = 0;
        for (const f of o.faces) cost += __hit(r, f);
        const pen = cost * 1000 + Math.abs(y - o.prefY) * 0.5 + k * 7 + (1 - s) * 4000;
        if (!found || pen < found.pen) found = { x, y, s, cost, pen, W, H };
      });
    }
    if (found && (!best || found.pen < best.pen)) best = found;
    if (found && found.cost === 0) break;
  }
  return best;
}
function __fontsReady() {
  const loads = ["500", "700", "800", "900"].map((w) => document.fonts.load(w + " 64px Montserrat").catch(() => null));
  return Promise.all(loads).then(() => document.fonts.ready);
}
// Text measured with the real font on a canvas: works even while a scene is hidden.
const __ctx = document.createElement("canvas").getContext("2d");
function __textW(text, weight, size, ls) {
  __ctx.font = weight + " " + size + "px Montserrat";
  return __ctx.measureText(text).width + (ls || 0) * size * text.length;
}
function __wrap(text, weight, size, maxW, ls) {
  const lines = [];
  let cur = "";
  for (const w of text.split(/\s+/)) {
    const t = cur ? cur + " " + w : w;
    if (cur && __textW(t, weight, size, ls) > maxW) { lines.push(cur); cur = w; } else cur = t;
  }
  if (cur) lines.push(cur);
  return { lines: lines.length, w: Math.max(...lines.map((l) => __textW(l, weight, size, ls))) };
}
// Places each keyword on its own: they stack like a block when there is room and spread
// into the gaps between faces when there isn't. Never over the presenter or each other.
// o: { sizes(s) -> [{ w, h, indent, gap }], faces, pres, side, xMin, xMax, yMin, yMax, prefY, pad, scales }
// Returns { s, cost, items: [{ x, y, W, H }] } (padded rectangles), the largest clear scale.
function __placeItems(o) {
  const scales = o.scales || [1, 0.88, 0.77, 0.67, 0.58, 0.5, 0.43];
  let best = null;
  for (const s of scales) {
    const items = o.sizes(s);
    const placed = [];
    let cost = 0, pen = 0, ok = true;
    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      const W = it.w + 2 * o.pad, H = it.h + 2 * o.pad;
      // the preferred spot hugs this side's edge; any spot in the safe area is allowed
      const idealX = o.side === "right" ? o.xMax - it.indent - W : o.xMin + it.indent;
      const xLo = o.areaMin != null ? o.areaMin : o.xMin, xHi = o.areaMax != null ? o.areaMax : o.xMax;
      const idealY = i === 0 ? o.prefY : placed[i - 1].y + placed[i - 1].H - 2 * o.pad + it.gap;
      let f = null;
      for (let y = o.yMin; y + H <= o.yMax; y += 12) {
        for (let x = xLo; x + W <= xHi + 0.5; x += 24) {
          const r = [x, y, x + W, y + H];
          if (o.pres && __hit(r, o.pres) > 0) continue;
          if (placed.some((p) => __hit(r, [p.x + 10, p.y + 10, p.x + p.W - 10, p.y + p.H - 10]) > 0)) continue;
          let c = 0;
          for (const fc of o.faces) c += __hit(r, fc);
          const p2 = c * 1000 + Math.abs(y - idealY) * 0.6 + Math.abs(x - idealX) * 0.4;
          if (!f || p2 < f.p) f = { x, y, W, H, c, p: p2 };
        }
      }
      if (!f) { ok = false; break; }
      placed.push(f);
      cost += f.c;
      pen += f.p;
    }
    if (!ok) continue;
    const cand = { s, cost, items: placed, pen: pen + (1 - s) * 4000 };
    if (!best || cand.cost < best.cost || (cand.cost === best.cost && cand.pen < best.pen)) best = cand;
    if (cost === 0) break;
  }
  return best;
}
