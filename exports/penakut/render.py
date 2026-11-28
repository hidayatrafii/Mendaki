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
FULL = lambda x: (x, 0, 460, 576)
ZOOM = (560, 176, 320, 400)
LIE = (520, 60, 400, 500)
PZ = (200, 0, 280, 350)
shots = [
    dict(s=0.0,  e=3.2,  src='v4', t0=0.0,   sp=1.0, c0=FULL(0),   c1=(20, 40, 400, 500)),
    dict(s=3.2,  e=6.0,  src='v4', t0=1.0,   sp=2.0, c0=FULL(0),   c1=FULL(0)),
    dict(s=6.0,  e=8.6,  src='v3', t0=50.0,  sp=2.0, c0=FULL(60),  c1=FULL(60)),
    dict(s=8.6,  e=9.5,  src='v3', t0=56.0,  sp=1.0, c0=FULL(60),  c1=(180, 202, 300, 375), freeze=True, zoomdur=0.12),
    dict(s=9.5,  e=12.3, src='v3', t0=66.0,  sp=2.5, c0=FULL(380), c1=FULL(380)),
    dict(s=12.3, e=12.9, src='v3', t0=73.0,  sp=1.0, c0=FULL(380), c1=(560, 60, 380, 475), freeze=True, zoomdur=0.12),
    dict(s=12.9, e=15.9, src='v3', t0=74.0,  sp=3.0, c0=FULL(450), c1=FULL(450)),
    dict(s=15.9, e=16.6, src='v2', t0=12.5,  sp=1.0, c0=FULL(400), c1=FULL(400), freeze=True, dark=True),
    dict(s=16.6, e=19.6, src='v2', t0=7.0,   sp=1.2, c0=FULL(250), c1=(250, 60, 400, 500), shake=(16.6, 17.7, 10)),
    dict(s=19.6, e=23.6, src='v2', t0=13.0,  sp=2.0, c0=FULL(400), c1=FULL(400), shake=(19.6, 20.6, 12), red=(19.6, 28.8)),
    dict(s=23.6, e=27.9, src='v2', t0=22.0,  sp=1.4, c0=FULL(480), c1=(470, 30, 420, 525), red=(19.6, 28.8)),
    dict(s=27.9, e=28.8, src='v2', t0=28.0,  sp=1.0, c0=(470, 30, 420, 525), c1=(560, 120, 330, 412), freeze=True, zoomdur=0.12, red=(19.6, 28.8)),
    dict(s=28.8, e=33.8, src='v2', t0=60.0,  sp=6.0, c0=LIE, c1=LIE),
    dict(s=33.8, e=37.8, src='v2', t0=96.0,  sp=2.0, c0=LIE, c1=(560, 120, 360, 450)),
    dict(s=37.8, e=41.3, src='v1', t0=34.0,  sp=2.0, c0=(100, 0, 460, 576), c1=(140, 0, 380, 475), bright=True),
    dict(s=41.3, e=43.3, src='v1', t0=41.0,  sp=2.0, c0=(140, 0, 380, 475), c1=(170, 0, 330, 412), bright=True),
    dict(s=43.3, e=45.0, src='v1', t0=45.0,  sp=1.0, c0=(170, 0, 330, 412), c1=PZ, freeze=True, zoomdur=0.3, bright=True),
    dict(s=45.0, e=45.7, src='v1', t0=43.4,  sp=2.0, c0=PZ, c1=PZ, reverse=True, src_span=1.6, bright=True),
    dict(s=45.7, e=51.7, src='v1', t0=43.4,  sp=0.4, c0=(170, 0, 330, 412), c1=PZ, shake=(49.2, 49.8, 12), bright=True),
    dict(s=51.7, e=55.2, src='v1', t0=46.0,  sp=2.0, c0=PZ, c1=(100, 0, 460, 576), bright=True),
    dict(s=55.2, e=59.9, src='v1', t0=64.0,  sp=1.5, c0=FULL(380), c1=FULL(380)),
]
TOTAL = shots[-1]['e']
DARK, GHOST, FRZ, REW, RPL, AFTER = 15.9, 16.6, 43.3, 45.0, 45.7, 51.7
LIE0, LIE1, BOTH0, BOTH1 = 28.8, 33.8, 33.8, 37.8
PUNCH = [8.6, 12.3, 27.9]
PUSH_T = RPL + (44.8 - 43.4) / 0.4

