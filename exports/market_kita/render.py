import sys, os, math, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "in.mp4")
FPS = 30
SW, SH = 576, 1024
W, H = 1080, 1920
K = W / SW
NFR = 1574
FONTS = os.path.join(HERE, "fonts")
F_FUN = os.path.join(FONTS, "LuckiestGuy-Regular.ttf")
F_BLK = os.path.join(FONTS, "Poppins-Black.ttf")
F_XB = os.path.join(FONTS, "Poppins-ExtraBold.ttf")
F_EMO = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# ---------------------------------------------------------------- script
CAPS = [
    (0.0, 1.2, "Wisdom tooth out"), (1.2, 2.4, "Can't talk today"), (2.4, 3.45, "But Market Kita"),
    (3.45, 4.6, "needs a shoutout!"), (4.6, 6.4, "so I'm her voice today"), (6.6, 7.9, "Don't mess this up"),
    (7.9, 8.85, "Okay no pressure"), (9.1, 10.15, "Our young entrepreneurs"), (10.15, 11.15, "Are getting ready for"),
    (11.15, 12.15, "Market Kita"), (12.15, 12.9, "And MENDAKI is"), (12.9, 13.95, "helping them prepare"),
    (13.95, 14.95, "With a little guidance"), (14.95, 15.6, "From someone who's done it"),
    (16.0, 17.6, "First market don't do this"), (17.6, 18.45, "Yeah what she said"),
    (18.45, 19.45, "First market don't do this"), (19.45, 19.95, "Kak Haryani"), (19.95, 20.65, "3 things"),
    (20.65, 21.7, "not to do at your first market"), (22.15, 23.45, "Okay first is"),
    (23.45, 25.2, "don't leave your booth bare"), (25.4, 27.7, "tolonglah decorate yes?"), (27.7, 28.45, "Second"),
    (28.45, 29.45, "When you open your booth"), (29.45, 30.7, "don't go behind it"), (30.7, 31.2, "and play your phone"),
    (31.2, 32.45, "Thirdly"), (32.45, 33.95, "don't forget to market"), (33.95, 34.75, "for people to come"),
    (34.95, 35.95, "if they don't know you're"), (35.95, 37.45, "there nobody's gonna come"),
    (38.0, 41.45, "Come down to Market Kita"), (41.45, 42.45, "on 4th-6th December"), (42.45, 43.15, "at Scape!"),
    (43.15, 44.15, "Come and support"), (44.15, 45.15, "your young entrepreneurs"), (45.15, 46.65, "Bring your friends!"),
    (46.65, 47.45, "Yes you heard her!"), (47.45, 48.5, "Bring your friends!"),
]
KEYWORDS = {"MARKET", "KITA", "MENDAKI", "SHOUTOUT!", "DON'T", "BARE", "DECORATE", "PHONE", "THIRDLY", "SECOND",
            "FIRST", "FRIENDS!", "SCAPE!", "DECEMBER", "4TH-6TH", "NOBODY'S", "3", "PRESSURE", "TOOTH", "VOICE",
            "ENTREPRENEURS", "SUPPORT", "GUIDANCE", "MESS"}

# cut frame -> transition type
CUTS = {71: "punch", 106: ("whip", 1), 145: "glitch", 156: "punch", 188: ("whip", -1), 333: ("whip", 1),
        389: ("whip", -1), 425: "punch", 683: "punch", 832: "glitch", 949: "punch", 1195: ("whip", 1),
        1363: "punch", 1462: "spin"}
SEG_STARTS = [0, 33, 71, 106, 145, 156, 188, 277, 333, 389, 425, 480, 683, 832, 949, 1132, 1195, 1363, 1462]
ZOOM_ALT = {683: 1.13, 949: 1.13, 1363: 1.10, 1195: 1.0, 832: 1.0, 480: 1.0}
NAMETAG = (446, 662)

