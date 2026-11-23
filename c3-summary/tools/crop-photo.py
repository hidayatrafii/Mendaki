# Face-aware crop: cuts a photo to the given aspect, keeping the faces in frame, and resizes.
# usage: python3 tools/crop-photo.py <yunet.onnx> <in> <out> <width> <height>
import cv2, sys, numpy as np
model, src, out, W, H = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
img = cv2.imread(src); h, w = img.shape[:2]
s = 1200 / max(h, w); sm = cv2.resize(img, (int(w * s), int(h * s)))
det = cv2.FaceDetectorYN.create(model, "", (sm.shape[1], sm.shape[0]), 0.6, 0.3, 5000)
_, f = det.detect(sm)
target = W / H
if w / h > target: cw, ch = int(h * target), h
else: cw, ch = w, int(w / target)
if f is not None and len(f):
    f = f[:, :4] / s
    # centre on the faces, weighted by size; keep the topmost face's hair in frame
    cx = np.average(f[:, 0] + f[:, 2] / 2, weights=f[:, 2] ** 2)
    top = (f[:, 1] - f[:, 3] * 0.6).min(); bot = (f[:, 1] + f[:, 3] * 1.4).max()
    cy = (top + bot) / 2 if bot - top < ch * 0.9 else top + ch * 0.45
else:
    cx, cy = w / 2, h * 0.45
x0 = int(min(max(cx - cw / 2, 0), w - cw)); y0 = int(min(max(cy - ch / 2, 0), h - ch))
crop = img[y0:y0 + ch, x0:x0 + cw]
cv2.imwrite(out, cv2.resize(crop, (W, H), interpolation=cv2.INTER_AREA if cw > W else cv2.INTER_LANCZOS4), [cv2.IMWRITE_JPEG_QUALITY, 90])
print(out, f"{w}x{h} -> crop {cw}x{ch} at {x0},{y0}; faces", 0 if f is None else len(f))
