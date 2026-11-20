"""Recover Peng Fig. 9(b,d) independently from native PDF objects and axis ticks."""
import csv
import sys
from pathlib import Path
import pdfplumber

root = Path(__file__).resolve().parents[1]
output = csv.writer(sys.stdout, lineterminator="\n")
output.writerow(["hrr_kw","opening","r_cm","delta_T_K"])
with pdfplumber.open(next((root/"02_References/02_Papers").glob("Peng*.pdf"))) as pdf:
    page = pdf.pages[7]
    for q,top,bottom in [(47.2,55,213),(106.2,264,424)]:
        borders=[l for l in page.lines if 325<l["x0"]<332 and top<l["top"]<bottom
                 and l["width"]>180 and l["height"]<0.001 and l["stroking_color"]==0]
        assert len(borders)==2
        left,right=borders[0]["x0"],borders[0]["x1"]
        ticks=sorted({round(l["top"],3) for l in page.lines if abs(l["x0"]-left)<0.01
                      and 2.8<l["width"]<3.1 and l["height"]<0.001 and top<l["top"]<bottom})
        step=50 if q==47.2 else 100
        labels=list(range(700,349,-50)) if q==47.2 else list(range(1000,399,-100))
        assert len(ticks)==len(labels)
        for op,objects in [('OP-1',page.rects),('OP-6',page.curves)]:
            points=[]
            for v in objects:
                if not v['stroke'] or not 3.5<v['width']<5 or not 3.5<v['height']<6: continue
                if op=='OP-1' and v['stroking_color']!=0: continue
                if op=='OP-6' and v['stroking_color']!=(0.502,0,0): continue
                x=(v['x1']+v['x0'])/2
                y=(v['top']+v['bottom'])/2
                if not left<x<right or not top<y<bottom: continue
                if x>445 and y<top+55: continue  # legend
                r=(x-left)/(right-left)*800-400
                if abs(r)>334: continue
                k=min(range(len(ticks)-1),key=lambda i:abs(y-(ticks[i]+ticks[i+1])/2))
                dt=labels[k]-(y-ticks[k])*step/(ticks[k+1]-ticks[k])
                points.append((r,dt))
            assert len(points)==51,(q,op,len(points))
            for r,t in sorted(points): output.writerow([q,op,round(r,1),round(t,1)])
