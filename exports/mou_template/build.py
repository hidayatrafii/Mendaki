"""Render the MENDAKI MOU carousel (5 slides, 1080x1350) from content.json.

Usage: python3 exports/mou_template/build.py [path/to/content.json]  (needs Node + Playwright for render.js)
Layout follows reference/mou_carousel/DESIGN_SPEC.md (coordinates on a 1280x1600 canvas).
"""
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FONTS = ROOT / "exports" / "assets" / "fonts"


def t(s):
    """Escape text; *words* become yellow."""
    s = html.escape(s)
    return re.sub(r"\*(.+?)\*", r'<span class="y">\1</span>', s)


def photo(path, cls, label):
    """path may end in '#<css object-position>' to choose the crop, e.g. 'a.jpg#50% 30%'."""
    if path:
        path, _, pos = path.partition("#")
        p = (ROOT / path).resolve()
        style = f' style="object-position:{pos}"' if pos else ""
        return f'<div class="{cls} ph"><img src="{p.as_uri()}"{style}></div>'
    return f'<div class="{cls} ph empty"><span>{html.escape(label)}</span></div>'


CSS = f"""
@font-face {{ font-family: Playfair; src: url('{(FONTS / "PlayfairDisplay-VF.ttf").as_uri()}'); font-weight: 400 900; }}
@font-face {{ font-family: Playfair; font-style: italic; src: url('{(FONTS / "PlayfairDisplay-Italic-VF.ttf").as_uri()}'); font-weight: 400 900; }}
@font-face {{ font-family: Outfit; src: url('{(FONTS / "Outfit-VF.ttf").as_uri()}'); font-weight: 100 900; }}
@font-face {{ font-family: Questrial; src: url('{(FONTS / "Questrial-Regular.ttf").as_uri()}'); }}
@font-face {{ font-family: Caveat; src: url('{(FONTS / "Caveat-VF.ttf").as_uri()}'); font-weight: 400 700; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #000; }}
.slide {{ width: 1280px; height: 1600px; background: #0E1D46; position: relative; overflow: hidden;
  color: #fff; font-family: Questrial; }}
.y {{ color: #F3CF45; }}
.pill {{ position: absolute; left: 88px; height: 68px; padding: 0 30px; border-radius: 34px; background: #F2CE46;
  color: #000; font-family: Outfit; font-weight: 450; font-size: 39px; display: flex; align-items: center; white-space: nowrap; }}
.head {{ position: absolute; left: 90px; font-family: Playfair; font-weight: 900; font-size: 156px; line-height: 1.09;
  letter-spacing: -1px; color: #F8F8FA; }}
.head .l2 {{ color: #F3CF45; display: block; }}
.lead {{ position: absolute; left: 100px; right: 100px; text-align: center; font-size: 31px; line-height: 1.46; letter-spacing: 2.4px; }}
.ph {{ position: absolute; overflow: hidden; }}
.ph img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.ph.empty {{ background: #192A60; border: 3px dashed rgba(255,255,255,.35); display: flex; align-items: center; justify-content: center;
  color: rgba(255,255,255,.6); font-size: 30px; letter-spacing: 2px; text-align: center; padding: 20px; }}
.logo {{ position: absolute; right: 45px; top: 38px; width: 160px; }}
.card {{ background: #192A60; }}
.cushion {{ border-radius: 50% / 14px; }}
.box {{ position: absolute; left: 90px; right: 90px; display: flex; align-items: center; justify-content: center; text-align: center; }}
.caps {{ position: absolute; left: 137px; font-family: Playfair; font-weight: 900; font-size: 33px; letter-spacing: 2px; text-transform: uppercase; }}
.area {{ position: absolute; left: 160px; right: 135px; height: 88px; display: flex; align-items: center; }}
.area .n {{ width: 88px; font-family: Playfair; font-weight: 900; font-size: 74px; color: #F3CF45; text-align: center; }}
.area .bar {{ flex: 1; height: 100%; margin-left: 0; display: flex; align-items: center; justify-content: center;
  font-size: 33px; letter-spacing: 1.6px; text-align: center; line-height: 1.1; padding: 0 30px; }}
.stat {{ position: absolute; width: 535px; height: 398px; border-radius: 32px; padding: 34px 40px; }}
.stat .num {{ font-family: Playfair; font-weight: 900; font-size: 118px; line-height: 1; color: #F3CF45; }}
.stat .lab {{ font-size: 30px; margin-top: 14px; line-height: 1.35; }}
.stat .desc {{ font-size: 27px; color: #ACB8E0; text-align: center; line-height: 1.33; margin-top: 52px; letter-spacing: .8px; }}
.quote {{ position: absolute; left: 128px; right: 128px; top: 1002px; padding: 30px 52px 34px; border-radius: 26px; }}
.quote p {{ font-size: 30px; line-height: 1.95; letter-spacing: 1.2px; }}
.quote .att {{ color: #F3CF45; font-size: 29px; line-height: 1.5; margin-top: 4px; letter-spacing: 0; }}
.qm {{ position: absolute; font-family: Caveat; font-weight: 400; font-size: 78px; color: #F3CF45; line-height: 1; }}
.person {{ position: absolute; width: 540px; height: 218px; border-radius: 26px; padding: 26px 34px; }}
.person .role {{ font-family: Outfit; font-weight: 500; font-size: 22px; letter-spacing: 3px; text-transform: uppercase; color: #F3CF45; }}
.person .name {{ font-family: Playfair; font-weight: 900; font-size: 29px; line-height: 1.15; margin-top: 10px; white-space: nowrap; }}
.person .ptitle {{ font-size: 23px; color: #ACB8E0; line-height: 1.35; margin-top: 8px; letter-spacing: .5px; }}
.flow {{ position: absolute; left: 90px; right: 90px; height: 150px; border-radius: 26px; display: flex; align-items: center; padding: 0 34px; }}
.flow .ico {{ width: 92px; height: 92px; border-radius: 50%; background: #F3CF45; flex: none; display: flex; align-items: center; justify-content: center; }}
.flow .ico svg {{ width: 52px; height: 52px; }}
.flow .ftitle {{ width: 270px; margin-left: 28px; font-family: Playfair; font-weight: 900; font-size: 33px; line-height: 1.12; flex: none; }}
.flow .arrow {{ width: 62px; flex: none; margin: 0 22px 0 4px; }}
.flow .fout {{ flex: 1; font-size: 26px; line-height: 1.38; color: #DDE3F5; letter-spacing: .4px; }}
.mini {{ position: absolute; top: 1234px; width: 352px; height: 282px; border-radius: 26px; padding: 24px 28px; }}
.mini .num {{ font-family: Playfair; font-weight: 900; font-size: 72px; line-height: 1; color: #F3CF45; }}
.mini .lab {{ font-size: 21px; line-height: 1.4; margin-top: 12px; color: #DDE3F5; }}
.arrows {{ position: absolute; left: 0; top: 0; width: 1280px; height: 1600px; }}
.call {{ position: absolute; left: 680px; width: 510px; height: 156px; border-radius: 24px; display: flex; align-items: center; gap: 18px; padding: 0 24px; }}
.call .ico {{ width: 66px; height: 66px; border-radius: 50%; background: #F3CF45; flex: none; display: flex; align-items: center; justify-content: center; }}
.call .ico svg {{ width: 38px; height: 38px; }}
.call .ctitle {{ font-family: Playfair; font-weight: 900; font-size: 27px; line-height: 1.1; }}
.call .cout {{ font-size: 21px; line-height: 1.32; color: #DDE3F5; margin-top: 6px; }}
.col {{ position: absolute; top: 1240px; width: 352px; height: 236px; border-radius: 26px; padding: 30px 30px; }}
.col .num {{ font-family: Playfair; font-weight: 900; font-size: 58px; line-height: 1; color: #F3CF45; white-space: nowrap; }}
.col .ico {{ width: 72px; height: 72px; border-radius: 50%; background: #F3CF45; display: flex; align-items: center; justify-content: center; }}
.col .ico svg {{ width: 42px; height: 42px; }}
.col .ctitle {{ font-family: Playfair; font-weight: 900; font-size: 30px; line-height: 1.12; margin-top: 20px; }}
.col .cout {{ font-size: 26px; line-height: 1.4; color: #DDE3F5; margin-top: 16px; }}
.tag {{ position: absolute; right: 75px; bottom: 82px; font-family: Playfair; font-weight: 700; font-size: 37px; }}
"""

