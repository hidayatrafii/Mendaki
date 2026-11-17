"""Per-clip colour normalisation + shared look, built from measured clip stats."""
import json, math

STATS = json.load(open('/home/user/Mendaki/work/colorstats.json'))
TARGET_RG, TARGET_BG = 1.10, 0.90
LOOK = "curves=master='0/0 0.25/0.23 0.75/0.77 1/1'"


def grade(key, strength=0.6):
    s = STATS[key]
    r, g, b = s['rgb']
    rg, bg = r / g, b / g
    gR = (TARGET_RG / rg) ** strength
    gB = (TARGET_BG / bg) ** strength
    lum = 0.2126 * gR + 0.7152 + 0.0722 * gB
    gR, gG, gB = gR / lum, 1 / lum, gB / lum
    blk = max(0.0, (s['p2'] - 6) / 255) if s['p2'] > 8 else 0.0
    p50 = s['p50'] / 255
    tgt = (0.35 * 128 + 0.65 * s["p50"]) / 255
    gamma = min(max(math.log(p50) / math.log(tgt), 0.85), 1.25)
    sat = min(max((40 / s['sat']) ** 0.6, 0.85, ), 1.5)
    parts = []
    if blk > 0:
        parts.append(f'colorlevels=rimin={blk:.3f}:gimin={blk:.3f}:bimin={blk:.3f}')
    parts.append(f'colorchannelmixer=rr={gR:.4f}:gg={gG:.4f}:bb={gB:.4f}')
    parts.append(f'eq=gamma={gamma:.3f}:saturation={sat:.3f}:contrast=1.05')
    parts.append(LOOK)
    return ','.join(parts)
