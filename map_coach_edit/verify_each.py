import sys, numpy as np
sys.path.insert(0, '.'); from edl import CLIPS, _a
from faster_whisper import WhisperModel
m = WhisperModel('medium.en', device='cpu', compute_type='int8', cpu_threads=4)
sil = np.zeros(8000, np.float32)
idx = [int(i) for i in sys.argv[1:]] or range(len(CLIPS))
for i in idx:
    c = CLIPS[i]; a = _a(c['key'])[int(c['a']*16000):int(c['b']*16000)]
    segs, _ = m.transcribe(np.concatenate([sil, a, sil]), beam_size=5, initial_prompt='MAP coach, PSLE, MENDAKI.')
    print(i, '|', ' '.join(s[0] for s in c['subs']), '||', ''.join(s.text for s in segs).strip())
