import sys; sys.argv=["x"]; sys.path.insert(0,".")
import render3 as r, numpy as np, cv2, json
from PIL import Image
det=cv2.FaceDetectorYN.create("../models/face_detection_yunet_2023mar.onnx","",(540,960),0.6,0.3,5000)
DRAW={"checklist":r.draw_checklist,"badges":r.draw_badges,"banner":r.draw_banner,"nametag":r.draw_nametag,
      "info":r.draw_info,"stickers":r.draw_stickers,"captions":r.draw_captions,"end":r.draw_end}
a,b=int(sys.argv[1]) if False else 0,0
import os
a,b=map(int,os.environ["RANGE"].split(","))
res=[]
allf=[]
orig=r.process
def base(img,idx):  # video without overlays, same geometry
    r.draw_checklist=r.draw_badges=r.draw_banner=r.draw_nametag=r.draw_info=r.draw_sparkles=r.draw_stickers=r.draw_captions=r.draw_confetti=r.draw_end=r.draw_progress=lambda *x:None
    return orig(img,idx)
for n,f in r.read_frames(a,b):
    if n%4: continue
    img=base(f,n)
    _,fs=det.detect(cv2.resize(img,(540,960)))
    boxes=[] if fs is None else [tuple(int(v) for v in f[:4]) for f in fs]
    boxes=[(max(0,x-w//6),max(0,y-h//4),w+w//3,h+h//3) for x,y,w,h in boxes]   # pad: hijab/forehead
    allf.append((n,boxes))
    t=(n+1)/30
    for name,fn in DRAW.items():
        cv=Image.new("RGBA",(1080,1920),(0,0,0,0)); fn(cv,t)
        al=np.asarray(cv)[...,3]
        for x,y,w,h in boxes:
            x,y,w,h=[v*2 for v in (x,y,w,h)]
            ov=(al[y:y+h,x:x+w]>60).mean()
            if ov>0.04: res.append((n,round(t,2),name,round(float(ov),2),[int(x),int(y),int(w),int(h)]))
json.dump(res,open(f"faces_{a}.json","w")); json.dump(allf,open(f"facebox_{a}.json","w"))
