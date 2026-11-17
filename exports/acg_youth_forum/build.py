#!/usr/bin/env python3
"""ACG Youth Forum 2026 speech edit: hook -> event intro -> speech -> end card."""
import json, os, subprocess, sys, math

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

INTRO_LEN = 7.0
END_LEN = 3.0

# ---- speech selections: (src_in, src_out, caption text, section)
HOOK = [
    (283.85, 292.30, "In the past year alone, six out of eight new cases dealt with the Internal Security Act, or ISA, involved youth", 'hook'),
    (292.72, 294.45, "aged 20 and below.", 'hook'),
]
BODY = [
    (27.55, 34.95, "Every day, artificial intelligence and algorithms help decide what appears and displays on our screens.", 'ai'),
    (42.80, 49.85, "But they must never decide what we believe in, who we trust, or how we treat another person.", 'ai'),
    (50.85, 54.35, "That responsibility ultimately rests on us.", 'ai'),
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

# b-roll pool per section: (clip, source in-point)
POOL = {
    'hook':    [('IMG_0569', 1.0)],
    'ai':      [('DJI_20261117114338_0101_D', 0.5), ('IMG_0571', 1.0), ('IMG_0566', 0.3)],
    'youth':   [('DJI_20261117115911_0104_D', 0.3), ('IMG_0565', 2.0), ('IMG_0569', 9.5)],
    'actions': [('DJI_20261117114451_0102_D', 4.5), ('IMG_0567', 0.4), ('IMG_0568', 1.0), ('DJI_20261117120031_0107_D', 0.5), ('IMG_0570', 0.2), ('IMG_0569', 6.0), ('IMG_0568', 5.0)],
    'respond': [('DJI_20261117115954_0106_D', 5.0), ('DJI_20261117120054_0108_D', 0.5), ('IMG_0571', 4.5)],
    'belong':  [('DJI_20261117115923_0105_D', 1.0), ('IMG_0566', 3.5), ('IMG_0646', 2.0), ('IMG_0565', 9.0), ('IMG_0650', 3.0)],
    'close':   [('DJI_20261117130115_0111_D', 2.0), ('DJI_20261117130127_0112_D', 3.0), ('DJI_20261117125954_0109_D', 3.5)],
}
INTRO_SHOTS = [('IMG_0570', 0.2, 1.7), ('IMG_0565', 4.0, 1.7), ('IMG_0647', 1.5, 1.8), ('DJI_20261117130030_0110_D', 1.6, 1.8)]
END_SHOT = ('DJI_20261117130127_0112_D', 8.0)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(cmd)); print(r.stderr[-3000:]); sys.exit(1)
    return r


def dur_of(p):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).stdout)


# ---------------- output timeline ----------------
segs = []  # dict(src_in, src_out, out_in, text, section)
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
print(f'hook {HOOK_END:.2f}s, body {BODY_START:.2f}-{BODY_END:.2f}, total {TOTAL:.2f}s')


def src2out(ts):
    for s in segs:
        if s['a'] - 0.05 <= ts <= s['b'] + 0.05:
            return s['o'] + min(max(ts - s['a'], 0), s['b'] - s['a'])
    return None


# ---------------- b-roll windows over splices ----------------
def sec_at(o):
    for s in segs:
        if s['o'] <= o < s['o'] + s['b'] - s['a']:
            return s['sec']
    return segs[-1]['sec']

splices = []
for i in range(1, len(segs)):
    o = segs[i]['o']
    if abs(o - INTRO_END) < 1e-6 or i == 0:
        continue
    splices.append(o)
wins = []
for o in splices:
    a, b = o - 1.3, o + 1.7
    wins.append([max(a, BODY_START + 4.2) if o > BODY_START else max(a, 1.2), b])
# hook splice
wins = [w for w in wins if w[1] > w[0]]
wins.sort()
merged = []
for w in wins:
    if merged and w[0] - merged[-1][1] < 1.6:   # keep a-roll stretches >= 1.6s
        merged[-1][1] = max(merged[-1][1], w[1])
    else:
        merged.append(list(w))
