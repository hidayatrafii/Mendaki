import numpy as np
from scipy import signal

SR = 44100
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(SR * d)) / SR


def env_ad(n, a, d_curve=4.0):
    a = max(1, int(a))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[a:] = np.exp(-d_curve * np.linspace(0, 1, n - a))
    return e


def sweep_filter(x, f0, f1, q=1.2, btype="band"):
    """Block-wise time-varying bandpass."""
    out = np.zeros_like(x)
    blk = 512
    nb = int(np.ceil(len(x) / blk))
    zi = None
    for i in range(nb):
        fr = i / max(1, nb - 1)
        f = f0 * (f1 / f0) ** fr
        lo, hi = f / (1 + 1 / q), f * (1 + 1 / q)
        hi = min(hi, SR / 2 - 100)
        sos = signal.butter(2, [lo, hi], btype="bandpass", fs=SR, output="sos")
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        seg = x[i * blk:(i + 1) * blk]
        y, zi = signal.sosfilt(sos, seg, zi=zi)
        out[i * blk:(i + 1) * blk] = y
    return out


def whoosh(d=0.45, f0=300, f1=4000):
    n = int(SR * d)
    x = rng.standard_normal(n)
    up = sweep_filter(x, f0, f1, q=1.5)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    y = up * e
    return y / (np.abs(y).max() + 1e-9) * 0.8


def swish(d=0.22):
    return whoosh(d, 1500, 7000) * 0.7


def pop(f=500):
    t = t_(0.09)
    fr = f * (1 + 2.2 * t / t[-1])
    ph = 2 * np.pi * np.cumsum(fr) / SR
    y = np.sin(ph) * np.exp(-t * 45)
    y[:60] += rng.standard_normal(60) * 0.4 * np.linspace(1, 0, 60)
    return y * 0.9


def ding(f=1318.5, d=1.0):
    t = t_(d)
    y = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 3)
         + 0.25 * np.sin(2 * np.pi * f * 3.02 * t) * np.exp(-t * 5))
    return y * np.exp(-t * 4) * 0.5


def boom(d=0.9):
    t = t_(d)
    fr = 40 + 90 * np.exp(-t * 12)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    y = np.sin(ph) * np.exp(-t * 4.5)
    nz = rng.standard_normal(len(t)) * np.exp(-t * 30)
    sos = signal.butter(2, 900, fs=SR, output="sos")
    y = y + 0.6 * signal.sosfilt(sos, nz)
    y = np.tanh(y * 1.8)
    return y * 0.9


def buzzer(d=0.38):
    t = t_(d)
    y = signal.square(2 * np.pi * 150 * t) * 0.5 + signal.square(2 * np.pi * 153 * t) * 0.5
    sos = signal.butter(2, 2500, fs=SR, output="sos")
    y = signal.sosfilt(sos, y)
    e = np.ones(len(t)); e[:200] = np.linspace(0, 1, 200); e[-1500:] = np.linspace(1, 0, 1500)
    return y * e * 0.45


def boing(d=0.6):
    t = t_(d)
    fr = 180 + 220 * np.exp(-t * 3) * (1 + 0.35 * np.sin(2 * np.pi * 14 * t))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    y = np.sin(ph) * np.exp(-t * 4)
    return y * 0.7


def sparkle(n=7, d=0.6):
    out = np.zeros(int(SR * d) + SR // 4)
    notes = [2093, 2349, 2637, 3136, 3520, 4186, 4699, 5274]
    for i in range(n):
        s = int(i * d / n * SR)
        f = notes[i % len(notes)]
        t = t_(0.25)
        y = np.sin(2 * np.pi * f * t) * np.exp(-t * 18) * 0.35
        out[s:s + len(y)] += y
    return out


def crickets(d=2.2):
    out = np.zeros(int(SR * d))
    t = t_(0.022)
    chirp_ = np.sin(2 * np.pi * 4600 * t) * np.sin(np.pi * t / t[-1])
    pos = 0.0
    while pos < d - 0.2:
        for k in range(3):
            s = int((pos + k * 0.045) * SR)
            out[s:s + len(chirp_)] += chirp_ * 0.22
        pos += 0.55
    # gentle fade
    out *= np.minimum(1, np.linspace(0, 6, len(out))) * np.minimum(1, np.linspace(6, 0, len(out)))
    return out


def glitch(d=0.25):
    n = int(SR * d)
    y = np.zeros(n)
    i = 0
    while i < n:
        L = int(rng.integers(300, 2200))
        kind = rng.integers(0, 3)
        tt = np.arange(L) / SR
        if kind == 0:
            seg = signal.square(2 * np.pi * rng.integers(200, 1800) * tt)
        elif kind == 1:
            seg = rng.standard_normal(L)
        else:
            seg = np.zeros(L)
        y[i:i + L] = seg[: n - i] * 0.35
        i += L
    return np.round(y * 6) / 6  # bitcrush


def riser(d=1.0):
    t = t_(d)
    fr = 200 * (8 ** (t / d))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    nz = sweep_filter(rng.standard_normal(len(t)), 500, 8000, q=1.2)
    y = (0.35 * np.sin(ph) + 0.6 * nz / np.abs(nz).max()) * (t / d) ** 2
    return y * 0.7


def tada():
    tri = lambda f, tt: signal.sawtooth(2 * np.pi * f * tt, 0.5)
    out = np.zeros(int(SR * 1.8))
    seq = [(0.0, [523.25]), (0.11, [659.25]), (0.22, [783.99]), (0.36, [523.25, 659.25, 783.99, 1046.5])]
    for st, fs in seq:
        dur = 0.14 if len(fs) == 1 else 1.3
        tt = t_(dur)
        e = np.exp(-tt * (12 if len(fs) == 1 else 2.2))
        y = sum(tri(f, tt) + 0.5 * np.sin(2 * np.pi * 2 * f * tt) for f in fs) / len(fs)
        s = int(st * SR)
        out[s:s + len(tt)] += y * e * 0.45
    return out


def shutter():
    n = int(SR * 0.08)
    y = rng.standard_normal(n) * np.exp(-np.linspace(0, 12, n))
    sos = signal.butter(2, [1500, 7000], btype="bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, y) * 1.2


LIB = {
    "whoosh": lambda: whoosh(),
    "whoosh_long": lambda: whoosh(0.7, 200, 5000),
    "swish": swish,
    "pop": lambda: pop(520),
    "pop_hi": lambda: pop(850),
    "ding": ding,
    "boom": boom,
    "buzzer": buzzer,
    "boing": boing,
    "sparkle": sparkle,
    "crickets": crickets,
    "glitch": glitch,
    "riser": riser,
    "tada": tada,
    "click": shutter,
}


def render(events, total, out_path):
    """events: list of (time, name, gain_db, pan[-1..1])"""
    n = int(SR * (total + 2))
    mix = np.zeros((n, 2))
    cache = {}
    for t, name, g, pan in events:
        if name not in cache:
            cache[name] = LIB[name]()
        y = cache[name] * (10 ** (g / 20))
        s = int(t * SR)
        e = min(n, s + len(y))
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        mix[s:e, 0] += y[: e - s] * l * 1.414
        mix[s:e, 1] += y[: e - s] * r * 1.414
    mix = mix[: int(SR * total)]
    pk = np.abs(mix).max()
    if pk > 0.98:
        mix *= 0.98 / pk
    from scipy.io import wavfile
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))
