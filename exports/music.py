# Original synthesized track: 160 BPM half-time pop/trap, 1 bar = 1.5s = one clip.
import numpy as np, wave, sys
SR=44100; BPM=160; B=60/BPM; BAR=4*B; DUR=15.0
N=int(SR*DUR); rng=np.random.default_rng(7)
mixL=np.zeros(N); mixR=np.zeros(N)
def t_(n): return np.arange(n)/SR
def add(sig,start,gain=1.0,pan=0.0):
    i=int(start*SR); 
    if i>=N: return
    s=sig[:N-i]*gain
    mixL[i:i+len(s)]+=s*np.sqrt(0.5*(1-pan)); mixR[i:i+len(s)]+=s*np.sqrt(0.5*(1+pan))
def lp(x,fc):
    fc=np.broadcast_to(np.asarray(fc,float),x.shape)
    a=1-np.exp(-2*np.pi*fc/SR); y=np.empty_like(x); z=0.0
    for i in range(len(x)): z+=a[i]*(x[i]-z); y[i]=z
    return y
def hp(x,fc): return x-lp(x,fc)
def mtof(m): return 440*2**((m-69)/12)
def env(n,a=0.005,d=0.2):
    t=t_(n); e=np.minimum(t/a,1)*np.exp(-t/d); return e
# --- instruments
def kick():
    n=int(.45*SR); t=t_(n); f=45+120*np.exp(-t/0.04)
    ph=2*np.pi*np.cumsum(f)/SR; return np.tanh(2*np.sin(ph)*np.exp(-t/0.25))*0.9
def clap():
    n=int(.35*SR); t=t_(n); x=rng.standard_normal(n)
    e=np.zeros(n)
    for o in (0,.01,.02): e+=np.where(t>=o,np.exp(-(t-o)/0.012),0)
    e+=np.where(t>=.03,np.exp(-(t-.03)/0.12),0)
    x=hp(lp(x,6000),900)*e; tone=np.sin(2*np.pi*190*t)*np.exp(-t/0.05)*0.4
    return (x+tone)*0.6
def hat(d=0.03,g=1):
    n=int(.12*SR); x=hp(rng.standard_normal(n),7000)*np.exp(-t_(n)/d); return x*0.25*g
def b808(m,length,glide_from=None):
    n=int(length*SR); t=t_(n); f=np.full(n,mtof(m))
    if glide_from is not None: f=mtof(m)+(mtof(glide_from)-mtof(m))*np.exp(-t/0.06)
    ph=2*np.pi*np.cumsum(f)/SR; e=np.minimum(t/0.004,1)*np.exp(-t/1.2)
    e*=np.clip((length-t)/0.03,0,1)
    return np.tanh(1.6*np.sin(ph))*e*0.55
def pluck(m,length=0.3):
    n=int((length+0.4)*SR); t=t_(n); f=mtof(m)
    x=sum(((-1)**k)*np.sin(2*np.pi*f*k*t+0.0)/k for k in range(1,9))  # saw-ish
    x+=0.5*np.sin(2*np.pi*f*2*t)
    cutoff=300+5000*np.exp(-t/0.08)
    return lp(x,cutoff)*env(n,0.002,0.22)*0.32
def pad(notes,length):
    n=int(length*SR); t=t_(n); x=np.zeros(n)
    for m in notes:
        for det in (-0.12,0,0.12):
            f=mtof(m+det); x+=((t*f+rng.random())%1*2-1)
    x/=len(notes)*3
    e=np.minimum(t/0.15,1)*np.clip((length-t)/0.2,0,1)
    return lp(x,1800)*e*0.5
