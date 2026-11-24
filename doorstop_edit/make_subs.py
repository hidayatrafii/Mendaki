import json
W="/home/user/Mendaki/work"
words=json.load(open(f"{W}/edit_words.json"))
# (source phrase as transcribed, caption text to display)
G=[("So, at the beginning of the school year,","So, as we begin the school year,"),
("as you know, for many parents,","as you know, for many parents,"),
("it's also a time where, you know, there are a lot of expenses for school","it's also a time where there are a lot of expenses for school"),
("and we want our kids to have the best start in life.","and we want our kids to have the best start in life."),
("You have things like school books, textbooks, uniforms","You have things like schoolbooks, textbooks, uniforms"),
("and other expenses that parents have to fork out.","and other expenses that parents have to fork out."),
("And during these times,","And during these times,"),
("especially when you have costs of living concerns,","especially when you have cost of living concerns,"),
("challenging times,","challenging times,"),
("we want to help parents from low -income families","we want to help parents from low-income families"),
("to support their kids.","to support their kids."),
("MENDAKI has introduced the Ready for School e -voucher initiative,","MENDAKI is introducing the Ready for School e-voucher initiative,"),
("which we hope to help kids","which we hope to help kids"),
("from primary one all the way up to university.","from Primary One all the way up to university."),
("This year, MENDAKI is giving out $280 e -vouchers","This year, MENDAKI is giving out $250 e-vouchers"),
("that parents can use for their children,","that parents can use for their children,"),
("whether it's school books,","whether it's schoolbooks,"),
("whether it is stationary or even shoes.","whether it is stationery or even shoes."),
("I think it's important because","I think it's important because"),
("especially for parents who have more than one child,","especially for parents who have more than one child,"),
("as you know, sometimes you have two or three kids.","as you know, sometimes you have two or three kids."),
("I think it's always challenging","I think it's always challenging"),
("to try to fork out that much expenses at one go.","to try to fork out that much expense at one go."),
("We are pegging it at about $1 ,000","We are pegging it at about $1,000"),
("per capita income and below.","per capita income and below."),
("So we expect more than 22 ,000 students","So we expect more than 22,000 students"),
("who could benefit from this.","who could benefit from this."),
("And this is in addition to about 13 ,000 others","And this is in addition to about 13,000 others"),
("that typically benefit from our DTFS","that typically benefit from our TTFS"),
("and other MENDAKI schemes as well.","and other MENDAKI schemes as well."),
("So it's an application basis","So it's an application basis"),
("and we start to take applications from 1st December.","and we start to take applications from 1st December."),
("So we hope that this will do its part","So we hope that this will do its part"),
("to help parents and children have a good start for the year","to help parents and children have a good start for the year"),
("and not to worry about some of these expenses","and not to worry about some of these expenses"),
("that would have otherwise held them back.","that would have otherwise held them back."),
]
caps=[];i=0
for src,disp in G:
    n=len(src.split()); toks=words[i:i+n]
    got=" ".join(w[2].strip() for w in toks)
    assert got==src,(got,src)
    caps.append([toks[0][0],toks[-1][1],disp.rstrip(",")]); i+=n
assert i==len(words),(i,len(words))
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
def srt(t): return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(round(t%1*1000)):03d}"
hdr=open("/home/user/Mendaki/subtitles/style_template.ass").read().rstrip()+"\n"
L=[];S=[]
for k,(s,e,t) in enumerate(caps):
    e2=min(caps[k+1][0],e+0.5) if k+1<len(caps) else e+0.6
    L.append(f"Dialogue: 0,{ts(s)},{ts(e2)},Default,,0,0,0,,{t}")
    S.append(f"{k+1}\n{srt(s)} --> {srt(e2)}\n{t}\n")
open(f"{W}/subs.ass","w").write(hdr+"\n".join(L)+"\n")
open(f"{W}/subs.srt","w").write("\n".join(S))
print(len(caps),"captions OK")
