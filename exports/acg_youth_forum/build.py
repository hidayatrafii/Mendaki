#!/usr/bin/env python3
"""ACG Youth Forum 2026 speech edit (v2): hook -> event intro -> speech -> end card."""
import json, os, subprocess, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import grade
from PIL import ImageFont

W, H, FPS = 1080, 1920, 30000 / 1001
ROOT = '/home/user/Mendaki'
WORK = f'{ROOT}/work'
SPEECH = f'{ROOT}/footage/speech/DJI_20261117114504_0103_D.MP4'
PROXY = f'{WORK}/proxy'
SCR = '/tmp/claude-0/-home-user-Mendaki/15c5929f-e368-5422-82b3-d6e7773bfd06/scratchpad'
FONTDIR = f'{SCR}/fonts'
LOGO = f'{SCR}/logo.png'
MUSIC = '/root/.claude/uploads/15c5929f-e368-5422-82b3-d6e7773bfd06/8d509ce4-Upbeat_Exciting_Background_Music_For_Videos.mp3'
OUT = f'{ROOT}/exports/ACG_Youth_Forum_2026_Speech.mp4'
PIECES = f'{WORK}/pieces'
os.makedirs(PIECES, exist_ok=True)

END_LEN = 2.2

# ---- speech selections: (src_in, src_out, caption text, section)
HOOK = []
BODY = [
    (27.55, 34.95, "Every day, artificial intelligence and algorithms help decide what appears and displays on our screens.", 'ai'),
    (42.80, 49.85, "But they must never decide what we believe in, who we trust, or how we treat another person.", 'ai'),
    (283.85, 292.30, "In the past year alone, six out of eight new cases dealt with the Internal Security Act, or ISA, involved youth", 'stat'),
    (292.72, 294.45, "aged 20 and below.", 'stat'),
    (339.55, 345.58, "These figures are serious, but I do not want us to see young people as being vulnerable", 'youth'),
    (349.42, 350.75, "to online extremism.", 'youth'),
    (351.30, 355.40, "I believe we can also be among our strongest defences against it.", 'youth'),
    (436.53, 441.95, "Let me share three simple actions. Recognise, reflect, and respond.", 'actions'),
    (442.85, 445.20, "First, recognise manipulation and warning signs.", 'actions'),
    (445.85, 456.50, "When you encounter content that makes you angry or fearful, ask yourself, who created this? Why am I seeing it? Who benefits if I share this?", 'actions'),
    (480.85, 483.60, "Second, reflect before reacting.", 'actions'),
    (492.25, 496.00, "Do not outsource your judgement to the machine.", 'actions'),
    (514.80, 517.50, "Third, respond with care.", 'respond'),
    (550.50, 552.90, "Speaking up is not betraying a friend.", 'respond'),
    (584.72, 591.95, "I'm only asking you to look out for one another and to help someone get support early.", 'respond'),
    (657.85, 661.60, "To every young person who feels isolated or unheard,", 'belong'),
    (662.60, 664.40, "our message must be clear.", 'belong'),
    (665.02, 666.10, "You matter.", 'belong'),
    (666.80, 668.12, "You belong here.", 'belong'),
    (668.75, 673.30, "And there are people out there who care enough to help.", 'belong'),
    (726.35, 734.55, "So take control of your feed, look out for your friends, and never underestimate the impact you can make on someone's life.", 'close'),
    (735.30, 738.45, "So recognise, reflect, respond.", 'close'),
    (739.45, 744.50, "Together we can keep Singapore safe, cohesive, and full of hope.", 'close'),
]
# a-roll ranges where the camera moves: always covered with b-roll
FORCE_BROLL_SRC = [(42.80, 49.85)]

