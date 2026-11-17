"""Verify (1) speech audio placement vs source, (2) a-roll picture vs source, (3) captions vs spoken words."""
import subprocess, json, glob, re, numpy as np
from scipy.signal import correlate

FPS = 30000 / 1001
SP = '/home/user/Mendaki/footage/speech/DJI_20261117114504_0103_D.MP4'
OUT = '/home/user/Mendaki/exports/ACG_Youth_Forum_2026_Speech_NoMusic.mp4'
src_txt = open('/home/user/Mendaki/work/build.py').read(); ns = {}
exec(src_txt[src_txt.index('BODY = ['):src_txt.index('# a-roll ranges where')], ns)
exec(src_txt[src_txt.index('LOGO_SHOTS = ['):src_txt.index('INTRO_LEN = ')], ns)
t = sum(d for *_, d in ns['LOGO_SHOTS'] + ns['MONTAGE'])
segs = []
for a, b, txt, sec in ns['BODY']:
    segs.append((a, b, t, txt)); t += b - a
TOTAL = t
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', OUT], capture_output=True, text=True).stdout)
print(f'timeline {TOTAL:.2f}s, file {dur:.2f}s')

# 1. audio: each line found at its expected time?
SR = 8000
def load(p, extra=[]):
    r = subprocess.run(['ffmpeg', '-v', 'error', *extra, '-i', p, '-map', '0:a:0', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(r, np.int16).astype(float)
out = load(OUT)
worst = 0
for a, b, o, txt in segs:
    d = min(1.5, b - a - 0.3)
    x = load(SP, ['-ss', f'{a + 0.15:.3f}', '-t', f'{d:.3f}'])
    y = out[int((o + 0.15 - 0.25) * SR):int((o + 0.15 + d + 0.25) * SR)]
    c = correlate(y, x, 'valid'); k = int(np.argmax(c))
    nc = c[k] / (np.linalg.norm(x) * np.linalg.norm(y[k:k + len(x)]) + 1e-9)
    off = (k / SR - 0.25) * 1000; worst = max(worst, abs(off))
    print(f'  audio  out {o:6.2f}s  offset {off:+6.1f} ms  match {nc:.2f}  "{txt[:40]}"')
print(f'AUDIO worst offset {worst:.1f} ms')

# 2. picture: a-roll frames vs source frames (grade-independent correlation)
def frames(path, t, n, pre):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', path, '-frames:v', str(n), '-vf', pre + 'scale=108:192,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    v = np.frombuffer(b, np.uint8).astype(float).reshape(n, -1); v = v - v.mean(1, keepdims=True)
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
offs = []
for a, b, o, txt in segs:
    for frac in (0.3, 0.7):
        T = o + (b - a) * frac; s = a + (T - o)
        f = frames(OUT, T, 1, '')[0]; S = frames(SP, s - 0.2, 13, 'scale=1080:1920,')
        cc = S @ f; i = int(np.argmax(cc))
        if cc[i] > 0.95:
            offs.append(i / FPS - 0.2)
print(f'PICTURE a-roll checks {len(offs)}, offsets (ms): {sorted(set(round(x*1000) for x in offs))}')

# 3. captions vs words heard (fresh transcription of the final speech track)
aj = sorted(glob.glob('/home/user/Mendaki/work/align_*.json'), key=lambda p: __import__('os').path.getmtime(p))[-1]
AW = json.load(open(aj))
norm = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())
ev = []
for l in open('/home/user/Mendaki/work/gfx.ass'):
    if l.startswith('Dialogue') and ',Sub,' in l:
        p = l.split(',', 9)
        ts = lambda x: sum(float(q) * m for q, m in zip(x.split(':'), [3600, 60, 1]))
        ev.append((ts(p[1]), ts(p[2]), re.sub(r'\{[^}]*\}', '', p[9]).strip()))
caps = {}
for s0, s1, txt in ev:
    caps.setdefault((s0, s1), []).append(txt)
devs = []
for (s0, s1), lines in sorted(caps.items()):
    first = norm(' '.join(lines).split()[0])
    cand = [w for w in AW if norm(w['w']) == first and abs(w['s'] - s0) < 1.5]
    if cand:
        w = min(cand, key=lambda w: abs(w['s'] - s0)); devs.append(s0 - w['s'])
        print(f'  caption {s0:6.2f}s  word "{w["w"]}" spoken {w["s"]:6.2f}s  ({(s0 - w["s"]) * 1000:+.0f} ms)  {" / ".join(lines)[:50]}')
    else:
        print(f'  caption {s0:6.2f}s  first word not found nearby: {" / ".join(lines)[:50]}')
print(f'CAPTIONS {len(devs)} checked, start vs spoken word: mean {np.mean(devs)*1000:+.0f} ms, worst {max(abs(x) for x in devs)*1000:.0f} ms')
