# MAP Coach recruitment video renderer (9:16, 1080x1920, 29.97 fps).
#   python3 render.py OUT.mp4 [--preview SECONDS]
# Picture is composited per frame (sub-pixel zooms -> no jitter); every segment is cut on whole frames and its
# audio is cut to exactly the same length, so A/V never drifts. Subtitles are burned last with libass using the
# doorstop style template (Poppins ExtraBold, #EEDCA2).
import sys, os, json, subprocess, wave
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from edl import CLIPS, RAW, QUESTIONS
from PIL import ImageFont
ROOT = "/home/user/Mendaki"; FOOT = f"{ROOT}/footage"; WORK = f"{ROOT}/work"
W, H = 1080, 1920; FPS = 30000 / 1001; SR = 48000
DW, DH = 1728, 3072                       # decode size for interviews (headroom for punch-ins)
TAIL = 4.0                                # end card after the last word
MUSIC_IN = 10.0                           # start of the used section in the music file (track 1 ends ~98 s)

# ---------------------------------------------------------------- timeline
FACE = {"S": (567, 675), "A91": (553, 661), "A92": (540, 648), "A95": (537, 750)}  # 1080-scale
BASE = {"S": 1.0, "A91": 1.0, "A92": 1.12, "A95": 1.12}
TY = {}
t0 = 0; prev = None
for i, c in enumerate(CLIPS):
    c["n"] = int(round((c["b"] - c["a"]) * FPS)); c["f0"] = t0; t0 += c["n"]
    # framing: constant within an answer (pause cuts get a short soft dissolve instead of a zoom change);
    # alternates only between consecutive answers of the same speaker
    same = prev is not None and prev["parent"] == c["parent"]
    tight = prev["tight"] if same else ((not prev["tight"]) if prev and prev["key"] == c["key"] else c["zoom"] > 1)
    c["tight"] = tight; c["z"] = BASE[c["key"]] * (1.2 if tight else 1.0)
    c["xfade"] = same
    c["settle"] = prev is None or prev["sec"] != c["sec"]          # soft push-in at the start of each section
    prev = c
NS = t0; NT = NS + int(round(TAIL * FPS)); TOTAL = NT / FPS
def ft(f): return f / FPS
def clip_t(i): return ft(CLIPS[i]["f0"])

def src2frame(p, t):
    """output frame of source time t inside answer p (snaps to the next kept piece if t falls in a removed pause)"""
    cs = [c for c in CLIPS if c["parent"] == p]
    for c in cs:
        if t < c["b"]: return c["f0"] + max(0, int(round((t - c["a"]) * FPS)))
    return cs[-1]["f0"] + cs[-1]["n"]
def pend(p): c = [c for c in CLIPS if c["parent"] == p][-1]; return c["f0"] + c["n"]
def pstart(p): return [c for c in CLIPS if c["parent"] == p][0]["f0"]
def P(key, a):  # answer index from its RAW in-point
    return next(i for i, x in enumerate(RAW) if x[0] == key and abs(x[1] - a) < 0.01)