# b-roll pool per section: (clip, source in-point)
POOL = {
    'ai':      [('DJI_20261117103321_0067_D', 1.0), ('DJI_20261117103613_0070_D', 2.0), ('DJI_20261117105416_0084_D', 2.5), ('IMG_0565', 6.0)],
    'stat':    [('IMG_0569', 9.5), ('DJI_20261117103206_0063_D', 3.0), ('DJI_20261117103243_0065_D', 2.0)],
    'youth':   [('DJI_20261117103226_0064_D', 4.5), ('DJI_20261117103151_0062_D', 2.5), ('IMG_0566', 0.3)],
    'actions': [('DJI_20261117104328_0071_D', 2.0), ('DJI_20261117103300_0066_D', 1.0), ('DJI_20261117114451_0102_D', 3.0), ('DJI_20261117115911_0104_D', 1.6),
                ('DJI_20261117120054_0108_D', 0.5), ('DJI_20261117115923_0105_D', 4.0), ('DJI_20261117104719_0082_D', 1.0)],
    'respond': [('DJI_20261117103331_0068_D', 0.5), ('DJI_20261117115954_0106_D', 1.0), ('DJI_20261117103206_0063_D', 0.2)],
    'belong':  [('DJI_20261117112817_0087_D', 5.5), ('DJI_20261117103331_0068_D', 6.5), ('DJI_20261117104328_0071_D', 5.5), ('IMG_0571', 4.5), ('DJI_20261117103243_0065_D', 4.0)],
    'close':   [('DJI_20261117130115_0111_D', 3.6), ('DJI_20261117130127_0112_D', 3.0), ('DJI_20261117125954_0109_D', 3.5), ('DJI_20261117130030_0110_D', 4.0)],
}
# intro: logo over two clean wide shots (no faces behind it), then engagement montage
LOGO_SHOTS = [('IMG_0570', 0.2, 1.3), ('DJI_20261117114451_0102_D', 6.5, 1.3)]
MONTAGE = [
    ('DJI_20261117103151_0062_D', 0.5, 0.9),   # teams at tables, challenge in progress
    ('DJI_20261117103243_0065_D', 1.0, 0.9),   # team presenting their work
    ('DJI_20261117103331_0068_D', 4.5, 0.9),   # team huddle, laughing
    ('DJI_20261117105416_0084_D', 1.0, 0.9),   # participants on their phones
    ('DJI_20261117112817_0087_D', 1.2, 1.0),   # Zaqy shakes hands with youths at their table
    ('DJI_20261117103226_0064_D', 2.5, 0.9),   # youths presenting
    ('DJI_20261117115911_0104_D', 0.4, 0.9),   # youth asks a question on the mic
    ('DJI_20261117130115_0111_D', 2.5, 0.9),   # Zaqy presents a prize to a team
    ('DJI_20261117130127_0112_D', 10.8, 1.0),  # team photo with Zaqy
]
INTRO_SHOTS = LOGO_SHOTS + MONTAGE
LOGO_SEG = sum(d for *_, d in LOGO_SHOTS)
INTRO_LEN = sum(d for *_, d in INTRO_SHOTS)
END_SHOT = ('DJI_20261117130127_0112_D', 8.0)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(cmd)); print(r.stderr[-3000:]); sys.exit(1)
    return r


def dur_of(p):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).stdout)


# ---------------- output timeline ----------------
segs = []
t = 0.0
for a, b, txt, sec in HOOK:
    segs.append(dict(a=a, b=b, o=t, text=txt, sec=sec)); t += b - a
HOOK_END = t
INTRO_START, INTRO_END = t, t + INTRO_LEN
t = INTRO_END
BODY_START = t
for a, b, txt, sec in BODY:
    segs.append(dict(a=a, b=b, o=t, text=txt, sec=sec)); t += b - a
BODY_END = t
TOTAL = BODY_END + END_LEN
print(f'hook {HOOK_END:.2f}s, intro {INTRO_LEN:.1f}s, body {BODY_START:.2f}-{BODY_END:.2f}, total {TOTAL:.2f}s')


def src2out(ts):
    for s in segs:
        if s['a'] - 0.05 <= ts <= s['b'] + 0.05:
            return s['o'] + min(max(ts - s['a'], 0), s['b'] - s['a'])
    return None


def seg_end(s):
    return s['o'] + s['b'] - s['a']


def sec_at(o):
    for s in segs:
        if s['o'] <= o < seg_end(s):
            return s['sec']
    return segs[-1]['sec']


# ---------------- b-roll windows ----------------
wins = []
for i in range(1, len(segs)):
    o = segs[i]['o']
    if abs(o - INTRO_END) < 1e-6:
        continue
    a, b = o - 1.3, o + 1.7
    a = max(a, BODY_START + 5.6) if o > BODY_START else max(a, 1.2)
    wins.append([a, b])
