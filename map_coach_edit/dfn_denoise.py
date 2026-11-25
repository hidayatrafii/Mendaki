# DeepFilterNet3 speech enhancement for one interview source, with an attenuation limit so the voice stays natural.
#   python3 dfn_denoise.py SRC.MP4 OUT.wav [ATTEN_LIMIT_DB]
import sys, types, subprocess, numpy as np
if not hasattr(np, "long"): np.long = int          # removed in older numpy, still used by DeepFilterNet
import torchaudio
if not hasattr(torchaudio, "backend"):            # DeepFilterNet 0.5.6 imports a module removed from new torchaudio
    b = types.ModuleType("torchaudio.backend"); c = types.ModuleType("torchaudio.backend.common")
    class AudioMetaData: pass
    c.AudioMetaData = AudioMetaData; b.common = c
    sys.modules["torchaudio.backend"] = b; sys.modules["torchaudio.backend.common"] = c
import torch
from df.enhance import init_df, enhance
from scipy.io import wavfile
src, dst = sys.argv[1], sys.argv[2]; lim = float(sys.argv[3]) if len(sys.argv) > 3 else 15
# weights: DeepFilterNet3 (github download is blocked here; mirrored from huggingface fal/DeepFilterNet3)
model, state, _ = init_df("/home/user/Mendaki/work/dfn_model", post_filter=False, log_level="ERROR")
sr = state.sr()
x = np.frombuffer(subprocess.run(["ffmpeg","-loglevel","error","-i",src,"-vn","-ac","1","-ar",str(sr),"-f","s16le","-"],
                                 capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
torch.set_num_threads(4)
y = enhance(model, state, torch.from_numpy(x)[None], atten_lim_db=lim)[0].numpy()
wavfile.write(dst, sr, (np.clip(y, -1, 1) * 32767).astype(np.int16))
hop = sr // 20; db = lambda v: 20*np.log10(v+1e-9)
r = np.sqrt(np.mean(x[:len(x)//hop*hop].reshape(-1,hop)**2,1)); r2 = np.sqrt(np.mean(y[:len(y)//hop*hop].reshape(-1,hop)**2,1))
q = r <= np.percentile(r, 12)
print(f"{src.split('/')[-1]}: room tone {db(np.median(r[q])):.1f} -> {db(np.median(r2[q])):.1f} dB, speech {db(np.percentile(r,90)):.1f} -> {db(np.percentile(r2,90)):.1f} dB")