# b-roll: (answer, source time it starts at or None = answer start, duration s or None = to answer end, file, source in s)
BROLL = [
    (P("S", 54.12), 59.30, 3.0, "DJI_20261114092503_0146_D", 0.3),     # "my way of giving back" -> coaches in discussion
    (P("S", 54.12), 64.40, 3.0, "DJI_20261114095607_0175_D", 0.3),     # "contributing to the community in education" -> wide of the session (steady)
    (P("S", 74.32), 74.90, 3.3, "DJI_20261114092728_0149_D", 1.0),     # "interact with a lot of students"
    (P("A92", 13.12), 17.26, 3.2, "DJI_20261114094848_0171_D", 0.2),   # Azyyati at the coaches' session
    (P("A95", 199.78), None, None, "DJI_20261114094206_0166_D", 2.0),  # "worked really hard" -> worksheets on the table
    (P("A95", 18.35), None, 3.85, "DJI_20261114101621_0180_D", 0.3),   # whole line as voice-over (sponsor banner in that take)
    (P("A95", 18.35), "chain", None, "DJI_20261114101644_0181_D", 0.0),
    (P("S", 203.72), 205.20, 3.0, "DJI_20261114092303_0141_D", 0.3),   # "many different backgrounds" -> coaches chatting
    (P("A95", 101.50), 103.40, 3.8, "DJI_20261114095808_0178_D", 0.4), # "impact on a child's life" -> coach sharing with mic
]
BR = []
for p, t, dur, f, si in BROLL:
    s = BR[-1]["e"] if t == "chain" else (pstart(p) if t is None else src2frame(p, t))
    e = pend(p) if dur is None else min(pend(p) if t is None else 10**9, s + int(round(dur * FPS)))
    if t == "chain": BR[-1]["hard_out"] = True
    BR.append(dict(s=s, e=e, f=f, si=si, hard_in=t is None or t == "chain", hard_out=dur is None))
CUTS = sorted({c["f0"] for c in CLIPS} | {NS})
for b in BR:     # a dissolve that starts/ends right at a cut looks like a double exposure: snap it to the cut instead
    k = min(CUTS, key=lambda x: abs(x - b["s"]))
    if not b["hard_in"] and abs(k - b["s"]) <= 9: b["s"], b["hard_in"] = k, True
    k = min(CUTS, key=lambda x: abs(x - b["e"]))
    if not b["hard_out"] and abs(k - b["e"]) <= 9: b["e"], b["hard_out"] = k, True

# graphics: (png, start frame, end frame, motion)
def fr(t): return int(round(t * FPS))
GFX = [
    ("lt_syaheer.png", pstart(P("S", 38.30)) + fr(0.35), pstart(P("S", 38.30)) + fr(4.6), "up"),
    ("lt_azyyati.png", pstart(P("A91", 22.62)) + fr(0.25), pend(P("A91", 91.42)) - fr(0.2), "up"),
    # CTA end card, built up in stages: card -> line 1 -> URL -> underline wipe -> line 3
    ("end_bg.png", NS + fr(0.35), NT, "card"),
    ("end_l1.png", NS + fr(0.65), NT, "rise"),
    ("end_url.png", NS + fr(0.90), NT, "popc"),
    ("end_ul.png", NS + fr(1.25), NT, "wipe"),
    ("end_l3.png", NS + fr(1.45), NT, "rise"),
]
SECTIONS = {}
for c in CLIPS:
    if c["sec"] in QUESTIONS:
        s0, e0 = SECTIONS.get(c["sec"], (10**9, 0)); SECTIONS[c["sec"]] = (min(s0, c["f0"]), max(e0, c["f0"] + c["n"]))
for q, (s0, e0) in SECTIONS.items():          # question box over each answer block, just above the heads
    GFX.append((f"{q}.png", s0 + fr(0.08), e0 - fr(0.12), "pop"))

# ---------------------------------------------------------------- subtitles (doorstop template)
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
def srt(t): return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(round(t%1*1000))%1000:03d}"
caps = []
for ci, c in enumerate(CLIPS):
    for text, s, e in c["subs"]:
        o = ft(c["f0"]); a = max(o, o + s - c["a"]); b = min(o + ft(c["n"]), o + e - c["a"])
        caps.append([a, b, text, ci, s, e])
for k in range(len(caps) - 1):
    caps[k][1] = caps[k + 1][0]                 # each line holds until the next starts (doorstop behaviour)...
    c, d = CLIPS[caps[k][3]], CLIPS[caps[k + 1][3]]
    if c["key"][0] != d["key"][0]:
        caps[k][1] = ft(pend(c["parent"]))      # ...but never carries over onto the other coach