# stickers: (t0, t1, emoji, x, y, size)
STICKERS = [
    (0.05, 1.2, "🦷", 850, 760, 210), (1.25, 2.4, "🤐", 850, 760, 210), (2.45, 4.6, "📢", 215, 800, 230),
    (4.8, 6.4, "🎤", 860, 820, 200), (6.65, 7.9, "😬", 860, 800, 220), (7.95, 8.85, "😅", 220, 820, 210),
    (12.2, 13.95, "🤝", 860, 820, 190), (14.0, 15.55, "💡", 215, 820, 190), (17.62, 18.45, "😂", 880, 820, 180),
    (25.45, 27.7, "🎈", 870, 860, 190), (25.6, 27.7, "🎀", 200, 880, 170), (30.72, 31.2, "📱", 860, 860, 190),
    (32.5, 34.75, "📣", 200, 880, 190), (35.95, 37.45, "🦗", 860, 1330, 180), (36.3, 37.45, "🦗", 230, 1380, 140),
    (38.05, 41.45, "🛍️", 200, 790, 200), (41.5, 42.45, "DATE", 860, 800, 200), (42.5, 43.15, "📍", 210, 800, 200),
    (43.2, 45.1, "💪", 870, 800, 190), (45.2, 46.65, "🙌", 200, 800, 200), (46.7, 47.45, "👂", 870, 800, 190),
    (47.5, 48.6, "👯", 870, 800, 200),
]
SPARKLES = [(2.45, 3.45), (11.15, 12.15), (38.0, 39.6)]
SHAKES = [(6.6, 7.6, 7), (16.0, 16.35, 10), (22.2, 22.45, 9), (27.7, 27.95, 9), (31.2, 31.45, 9), (48.75, 49.0, 12)]
BADGES = [(22.2, 27.7, "#1"), (27.7, 31.2, "#2"), (31.2, 37.45, "#3")]
CHECK_ITEMS = [(23.5, "BARE BOOTH"), (29.5, "GLUED TO PHONE"), (32.5, "NO PROMO")]


# ---------------------------------------------------------------- helpers
def ease_back(x, s=1.9):
    x = min(max(x, 0.0), 1.0) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


@functools.lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


@functools.lru_cache(None)
def text_img(txt, path, size, fill, stroke=8, sfill=(0, 0, 0), shadow=True):
    f = font(path, size)
    bb = f.getbbox(txt, stroke_width=stroke)
    pad = 24
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    org = (pad - bb[0], pad - bb[1])
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((org[0] + 5, org[1] + 8), txt, font=f, fill=(0, 0, 0, 170), stroke_width=stroke,
                                stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(5)))
    ImageDraw.Draw(im).text(org, txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im


@functools.lru_cache(None)
def emoji_img(ch, size):
    f = font(F_EMO, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    # drop shadow + white rim
    pad = 20
    out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    a = im.split()[3]
    rim = Image.new("RGBA", out.size, (0, 0, 0, 0))
    rim.paste((255, 255, 255, 255), (pad, pad), a)
    rim = rim.filter(ImageFilter.MaxFilter(9))
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 140), (pad + 6, pad + 10), a)
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    out = Image.alpha_composite(shadow, rim)
    out.alpha_composite(im, (pad, pad))
    return out


def paste(canvas, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if abs(rot) > 0.05:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    canvas.alpha_composite(im, (max(0, x), max(0, y)),
                           (max(0, -x), max(0, -y)) + (min(im.width, W - x), min(im.height, H - y)))


def rrect_img(w, h, r, fill, outline=(0, 0, 0, 255), ow=6, shadow=True):
    pad = 26
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad + 6, pad + 10, pad + w + 6, pad + h + 10), r, fill=(0, 0, 0, 120))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill, outline=outline, width=ow)
    return im


def star_poly(cx, cy, r, rot=0, pts=4, inner=0.38):
    out = []
    for i in range(pts * 2):
        a = rot + i * math.pi / pts
        rr = r if i % 2 == 0 else r * inner
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out


