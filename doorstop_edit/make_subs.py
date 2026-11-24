import json, re
W = "/home/user/Mendaki/work"
toks = [[w[0], w[1], w[2].strip()] for w in json.load(open(f"{W}/edit_words.json"))]
FIX = [("So at the beginning of the school year,", "So, as we begin the school year,"),
 ("where, you know,", "where"), ("We have things like", "You have things like"),
 ("school books,", "schoolbooks,"), ("low -income", "low-income"), ("reducing", "introducing"),
 ("e -voucher", "e-voucher"), ("e -vouchers", "e-vouchers"), ("primary one", "Primary One"),
 ("$203", "$250"), ("as much expense", "that much expense"), ("$1 ,000", "$1,000"),
 ("22 ,000", "22,000"), ("13 ,000", "13,000"), ("on an application", "an application"),
 ("start the applications", "start to take applications")]
for src, dst in FIX:
    s = src.split(); n = len(s); i = 0; hit = False
    while i <= len(toks) - n:
        if [t[2] for t in toks[i:i+n]] == s:
            dw = dst.split(); st, en = toks[i][0], toks[i+n-1][1]
            step = (en - st) / len(dw)
            toks[i:i+n] = [[st + j*step, st + (j+1)*step, w] for j, w in enumerate(dw)]
            hit = True; i += len(dw)
        else: i += 1
    assert hit, src
PHRASES = """So, as we begin the school year,
as you know, for many parents,
it's also a time where
there are a lot of
expenses for school
and we want our kids
to have the best start in life.
You have things like
schoolbooks, textbooks, uniforms
and other expenses
that parents have to fork out.
And during these times,
especially when you have
cost of living concerns,
challenging times,
we want to help parents
from low-income families
to support their kids.
MENDAKI is introducing
the Ready for School
e-voucher initiative,
which we hope to help kids
from Primary One
all the way up to university.
This year, MENDAKI
is giving out $250 e-vouchers
that parents can use
for their children,
whether it's schoolbooks,
whether it is stationery
or even shoes.
I think it's important because
especially for parents
who have more than one child,
as you know,
sometimes you have
two or three kids.
I think it's always challenging
to try to fork out
that much expense at one go.
We are pegging it at about
$1,000 per capita income
and below.
So we expect more than
22,000 students
who could benefit from this.
And this is in addition to
about 13,000 others
that typically benefit
from our TTFS
and other MENDAKI schemes
as well.
So it's an application basis
and we start to take
applications from 1st December.
So we hope that this
will do its part
to help parents and children
have a good start for the year
and not to worry
about some of these expenses
that would have otherwise
held them back.""".split("\n")
norm = lambda w: re.sub(r"[^a-z0-9$]", "", w.lower())
merged, i = [], 0
for ph in PHRASES:
    n = len(ph.split()); seg = toks[i:i+n]
    assert [norm(x[2]) for x in seg] == [norm(w) for w in ph.split()], (ph, [x[2] for x in seg])
    merged.append(seg[:-1] + [[seg[-1][0], seg[-1][1], ""]] if False else seg); i += n
    merged[-1] = [[seg[0][0], seg[-1][1], ph]]
assert i == len(toks), (i, len(toks))
caps = [[c[0][0], c[-1][1], c[0][2].rstrip(",")] for c in merged]
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
def srt(t): return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(round(t%1*1000))%1000:03d}"
hdr = open("/home/user/Mendaki/subtitles/style_template.ass").read().rstrip() + "\n"
L, S = [], []
for k, (s, e, t) in enumerate(caps):
    e2 = caps[k+1][0] if k+1 < len(caps) else e + 0.6
    L.append(f"Dialogue: 0,{ts(s)},{ts(e2)},Default,,0,0,0,,{t}")
    S.append(f"{k+1}\n{srt(s)} --> {srt(e2)}\n{t}\n")
    print(f"{s:6.2f} {t}")
open(f"{W}/subs.ass", "w").write(hdr + "\n".join(L) + "\n")
open(f"{W}/subs.srt", "w").write("\n".join(S))