caps[-1][1] = ft(NS) + 0.15
CAPX = [list(x) for x in caps]                 # keeps clip / source times for word-timed splitting
caps = [x[:3] for x in caps]
import json as _json
_WORDS = {}
def src_words(key, s, e):
    if key not in _WORDS: _WORDS[key] = _json.load(open(f"{WORK}/aud/{CLIPS[[c['key'] for c in CLIPS].index(key)]['src']}.json"))
    return [w for w in _WORDS[key] if s - 0.12 <= w["s"] < e + 0.05]
# Line layout: libass renders this style like Poppins ExtraBold at ~41.4 px; wrap ourselves so the two lines sit closer
SUBF = ImageFont.truetype(f"{ROOT}/fonts/Poppins-ExtraBold.ttf", 41.4); MAXW = 700; BASE_Y = 1400; PITCH = 54
def tw(s): b = SUBF.getbbox(s); return b[2] - b[0]
def wrap(t):
    """fewest lines that fit MAXW, as evenly balanced as possible"""
    w = t.split()
    if tw(t) <= MAXW: return [t]
    best = None
    for i in range(1, len(w)):
        L = [" ".join(w[:i]), " ".join(w[i:])]
        if max(map(tw, L)) <= MAXW and (best is None or max(map(tw, L)) < max(map(tw, best))): best = L
    if best: return best
    for i in range(1, len(w) - 1):
        for j in range(i + 1, len(w)):
            L = [" ".join(w[:i]), " ".join(w[i:j]), " ".join(w[j:])]
            if best is None or max(map(tw, L)) < max(map(tw, best)): best = L
    return best
def one_line(caps):
    """every caption on a single line: split longer ones into balanced chunks, each timed from its first word's
    timestamp (mapped through the edit), falling back to its share of the characters"""
    out = []
    for (a, b, t), (_, _, _, ci, s_src, e_src) in zip(caps, CAPX):
        w = t.split(); n = 1
        while True:
            # best split of the words into n chunks (balanced by width)
            import itertools
            best = None
            for cut in itertools.combinations(range(1, len(w)), n - 1):
                idx = (0,) + cut + (len(w),); L = [" ".join(w[idx[i]:idx[i+1]]) for i in range(n)]
                if best is None or max(map(tw, L)) < max(map(tw, best)): best = L
            if max(map(tw, best)) <= MAXW1 or n >= len(w): break
            n += 1
        tot = sum(len(x) for x in best); starts = []; acc = 0
        c = CLIPS[ci]; ws = src_words(c["key"], s_src, e_src) if len(best) > 1 else []
        for x in best:
            if acc and len(ws) == len(w):        # word count matches the transcript: use the real word time
                starts.append(min(b - 0.3, max(a + 0.3, ft(src2frame(c["parent"], ws[acc]["s"])))))
            else:
                starts.append(a + (b - a) * sum(len(y) for y in best[:best.index(x)]) / tot)
            acc += len(x.split())
        for i, x in enumerate(best):
            out.append([starts[i], starts[i + 1] if i + 1 < len(best) else b, x])
    return out
MAXW1 = 760          # widest single line (centred) that stays clear of the Reels/TikTok side buttons
def write_subs():
    hdr = open(f"{ROOT}/subtitles/style_template.ass").read().rstrip().replace("WrapStyle: 0", "WrapStyle: 2") + "\n"   # we wrap ourselves
    L = []
    for a, b, t in one_line(caps):
        lines = [t]
        for j, ln in enumerate(lines):
            y = BASE_Y - PITCH * (len(lines) - 1 - j)
            L.append(f"Dialogue: 0,{ts(a)},{ts(b)},Default,,0,0,0,,{{\\an2\\pos(540,{y})}}{ln}")
    open(f"{WORK}/mapc_subs.ass", "w").write(hdr + "\n".join(L) + "\n")
    open(f"{HERE}/subs.srt", "w").write("\n".join(f"{k+1}\n{srt(a)} --> {srt(b)}\n{t}\n" for k, (a, b, t) in enumerate(one_line(caps))))