# --- arrangement (A minor: Am F C G ...)
chords=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]
roots=[33,29,36,31]
hook=[  # (beat offset in 8ths, midi, len in 8ths) -- one bar each, 2-bar phrase
 [(0,76,1),(1,72,1),(2,76,1),(3,79,2),(5,76,1),(6,74,1),(7,72,1)],
 [(0,72,1),(1,69,1),(2,72,1),(3,77,2),(5,76,1),(6,72,2)],
 [(0,76,1),(1,72,1),(2,76,1),(3,79,2),(5,81,1),(6,79,1),(7,76,1)],
 [(0,74,2),(2,71,1),(3,74,1),(4,79,3),(7,74,1)],
]
E8=B/2
sc=np.ones(N)  # sidechain envelope
for bar in range(10):
    T=bar*BAR; ci=bar%4
    full = 1<=bar<=8
    # pad everywhere
    add(pad([n+12 for n in chords[ci]] if bar==0 else chords[ci],BAR+0.05),T,0.9 if bar>0 else 0.6,0)
    # hook
    for (o,m,l) in hook[ci]:
        g=0.55 if bar==0 else 1.0
        add(pluck(m,l*E8),T+o*E8,g,-0.25); add(pluck(m+12,l*E8),T+o*E8+0.1875,0.18*g,0.5)  # echo
    if full and bar!=8:
        for k in (0,2.5): add(kick(),T+k*B,1.0); sc[int((T+k*B)*SR):int((T+k*B+0.25)*SR)]=np.minimum(sc[int((T+k*B)*SR):int((T+k*B+0.25)*SR)],np.linspace(0.35,1,int(0.25*SR))[:len(sc[int((T+k*B)*SR):int((T+k*B+0.25)*SR)])])
        add(clap(),T+2*B,0.9)
        for h in range(8):
            add(hat(),T+h*E8,0.9 if h%2==0 else 0.55,0.3)
        if bar%2==0:  # 16th roll
            for r in range(4): add(hat(0.015,0.7),T+3*B+r*B/4,0.8,0.3)
        else:  # triplet roll
            for r in range(6): add(hat(0.012,0.6),T+3*B+r*B/6,0.7,0.3)
        prev = roots[(ci-1)%4]
        add(b808(roots[ci],2.4*B,glide_from=prev+12 if bar%2 else None),T,1.0)
        add(b808(roots[ci]+(12 if bar%2 else 7),1.4*B),T+2.5*B,0.8)
    if bar==8:  # build: snare roll + riser
        for r in range(16): add(clap(),T+r*B/4,0.25+0.5*r/16)
# intro riser (bar 0) and bar 8 riser
def riser(length):
    n=int(length*SR); t=t_(n); x=rng.standard_normal(n)
    x=lp(x,300+8000*(t/length)**2)*(t/length)**2; return x*0.35
add(riser(BAR),0,1,0); add(riser(BAR),8*BAR,1,0)
def impact():
    n=int(1.5*SR); t=t_(n); f=60+80*np.exp(-t/0.1)
    s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.6)
    s+=lp(rng.standard_normal(n),3000)*np.exp(-t/0.25)*0.4
    return s*0.7
add(impact(),BAR,0.9); add(impact(),9*BAR,1.1)
# final bar: big chord + kick + 808 sustain
add(kick(),9*BAR,1.1); add(b808(33,1.5),9*BAR,1.0)
add(pad([57,60,64,69],1.5),9*BAR,1.0)
# whoosh on every cut
def whoosh():
    n=int(0.4*SR); t=t_(n); x=rng.standard_normal(n)
    e=np.sin(np.pi*t/0.4)**2; return lp(x,1500+3000*e)*e*0.12
for bar in range(2,9): add(whoosh(),bar*BAR-0.2,1,(-1)**bar*0.6)
# apply sidechain to pad/hook approx (whole mix gentle duck excluding transient by mild amount)
duck=0.55+0.45*sc
mixL*=duck; mixR*=duck
# reverb (FFT convolution)
ir_n=int(1.8*SR); ir=rng.standard_normal(ir_n)*np.exp(-t_(ir_n)/0.5); ir=lp(ir,4000); ir/=np.sqrt((ir**2).sum())
def conv(x): L=len(x)+ir_n; F=np.fft.rfft(x,L)*np.fft.rfft(ir,L); return np.fft.irfft(F,L)[:len(x)]
mixL+=0.18*conv(mixL); mixR+=0.18*conv(np.roll(mixR,300))
# master: fade, soft clip, normalize
fade=np.clip((DUR-t_(N))/0.6,0,1); fadein=np.clip(t_(N)/0.05,0,1)
out=np.stack([mixL,mixR],1)*(fade*fadein)[:,None]
out/=np.abs(out).max(); out=np.tanh(out*1.6)/np.tanh(1.6)*0.95
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype('<i2').tobytes()); w.close()