# ---------------------------------------------------------------- caption layout
CAP_SIZE = 84
CAP_Y = 1060


@functools.lru_cache(None)
def layout(idx):
    s, e, txt = CAPS[idx]
    words = txt.upper().split()
    f = font(F_FUN, CAP_SIZE)
    sp = f.getlength(" ") + 6
    widths = [f.getlength(w) for w in words]
    lines, cur, cw = [], [], 0
    for i, w in enumerate(words):
        add = widths[i] + (sp if cur else 0)
        if cur and cw + add > 930:
            lines.append(cur); cur, cw = [], 0; add = widths[i]
        cur.append(i); cw += add
    lines.append(cur)
    lh = 104
    pos = {}
    for li, ln in enumerate(lines):
        tw = sum(widths[i] for i in ln) + sp * (len(ln) - 1)
        x = W / 2 - tw / 2
        y = CAP_Y + (li - (len(lines) - 1) / 2) * lh
        for i in ln:
            pos[i] = (x + widths[i] / 2, y)
            x += widths[i] + sp
    n = len(words)
    step = min((e - s) * 0.7 / n, 0.2)
    times = [s + i * step for i in range(n)]
    return words, widths, pos, times


def draw_captions(cv, t):
    for idx, (s, e, _) in enumerate(CAPS):
        if not (s <= t < e):
            continue
        words, widths, pos, times = layout(idx)
        out_k = min(1.0, (e - t) / 0.1)  # quick exit
        active = max(i for i in range(len(words)) if times[i] <= t)
        for i, w in enumerate(words):
            if t < times[i]:
                continue
            p = (t - times[i]) / 0.16
            sc = ease_back(p) * (0.85 + 0.15 * out_k)
            dy = -18 * math.sin(min(p, 1) * math.pi) if p < 1 else 0
            cx, cy = pos[i]
            key = w.strip(",.?") in KEYWORDS or w in KEYWORDS
            if i == active:
                pill = rrect_img(int(widths[i]) + 34, CAP_SIZE + 16, 22, (255, 61, 127, 255), ow=6, shadow=False)
                paste(cv, pill, cx, cy + 2 + dy, sc * 1.08, rot=2.5, alpha=out_k)
                im = text_img(w, F_FUN, CAP_SIZE, (255, 255, 255), 8)
                paste(cv, im, cx, cy + dy - 4, sc * 1.1, rot=2.5, alpha=out_k)
            else:
                col = (183, 255, 59) if key else (255, 255, 255)
                im = text_img(w, F_FUN, CAP_SIZE, col, 8)
                paste(cv, im, cx, cy + dy, sc, alpha=out_k)


# ---------------------------------------------------------------- other gfx
@functools.lru_cache(None)
def date_sticker():
    a = text_img("4-6", F_FUN, 92, (230, 40, 60), 0, shadow=False)
    b = text_img("DEC", F_FUN, 64, (20, 20, 20), 0, shadow=False)
    im = rrect_img(210, 200, 30, (255, 255, 255, 255), ow=8)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((26, 26, 236, 80), 26, fill=(230, 40, 60, 255))
    im.alpha_composite(a, (int(im.width / 2 - a.width / 2), 62))
    im.alpha_composite(b, (int(im.width / 2 - b.width / 2), 140))
    return im


def draw_stickers(cv, t):
    for i, (s, e, ch, x, y, sz) in enumerate(STICKERS):
        if not (s <= t < e):
            continue
        p = (t - s) / 0.25
        sc = ease_back(p, 2.6)
        q = (e - t) / 0.15
        if q < 1:
            sc *= ease_out(q)
        rot = 9 * math.sin((t - s) * 7 + i) + (1 - min(p, 1)) * -40
        fy = 10 * math.sin((t - s) * 5 + i)
        paste(cv, date_sticker() if ch == "DATE" else emoji_img(ch, sz), x, y + fy, sc, rot)


