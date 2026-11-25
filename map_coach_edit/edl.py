# MAP Coach recruitment video - edit decision list (v2: question-led flow, pauses trimmed).
# RAW entries are answer "phrases" in source time; the build step splits them at internal pauses (> MAX_GAP) so the
# delivery is snappy. Subtitles are given in SOURCE time and mapped to output time by the renderer.
import os, wave, numpy as np
WORK = "/home/user/Mendaki/work"
SRC = {
    "S":   "S_DJI_20261114111251_0188_D",   # Syaheer, single long take
    "A91": "A_DJI_20261114112727_0191_D",   # Azyyati intro / inspiration
    "A92": "A_DJI_20261114113346_0192_D",   # Azyyati rewarding (clean take)
    "A95": "A_DJI_20261114113856_0195_D",   # Azyyati encourage + memorable story + hope (banner in shot at ~18-25 s)
}
QUESTIONS = {   # shown in the question box above the speakers' heads
    "q1": "What inspired you?",
    "q2": "Most rewarding part?",
    "q3": "A memorable moment?",
    "q4": "Beyond academics?",
    "q5": "Thinking of joining?",
}
_aud = {}
def _a(k):
    if k not in _aud:
        w = wave.open(f"{WORK}/aud/{SRC[k]}.wav")
        _aud[k] = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return _aud[k]
def _env(k):
    """10 ms RMS envelope in dB"""
    a = _a(k); h = 160; n = len(a) // h
    return 20 * np.log10(np.sqrt(np.mean(a[:n*h].reshape(n, h) ** 2, 1)) + 1e-9)
def snap(k, t, r=0.05):
    a = _a(k)
    def e(x):
        i = max(0, int(x * 16000)); return float(np.sqrt(np.mean(a[i:i+160] ** 2) + 1e-12))
    return min((t + j * 0.005 for j in range(int(-r*200), int(r*200) + 1)), key=e)

# (key, in, out, prefer_tight, [subtitle phrases (text, s, e)], section)
RAW = [
 # HOOK - payoff of Azyyati's story
 ("A95", 215.50, 217.32, True,  [("The first thing she did", 215.58, 216.42), ("was to call me", 216.42, 217.28)], "hook"),
 ("A95", 220.38, 224.22, False, [("and thank me for the contribution", 220.45, 223.30), ("I had in her life.", 223.30, 224.16)], "hook"),
 # INTROS (years of service are on the lower thirds)
 ("S",   38.30, 43.84, False, [("Hi, I'm Syaheer.", 38.36, 39.00), ("I've been a MAP Coach since 2011,", 39.34, 42.48), ("which is about 15 years ago.", 42.70, 43.76)], "intro"),
 ("A91", 22.62, 24.51, False, [("Hi, I'm Nur Azyyati.", 22.68, 24.24)], "intro"),
 ("A91", 91.42, 93.62, True, [("Teaching has always been my passion.", 91.50, 93.54)], "intro"),
 # Q1 WHAT INSPIRED YOU - each coach answers in one go
 ("S",   54.12, 61.72, False, [("I used to be an educator,", 54.20, 55.14), ("so I've moved out to IT", 55.42, 58.10), ("in corporate roles.", 58.10, 58.98), ("And this is my way of giving back.", 59.48, 61.68)], "q1"),
 ("A91", 108.86, 113.56, True, [("I want to help those, especially students", 108.90, 110.64), ("who need more guidance and support.", 110.64, 113.52)], "q1"),
 # Q2 MOST REWARDING PART
 ("S",   73.84, 78.46, True,  [("I get to interact with a lot of students", 73.90, 76.16), ("and I've touched many lives.", 76.16, 78.44)], "q2"),
 ("A92", 13.12, 21.16, False, [("It's fulfilling to see students", 13.18, 14.94), ("who initially struggle,", 14.94, 16.55), ("doubt themselves or lack motivation", 17.26, 19.02), ("slowly begin to believe", 19.02, 20.10), ("in their own abilities.", 20.10, 21.12)], "q2"),
 # Q3 A MEMORABLE MOMENT - Azyyati's story (pays off the hook)
 ("A95", 170.84, 174.34, False, [("Back in 2024, I was teaching", 170.86, 172.92), ("a Primary 6 Foundation student.", 172.92, 174.30)], "q3"),
 ("A95", 176.58, 178.10, True,  [("She has to retake her PSLE.", 176.62, 177.86)], "q3"),
 ("A95", 181.68, 184.68, False, [("She told me that", 181.72, 182.64), ("this is the last time.", 182.64, 184.66)], "q3"),
 ("A95", 199.78, 201.54, True,  [("She worked really, really hard.", 199.80, 201.50)], "q3"),
 ("A95", 224.71, 228.60, False, [("She actually passed", 224.75, 226.60), ("her Math Foundation", 226.60, 228.58)], "q3"),
 ("A95", 229.20, 230.08, True,  [("for the first time.", 229.22, 230.02)], "q3"),
 # Q4 BEYOND ACADEMICS
 ("A95", 18.35, 25.40, False, [("I hope my students walk away", 18.50, 20.02), ("with greater confidence in themselves", 20.02, 22.04), ("and believe that they are capable", 22.04, 23.48), ("of achieving more than they think.", 23.48, 25.30)], "q4"),
 # Q5 THINKING OF JOINING
 ("S",   202.88, 208.30, False, [("As the head coaches and coaches", 202.93, 205.26), ("come from many different backgrounds,", 205.26, 206.76), ("not strictly just education.", 206.92, 208.16)], "q5"),
 ("A95", 96.98, 100.86, False, [("You don't have to be a perfect educator", 97.00, 99.04), ("because I think every human makes mistakes.", 99.04, 100.82)], "q5"),
 ("A95", 101.50, 107.58, True,  [("As long as you are passionate,", 101.50, 102.90), ("you have the patience", 103.50, 104.14), ("and you are willing to have", 104.14, 106.16), ("an impact on a child's life.", 106.16, 107.54)], "q5"),
 ("S",   291.40, 294.34, False, [("If you are already thinking about it,", 291.48, 293.08), ("sign up.", 293.78, 294.24)], "q5"),
]

