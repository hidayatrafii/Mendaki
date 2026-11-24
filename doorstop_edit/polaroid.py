import sys, math, subprocess
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
W, H, FPS = 1080, 1920, 30
def ease_out_back(x, s=1.4):
    x -= 1; return x*x*((s+1)*x + s) + 1
def build(photo, dur, angle, out):
    src = Image.open(photo).convert("RGB")
    # background: cover-fit, heavy blur, darkened
    sc = max(W/src.width, H/src.height)
    bg = src.resize((math.ceil(src.width*sc), math.ceil(src.height*sc)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width-W)//2+W, (bg.height-H)//2+H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(45))).enhance(0.62)
    # polaroid card (2x supersampled)
    S = 2; pw = 760*S; ph = round(pw*src.height/src.width)
    side, top, bottom = 34*S, 34*S, 150*S
    cw, ch = pw+2*side, ph+top+bottom
    card = Image.new("RGBA", (cw, ch), (250, 249, 245, 255))
    card.paste(src.resize((pw, ph), Image.LANCZOS), (side, top))
    d = ImageDraw.Draw(card); d.rectangle([side-1, top-1, side+pw, top+ph], outline=(225,223,218,255), width=2)
    # tape strip
    tape = Image.new("RGBA", (190*S, 52*S), (245, 236, 205, 175))
    tape = tape.rotate(-angle*1.6, expand=True, resample=Image.BICUBIC)
    pad = 60*S
    big = Image.new("RGBA", (cw+2*pad, ch+2*pad), (0,0,0,0))
    # shadow
    sh = Image.new("RGBA", big.size, (0,0,0,0))
    ImageDraw.Draw(sh).rectangle([pad+10*S, pad+16*S, pad+cw+10*S, pad+ch+16*S], fill=(0,0,0,120))
    sh = sh.filter(ImageFilter.GaussianBlur(14*S))
    big.alpha_composite(sh); big.alpha_composite(card, (pad, pad))
    big.alpha_composite(tape, (pad+cw//2-tape.width//2, pad-tape.height//2+6*S))
    big = big.rotate(angle, expand=True, resample=Image.BICUBIC)
    big = big.resize((big.width//S, big.height//S), Image.LANCZOS)
    cx, cy = W//2, 820
    n = int(round(dur*FPS))
    p = subprocess.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-c:v","libx264","-crf","14","-preset","fast","-pix_fmt","yuv420p",out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i/FPS
        x = min(1, t/0.45)
        s = 0.86 + 0.14*ease_out_back(x) + 0.03*(t/dur)          # pop in, then slow push
        dy = (1-min(1, t/0.45))**2 * 140                           # rise up into place
        a_in = min(1, t/0.2); a_out = min(1, (dur-t)/0.25)
        im = big.resize((max(1,int(big.width*s)), max(1,int(big.height*s))), Image.BILINEAR)
        fr = bg.copy().convert("RGBA")
        fr.alpha_composite(im, (int(cx-im.width/2), int(cy-im.height/2+dy)))
        fr = fr.convert("RGB")
        # whole b-roll (incl. bg) fades over the talking head at start/end
        alpha = min(a_in, a_out)
        if alpha < 1:
            fr = Image.blend(Image.new("RGB",(W,H),(0,0,0)), fr, 1.0) if False else fr
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
if __name__ == "__main__":
    build(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
