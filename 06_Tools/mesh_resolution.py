"""Compute plume resolution using Yuen et al. (2015), eqs. 26-27, in SI."""
import csv
import math
import re
import sys
from pathlib import Path

models=Path(__file__).resolve().parents[1]/"03_Models"
out=csv.writer(sys.stdout,lineterminator="\n")
out.writerow(["grid","hrr_kW","cells","dx_m","dy_m","dz_m","Dstar_m","Rstar_volume","Rstar_longest","cells_across_Dstar_longest"])
for grid in ("coarse","medium","fine","doorflow"):
    deck=(models/f"op1_106_{grid}.fds").read_text()
    ijk=tuple(map(int,re.search(r"IJK=([\d,]+)",deck)[1].split(",")))
    xb=list(map(float,re.search(r"&MESH[^\n]*XB=([\d.,]+)",deck)[1].split(",")))
    spacing=[(xb[2*i+1]-xb[2*i])/n for i,n in enumerate(ijk)]
    temp=float(re.search(r"TMPA=([\d.]+)",deck)[1])+273.15
    density=101325/(287.05*temp)
    for q in (47.2,106.2):
        diameter=(1000*q/(density*temp*1005*math.sqrt(9.81)))**0.4
        effective=math.prod(spacing)**(1/3)
        out.writerow([grid,q,math.prod(ijk),*[round(v,5) for v in (*spacing,diameter,effective/diameter,max(spacing)/diameter,diameter/max(spacing))]])
