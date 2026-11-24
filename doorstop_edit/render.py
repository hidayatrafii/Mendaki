import sys, json, subprocess, os
W = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, W)
from edl import CLIPS
SRC = "/home/user/Mendaki/footage/doorstop_raw.mov"; FPS = 30
SPEECH = sum(b-a for a,b,_,_ in CLIPS)
TAIL = 2.5   # music + closing photo after the last word, then fade to black
TOTAL = SPEECH + TAIL
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
             "-af",f"afade=t=in:d=0.012,afade=t=out:st={d-0.02:.3f}:d=0.02",
             "-c:v","libx264","-crf","12","-preset","fast","-pix_fmt","yuv420p","-c:a","pcm_s16le","-ar","48000",o])
        inputs += ["-i", o]
    n = len(CLIPS)
    fc.append("".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc0][ac0]")
    fc.append(f"[vc0]tpad=stop_mode=clone:stop_duration={TAIL}[vc]")
    fc.append(f"[ac0]apad=pad_dur={TAIL}[ac]")
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
    fc.append(f"[olt]subtitles={W}/subs.ass:fontsdir=/home/user/Mendaki/fonts,format=yuv420p,fade=t=out:st={TOTAL-0.7:.3f}:d=0.7[vout]")
    inputs += ["-i", "/home/user/Mendaki/footage/music/bgm.mp3"]; mi = idx + 1
    fc.append("[ac]loudnorm=I=-14:TP=-2:LRA=11,aresample=48000,asplit=2[voice][key]")
    # music bed: ~-27 LUFS, gently ducked further whenever he speaks
    fc.append(f"[{mi}:a]atrim=0:{TOTAL:.3f},asetpts=PTS-STARTPTS,aresample=48000,volume=-10dB,afade=t=in:d=0.4,afade=t=out:st={TOTAL-2.6:.3f}:d=2.6[mus]")
    fc.append("[mus][key]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=400[duck]")
    fc.append("[voice][duck]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.84[aout]")
    run(["ffmpeg","-loglevel","error","-y",*inputs,"-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]",
         "-r",str(FPS),"-c:v","libx264","-crf","18","-preset","medium","-profile:v","high","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","192k","-movflags","+faststart","-t",f"{TOTAL:.3f}",out])
    print("TOTAL", round(TOTAL,2))
