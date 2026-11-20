# Builds assets/faces.json from the raw YuNet detections (footage frames every 0.2 s, plus
# each photo's faces mapped onto its card). Usage: python3 tools/build-faces.py raw.json
import json, sys
raw = json.load(open(sys.argv[1]))
def grow(b):  # pad for hair and chin
    x, y, w, h = b
    return [max(0, int(x - 0.12 * w)), max(0, int(y - 0.30 * h)), min(1920, int(x + 1.12 * w)), min(1080, int(y + 1.20 * h))]
samples = []
for f in raw["footage"]:
    t = f["t"]
    boxes = [grow(b) for b in f["faces"] if b[2] >= 14]
    for p in raw["photos"]:
        if p["start"] - 0.1 <= t < p["end"] + 0.1:
            boxes += [grow(b) for b in p["faces"]]
    samples.append([t, boxes])
json.dump({"about": "Faces on screen (1920x1080) every 0.2 s, as [x0,y0,x1,y1] padded for hair and chin: the footage plus the photo cards at their clip times. Text and glow are laid out to stay off them. Built with the YuNet face detector.", "step": 0.2, "samples": samples}, open("assets/faces.json", "w"), separators=(",", ":"))
print(len(samples), "samples")