def draw_sparkles(cv, t):
    d = ImageDraw.Draw(cv)
    for s, e in SPARKLES:
        if not (s <= t < e):
            continue
        r = np.random.default_rng(int(s * 100))
        for k in range(10):
            ph = r.uniform(0, 1)
            x = r.uniform(80, 1000); y = CAP_Y + r.choice([-1, 1]) * r.uniform(90, 230)
            life = ((t - s) * 2.2 + ph) % 1.0
            rr = 34 * math.sin(life * math.pi) * r.uniform(0.6, 1.2)
            if rr < 2:
                continue
            col = [(255, 230, 60, 255), (255, 255, 255, 255), (183, 255, 59, 255)][k % 3]
            d.polygon(star_poly(x, y, rr, rot=life * 2), fill=col, outline=(0, 0, 0, 255), width=3)


@functools.lru_cache(None)
def banner_img(txt):
    f = font(F_FUN, 70)
    lines = txt.split("\n")
    tw = max(f.getlength(l) for l in lines)
    w, h = int(tw + 90), 95 * len(lines) + 40
    im = rrect_img(w, h, 26, (255, 214, 10, 255), ow=8)
    for i, l in enumerate(lines):
        ti = text_img(l, F_FUN, 70, (20, 20, 20), 0, shadow=False)
        im.alpha_composite(ti, (int(im.width / 2 - ti.width / 2), int(26 + 20 + i * 95 + 47 - ti.height / 2)))
    return im


def draw_banner(cv, t):
    if 16.0 <= t < 21.9:
        txt = "FIRST MARKET?\nDON'T DO THIS!" if t < 19.95 else "3 THINGS\nNOT TO DO!"
        s0 = 16.0 if t < 19.95 else 19.95
        p = (t - s0) / 0.3
        sc = ease_back(p, 2.2) * (1 + 0.025 * math.sin(t * 8))
        if t > 21.6:
            sc *= ease_out((21.9 - t) / 0.3)
        paste(cv, banner_img(txt), 540, 300, sc, rot=-4)
        e = emoji_img("🚫", 120)
        paste(cv, e, 540 + banner_img(txt).width / 2 - 30, 210, ease_back((t - s0 - 0.15) / 0.3, 2.6) * sc, rot=12)


@functools.lru_cache(None)
def nametag_imgs():
    a = text_img("KAK HARYANI OTHMAN", F_BLK, 50, (255, 255, 255), 0, shadow=False)
    pa = rrect_img(a.width + 10, 84, 42, (255, 61, 127, 255), ow=6)
    pa.alpha_composite(a, (int(pa.width / 2 - a.width / 2), int(pa.height / 2 - a.height / 2) - 4))
    b = text_img("Founder · MakBesar Pte Ltd", F_XB, 36, (20, 20, 20), 0, shadow=False)
    pb = rrect_img(b.width + 10, 62, 31, (183, 255, 59, 255), ow=5)
    pb.alpha_composite(b, (int(pb.width / 2 - b.width / 2), int(pb.height / 2 - b.height / 2) - 3))
    return pa, pb


def draw_nametag(cv, t):
    s, e = 16.05, 21.75
    if not (s <= t < e):
        return
    pa, pb = nametag_imgs()
    pin = ease_back((t - s) / 0.4, 1.6)
    pin2 = ease_back((t - s - 0.12) / 0.4, 1.6)
    pout = ease_out((e - t) / 0.3) if t > e - 0.3 else 1
    x1 = -pa.width / 2 + (50 + pa.width) * pin * pout
    x2 = -pb.width / 2 + (90 + pb.width) * pin2 * pout
    paste(cv, pa, x1 - pa.width / 2 + pa.width / 2, 1250, rot=-2)
    paste(cv, pb, x2 - pb.width / 2 + pb.width / 2, 1335, rot=-2)
    e_ = emoji_img("👩‍💼" if False else "⭐", 70)
    paste(cv, e_, x1 + pa.width / 2 - 10, 1210, ease_back((t - s - 0.4) / 0.3, 2.6) * pout, rot=20 * math.sin(t * 4))


