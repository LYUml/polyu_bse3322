"""Render completed OP-6 scenario minima from the review table."""
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
source = root / "05_Calculations/tall_makeup_op6_completed_scenarios.csv"
with source.open(encoding="utf-8-sig") as stream:
    rows = [r for r in csv.DictReader(stream) if r["opening"] == "OP6"
            and float(r["end_s"]) == 120 and float(r["total_flow_m3_s"]) == 1.28]

canvas = Image.new("RGB", (1500, 780), "white")
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype("arial.ttf", 29)
title = ImageFont.truetype("arialbd.ttf", 40)
draw.text((65, 40), "Minimum thermal layer height by curtain depth", font=title, fill="#15252d")
draw.text((65, 103), "OP-6   |   1.28 m³/s   |   Eight stations, 0–120 s", font=font, fill="#354954")
draw.text((65, 189), "Minimum height (m)", font=font, fill="#15252d")

def y(height):
    return 640 - height * 950

for tick in (0, 0.1, 0.2, 0.3, 0.4):
    draw.line((175, y(tick), 1390, y(tick)), fill="#d7dde0", width=2)
    draw.text((150, y(tick)), f"{tick:.1f}", anchor="rm", font=font, fill="#354954")
draw.line((175, y(0.38), 1390, y(0.38)), fill="#ac3d36", width=3)
draw.text((1390, y(0.38)-5), "0.38 m target", anchor="rb", font=font, fill="#963229")

depths = sorted({float(row["curtain_depth_m"]) for row in rows})
colors = {0.16: "#185c81", 0.24: "#268566", 0.32: "#805a96"}
for i, depth in enumerate(depths):
    draw.text((510 + 315*i, 185), f"{depth:.2f} m curtain", font=font, fill=colors[depth])
    for row in rows:
        if float(row["curtain_depth_m"]) != depth:
            continue
        soot = float(row["soot_yield"])
        x = 290 + (soot - 0.02) * 12000 + (i-1)*48
        h = float(row["min_layer_m"])
        draw.rectangle((x-19, y(h), x+19, y(0)), fill=colors[depth])
for soot in (0.02, 0.05, 0.10):
    draw.text((290 + (soot-0.02)*12000, 655), f"{soot:.2f}", anchor="mt", font=font, fill="#15252d")
draw.text((760, 714), "Soot yield (kg/kg)", anchor="mt", font=font, fill="#15252d")
canvas.save(root / "07_Report/op6_curtain_soot_minimum_height.png", dpi=(200, 200))
