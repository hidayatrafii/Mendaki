import sys; sys.path.insert(0,"..")
import numpy as np, sfx
from sfx import t_, SR
def tick():
    t=t_(0.03); return np.sin(2*np.pi*2400*t)*np.exp(-t*160)*0.5
def shimmer():
    out=np.zeros(int(SR*1.4)); notes=[1567.98,2093,2349.3,2637,3136,3520]
    for i,f in enumerate(notes):
        t=t_(1.0); s=int(i*0.06*SR); out[s:s+len(t)]+=np.sin(2*np.pi*f*t)*np.exp(-t*5)*0.18
    return out
def soft_pop(): return sfx.pop(420)*0.6
sfx.LIB.update(tick=tick, shimmer=shimmer, soft_pop=soft_pop)
E=[]
def a(t,n,g=-14,p=0.0): E.append((t,n,g,p))
a(0.0,"whoosh",-12)
for c,ty in {28:"punch",49:"whip",374:"whip",394:"punch",503:"leak",536:"punch",704:"whip",728:"punch",737:"whip",762:"punch",1031:"leak",1594:"whip",1981:"punch",2009:"whip",2025:"punch"}.items():
    t=c/30
    if ty=="whip": a(t-0.12,"whoosh",-13,0.3)
    elif ty=="punch": a(t-0.08,"swish",-15)
    else: a(t-0.15,"whoosh_long",-14)
a(11.45,"whoosh_long",-13); a(22.05,"whoosh_long",-13)
for s in [6.03,14.73,25.8,54.9]: a(s,"shimmer",-12)
for s in [9.35,18.2,20.1,30.65,32.1,33.02,47.78,50.72,51.7,53.25,65.22,68.97,71.3]: a(s,"soft_pop",-15,0.4)
a(30.62,"ding",-18)
for s in [16.6,29.0,27.57]: a(s,"soft_pop",-14); a(s+0.02,"click",-20)
for s in [40.28,42.5,43.88,45.95,46.88]: a(s-0.1,"swish",-15); a(s+0.05,"shimmer",-15)
a(54.95,"soft_pop",-14)
for s in [56.47,58.63,60.2]: a(s,"soft_pop",-14); a(s+0.05,"whoosh",-20)
for k in range(14): a(63.7+k*0.065,"tick",-18)
a(64.62,"ding",-17)
a(66.27,"soft_pop",-13); a(66.5,"click",-17); a(67.1,"click",-19)
a(67.9,"soft_pop",-14)
a(74.5,"swish",-14)
a(74.85,"riser",-16)
a(75.4,"boom",-14); a(75.42,"whoosh_long",-14); a(75.5,"shimmer",-11); a(75.9,"soft_pop",-14)
sfx.render(E,78.4,"sfx.wav")