@functools.lru_cache(None)
def check_header():
    a = text_img("FIRST MARKET DON'TS", F_FUN, 44, (255, 255, 255), 0, shadow=False)
    im = rrect_img(560, 76, 20, (230, 40, 60, 255), ow=6)
    im.alpha_composite(a, (int(im.width / 2 - a.width / 2) + 30, int(im.height / 2 - a.height / 2)))
    e = emoji_img("🚫", 58)
    im.alpha_composite(e, (36, int(im.height / 2 - e.height / 2)))
    return im


@functools.lru_cache(None)
def check_item(i, txt):
    im = rrect_img(560, 66, 18, (255, 255, 255, 240), ow=5)
    n = text_img(f"{i + 1}.", F_FUN, 40, (230, 40, 60), 0, shadow=False)
    a = text_img(txt, F_BLK, 36, (25, 25, 25), 0, shadow=False)
    im.alpha_composite(n, (40, int(im.height / 2 - n.height / 2) + 2))
    im.alpha_composite(a, (88, int(im.height / 2 - a.height / 2) - 2))
    return im


def draw_checklist(cv, t, fr):
    s, e = 22.15, 37.45
    if not (s <= t < e):
        return
    pin = ease_back((t - s) / 0.35, 1.5)
    pout = ease_out((e - t) / 0.35) if t > e - 0.35 else 1
    off = (1 - pin * pout) * -700
    h = check_header()
    paste(cv, h, 30 + h.width / 2 + off, 180, rot=-2)
    d = ImageDraw.Draw(cv)
    for i, (ti, txt) in enumerate(CHECK_ITEMS):
        if t < ti:
            continue
        p = ease_back((t - ti) / 0.3, 2.0)
        im = check_item(i, txt)
        cx, cy = 40 + im.width / 2 + off + (1 - p) * -200, 262 + i * 76
        paste(cv, im, cx, cy, max(p, 0.01) if p < 1 else 1, rot=-2)
        # red X stamp
        q = (t - ti - 0.35) / 0.2
        if q > 0:
            x0 = cx + im.width / 2 - 8
            ex = emoji_img("❌", 54)
            paste(cv, ex, x0, cy - 3, ease_back(q, 3.0) * (1 + 1.2 * max(0, 1 - q)), rot=-10)


