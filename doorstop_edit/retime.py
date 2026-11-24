# Re-anchor cards, photos and lower third to word timings of the current edit
import json, re
W = "/home/user/Mendaki/work"
w = [[x[0], x[1], re.sub(r"[^a-z0-9$]", "", x[2].lower())] for x in json.load(open(f"{W}/edit_words.json"))]
def find(word, after=0.0, nth=1):
    k = 0
    for s, e, t in w:
        if s >= after and t.startswith(word):
            k += 1
            if k == nth: return s, e
    raise KeyError(word)
SPEECH = w[-1][1]
TOTAL = round(sum(b - a for a, b, _, _ in __import__("edl").CLIPS) + 2.5, 2)
seg0 = find("so", find("university")[1])[0]                # "So, as we begin..."
prim = find("primary")[0]; univ = find("university")[0]; frm = find("from")[0]
alls = find("all", prim)[0]
cards = {c["id"]: c for c in json.load(open("/home/user/Mendaki/number_cards/cards.json"))}
def setc(i, s, e): cards[i]["start"], cards[i]["end"] = round(s, 2), round(e, 2)
setc("primary", prim, seg0 - 0.05)
giving = find("giving")[0]; setc("voucher", giving + 0.25, giving + 2.95)
d1 = find("$1")[0]; so22 = find("so", d1)[0]; setc("pci", d1 - 0.1, so22 - 0.1)
n22 = find("22")[0]; setc("students", n22 - 0.15, n22 + 2.55)
appl = find("applications", find("start", n22)[0])[0]; setc("apply", appl - 0.3, appl + 2.35)
json.dump(list(cards.values()), open("/home/user/Mendaki/number_cards/cards.json", "w"), indent=0, ensure_ascii=False)
# photos
we_have = find("we", find("life")[1])[0]; textb = find("textbooks")[0]; and_during = find("and", find("out", textb)[1])[0]
child = find("children", giving)[0]; wh2 = find("whether", child, 2)[0]; shoes = find("shoes")[1]
will = find("will", find("december")[1])[0]; parents = find("parents", will)[0]; year = find("year", parents)[1]
that = find("that", find("expenses", year)[1])[0]
B = [{"photos":["photo9.jpg","photo5.jpg","photo4.jpg"],"appear":[prim, alls + 0.1, univ],"start":frm - 0.05,"end":seg0,"layout":"3top"},
     {"photos":["photo7.jpg","photo6.jpg"],"appear":[we_have + 0.05, textb],"start":we_have,"end":and_during},
     {"photos":["photo8.jpg","photo1.jpg"],"appear":[child - 0.25, wh2],"start":child - 0.3,"end":shoes + 0.35},
     {"photos":["photo11.jpg","photo10.jpg"],"appear":[will - 0.15, parents],"start":will - 0.2,"end":year + 0.25},
     {"photos":["photo3.jpg"],"appear":[that + 0.05],"start":that,"end":TOTAL}]
for b in B:
    b["start"] = round(b["start"], 2); b["end"] = round(b["end"], 2); b["appear"] = [round(x, 2) for x in b["appear"]]
json.dump(B, open(f"{W}/broll_plan.json", "w"))
lt_end = round(B[0]["start"] - 0.05, 2)
r = open(f"{W}/render.py").read()
r = re.sub(r"fade=t=out:st=[0-9.]+:d=0.3:alpha=1\[lt\]", f"fade=t=out:st={lt_end-0.35:.2f}:d=0.3:alpha=1[lt]", r)
r = re.sub(r"between\(t,0.3,[0-9.]+\)", f"between(t,0.3,{lt_end})", r)
open(f"{W}/render.py", "w").write(r)
print("TOTAL", TOTAL, "LT until", lt_end)
for c in cards.values(): print(c["id"], c["start"], c["end"])
for b in B: print(b["photos"], b["start"], b["end"], b["appear"])
