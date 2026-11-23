"""Refresh grouped margin tests and score previously frozen design predictions."""
import argparse
import csv
import hashlib
import re
import subprocess
from tempfile import NamedTemporaryFile

import numpy as np
from run import HERE, ROOT, H, LIMIT, X, centres, scales, direction

# Reuse the PIELM temporal basis and add seven explicit design/grid inputs.
SLOPES = np.random.default_rng(3322).normal(0, .35, (7,len(centres)))
TIMES = np.arange(241)*.5
PATTERN = re.compile(r'(tall_makeup|inlet44L48R|inlet44|inlet48)_([16])_([0-9p]+)_([0-9p]+)_([0-9p]+)(_z38)?_120')


def design(name):
    family, door, soot, depth, flow, fine = PATTERN.fullmatch(name).groups()
    left,right = {'tall_makeup':(.36,.36),'inlet44L48R':(.44,.48),
                  'inlet44':(.44,.44),'inlet48':(.48,.48)}[family]
    soot,depth,flow = [float(v.replace('p','.')) for v in (soot,depth,flow)]
    return np.array([(left-.44)/.08,(right-.44)/.08,door=='6',(soot-.05)/.05,
                     (depth-.24)/.08,(flow-1.28)/.32,bool(fine)])


def basis(t, params, slopes=SLOPES):
    a = np.tanh((t[:,None]-centres)/scales+params@slopes)
    raw = np.column_stack((np.ones(len(t)),a))
    derivative = np.column_stack((np.zeros(len(t)),(1-a*a)/scales))
    gate = np.exp(-t[:,None]/2)
    return (1-gate)*raw, gate*raw/2+(1-gate)*derivative


def load_complete(names=None):
    cases = {}
    for path in sorted((ROOT/'04_Results').glob('*/*_devc.csv')):
        name = path.name.removesuffix('_devc.csv')
        if not PATTERN.fullmatch(name) or (names is not None and name not in names):
            continue
        log = path.with_name(name+'.out')
        if not log.exists() or f'STOP: FDS completed successfully (CHID: {name})' not in log.read_text(errors='replace')[-2048:]:
            continue
        # Existing validator checks deck identity, sampling gaps, units and completion.
        subprocess.run(['node',str(ROOT/'06_Tools/summarize_design.cjs'),str(path.parent)],
                       capture_output=True,check=True)
        with path.open() as f:
            next(f)
            rows = list(csv.DictReader(f))
        t = np.array([float(r['Time']) for r in rows])
        y = np.array([[float(r[f'layer{x:g}']) for x in X] for r in rows])
        if t[0]!=0 or abs(t[-1]-120)>.001 or not np.all((0<=y)&(y<=H)):
            raise ValueError(name)
        if name in cases:
            prior=cases[name]
            if not np.array_equal(y,prior['y']) or not np.array_equal(t,prior['t']):
                raise ValueError('Conflicting completed replicas: '+name)
            continue
        d = design(name)
        phi,deriv = basis(t,d)
        residual = (deriv+(1.28+.32*d[5])/(6.6*.9*H)*phi)[t>=10]
        residual -= residual.mean(axis=0)
        cases[name] = dict(name=name,directory=path.parent,design=d,phi=phi,t=t,y=y,gram=phi.T@phi,
                           rhs=phi.T@(H-y),physics=residual.T@residual,
                           digest=hashlib.sha256(path.read_bytes()).hexdigest())
    return cases


def model(train,name):
    return predict_minima(train, design(name))


def predict_minima(train, d, slopes=SLOPES):
    phi,_=basis(TIMES,d,slopes)
    # Learn the station-wise discrepancy between fitted smooth minima and device minima.
    # The calibration fit, like the PIELM fit, sees outer-training cases only.
    gram=sum(c['gram'] for c in train)+.1*np.eye(phi.shape[1])
    rhs=sum(c['rhs'] for c in train)
    w=np.linalg.solve(gram,rhs)
    avg=np.linalg.solve(gram+25*sum(c['physics'] for c in train),rhs@direction)
    w+=np.outer(avg-w@direction,direction)
    curve=np.clip(H-phi@w,0,H).min(axis=0)
    offset=np.array([c['y'].min(axis=0)-np.clip(H-basis(TIMES,c['design'],slopes)[0]@w,0,H).min(axis=0)
                     for c in train])
    xx=np.array([c['design'] for c in train])
    def kernel(a,b):
        return np.exp(-.5*((a[:,None]-b[None,:])**2).sum(axis=2))
    coeff=np.linalg.solve(kernel(xx,xx)+.25*np.eye(len(xx)),kernel(xx,d[None,:])).T
    correction=offset.mean(axis=0)+(coeff@(offset-offset.mean(axis=0)))[0]
    return curve,np.clip(curve+correction,0,H)


def output(cases,name):
    train=[c for c in cases.values() if not np.array_equal(c['design'][:-1],design(name)[:-1])]
    if not train:
        raise ValueError('Empty training set')
    a,b=model(train,name)
    digest=hashlib.sha256(''.join(sorted(c['digest'] for c in train)).encode()).hexdigest()
    return [dict(case=name,station_m=x,baseline_m=h,corrected_m=p,training_cases=len(train),
                 training_digest=digest) for x,h,p in zip(X,a,b)]


def save(path,rows):
    with NamedTemporaryFile(mode='w',newline='',encoding='utf-8',dir=path.parent,delete=False) as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    from pathlib import Path
    Path(f.name).replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',nargs='*',default=[])
    args=parser.parse_args()
    cases=load_complete()
    archive=HERE/'margin_frozen.csv'
    frozen=list(csv.DictReader(archive.open())) if archive.exists() else []
    for name in args.freeze:
        if any(r['case']==name for r in frozen):
            continue
        if name in cases:
            raise ValueError('Cannot freeze after completion: '+name)
        frozen.extend(output(cases,name))
    if args.freeze:
        save(archive,frozen)
    cv=[]
    for name,c in cases.items():
        for r,y in zip(output(cases,name),c['y'].min(axis=0)):
            cv.append(dict(**r,actual_m=y))
    save(HERE/'margin_grouped.csv',cv)
    scored=[dict(**r,actual_m=cases[r['case']]['y'][:,list(X).index(float(r['station_m']))].min())
            for r in frozen if r['case'] in cases]
    if scored:
        save(HERE/'margin_prospective.csv',scored)
    for tag,rows in [('grouped',cv),('prospective',scored)]:
        if not rows:
            continue
        for key in ['baseline_m','corrected_m']:
            designs=sorted({r['case'] for r in rows})
            actual,pred=([min(float(r[k]) for r in rows if r['case']==name) for name in designs]
                         for k in ['actual_m',key])
            actual,pred=np.array(actual),np.array(pred)
            print(tag,key,len(designs),'design-min MAE',np.mean(abs(actual-pred)),
                  'false pass',sum((actual<LIMIT)&(pred>=LIMIT)),'of',sum(actual<LIMIT),
                  'false fail',sum((actual>=LIMIT)&(pred<LIMIT)),'of',sum(actual>=LIMIT))


if __name__=='__main__':
    main()
