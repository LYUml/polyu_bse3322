"""Paired geometry ablation, held out by physical layout, using existing FDS outputs."""
import csv
import json
import re
import subprocess

import numpy as np

from margin_monitor import HERE, ROOT, H, LIMIT, SLOPES, X, basis, predict_minima, save

NAME = re.compile(r"(.+)_([16])_([0-9p]+)_([0-9p]+)_([0-9p]+)(_z38)?_120")
EXTENDED = np.vstack((SLOPES, np.random.default_rng(3323).normal(0, .35, (14, SLOPES.shape[1]))))


def geometry(deck):
    ends = [0., 0.]
    curtains, vents = [], []
    for kind, body in re.findall(r"&(VENT|OBST)\s+([^/]+?)/", deck):
        match = re.search(r"XB=([\d., +\-]+)", body)
        if not match:
            continue
        a,b,c,d,e,f = map(float, match[1].strip(" ,").split(","))
        if kind == "OBST" and a == b and (c,d,f) == (0,.9,.76):
            curtains.append((a, round(f-e, 4)))
        if kind == "VENT" and "SURF_ID='OPEN'" in body and a==b and a in (0,6.6) and (c,d,e)==(0,.9,0):
            ends[int(a>0)] = f
        if kind == "VENT" and "SURF_ID='HVAC'" in body:
            assert e == f == .76
            vents.append((round((a+b)/2,4),round((c+d)/2,4),round((b-a)*(d-c),5)))
    assert len(curtains) in (0,2) and 0<len(vents)<=4
    curtains.sort()
    spacing = round(curtains[-1][0]-curtains[0][0],4) if curtains else 0.
    return ends, curtains, spacing, sorted(vents)


def load():
    data = {}
    for file in sorted((ROOT/'04_Results').glob('*/*_devc.csv')):
        name=file.name.removesuffix('_devc.csv')
        m=NAME.fullmatch(name)
        if not m:
            continue
        folder=file.parent
        deckfile=folder/(name+'.fds')
        if not deckfile.exists():
            continue
        deck=deckfile.read_text()
        if "FUEL='PROPYLENE'" not in deck or "SURF_ID='HVAC'" not in deck:
            continue
        event=ROOT/'05_Calculations'/(name+'_screen_failure.json')
        complete='FDS completed successfully (CHID: '+name+')' in (folder/(name+'.out')).read_text(errors='replace')[-2048:]
        if not complete and not event.exists():
            continue
        ends,curtains,spacing,vents=geometry(deck)
        depth=curtains[0][1] if curtains else 0.
        q=sum(map(float,re.findall(r'VOLUME_FLOW=([\d.]+)',deck)))
        soot=float(re.search(r'SOOT_YIELD=([\d.]+)',deck)[1])
        assert abs(q-float(m[5].replace('p','.')))<1e-5 and abs(depth-float(m[4].replace('p','.')))<1e-5
        raw=np.array([(ends[0]-.44)/.08,(ends[1]-.44)/.08,m[2]=='6',(soot-.05)/.05,
                      (depth-.24)/.08,(q-1.28)/.32,bool(m[6])])
        # Zero-centre added predictors at the previously studied two-vent preset.
        def encode(gap, outlets):
            slots=[((x-3.3)/3.3,(y-.45)/.45,area/.32) for x,y,area in outlets]
            return np.array([gap,(len(slots))/2,*np.ravel(slots+[(0,0,0)]*(4-len(slots)))])
        extra=encode(spacing,vents)-encode(1.,[(3.1,.45,.32),(3.5,.45,.32)])
        key=json.dumps([ends,[x for x,_ in curtains],vents],separators=(',',':'))
        if complete:
            subprocess.run(['node',str(ROOT/'06_Tools/summarize_design.cjs'),str(folder)],capture_output=True,check=True)
        with file.open() as f:
            next(f)
            rows=list(csv.DictReader(f))
        t=np.array([float(r['Time']) for r in rows])
        y=np.array([[float(r[f'layer{x:g}']) for x in X] for r in rows])
        if not complete:
            rec=json.loads(event.read_text())
            assert rec['chid']==name and rec['observed_min_m']<LIMIT
        case=dict(observed=y.min() if complete else rec['observed_min_m'],name=name,key=key,raw=raw,extra=extra,complete=complete,y=y,t=t,flow=q,spacing=spacing,vents=vents)
        if name in data:
            assert key==data[name]['key'] and (not complete or not data[name]['complete'] or np.array_equal(y,data[name]['y']))
            if data[name]['complete'] or not complete:
                continue
        data[name]=case
    return data


def evaluate(data):
    rows=[]
    for augmented in (False,True):
        slopes=EXTENDED if augmented else SLOPES
        for c in data.values():
            d=np.r_[c['raw'],c['extra']] if augmented else c['raw']
            c['design']=d
            if c['complete']:
                phi,der=basis(c['t'],d,slopes)
                res=(der+c['flow']/(6.6*.9*H)*phi)[c['t']>=10]
                res-=res.mean(axis=0)
                c.update(gram=phi.T@phi,rhs=phi.T@(H-c['y']),physics=res.T@res)
        for key in sorted({c['key'] for c in data.values()}):
            train=[c for c in data.values() if c['complete'] and c['key']!=key]
            x=np.array([c['design'] for c in train])
            y=np.array([c['y'].min() for c in train])
            xc=x-x.mean(0)
            coef=np.linalg.solve(xc.T@xc+np.eye(x.shape[1]),xc.T@(y-y.mean()))
            for c in data.values():
                if c['key']!=key:
                    continue
                d=c['design']
                dist=np.linalg.norm(x-d,axis=1)
                rows.append(dict(case=c['name'],layout=key,augmented=int(augmented),complete=int(c['complete']),
                                 observed_min_m=c['observed'],pinn=predict_minima(train,d,slopes)[1].min(),
                                 ridge=y.mean()+(d-x.mean(0))@coef,nearest=y[np.isclose(dist,dist.min())].mean()))
    return rows


if __name__=='__main__':
    data=load()
    rows=evaluate(data)
    save(HERE/'vent_geometry_ablation.csv',rows)
    for aug in (0,1):
        part=[r for r in rows if r['augmented']==aug]
        print('cases, layouts, full, failures',len(part),len({r['layout'] for r in part}),sum(r['complete'] for r in part),sum(r['observed_min_m']<LIMIT for r in part))
        for method in ('pinn','ridge','nearest'):
            print(aug,method,'MAE cm',round(100*np.mean([abs(r[method]-r['observed_min_m']) for r in part if r['complete']]),2),
                  'false pass',sum(r[method]>=LIMIT>r['observed_min_m'] for r in part),
                  'false fail',sum(r[method]<LIMIT<=r['observed_min_m'] for r in part))


