"""Audit grid-resolved room openings and flush burner from actual FDS SMV indices."""
import csv
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["mesh","object","x_min_m","x_max_m","y_min_m","y_max_m","z_min_m","z_max_m","area_m2","area_change_pct"])
for mesh in ("coarse","medium","fine","doorflow"):
    case=f"op1_106_{mesh}"
    source=root / "04_Results" / case / (case+".smv")
    if mesh=="doorflow" and not source.exists():
        source=root / "04_Results/doorflow_check/doorflow_check.smv"
    text=source.read_text().splitlines()
    def block(name):
        i=text.index(name)
        count=int(text[i+1].split()[0])
        return [(list(map(float,text[i+2+j].split()[:6])),
                 list(map(int,text[i+2+count+j].split()[:6]))) for j in range(count)]
    grid=next(i for i,line in enumerate(text) if line.startswith("GRID "))
    nx,ny,nz=map(int,text[grid+1].split()[:3])
    def emit(name, idx, nominal, axis):
        xa,xb,ya,yb,za,zb=[n*scale for n,scale in zip(idx,(6.6/nx,6.6/nx,1.4/ny,1.4/ny,.76/nz,.76/nz))]
        area=(xb-xa)*((yb-ya) if axis=="z" else (zb-za))
        writer.writerow([mesh,name,*[round(v,6) for v in (xa,xb,ya,yb,za,zb,area)],round(100*(area/nominal-1),2)])
    [(geom,idx)]=[(g,j) for g,j in block("VENT") if g==[3.175,3.425,.325,.575,0,0]]
    emit("burner",idx,.25**2,"z")
    lintels=sorted([(g,j) for g,j in block("OBST") if g[4:]==[.63,.76]])
    assert len(lintels)==4
    for name,(_,j) in zip(("L2","L1","R1","R2"),lintels):
        emit(name,j[:4]+[0,j[4]],.43*.63,"y")
