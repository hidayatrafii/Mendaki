# Transcribe the finished video and check every subtitle starts within 0.25 s of its first spoken word.
import sys, re, subprocess, numpy as np
from faster_whisper import WhisperModel
vid, srt = sys.argv[1], sys.argv[2]
a = np.frombuffer(subprocess.run(["ffmpeg","-loglevel","error","-i",vid,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout,np.int16).astype(np.float32)/32768
m = WhisperModel('medium.en', device='cpu', compute_type='int8', cpu_threads=4)
segs, _ = m.transcribe(a, beam_size=5, word_timestamps=True, condition_on_previous_text=False)
words = [(w.start, re.sub(r'[^a-z0-9]','',w.word.lower())) for s in segs for w in s.words]
def tsec(x): h,m_,s = x.split(':'); return int(h)*3600+int(m_)*60+float(s.replace(',','.'))
bad = 0; offs = []
for blk in open(srt).read().strip().split('\n\n'):
    L = blk.split('\n'); st = tsec(L[1].split(' --> ')[0]); first = re.sub(r'[^a-z0-9]','',L[2].split()[0].lower())
    cand = [t for t, w in words if abs(t - st) < 1.5 and (w == first or w[:3] == first[:3])]
    if not cand: print('?? no match', round(st,2), L[2]); continue
    t = min(cand, key=lambda t: abs(t - st)); offs.append(t - st)
    if abs(t - st) > 0.25: bad += 1; print(f'OFF {t-st:+.2f}s', round(st,2), L[2])
print(f'{len(offs)} lines matched, median offset {np.median(offs):+.3f}s, max |offset| {np.max(np.abs(offs)):.2f}s, {bad} over 0.25s')
