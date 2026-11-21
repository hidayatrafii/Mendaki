import sys, os, math, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from render import ease_back, ease_out, font, text_img, emoji_img, paste, rrect_img, star_poly  # noqa

SRC = os.path.join(HERE, "in.mp4")
FPS = 30
SW, SH = 576, 1024
W, H = 1080, 1920
NFR = 2352
REPO_FONTS = "/home/user/Mendaki/exports/assets/fonts"
P7 = os.path.join(REPO_FONTS, "Poppins-700.ttf")
P8 = os.path.join(REPO_FONTS, "Poppins-800.ttf")
P9 = os.path.join(REPO_FONTS, "Poppins-900.ttf")
LOGO = "/home/user/Mendaki/exports/assets/logos/mendaki_logo_white.webp"

GOLD = (245, 197, 66)
PLUM = (59, 21, 48)
CREAM = (255, 244, 214)
CAP_COL = (245, 226, 165)

# ---------------------------------------------------------------- corrected subtitles (start, end, text)
CAPS = [
    (0.33, 1.0, "Eh, Dyn!"), (1.0, 1.75, "Dyn Norahim!"), (1.87, 3.0, "nak gi mana?"),
    (3.47, 4.95, "nak prep event"), (5.0, 5.9, "ada event apa?"), (6.03, 7.35, 'event "Kita Jaga Kita"'),
    (7.7, 8.9, "kita jaga siapa?"), (9.3, 10.3, "huh, kau siapa?"), (12.0, 13.5, "eh, korang buat apa kat sini?"),
    (13.73, 14.72, "Dyn cakap dia gi"), (14.73, 15.5, '"Kita Jaga Kita"'), (15.73, 16.6, "oh, bila?"),
    (16.6, 18.1, "27 November ni"), (18.13, 20.03, "eh, korang tak ajak aku?"),
    (20.07, 21.9, "ajaklah ni, tapi korang siapa?"), (24.1, 25.37, "eh, korang nak gi mana?"),
    (25.8, 26.6, '"Kita Jaga Kita"'), (27.0, 27.55, "kat mana?"), (27.57, 28.95, "Malay Heritage Centre"),
    (29.0, 30.5, "oh, yang 27 November ni?"), (30.6, 31.8, "finally someone knows!"),
    (32.07, 32.98, "tapi korang ni siapa?"), (33.0, 33.4, "nak ikut!"), (34.1, 36.15, "oh, so event dia kat sini?"),
    (36.17, 37.2, "ya, kat sini"), (37.23, 39.0, "ok, but siapa lagi ada?"), (39.03, 40.28, "ada co-host Raja Razie"),
    (41.03, 41.18, "ada co-host Raja Razie"), (41.2, 42.5, "ada speaker Dr Azhar Ibrahim"),
    (43.57, 43.88, "ada Ustazah Kalthom Isa"), (44.88, 45.22, "ada Ustazah Kalthom Isa"),
    (45.23, 45.95, "lepas tu ada Syarif"), (46.65, 46.88, "and Dyn Norahim"), (47.75, 48.7, "oh!"),
    (48.75, 50.67, "ya ya, tapi korang pergi je lah"), (50.7, 51.67, "tapi korang siapa?"),
    (51.68, 52.3, "nak ikut!"), (53.2, 54.18, "ok, dorang dah takde"), (54.2, 54.55, "ok guys,"),
    (54.9, 56.45, 'join majlis "Kita Jaga Kita"'), (56.47, 57.9, "27 November"), (57.93, 58.62, "Jumaat ini"),
    (58.63, 59.9, "8pm – 9.30pm"), (60.2, 61.96, "di Malay Heritage Centre"), (61.97, 62.93, "Auditorium, ok!"),
    (63.0, 63.68, "tempat terhad"), (63.7, 65.17, "300 orang saja kita invite!"), (65.2, 65.8, "jom, jom, jom!"),
    (66.27, 67.77, "so, cepat daftar!"), (67.9, 68.93, "limited slots tau!"), (68.97, 69.8, "jumpa korang kat sini!"),
    (69.83, 71.25, "eh, korang boleh just..."), (71.27, 72.75, "just go?"), (74.5, 75.4, "wait..."),
]
CARD_WIN = [(40.28, 41.03), (42.5, 43.57), (43.88, 44.88), (45.95, 46.65), (46.88, 47.75)]
CUTS = {28: "punch", 49: ("whip", 1), 374: ("whip", -1), 394: "punch", 503: "leak", 536: "punch",
        704: ("whip", 1), 728: "punch", 737: ("whip", -1), 762: "punch", 1031: "leak", 1594: ("whip", 1),
        1981: "punch", 2009: ("whip", -1), 2025: "punch", 2263: "leak"}