for a, b in FORCE_BROLL_SRC:
    wins.append([src2out(a) - 0.3, src2out(b) + 0.3])
wins = sorted(w for w in wins if w[1] > w[0])
merged = []
for w in wins:
    if merged and w[0] - merged[-1][1] < 1.6:
        merged[-1][1] = max(merged[-1][1], w[1])
    else:
        merged.append(list(w))
for w in merged:
    lim = BODY_END - 1.5 if w[0] > BODY_START else HOOK_END
    w[1] = lim if lim - w[1] < 1.0 else min(w[1], lim)

pool_idx = {k: 0 for k in POOL}
broll_windows = []
for w in merged:
    sec = sec_at((w[0] + w[1]) / 2)
    n = max(1, math.ceil((w[1] - w[0]) / 3.2))
    step = (w[1] - w[0]) / n
    for k in range(n):
        clip, cin = POOL[sec][pool_idx[sec] % len(POOL[sec])]; pool_idx[sec] += 1
        broll_windows.append((w[0] + k * step, w[0] + (k + 1) * step, clip, cin))

timeline = []


def add_aroll(o0, o1):
    pts = [o0] + [s['o'] for s in segs if o0 < s['o'] < o1] + [o1]
    for x, y in zip(pts, pts[1:]):
        if y - x > 0.02:
            timeline.append((x, y, 'aroll', None))


def fill(o0, o1):
    c = o0
    for (x, y, clip, cin) in broll_windows:
        if y <= o0 or x >= o1:
            continue
        x, y = max(x, o0), min(y, o1)
        if x > c:
            add_aroll(c, x)
        timeline.append((x, y, 'broll', (clip, cin)))
        c = y
    if o1 > c:
        add_aroll(c, o1)


fill(0, HOOK_END)
c = INTRO_START
for clip, cin, d in INTRO_SHOTS:
    timeline.append((c, c + d, 'broll', (clip, cin))); c += d
fill(BODY_START, BODY_END)
timeline.append((BODY_END, TOTAL, 'end', END_SHOT))


# ---------------- render pieces ----------------
def frames(x):
    return round(x * FPS)


aroll_alt = 0
for i, (o0, o1, kind, p) in enumerate(timeline):
    nf = frames(o1) - frames(o0)
    path = f'{PIECES}/p{i:03d}.mp4'
    if kind == 'aroll':
        s = next(s for s in segs if s['o'] - 1e-6 <= o0 < seg_end(s) - 1e-6)
        src = s['a'] + (o0 - s['o'])
        if s['sec'] == 'hook':
            vf = (f"scale=1728:3072,zoompan=z='1.0+0.0004*(on+{frames(o0)})':x='iw*0.36-iw/zoom*0.36':y='ih*0.45-ih/zoom*0.45':d=1:s={W}x{H}:fps=30000/1001")
        else:
            tight = (aroll_alt % 2 == 1); aroll_alt += 1
            vf = ("crop=1300:2311:0:330,scale=1080:1920" if tight else f"scale={W}:{H}")
        vf += ',' + grade('SPEECH')
        inp = SPEECH
    else:
        clip, src = p
        inp = f'{PROXY}/{clip}.mp4'
        vf = grade(clip)
        if kind == 'end':
            vf += ',gblur=sigma=28,eq=brightness=-0.08:saturation=0.8'
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{src:.3f}', '-i', inp, '-frames:v', str(nf),
           '-vf', vf + ',setsar=1,format=yuv420p', '-r', '30000/1001', '-an',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', path]
    if not os.path.exists(path) or '--force' in sys.argv:
        run(cmd)
    got = int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', path]).stdout)
    if got < nf:
        run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vf', f'tpad=stop_mode=clone:stop={nf-got}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', path + '.tmp.mp4'])
        os.replace(path + '.tmp.mp4', path)
    print(f'{i:3d} {o0:7.2f}-{o1:7.2f} {kind:5s} {p if p else ""}')

with open(f'{WORK}/concat.txt', 'w') as f:
    for i in range(len(timeline)):
        f.write(f"file '{PIECES}/p{i:03d}.mp4'\n")
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{WORK}/concat.txt', '-c', 'copy', f'{WORK}/video_nogfx.mp4'])

