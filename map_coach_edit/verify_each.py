# Transcribe each answer (all its pause-trimmed sub-clips joined) and compare with the subtitle text.
import sys, re, numpy as np
from edl import CLIPS, RAW, _a
from faster_whisper import WhisperModel
m = WhisperModel('medium.en', device='cpu', compute_type='int8', cpu_threads=4)
sil = np.zeros(8000, np.float32); N = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower()).split()
for p in range(len(RAW)):
    cs = [c for c in CLIPS if c['parent'] == p]; parts = []
    for c in cs:
        x = _a(c['key'])[int(c['a']*16000):int(c['b']*16000)].copy(); f = 128
        x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f); parts.append(x)
    s, _ = m.transcribe(np.concatenate([sil, *parts, sil]), beam_size=5, initial_prompt='MAP coach, PSLE, MENDAKI.')
    got = ''.join(t.text for t in s).strip(); want = ' '.join(x[0] for x in RAW[p][4])
    print(('OK  ' if N(got) == N(want) else 'DIFF'), p, '|', want, '||', got)