SEG_STARTS = sorted(set([0, 28, 49, 351, 374, 394, 503, 536, 687, 704, 728, 737, 762, 1031, 1594, 1981, 2009,
                         2025, 2263]))
ZOOM_ALT = {394: 1.08, 536: 1.08, 728: 1.08, 762: 1.0, 1981: 1.08, 2025: 1.0}
STICKERS = [
    (9.35, 10.3, "🤨", 870, 1000, 170), (18.2, 20.0, "😤", 880, 1000, 160), (20.1, 21.9, "🤔", 200, 1000, 160),
    (30.65, 31.8, "🙌", 860, 1000, 170), (32.1, 33.0, "🤨", 210, 1000, 160), (33.02, 33.45, "🙋", 860, 1000, 160),
    (47.78, 48.7, "😮", 860, 1000, 160), (50.72, 51.67, "🤔", 210, 1000, 160), (51.7, 52.3, "🙋", 860, 1000, 160),
    (53.25, 54.2, "💨", 860, 1060, 180), (65.22, 65.8, "🙌", 860, 1000, 170), (68.97, 69.8, "👋", 200, 1000, 160),
    (71.3, 72.75, "👉", 880, 1000, 160), (74.5, 75.4, "✋", 860, 1000, 180),
]
SPARKLES = [(6.03, 7.35), (14.73, 15.5), (25.8, 26.6), (54.9, 56.45)]
SHAKES = [(74.5, 74.75, 4)]
CARD_RECT = (188, 394, 750, 1238)


# ---------------------------------------------------------------- caption style: Poppins, same size, stroke + shadow
def _cap_size():
    # original caption "Malay Heritage Center" was ~245px wide at 576 -> 459px at 1080
    target = 245 * W / SW
    for s in range(20, 60):
        if ImageFont.truetype(P7, s).getlength("Malay Heritage Center") >= target:
            return s
    return 32


CAP_SIZE = _cap_size()
CAP_Y = 637 * W / SW


@functools.lru_cache(None)
def cap_img(txt):
    f = font(P7, CAP_SIZE)
    st = 3
    bb = f.getbbox(txt, stroke_width=st)
    pad = 20
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    org = (pad - bb[0], pad - bb[1])
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((org[0] + 2, org[1] + 4), txt, font=f, fill=(0, 0, 0, 210), stroke_width=st + 1,
                            stroke_fill=(0, 0, 0, 210))
    im = sh.filter(ImageFilter.GaussianBlur(4))
    ImageDraw.Draw(im).text(org, txt, font=f, fill=CAP_COL, stroke_width=st, stroke_fill=(28, 14, 20, 255))
    return im


def draw_captions(cv, t):
    for s, e, txt in CAPS:
        if s <= t < e:
            p = (t - s) / 0.13
            sc = 0.9 + 0.1 * ease_back(p, 1.6)
            a = min(1.0, p * 1.5, (e - t) / 0.06)
            paste(cv, cap_img(txt), W / 2, CAP_Y + 8 * (1 - ease_out(p)), sc, alpha=max(0.0, a))


