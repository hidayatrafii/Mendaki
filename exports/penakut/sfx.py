# Synthesised SFX (numpy) -> dict of float32 mono arrays @44100
import numpy as np
SR=44100
rng=np.random.default_rng(7)
def t(d): return np.arange(int(d*SR))/SR
def env(n,a=0.005,r=None,curve=4):
    x=np.linspace(0,1,n); e=np.minimum(1,x*(n/SR)/max(a,1e-4))
    return e*(1-x)**curve if r is None else e
def lp(x,k=8):  # crude lowpass via moving avg
    return np.convolve(x,np.ones(k)/k,'same')
def norm(x,p=0.9): return (x/ (np.abs(x).max()+1e-9)*p).astype(np.float32)
def sweep(f0,f1,d,shape='exp'):
    tt=t(d); f=f0*(f1/f0)**(tt/d) if shape=='exp' else f0+(f1-f0)*tt/d
    return np.sin(2*np.pi*np.cumsum(f)/SR)
def whoosh(d=0.55):
    n=rng.standard_normal(int(d*SR)); out=np.zeros_like(n)
    for k,w in [(3,.5),(9,.3),(25,.2)]: out+=lp(n,k)*w
    x=np.linspace(0,1,len(n)); e=np.sin(np.pi*x)**2
    return norm(out*e,0.6)
def pop():
    d=0.09; s=sweep(900,300,d)*env(int(d*SR),0.002,curve=3); return norm(s,0.6)
def boom():
    d=1.6; tt=t(d); f=60*np.exp(-tt*1.5)+38
    s=np.sin(2*np.pi*np.cumsum(f)/SR)+0.4*np.sin(4*np.pi*np.cumsum(f)/SR)
    s=np.tanh(2.5*s)*np.exp(-tt*2.2)
    click=rng.standard_normal(len(tt))*np.exp(-tt*120)*0.6
    return norm(s+click,0.95)
def scratch():
    d=0.55; tt=t(d); n=rng.standard_normal(len(tt))
    wob=np.sin(2*np.pi*(9*tt+ 5*tt**2))
    f=700+600*wob; car=np.sin(2*np.pi*np.cumsum(f)/SR)
    s=(lp(n,4)*0.6+car*0.5)*(0.6+0.4*np.abs(wob))*np.exp(-tt*2)
    return norm(s,0.8)
def sting():
    d=2.6; tt=t(d); s=np.zeros_like(tt)
    for f in [55,58.3,82.4,87.3,116.5,123.5]:
        ph=2*np.pi*f*tt*(1+0.003*np.sin(2*np.pi*5*tt))
        s+=2*(ph/(2*np.pi)%1)-1
    s=lp(s,12)*(1+0.5*np.sin(2*np.pi*11*tt))
    hi=sweep(1500,2400,d)*0.35*(1+0.6*np.sin(2*np.pi*13*tt))
    e=np.minimum(1,tt/0.03)*np.exp(-tt*0.9)
    return norm(np.tanh((s*0.25+hi))*e,0.85)
def slide_down(d=0.9):
    tt=t(d); f=1600*(0.2)**(tt/d)*(1+0.03*np.sin(2*np.pi*7*tt))
    s=np.sin(2*np.pi*np.cumsum(f)/SR); s+=0.2*np.sin(4*np.pi*np.cumsum(f)/SR)
    return norm(s*np.minimum(1,tt/0.02)*np.minimum(1,(d-tt)/0.1),0.55)
def boing(d=0.8):
    tt=t(d); f=180+120*np.sin(2*np.pi*14*tt)*np.exp(-tt*4)+tt*40
    s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*3.5)
    return norm(s,0.8)
def rewind(d=0.75):
    tt=t(d); s=np.zeros_like(tt); k=0
    seg=0.06
    while k*seg<d:
        a=int(k*seg*SR); b=min(len(tt),a+int(seg*SR)); u=tt[a:b]-tt[a]
        f=400+4000*u/seg; s[a:b]=np.sin(2*np.pi*np.cumsum(f)/SR)*np.hanning(b-a); k+=1
    n=lp(rng.standard_normal(len(tt)),3)*0.3
    return norm(s+n,0.5)
def ding():
    d=1.4; tt=t(d); s=sum(a*np.sin(2*np.pi*f*tt)*np.exp(-tt*k) for f,a,k in [(1320,1,3),(2640,.4,5),(3960,.2,7),(1980,.3,4)])
    return norm(s,0.45)
def shutter():
    d=0.25; tt=t(d); n=rng.standard_normal(len(tt))
    e=np.exp(-((tt-0.01)/0.004)**2)+0.7*np.exp(-((tt-0.11)/0.006)**2)
    return norm(n*e,0.7)