# ---------------------------------------------------------------- audio
def read_seg(src, a, n_samples):
    out = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{a:.4f}", "-i", src, "-t", f"{n_samples/SR + 0.05:.4f}",
                          "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(out, np.int16).astype(np.float32) / 32768
    x = np.pad(x, (0, max(0, n_samples - len(x))))[:n_samples]
    return x
def build_voice(path):
    parts = []
    for c in CLIPS:
        n = int(round(c["n"] / FPS * SR)); x = read_seg(f"{WORK}/dfn/{c['src']}.wav", c["a"], n)   # DeepFilterNet-cleaned
        fr_ = x[: len(x) // 480 * 480].reshape(-1, 480); r = np.sqrt((fr_ ** 2).mean(1))
        lvl = np.sqrt(np.mean(np.sort(r)[len(r) // 2:] ** 2))          # loudness of the speaking half
        x = x * (0.08 / max(lvl, 1e-4))                                     # level-match the two speakers / takes
        f = int(0.008 * SR); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        parts.append(x)
    v = np.concatenate(parts); v = np.pad(v, (0, int(round(TOTAL * SR)) - len(v)))
    w = wave.open(path, "w"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

# ---------------------------------------------------------------- video
class Reader:
    def __init__(self, src, a, n, w, h, grade=True):
        vf = f"scale={w}:{h}:flags=lanczos" + (",eq=contrast=1.04:saturation=1.07:brightness=0.005" if grade else "")
        self.w, self.h = w, h
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{a:.4f}", "-i", src, "-frames:v", str(n), "-an",
                                   "-vf", vf, "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10**8)
        self.last = None
    def get(self):
        b = self.p.stdout.read(self.w * self.h * 3)
        if len(b) == self.w * self.h * 3: self.last = Image.frombytes("RGB", (self.w, self.h), b)
        return self.last
    def close(self): self.p.stdout.close(); self.p.kill()

def zoom_box(fx, fy, z, sw, sh, ty_override=None):
    """crop box (in source pixels) for zoom z about the face, face pulled toward centre when tight"""
    tx = fx if z <= 1.001 else (fx + 540) / 2; ty = ty_override or (min(fy, 700) if z > 1.001 else fy)
    bw, bh = W / z, H / z
    x0 = min(max(0, fx - tx / z), W - bw); y0 = min(max(0, fy - ty / z), H - bh)
    k = sw / W
    return (x0 * k, y0 * k, (x0 + bw) * k, (y0 + bh) * k)
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def fade(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im
G = {g[0]: Image.open(f"{HERE}/gfx/{g[0]}").convert("RGBA") for g in GFX}
GB = {k: (im, im.getbbox()) for k, im in G.items()}

TB = pstart(P("S", 38.30)); TO, TI = 6, 8     # transition boundary (hook -> intros), frames out / in

def render(out, limit=None):
    write_subs()
    nt = NT if limit is None else min(NT, int(limit * FPS))
    build_voice(f"{WORK}/mapc_voice.wav")
    SND = {"end_bg.png": "card", "end_l1.png": "pop", "end_url.png": "pop", "end_ul.png": "tick", "end_l3.png": "pop"}
    EV = [[ft(g[1]), SND.get(g[0], "lt")] for g in GFX]
    EV += [[ft(c["f0"]), "trans" if c["f0"] == TB else "tr"] for c in CLIPS[1:] if c["settle"]]
    subprocess.run(["python3", f"{HERE}/sfx.py", json.dumps(EV), f"{TOTAL:.3f}", f"{WORK}/mapc_sfx.wav"], check=True)
    q3a = ft(min(c["f0"] for c in CLIPS if c["sec"] == "q3" and c["key"] == "A95")); q3b = ft(max(c["f0"] + c["n"] for c in CLIPS if c["sec"] == "q3"))
    fc = ";".join([
        "[1:a]highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=160:makeup=2,"
        "loudnorm=I=-19.2:TP=-3:LRA=9,aresample=48000,asplit=2[voice][key]",
        # music bed (track 1 of the supplied file), under speech (~13 dB below the voice so every word is clear), a little lower in the story,
        # back up for the end card, then fades with the picture
        f"[2:a]atrim={MUSIC_IN}:{MUSIC_IN + TOTAL + 0.1:.3f},asetpts=PTS-STARTPTS,aresample=48000,"
        f"volume='if(between(t,{q3a:.2f},{q3b:.2f}),0.085,if(gt(t,{ft(NS):.2f}),0.34,0.105))':eval=frame,"
        f"afade=t=in:d=0.6,afade=t=out:st={TOTAL - 1.4:.3f}:d=1.4[mus]",
        "[mus][key]sidechaincompress=threshold=0.05:ratio=2.5:attack=30:release=450[duck]",
        "[3:a]aresample=48000,volume=0.9,pan=stereo|c0=c0|c1=c0[sfx]",
        "[voice]pan=stereo|c0=c0|c1=c0[v2]",
        f"[v2][duck][sfx]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.80,afade=t=out:st={TOTAL - 0.6:.3f}:d=0.6[aout]",
        f"[0:v]subtitles={WORK}/mapc_subs.ass:fontsdir={ROOT}/fonts,fade=t=out:st={TOTAL - 0.6:.3f}:d=0.6,format=yuv420p[vout]",
    ])
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", "30000/1001", "-i", "-", "-i", f"{WORK}/mapc_voice.wav", "-i", f"{FOOT}/music.mp3",
                            "-i", f"{WORK}/mapc_sfx.wav", "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
                            "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-profile:v", "high", "-pix_fmt", "yuv420p",
                            "-r", "30000/1001", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-t", f"{nt / FPS:.4f}", out], stdin=subprocess.PIPE)
    ci = 0; rd = None; br = {}; tail_rd = None; last_base = None; held = None; XF = 3
    for f in range(nt):
        # --- base picture
        if f < NS:
            while f >= CLIPS[ci]["f0"] + CLIPS[ci]["n"]: ci += 1
            c = CLIPS[ci]
            if f == c["f0"]:
                if rd: rd.close()
                rd = Reader(f"{FOOT}/int/{c['src']}.MP4", c["a"], c["n"], DW, DH)
                held = last_base if c["xfade"] else None
            img = rd.get(); lt = (f - c["f0"]) / FPS
            z = c["z"]
            if c["settle"] and ci > 0 and c["f0"] != TB: z *= 1 + 0.045 * (1 - ease(lt / 0.4))
            q = 0.0                                   # zoom-blur transition after the hook
            if TB - TO <= f < TB: q = ((f - (TB - TO) + 1) / TO) ** 2; z *= 1 + 0.22 * q
            elif TB <= f < TB + TI: q = (1 - (f - TB) / TI) ** 2; z *= 1 + 0.16 * q
            fx, fy = FACE[c["key"]]
            frame = img.resize((W, H), Image.BILINEAR, box=zoom_box(fx, fy, z, DW, DH, TY.get(c["key"])))
            if q > 0.02:
                frame = Image.blend(frame, frame.filter(ImageFilter.GaussianBlur(14 * q)), min(1.0, 1.2 * q))
                frame = Image.blend(frame, Image.new("RGB", (W, H), (255, 250, 235)), 0.18 * q)
            k_in = f - c["f0"]                        # pause cut inside an answer: 3-frame soft dissolve, no zoom jump
            if held is not None and k_in < XF: frame = Image.blend(held, frame, (k_in + 1) / (XF + 1))
            last_base = frame
            # --- b-roll
            for k, b in enumerate(BR):
                if b["s"] <= f < b["e"]:
                    if k not in br: br[k] = Reader(f"{FOOT}/broll/{b['f']}.MP4", b["si"], b["e"] - b["s"] + 2, W, H)
                    bi = br[k].get(); p = (f - b["s"]) / max(1, b["e"] - b["s"])
                    bz = 1.0 + 0.05 * p                                    # gentle push so stills never look frozen
                    bw, bh = W / bz, H / bz
                    bi = bi.resize((W, H), Image.BILINEAR, box=((W - bw) / 2, (H - bh) / 2, (W + bw) / 2, (H + bh) / 2))
                    a = 1.0
                    if not b["hard_in"]: a = min(a, (f - b["s"] + 1) / 6)
                    if not b["hard_out"]: a = min(a, (b["e"] - f) / 6)
                    frame = Image.blend(frame, bi, a) if a < 1 else bi
                elif f >= b["e"] and k in br: br.pop(k).close()
        else:
            # --- end card background: group photo, sharp for a beat, then softly blurred and dimmed under the card
            if tail_rd is None:
                if rd: rd.close()
                tail_rd = Reader(f"{FOOT}/broll/DJI_20261114110325_0186_D.MP4", 4.0, NT - NS + 2, W, H)   # pan starts at 4.0 s
            bi = tail_rd.get(); lt = (f - NS) / FPS; p = ease((lt - 0.3) / 0.6)
            small = bi.resize((270, 480), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
            frame = Image.blend(bi, small, p)
            frame = Image.blend(frame, Image.new("RGB", (W, H), (8, 20, 40)), 0.4 * p)
        frame = frame.convert("RGBA")
        # --- graphics
        for name, s, e, mv in GFX:
            if s <= f < e:
                im, bb = GB[name]; lt = (f - s) / FPS
                a = min(ease(lt / 0.3), 1.0) * (1 if e >= NT else min(1.0, (e - f) / FPS / 0.22))
                d = (1 - ease(lt / 0.35))
                crop = im.crop(bb)
                if mv in ("card", "popc"):           # end card / URL: scale up about the centre (URL with a light overshoot)
                    x = min(1.0, lt / 0.32)
                    sc = (0.92 + 0.08 * ease(x)) if mv == "card" else (0.8 + 0.2 * (1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2))
                    if abs(sc - 1) > 0.001: crop = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))), Image.BILINEAR)
                    frame.alpha_composite(fade(crop, a), (int((bb[0] + bb[2]) / 2 - crop.width / 2), int((bb[1] + bb[3]) / 2 - crop.height / 2)))
                elif mv == "wipe":                   # underline draws from left to right
                    w = int(crop.width * ease(lt / 0.35))
                    if w > 0: frame.alpha_composite(crop.crop((0, 0, w, crop.height)), (bb[0], bb[1]))
                elif mv == "rise":
                    frame.alpha_composite(fade(crop, min(1.0, lt / 0.25)), (bb[0], int(bb[1] + 22 * (1 - ease(lt / 0.3)))))
                elif mv == "pop":                      # question bubble: small scale-up from its tail
                    sc = 0.86 + 0.14 * ease(lt / 0.3)
                    if sc < 0.999: crop = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))), Image.BILINEAR)
                    frame.alpha_composite(fade(crop, a), (int((bb[0] + bb[2]) / 2 - crop.width / 2), int(bb[3] - crop.height)))
                else:
                    dx, dy = {"down": (0, -24 * d), "up": (0, 30 * d), "right": (-40 * d, 0)}[mv]
                    frame.alpha_composite(fade(crop, a), (int(bb[0] + dx), int(bb[1] + dy)))
        enc.stdin.write(frame.convert("RGB").tobytes())
        if f % 300 == 0: print(f"{f/FPS:6.1f}s / {nt/FPS:.1f}s", flush=True)
    enc.stdin.close(); enc.wait()
    print("TOTAL", round(TOTAL, 2), "s")

if __name__ == "__main__":
    lim = float(sys.argv[sys.argv.index("--preview") + 1]) if "--preview" in sys.argv else None
    render(sys.argv[1], lim)
