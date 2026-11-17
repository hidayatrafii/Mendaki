"""Neutral, soft colour grade: per-clip white balance toward neutral, no saturation boosts, lowered contrast."""
import json, math

STATS = json.load(open('/home/user/Mendaki/work/colorstats.json'))
TARGET_RG, TARGET_BG = 1.0, 0.98          # neutral grey-world target for mid-tones
CONTRAST = 0.92                            # softer than camera
LIFT = 0.025                               # small black lift = gentle, not crushed

# iPhone HLG clips: soft, neutral, slightly cooler to keep skin from going orange
IPHONE_SOFT = (f'eq=contrast=0.86:saturation=0.82:gamma=1.04,'
               f'colorchannelmixer=rr=0.96:gg=1.0:bb=1.03,'
               f'colorlevels=romin={LIFT}:gomin={LIFT}:bomin={LIFT}')


def grade(key):
    if key.startswith('IMG_'):
        return IPHONE_SOFT
    s = STATS[key]
    r, g, b = s['rgb']
    rg, bg = r / g, b / g
    # warm indoor clips get a stronger correction than daylight clips
    strength = 0.9 if rg > 1.08 else 0.7
    gR = (TARGET_RG / rg) ** strength
    gB = (TARGET_BG / bg) ** strength
    lum = 0.2126 * gR + 0.7152 + 0.0722 * gB
    gR, gG, gB = gR / lum, 1 / lum, gB / lum
    p50 = s['p50'] / 255
    tgt = (0.35 * 128 + 0.65 * s['p50']) / 255
    gamma = min(max(math.log(p50) / math.log(tgt), 0.88), 1.2)
    # never boost saturation; pull down already-saturated clips
    sat = min(max((28 / s['sat']) ** 0.4, 0.82), 1.0)
    return (f'colorchannelmixer=rr={gR:.4f}:gg={gG:.4f}:bb={gB:.4f},'
            f'eq=gamma={gamma:.3f}:saturation={sat:.3f}:contrast={CONTRAST},'
            f'colorlevels=romin={LIFT}:gomin={LIFT}:bomin={LIFT}')
