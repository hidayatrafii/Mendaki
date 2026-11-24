import json, re
W = "/home/user/Mendaki/work"
toks = [[w[0], w[1], w[2].strip()] for w in json.load(open(f"{W}/edit_words.json"))]
# (as transcribed | as displayed). Display text corrects ASR slips against the footage/talking points.
P = """MENDAKI is *|MENDAKI is introducing
the Ready for School|
e -voucher initiative|e-voucher initiative,
which we hope to help kids|
from primary one|from Primary One
all the way up to university.|
So * * * of the school year,|So, as we begin the school year,
as you know, for many parents,|
it's also a time where, you know,|it's also a time where
there are a lot of|
expenses for school|
and we want our kids|
to have the best start in life.|
We have things like|You have things like
school books, textbooks, uniforms,|schoolbooks, textbooks, uniforms
and other expenses|
that parents have to fork out.|
And during these times,|
especially when you have|
* of living concerns,|cost of living concerns,
challenging times,|
we want to help parents|
from low -income families|from low-income families
to support their kids.|
This year, MENDAKI|
is giving out * e -vouchers|is giving out $250 e-vouchers
that parents can use|
for their children,|
whether it's school books,|whether it's schoolbooks,
whether it is stationery|
or even shoes.|
We are * it at about|We are pegging it at about
$1 ,000 per capita income|$1,000 per capita income
and below.|
So we expect more than|
22 ,000 students|22,000 students
who could benefit from this.|
So it's an application basis|
and we start *|and we start to take
applications from 1st December.|
So we hope that this|
will do its part|
to help parents and children|
have a good start for the year|
and not to worry|
about some of these expenses|
that would have otherwise|
held them back.|"""
import difflib
N = lambda w: re.sub(r"[^a-z0-9$]", "", w.lower())
phr = []
for line in P.split("\n"):
    src, disp = line.split("|"); disp = disp or src
    phr.append(disp.replace(" -", "-"))
dw = [(pi, x) for pi, ph in enumerate(phr) for x in ph.split()]
aw = [N(t[2]) for t in toks]
sm = difflib.SequenceMatcher(None, [N(x) for _, x in dw], aw, autojunk=False)
tm = [None] * len(dw)
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == "equal":
        for k in range(i2 - i1): tm[i1 + k] = (toks[j1 + k][0], toks[j1 + k][1])
    elif op == "replace" and j2 > j1:
        st, en = toks[j1][0], toks[j2 - 1][1]; n = i2 - i1
        for k in range(n): tm[i1 + k] = (st + (en - st) * k / n, st + (en - st) * (k + 1) / n)
for k in range(len(tm)):                      # words the speaker didn't say clearly: borrow neighbours
    if tm[k] is None:
        prev = next((tm[j] for j in range(k - 1, -1, -1) if tm[j]), None)
        nxt = next((tm[j] for j in range(k + 1, len(tm)) if tm[j]), None)
        tm[k] = (prev[1] if prev else nxt[0], nxt[0] if nxt else prev[1])
caps = []
for pi, ph in enumerate(phr):
    idx = [k for k, (q, _) in enumerate(dw) if q == pi]
    caps.append([tm[idx[0]][0], tm[idx[-1]][1], ph.rstrip(",")])
ratio = sm.ratio(); print("alignment match", round(ratio, 3)); assert ratio > 0.9
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
def srt(t): return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(round(t%1*1000))%1000:03d}"
hdr = open("/home/user/Mendaki/subtitles/style_template.ass").read().rstrip() + "\n"
L, S = [], []
for k, (s, e, t) in enumerate(caps):
    e2 = caps[k+1][0] if k+1 < len(caps) else e + 0.6
    L.append(f"Dialogue: 0,{ts(s)},{ts(e2)},Default,,0,0,0,,{t}")
    S.append(f"{k+1}\n{srt(s)} --> {srt(e2)}\n{t}\n")
open(f"{W}/subs.ass", "w").write(hdr + "\n".join(L) + "\n")
open(f"{W}/subs.srt", "w").write("\n".join(S))
for s,e,t in caps: print(f"{s:6.2f}-{e:6.2f} {t}")
