import sys, json, subprocess, os
W = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, W)
from edl import CLIPS
SRC = "/home/user/Mendaki/footage/doorstop_raw.mov"; FPS = 30
TOTAL = sum(b-a for a,b,_,_ in CLIPS)
BROLL = json.load(open(f"{W}/broll_plan.json"))
LT = "/home/user/Mendaki/lower_thirds/zaqy_lower_third_9x16.png"
def run(c): subprocess.run(c, check=True)
if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(f"{W}/segs", exist_ok=True); os.makedirs(f"{W}/broll", exist_ok=True)
    inputs, fc = [], []
    for i,(a,b,si,k) in enumerate(CLIPS):
        d=b-a; o=f"{W}/segs/c{i:02d}.mkv"
        # alternate a gentle punch-in on every other clip within a segment, so filler cuts read as camera changes
        vf = f"fps={FPS}"
        if k % 2 == 1:
            vf += ",scale=1210:2150:flags=lanczos,crop=1080:1920:60:60"
        run(["ffmpeg","-loglevel","error","-y","-ss",f"{a:.3f}","-i",SRC,"-t",f"{d:.3f}","-vf",vf,
             "-af",f"afade=t=in:d=0.015,afade=t=out:st={d-0.025:.3f}:d=0.025",
             "-c:v","libx264","-crf","12","-preset","fast","-pix_fmt","yuv420p","-c:a","pcm_s16le","-ar","48000",o])
        inputs += ["-i", o]
    n = len(CLIPS)
    fc.append("".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    last, idx = "vc", n
    for j,(photo,s,e,ang) in enumerate(BROLL):
        clip = f"{W}/broll/pol{j}.mp4"
        run(["python3","-I",f"{W}/polaroid.py",f"{W}/broll/{photo}",str(e-s),str(ang),clip])
        inputs += ["-i", clip]
        fc.append(f"[{idx}:v]format=yuva420p,fade=t=in:d=0.2:alpha=1,fade=t=out:st={e-s-0.2:.3f}:d=0.2:alpha=1,setpts=PTS-STARTPTS+{s}/TB[b{j}]")
        fc.append(f"[{last}][b{j}]overlay=0:0:enable='between(t,{s},{e})':eof_action=pass[o{j}]")
        last = f"o{j}"; idx += 1
    inputs += ["-loop","1","-t",f"{TOTAL:.3f}","-i",LT]
    fc.append(f"[{idx}:v]format=rgba,fps={FPS},fade=t=in:st=0.4:d=0.3:alpha=1,fade=t=out:st=4.8:d=0.3:alpha=1[lt]")
    fc.append(f"[{last}][lt]overlay=0:0:enable='between(t,0.3,5.2)':shortest=1[olt]")
    fc.append(f"[olt]subtitles={W}/subs.ass:fontsdir=/home/user/Mendaki/fonts,format=yuv420p[vout]")
    fc.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
    run(["ffmpeg","-loglevel","error","-y",*inputs,"-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]",
         "-r",str(FPS),"-c:v","libx264","-crf","18","-preset","medium","-profile:v","high","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","192k","-movflags","+faststart","-t",f"{TOTAL:.3f}",out])
    print("TOTAL", round(TOTAL,2))