# ---------------- speech audio ----------------
parts = []
for k, s in enumerate(segs):
    p = f'{WORK}/a{k:02d}.wav'
    d = s['b'] - s['a']
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['a']:.3f}", '-t', f'{d:.3f}', '-i', SPEECH, '-vn', '-ac', '1', '-ar', '48000',
         '-af', f'afade=t=in:d=0.015,afade=t=out:st={d-0.025:.3f}:d=0.025', p])
    parts.append((s['o'], p))
inputs, flt = [], []
for k, (o, p) in enumerate(parts):
    inputs += ['-i', p]
    flt.append(f'[{k}]adelay={int(round(o*1000))}|{int(round(o*1000))}[d{k}]')
flt.append(''.join(f'[d{k}]' for k in range(len(parts))) + f'amix=inputs={len(parts)}:normalize=0,apad=whole_dur={TOTAL:.3f}[raw]')
# AI enhancement (Resemble Enhance) removes room echo/noise and restores close-mic tone;
# afterwards only a light "lav mic" finish: gentle EQ, de-ess, compression, loudness.
enh = ('highpass=f=80,'
       'equalizer=f=200:t=q:w=1.0:g=-1.5,equalizer=f=3000:t=q:w=1.5:g=1.5,'
       'deesser=i=0.25,'
       'acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150:makeup=2,'
       'loudnorm=I=-15:TP=-2:LRA=7')
run(['python3', f'{WORK}/declick.py', f'{WORK}/speech_raw.wav', f'{WORK}/speech_dc.wav'])
import hashlib
_h = hashlib.md5(open(f'{WORK}/speech_dc.wav', 'rb').read()).hexdigest()[:10]
_ai = f'{WORK}/speech_ai_{_h}.wav'
if not os.path.exists(_ai):
    env = dict(os.environ, PYTHONPATH=f'{WORK}/stubs', HF_HUB_DISABLE_XET='1')
    r = subprocess.run(['python3', f'{WORK}/enhance.py', f'{WORK}/speech_dc.wav', _ai], capture_output=True, text=True, env=env)
    if r.returncode:
        print(r.stderr[-2000:]); sys.exit(1)
run(['ffmpeg', '-v', 'error', '-y', '-i', _ai, '-af', enh, '-ar', '48000', f'{WORK}/speech_enh.wav'])


# ---------------- music bed ----------------
def vol_expr():
    lo, hi, r = 0.13, 0.85, 0.35

    def ramp(a, b):
        return f"clip(min((t-({a}-{r}))/{r},(({b}+{r})-t)/{r}),0,1)"
    return f"{lo}+({hi}-{lo})*max({ramp(INTRO_START+0.25, INTRO_END-0.35)},{ramp(BODY_END+0.2, TOTAL+5)})"


run(['ffmpeg', '-v', 'error', '-y', '-i', MUSIC, '-t', f'{TOTAL:.3f}',
     '-af', f"loudnorm=I=-16:TP=-2,volume='{vol_expr()}':eval=frame,afade=t=in:d=0.6,afade=t=out:st={TOTAL-1.6:.3f}:d=1.6",
     '-ar', '48000', '-ac', '2', f'{WORK}/music_bed.wav'])

# ---------------- captions ----------------
T = json.load(open(f'{WORK}/transcript.json'))
WORDS = [w for s in T for w in s['words']]

SUB_SIZE = 76
SUB_FONT = ImageFont.truetype(f'{FONTDIR}/Poppins-700.ttf', 100)
PX_PER_PIL100 = 0.563 * SUB_SIZE / 100   # libass Poppins Bold calibration
MAXW = 780
SUB_BASE = 1400      # baseline of the bottom line (fixed for every caption)
LINE_STEP = 66       # tighter than libass default line spacing


def width(txt):
    return SUB_FONT.getlength(txt) * PX_PER_PIL100


def wrap2(words):
    """Return text with at most one \\N, balanced; None if it can't fit in 2 lines."""
    txt = ' '.join(words)
    if width(txt) <= MAXW:
        return txt
    best = None
    for k in range(1, len(words)):
        a, b = ' '.join(words[:k]), ' '.join(words[k:])
        wa, wb = width(a), width(b)
        if wa <= MAXW and wb <= MAXW:
            score = max(wa, wb) - (60 if words[k-1][-1] in ',;' else 0) + (200 if words[k-1].lower().strip(',') in WEAK | {'look', 'decide', 'see'} else 0)
            if best is None or score < best[0]:
                best = (score, a + r'\N' + b)
    return best[1] if best else None


