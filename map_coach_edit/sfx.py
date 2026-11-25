# Synthesised SFX (from doorstop_edit/sfx.py, + soft "tr" swish): "pop" when a polaroid lands, "whoosh + tick" when a text card / lower third slides in.
import numpy as np, wave, json, sys
SR = 48000
def whoosh(dur, f0=300, f1=4000, seed=7):
    n = int(SR*dur); t = np.arange(n)/SR; x = np.random.default_rng(seed).standard_normal(n)
    fc = f0*(f1/f0)**(t/dur); y = np.zeros(n); a = 0.0
    for i in range(n):
        al = 1-np.exp(-2*np.pi*fc[i]/SR); a += al*(x[i]-a); y[i] = a
    pk = dur*0.65; env = np.minimum(1, t/pk)**2*np.exp(-np.maximum(0, t-pk)/0.05)
    y = y*env; return y/np.max(np.abs(y))
def tone(f, dur, decay):
    t = np.arange(int(SR*dur))/SR
    return (np.sin(2*np.pi*f*t)*0.6 + np.sin(2*np.pi*2*f*t)*0.25)*np.exp(-t/decay)
def pop():   # soft, rounded "pop": pitch-dropping sine blip + tiny air
    t = np.arange(int(SR*0.12))/SR; f = 900*np.exp(-t/0.03)+380
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.035)
def build(events, total, out):
    tr = np.zeros(int(SR*total)+SR); W1 = whoosh(0.42); W2 = whoosh(0.22, 600, 6000, 3); T = tone(1320, 0.09, 0.018); P = pop()
    def put(sig, t0, g):
        i = max(0, int(t0*SR)); tr[i:i+len(sig)] += g*sig[:len(tr)-i]
    for t0, kind in events:
        if kind == "card": put(W1, t0-0.30, 0.22); put(T, t0+0.08, 0.10)
        elif kind == "lt": put(W1, t0-0.25, 0.18)
        elif kind == "pop": put(W2, t0-0.12, 0.08); put(P, t0+0.04, 0.22)
        elif kind == "tr": put(W2, t0-0.14, 0.07)          # very soft swish on section changes
        elif kind == "trans": put(W1, t0-0.30, 0.15)       # soft whoosh under the post-hook zoom transition
        elif kind == "tick": put(T, t0 + 0.05, 0.09)         # light tick as the URL underline draws
    tr = tr[:int(SR*total)]
    f = wave.open(out, "w"); f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((np.clip(tr, -1, 1)*32767).astype(np.int16).tobytes()); f.close()
if __name__ == "__main__":
    build(json.loads(sys.argv[1]), float(sys.argv[2]), sys.argv[3])
