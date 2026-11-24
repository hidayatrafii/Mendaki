"""Tone-grade event photos: pull down highlights, add contrast and a little colour.

Usage: python3 exports/mou_template/grade_photos.py
Reads exports/mou_template/photos/*.jpg, writes exports/mou_template/photos/graded/*.jpg (originals untouched).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

HERE = Path(__file__).resolve().parent
SRC, DST = HERE / "photos", HERE / "photos" / "graded"


def grade(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255.0
    a = a ** 1.22                                  # darken mid-tones slightly (less washed out)
    a = np.where(a > 0.62, 0.62 + (a - 0.62) * 0.62, a)  # roll off highlights
    a = (a - 0.5) * 1.20 + 0.5                     # contrast
    a = a - 0.015                                  # deepen blacks a touch
    out = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    out = ImageEnhance.Color(out).enhance(1.14)    # gentle saturation
    return ImageEnhance.Sharpness(out).enhance(1.15)


DST.mkdir(exist_ok=True)
for f in sorted(SRC.glob("*.jpg")):
    grade(Image.open(f)).save(DST / f.name, quality=93)
    print("graded", f.name)
