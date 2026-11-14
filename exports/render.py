import numpy as np, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC, AUD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
LIMIT = float(sys.argv[4]) if len(sys.argv)>4 else 15.0
W,H,FPS=1080,1920,30; NF=int(LIMIT*FPS)
FD='/usr/share/fonts/opentype/inter/'; MONO='/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf'
EMO='/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
CY=(94,242,255); LIME=(200,255,90); WHITE=(255,255,255); INK=(10,14,40)
def F(name,size): return ImageFont.truetype(FD+name,size)
def clamp(x,a=0,b=1): return max(a,min(b,x))
def ease_out(x): x=clamp(x); return 1-(1-x)**3
def back_out(x):
    x=clamp(x); c=1.9; return 1+(c+1)*(x-1)**3+c*(x-1)**2
def emoji(ch,size):
    f=ImageFont.truetype(EMO,109); im=Image.new('RGBA',(160,160)); ImageDraw.Draw(im).text((10,10),ch,font=f,embedded_color=True)
    im=im.crop(im.getbbox()); return im.resize((size,int(size*im.height/im.width)),Image.LANCZOS)

# ---------- word tokens: (text, font, color, highlight_bg or None) / emoji tokens
def word_img(tok):
    if tok[0]=='emoji': return emoji(tok[1],tok[2])
    text,font,col,bg=tok
    l,t,r,b=font.getbbox(text); pad=(26,10) if bg else (4,4)
    asc,desc=font.getmetrics(); w=r-l+2*pad[0]; h=asc+desc+2*pad[1]
    im=Image.new('RGBA',(w+20,h+20)); d=ImageDraw.Draw(im)
    if bg: d.rounded_rectangle((10,10,10+w,10+h),radius=h//2.6,fill=bg+(255,))
    else:  # soft shadow
        sh=Image.new('RGBA',im.size); ImageDraw.Draw(sh).text((10+pad[0]-l,10+pad[1]+4),text,font=font,fill=(0,0,0,170))
        im=Image.alpha_composite(im,sh.filter(ImageFilter.GaussianBlur(7))); d=ImageDraw.Draw(im)
    d.text((10+pad[0]-l,10+pad[1]),text,font=font,fill=col+(255,))
    return im
def layout(lines,cy,gap=8,lgap=6):
    """lines: list of token lists. returns list of (img,x,y,order)"""
    out=[]; rows=[[word_img(t) for t in ln] for ln in lines]
    hs=[max(i.height for i in r) for r in rows]; tot=sum(hs)+lgap*(len(rows)-1)
    y=cy-tot//2; k=0
    for r,h in zip(rows,hs):
        wsum=sum(i.width for i in r)+gap*(len(r)-1); x=(W-wsum)//2
        for i in r: out.append((i,x,y+(h-i.height)//2,k)); x+=i.width+gap; k+=1
        y+=h+lgap
    return out

# ---------- text blocks: (start,end,items,stagger,style)
B=[]
fT=F('InterDisplay-Black.otf',150); fT2=F('InterDisplay-Black.otf',118)
fQ=F('InterDisplay-ExtraBold.otf',84); fQb=F('InterDisplay-Black.otf',92)
fS=F('InterDisplay-Black.otf',104); fs=F('InterDisplay-Bold.otf',64)
B.append((0.15,2.85,layout([[('SPACE',fT,WHITE,None)],[('DATA FOUNDATIONS',F('InterDisplay-Black.otf',88),WHITE,None)],[('WORKSHOP',fT2,CY,None)]],1300,lgap=-6),0.12,'slide'))
B.append((3.0,5.9,layout([[('Ever wondered what',fQ,WHITE,None)],[('Earth',fQb,INK,LIME),('looks like',fQ,WHITE,None)],[('from',fQ,WHITE,None),('space?',fQb,INK,CY),('emoji','🛰️',96)]],1280,gap=14,lgap=10),0.09,'pop'))
B.append((6.0,8.9,layout([[('hands-on with',fs,WHITE,None)],[('DIGITAL MAPS',fS,INK,CY),('emoji','🗺️',100)]],1330,gap=14,lgap=12),0.12,'pop'))
B.append((9.0,11.9,layout([[('& real',fs,WHITE,None)],[('SATELLITE',fS,INK,LIME)],[('IMAGERY',fS,INK,LIME),('emoji','🛰️',100)]],1290,gap=14,lgap=10),0.12,'pop'))
B.append((12.05,13.45,layout([[('our young',fs,WHITE,None)],[('SPACE EXPLORERS',F('InterDisplay-Black.otf',96),WHITE,None),('emoji','🚀',96)]],1360,gap=14,lgap=8),0.1,'pop'))
B.append((13.55,15.2,layout([[('a whole new way',fQ,WHITE,None)],[('to see',fQ,WHITE,None),('our world',fQb,INK,CY),('emoji','🌍',92)]],1240,gap=14,lgap=10),0.1,'pop'))

def draw_block(frame,t,blk):
    s,e,items,stag,style=blk
    if t<s or t>e+0.01: return
    out=clamp((e-t)/0.25)  # exit fade
    for img,x,y,k in items:
        lt=(t-s-k*stag)/0.38
        if lt<=0: continue
        if style=='slide':
            p=ease_out(lt); dy=int((1-p)*90); a=p*out
            im=img
            frame.alpha_composite(fade(im,a),(x,y+dy))
        else:
            sc=max(0.05,back_out(lt)); a=clamp(lt*2.5)*out
            im=img if abs(sc-1)<0.01 else img.resize((max(1,int(img.width*sc)),max(1,int(img.height*sc))),Image.BILINEAR)
            frame.alpha_composite(fade(im,a),(x+(img.width-im.width)//2,y+(img.height-im.height)//2))
def fade(im,a):
    if a>=0.999: return im
    im=im.copy(); al=im.getchannel('A').point(lambda v:int(v*a)); im.putalpha(al); return im

# ---------- static HUD
fm=ImageFont.truetype(MONO,30); fm2=ImageFont.truetype(MONO,26)
hud=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(hud)
m=48; L=70; top=250; bot=1640
for (x,y,sx,sy) in [(m,top,1,1),(W-m,top,-1,1),(m,bot,1,-1),(W-m,bot,-1,-1)]:
    d.line([(x,y),(x+sx*L,y)],fill=CY+(230,),width=5); d.line([(x,y),(x,y+sy*L)],fill=CY+(230,),width=5)
# readability gradient bottom-centre
grad=np.zeros((H,W,4),np.uint8); ys=np.arange(H)
a=np.clip(1-np.abs(ys-1330)/520,0,1)**1.6*150; grad[...,3]=a[:,None].astype(np.uint8)
grad=Image.fromarray(grad,'RGBA')
vig=np.zeros((H,W,4),np.uint8); yy,xx=np.mgrid[0:H,0:W]; r=np.sqrt(((xx-W/2)/(W*0.75))**2+((yy-H/2)/(H*0.72))**2)
vig[...,3]=(np.clip(r-0.55,0,1)*300).clip(0,170).astype(np.uint8); vig=Image.fromarray(vig,'RGBA')
grain=[(np.random.default_rng(i).normal(0,9,(H//2,W//2,1))).repeat(2,0).repeat(2,1) for i in range(4)]

def hud_dyn(frame,t):
    d=ImageDraw.Draw(frame)
    blink = int(t*2)%2==0
    if blink: d.ellipse((m+18,top+22,m+38,top+42),fill=(255,60,80,255))
    d.text((m+50,top+16),'SAT-LINK // IGS 1',font=fm,fill=WHITE+(235,))
    tc=f'T+00:{int(t):02d}.{int((t%1)*100):02d}'; w=fm.getlength(tc)
    d.text((W-m-18-w,top+16),tc,font=fm,fill=WHITE+(235,))
    lat=1.30+0.02*math.sin(t*0.9); lon=103.82+0.03*math.cos(t*0.7); alt=408+3*math.sin(t*2)
    d.text((m+18,bot-48),f'LAT {lat:.4f}  LON {lon:.4f}',font=fm2,fill=CY+(220,))
    s=f'ALT {alt:05.1f}KM'; d.text((W-m-18-fm2.getlength(s),bot-48),s,font=fm2,fill=CY+(220,))

def reticle(frame,t,s,e,cx,cy):
    if not (s<=t<=e): return
    p=ease_out((t-s)/0.45); size=int(400-180*p); a=int(255*clamp((e-t)/0.2))
    d=ImageDraw.Draw(frame); x0,y0,x1,y1=cx-size//2,cy-size//2,cx+size//2,cy+size//2; L2=46
    col=LIME+(a,)
    for (x,y,sx,sy) in [(x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)]:
        d.line([(x,y),(x+sx*L2,y)],fill=col,width=6); d.line([(x,y),(x,y+sy*L2)],fill=col,width=6)
    d.line([(cx-18,cy),(cx+18,cy)],fill=col,width=3); d.line([(cx,cy-18),(cx,cy+18)],fill=col,width=3)
    if p>0.95 and int(t*6)%2==0:
        txt='● TARGET LOCKED'; d.text((x0,y0-44),txt,font=fm2,fill=col)

def orbit(frame,t):  # intro orbit around title
    if t>2.9: return
    a=clamp(t/0.4)*clamp((2.9-t)/0.25)
    ov=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(ov)
    cx,cy,rx,ry=W//2,1300,470,150
    d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),outline=CY+(int(120*a),),width=3)
    ang=t*2.6; px,py=cx+rx*math.cos(ang),cy+ry*math.sin(ang)
    for k in range(10):  # trail
        aa=ang-k*0.06; qx,qy=cx+rx*math.cos(aa),cy+ry*math.sin(aa)
        rr=11-k; d.ellipse((qx-rr,qy-rr,qx+rr,qy+rr),fill=WHITE+(int(a*(230-20*k)),))
    frame.alpha_composite(ov)

# ---------- I/O
dec=subprocess.Popen(['ffmpeg','-v','error','-i',SRC,'-t',str(LIMIT),'-vf',
  'fps=30,scale=1080:1920:flags=lanczos,unsharp=5:5:0.9:5:5:0.0,eq=contrast=1.08:saturation=1.18:brightness=0.01,colorbalance=bs=0.05:bm=0.02:rh=0.03',
  '-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',AUD,
  '-map','0:v','-map','1:a','-c:v','libx264','-preset','slow','-crf','16','-profile:v','high','-pix_fmt','yuv420p','-r','30',
  '-c:a','aac','-b:a','256k','-ar','44100','-shortest','-movflags','+faststart',OUT],stdin=subprocess.PIPE)
CUT=1.5; last=None
for i in range(NF):
    raw=dec.stdout.read(W*H*3)
    if len(raw)<W*H*3: raw=last
    last=raw; t=i/FPS
    arr=np.frombuffer(raw,np.uint8).reshape(H,W,3)
    tc=t%CUT; ci=int(t//CUT)
    # punch-in zoom on each cut + slow drift
    z=1.0+0.10*(1-ease_out(tc/0.35))+0.03*(tc/CUT) if ci>0 else 1.02+0.04*(tc/CUT)
    img=Image.fromarray(arr)
    cw,ch=int(W/z),int(H/z); img=img.resize((W,H),Image.BILINEAR,box=((W-cw)/2,(H-ch)/2,(W+cw)/2,(H+ch)/2))
    a=np.asarray(img).astype(np.float32)
    if ci>0 and tc<0.1:  # RGB split glitch + flash
        k=1-tc/0.1; sh=int(22*k)
        a[...,0]=np.roll(a[...,0],sh,1); a[...,2]=np.roll(a[...,2],-sh,1)
        a=a+(255-a)*0.45*k
    a+=grain[i%4]
    frame=Image.fromarray(np.clip(a,0,255).astype(np.uint8)).convert('RGBA')
    frame.alpha_composite(vig); 
    if t>0.1: frame.alpha_composite(grad)
    frame.alpha_composite(hud); hud_dyn(frame,t)
    reticle(frame,t,6.05,7.4,440,1060); reticle(frame,t,9.05,10.4,585,960)
    orbit(frame,t)
    for blk in B: draw_block(frame,t,blk)
    if t>14.4:  # fade to black
        frame=Image.blend(frame,Image.new('RGBA',(W,H),(0,0,0,255)),clamp((t-14.4)/0.6))
    enc.stdin.write(frame.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.kill()
