import sys, json, subprocess, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edl import SEGS
W = "/home/user/Mendaki/work"
SRC = "/home/user/Mendaki/footage/doorstop_raw.mov"
FPS = 30

# output start time of each segment
starts, t = [], 0.0
for a, b, _ in SEGS:
    starts.append(t); t += b - a
TOTAL = t

# B-roll: (photo, start, end) in output time; set by covering cuts
BROLL = json.load(open(f"{W}/broll_plan.json"))

def make_broll(photo, dur, out):
    n = int(round(dur * FPS)) + 2
    fg = (f"[0:v]scale=4320:-2,zoompan=z='1+0.06*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x720:fps={FPS}[fg]")
    bg = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=-0.12,loop=loop={n}:size=1,fps={FPS}[bg]")
    fc = f"{fg};{bg};[bg][fg]overlay=0:(H-h)/2-110:shortest=1,trim=duration={dur},setpts=PTS-STARTPTS,format=yuv420p,fade=t=in:d=0.15,fade=t=out:st={dur-0.15}:d=0.15[v]"
    subprocess.run(["ffmpeg","-loglevel","error","-y","-loop","1","-i",photo,"-filter_complex",fc,"-map","[v]","-t",str(dur),"-r",str(FPS),"-c:v","libx264","-crf","16","-preset","fast","-pix_fmt","yuv420p",out],check=True)

if __name__ == "__main__":
    os.makedirs(f"{W}/segs", exist_ok=True)
    lst=[]
    for i,(a,b,_) in enumerate(SEGS):
        d=b-a; o=f"{W}/segs/s{i:02d}.mkv"; lst.append(o)
        subprocess.run(["ffmpeg","-loglevel","error","-y","-ss",f"{a:.3f}","-i",SRC,"-t",f"{d:.3f}",
          "-vf",f"fps={FPS}","-af",f"afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03",
          "-c:v","libx264","-crf","12","-preset","fast","-pix_fmt","yuv420p","-c:a","pcm_s16le","-ar","48000",o],check=True)
    inputs=[]; fc=[]
    for o in lst: inputs+=["-i",o]
    fc.append("".join(f"[{i}:v][{i}:a]" for i in range(len(lst))) + f"concat=n={len(lst)}:v=1:a=1[vc][ac]")
    last = "vc"; idx = len(lst)
    for k,(photo,s,e) in enumerate(BROLL):
        clip = f"{W}/broll/clip{k}.mp4"
        make_broll(f"{W}/broll/{photo}", e-s, clip)
        inputs += ["-i", clip]
        fc.append(f"[{idx}:v]setpts=PTS-STARTPTS+{s}/TB[b{k}]")
        fc.append(f"[{last}][b{k}]overlay=0:0:enable='between(t,{s},{e})':eof_action=pass[o{k}]")
        last=f"o{k}"; idx+=1
    # lower third 0.4s - 5.0s
    inputs += ["-loop","1","-t",str(TOTAL),"-i","/home/user/Mendaki/lower_thirds/zaqy_lower_third_9x16.png"]
    fc.append(f"[{idx}:v]format=rgba,fps={FPS},fade=t=in:st=0.4:d=0.3:alpha=1,fade=t=out:st=4.8:d=0.3:alpha=1[lt]")
    fc.append(f"[{last}][lt]overlay=0:0:enable='between(t,0.3,5.2)':shortest=1[olt]")
    fc.append(f"[olt]subtitles={W}/subs.ass:fontsdir=/home/user/Mendaki/fonts,format=yuv420p[vout]")
    fc.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
    out = sys.argv[1] if len(sys.argv)>1 else f"{W}/draft.mp4"
    subprocess.run(["ffmpeg","-loglevel","error","-stats","-y",*inputs,"-filter_complex",";".join(fc),
        "-map","[vout]","-map","[aout]","-r",str(FPS),"-c:v","libx264","-crf","18","-preset","medium","-profile:v","high",
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart","-t",f"{TOTAL:.3f}",out],check=True)
    print("TOTAL", TOTAL)