caps = []
def cap(s, e, lines, cy, cx=W // 2, anim='fade', **kw): caps.append((s, e, caption(lines, **kw), cx, cy, anim))
def C(text, size=64, wt=700): return ('t', text, size, WHITE, None, wt)
cap(0.3, 3.1, [[C('bukti cctv:', 44, 600)], [C('saya penakut.', 92, 800)]], 210, lgap=0)
cap(6.15, 9.45, [[C('kawan semua dah lari.', 60, 700)]], 230)
cap(29.2, 33.7, [[C('strategi: main mati.', 60, 700)]], 230)
cap(55.7, 59.4, [[C('terima kasih, kawan.', 64, 700)]], 220)

ME = caption([[('t', 'me', 44, BLACK, YEL, 800)]])
ME_LIE, ASY_LIE = (733, 248), (815, 425)
ASY = caption([[('t', 'asyraf', 44, BLACK, WHITE, 800)]])
FMS = ImageFont.truetype(MONO, 30)

def src_to_panel(sx, sy, crop):
    x, y, w, h = crop; return PX + (sx - x) * PW / w, PY + (sy - y) * PH / h

def ring(d, cx, cy, r, col, w=7):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(0, 0, 0, 120), width=w + 4)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=w)

# ---------------- frame composer ----------------
def compose(t, src, crop, shot):
    # background: blurred, darkened source
    cx = SW // 2 - 162; bg = Image.fromarray(src[:, cx:cx + 324]).resize((54, 96), Image.BILINEAR)
    bg = bg.filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    bg = Image.eval(bg, lambda v: int(v * 0.35)).convert('RGBA')
    if shot.get('bright'): src = np.clip(src.astype(np.float32) * 1.9 + 8, 0, 255).astype(np.uint8)
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
    if 'red' in shot and shot['red'][0] <= t < shot['red'][1]:
        a = 0.35 + 0.25 * math.sin(t * 12)
        rv = red_vig().copy(); rv.putalpha(Image.eval(rv.getchannel('A'), lambda v: int(v * a))); img.alpha_composite(rv)
    # freeze: ring + 'me' tag on the guy in specs
    def tag(k, sx=690, sy=330, r=150):
        cx_, cy_ = src_to_panel(sx, sy, crop); ring(d, cx_, cy_, r * k + 1, YEL)
        if k > 0.9: img.alpha_composite(ME, (int(cx_ + r * 0.72), int(cy_ - r * 0.72 - ME.height)))
    if LIE0 <= t < LIE1:
        d.text((W - 200, PY + 52), '>> 6x', font=FM, fill=WHITE)
    if REW <= t < RPL and int(t * 8) % 2 == 0:
        d.text((W - 260, PY + 52), '<< REW', font=FM, fill=WHITE)
    if RPL <= t < AFTER:
        d.text((W - 310, PY + 52), 'REPLAY 0.4x', font=FM, fill=WHITE)
    if REW <= t < RPL:
        r = np.random.default_rng(int(t * 100))
        for _ in range(5):
            yy = int(r.integers(PY, PY + PH)); d.rectangle((0, yy, W, yy + int(r.integers(3, 12))), fill=(255, 255, 255, 70))
    for ft, dur, k in [(0.0, 0.2, .5), (GHOST, 0.25, .8), (FRZ, 0.15, .6), (PUSH_T, 0.25, .7)] + [(p_, 0.12, .5) for p_ in PUNCH]:
        if ft <= t < ft + dur:
            a = int(255 * (1 - (t - ft) / dur) * k); img.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, a)))
    for s, e, im, cx, cy, an in caps:
        if not (s <= t < e): continue
        alpha = min(1.0, (t - s) / 0.3, (e - t) / 0.3); dy = int(12 * (1 - ease((t - s) / 0.4)))
        im2 = im.copy(); im2.putalpha(Image.eval(im2.getchannel('A'), lambda v: int(v * alpha)))
        img.alpha_composite(im2, (int(cx - im.width / 2), int(cy - im.height / 2 + dy)))
    if t > TOTAL - 0.8:
        img.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - TOTAL + 0.8) / 0.8)))))
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
    put_music(0.0, DARK, 0.0, 0.55, fout=0.05)
    put_music(BOTH0, FRZ, DARK, 0.55, fin=0.3)
    
    put_music(AFTER, TOTAL, DARK + FRZ - BOTH0, 0.5, fin=0.4, fout=1.5)
    S = SFX.all_sfx()
    def fx(name, at, vol=1.0, maxdur=None):
        s = S[name]
        if maxdur: s = s[:int(maxdur * SR)]
        a = int(at * SR); n = min(len(s), N - a); out[a:a + n] += (s[:n] * vol)[:, None]
    fx('whoosh', 0.0, .5)
    for p_ in PUNCH: fx('boom', p_, .9)
    fx('scratch', 27.85, .6)
    crk = SFX.crickets(LIE1 - LIE0); a_ = int(LIE0 * SR); out[a_:a_ + len(crk)] += (crk * .5)[:, None]
    fx('scratch', DARK, .8); fx('boom', GHOST, .9); fx('sting', GHOST, .6); fx('sting', 18.9, .7); fx('sting', 22.9, .6)
    fx('scratch', FRZ, .8); fx('shutter', FRZ + 0.05, .6)
    fx('rewind', REW - 0.05, .7)
    fx('heart', RPL + 0.05, .85, maxdur=PUSH_T - RPL - 0.05)
    fx('boom', PUSH_T, 1.0)
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