# ---------------------------------------------------------------- promo gfx
@functools.lru_cache(None)
def chip(txt, icon=None, size=40, fill=PLUM, tcol=CREAM, border=GOLD):
    a = text_img(txt, P8, size, tcol, 0, shadow=False)
    ic = emoji_img(icon, int(size * 1.35)) if icon else None
    iw = ic.width - 26 if ic else 0
    w = a.width - 30 + iw + 64
    h = int(size * 1.9)
    im = rrect_img(w, h, h // 2, fill + (245,), outline=border + (255,), ow=5)
    x = 26 + 30
    if ic:
        im.alpha_composite(ic, (x - 18, int(im.height / 2 - ic.height / 2)))
        x += iw
    im.alpha_composite(a, (x - 22, int(im.height / 2 - a.height / 2) - 2))
    return im


def anim_in_out(t, s, e, din=0.35, dout=0.25, k=1.3):
    if not (s <= t < e):
        return 0.0
    sc = ease_back((t - s) / din, k)
    if t > e - dout:
        sc *= ease_out((e - t) / dout)
    return sc


def draw_date_pops(cv, t):
    for s, e in [(16.6, 18.1), (29.0, 30.5)]:
        sc = anim_in_out(t, s, e)
        if sc:
            paste(cv, chip("FRI, 27 NOV 2026", "📅", 32), W / 2, 1400, sc)
    for s, e in [(27.57, 28.95)]:
        sc = anim_in_out(t, s, e)
        if sc:
            paste(cv, chip("Auditorium, Malay Heritage Centre", "📍", 30), W / 2, 1400, sc)


@functools.lru_cache(None)
def kjk_title(size=96):
    return text_img("KITA JAGA KITA", P9, size, GOLD, 6, PLUM)


INFO = [(56.47, "FRIDAY, 27 NOV 2026", "📅"), (58.63, "8.00PM – 9.30PM", "🕗"),
        (60.2, "Auditorium, Malay Heritage Centre", "📍")]


def draw_info_panel(cv, t):
    s, e = 54.95, 65.4
    if not (s <= t < e):
        return
    pout = ease_out((e - t) / 0.3) if t > e - 0.3 else 1
    ti = kjk_title(60)
    sc = ease_back((t - s) / 0.4, 1.8) * pout
    paste(cv, ti, W / 2, 1330, sc, rot=0)
    y = 1410
    for i, (ts, txt, ic) in enumerate(INFO):
        if t < ts:
            continue
        p = ease_back((t - ts) / 0.35, 1.8) * pout
        im = chip(txt, ic, 30 if len(txt) > 20 else 32)
        off = (1 - min(1, (t - ts) / 0.35)) * (300 if i % 2 else -300)
        paste(cv, im, W / 2 + off, y + i * 78, p)
    # 300 PAX counter
    cs = 63.7
    if t >= cs:
        n = int(min(300, 300 * ease_out((t - cs) / 0.9)))
        p = ease_back((t - cs) / 0.3, 2.2) * pout
        im = chip(f"ONLY {n} PAX", "🎟️", 34, fill=GOLD, tcol=PLUM, border=(255, 255, 255))
        pulse = 1
        paste(cv, im, W / 2, 1410 + 3 * 78 + 6, p * pulse)


@functools.lru_cache(None)
def register_btn():
    a = text_img("REGISTER NOW", P8, 44, PLUM, 0, shadow=False)
    im = rrect_img(a.width + 70, 90, 45, GOLD + (255,), outline=(255, 255, 255, 255), ow=5)
    im.alpha_composite(a, (int(im.width / 2 - a.width / 2), int(im.height / 2 - a.height / 2) - 3))
    return im


def draw_register(cv, t):
    for s, e, y in [(66.27, 67.85, 1430), (75.9, 79.0, 1745)]:
        if not (s <= t < e):
            continue
        p = ease_back((t - s) / 0.35, 2.2)
        if e - t < 0.25:
            p *= ease_out((e - t) / 0.25)
        pulse = 1 + 0.015 * math.sin((t - s) * 5)
        b = register_btn()
        paste(cv, b, W / 2, y, p * pulse)
        # shine across the button
        q = ((t - s) * 0.8) % 1.0
        sh = Image.new("RGBA", b.size, (0, 0, 0, 0))
        x = -120 + q * (b.width + 240)
        ImageDraw.Draw(sh).polygon([(x, 0), (x + 50, 0), (x - 10, b.height), (x - 60, b.height)],
                                   fill=(255, 255, 255, 110))
        sh.putalpha(Image.fromarray(np.minimum(np.asarray(sh.split()[3]), np.asarray(b.split()[3]))))
        paste(cv, sh, W / 2, y, p * pulse)
        # tapping finger
        tap = 1 - 0.06 * abs(math.sin((t - s) * 5))
        paste(cv, emoji_img("👆", 80), W / 2 + b.width / 2 - 30, y + 60, p * tap, rot=-15)


@functools.lru_cache(None)
def stamp_img():
    a = text_img("LIMITED SLOTS", P8, 38, CREAM, 0, shadow=False)
    im = rrect_img(a.width + 60, 76, 38, PLUM + (245,), outline=GOLD + (255,), ow=5)
    im.alpha_composite(a, (int(im.width / 2 - a.width / 2), int(im.height / 2 - a.height / 2) - 3))
    return im


def draw_stamp(cv, t):
    s, e = 67.9, 68.95
    if s <= t < e:
        sc = anim_in_out(t, s, e, 0.3, 0.2, 1.4)
        paste(cv, stamp_img(), W / 2 + 20, 1400, sc)
        paste(cv, emoji_img("⏳", 70), W / 2 + 20 - stamp_img().width / 2 + 40, 1400, sc,
              rot=6 * math.sin(t * 4))


def draw_stickers(cv, t):
    for i, (s, e, ch, x, y, sz) in enumerate(STICKERS):
        if not (s <= t < e):
            continue
        p = (t - s) / 0.22
        sc = ease_back(p, 1.5)
        if e - t < 0.12:
            sc *= ease_out((e - t) / 0.12)
        rot = 4 * math.sin((t - s) * 4 + i)
        paste(cv, emoji_img(ch, int(sz * 0.75)), x, y + 5 * math.sin((t - s) * 5 + i), sc, rot)


def draw_sparkles(cv, t):
    d = ImageDraw.Draw(cv)
    for s, e in SPARKLES:
        if not (s <= t < e + 0.3):
            continue
        r = np.random.default_rng(int(s * 100))
        fade = min(1, (e + 0.3 - t) / 0.3)
        for k in range(7):
            ph = r.uniform(0, 1)
            x = W / 2 + r.choice([-1, 1]) * r.uniform(170, 470)
            y = CAP_Y + r.uniform(-130, 110)
            life = ((t - s) * 1.8 + ph) % 1.0
            rr = 16 * math.sin(life * math.pi) * r.uniform(0.6, 1.3) * fade
            if rr < 2:
                continue
            col = [(255, 214, 90, 255), (255, 250, 230, 255), (245, 180, 40, 255)][k % 3]
            d.polygon(star_poly(x, y, rr, rot=life * 2), fill=col)


def card_shine(img, t):
    """light sweep across the speaker cards when each one appears"""
    for s, e in CARD_WIN:
        if s <= t < s + 0.55:
            q = (t - s) / 0.55
            x0, y0, x1, y1 = CARD_RECT
            ov = np.zeros((y1 - y0, x1 - x0), np.float32)
            xx = np.arange(x1 - x0)[None, :] + np.arange(y1 - y0)[:, None] * 0.45
            c = -300 + q * (x1 - x0 + 700)
            ov = np.clip(1 - np.abs(xx - c) / 70, 0, 1) * 0.55
            roi = img[y0:y1, x0:x1].astype(np.float32)
            img[y0:y1, x0:x1] = np.clip(roi + ov[..., None] * 255, 0, 255).astype(np.uint8)
    return img


@functools.lru_cache(None)
def logo_img():
    im = Image.open(LOGO).convert("RGBA")
    s = 190 / im.width
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def draw_logo(cv, t):
    if t < 75.3:
        lg = logo_img()
        a = min(1.0, t / 0.6) * (min(1.0, (75.3 - t) / 0.3)) * 0.9
        paste(cv, lg, W - 40 - lg.width / 2, 60 + lg.height / 2, alpha=a)


def draw_end(cv, t):
    s = 75.6
    if t < s:
        return
    d = ImageDraw.Draw(cv)
    r = np.random.default_rng(11)
    for k in range(26):
        x, y = r.uniform(60, 1020), r.uniform(330, 1560)
        life = ((t - s) * r.uniform(0.6, 1.2) + r.uniform(0, 1)) % 1.0
        rr = 22 * math.sin(life * math.pi) * r.uniform(0.6, 1.4)
        if rr > 2:
            d.polygon(star_poly(x, y, rr, rot=life * 3), fill=(255, 226, 120, 230))


def draw_progress(cv, t):
    d = ImageDraw.Draw(cv)
    d.rectangle((0, 0, W, 8), fill=(0, 0, 0, 80))
    d.rectangle((0, 0, int(W * t / (NFR / FPS)), 8), fill=GOLD + (255,))


# ---------------------------------------------------------------- frame pipeline
def in_card(t):
    return any(s - 0.02 <= t < e + 0.02 for s, e in CARD_WIN)


def cap_active(t):
    return any(s - 0.07 <= t < e + 0.07 for s, e, _ in CAPS)


def clean(fr, n):
    t = n / FPS
    if not cap_active(t) or in_card(t) or t >= 75.4:
        return fr
    b = fr[612:662].astype(np.int16)
    m = ((b[..., 2] > 185) & (b[..., 1] > 165) & (b[..., 0] > 70) & (b[..., 0] < 210) &
         (b[..., 2] - b[..., 0] > 32)).astype(np.uint8)
    if m.sum() < 15:
        return fr
    full = np.zeros(fr.shape[:2], np.uint8)
    full[612:662] = m
    full = cv2.dilate(full, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    full = full | np.roll(np.roll(full, 2, 0), 1, 1)
    y0, y1 = 580, 700
    fr = fr.copy()
    fr[y0:y1] = cv2.inpaint(fr[y0:y1].copy(), full[y0:y1], 5, cv2.INPAINT_TELEA)
    return fr


_x = np.arange(256) / 255.0
LUT = np.clip((0.75 * _x + 0.25 * (0.5 - 0.5 * np.cos(np.pi * _x))) * 255, 0, 255).astype(np.uint8)
WARM = np.zeros((H, W, 3), np.float32)
_yy, _xx = np.mgrid[0:H, 0:W]
_r = np.sqrt(((_xx - W * 0.85) / W) ** 2 + ((_yy - H * 0.2) / H) ** 2)
WARM[..., 2] = 255; WARM[..., 1] = 170; WARM[..., 0] = 60
LEAK_A = np.clip(1 - _r / 0.9, 0, 1).astype(np.float32) ** 1.5


def grade(img):
    img = cv2.LUT(img, LUT)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv[..., 1] = cv2.LUT(hsv[..., 1], np.clip(np.arange(256) * 1.1, 0, 255).astype(np.uint8))
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def seg_of(n):
    s = max(x for x in SEG_STARTS if x <= n)
    nx = [x for x in SEG_STARTS if x > n]
    return s, (nx[0] if nx else NFR)


def process(fr, n):
    t = n / FPS
    fr = clean(fr, n)
    img = cv2.resize(fr, (W, H), interpolation=cv2.INTER_LANCZOS4)
    bl = cv2.GaussianBlur(img, (0, 0), 1.3)
    img = cv2.addWeighted(img, 1.4, bl, -0.4, 0)
    img = grade(img)
    img = card_shine(img, t)

    s0, s1 = seg_of(n)
    z = ZOOM_ALT.get(s0, 1.0) + 0.03 * (n - s0) / max(1, s1 - s0)
    if n < 10:
        z += 0.25 * (1 - ease_out(n / 10))
    dx = dy = 0.0
    blurL = 0
    flash = 0.0
    leak = 0.0
    for c, typ in CUTS.items():
        k = n - c
        if typ == "punch" and 0 <= k < 8:
            z += 0.1 * math.exp(-0.6 * k); flash = max(flash, 0.2 * math.exp(-1.1 * k))
        elif typ == "leak" and -4 <= k < 10:
            leak = max(leak, 0.6 * math.exp(-abs(k) / 3.5)); z += 0.06 * math.exp(-abs(k) / 4)
        elif isinstance(typ, tuple):
            d = typ[1]
            if -3 <= k < 0:
                p = (k + 4) / 3
                dx -= d * W * 0.35 * p * p; blurL = max(blurL, int(20 + 80 * p))
            elif 0 <= k < 5:
                p = 1 - k / 5
                dx += d * W * 0.35 * p * p; blurL = max(blurL, int(80 * p))
    # "wait..." freeze-zoom
    if 74.5 <= t < 75.4:
        z *= 1 + 0.12 * ease_out((t - 74.5) / 0.3)
    for s, e, a in SHAKES:
        if s <= t < e:
            k = 1 - (t - s) / (e - s)
            dx += a * k * math.sin(t * 91); dy += a * k * math.cos(t * 73)
    M = cv2.getRotationMatrix2D((540, 820), 0, z)
    M[0, 2] += dx; M[1, 2] += dy
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    if blurL > 2:
        kk = np.full((1, blurL), 1.0 / blurL, np.float32)
        img = cv2.filter2D(img, -1, kk)
    if leak > 0.01:
        a = (LEAK_A * leak)[..., None]
        img = np.clip(img.astype(np.float32) + WARM * a, 0, 255).astype(np.uint8)
    if flash > 0.01:
        img = cv2.addWeighted(img, 1 - flash, np.full_like(img, 255), flash, 0)

    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_sparkles(cv, t)
    draw_date_pops(cv, t)
    draw_info_panel(cv, t)
    draw_stamp(cv, t)
    draw_stickers(cv, t)
    draw_captions(cv, t)
    draw_register(cv, t)
    draw_end(cv, t)
    draw_logo(cv, t)
    draw_progress(cv, t)
    ov = np.asarray(cv)
    a = ov[..., 3:4].astype(np.float32) / 255.0
    img = (img.astype(np.float32) * (1 - a) + ov[..., 2::-1].astype(np.float32) * a).astype(np.uint8)
    return img


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
        if n % 100 == 0:
            print(f"chunk {a}: frame {n}", flush=True)
    enc.stdin.close(); enc.wait()


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        outdir = os.path.join(HERE, "prev"); os.makedirs(outdir, exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(",")]:
            n = int(round(t * FPS))
            img = process(next(read_frames(n, n + 1))[1], n)
            cv2.imwrite(os.path.join(outdir, f"p_{t:06.2f}.jpg"), cv2.resize(img, (360, 640)),
                        [cv2.IMWRITE_JPEG_QUALITY, 88])
    else:
        render_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
