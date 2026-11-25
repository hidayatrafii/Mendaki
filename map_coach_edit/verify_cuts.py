import sys, numpy as np, re, difflib
sys.path.insert(0, '.'); from edl import CLIPS, _a
from faster_whisper import WhisperModel
parts = []
for c in CLIPS:
    a = _a(c['key'])[int(c['a']*16000):int(c['b']*16000)].copy()
    f = 160; a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
    parts.append(a)
x = np.concatenate(parts)
m = WhisperModel('medium.en', device='cpu', compute_type='int8', cpu_threads=4)
segs, _ = m.transcribe(x, beam_size=5, word_timestamps=True, condition_on_previous_text=False)
got = [w.word.strip() for s in segs for w in s.words]
want = ' '.join(s[0] for c in CLIPS for s in c['subs']).split()
N = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())
sm = difflib.SequenceMatcher(None, [N(w) for w in want], [N(w) for w in got], autojunk=False)
print('ratio', round(sm.ratio(), 3))
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != 'equal': print(op, '| want:', ' '.join(want[i1:i2]), '| heard:', ' '.join(got[j1:j2]))
