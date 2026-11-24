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
        run(["ffmpeg","-loglevel","error","-y","-ss",f"{a:.3f}","-i",SRC,"-t",f"{d:.3f}","-vf",vf,
             "-af",f"afade=t=in:d=0.012,afade=t=out:st={d-0.02:.3f}:d=0.02",
             "-c:v","libx264","-crf","12","-preset","fast","-pix_fmt","yuv420p","-c:a","pcm_s16le","-ar","48000",o])
        inputs += ["-i", o]
    n = len(CLIPS)
    fc.append("".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc0][ac0]")
    fc.append(f"[vc0]tpad=stop_mode=clone:stop_duration={TAIL}[vc]")
    fc.append(f"[ac0]apad=pad_dur={TAIL}[ac]")
    last, idx = "vc", n
    for j,B in enumerate(BROLL):
        s, e = B["start"], B["end"]
        chained = any(abs(B2["start"] - e) < 0.05 for B2 in BROLL)   # back-to-back: hold under next one's fade-in
        if chained: e = e + 0.3
        clip = f"{W}/broll/col{j}.mp4"
        run(["python3","-I",f"{W}/collage.py",json.dumps({"photos":[f"{W}/broll/{p}" for p in B["photos"]],
             "appear":[x-s for x in B["appear"]],"dur":e-s,"out":clip})])
        inputs += ["-i", clip]
        fout = "" if chained or e >= TOTAL-0.05 else f",fade=t=out:st={e-s-0.2:.3f}:d=0.2:alpha=1"
        fc.append(f"[{idx}:v]format=yuva420p,fade=t=in:d=0.2:alpha=1{fout},setpts=PTS-STARTPTS+{s}/TB[b{j}]")
        fc.append(f"[{last}][b{j}]overlay=0:0:enable='between(t,{s},{e})':eof_action=pass[o{j}]")
        last = f"o{j}"; idx += 1
    inputs += ["-loop","1","-t",f"{TOTAL:.3f}","-i",LT]
    fc.append(f"[{idx}:v]format=rgba,fps={FPS},fade=t=in:st=0.4:d=0.3:alpha=1,fade=t=out:st=3.45:d=0.3:alpha=1[lt]")
    fc.append(f"[{last}][lt]overlay=0:0:enable='between(t,0.3,3.8)':shortest=1[olt]")
    CARDS = json.load(open("/home/user/Mendaki/number_cards/cards.json")); cur = "olt"
    for c in CARDS:
        idx += 1; s0, e0 = c["start"], c["end"]
        inputs += ["-loop","1","-t",f"{TOTAL:.3f}","-i",f"/home/user/Mendaki/number_cards/{c['id']}.png"]
        fc.append(f"[{idx}:v]format=rgba,fps={FPS},fade=t=in:st={s0}:d=0.22:alpha=1,fade=t=out:st={e0-0.2:.3f}:d=0.2:alpha=1[cd{idx}]")
        fc.append(f"[{cur}][cd{idx}]overlay=x=0:y='24*max(0\\,1-(t-{s0})/0.25)':enable='between(t,{s0},{e0})':shortest=1[k{idx}]")
        cur = f"k{idx}"
    fc.append(f"[{cur}]subtitles={W}/subs.ass:fontsdir=/home/user/Mendaki/fonts,format=yuv420p,fade=t=out:st={TOTAL-0.7:.3f}:d=0.7[vout]")
    inputs += ["-i", "/home/user/Mendaki/footage/music/bgm_upbeat.mp3"]; mi = idx + 1
    EV = [[0.4,"lt"]] + [[c["start"],"card"] for c in CARDS] + [[x,"pop"] for B in BROLL for x in B["appear"]]
    run(["python3","-I",f"{W}/sfx.py",json.dumps(EV),f"{TOTAL:.3f}",f"{W}/sfx.wav"])
    inputs += ["-i", f"{W}/sfx.wav"]; si_ = mi + 1
    fc.append("[ac]loudnorm=I=-12:TP=-1.5:LRA=11,aresample=48000,asplit=2[voice][key]")
    # music bed: ~-27 LUFS, gently ducked further whenever he speaks
    fc.append(f"[{mi}:a]atrim=0.15:{TOTAL+0.15:.3f},asetpts=PTS-STARTPTS,aresample=48000,volume=-11dB,afade=t=in:d=0.4,afade=t=out:st={TOTAL-2.6:.3f}:d=2.6[mus]")
    fc.append("[mus][key]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=400[duck]")
    fc.append(f"[{si_}:a]aresample=48000,pan=stereo|c0=c0|c1=c0[sfx]")
    fc.append("[voice][duck][sfx]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.8[aout]")
    run(["ffmpeg","-loglevel","error","-y",*inputs,"-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]",
         "-r",str(FPS),"-c:v","libx264","-crf","18","-preset","medium","-profile:v","high","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","192k","-movflags","+faststart","-t",f"{TOTAL:.3f}",out])
    print("TOTAL", round(TOTAL,2))
