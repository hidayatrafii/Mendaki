import sys, re; sys.path.insert(0, "..")
import numpy as np, sfx
from sfx import t_, SR
sys.path.insert(0, "../v2")
def shimmer():
    out=np.zeros(int(SR*1.4)); notes=[1567.98,2093,2349.3,2637,3136,3520]
    for i,f in enumerate(notes):
        t=t_(1.0); s=int(i*0.06*SR); out[s:s+len(t)]+=np.sin(2*np.pi*f*t)*np.exp(-t*5)*0.18
    return out
sfx.LIB.update(shimmer=shimmer, soft_pop=lambda: sfx.pop(420)*0.6)
src = open("../audio.py").read()
E = []
SWAP = {"buzzer": "soft_pop", "boing": "soft_pop", "glitch": "swish", "sparkle": "shimmer"}
for m in re.finditer(r'a\(([\d.]+),"(\w+)"(?:,(-?\d+))?(?:,(-?[\d.]+))?\)', src):
    t, n, g, p = float(m.group(1)) - 1/30, m.group(2), int(m.group(3) or -8), float(m.group(4) or 0)
    n = SWAP.get(n, n)
    g -= 4
    if n == "tada": g -= 2
    E.append((max(0, t), n, g, p))
sfx.render(E, 52.43, "sfx.wav")
print(len(E), "events")
