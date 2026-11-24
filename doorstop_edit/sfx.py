# Synthesised, subtle "whoosh + soft tick" for each number card (no third-party SFX needed)
import numpy as np, wave, json, sys
SR = 48000
def whoosh(dur=0.42):
    n = int(SR*dur); t = np.arange(n)/SR
    rng = np.random.default_rng(7); x = rng.standard_normal(n)
    # sweeping one-pole lowpass: cutoff rises 300 Hz -> 4 kHz
    fc = 300 * (4000/300) ** (t/dur); y = np.zeros(n); a = 0.0
    for i in range(n):
        al = 1 - np.exp(-2*np.pi*fc[i]/SR); a += al*(x[i]-a); y[i] = a
    env = np.minimum(1, t/0.28) ** 2 * np.exp(-np.maximum(0, t-0.28)/0.05)
    return y*env/np.max(np.abs(y*env))
def tick(dur=0.09):
    t = np.arange(int(SR*dur))/SR
    return (np.sin(2*np.pi*1320*t)*0.6 + np.sin(2*np.pi*2640*t)*0.25) * np.exp(-t/0.018)
def build(times, total, out):
    tr = np.zeros(int(SR*total)+SR); w = whoosh(); k = tick()
    for t0 in times:
        i = int((t0-0.30)*SR); tr[i:i+len(w)] += 0.22*w          # whoosh leads into the card
        j = int((t0+0.08)*SR); tr[j:j+len(k)] += 0.10*k          # soft tick as it lands
    tr = tr[:int(SR*total)]
    st = (np.clip(tr, -1, 1)*32767).astype(np.int16)
    f = wave.open(out, "w"); f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(st.tobytes()); f.close()
if __name__ == "__main__":
    cards = json.load(open(sys.argv[1])); build([c["start"] for c in cards], float(sys.argv[2]), sys.argv[3])