# never run into the end card
for w in merged:
    lim = BODY_END - 1.5 if w[0] > BODY_START else HOOK_END
    w[1] = lim if lim - w[1] < 1.0 else min(w[1], lim)

pool_idx = {k: 0 for k in POOL}
timeline = []  # (out_in, out_out, kind, params)
cursor = 0.0
def add_aroll(o0, o1):
    # split at splice points so a-roll never spans a jump un-covered
    pts = [o0] + [s['o'] for s in segs if o0 < s['o'] < o1] + [o1]
    for x, y in zip(pts, pts[1:]):
        if y - x > 0.02:
            timeline.append((x, y, 'aroll', None))

broll_windows = []
for w in merged:
    sec = sec_at((w[0] + w[1]) / 2)
    # chop long windows into <= 3.4s shots
    n = max(1, math.ceil((w[1] - w[0]) / 3.4))
    step = (w[1] - w[0]) / n
    for k in range(n):
        clip, cin = POOL[sec][pool_idx[sec] % len(POOL[sec])]; pool_idx[sec] += 1
        broll_windows.append((w[0] + k * step, w[0] + (k + 1) * step, clip, cin))

# assemble hook + body a-roll/b-roll
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
assert abs(c - INTRO_END) < 1e-6, c
fill(BODY_START, BODY_END)
timeline.append((BODY_END, TOTAL, 'end', END_SHOT))

# ---------------- render pieces ----------------
def frames(x):
    return round(x * FPS)

# frame-accurate durations: compute in frames from cumulative boundaries
render = []
for i, (o0, o1, kind, p) in enumerate(timeline):
    nf = frames(o1) - frames(o0)
    render.append((i, o0, o1, nf, kind, p))

aroll_alt = 0
for i, o0, o1, nf, kind, p in render:
    path = f'{PIECES}/p{i:03d}.mp4'
    if kind == 'aroll':
        # locate source time
        s = next(s for s in segs if s['o'] - 1e-6 <= o0 < s['o'] + s['b'] - s['a'] - 1e-6)
        src = s['a'] + (o0 - s['o'])
        if s['sec'] == 'hook':
            # slow push-in for the hook
            vf = (f"scale=1728:3072,zoompan=z='1.0+0.0004*(on+{frames(o0)})':x='iw*0.36-iw/zoom*0.36':y='ih*0.45-ih/zoom*0.45':d=1:s={W}x{H}:fps=30000/1001")
        else:
            tight = (aroll_alt % 2 == 1); aroll_alt += 1
            vf = ("crop=1300:2311:0:330,scale=1080:1920" if tight else f"scale={W}:{H}")
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{src:.3f}', '-i', SPEECH, '-frames:v', str(nf),
               '-vf', vf + ',setsar=1,format=yuv420p', '-r', '30000/1001', '-an',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', path]
    elif kind == 'broll':
        clip, cin = p
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{cin:.3f}', '-i', f'{PROXY}/{clip}.mp4', '-frames:v', str(nf),
               '-vf', 'setsar=1,format=yuv420p', '-r', '30000/1001', '-an',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', path]
    else:
        clip, cin = p
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{cin:.3f}', '-i', f'{PROXY}/{clip}.mp4', '-frames:v', str(nf),
               '-vf', 'gblur=sigma=28,eq=brightness=-0.08:saturation=0.8,setsar=1,format=yuv420p', '-r', '30000/1001', '-an',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', path]
    if not os.path.exists(path) or '--force' in sys.argv:
        run(cmd)
    got = int(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', path]).stdout)
    if got < nf:
        # clip too short: pad by cloning last frame
        run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vf', f'tpad=stop_mode=clone:stop={nf-got}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', path + '.tmp.mp4'])
        os.replace(path + '.tmp.mp4', path)
    print(f'{i:3d} {o0:7.2f}-{o1:7.2f} {kind:5s} {p if p else ""}')

with open(f'{WORK}/concat.txt', 'w') as f:
    for i, *_ in render:
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
# place on timeline with adelay
inputs, flt = [], []
for k, (o, p) in enumerate(parts):
    inputs += ['-i', p]
    flt.append(f'[{k}]adelay={int(round(o*1000))}|{int(round(o*1000))}[d{k}]')
flt.append(''.join(f'[d{k}]' for k in range(len(parts))) + f'amix=inputs={len(parts)}:normalize=0,apad=whole_dur={TOTAL:.3f}[raw]')
enh = ('highpass=f=85,lowpass=f=14000,'
       'afftdn=nr=14:nf=-42:tn=1,'
       'equalizer=f=220:t=q:w=1.0:g=-3,equalizer=f=3200:t=q:w=1.2:g=3.5,equalizer=f=8000:t=h:w=0.7:g=1.5,'
       'deesser=i=0.35,'
       'acompressor=threshold=-22dB:ratio=3:attack=6:release=120:makeup=3,'
       'loudnorm=I=-15:TP=-2:LRA=8')
flt.append(f'[raw]{enh}[sp]')
run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(flt), '-map', '[sp]', '-ar', '48000', '-t', f'{TOTAL:.3f}', f'{WORK}/speech_enh.wav'])

