"""Build the three Task-2 design decks (A: no measures, B: shafts, C: shafts + curtains).

All three share the 106.2 kW propylene fire, the 203x40x32 mesh and the same
66-point ceiling array, so that the only difference is the smoke-control measure.
Each deck also gets layer-height devices and two vertical thermocouple trees,
which the previous design runs were missing.
"""
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "..", "_tmp", "bse_data")
OUT = BASE

SRC = {
    "A": "Smoke Extraction 1__BSE3322_Fire_CFD_Model.fds",          # shafts; strip them
    "B": "Smoke Extraction 1__BSE3322_Fire_CFD_Model.fds",          # keep as is
    "C": "Smoke Extraction 1 but Fire curtain__BSE3322_Fire_CFD_Model.fds",
}

LAYER = """\
&DEVC ID='LAYER_bay', QUANTITY='LAYER HEIGHT', XB=3.0,3.8,0.3,0.6,0.0,0.76/
&DEVC ID='LAYER_far', QUANTITY='LAYER HEIGHT', XB=5.4,5.8,0.3,0.6,0.0,0.76/
&DEVC ID='V_fire_0.2', QUANTITY='TEMPERATURE', XYZ=3.30,0.45,0.20/
&DEVC ID='V_fire_0.4', QUANTITY='TEMPERATURE', XYZ=3.30,0.45,0.40/
&DEVC ID='V_fire_0.55', QUANTITY='TEMPERATURE', XYZ=3.30,0.45,0.55/
&DEVC ID='V_fire_0.70', QUANTITY='TEMPERATURE', XYZ=3.30,0.45,0.70/
&DEVC ID='V_far_0.2', QUANTITY='TEMPERATURE', XYZ=5.60,0.45,0.20/
&DEVC ID='V_far_0.4', QUANTITY='TEMPERATURE', XYZ=5.60,0.45,0.40/
&DEVC ID='V_far_0.55', QUANTITY='TEMPERATURE', XYZ=5.60,0.45,0.55/
&DEVC ID='V_far_0.70', QUANTITY='TEMPERATURE', XYZ=5.60,0.45,0.70/
&DEVC ID='VIS_bay', QUANTITY='VISIBILITY', XYZ=3.30,0.45,0.40/
&DEVC ID='CO_bay', QUANTITY='VOLUME FRACTION', SPEC_ID='CARBON MONOXIDE', XYZ=3.30,0.45,0.40/
"""

OPEN_TOP = (
    "&VENT ID='Vent-R-upper', SURF_ID='OPEN', XB=0.0,0.0,0.0,1.3,0.76,1.06/\n"
    "&VENT ID='Vent-L-upper', SURF_ID='OPEN', XB=6.6,6.6,0.0,1.3,0.76,1.06/\n"
    "&VENT ID='Vent-Front-upper', SURF_ID='OPEN', XB=0.0,6.6,1.3,1.3,0.76,1.06/\n"
)


def strip_measure(text: str) -> str:
    """Case A: remove the ceiling slab, the shafts and their hardware."""
    keep = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("&") and (
            "Obstruction" in line and ("0.76,0.8" in line or "FANty" in line)
            or "Vent-Upper" in line
            or "Vent-FANTY" in line
            or "Vent-Left Upper" in line
            or "Vent-Right Upper" in line
            or s.startswith("&HVAC")
        ):
            continue
        keep.append(line)
    text = "\n".join(keep) + "\n"
    return text.replace("&VENT ID='Vent-R'", OPEN_TOP + "&VENT ID='Vent-R'")


def build(tag: str) -> str:
    src = os.path.join(DATA, SRC[tag])
    text = open(src, encoding="latin-1").read()
    if tag == "A":
        text = strip_measure(text)
    text = re.sub(r"&HEAD[^/]*/", f"&HEAD CHID='t2{tag}', TITLE='Task 2 case {tag}'/", text, count=1)
    text = text.replace("&TAIL", LAYER + "&TAIL")
    path = os.path.join(OUT, f"t2_{tag}.fds")
    open(path, "w", encoding="latin-1").write(text)
    return path


if __name__ == "__main__":
    for tag in ("A", "B", "C"):
        print("wrote", build(tag))
