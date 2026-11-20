"""Render the four digitized experimental profiles with identical panel scales."""
import csv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
with (root / "05_Calculations/peng_fig9.csv").open() as source:
    rows = list(csv.DictReader(source))
im = Image.new("RGB", (1500, 790), "white")
draw = ImageDraw.Draw(im)
def label(x, y, text, size=24, anchor="la"):
    draw.text((x, y), text, fill="#202020", anchor=anchor,
              font=ImageFont.truetype("arial.ttf", size))
label(75, 40, "Ceiling temperature rise along the compartment centreline", 39)
label(75, 104, "Temperature rise, ΔT (K)", 24)
for n, power in enumerate(["47.2", "106.2"]):
    left = 100 + n * 720
    def xy(r, t):
        return left+(r+350)*620/700, 620-(t-300)*400/700
    label(left, 158, power+" kW", 30)
    for t in range(300, 1001, 100):
        _, y = xy(0, t)
        draw.line((left,y,left+620,y), fill="#d7dce0")
        label(left-9,y,str(t),19,"rm")
    for r in range(-300, 301, 100):
        x,_ = xy(r,300)
        label(x,640,str(r),19,"mm")
    label(left+310,680,"Distance from fire axis, r (cm)",22,"mm")
    for op, color in [("OP-1","#153f69"),("OP-6","#a24220")]:
        points=[xy(float(v["r_cm"]),float(v["delta_T_K"])) for v in rows if v["hrr_kw"]==power and v["opening"]==op]
        assert len(points)==51
        for x,y in points:
            if op=="OP-1": draw.rectangle((x-4,y-4,x+4,y+4),outline=color,width=2)
            else: draw.polygon([(x-5,y),(x+4,y-5),(x+4,y+5)],outline=color,width=2)
draw.rectangle((830,114,842,126),outline="#153f69",width=2)
label(855,105,"OP-1  All open",22)
draw.polygon([(1100,120),(1112,113),(1112,127)],outline="#a24220",width=2)
label(1124,105,"OP-6  R1 only",22)
label(75,736,"Source: Peng et al. (2021), Fig. 9(b,d). Digitized from the published figure.",21)
im.save(root/"07_Report/peng_ceiling_profiles.png",dpi=(200,200))
