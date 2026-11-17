import sys, time, torch, numpy as np
from scipy.io import wavfile
from resemble_enhance.enhancer.inference import enhance
src, dst = sys.argv[1], sys.argv[2]
lambd = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
sr, x = wavfile.read(src)
x = x.astype(np.float32) / 32768.0
if x.ndim > 1:
    x = x.mean(1)
torch.set_num_threads(4)
t = time.time()
out, osr = enhance(torch.from_numpy(x), sr, 'cpu', nfe=48, solver='midpoint', lambd=lambd, tau=0.5)
y = out.numpy()
y = y / max(np.abs(y).max(), 1e-9) * 0.9
wavfile.write(dst, osr, (y * 32767).astype(np.int16))
print(f'enhanced in {time.time()-t:.0f}s at {osr} Hz')
