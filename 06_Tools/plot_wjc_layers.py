"""Render selected WJC center-plane thermal layer estimates from diagnostic CSV."""
import csv
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
records = defaultdict(list)
with (root / "04_Results/wjc_layer_diagnostic.csv").open(encoding="utf-8-sig") as source:
    for row in csv.DictReader(source):
        records[row["x_m"], row["case"]].append(row)

canvas = Image.new("RGB", (1400, 880), "white")
draw = ImageDraw.Draw(canvas)
def label(x, y, text, size=20, color="#253348", bold=False):
    font = ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
    draw.text((x,y), text, fill=color, font=font)

label(55,22,"Thermal layer inside the curtain bay",38,bold=True)
label(56,80,"WJC center-plane data  |  soot yield 0.10  |  50-100 s  |  matched exhaust settings",23)
colors = {"no_curtain":"#286DA8", "curtain":"#B34824"}
for j,(kind,title) in enumerate([("no_curtain","Without curtains"),("curtain","With curtains")]):
    left=100+j*675
    label(left,137,title,24,colors[kind],True)
    for i,x in enumerate(["2.991","3.609"]):
        top=220+i*276
        right=left+560
        def px(t): return left+(t-50)*11.2
        def py(h): return top+200-h*250
        label(left,top-43,"x = "+x+" m",20,bold=True)
        for h in [0,0.2,0.4,0.6,0.8]:
            draw.line((left,py(h),right,py(h)),fill="#DBE1E8")
            label(left-43,py(h)-12,f"{h:.1f}",17)
        for tick in range(50,101,10):
            label(px(tick)-12,top+204,str(tick),17)
        for segment in range(left,right,14):
            draw.line((segment,py(.38),min(segment+8,right),py(.38)),fill="#292929",width=2)
        prev=None
        series=records[x,kind]
        assert len(series)==501
        for row in series:
            if row["status"]!="estimate":
                prev=None
                continue
            pos=(px(float(row["time_s"])),py(float(row["height_m"])))
            if prev: draw.line([prev,pos],fill=colors[kind],width=2)
            prev=pos
        valid=[r for r in series if r["status"]=="estimate"]
        below=sum(float(r["height_m"])<.38 for r in valid)
        label(left+275,top-42,f"Below 0.38 m: {below}/{len(valid)} frames",18,colors[kind])
label(55,758,"Horizontal axis: time (s)     Vertical axis: height above floor (m)     Dashed line: 0.38 m criterion",20)
label(55,802,"Gaps omit weak or invalid thermal profiles. Local temperature-derived estimates require soot corroboration.",19)
canvas.save(root / "05_Calculations/wjc_thermal_layer.png")