_SV = '<svg viewBox="0 0 24 24" fill="none" stroke="#0E1D46" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
ICONS = {
    "cap": _SV + '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/><path d="M22 9v5"/></svg>',
    "people": _SV + '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.2c3 .3 5.5 2.7 5.5 5.8"/></svg>',
    "flask": _SV + '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3"/><path d="M7.5 15h9"/></svg>',
}
ARROW = '<svg viewBox="0 0 48 24" fill="none" stroke="#F3CF45" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h40M34 4l9 8-9 8"/></svg>'


def slides(c):
    cv, ab, im, lj, q = c["cover"], c["about"], c["impact"], c["journey"], c["quote"]
    logo = (HERE / "logo_white.png").as_uri()
    s = []
    # 1 Cover
    s.append(f"""
      <img class="logo" src="{logo}">
      <div class="pill" style="top:182px">{t(cv['pill'])}</div>
      <div class="head" style="top:272px">{t(cv['headline_white'])}<span class="l2">{t(cv['headline_yellow'])}</span></div>
      <div class="lead" style="top:660px">{t(cv['lead'])}</div>
      {photo(cv['photo'], '', 'GROUP PHOTO (landscape)').replace('class=" ph', 'style="left:82px;top:845px;width:1116px;height:627px" class="ph')}
    """)
    # 2 About the MOU: context, landscape MOU photo, three area cards below
    calls = "".join(
        f'<div class="col card" style="left:{90 + i * 374}px">'
        f'<div class="num">{t(ar["number"])}</div><div class="cout">{t(ar["label"])}</div></div>'
        for i, ar in enumerate(ab["areas"][:3]))
    s.append(f"""
      <div class="pill" style="top:96px">{t(ab['pill'])}</div>
      <div class="head" style="top:176px;font-size:104px">{t(ab['headline_white'])}<span class="l2">{t(ab['headline_yellow'])}</span></div>
      <div class="lead" style="top:428px;left:90px;right:90px;text-align:left;font-size:28px;letter-spacing:.8px">{t(ab['body'])}</div>
      {photo(ab.get('photo', ''), '', 'MOU PHOTO (landscape)').replace('class=" ph', 'style="left:90px;top:600px;width:1100px;height:600px;border-radius:26px" class="ph')}
      {calls}
    """)
    # 4 Learning journey: two photos + caption
    s.append(f"""
      <div class="pill" style="top:186px;left:84px">{t(lj['pill'])}</div>
      <div class="head" style="top:268px">{t(lj['headline_white'])}<span class="l2">{t(lj['headline_yellow'])}</span></div>
      {photo(lj['photo_left'], '', 'PHOTO 1 (portrait)').replace('class=" ph', 'style="left:93px;top:800px;width:534px;height:620px;border-radius:26px" class="ph')}
      {photo(lj['photo_right'], '', 'PHOTO 2 (portrait)').replace('class=" ph', 'style="left:653px;top:800px;width:534px;height:620px;border-radius:26px" class="ph')}
      <div class="lead" style="top:662px;left:93px;right:93px;text-align:left;font-size:28px;letter-spacing:.8px">{t(lj['caption'])}</div>
    """)
    # 5 Quote
    s.append(f"""
      {photo(q['photo'], '', 'SIGNATORIES PHOTO (landscape)').replace('class=" ph', 'style="left:120px;top:295px;width:1040px;height:585px" class="ph')}
      <div class="quote card"><p>{t(q['text'])}</p><div class="att">{t(q['attribution'])}</div></div>
      <div class="qm" style="left:140px;top:968px">66</div>
      <div class="qm qm-end" style="right:142px;top:QEND">99</div>
      <div class="tag">{t(q['tagline'])}</div>
    """)
    return s


def main():
    cfile = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "content.json"
    c = json.loads(cfile.read_text())
    out = ROOT / c.get("output_dir", "exports/mou_template/out")
    out.mkdir(parents=True, exist_ok=True)
    bodies = slides(c)
    for old in out.glob("slide*.png"):
        old.unlink()
    for i, body in enumerate(bodies, 1):
        (out / f"slide{i}.html").write_text(
            f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='slide'>{body}</div></body></html>")
    subprocess.run(["node", str(HERE / "render.js"), str(out), str(len(bodies))], check=True, cwd="/tmp")
    for i in range(1, len(bodies) + 1):
        raw = out / f"_raw{i}.png"
        Image.open(raw).convert("RGB").resize((1080, 1350), Image.LANCZOS).save(out / f"slide{i}.png", optimize=True)
        raw.unlink()
        (out / f"slide{i}.html").unlink()
    print("Rendered to", out)


if __name__ == "__main__":
    main()
