# Polaroid collage b-roll: 1-4 polaroids pop in one by one over a blurred backdrop.
import sys, json, math, subprocess
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
W, H, FPS = 1080, 1920, 30
LAYOUTS = {  # (pw, [(cx, cy, angle), ...])
 1: (760, [(540, 820, -4)]),
 2: (520, [(400, 540, -5), (680, 930, 4)]),
 3: (440, [(330, 520, -5), (760, 640, 5), (530, 960, -3)]),
 4: (380, [(300, 400, -6), (780, 440, 5), (320, 740, 4), (770, 770, -5)]),
 "3top": (420, [(300, 410, -5), (780, 500, 5), (540, 770, -3)]),   # 3 photos kept above a number card
}
def ease_out_back(x, s=1.5):
    x -= 1; return x*x*((s+1)*x + s) + 1
def polaroid(path, pw, angle):
    src = Image.open(path).convert("RGB"); S = 2; k = pw/760
    p = int(pw*S); ph = round(p*src.height/src.width)
    side, top, bottom = int(34*k*S), int(34*k*S), int(150*k*S)
    cw, ch = p+2*side, ph+top+bottom
    card = Image.new("RGBA", (cw, ch), (250, 249, 245, 255))
    card.paste(src.resize((p, ph), Image.LANCZOS), (side, top))
    ImageDraw.Draw(card).rectangle([side-1, top-1, side+p, top+ph], outline=(225, 223, 218, 255), width=2)
    tape = Image.new("RGBA", (int(190*k*S), int(52*k*S)), (245, 236, 205, 175)).rotate(-angle*1.6, expand=True, resample=Image.BICUBIC)
    pad = int(60*k*S)
    big = Image.new("RGBA", (cw+2*pad, ch+2*pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", big.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad+int(10*k*S), pad+int(16*k*S), pad+cw+int(10*k*S), pad+ch+int(16*k*S)], fill=(0, 0, 0, 130))
    big.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14*k*S))); big.alpha_composite(card, (pad, pad))
    big.alpha_composite(tape, (pad+cw//2-tape.width//2, pad-tape.height//2+int(6*k*S)))
    big = big.rotate(angle, expand=True, resample=Image.BICUBIC)
    return big.resize((big.width//S, big.height//S), Image.LANCZOS)
def build(photos, appear, dur, out, layout=None):
    n = len(photos); pw, slots = LAYOUTS[layout or n]
    src = Image.open(photos[0]).convert("RGB")
    sc = max(W/src.width, H/src.height)
    bg = src.resize((math.ceil(src.width*sc), math.ceil(src.height*sc)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width-W)//2+W, (bg.height-H)//2+H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(45))).enhance(0.55)
    items = [polaroid(p, pw, a) for p, (_, _, a) in zip(photos, slots)]
    nf = int(round(dur*FPS))
    proc = subprocess.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-crf","14","-preset","fast","-pix_fmt","yuv420p",out], stdin=subprocess.PIPE)
    for f in range(nf):
        t = f/FPS
        z = 1.0 + 0.06*t/max(dur, 1)                      # slow push-in on the backdrop
        cw, ch = W/z, H/z; x0, y0 = (W-cw)/2, (H-ch)/2
        fr = bg.resize((W, H), Image.BILINEAR, box=(x0, y0, x0+cw, y0+ch)).convert("RGBA")
        for im, (cx, cy, _), ta in zip(items, slots, appear):
            if t < ta: continue
            x = min(1, (t-ta)/0.35)
            s = 0.7 + 0.3*ease_out_back(x) + 0.05*(t-ta)/max(dur, 1)
            dy = (1-x)**2 * 90; a = min(1, (t-ta)/0.12)
            r = im.resize((max(1, int(im.width*s)), max(1, int(im.height*s))), Image.BILINEAR)
            if a < 1:
                al = r.getchannel("A").point(lambda v: int(v*a)); r.putalpha(al)
            fr.alpha_composite(r, (int(cx-r.width/2), int(cy-r.height/2+dy)))
        proc.stdin.write(fr.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()
if __name__ == "__main__":
    a = json.loads(sys.argv[1]); build(a["photos"], a["appear"], a["dur"], a["out"], a.get("layout"))
