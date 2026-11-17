"""Suppress camera-shutter clicks: duck the >3 kHz band for ~25 ms at each sharp HF transient.
usage: python3 declick.py in.wav out.wav"""
import sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt
from scipy.ndimage import median_filter

src, dst = sys.argv[1], sys.argv[2]
sr, x = wavfile.read(src)
x = x.astype(np.float64)
if x.ndim > 1:
    x = x.mean(1)
hp = sosfiltfilt(butter(4, 3000, 'hp', fs=sr, output='sos'), x)
lo = x - hp
det = sosfiltfilt(butter(4, 6000, 'hp', fs=sr, output='sos'), x)
f = sr // 500  # 2 ms frames
n = len(det) // f
e = np.sqrt((det[:n * f].reshape(n, f) ** 2).mean(1))
base = median_filter(e, size=25) + 1e-9
floor = np.percentile(e[e > 0], 90) if np.any(e > 0) else 0
hits = np.where((e / base > 5) & (e > floor))[0]
g = np.ones(len(x))
ramp = int(0.005 * sr); hold = int(0.025 * sr)
win = np.concatenate([np.linspace(1, 0.12, ramp), np.full(hold, 0.12), np.linspace(0.12, 1, ramp)])
for i in hits:
    s0 = max(i * f - int(0.008 * sr), 0)
    seg = win[:max(0, min(len(win), len(g) - s0))]
    g[s0:s0 + len(seg)] = np.minimum(g[s0:s0 + len(seg)], seg)
y = lo + g * hp
print(f'declick: {len(hits)} transient frames ducked')
wavfile.write(dst, sr, np.clip(y, -32768, 32767).astype(np.int16))