# ---------------- music bed ----------------
def vol_expr():
    # loud in intro and end card, low under speech; 0.35s ramps
    lo, hi = 0.13, 0.85
    r = 0.35
    def ramp(a, b):  # 0 outside, 1 inside [a,b] with ramps
        return f"clip(min((t-({a}-{r}))/{r},(({b}+{r})-t)/{r}),0,1)"
    return f"{lo}+({hi}-{lo})*max({ramp(INTRO_START+0.25, INTRO_END-0.35)},{ramp(BODY_END+0.2, TOTAL+5)})"
run(['ffmpeg', '-v', 'error', '-y', '-i', MUSIC, '-t', f'{TOTAL:.3f}',
     '-af', f"loudnorm=I=-16:TP=-2,volume='{vol_expr()}':eval=frame,afade=t=in:d=0.6,afade=t=out:st={TOTAL-1.6:.3f}:d=1.6",
     '-ar', '48000', '-ac', '2', f'{WORK}/music_bed.wav'])

# ---------------- captions + gfx (ASS) ----------------
T = json.load(open(f'{WORK}/transcript.json'))
WORDS = [w for s in T for w in s['words']]

def ass_t(x):
    x = max(x, 0); h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f'{h}:{m:02d}:{s:05.2f}'

def chunk_words(words):
    out, cur = [], []
    for w in words:
        cur.append(w)
        txt = ' '.join(cur)
        endp = w[-1] in ',.?!'
        if len(cur) >= 4 or len(txt) >= 18 or (endp and len(cur) >= 2) or (w[-1] in '.?!'):
            out.append(cur); cur = []
    if cur:
        if out and len(cur) == 1 and len(' '.join(out[-1] + cur)) <= 24:
            out[-1] += cur
        else:
            out.append(cur)
    return out

events = []
CREAM = '&H00A4DCEC'
for s in segs:
    sw = [w for w in WORDS if s['a'] - 0.05 <= w['s'] <= s['b'] - 0.05]
    cw = s['text'].split()
    chunks = chunk_words(cw)
    seg_o0, seg_o1 = s['o'], s['o'] + s['b'] - s['a']
    idx = 0
    starts = []
    for ch in chunks:
        if sw:
            j = min(int(round(idx * len(sw) / len(cw))), len(sw) - 1)
            st = src2out(sw[j]['s'])
        else:
            st = seg_o0 + (seg_o1 - seg_o0) * idx / len(cw)
        starts.append(max(st if st is not None else seg_o0, seg_o0))
        idx += len(ch)
    starts[0] = seg_o0 + 0.02
    for k, ch in enumerate(chunks):
        st = starts[k]
        en = starts[k + 1] if k + 1 < len(chunks) else seg_o1
        if en - st < 0.25:
            continue
        txt = ' '.join(ch)
        events.append(('Sub', st, en - 0.02, r'{\fad(40,0)\blur1.5\4a&H30&}' + txt))
        events.append(('SubGlow', st, en - 0.02, r'{\fad(40,0)\blur14\1a&HFF&\3c&H000000&\3a&H90&\bord10}' + txt))