def heartbeat(n=6,start=0.95,end=0.45):
    gaps=np.linspace(start,end,n); tot=sum(gaps)+0.5; out=np.zeros(int(tot*SR)); pos=0
    for g in gaps:
        for off,amp in [(0,1),(0.16,0.7)]:
            tt=t(0.25); th=np.sin(2*np.pi*(50+30*np.exp(-tt*20))*tt)*np.exp(-tt*16)*amp
            a=int((pos+off)*SR); out[a:a+len(th)]+=th
        pos+=g
    return norm(np.tanh(out*2),0.9)
def trombone():
    notes=[(233.1,.45),(220,.45),(207.7,.45),(196,1.4)]; out=[]
    for i,(f,d) in enumerate(notes):
        tt=t(d); vib=1+(0.02*np.sin(2*np.pi*6*tt)*np.minimum(1,tt/0.3) if i==3 else 0*tt)
        ph=np.cumsum(f*vib)/SR; s=sum(np.sin(2*np.pi*k*ph)/k**1.2 for k in range(1,9))
        e=np.minimum(1,tt/0.04)*np.minimum(1,(d-tt)/0.06); out.append(lp(s,6)*e)
    return norm(np.concatenate(out),0.6)
def tick():
    d=0.04; tt=t(d); return norm(rng.standard_normal(len(tt))*np.exp(-tt*200),0.4)
def crickets(d):
    tt=t(d); out=np.zeros_like(tt)
    for start in np.arange(0.15,d-0.4,0.75):
        for j in range(3):
            a=int((start+j*0.07)*SR); n=int(0.045*SR)
            if a+n>len(out): break
            u=np.arange(n)/SR; out[a:a+n]+=np.sin(2*np.pi*4600*u)*(0.5+0.5*np.sin(2*np.pi*90*u))*np.hanning(n)
    return norm(out,0.35)
def drone(d):
    tt=t(d); s=sum(np.sin(2*np.pi*f*tt+ph) for f,ph in [(41,0),(41.7,1),(61.5,2),(82.3,.5),(123,1.3)])
    s*=0.7+0.3*np.sin(2*np.pi*0.25*tt); s+=lp(rng.standard_normal(len(tt)),60)*2
    e=np.minimum(1,tt/0.8)*np.minimum(1,(d-tt)/0.8); return norm(np.tanh(s*0.5)*e,0.5)
def whispers(d):
    tt=t(d); n=rng.standard_normal(len(tt)); hi=n-lp(n,3)            # hiss
    env=np.zeros_like(tt)
    for st in np.arange(0.2,d-0.6,0.55):
        if rng.random()<0.75:
            a=int(st*SR); L=int(rng.uniform(0.25,0.5)*SR); L=min(L,len(env)-a); env[a:a+L]+=np.hanning(L)*rng.uniform(.4,1)
    form=sum(np.sin(2*np.pi*f*tt) for f in (900,2400,3300))*0.15+1
    return norm(hi*env*form,0.35)
def swell(d=1.2):
    tt=t(d); n=rng.standard_normal(len(tt)); s=(n-lp(n,6))*0.6+np.sin(2*np.pi*(300+900*tt/d)*tt)*0.3
    e=(tt/d)**3; return norm(s*e,0.7)
def static(d=0.45):
    tt=t(d); n=rng.standard_normal(len(tt)); gate=(np.sin(2*np.pi*23*tt)>0).astype(float)*0.7+0.3
    return norm(n*gate*np.exp(-tt*4),0.6)
def moan(d=1.8):
    tt=t(d); f=330*(0.62)**(tt/d)*(1+0.025*np.sin(2*np.pi*5.5*tt))
    s=np.sin(2*np.pi*np.cumsum(f)/SR)+0.3*np.sin(2*np.pi*np.cumsum(f*1.5)/SR)
    s*=np.minimum(1,tt/0.3)*np.minimum(1,(d-tt)/0.6)
    out=s.copy()
    for k,g in [(0.13,.5),(0.27,.35),(0.41,.22)]:
        o=int(k*SR); out[o:]+=s[:-o]*g
    return norm(out,0.5)
def all_sfx():
    return dict(whoosh=whoosh(),pop=pop(),boom=boom(),scratch=scratch(),sting=sting(),slide=slide_down(),
                boing=boing(),rewind=rewind(),ding=ding(),shutter=shutter(),heart=heartbeat(),trombone=trombone(),tick=tick(),swell=swell(),static=static(),moan=moan())