@functools.lru_cache(None)
def badge_img(txt):
    sz = 300
    im = Image.new("RGBA", (sz + 40, sz + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((28, 32, 28 + sz - 16, 32 + sz - 16), fill=(0, 0, 0, 130))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im)
    d.polygon(star_poly(im.width / 2, im.height / 2, sz / 2 - 4, rot=0.2, pts=14, inner=0.84), fill=(255, 214, 10, 255),
              outline=(0, 0, 0, 255), width=8)
    ti = text_img(txt, F_FUN, 130, (230, 40, 60), 9, (0, 0, 0), shadow=False)
    im.alpha_composite(ti, (int(im.width / 2 - ti.width / 2), int(im.height / 2 - ti.height / 2) + 6))
    return im


def draw_badges(cv, t):
    for s, e, txt in BADGES:
        if not (s <= t < e):
            continue
        p = (t - s) / 0.22
        sc = 1 + 1.6 * (1 - ease_out(p)) if p < 1 else 1 + 0.04 * math.sin((t - s) * 6)
        q = (e - t) / 0.15
        if q < 1:
            sc *= ease_out(q)
        rot = -14 + 8 * math.sin((t - s) * 3)
        paste(cv, badge_img(txt), 880, 330, sc * 0.82, rot, alpha=min(1, p * 2 + 0.2))


# confetti
_cr = np.random.default_rng(3)
CONF_COLS = [(255, 61, 127), (183, 255, 59), (255, 214, 10), (77, 200, 255), (255, 140, 0), (255, 255, 255)]


def make_confetti(t0, n, origin, spread):
    ps = []
    for _ in range(n):
        if origin == "top":
            x, y = _cr.uniform(-50, W + 50), _cr.uniform(-400, -20)
            vx, vy = _cr.uniform(-80, 80), _cr.uniform(250, 520)
        else:
            side = origin
            x = -20 if side == "left" else W + 20
            y = 1500
            ang = _cr.uniform(-75, -45) if side == "left" else _cr.uniform(-135, -105)
            sp = _cr.uniform(1300, 2300)
            vx, vy = sp * math.cos(math.radians(ang)), sp * math.sin(math.radians(ang))
        ps.append(dict(t0=t0 + _cr.uniform(0, spread), x=x, y=y, vx=vx, vy=vy, w=_cr.uniform(14, 26),
                       h=_cr.uniform(8, 14), r=_cr.uniform(0, 6.28), vr=_cr.uniform(-9, 9),
                       c=CONF_COLS[_cr.integers(len(CONF_COLS))], ph=_cr.uniform(0, 6.28)))
    return ps


CONFETTI = (make_confetti(48.75, 110, "left", 0.15) + make_confetti(48.75, 110, "right", 0.15)
            + make_confetti(49.1, 160, "top", 3.0) + make_confetti(38.0, 60, "left", 0.1)
            + make_confetti(38.0, 60, "right", 0.1))


def draw_confetti(cv, t):
    d = ImageDraw.Draw(cv)
    for p in CONFETTI:
        dt = t - p["t0"]
        if dt < 0 or dt > 4.5:
            continue
        drag = math.exp(-1.6 * dt)
        x = p["x"] + p["vx"] * (1 - drag) / 1.6 + 40 * math.sin(dt * 4 + p["ph"])
        y = p["y"] + p["vy"] * (1 - drag) / 1.6 + 380 * dt * dt * 0.5
        if y > H + 40 or y < -450:
            continue
        r = p["r"] + p["vr"] * dt
        fl = abs(math.cos(dt * 7 + p["ph"]))
        w, h = p["w"], p["h"] * (0.25 + 0.75 * fl)
        cs, sn = math.cos(r), math.sin(r)
        pts = [(x + a * cs - b * sn, y + a * sn + b * cs) for a, b in
               [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]]
        d.polygon(pts, fill=p["c"] + (255,))


@functools.lru_cache(None)
def end_imgs():
    a = text_img("SEE YOU THERE!", F_FUN, 92, (20, 20, 20), 0, shadow=False)
    pa = rrect_img(a.width + 60, 130, 40, (183, 255, 59, 255), ow=8)
    pa.alpha_composite(a, (int(pa.width / 2 - a.width / 2), int(pa.height / 2 - a.height / 2) + 4))
    b = text_img("SAVE THE DATE!", F_FUN, 72, (255, 255, 255), 8)
    return pa, b


def draw_end(cv, t):
    s = 48.95
    if t < s:
        return
    pa, b = end_imgs()
    paste(cv, b, 540, 150, ease_back((t - s) / 0.35, 2.2) * (1 + 0.03 * math.sin(t * 7)), rot=-3)
    paste(cv, emoji_img("🛍️", 110), 540 + b.width / 2 + 60, 140, ease_back((t - s - 0.2) / 0.3, 2.6),
          rot=15 * math.sin(t * 5))
    paste(cv, emoji_img("🎉", 110), 540 - b.width / 2 - 60, 140, ease_back((t - s - 0.25) / 0.3, 2.6),
          rot=-15 * math.sin(t * 5))
    s2 = 49.3
    sc = ease_back((t - s2) / 0.35, 2.2) * (1 + 0.05 * abs(math.sin((t - s2) * 4.5)))
    paste(cv, pa, 540, 1775 - 18 * abs(math.sin((t - s2) * 4.5)), sc, rot=2)


def draw_progress(cv, t):
    d = ImageDraw.Draw(cv)
    w = int(W * t / (NFR / FPS))
    d.rectangle((0, 0, W, 9), fill=(0, 0, 0, 90))
    d.rectangle((0, 0, w, 9), fill=(183, 255, 59, 255))


# ---------------------------------------------------------------- frame processing
def cap_active(t):
    return any(s - 0.05 <= t < e + 0.05 for s, e, _ in CAPS)


def clean(fr, n):
    t = n / FPS
    m = np.zeros(fr.shape[:2], np.uint8)
    if cap_active(t):
        b = fr[528:596].astype(np.int16)
        mn, mx = b.min(2), b.max(2)
        m[528:596] = ((mn > 222) & (mx - mn < 36)).astype(np.uint8)
    if NAMETAG[0] <= n <= NAMETAG[1]:
        b = fr[588:700].astype(np.int16)
        m[588:700] |= ((b[..., 2] > 170) & (b[..., 1] > 150) & (b[..., 0] < 140) & (b[..., 2] - b[..., 0] > 70)).astype(np.uint8)
    if not m.any():
        return fr
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    m = m | np.roll(np.roll(m, 3, 0), 2, 1)
    y0 = 500
    roi = fr[y0:720].copy()
    roi = cv2.inpaint(roi, m[y0:720], 5, cv2.INPAINT_TELEA)
    fr = fr.copy(); fr[y0:720] = roi
    return fr


_x = np.arange(256) / 255.0
LUT = np.clip((0.72 * _x + 0.28 * (0.5 - 0.5 * np.cos(np.pi * _x))) * 255 * 1.02, 0, 255).astype(np.uint8)


def grade(img):
    img = cv2.LUT(img, LUT)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv[..., 1] = cv2.LUT(hsv[..., 1], np.clip(np.arange(256) * 1.14, 0, 255).astype(np.uint8))
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def seg_of(n):
    s = 0
    for st in SEG_STARTS:
        if st <= n:
            s = st
    nxt = [x for x in SEG_STARTS if x > n]
    return s, (nxt[0] if nxt else NFR)


def shake_at(t):
    for s, e, a in SHAKES:
        if s <= t < e:
            k = 1 - (t - s) / (e - s)
            return a * k * math.sin(t * 91), a * k * math.cos(t * 73)
    return 0.0, 0.0


def process(fr, n):
    t = n / FPS
    fr = clean(fr, n)
    img = cv2.resize(fr, (W, H), interpolation=cv2.INTER_LANCZOS4)
    bl = cv2.GaussianBlur(img, (0, 0), 1.3)
    img = cv2.addWeighted(img, 1.45, bl, -0.45, 0)
    img = grade(img)

    s0, s1 = seg_of(n)
    z = ZOOM_ALT.get(s0, 1.0) + 0.035 * (n - s0) / max(1, s1 - s0)
    if n < 8:
        z += 0.3 * (1 - ease_out(n / 8))
    dx = dy = 0.0
    rot = 0.0
    blurL = 0
    rgb = 0
    flash = 0.0
    slices = False
    for c, typ in CUTS.items():
        k = n - c
        if typ == "punch" and 0 <= k < 8:
            z += 0.2 * math.exp(-0.6 * k); flash = max(flash, 0.45 * math.exp(-1.0 * k))
        elif isinstance(typ, tuple):
            d = typ[1]
            if -3 <= k < 0:
                p = (k + 4) / 3
                dx -= d * W * 0.4 * p * p; blurL = max(blurL, int(20 + 90 * p))
            elif 0 <= k < 5:
                p = 1 - k / 5
                dx += d * W * 0.4 * p * p; blurL = max(blurL, int(90 * p))
        elif typ == "glitch" and -2 <= k < 5:
            rgb = max(rgb, int(28 * (1 - abs(k) / 5))); slices = True
        elif typ == "spin" and 0 <= k < 14:
            p = (1 - k / 14) ** 3
            rot += 35 * p; z += 0.9 * p; flash = max(flash, 0.9 * math.exp(-0.8 * k))
    # dramatic crickets push-in
    if 35.95 <= t < 37.5:
        z *= 1 + 0.18 * ease_out((t - 35.95) / 1.5)
    # end-card breathing
    if t >= 49.2:
        z *= 1 + 0.015 * math.sin((t - 49.2) * 2.5)
    sx, sy = shake_at(t)
    dx += sx; dy += sy
    ax, ay = (540, 760) if n < 1462 else (540, 960)
    M = cv2.getRotationMatrix2D((ax, ay), rot, z)
    M[0, 2] += dx; M[1, 2] += dy
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    if blurL > 2:
        kk = np.zeros((1, blurL), np.float32); kk[:] = 1.0 / blurL
        img = cv2.filter2D(img, -1, kk)
    if rot > 1:
        img = cv2.GaussianBlur(img, (0, 0), rot / 4)
    if rgb:
        img[..., 0] = np.roll(img[..., 0], rgb, 1)
        img[..., 2] = np.roll(img[..., 2], -rgb, 1)
        if slices:
            r = np.random.default_rng(n)
            for _ in range(6):
                y = r.integers(0, H - 120); h = r.integers(20, 120)
                img[y:y + h] = np.roll(img[y:y + h], int(r.integers(-80, 80)), 1)
    if 35.95 <= t < 37.5:  # desaturate + vignette for "nobody's gonna come"
        p = ease_out((t - 35.95) / 0.6)
        g = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        img = cv2.addWeighted(img, 1 - 0.75 * p, g, 0.75 * p, 0)
        img = (img * VIG[..., None] ** p).astype(np.uint8)
    if flash > 0.01:
        img = cv2.addWeighted(img, 1 - flash, np.full_like(img, 255), flash, 0)

    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_confetti(cv, t) if t < 45 else None
    draw_checklist(cv, t, n)
    draw_badges(cv, t)
    draw_banner(cv, t)
    draw_nametag(cv, t)
    draw_sparkles(cv, t)
    draw_stickers(cv, t)
    draw_captions(cv, t)
    if t >= 45:
        draw_confetti(cv, t)
    draw_end(cv, t)
    draw_progress(cv, t)
    ov = np.asarray(cv)
    a = ov[..., 3:4].astype(np.float32) / 255.0
    rgbov = ov[..., 2::-1].astype(np.float32)
    img = (img.astype(np.float32) * (1 - a) + rgbov * a).astype(np.uint8)
    return img


_yy, _xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1.15 - 0.75 * (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) ** 1.2 * 0.6, 0.25, 1).astype(np.float32)


def read_frames(a, b):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"select='between(n\\,{a}\\,{b - 1})'",
                          "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    sz = SW * SH * 3
    for n in range(a, b):
        buf = p.stdout.read(sz)
        if len(buf) < sz:
            break
        yield n, np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
    p.stdout.close(); p.wait()


def render_chunk(a, b, out):
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                            "-pix_fmt", "yuv420p", "-profile:v", "high", "-x264-params", "keyint=60", out],
                           stdin=subprocess.PIPE)
    for n, fr in read_frames(a, b):
        enc.stdin.write(process(fr, n).tobytes())
        if n % 50 == 0:
            print(f"chunk {a}: frame {n}", flush=True)
    enc.stdin.close(); enc.wait()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        ts = [float(x) for x in sys.argv[2].split(",")]
        outdir = os.path.join(HERE, "prev"); os.makedirs(outdir, exist_ok=True)
        for t in ts:
            n = int(round(t * FPS))
            fr = next(read_frames(n, n + 1))[1]
            img = process(fr, n)
            cv2.imwrite(os.path.join(outdir, f"p_{t:06.2f}.jpg"), cv2.resize(img, (360, 640)), [cv2.IMWRITE_JPEG_QUALITY, 85])
    elif mode == "chunk":
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