MAX_GAP, KEEP = 0.20, 0.07      # pauses longer than MAX_GAP are cut down to 2*KEEP of air
_floor = {}
def split_pauses(k, a, b):
    e = _env(k)
    if k not in _floor: _floor[k] = float(np.percentile(e, 10))      # room tone of the whole take
    th = _floor[k] + 6                                                 # only true silence counts as a pause
    segs = []; cur = a; i = int(a * 100); end = int(b * 100); run = None
    while i < end:
        if e[i] < th:
            run = i if run is None else run
        else:
            if run is not None and (i - run) / 100 > MAX_GAP and run / 100 - cur > 0.15:
                segs.append((cur, run / 100 + KEEP)); cur = i / 100 - KEEP
            run = None
        i += 1
    segs.append((cur, b)); return segs

CLIPS = []
for p, (k, a, b, tight, subs, sec) in enumerate(RAW):
    a, b = snap(k, a), snap(k, b)
    for j, (sa, sb) in enumerate(split_pauses(k, a, b)):
        sa = a if j == 0 else snap(k, sa, 0.03); sb = b if sb == b else snap(k, sb, 0.03)
        CLIPS.append(dict(key=k, src=SRC[k], a=round(sa, 3), b=round(sb, 3), zoom=1.2 if tight else 1.0,
                          sec=sec, parent=p, subs=[]))
# attach each subtitle phrase to the sub-clip in which it starts (or the next one if it starts in a removed pause)
for p, (k, a, b, tight, subs, sec) in enumerate(RAW):
    cs = [c for c in CLIPS if c["parent"] == p]
    for text, s, e in subs:
        c = next((c for c in cs if s < c["b"] - 0.05), cs[-1])
        c["subs"].append((text, max(s, c["a"]), e))

if __name__ == "__main__":
    t = 0; raw_t = sum(r[2] - r[1] for r in RAW)
    for c in CLIPS:
        d = c["b"] - c["a"]; print(f"{t:6.2f} +{d:5.2f} p{c['parent']:02d} {c['key']:4} {c['a']:7.2f}-{c['b']:7.2f} {c['sec']:6} {' / '.join(s[0] for s in c['subs'])}"); t += d
    print(f"speech total {t:.2f}s (before pause trimming {raw_t:.2f}s)")