def ow(src):  # output time of source word
    return src2out(src)

def find_word(word, after, before=None):
    for w in WORDS:
        if w['s'] >= after and (before is None or w['s'] <= before) and word.lower() in w['w'].lower():
            return w['s']
    raise KeyError(word)

gfx = []
# --- hook stat card
st6 = ow(find_word('six', 284, 286))
card = (r'{\an7\pos(90,250)\bord0\shad0\1c&HFFFFFF&\1a&H08&\p1}'
        r'm 30 0 l 870 0 b 900 0 900 0 900 30 l 900 370 b 900 400 900 400 870 400 l 30 400 b 0 400 0 400 0 370 l 0 30 b 0 0 0 0 30 0{\p0}')
gfx.append(('Card', st6 - 0.1, HOOK_END - 0.05, r'{\fad(200,150)}' + card))
gfx.append(('Stat', st6, HOOK_END - 0.05, r'{\an5\pos(540,385)\fad(200,150)\fscx85\fscy85\t(0,250,\fscx100\fscy100)}6 OUT OF 8'))
gfx.append(('StatSub', st6 + 0.35, HOOK_END - 0.05, r'{\an5\pos(540,540)\fad(250,150)}new ISA cases involved youths' + r'\N' + 'aged 20 and below'))

# --- intro titles
gfx.append(('IntroSub', INTRO_START + 1.0, INTRO_END - 0.15, r'{\an5\pos(540,1150)\fad(300,250)\fsp3}SAFEGUARDING YOUTHS AGAINST\NONLINE EXTREMISM'))
gfx.append(('IntroDate', INTRO_START + 1.4, INTRO_END - 0.15, r'{\an5\pos(540,1310)\fad(300,250)\fsp6}17 NOVEMBER 2026'))

# --- lower third (minister)
lt0, lt1 = BODY_START + 0.4, BODY_START + 5.4
box1 = r'{\an7\pos(60,1540)\bord0\shad0\1c&H3D2114&\p1}m 0 0 l 700 0 l 700 104 l 0 104{\p0}'
box2 = r'{\an7\pos(60,1644)\bord0\shad0\1c&HE0904A&\p1}m 0 0 l 960 0 l 960 124 l 0 124{\p0}'
gfx.append(('Box', lt0, lt1, r'{\fad(200,200)\clip(60,1540,60,1644)\t(0,300,\clip(60,1540,760,1644))}' + box1))
gfx.append(('Box', lt0 + 0.15, lt1, r'{\fad(200,200)\clip(60,1644,60,1768)\t(0,300,\clip(60,1644,1020,1768))}' + box2))
gfx.append(('LTName', lt0 + 0.25, lt1, r'{\an4\pos(92,1593)\fad(250,200)}Mr Zaqy Mohamad'))
gfx.append(('LTTitle', lt0 + 0.35, lt1, r'{\an4\pos(92,1706)\fad(250,200)}Acting Minister-in-charge of Muslim Affairs &\NSenior Minister of State for Defence'))

# --- three actions chips
def chip(label, num, t0, t1, y=330):
    w = 42 * len(label) + 210
    x0 = 540 - w // 2
    shape = (rf'{{\an7\pos({x0},{y})\bord0\shad0\1c&HE0904A&\p1}}'
             rf'm 52 0 l {w-52} 0 b {w} 0 {w} 104 {w-52} 104 l 52 104 b 0 104 0 0 52 0{{\p0}}')
    gfx.append(('Chip', t0, t1, r'{\fad(180,180)}' + shape))
    gfx.append(('ChipText', t0, t1, rf'{{\an5\pos(540,{y+53})\fad(180,180)}}{{\1c&HA4DCEC&}}{num}  {{\1c&HFFFFFF&}}{label}'))

