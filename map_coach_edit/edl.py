# MAP Coach recruitment video - edit decision list.
# Each clip: (source key, in, out, zoom, display subtitle phrases [(text, src_start, src_end)])
# Subtitle phrases are given in SOURCE time; they are mapped to output time by the renderer.
import os, json, wave, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = "/home/user/Mendaki/work"
SRC = {
    "S":   "S_DJI_20261114111251_0188_D",   # Syaheer, single long take
    "A91": "A_DJI_20261114112727_0191_D",   # Azyyati intro / inspiration
    "A92": "A_DJI_20261114113346_0192_D",   # Azyyati rewarding (clean take)
    "A94": "A_DJI_20261114113643_0194_D",   # Azyyati beyond academics (clean take)
    "A95": "A_DJI_20261114113856_0195_D",   # Azyyati encourage + memorable story
}
_aud = {}
def _a(k):
    if k not in _aud:
        w = wave.open(f"{WORK}/aud/{SRC[k]}.wav")
        _aud[k] = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return _aud[k]
def snap(k, t, r=0.05):
    """move a cut point to the quietest 10 ms window within +-r so cuts never land mid-syllable"""
    a = _a(k)
    def e(x):
        i = max(0, int(x * 16000)); return float(np.sqrt(np.mean(a[i:i+160] ** 2) + 1e-12))
    return min((t + j * 0.005 for j in range(int(-r*200), int(r*200) + 1)), key=e)

# (key, in, out, zoom, [subtitle phrases (text, s, e) in source time], section)
RAW = [
 # HOOK - payoff of Azyyati's story
 ("A95", 215.50, 217.32, 1.18, [("The first thing she did", 215.58, 216.42), ("was to call me", 216.42, 217.28)], "hook"),
 ("A95", 220.38, 224.22, 1.18, [("and thank me for the contribution", 220.45, 223.30), ("I had in her life.", 223.30, 224.16)], "hook"),
 # INTROS
 ("S",   38.30, 43.84, 1.00, [("Hi, I'm Syaheer.", 38.36, 39.00), ("I've been an MAP Coach since 2011,", 39.34, 42.48), ("which is about 15 years ago.", 42.70, 43.76)], "intro_s"),
 ("A91", 22.62, 24.26, 1.00, [("Hi, I'm Nur Azyyati.", 22.68, 24.24)], "intro_a"),
 ("A91", 91.42, 93.62, 1.18, [("Teaching has always been my passion.", 91.50, 93.54)], "intro_a"),
 # Q1 INSPIRATION
 ("S",   54.12, 59.02, 1.18, [("I used to be an educator,", 54.20, 55.14), ("so I've moved out to IT", 55.42, 58.10), ("in corporate roles.", 58.10, 58.98)], "q1"),
 ("S",   59.44, 61.72, 1.00, [("And this is my way of giving back.", 59.48, 61.68)], "q1"),
 ("A91", 108.86, 113.56, 1.00, [("I want to help those, especially students", 108.90, 110.64), ("who need more guidance and support.", 110.64, 113.52)], "q1"),
 # Q2 REWARDING
 ("S",   73.84, 78.46, 1.18, [("I get to interact", 73.90, 75.16), ("with a lot of students", 75.16, 76.16), ("and I've touched many lives.", 76.16, 78.44)], "q2"),
 ("A92", 13.12, 16.58, 1.18, [("It's fulfilling to see students", 13.18, 14.94), ("who initially struggle,", 14.94, 16.55)], "q2"),
 ("A92", 17.22, 21.16, 1.00, [("doubt themselves or lack motivation", 17.26, 19.02), ("slowly begin to believe", 19.02, 20.10), ("in their own abilities.", 20.10, 21.12)], "q2"),
 # Q3 MEMORABLE
 ("S",   109.58, 112.36, 1.00, [("When I meet them outside now,", 109.64, 111.08), ("they are doing well.", 111.12, 112.32)], "q3"),
 ("S",   112.56, 117.86, 1.18, [("Before this, they were actually", 112.60, 114.32), ("not very confident about themselves.", 114.32, 117.82)], "q3"),
 ("A95", 170.84, 174.34, 1.00, [("Back in 2024, I was teaching", 170.86, 172.92), ("a Primary 6 Foundation student.", 172.92, 174.30)], "q3"),
 ("A95", 176.58, 177.90, 1.00, [("She has to retake her PSLE.", 176.62, 177.86)], "q3"),
 ("A95", 181.68, 184.68, 1.18, [("She told me that", 181.72, 182.64), ("this is the last time.", 182.64, 184.66)], "q3"),
 ("A95", 199.78, 201.54, 1.00, [("She worked really, really hard.", 199.80, 201.50)], "q3"),
 ("A95", 224.71, 228.60, 1.18, [("She actually passed", 224.84, 226.60), ("her Math Foundation", 226.60, 228.58)], "q3"),
 ("A95", 229.20, 230.08, 1.18, [("for the first time.", 229.22, 230.02)], "q3"),
 # Q4 BEYOND ACADEMICS
 ("A95", 18.35, 25.40, 1.00, [("I hope my students walk away", 18.50, 20.02), ("with greater confidence in themselves", 20.02, 22.04), ("and believe that they are capable", 22.04, 23.48), ("of achieving more than they think.", 23.48, 25.30)], "q4"),   # 0194 take has a sponsor banner in shot
 # Q5 ENCOURAGE
 ("A95", 96.98, 100.86, 1.18, [("You don't have to be a perfect educator", 97.00, 99.04), ("because I think every human makes mistakes.", 99.04, 100.82)], "q5"),
 ("A95", 101.50, 107.58, 1.00, [("As long as you are passionate,", 101.50, 102.90), ("you have the patience", 103.50, 104.14), ("and you are willing to have", 104.14, 106.16), ("an impact on a child's life.", 106.16, 107.54)], "q5"),
 ("S",   291.40, 294.34, 1.18, [("If you are already thinking about it,", 291.48, 293.08), ("sign up.", 293.78, 294.24)], "q5"),
]
CLIPS = []
for k, a, b, z, subs, sec in RAW:
    CLIPS.append(dict(key=k, src=SRC[k], a=round(snap(k, a), 3), b=round(snap(k, b), 3), zoom=z, subs=subs, sec=sec))
if __name__ == "__main__":
    t = 0
    for c in CLIPS:
        d = c["b"] - c["a"]; print(f"{t:6.2f} +{d:5.2f} {c['key']:4} {c['a']:7.2f}-{c['b']:7.2f} {c['sec']:8} {' / '.join(s[0] for s in c['subs'])}"); t += d
    print("speech total", round(t, 2))
