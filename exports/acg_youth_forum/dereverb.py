"""WPE dereverberation (nara_wpe) for a mono wav: python3 dereverb.py in.wav out.wav"""
import sys
import numpy as np
from scipy.io import wavfile
from nara_wpe.wpe import wpe
from nara_wpe.utils import stft, istft

src, dst = sys.argv[1], sys.argv[2]
sr, x = wavfile.read(src)
x = x.astype(np.float64)
if x.ndim > 1:
    x = x.mean(1)
peak = np.abs(x).max() or 1.0
x = x / peak
SIZE, SHIFT = 2048, 512          # at 48 kHz: 43 ms window, 10.7 ms hop
TAPS, DELAY = 40, 2              # predicts ~430 ms of late reverb
Y = stft(x[None, :], size=SIZE, shift=SHIFT)          # (1, T, F)
Y = Y.transpose(2, 0, 1)                               # (F, 1, T)
Z = np.empty_like(Y)
for f0 in range(0, Y.shape[0], 48):   # chunk over frequency to bound memory
    Z[f0:f0+48] = wpe(Y[f0:f0+48], taps=TAPS, delay=DELAY, iterations=3, statistics_mode='full')
z = istft(Z.transpose(1, 2, 0), size=SIZE, shift=SHIFT)[0][:len(x)]
# gentle blend keeps it natural (full WPE can sound slightly phasey)
out = 0.92 * z + 0.08 * x[:len(z)]
out = out / max(np.abs(out).max(), 1e-9) * 0.9
wavfile.write(dst, sr, (out * 32767).astype(np.int16))