WEAK = {'the', 'a', 'an', 'to', 'of', 'and', 'or', 'in', 'on', 'for', 'with', 'we', 'i', 'you', 'our', 'your', 'be',
        'is', 'as', 'that', 'what', 'who', 'being', 'get', 'can', 'must', 'not', 'how', 'my', 'their', 'this', 'it', "i'm"}
STARTERS = {'and', 'but', 'or', 'so', 'who', 'because', 'while', 'until', 'when', 'to'}


def break_cost(ws, k):
    """Cost of ending a caption after ws[k-1] (k < len(ws))."""
    last, nxt = ws[k-1]['w'], ws[k]['w']
    if last[-1] in ',;:':
        return 0
    c = 60
    if nxt.lower() in STARTERS:
        c = 20
    if last.lower().strip(',') in WEAK:
        c += 120
    if last[0].isupper() and nxt[0].isupper():
        c += 200
    return c


def split_sentence(ws):
    """Fewest/cleanest captions of <= 2 lines via DP over break points."""
    n = len(ws)
    INF = float('inf')
    best = [INF] * (n + 1); prev = [0] * (n + 1); best[0] = 0
    for j in range(1, n + 1):
        for i in range(j):
            if best[i] == INF:
                continue
            if not wrap2([w['w'] for w in ws[i:j]]):
                continue
            c = best[i] + 100 + (80 if j - i <= 2 and n > 2 else 0) + (break_cost(ws, j) if j < n else 0)
            if c < best[j]:
                best[j] = c; prev[j] = i
    out, j = [], n
    while j > 0:
        out.append(ws[prev[j]:j]); j = prev[j]
    return out[::-1]


# word-level timeline in output time
wl = []
for s in segs:
    sw = [w for w in WORDS if s['a'] - 0.05 <= w['s'] <= s['b'] - 0.05]
    cw = s['text'].split()
    for i, w in enumerate(cw):
        if sw:
            j = min(int(i * len(sw) / len(cw)), len(sw) - 1)
            st = src2out(min(max(sw[j]['s'], s['a']), s['b']))
            jn = min(int((i + 1) * len(sw) / len(cw)) - 1, len(sw) - 1)
            en = src2out(min(max(sw[max(jn, j)]['e'], s['a']), s['b']))
        else:
            st = s['o'] + (s['b'] - s['a']) * i / len(cw)
            en = s['o'] + (s['b'] - s['a']) * (i + 1) / len(cw)
        wl.append(dict(w=w, s=st, e=max(en, st + 0.1)))

sentences, cur = [], []
for w in wl:
    cur.append(w)
    if w['w'][-1] in '.?!':
        sentences.append(cur); cur = []
if cur:
    sentences.append(cur)

caps = []
for sn in sentences:
    for ch in split_sentence(sn):
        caps.append(dict(s=ch[0]['s'], e=ch[-1]['e'], text=wrap2([w['w'] for w in ch])))
def fq(x):  # snap to frame boundary
    return round(x * FPS) / FPS
for cp in caps:
    cp['s'] = fq(max(cp['s'] - 0.05, 0))
for k, cp in enumerate(caps):
    nxt = caps[k + 1]['s'] if k + 1 < len(caps) else TOTAL
    e = max(cp['e'] + 0.3, cp['s'] + 0.6)
    cp['e'] = nxt if (nxt - e) < 0.35 else fq(e)   # close small gaps: no blink between captions
    cp['e'] = min(cp['e'], nxt)


