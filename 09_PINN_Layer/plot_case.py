"""Render the eight held-out station traces for the prior GP false-pass example."""
import csv
import gzip
from PIL import Image, ImageDraw, ImageFont
from run import HERE, X

case = 'tall_makeup_6_0p05_0p24_1p28_120'
with gzip.open(HERE/'holdout_curves.csv.gz', 'rt') as f:
    rows = [r for r in csv.DictReader(f) if r['case'] == case]
img = Image.new('RGB', (1220, 920), 'white')
draw = ImageDraw.Draw(img)
def label(x, y, text, size=17, fill='#25313d'):
    draw.text((x, y), text, font=ImageFont.load_default(size=size), fill=fill)

label(46, 14, 'Eight smoke-layer stations | held-out OP-6 design', 30)
label(46, 53, 'Tall makeup   /   curtain 0.24 m   /   flow 1.28 m3/s   /   soot yield 0.05', 19)
for left, name, color in [(46,'FDS','#284669'),(165,'PINN','#df682d'),(292,'0.38 m threshold','#a92f49')]:
    draw.line((left, 96, left+23, 96), fill=color, width=3)
    label(left+30,84,name)
for i, station in enumerate(X):
    records = [r for r in rows if float(r['x_m']) == station]
    left, top = 65+(i%2)*610, 152+(i//2)*185
    right, bottom = left+510, top+118
    label(left,top-30,f'x = {station:g} m',19)
    for height in [0, .38, .76]:
        y = bottom-height/.76*118
        draw.line((left,y,right,y), fill='#a92f49' if height==.38 else '#cbd3da')
        label(left-47,y-10,f'{height:.2f}',14)
    for key,color in [('fds_m','#284669'),('pinn_m','#df682d')]:
        pts=[(left+float(r['time_s'])/120*510,bottom-float(r[key])/.76*118) for r in records]
        draw.line(pts, fill=color, width=2)
    for t in [0,30,60,90,120]:
        label(left+t/120*510-6,bottom+4,str(t),14)
label(46, 882, 'Horizontal axis: time (s)   /   Vertical axis: layer height (m)   /   Native device samples joined by lines',18)
img.save(HERE/'eight_stations.png')
