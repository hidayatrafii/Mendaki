"""Remove the burned-in name tag with LaMa (ONNX) using a pixel-exact static mask."""
import sys, os
import numpy as np, cv2, onnxruntime as ort
sys.argv_saved = list(sys.argv); sys.argv = ["x"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3 as r  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(os.path.dirname(HERE), "models", "lama_fp32.onnx")
OUT = os.path.join(HERE, "fixed"); os.makedirs(OUT, exist_ok=True)
CORE_Y0 = 1020                       # core.npy covers rows 1020..1380
RY0, RY1 = 960, 1472                 # patch band (512 tall)
WINDOWS = [130, 450]                 # x-starts of two 512-wide tiles covering x 130..962
FIRST, LAST = 425, 615               # frame indices where the tag is on screen

core = np.zeros((1920, 1080), np.uint8)
c = np.load(os.path.join(HERE, "core.npy"))
core[CORE_Y0:CORE_Y0 + c.shape[0]] = c
core_d = cv2.dilate(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))


def frame_mask(f):
    b = f.astype(np.int16)
    yel = (b[..., 2] > 150) & (b[..., 1] > 120) & (b[..., 0] < 170) & (b[..., 2] - b[..., 0] > 45)
    m = (yel & (core_d > 0)).astype(np.uint8)          # only letters that have typed in so far
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    m = m | np.roll(np.roll(m, 4, 0), 4, 1)            # cover the drop shadow (down-right)
    allowed = (core_d > 0) | (np.roll(np.roll(core_d, 4, 0), 4, 1) > 0)
    return (m.astype(bool) & allowed).astype(np.uint8)


def main(a, b, threads):
    so = ort.SessionOptions(); so.intra_op_num_threads = threads
    sess = ort.InferenceSession(MODEL, so)
    for n, f in r.read_frames(a, b):
        m = frame_mask(f)
        band = f[RY0:RY1].copy()
        if m[RY0:RY1].any():
            for x0 in WINDOWS:
                tile = band[:, x0:x0 + 512]
                mt = m[RY0:RY1, x0:x0 + 512]
                if not mt.any():
                    continue
                img = cv2.cvtColor(tile, cv2.COLOR_BGR2RGB).astype(np.float32).transpose(2, 0, 1)[None] / 255.0
                msk = mt.astype(np.float32)[None, None]
                out = sess.run(None, {"image": img, "mask": msk})[0][0].transpose(1, 2, 0)
                if out.max() <= 1.5:
                    out = out * 255.0
                out = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
                feather = cv2.GaussianBlur(mt.astype(np.float32), (0, 0), 1.2)
                feather = np.maximum(feather, mt.astype(np.float32))[..., None]
                band[:, x0:x0 + 512] = (tile * (1 - feather) + out * feather).astype(np.uint8)
        cv2.imwrite(os.path.join(OUT, f"{n:05d}.png"), band)
        print("done", n, flush=True)


if __name__ == "__main__":
    a, b, th = map(int, sys.argv_saved[1:4])
    main(a, b, th)