def ass_t(x):
    cs = int(round(max(x, 0) * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); sec, cs = divmod(cs, 100)
    return f'{h}:{m:02d}:{sec:02d}.{cs:02d}'


events = []
for cp in caps:
    lines = cp['text'].split(r'\N')
    for li, ln in enumerate(lines):
        y = SUB_BASE - LINE_STEP * (len(lines) - 1 - li)
        events.append(('Sub', cp['s'], cp['e'], rf'{{\an2\pos(540,{y})\blur1.2}}' + ln))
        events.append(('SubGlow', cp['s'], cp['e'], rf'{{\an2\pos(540,{y})\blur14\1a&HFF&\3c&H000000&\3a&H90&\bord10}}' + ln))


def find_word(word, after, before=None):
    for w in WORDS:
        if w['s'] >= after and (before is None or w['s'] <= before) and word.lower() in w['w'].lower():
            return w['s']
    raise KeyError(word)


gfx = []
# --- hook stat card
st6 = src2out(find_word('six', 284, 286))
stat_end = seg_end(next(x for x in segs if abs(x['a'] - 292.72) < 1e-3)) - 0.05
card = (r'{\an7\pos(140,100)\bord0\shad0\1c&HFFFFFF&\1a&H08&\p1}'
        r'm 30 0 l 770 0 b 800 0 800 0 800 30 l 800 300 b 800 330 800 330 770 330 l 30 330 b 0 330 0 330 0 300 l 0 30 b 0 0 0 0 30 0{\p0}')
gfx.append(('Card', st6 - 0.1, stat_end, r'{\fad(200,150)}' + card))
gfx.append(('Stat', st6, stat_end, r'{\an5\pos(540,205)\fad(200,150)\fscx85\fscy85\t(0,250,\fscx100\fscy100)}6 OUT OF 8'))
gfx.append(('StatSub', st6 + 0.35, stat_end, r'{\an5\pos(540,350)\fad(250,150)}new ISA cases involved youths' + r'\N' + 'aged 20 and below'))

# --- lower third (minister): sits above the subtitles
lt0, lt1 = BODY_START + 0.4, BODY_START + 5.4
LY = 980
box1 = rf'{{\an7\pos(60,{LY})\bord0\shad0\1c&H3D2114&\p1}}m 0 0 l 640 0 l 640 104 l 0 104{{\p0}}'
box2 = rf'{{\an7\pos(60,{LY+104})\bord0\shad0\1c&HE0904A&\p1}}m 0 0 l 860 0 l 860 132 l 0 132{{\p0}}'
gfx.append(('Box', lt0, lt1, rf'{{\fad(200,200)\clip(60,{LY},60,{LY+104})\t(0,300,\clip(60,{LY},700,{LY+104}))}}' + box1))
gfx.append(('Box', lt0 + 0.15, lt1, rf'{{\fad(200,200)\clip(60,{LY+104},60,{LY+236})\t(0,300,\clip(60,{LY+104},920,{LY+236}))}}' + box2))
gfx.append(('LTName', lt0 + 0.25, lt1, rf'{{\an4\pos(90,{LY+53})\fad(250,200)}}Mr Zaqy Mohamad'))
gfx.append(('LTTitle', lt0 + 0.35, lt1, rf'{{\an4\pos(90,{LY+170})\fad(250,200)}}Acting Minister-in-charge of Muslim Affairs &\NSenior Minister of State for Defence'))


# --- three actions chips
def chip(label, num, t0, t1, y=200):
    w = 42 * len(label) + 210
    x0 = 540 - w // 2
    shape = (rf'{{\an7\pos({x0},{y})\bord0\shad0\1c&HE0904A&\p1}}'
             rf'm 52 0 l {w-52} 0 b {w} 0 {w} 104 {w-52} 104 l 52 104 b 0 104 0 0 52 0{{\p0}}')
    gfx.append(('Chip', t0, t1, r'{\fad(180,180)}' + shape))
    gfx.append(('ChipText', t0, t1, rf'{{\an5\pos(540,{y+53})\fad(180,180)}}{{\1c&HA4DCEC&}}{num}  {{\1c&HFFFFFF&}}{label}'))


def seg_span(a):
    s = next(s for s in segs if abs(s['a'] - a) < 1e-3)
    return s['o'], seg_end(s)


r1 = src2out(find_word('Recognize', 439, 440)); r2 = src2out(find_word('reflect', 440, 441)); r3 = src2out(find_word('respond', 441, 442))
s7_end = seg_span(436.53)[1]
chip('RECOGNISE', '01', r1, s7_end, 180)
chip('REFLECT', '02', r2, s7_end, 300)
chip('RESPOND', '03', r3, s7_end, 420)
chip('RECOGNISE', '01', seg_span(442.85)[0] + 0.1, seg_span(445.85)[1] - 0.1)
chip('REFLECT', '02', seg_span(480.85)[0] + 0.1, seg_span(492.25)[1] - 0.1)
chip('RESPOND', '03', seg_span(514.80)[0] + 0.1, seg_span(584.72)[1] - 0.1)

gfx.append(('EndTag', BODY_END + 0.5, TOTAL, r'{\an5\pos(540,1200)\fad(300,0)\fsp4}RECOGNISE  ·  REFLECT  ·  RESPOND'))

CREAM = '&H00A4DCEC'
header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Poppins,{SUB_SIZE},{CREAM},&H000000FF,&H00000000,&H40000000,1,0,0,0,100,100,0,0,1,0,3,2,40,40,500,1
Style: SubGlow,Poppins,{SUB_SIZE},&HFF000000,&H000000FF,&H00000000,&HFF000000,1,0,0,0,100,100,0,0,1,0,0,2,40,40,500,1
Style: Card,Poppins,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Stat,Poppins ExtraBold,170,&H003D2114,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: StatSub,Poppins Medium,50,&H003D2114,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Box,Poppins,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: LTName,Poppins,76,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1
Style: LTTitle,Poppins Medium,44,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1
Style: Chip,Poppins,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: ChipText,Poppins SemiBold,56,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,0,0,0,1
Style: EndTag,Poppins SemiBold,50,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,0,2,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
layer = {'Card': 1, 'Box': 1, 'Chip': 1, 'SubGlow': 1}
with open(f'{WORK}/gfx.ass', 'w') as f:
    f.write(header)
    for st, a, b, txt in events + gfx:
        f.write(f"Dialogue: {layer.get(st, 2)},{ass_t(a)},{ass_t(b)},{st},,0,0,0,,{txt}\n")
with open(f'{WORK}/captions.txt', 'w') as f:
    for cp in caps:
        f.write(f"{cp['s']:7.2f}-{cp['e']:7.2f}  {cp['text'].replace(chr(92)+'N', ' / ')}\n")

# ---------------- final composite ----------------
LOGO_W = 920
li, lo = INTRO_START + 0.2, INTRO_START + LOGO_SEG - 0.05
ei = BODY_END + 0.15
fc = (
    f"[0:v]eq=brightness=-0.10:contrast=0.95:enable='between(t,{INTRO_START:.3f},{INTRO_START+LOGO_SEG:.3f})'[v0];"
    f"[2:v]format=rgba,split[lg1][lg2];"
    f"[lg1]scale=w='{LOGO_W}*(0.9+0.1*min(1,max(0,(t-{li:.3f})/0.45)))':h=-1:eval=frame,"
    f"fade=t=in:st={li:.3f}:d=0.3:alpha=1,fade=t=out:st={lo-0.25:.3f}:d=0.25:alpha=1[l1];"
    f"[lg2]scale=w='{int(LOGO_W*0.85)}*(0.9+0.1*min(1,max(0,(t-{ei:.3f})/0.45)))':h=-1:eval=frame,"
    f"fade=t=in:st={ei:.3f}:d=0.35:alpha=1[l2];"
    f"[v0][l1]overlay=x='(W-w)/2':y='560-h/2':enable='between(t,{li:.3f},{lo:.3f})':eval=frame[v1];"
    f"[v1][l2]overlay=x='(W-w)/2':y='860-h/2':enable='gte(t,{ei:.3f})':eval=frame[v2];"
    f"[v2]ass={WORK}/gfx.ass:fontsdir={FONTDIR}[v];"
    f"[1:a][3:a]amix=inputs=2:normalize=0,volume=2.3dB,alimiter=limit=0.82:level=false[a]"
)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
run(['ffmpeg', '-v', 'error', '-y', '-i', f'{WORK}/video_nogfx.mp4', '-i', f'{WORK}/speech_enh.wav',
     '-loop', '1', '-framerate', '30000/1001', '-t', f'{TOTAL:.3f}', '-i', LOGO, '-i', f'{WORK}/music_bed.wav',
     '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-t', f'{TOTAL:.3f}',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '6M', '-bufsize', '12M', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
     '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT])
print('done', OUT, dur_of(OUT))