r1 = ow(find_word('Recognize', 439, 440)); r2 = ow(find_word('reflect', 440, 441)); r3 = ow(find_word('respond', 441, 442))
s7_end = next(s for s in segs if abs(s['a'] - 436.53) < 1e-3); s7_end = s7_end['o'] + s7_end['b'] - s7_end['a']
chip('RECOGNISE', '01', r1, s7_end, 280)
chip('REFLECT', '02', r2, s7_end, 410)
chip('RESPOND', '03', r3, s7_end, 540)
def seg_span(a):
    s = next(s for s in segs if abs(s['a'] - a) < 1e-3)
    return s['o'], s['o'] + s['b'] - s['a']
chip('RECOGNISE', '01', seg_span(442.85)[0] + 0.1, seg_span(445.85)[1] - 0.1)
chip('REFLECT', '02', seg_span(480.85)[0] + 0.1, seg_span(492.25)[1] - 0.1)
chip('RESPOND', '03', seg_span(514.80)[0] + 0.1, seg_span(584.72)[1] - 0.1)

# --- end card text
gfx.append(('EndTag', BODY_END + 0.6, TOTAL, r'{\an5\pos(540,1200)\fad(300,0)\fsp4}RECOGNISE  ·  REFLECT  ·  RESPOND'))

header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Poppins SemiBold,84,{CREAM},&H000000FF,&H00000000,&H40000000,0,0,0,0,100,100,0,0,1,0,3,2,50,50,500,1
Style: SubGlow,Poppins SemiBold,84,&HFF000000,&H000000FF,&H00000000,&HFF000000,0,0,0,0,100,100,0,0,1,0,0,2,50,50,500,1
Style: Card,Poppins,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Stat,Poppins ExtraBold,170,&H003D2114,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: StatSub,Poppins Medium,50,&H003D2114,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: IntroSub,Poppins SemiBold,58,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,0,2,5,0,0,0,1
Style: IntroDate,Poppins SemiBold,46,{CREAM},&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,0,2,5,0,0,0,1
Style: Box,Poppins,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: LTName,Poppins Bold,64,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1
Style: LTTitle,Poppins Medium,38,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1
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

# ---------------- final composite ----------------
LOGO_W = 920
li, lo = INTRO_START + 0.35, INTRO_END - 0.15
ei = BODY_END + 0.15
fc = (
    f"[0:v]eq=brightness=-0.13:contrast=0.92:enable='between(t,{INTRO_START:.3f},{INTRO_END:.3f})'[v0];"
    f"[2:v]format=rgba,split[lg1][lg2];"
    f"[lg1]scale=w='{LOGO_W}*(0.9+0.1*min(1,max(0,(t-{li:.3f})/0.45)))':h=-1:eval=frame,"
    f"fade=t=in:st={li:.3f}:d=0.35:alpha=1,fade=t=out:st={lo-0.3:.3f}:d=0.3:alpha=1[l1];"
    f"[lg2]scale=w='{int(LOGO_W*0.85)}*(0.9+0.1*min(1,max(0,(t-{ei:.3f})/0.45)))':h=-1:eval=frame,"
    f"fade=t=in:st={ei:.3f}:d=0.35:alpha=1[l2];"
    f"[v0][l1]overlay=x='(W-w)/2':y='800-h/2':enable='between(t,{li:.3f},{lo:.3f})':eval=frame[v1];"
    f"[v1][l2]overlay=x='(W-w)/2':y='860-h/2':enable='gte(t,{ei:.3f})':eval=frame[v2];"
    f"[v2]ass={WORK}/gfx.ass:fontsdir={FONTDIR}[v];"
    f"[1:a][3:a]amix=inputs=2:normalize=0,volume=2.3dB,alimiter=limit=0.89:level=false[a]"
)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
run(['ffmpeg', '-v', 'error', '-y', '-i', f'{WORK}/video_nogfx.mp4', '-i', f'{WORK}/speech_enh.wav',
     '-loop', '1', '-framerate', '30000/1001', '-t', f'{TOTAL:.3f}', '-i', LOGO, '-i', f'{WORK}/music_bed.wav',
     '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-t', f'{TOTAL:.3f}',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
     '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT])
print('done', OUT, dur_of(OUT))
