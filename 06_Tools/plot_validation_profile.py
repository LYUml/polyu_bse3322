import csv
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
case = sys.argv[1]
opening, power, variant = case.split("_", 2)
power_kw = {"47": "47.2", "106": "106.2"}[power]
with (root / "05_Calculations" / f"{case}_90_120.csv").open(encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
if len(rows) != 51:
    raise ValueError("Expected 51 paired stations")
observed = [(float(r["figure_r_cm"]), float(r["exp_rise_K"])) for r in rows]
model = [(float(r["model_x_cm"])-330, float(r["fds_rise_K"])) for r in rows]
adiabatic = []
if variant == "board_doorflow":
    baseline = root / "05_Calculations" / f"{opening}_{power}_doorflow_90_120.csv"
    with baseline.open(encoding="utf-8-sig") as f:
        reference = list(csv.DictReader(f))
    keys = ("model_x_cm", "figure_r_cm", "exp_rise_K")
    if [[r[k] for k in keys] for r in reference] != [[r[k] for k in keys] for r in rows]:
        raise ValueError("Wall comparison requires matching experimental and model stations")
    adiabatic = [(float(r["model_x_cm"])-330, float(r["fds_rise_K"])) for r in reference]
low = math.floor(min(y for _, y in observed+model+adiabatic)/50)*50
high = math.ceil(max(y for _, y in observed+model+adiabatic)/50)*50
image = Image.new("RGB", (1400, 800), "white")
draw = ImageDraw.Draw(image)
def label(x, y, text, size, anchor="la"):
    draw.text((x,y), text, fill="#222222", font=ImageFont.truetype("arial.ttf", size), anchor=anchor)
def xy(x, y):
    return (110+(x+340)*1230/680, 640-(y-low)*440/(high-low))
label(72, 36, f"Ceiling temperature rise   |   OP-{opening[-1]}, {power_kw} kW", 39)
label(72, 105, "Temperature rise (K)", 24)
for t in range(low, high+1, 50):
    _, y = xy(0,t)
    draw.line((110,y,1340,y), fill="#d5dade")
    label(96,y,str(t),21,"rm")
for r in range(-300,301,100):
    x,_ = xy(r,low)
    label(x,663,str(r),21,"mm")
if adiabatic:
    draw.line([xy(x,y) for x,y in adiabatic], fill="#646464", width=3)
    draw.line((490,122,540,122),fill="#646464",width=3)
    label(552,122,"FDS, adiabatic",22,"lm")
draw.line([xy(x,y) for x,y in model], fill="#155482", width=4)
for x,y in observed:
    a,b = xy(x,y)
    draw.ellipse((a-5,b-5,a+5,b+5), fill="white", outline="#a64220", width=3)
draw.ellipse((740,117,750,127),fill="white",outline="#a64220",width=3)
label(763,122,"Peng et al. (2021), Fig. 9",22,"lm")
draw.line((1042,122,1092,122),fill="#155482",width=4)
variant_label = {"board_doorflow": "proxy board", "doorflow": "adiabatic"}.get(variant, variant)
label(1104,122,f"FDS, {variant_label}",22,"lm")
label(72, 82, "FDS averaging interval 90–120 s", 19)
label(725,724,"Distance from fire axis (cm)",25,"mm")
image.save(root/"07_Report"/f"{case}_validation.png",dpi=(200,200))
