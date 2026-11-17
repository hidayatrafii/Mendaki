"""Word timestamps of the assembled speech track (output timeline): python3 align.py in.wav out.json"""
import sys, json, numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
sr, x = wavfile.read(sys.argv[1]); x = x.astype(np.float32) / 32768
if x.ndim > 1: x = x.mean(1)
x = resample_poly(x, 1, sr // 16000).astype(np.float32)
m = WhisperModel('medium.en', device='cpu', compute_type='int8', cpu_threads=4)
segs, _ = m.transcribe(x, beam_size=5, word_timestamps=True, vad_filter=False,
                       initial_prompt='Speech by Minister Zaqy Mohamad on online extremism, AI, ISA, Singapore.')
json.dump([{'w': w.word.strip(), 's': w.start, 'e': w.end} for sg in segs for w in sg.words], open(sys.argv[2], 'w'), indent=0)
