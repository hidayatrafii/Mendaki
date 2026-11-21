"""Market Kita callout video: Poppins captions, youth-fun but refined GFX, TikTok/Reels safe zones."""
import sys, os, math, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from render import ease_back, ease_out, font, text_img, emoji_img, paste as _paste, rrect_img, star_poly  # noqa


def paste(canvas, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    """Skip graphics that are entirely off-canvas (e.g. mid slide-out) instead of crashing."""
    hw, hh = im.width * max(scale, 0) / 2 + 40, im.height * max(scale, 0) / 2 + 40
    if cx + hw < 0 or cx - hw > 1080 or cy + hh < 0 or cy - hh > 1920:
        return
    _paste(canvas, im, cx, cy, scale, rot, alpha)

SRC = os.path.join(HERE, "in.mov")
FPS = 30
W, H = 1080, 1920
NFR = 1573
FT = "/home/user/Mendaki/exports/assets/fonts"
P6, P7, P8, P9 = (os.path.join(FT, f"Poppins-{w}.ttf") for w in (600, 700, 800, 900))

# Safe zone for TikTok + Instagram Reels (1080x1920): keep text/graphics inside this box
SAFE = dict(left=72, right=940, top=270, bottom=1480)

GREEN = (38, 98, 58)
LIME = (200, 240, 90)
CREAM = (255, 246, 223)
PINK = (242, 92, 138)
INK = (22, 30, 24)

# ---------------------------------------------------------------- script (times on the original edit's clock)
CAPS = [
    (0.0, 1.2, "Wisdom tooth out"), (1.2, 2.4, "Can't talk today"), (2.4, 3.45, "But Market Kita"),
    (3.45, 4.6, "needs a shoutout!"), (4.6, 6.4, "so I'm her voice today"), (6.6, 7.9, "Don't mess this up"),
    (7.9, 8.85, "Okay, no pressure"), (9.1, 10.15, "Our young entrepreneurs"), (10.15, 11.15, "are getting ready for"),
    (11.15, 12.15, "Market Kita"), (12.15, 12.9, "and MENDAKI is"), (12.9, 13.95, "helping them prepare"),
    (13.95, 14.95, "with a little guidance"), (14.95, 15.6, "from someone who's done it"),
    (16.0, 17.6, "First market? Don't do this"), (17.6, 18.45, "Yeah, what she said"),
    (18.45, 19.45, "First market? Don't do this"), (19.45, 19.95, "Kak Haryani"), (19.95, 20.65, "3 things"),
    (20.65, 21.7, "not to do at your first market"), (22.15, 23.45, "Okay, first is"),
    (23.45, 25.2, "don't leave your booth bare"), (25.4, 27.7, "tolonglah decorate, yes?"), (27.7, 28.45, "Second,"),
    (28.45, 29.45, "when you open your booth"), (29.45, 30.7, "don't go behind it"), (30.7, 31.2, "and play your phone"),
    (31.2, 32.45, "Thirdly,"), (32.45, 33.95, "don't forget to market"), (33.95, 34.75, "for people to come"),
    (34.95, 35.95, "if they don't know you're there,"), (35.95, 37.45, "nobody's gonna come"),
    (38.0, 41.45, "Come down to Market Kita"), (41.45, 42.45, "on 4th–6th December"), (42.45, 43.15, "at *SCAPE!"),
    (43.15, 44.15, "Come and support"), (44.15, 45.15, "your young entrepreneurs"), (45.15, 46.65, "Bring your friends!"),
    (46.65, 47.45, "Yes, you heard her!"), (47.45, 48.5, "Bring your friends!"),
]
BRAND = {"Market", "Kita", "MENDAKI", "*SCAPE!", "Kita!"}
CUTS = {71: "punch", 106: ("whip", 1), 145: "leak", 156: "punch", 188: ("whip", -1), 333: ("whip", 1),
        389: ("whip", -1), 425: "punch", 683: "punch", 832: "leak", 949: "punch", 1195: ("whip", 1),
        1363: "punch", 1462: "spin"}
SEG_STARTS = [0, 33, 71, 106, 145, 156, 188, 277, 333, 389, 425, 480, 683, 832, 949, 1132, 1195, 1363, 1462]
ZOOM_ALT = {683: 1.1, 949: 1.1, 1363: 1.08}
NAMETAG = (440, 668)
STICKERS = [  # (t0, t1, emoji, x, y, size) -- x kept <= ~840 for the right-hand UI column
    (0.05, 1.2, "🦷", 820, 860, 150), (1.25, 2.4, "🤐", 820, 860, 150), (2.45, 4.6, "📢", 200, 880, 160),
    (4.8, 6.4, "🎤", 820, 880, 140), (6.65, 7.9, "😬", 820, 880, 150), (7.95, 8.85, "😅", 210, 900, 150),
    (12.2, 13.95, "🤝", 820, 900, 140), (14.0, 15.55, "💡", 200, 900, 140), (17.62, 18.45, "😂", 820, 880, 140),
    (25.45, 27.7, "🎈", 820, 900, 140), (25.6, 27.7, "🎀", 200, 920, 120), (30.72, 31.2, "📱", 820, 900, 140),
    (32.5, 34.75, "📣", 200, 920, 140), (35.95, 37.45, "🦗", 800, 1360, 120), (36.3, 37.45, "🦗", 240, 1390, 100),
    (38.05, 41.45, "🛍️", 200, 880, 150), (43.2, 45.1, "💪", 820, 880, 140), (45.2, 46.65, "🙌", 200, 880, 150),
    (46.7, 47.45, "👂", 820, 880, 140), (47.5, 48.6, "👯", 820, 880, 150),
]
SPARKLES = [(2.45, 3.45), (11.15, 12.15), (38.0, 39.6)]
SHAKES = [(6.6, 7.2, 4), (16.0, 16.25, 5), (48.75, 48.95, 6)]
BADGES = [(22.2, 27.7, "1"), (27.7, 31.2, "2"), (31.2, 37.45, "3")]
CHECK_ITEMS = [(23.5, "Bare booth"), (29.5, "Glued to your phone"), (32.5, "No promo")]
INFO = [(41.5, "4 – 6 DEC", "📅"), (42.5, "*SCAPE Camping Ground", "📍"), (43.2, "12PM – 9.30PM", "🕛")]

# ---------------------------------------------------------------- captions: Poppins, word-by-word, refined
CAP_SIZE = 64
CAP_Y = 1150
CAP_MAXW = SAFE["right"] - SAFE["left"] - 40


@functools.lru_cache(None)
def word_img(w, col):
    f = font(P8, CAP_SIZE)
    st = 4
    bb = f.getbbox(w, stroke_width=st)
    pad = 22
    sz = (bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2)
    org = (pad - bb[0], pad - bb[1])
    sh = Image.new("RGBA", sz, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((org[0] + 2, org[1] + 5), w, font=f, fill=(0, 0, 0, 150), stroke_width=st + 2,
                            stroke_fill=(0, 0, 0, 150))
    im = sh.filter(ImageFilter.GaussianBlur(6))
    if col != (255, 255, 255):  # soft glow behind highlighted words
        gl = Image.new("RGBA", sz, (0, 0, 0, 0))
        ImageDraw.Draw(gl).text(org, w, font=f, fill=col + (150,), stroke_width=st + 6, stroke_fill=col + (110,))
        im = Image.alpha_composite(im, gl.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).text(org, w, font=f, fill=col, stroke_width=st, stroke_fill=INK + (255,))
    return im


@functools.lru_cache(None)
def layout(idx):
    s, e, txt = CAPS[idx]
    words = txt.split()
    f = font(P8, CAP_SIZE)
    sp = f.getlength(" ") + 4
    widths = [f.getlength(w) for w in words]
    lines, cur, cw = [], [], 0
    for i, w in enumerate(words):
        add = widths[i] + (sp if cur else 0)
        if cur and cw + add > CAP_MAXW:
            lines.append(cur); cur, cw = [], 0; add = widths[i]
        cur.append(i); cw += add
    lines.append(cur)
    pos = {}
    cx0 = (SAFE["left"] + SAFE["right"]) / 2
    for li, ln in enumerate(lines):
        tw = sum(widths[i] for i in ln) + sp * (len(ln) - 1)
        x = cx0 - tw / 2
        y = CAP_Y + (li - (len(lines) - 1) / 2) * 84
        for i in ln:
            pos[i] = (x + widths[i] / 2, y); x += widths[i] + sp
    step = min((e - s) * 0.7 / len(words), 0.2)
    return words, pos, [s + i * step for i in range(len(words))]


def draw_captions(cv, t):
    for idx, (s, e, _) in enumerate(CAPS):
        if not (s <= t < e):
            continue
        words, pos, times = layout(idx)
        out_k = min(1.0, (e - t) / 0.08)
        active = max(i for i in range(len(words)) if times[i] <= t)
        for i, w in enumerate(words):
            if t < times[i]:
                continue
            p = (t - times[i]) / 0.18
            cx, cy = pos[i]
            col = LIME if (i == active or w in BRAND) else (255, 255, 255)
            sc = (0.8 + 0.2 * ease_back(p, 1.6)) * (1.06 if i == active else 1.0)
            paste(cv, word_img(w, col), cx, cy + 14 * (1 - ease_out(p)), sc, alpha=min(1, p * 2) * out_k)


# ---------------------------------------------------------------- gfx
@functools.lru_cache(None)
def chip(txt, icon=None, size=34, fill=GREEN, tcol=CREAM, border=LIME, weight=P8):
    a = text_img(txt, weight, size, tcol, 0, shadow=False)
    ic = emoji_img(icon, int(size * 1.35)) if icon else None
    iw = ic.width - 26 if ic else 0
    h = int(size * 1.95)
    im = rrect_img(a.width - 30 + iw + 64, h, h // 2, fill + (245,), outline=border + (255,), ow=5)
    x = 56
    if ic:
        im.alpha_composite(ic, (x - 18, int(im.height / 2 - ic.height / 2))); x += iw
    im.alpha_composite(a, (x - 22, int(im.height / 2 - a.height / 2) - 2))
    return im


def inout(t, s, e, din=0.35, dout=0.25, k=1.5):
    if not (s <= t < e):
        return 0.0
    v = ease_back((t - s) / din, k)
    return v * ease_out((e - t) / dout) if t > e - dout else v


def draw_stickers(cv, t):
    for i, (s, e, ch, x, y, sz) in enumerate(STICKERS):
        sc = inout(t, s, e, 0.25, 0.12, 2.0)
        if sc:
            paste(cv, emoji_img(ch, sz), x, y + 7 * math.sin((t - s) * 5 + i), sc, 6 * math.sin((t - s) * 5 + i))


def draw_sparkles(cv, t):
    d = ImageDraw.Draw(cv)
    for s, e in SPARKLES:
        if not (s <= t < e):
            continue
        r = np.random.default_rng(int(s * 100))
        for k in range(9):
            ph = r.uniform(0, 1)
            x = r.uniform(SAFE["left"] + 20, SAFE["right"] - 20)
            y = CAP_Y + r.choice([-1, 1]) * r.uniform(80, 170)
            life = ((t - s) * 2.0 + ph) % 1.0
            rr = 22 * math.sin(life * math.pi) * r.uniform(0.6, 1.2)
            if rr > 2:
                d.polygon(star_poly(x, y, rr, rot=life * 2), fill=[LIME + (255,), CREAM + (255,), (255, 214, 10, 255)][k % 3])


@functools.lru_cache(None)
def banner_img(l1, l2):
    a = text_img(l1, P7, 40, GREEN, 0, shadow=False)
    b = text_img(l2, P9, 62, INK, 0, shadow=False)
    w = max(a.width, b.width) + 30
    im = rrect_img(w, 150, 34, CREAM + (250,), outline=LIME + (255,), ow=6)
    im.alpha_composite(a, (int(im.width / 2 - a.width / 2), 26 + 6))
    im.alpha_composite(b, (int(im.width / 2 - b.width / 2), 26 + 54))
    return im


def draw_banner(cv, t):
    if 16.0 <= t < 21.9:
        first = t < 19.95
        s0 = 16.0 if first else 19.95
        im = banner_img("First market?", "DON'T DO THIS!") if first else banner_img("Kak Haryani's", "3 THINGS NOT TO DO")
        sc = ease_back((t - s0) / 0.35, 1.6)
        if t > 21.6:
            sc *= ease_out((21.9 - t) / 0.3)
        cx = (SAFE["left"] + SAFE["right"]) / 2
        paste(cv, im, cx, SAFE["top"] + 95, sc, rot=-2)
        paste(cv, emoji_img("🚫", 80), cx + im.width / 2 - 40, SAFE["top"] + 30, ease_back((t - s0 - .2) / .3, 2) * sc, 10)


@functools.lru_cache(None)
def nametag_imgs():
    a = text_img("Kak Haryani Othman", P8, 46, (255, 255, 255), 0, shadow=False)
    pa = rrect_img(a.width + 20, 80, 40, PINK + (255,), outline=(255, 255, 255, 255), ow=5)
    pa.alpha_composite(a, (int(pa.width / 2 - a.width / 2), int(pa.height / 2 - a.height / 2) - 3))
    b = text_img("Founder, MakBesar Pte Ltd", P7, 32, INK, 0, shadow=False)
    pb = rrect_img(b.width + 10, 58, 29, LIME + (255,), outline=INK + (255,), ow=4)
    pb.alpha_composite(b, (int(pb.width / 2 - b.width / 2), int(pb.height / 2 - b.height / 2) - 2))
    return pa, pb


def draw_nametag(cv, t):
    s, e = 14.25, 21.75
    if not (s <= t < e):
        return
    pa, pb = nametag_imgs()
    out = ease_out((e - t) / 0.3) if t > e - 0.3 else 1
    p1 = ease_back((t - s) / 0.45, 1.4) * out
    p2 = ease_back((t - s - 0.12) / 0.45, 1.4) * out
    L = SAFE["left"]
    paste(cv, pa, -pa.width / 2 + (L - 26 + pa.width) * p1, 1300, rot=-2)
    paste(cv, pb, -pb.width / 2 + (L + 10 + pb.width) * p2, 1378, rot=-2)
    paste(cv, emoji_img("✨", 56), L - 26 + pa.width * p1 + 10 - pa.width / 2 + pa.width / 2 - 20, 1262,
          ease_back((t - s - 0.45) / 0.3, 2) * out, 15 * math.sin(t * 3))


@functools.lru_cache(None)
def check_header():
    a = text_img("First market DON'Ts", P8, 34, CREAM, 0, shadow=False)
    e = emoji_img("🚫", 46)
    im = rrect_img(a.width + e.width + 30, 70, 35, GREEN + (250,), outline=LIME + (255,), ow=5)
    im.alpha_composite(e, (34, int(im.height / 2 - e.height / 2)))
    im.alpha_composite(a, (34 + e.width - 8, int(im.height / 2 - a.height / 2) - 2))
    return im


@functools.lru_cache(None)
def check_item(i, txt):
    n = text_img(f"{i + 1}", P9, 32, PINK, 0, shadow=False)
    a = text_img(txt, P7, 32, INK, 0, shadow=False)
    im = rrect_img(a.width + n.width + 60, 62, 31, CREAM + (245,), outline=INK + (255,), ow=4)
    im.alpha_composite(n, (40, int(im.height / 2 - n.height / 2) - 2))
    im.alpha_composite(a, (40 + n.width - 6, int(im.height / 2 - a.height / 2) - 2))
    return im


def draw_checklist(cv, t):
    s, e = 22.15, 37.45
    if not (s <= t < e):
        return
    pin = ease_back((t - s) / 0.35, 1.3)
    pout = ease_out((e - t) / 0.35) if t > e - 0.35 else 1
    off = (1 - pin * pout) * -700
    L = SAFE["left"] - 26
    h = check_header()
    paste(cv, h, L + h.width / 2 + off, SAFE["top"] + 40)
    for i, (ti, txt) in enumerate(CHECK_ITEMS):
        if t < ti:
            continue
        p = ease_back((t - ti) / 0.3, 1.5)
        im = check_item(i, txt)
        cx, cy = L + 10 + im.width / 2 + off + (1 - min(p, 1)) * -150, SAFE["top"] + 122 + i * 72
        paste(cv, im, cx, cy, max(0.01, min(p, 1.05)))
        q = (t - ti - 0.35) / 0.2
        if q > 0:
            paste(cv, emoji_img("❌", 40), cx + im.width / 2 - 4, cy, ease_back(q, 2.0), -10)


@functools.lru_cache(None)
def badge_img(num):
    sz = 190
    im = Image.new("RGBA", (sz + 40, sz + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((26, 30, 26 + sz - 12, 30 + sz - 12), fill=(0, 0, 0, 110))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im)
    d.ellipse((20, 20, 20 + sz, 20 + sz), fill=LIME + (255,), outline=INK + (255,), width=6)
    a = text_img("NO.", P7, 26, GREEN, 0, shadow=False)
    b = text_img(num, P9, 96, GREEN, 0, shadow=False)
    im.alpha_composite(a, (int(im.width / 2 - a.width / 2), 50))
    im.alpha_composite(b, (int(im.width / 2 - b.width / 2), 62))
    return im


def draw_badges(cv, t):
    for s, e, num in BADGES:
        if s <= t < e:
            p = (t - s) / 0.25
            sc = (1 + 0.5 * (1 - ease_out(p))) if p < 1 else 1 + 0.03 * math.sin((t - s) * 4)
            if e - t < 0.15:
                sc *= ease_out((e - t) / 0.15)
            paste(cv, badge_img(num), SAFE["right"] - 110, SAFE["top"] + 110, sc, -8 + 5 * math.sin((t - s) * 2),
                  alpha=min(1, p * 2))


def draw_info(cv, t):
    s, e = 41.45, 45.15
    if not (s <= t < e):
        return
    pout = ease_out((e - t) / 0.3) if t > e - 0.3 else 1
    for i, (ti, txt, ic) in enumerate(INFO):
        if t < ti:
            continue
        p = ease_back((t - ti) / 0.35, 1.5) * pout
        off = (1 - min(1, (t - ti) / 0.35)) * (260 if i % 2 else -260)
        paste(cv, chip(txt, ic, 32), (SAFE["left"] + SAFE["right"]) / 2 + off, 1270 + i * 72, p)


# confetti
_cr = np.random.default_rng(3)
CONF_COLS = [PINK, LIME, (255, 214, 10), (120, 200, 255), CREAM]


def make_confetti(t0, n, origin, spread):
    ps = []
    for _ in range(n):
        if origin == "top":
            x, y, vx, vy = _cr.uniform(-50, W + 50), _cr.uniform(-400, -20), _cr.uniform(-80, 80), _cr.uniform(250, 480)
        else:
            x, y = (-20 if origin == "left" else W + 20), 1450
            ang = _cr.uniform(-75, -45) if origin == "left" else _cr.uniform(-135, -105)
            sp = _cr.uniform(1200, 2100)
            vx, vy = sp * math.cos(math.radians(ang)), sp * math.sin(math.radians(ang))
        ps.append(dict(t0=t0 + _cr.uniform(0, spread), x=x, y=y, vx=vx, vy=vy, w=_cr.uniform(12, 22),
                       h=_cr.uniform(7, 12), r=_cr.uniform(0, 6.28), vr=_cr.uniform(-9, 9),
                       c=CONF_COLS[_cr.integers(len(CONF_COLS))], ph=_cr.uniform(0, 6.28)))
    return ps


CONFETTI = (make_confetti(48.75, 80, "left", 0.15) + make_confetti(48.75, 80, "right", 0.15)
            + make_confetti(49.1, 110, "top", 3.0) + make_confetti(38.0, 40, "left", 0.1)
            + make_confetti(38.0, 40, "right", 0.1))


def draw_confetti(cv, t):
    d = ImageDraw.Draw(cv)
    for p in CONFETTI:
        dt = t - p["t0"]
        if dt < 0 or dt > 4.5:
            continue
        drag = math.exp(-1.6 * dt)
        x = p["x"] + p["vx"] * (1 - drag) / 1.6 + 40 * math.sin(dt * 4 + p["ph"])
        y = p["y"] + p["vy"] * (1 - drag) / 1.6 + 190 * dt * dt
        if y > H + 40 or y < -450:
            continue
        r = p["r"] + p["vr"] * dt
        fl = abs(math.cos(dt * 7 + p["ph"]))
        w, h = p["w"], p["h"] * (0.25 + 0.75 * fl)
        cs, sn = math.cos(r), math.sin(r)
        d.polygon([(x + a * cs - b * sn, y + a * sn + b * cs) for a, b in
                   [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]], fill=p["c"] + (255,))


@functools.lru_cache(None)
def end_cta():
    a = text_img("See you there!", P9, 54, INK, 0, shadow=False)
    pa = rrect_img(a.width + 70, 100, 50, LIME + (255,), outline=(255, 255, 255, 255), ow=6)
    pa.alpha_composite(a, (int(pa.width / 2 - a.width / 2), int(pa.height / 2 - a.height / 2) - 3))
    return pa


def draw_end(cv, t):
    s = 49.2
    if t < s:
        return
    sc = ease_back((t - s) / 0.4, 1.6)
    bob = 6 * math.sin((t - s) * 4)
    cx = (SAFE["left"] + SAFE["right"]) / 2
    paste(cv, end_cta(), cx, END_CTA_Y + bob, sc)
    paste(cv, emoji_img("🎉", 80), cx + end_cta().width / 2 - 20, END_CTA_Y - 46 + bob, ease_back((t - s - .2) / .3, 2), 15)


def draw_progress(cv, t):
    d = ImageDraw.Draw(cv)
    d.rectangle((0, 0, W, 7), fill=(0, 0, 0, 70))
    d.rectangle((0, 0, int(W * t / (NFR / FPS)), 7), fill=LIME + (255,))


# ---------------------------------------------------------------- frame pipeline
POSTER_Y0, POSTER_Y1 = 286, 1634
END_SCALE = 0.78
END_CX, END_CY = (SAFE["left"] + SAFE["right"]) / 2, 790
END_CTA_Y = 1418


def end_card(img):
    """Shrink the poster into the safe zone over a blurred backdrop."""
    poster = img[POSTER_Y0:POSTER_Y1]
    bg = cv2.resize(poster, (W, H))
    bg = cv2.GaussianBlur(bg, (0, 0), 40)
    bg = (bg * 0.55).astype(np.uint8)
    pw, ph = int(W * END_SCALE), int((POSTER_Y1 - POSTER_Y0) * END_SCALE)
    sm = cv2.resize(poster, (pw, ph), interpolation=cv2.INTER_AREA)
    x0, y0 = int(END_CX - pw / 2), int(END_CY - ph / 2)
    # soft shadow
    sh = np.zeros((H, W), np.float32)
    sh[y0 + 14:y0 + ph + 14, x0 + 8:x0 + pw + 8] = 1
    sh = cv2.GaussianBlur(sh, (0, 0), 18)[..., None] * 0.6
    bg = (bg * (1 - sh)).astype(np.uint8)
    bg[y0:y0 + ph, x0:x0 + pw] = sm
    return bg


FIXED_DIR = os.path.join(HERE, "fixed")


def remove_nametag(img, idx):
    """Swap in the LaMa-cleaned band (see lama_fix.py) for frames where the burned-in tag is visible."""
    pth = os.path.join(FIXED_DIR, f"{idx:05d}.png")
    if not os.path.exists(pth):
        return img
    img = img.copy()
    img[960:1472] = cv2.imread(pth)
    return img


_x = np.arange(256) / 255.0
LUT = np.clip((0.78 * _x + 0.22 * (0.5 - 0.5 * np.cos(np.pi * _x))) * 255 * 1.01, 0, 255).astype(np.uint8)
_yy, _xx = np.mgrid[0:H, 0:W]
LEAK_A = (np.clip(1 - np.sqrt(((_xx - W * 0.85) / W) ** 2 + ((_yy - H * 0.2) / H) ** 2) / 0.9, 0, 1) ** 1.5).astype(np.float32)
WARM = np.zeros((H, W, 3), np.float32); WARM[..., 2] = 255; WARM[..., 1] = 190; WARM[..., 0] = 120
VIG = np.clip(1.15 - 0.45 * (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2), 0.3, 1).astype(np.float32)


def grade(img):
    img = cv2.LUT(img, LUT)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv[..., 1] = cv2.LUT(hsv[..., 1], np.clip(np.arange(256) * 1.1, 0, 255).astype(np.uint8))
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def seg_of(n):
    s = max(x for x in SEG_STARTS if x <= n)
    nx = [x for x in SEG_STARTS if x > n]
    return s, (nx[0] if nx else NFR + 1)


def process(img, idx):
    n = idx + 1            # this footage starts one frame later than the original edit
    t = n / FPS
    img = remove_nametag(img, idx)
    if n >= 1462:
        img = end_card(img)
    img = grade(img)
    s0, s1 = seg_of(n)
    z = ZOOM_ALT.get(s0, 1.0) + 0.03 * (n - s0) / max(1, s1 - s0)
    if n < 10:
        z += 0.2 * (1 - ease_out(n / 10))
    dx = dy = rot = 0.0
    blurL = 0
    flash = leak = 0.0
    for c, typ in CUTS.items():
        k = n - c
        if typ == "punch" and 0 <= k < 8:
            z += 0.12 * math.exp(-0.6 * k); flash = max(flash, 0.25 * math.exp(-1.1 * k))
        elif typ == "leak" and -4 <= k < 10:
            leak = max(leak, 0.65 * math.exp(-abs(k) / 3.5)); z += 0.05 * math.exp(-abs(k) / 4)
        elif typ == "spin" and 0 <= k < 14:
            p = (1 - k / 14) ** 3
            rot += 20 * p; z += 0.5 * p; flash = max(flash, 0.7 * math.exp(-0.8 * k))
        elif isinstance(typ, tuple):
            d = typ[1]
            if -3 <= k < 0:
                p = (k + 4) / 3; dx -= d * W * 0.35 * p * p; blurL = max(blurL, int(20 + 80 * p))
            elif 0 <= k < 5:
                p = 1 - k / 5; dx += d * W * 0.35 * p * p; blurL = max(blurL, int(80 * p))
    if 35.95 <= t < 37.5:
        z *= 1 + 0.12 * ease_out((t - 35.95) / 1.5)
    if t >= 49.2:
        z *= 1 + 0.01 * math.sin((t - 49.2) * 2.5)
    for s, e, a in SHAKES:
        if s <= t < e:
            k = 1 - (t - s) / (e - s); dx += a * k * math.sin(t * 91); dy += a * k * math.cos(t * 73)
    ax, ay = (540, 800) if n < 1462 else (END_CX, END_CY)
    M = cv2.getRotationMatrix2D((ax, ay), rot, z)
    M[0, 2] += dx; M[1, 2] += dy
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    if blurL > 2:
        img = cv2.filter2D(img, -1, np.full((1, blurL), 1.0 / blurL, np.float32))
    if rot > 1:
        img = cv2.GaussianBlur(img, (0, 0), rot / 5)
    if 35.95 <= t < 37.5:
        p = ease_out((t - 35.95) / 0.6)
        g = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        img = cv2.addWeighted(img, 1 - 0.7 * p, g, 0.7 * p, 0)
        img = (img * VIG[..., None] ** p).astype(np.uint8)
    if leak > 0.01:
        img = np.clip(img.astype(np.float32) + WARM * (LEAK_A * leak)[..., None], 0, 255).astype(np.uint8)
    if flash > 0.01:
        img = cv2.addWeighted(img, 1 - flash, np.full_like(img, 255), flash, 0)

    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_checklist(cv, t)
    draw_badges(cv, t)
    draw_banner(cv, t)
    draw_nametag(cv, t)
    draw_info(cv, t)
    draw_sparkles(cv, t)
    draw_stickers(cv, t)
    draw_captions(cv, t)
    draw_confetti(cv, t)
    draw_end(cv, t)
    draw_progress(cv, t)
    if os.environ.get("SAFE_GUIDE"):
        ImageDraw.Draw(cv).rectangle((SAFE["left"], SAFE["top"], SAFE["right"], SAFE["bottom"]),
                                     outline=(255, 0, 0, 255), width=4)
    ov = np.asarray(cv)
    a = ov[..., 3:4].astype(np.float32) / 255.0
    return (img.astype(np.float32) * (1 - a) + ov[..., 2::-1].astype(np.float32) * a).astype(np.uint8)


def read_frames(a, b):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"select='between(n\\,{a}\\,{b - 1})'",
                          "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    sz = W * H * 3
    for n in range(a, b):
        buf = p.stdout.read(sz)
        if len(buf) < sz:
            break
        yield n, np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    p.stdout.close(); p.wait()


def render_chunk(a, b, out):
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                            "-pix_fmt", "yuv420p", "-profile:v", "high", "-color_primaries", "bt709",
                            "-color_trc", "bt709", "-colorspace", "bt709", "-x264-params", "keyint=60", out],
                           stdin=subprocess.PIPE)
    for n, fr in read_frames(a, b):
        enc.stdin.write(process(fr, n).tobytes())
        if n % 100 == 0:
            print(f"chunk {a}: frame {n}", flush=True)
    enc.stdin.close(); enc.wait()


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        outdir = os.path.join(HERE, "prev"); os.makedirs(outdir, exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(",")]:
            n = int(round(t * FPS)) - 1
            img = process(next(read_frames(n, n + 1))[1], n)
            cv2.imwrite(os.path.join(outdir, f"p_{t:06.2f}.jpg"), cv2.resize(img, (360, 640)), [cv2.IMWRITE_JPEG_QUALITY, 88])
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
