# Penakut CCTV montage — 1080x1920 @30fps
# usage: python3 render.py SRC_DIR MUSIC OUT [preview_scale]
import numpy as np, subprocess, sys, os, math, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import sfx as SFX

SRC, MUSIC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ONLY = sys.argv[4] if len(sys.argv) > 4 else None   # e.g. "27-37" to render a range (preview)
W, H, FPS = 1080, 1920, 30
SW, SH = 1024, 576
HERE = os.path.dirname(os.path.abspath(__file__))
POP = HERE + '/../assets/fonts/Poppins-'
EMO = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
MONO = '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf'
YEL = (254, 213, 2); RED = (235, 40, 40); WHITE = (255, 255, 255); BLACK = (0, 0, 0)
PX, PY, PW, PH = 0, 330, 1080, 1350          # video panel (4:5)

def F(w, s): return ImageFont.truetype(POP + str(w) + '.ttf', s)
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x):
    x = clamp(x); c = 2.2; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k

_emo = {}
def emoji(ch, size):
    k = (ch, size)
    if k not in _emo:
        f = ImageFont.truetype(EMO, 109); im = Image.new('RGBA', (180, 160))
        ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox()); _emo[k] = im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)
    return _emo[k]

# ---------------- caption builder ----------------
# token: ('t', text, size, color, bg|None, weight) or ('e', emoji, size)
def tok_img(tk):
    if tk[0] == 'e': return emoji(tk[1], tk[2])
    _, text, size, col, bg, wt = tk
    font = F(wt, size); l, t_, r, b = font.getbbox(text); asc, desc = font.getmetrics()
    sw = max(4, size // 11)
    padx, pady = (24, 6) if bg else (sw, sw)
    w = r - l + 2 * padx; h = asc + desc + 2 * pady
    im = Image.new('RGBA', (w + 24, h + 24)); d = ImageDraw.Draw(im)
    if bg:
        d.rounded_rectangle((12, 16, 12 + w, 16 + h), radius=18, fill=(0, 0, 0, 160))
        d.rounded_rectangle((12, 12, 12 + w, 12 + h), radius=18, fill=bg + (255,))
        d.text((12 + padx - l, 12 + pady), text, font=font, fill=col + (255,))
    else:
        d.text((12 + padx - l, 12 + pady + 5), text, font=font, fill=(0, 0, 0, 150), stroke_width=sw, stroke_fill=(0, 0, 0, 150))
        d.text((12 + padx - l, 12 + pady), text, font=font, fill=col + (255,), stroke_width=sw, stroke_fill=BLACK + (255,))
    return im

def caption(lines, gap=10, lgap=0):
    rows = [[tok_img(t) for t in ln] for ln in lines]
    hs = [max(i.height for i in r) for r in rows]; ws = [sum(i.width for i in r) + gap * (len(r) - 1) for r in rows]
    cw, ch = max(ws), sum(hs) + lgap * (len(rows) - 1)
    im = Image.new('RGBA', (cw, ch)); y = 0
    for r, h_, w_ in zip(rows, hs, ws):
        x = (cw - w_) // 2
        for i in r: im.alpha_composite(i, (x, y + (h_ - i.height) // 2)); x += i.width + gap
        y += h_ + lgap
    return im

def T(text, size=78, col=WHITE, bg=None, wt=900): return ('t', text, size, col, bg, wt)
def E(ch, size=84): return ('e', ch, size)

# ---------------- static overlays ----------------
def make_scan():
    im = Image.new('RGBA', (PW, PH)); d = ImageDraw.Draw(im)
    for y in range(0, PH, 4): d.line((0, y, PW, y), fill=(0, 0, 0, 38))
    # vignette
    v = Image.new('L', (PW, PH), 0); dv = ImageDraw.Draw(v)
    for i in range(60):
        a = int(150 * (1 - i / 60) ** 2); dv.rectangle((i * 4, i * 4, PW - i * 4, PH - i * 4), outline=a, width=4)
    vig = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); vig.putalpha(v.filter(ImageFilter.GaussianBlur(20)))
    im.alpha_composite(vig)
    # corner brackets
    L = 70; m = 34; c = (255, 255, 255, 210)
    for (x, y, sx, sy) in [(m, m, 1, 1), (PW - m, m, -1, 1), (m, PH - m, 1, -1), (PW - m, PH - m, -1, -1)]:
        d.line((x, y, x + sx * L, y), fill=c, width=6); d.line((x, y, x, y + sy * L), fill=c, width=6)
    return im
SCAN = make_scan()
FM = ImageFont.truetype(MONO, 34)
RED_VIG = None
def red_vig():
    global RED_VIG
    if RED_VIG is None:
        v = Image.new('L', (W, H), 0); dv = ImageDraw.Draw(v)
        for i in range(80):
            dv.rectangle((i * 6, i * 6, W - i * 6, H - i * 6), outline=int(230 * (1 - i / 80) ** 2), width=6)
        im = Image.new('RGBA', (W, H), (200, 0, 0, 0)); im.putalpha(v.filter(ImageFilter.GaussianBlur(30))); RED_VIG = im
    return RED_VIG

HEADER = caption([[E('📹', 54), T('CCTV EXPOSED', 46, WHITE, RED, 800), E('😱', 54)]], gap=12)

# ---------------- source frame reader ----------------
def read_frames(src, t0, src_span, speed, n, reverse=False):
    """returns n frames (uint8 HxWx3) covering source [t0, t0+src_span] played at speed (or reversed)."""
    vf = f"setpts=(PTS-STARTPTS)/{speed},fps={FPS}"
    if reverse: vf = "reverse," + vf
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-t', f'{src_span + 0.3:.3f}', '-i', f'{SRC}/{src}.mov',
           '-vf', vf + f',scale={SW}:{SH}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, SH, SW, 3)
    if len(fr) < n: fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr[:n]

# ---------------- timeline ----------------
# shot: start, end, src, t0, speed, crop0, crop1 (x,y,w,h), extras
FULL = lambda x: (x, 0, 460, 576)
shots = [
    dict(s=0.0,  e=3.2,  src='v4', t0=0.0,   sp=1.0, c0=FULL(0),   c1=FULL(0)),
    dict(s=3.2,  e=7.2,  src='v4', t0=1.0,   sp=2.0, c0=FULL(0),   c1=(20, 40, 400, 500)),
    dict(s=7.2,  e=11.2, src='v3', t0=74.0,  sp=3.0, c0=FULL(450), c1=FULL(450)),
    dict(s=11.2, e=11.9, src='v2', t0=12.5,  sp=1.0, c0=FULL(400), c1=FULL(400), freeze=True, dark=True),
    dict(s=11.9, e=17.4, src='v2', t0=13.0,  sp=2.0, c0=FULL(400), c1=FULL(400), shake=(11.9, 13.6, 18), red=(11.9, 17.4)),
    dict(s=17.4, e=21.4, src='v2', t0=40.0,  sp=3.0, c0=FULL(520), c1=FULL(520)),
    dict(s=21.4, e=25.0, src='v4', t0=146.0, sp=2.2, c0=FULL(480), c1=FULL(480)),
    dict(s=25.0, e=27.05, src='v3', t0=3.0,  sp=1.0, c0=FULL(500), c1=(560, 120, 365, 456)),
    dict(s=27.05, e=29.6, src='v3', t0=5.05, sp=1.0, c0=(560, 120, 365, 456), c1=(560, 176, 320, 400), freeze=True, zoomdur=0.35),
    dict(s=29.6, e=30.3, src='v3', t0=3.65,  sp=2.0, c0=(540, 101, 380, 475), c1=(540, 101, 380, 475), reverse=True, src_span=1.4),
    dict(s=30.3, e=36.3, src='v3', t0=3.9,   sp=0.3, c0=(540, 101, 380, 475), c1=(560, 176, 320, 400), shake=(34.3, 35.0, 14)),
    dict(s=36.3, e=39.8, src='v3', t0=5.7,   sp=1.0, c0=(560, 176, 320, 400), c1=FULL(500)),
    dict(s=39.8, e=44.5, src='v1', t0=64.0,  sp=1.5, c0=FULL(380), c1=FULL(380)),
]
TOTAL = shots[-1]['e']
PUSH_T = 30.3 + (5.1 - 3.9) / 0.3   # = 34.3 in output time

# captions: (start, end, image, cx, cy, anim)
caps = []
def cap(s, e, lines, cy, cx=W // 2, anim='pop', **kw): caps.append((s, e, caption(lines, **kw), cx, cy, anim))
TOP = 220
cap(0.15, 3.15, [[T('BUKTI CCTV', 120, YEL, None, 900)], [T('SAYA PALING', 88)], [T('PENAKUT', 130, WHITE, RED, 900), E('😭', 110)]], 1000, lgap=6)
cap(3.25, 7.15, [[T('Masuk rumah hantu,', 64, WHITE, None, 800)], [T('konon BERANI', 76, BLACK, YEL, 900), E('😎', 74)]], TOP + 50)
cap(7.25, 11.15, [[T('Formasi', 64, WHITE, None, 800), T('ANAK AYAM', 76, BLACK, YEL, 900), E('🐥', 74)]], TOP)
cap(8.3, 11.15, [[T('berpeluk sampai sesak nafas', 46, WHITE, None, 800)]], 1760)
cap(11.2, 11.9, [[T('Tiba-tiba...', 96, WHITE, None, 900), E('😶', 90)]], 1000, anim='type')
cap(11.95, 17.35, [[E('👻', 90), T('HANTU DATANG', 88, WHITE, RED, 900), E('👻', 90)]], TOP, anim='shake')
cap(12.3, 14.4, [[T('AAAAAAAAA!!!', 120, YEL, None, 900)]], 1050, anim='wobble')
cap(17.45, 21.35, [[T('Strategi:', 64, WHITE, None, 800), T('DUDUK DIAM', 76, BLACK, YEL, 900)], [T('& baca doa', 64, WHITE, None, 800), E('🙏', 66), E('😭', 66)]], TOP + 50)
cap(21.45, 24.95, [[T('Misi terakhir:', 64, WHITE, None, 800)], [T('LUBANG KECIK', 76, BLACK, YEL, 900), E('🚪', 74)]], TOP + 50)
cap(22.4, 24.95, [[T('kena bongkok masuk', 46, WHITE, None, 800)]], 1760)
cap(25.05, 27.0, [[T('Saya: "tak nak lah..."', 66, WHITE, None, 800), E('😰', 70)]], TOP)
cap(27.15, 29.55, [[T('Jap...', 70, WHITE, None, 800), T('REWIND', 76, BLACK, YEL, 900), E('🤨', 74)]], TOP)
cap(29.6, 30.3, [[T('◀◀', 120, WHITE, None, 900)]], 1000, anim='blink')
cap(30.35, PUSH_T - 0.05, [[T('Perhatikan', 64, WHITE, None, 800), T('KAWAN', 76, BLACK, YEL, 900), T('ni', 64, WHITE, None, 800), E('👀', 70)]], TOP)
cap(PUSH_T, 36.25, [[T('DITOLAK MASUK!', 84, WHITE, RED, 900), E('💀', 80)]], TOP, anim='slam')
cap(36.35, 39.75, [[T('Lepas tolak,', 64, WHITE, None, 800), T('dia pun', 64, WHITE, None, 800)], [T('TERJUN SEKALI', 76, BLACK, YEL, 900), E('🤣', 74)]], TOP + 50)
cap(37.6, 39.75, [[T('kawan sejati ke ni?', 52, WHITE, None, 800), E('🤝', 56)]], 1760)
cap(39.85, 44.4, [[T('Moral of the story:', 60, WHITE, None, 800)], [T('JANGAN PERCAYA KAWAN', 60, BLACK, YEL, 900), E('🤡', 64)]], TOP + 50)
cap(41.6, 44.4, [[T('Penakut? Saya? Mana ada', 50, WHITE, None, 800), E('😅', 54)]], 1760)

STAMP = None
def stamp_img():
    global STAMP
    if STAMP is None:
        f = F(900, 92); txt = 'PENGKHIANAT!'; l, t_, r, b = f.getbbox(txt)
        w, h = r - l + 70, b - t_ + 60; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((6, 6, w - 6, h - 6), radius=16, outline=RED + (255,), width=10)
        d.text((35 - l, 30 - t_), txt, font=f, fill=RED + (255,))
        STAMP = im.rotate(-12, expand=True, resample=Image.BICUBIC)
    return STAMP

def label(text, emo, col):
    return caption([[T(text, 56, BLACK if col == YEL else WHITE, col, 900), E(emo, 60)]], gap=6)
LBL_ME = label('SAYA', '🥲', YEL); LBL_FR = label('KAWAN', '😈', RED)
REPLAY = caption([[E('🔁', 52), T('INSTANT REPLAY', 46, WHITE, RED, 800), T('0.3x', 46, BLACK, YEL, 800)]], gap=8)

def src_to_panel(sx, sy, crop):
    x, y, w, h = crop; return PX + (sx - x) * PW / w, PY + (sy - y) * PH / h

def draw_arrow(d, tip, ang, L=170, col=YEL):
    a = math.radians(ang); tx, ty = tip
    bx, by = tx - L * math.cos(a), ty - L * math.sin(a)
    d.line((bx, by, tx - 40 * math.cos(a), ty - 40 * math.sin(a)), fill=BLACK, width=30)
    d.line((bx, by, tx - 40 * math.cos(a), ty - 40 * math.sin(a)), fill=col, width=18)
    p = [(tx, ty), (tx - 70 * math.cos(a - .5), ty - 70 * math.sin(a - .5)), (tx - 70 * math.cos(a + .5), ty - 70 * math.sin(a + .5))]
    d.polygon(p, fill=col, outline=BLACK, width=5)

def ring(d, cx, cy, r, col, w=10):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=BLACK, width=w + 6)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=w)

# ---------------- frame composer ----------------
def compose(t, src, crop, shot):
    # background: blurred, darkened source
    cx = SW // 2 - 162; bg = Image.fromarray(src[:, cx:cx + 324]).resize((54, 96), Image.BILINEAR)
    bg = bg.filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    bg = Image.eval(bg, lambda v: int(v * 0.35)).convert('RGBA')
    x, y, w, h = crop
    x = clamp(x, 0, SW - w); y = clamp(y, 0, SH - h)
    pan = Image.fromarray(src).resize((PW, PH), Image.BILINEAR, box=(x, y, x + w, y + h)).convert('RGBA')
    if shot.get('dark'): pan = Image.eval(pan.convert('RGB'), lambda v: int(v * 0.3)).convert('RGBA')
    pan.alpha_composite(SCAN)
    dp = ImageDraw.Draw(pan)
    if int(t * 2) % 2 == 0:
        dp.ellipse((60, 62, 88, 90), fill=RED); dp.text((100, 56), 'REC', font=FM, fill=WHITE)
    dp.text((60, PH - 96), f"CAM-{ {'v1': '07', 'v2': '13', 'v3': '13', 'v4': '13'}[shot['src']] }  00:{int(t):02d}:{int((t % 1) * 30):02d}", font=FM, fill=(255, 255, 255, 200))
    ox = oy = 0
    if 'shake' in shot:
        a, b, amp = shot['shake']
        if a <= t < b:
            k = amp * (1 - (t - a) / (b - a)); r = np.random.default_rng(int(t * 1000))
            ox, oy = r.integers(-k - 1, k + 1, 2)
    bg.alpha_composite(pan, (int(PX + ox), int(PY + oy)))
    return bg

def overlays(img, t, crop, shot):
    d = ImageDraw.Draw(img)
    # header
    img.alpha_composite(HEADER, ((W - HEADER.width) // 2, 40))
    # red pulse during ghost
    if 'red' in shot and shot['red'][0] <= t < shot['red'][1]:
        a = 0.55 + 0.45 * math.sin(t * 14)
        rv = red_vig().copy(); rv.putalpha(Image.eval(rv.getchannel('A'), lambda v: int(v * a))); img.alpha_composite(rv)
    # arrow to hole (lubang kecik)
    if 21.9 <= t < 25.0:
        tip = src_to_panel(870, 470, crop); k = back((t - 21.9) / 0.3); bob = 14 * math.sin(t * 10)
        draw_arrow(d, (tip[0] - 20 + bob, tip[1] - 20 + bob), 45, L=170 * k + 1)
    # freeze-frame labels
    if 27.05 <= t < 29.6:
        cr = crop
        if t >= 27.45:
            k = back((t - 27.45) / 0.25); cx_, cy_ = src_to_panel(705, 535, cr); ring(d, cx_, cy_, 130 * k + 1, YEL)
            img.alpha_composite(LBL_ME, (int(cx_ - LBL_ME.width / 2), int(cy_ - 130 - LBL_ME.height)))
        if t >= 28.0:
            k = back((t - 28.0) / 0.25); cx_, cy_ = src_to_panel(688, 322, cr); ring(d, cx_, cy_, 150 * k + 1, RED)
            img.alpha_composite(LBL_FR, (int(cx_ + 90), int(cy_ - 150 - LBL_FR.height // 2)))
    # rewind lines
    if 29.6 <= t < 30.3:
        r = np.random.default_rng(int(t * 100))
        for _ in range(6):
            yy = int(r.integers(PY, PY + PH)); d.rectangle((0, yy, W, yy + int(r.integers(3, 14))), fill=(255, 255, 255, 90))
    # instant replay banner + tracking rings
    if 30.3 <= t < 36.3:
        if int(t * 3) % 3 != 0 or t > PUSH_T: img.alpha_composite(REPLAY, ((W - REPLAY.width) // 2, PY + 40))
        if t < PUSH_T + 0.2:
            # follow the 'me' head (moves slightly toward hole)
            u = clamp((t - 30.3) / (PUSH_T + 0.2 - 30.3)); hx, hy = lerp(705, 735, u), lerp(540, 530, u)
            cx_, cy_ = src_to_panel(hx, hy, crop); ring(d, cx_, cy_, 120, YEL, 8)
            img.alpha_composite(LBL_ME, (int(cx_ - LBL_ME.width / 2), int(cy_ - 120 - LBL_ME.height)))
        if 31.5 <= t < PUSH_T:
            cx_, cy_ = src_to_panel(688, 322, crop); ring(d, cx_, cy_, 140, RED, 8)
            img.alpha_composite(LBL_FR, (int(cx_ + 80), int(cy_ - 140 - LBL_FR.height // 2)))
        if t >= PUSH_T + 0.45:
            st = stamp_img(); k = clamp((t - PUSH_T - 0.45) / 0.18); sc = lerp(2.4, 1.0, ease(k))
            s2 = st.resize((int(st.width * sc), int(st.height * sc)), Image.BICUBIC)
            img.alpha_composite(s2, (int(W / 2 - s2.width / 2), int(PY + PH * 0.42 - s2.height / 2)))
    # flash
    for ft, dur in [(0.0, 0.25), (11.9, 0.3), (27.05, 0.2), (PUSH_T, 0.3), (36.3, 0.15)]:
        if ft <= t < ft + dur:
            a = int(255 * (1 - (t - ft) / dur) * 0.85); img.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, a)))
    # captions
    for s, e, im, cx, cy, an in caps:
        if not (s <= t < e): continue
        u = t - s; sc = 1.0; dx = dy = 0; rot = 0; alpha = 1.0
        if an in ('pop', 'shake', 'wobble'): sc = back(u / 0.22) * 0.6 + 0.4 if u < 0.22 else 1.0
        if an == 'slam': sc = lerp(2.2, 1.0, ease(u / 0.15))
        if an == 'shake': dx, dy = 6 * math.sin(t * 53), 5 * math.cos(t * 41)
        if an == 'wobble': rot = 6 * math.sin(t * 18); sc *= 1 + 0.06 * math.sin(t * 25)
        if an == 'blink' and int(t * 8) % 2: continue
        if e - t < 0.1: alpha = (e - t) / 0.1
        im2 = im
        if an == 'type':
            n = int(clamp(u / 0.45) * im.width); im2 = im.crop((0, 0, max(1, n), im.height))
            img.alpha_composite(im2, (int(cx - im.width / 2), int(cy - im.height / 2))); continue
        if sc != 1.0 or rot:
            im2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
            if rot: im2 = im2.rotate(rot, expand=True, resample=Image.BICUBIC)
        if alpha < 1: im2 = im2.copy(); im2.putalpha(Image.eval(im2.getchannel('A'), lambda v: int(v * alpha)))
        img.alpha_composite(im2, (int(cx - im2.width / 2 + dx), int(cy - im2.height / 2 + dy)))
    # end fade
    if t > TOTAL - 0.6:
        img.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - TOTAL + 0.6) / 0.6)))))
    return img

# ---------------- render video ----------------
def render_video(path):
    lo, hi = (0, TOTAL)
    if ONLY: lo, hi = map(float, ONLY.split('-'))
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for sh in shots:
        if sh['e'] <= lo or sh['s'] >= hi: continue
        f0, f1 = round(sh['s'] * FPS), round(sh['e'] * FPS); n = f1 - f0
        if sh.get('freeze'):
            fr = read_frames(sh['src'], sh['t0'], 0.1, 1.0, 1)
        else:
            span = sh.get('src_span', (sh['e'] - sh['s']) * sh['sp'])
            fr = read_frames(sh['src'], sh['t0'], span, sh['sp'], n, sh.get('reverse', False))
        for i in range(n):
            t = (f0 + i) / FPS
            if t < lo or t >= hi: continue
            src = fr[0] if sh.get('freeze') else fr[i]
            zd = sh.get('zoomdur', sh['e'] - sh['s']); k = ease(i / FPS / zd) if 'zoomdur' in sh else (i / max(1, n - 1))
            crop = tuple(lerp(a, b, k) for a, b in zip(sh['c0'], sh['c1']))
            img = compose(t, src, crop, sh); img = overlays(img, t, crop, sh)
            enc.stdin.write(img.convert('RGB').tobytes())
        print(f"shot {sh['s']:.1f}-{sh['e']:.1f} done", flush=True)
    enc.stdin.close(); enc.wait()

# ---------------- audio ----------------
SR = 44100
def render_audio(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', MUSIC, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    mus = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    N = int((TOTAL + 0.5) * SR); out = np.zeros((N, 2), np.float32)
    def put_music(o0, o1, m0, vol, fin=0.03, fout=0.03):
        a, b = int(o0 * SR), int(o1 * SR); seg = mus[int(m0 * SR): int(m0 * SR) + (b - a)] * vol
        n = len(seg); e = np.ones(n, np.float32)
        fi, fo = int(fin * SR), int(fout * SR); e[:fi] = np.linspace(0, 1, fi); e[n - fo:] = np.minimum(e[n - fo:], np.linspace(1, 0, fo))
        out[a:a + n] += seg * e[:, None]
    put_music(0.0, 11.2, 0.0, 0.55)                       # sneaky intro
    put_music(17.4, 27.05, 11.2, 0.55, fin=0.4)           # resume after ghost
    put_music(36.3, 44.5, 20.85, 0.5, fin=0.3, fout=1.2)  # resume after replay
    S = SFX.all_sfx()
    def fx(name, at, vol=1.0, maxdur=None):
        s = S[name]
        if maxdur: s = s[:int(maxdur * SR)]
        a = int(at * SR); n = min(len(s), N - a); out[a:a + n] += (s[:n] * vol)[:, None]
    fx('whoosh', 0.0, .8); fx('boom', 0.15, .8); fx('ding', 1.0, .6)
    for tt in [3.25, 4.0, 7.25, 8.3, 17.45, 18.2, 21.45, 22.4, 25.05]: fx('pop', tt, .7)
    fx('whoosh', 21.8, .6)
    fx('scratch', 11.2, .9); fx('boom', 11.9, 1.0); fx('sting', 11.9, .8); fx('sting', 14.4, .5)
    fx('scratch', 27.05, .9); fx('shutter', 27.1, .8); fx('pop', 27.45, .8); fx('pop', 28.0, .8); fx('ding', 28.0, .4)
    fx('rewind', 29.55, .9)
    fx('heart', 30.35, .9, maxdur=PUSH_T - 30.35)
    fx('boom', PUSH_T, 1.0); fx('slide', PUSH_T + 0.3, .8); fx('boing', PUSH_T + 0.45, .7)
    fx('whoosh', 36.2, .6); fx('boing', 36.9, .6)
    fx('pop', 39.85, .7); fx('trombone', 41.6, .9)
    out = np.tanh(out * 1.1) * 0.95
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(pcm.tobytes())

if __name__ == '__main__':
    tmpv, tmpa = OUT + '.video.mp4', OUT + '.audio.wav'
    render_audio(tmpa); render_video(tmpv)
    ss = ['-ss', ONLY.split('-')[0]] if ONLY else []
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmpv] + ss + ['-i', tmpa, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], check=True)
    os.remove(tmpv); os.remove(tmpa); print('wrote', OUT)
