import json, re
W = "/home/user/Mendaki/work"
toks = [[w[0], w[1], w[2].strip()] for w in json.load(open(f"{W}/edit_words.json"))]
# (as transcribed | as displayed). Display text corrects ASR slips against the footage/talking points.
P = """MENDAKI is reducing|MENDAKI is introducing
the Ready for School|
e -voucher initiative,|e-voucher initiative,
which we hope to help kids|
from primary one|from Primary One
all the way up to university.|
So at the beginning of the school year,|So, as we begin the school year,
as you know, for many parents,|
it's also a time where, you know,|it's also a time where
there are a lot of|
expenses for school|
and we want our kids|
to have the best start in life.|
We have things like|You have things like
school books, textbooks, uniforms|schoolbooks, textbooks, uniforms
and other expenses|
that parents have to fork out.|
And during these times,|
especially when you have|
costs of living concerns,|cost of living concerns,
challenging times,|
we want to help our parents|we want to help parents
from low -income families|from low-income families
to support their kids.|
This year, MENDAKI|
is giving out $203 e -vouchers|is giving out $250 e-vouchers
that parents can use|
for their children,|
whether it's school books,|whether it's schoolbooks,
whether it is stationery|
or even shoes.|
We are pegging it at about|
$1 ,000 per capita income|$1,000 per capita income
and below.|
So we expect more than|
22 ,000 students|22,000 students
who could benefit from this.|
And this in addition to|And this is in addition to
about 13 ,000 others|about 13,000 others
that typically benefit|
from our TTFS|
and other MENDAKI schemes|
as well.|
So it's an application basis|
and we start the|and we start to take
applications from 1st December.|
So we hope that this|
will do its part|
to help parents and children|
have a good start for the year|
and not to worry|
about some of these expenses|
that would have otherwise|
held them back.|"""
caps, i = [], 0
for line in P.split("\n"):
    src, disp = line.split("|"); disp = disp or src
    n = len(src.split()); seg = toks[i:i+n]
    assert [x[2] for x in seg] == src.split(), (src, [x[2] for x in seg])
    caps.append([seg[0][0], seg[-1][1], disp.rstrip(",")]); i += n
assert i == len(toks), (i, len(toks))
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
