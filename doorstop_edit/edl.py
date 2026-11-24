# Each segment: list of (in, out) source ranges kept (fillers removed), note. Output order.
SEGS_RAW = [
 ([(33.30, 41.10)], "As we begin the school year... best start in life"),
 ([(45.70, 47.55), (48.70, 50.84), (52.66, 53.36)], "schoolbooks, textbooks, uniforms... fork out (drop 2x um)"),
 ([(53.66, 55.60), (56.12, 60.67)], "cost of living... low-income families (drop um)"),
 ([(61.56, 62.63)], "to support their kids"),
 ([(64.28, 64.80), (66.40, 73.13)], "MENDAKI is introducing... Primary One to university (drop 'has introduced, uh')"),
 ([(107.77, 112.95)], "this year MENDAKI is giving out $250 e-vouchers"),
 ([(117.80, 119.78), (120.00, 120.62), (121.50, 121.94), (122.40, 123.00)], "schoolbooks, stationery, or even shoes (drop uh, 2x um)"),
 ([(81.40, 82.40), (82.70, 85.00), (85.95, 90.95)], "more than one child... two or three kids (drop 2x um)"),
 ([(130.88, 133.95)], "$1,000 per capita income and below (drop 'so, uh')"),
 ([(190.61, 200.09)], "22,000 students... 13,000 TTFS"),
 ([(138.32, 151.97)], "applications from 1st December... good start"),
]
import wave, numpy as np, os
_a = None
def _audio():
    global _a
    if _a is None:
        w = wave.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio16k.wav"))
        _a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return _a
def snap(t, r=0.10):
    a = _audio()
    def e(x):
        i = int(x * 16000); return float(np.sqrt(np.mean(a[i:i+480] ** 2)))
    return min((t + k * 0.01 for k in range(int(-r*100), int(r*100) + 1)), key=e)
# flat list of clips: (in, out, seg_index, sub_index)
CLIPS = []
for si, (rs, _) in enumerate(SEGS_RAW):
    for k, (a, b) in enumerate(rs):
        CLIPS.append((round(snap(a), 2), round(snap(b), 2), si, k))
SEGS = [(a, b, f"{si}.{k}") for a, b, si, k in CLIPS]

# ---- v3: remove ALL pauses: split each kept range at silences, then frame-align ----
import numpy as _np
FPS_OUT = 30
def _env(t0, t1, hop=0.01, win=0.03):
    a = _audio(); ts = _np.arange(t0, t1, hop); out = []
    for t in ts:
        i = int(t*16000); seg = a[i:i+int(win*16000)]
        out.append(20*_np.log10(_np.sqrt(_np.mean(seg**2))+1e-9))
    return ts, _np.array(out)
def tighten(a, b, thr=-44.0, min_gap=0.16, keep=0.06):
    ts, e = _env(a, b)
    quiet = e < thr; parts = []; cur = a; i = 0
    while i < len(ts):
        if quiet[i]:
            j = i
            while j < len(ts) and quiet[j]: j += 1
            g0, g1 = ts[i], ts[min(j, len(ts)-1)]
            if g1 - g0 >= min_gap:
                if g0 - a < 0.02: cur = max(a, g1 - keep)           # leading silence
                elif b - g1 < 0.02: parts.append((cur, g0 + keep)); cur = None; break  # trailing
                else: parts.append((cur, g0 + keep)); cur = g1 - keep
            i = j
        else: i += 1
    if cur is not None: parts.append((cur, b))
    return [(x, y) for x, y in parts if y - x > 0.08]
CLIPS = []
for si, (rs, _) in enumerate(SEGS_RAW):
    k = 0
    for (a, b) in rs:
        for (x, y) in tighten(snap(a), snap(b)):
            n = max(1, round((y - x) * FPS_OUT))          # whole output frames
            CLIPS.append((round(x, 3), round(x + n / FPS_OUT, 3), si, k)); k += 1
SEGS = [(a, b, f"{si}.{k}") for a, b, si, k in CLIPS]
