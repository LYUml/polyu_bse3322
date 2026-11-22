"""Grouped retrospective evaluation of first-breach risk at four horizons."""
import csv
import json

import numpy as np

from dual_task import verify_breach
from margin_monitor import HERE, ROOT, LIMIT, X, design, load_complete, save

HORIZONS = np.arange(30,121,30)


def stopped_time(name):
    report=json.loads((ROOT/'05_Calculations'/(name+'_screen_failure.json')).read_text(encoding='utf-8-sig'))
    verify_breach(name,report)
    expected=float(report['first_time_s'])
    for path in (ROOT/'04_Results').glob('*/'+name+'_devc.csv'):
        with path.open() as f:
            next(f)
            first=next((float(row['Time']) for row in csv.DictReader(f)
                        if min(float(row[f'layer{x:g}']) for x in X)<LIMIT),None)
        if first is not None and abs(first-expected)<.001:
            return first
    raise ValueError('Cannot confirm first recorded breach: '+name)


def hazards(coords, times, query):
    x,y=[],[]
    for d,t in zip(coords,times):
        for k,horizon in enumerate(HORIZONS):
            x.append(np.r_[1.,d,np.eye(4)[k,1:]])
            y.append(t<=horizon)
            if t<=horizon:
                break
    x,y=np.array(x),np.array(y)
    beta=np.zeros(x.shape[1])
    penalty=np.diag(np.r_[0.,np.ones(len(beta)-1)])
    for _ in range(60):
        p=1/(1+np.exp(-np.clip(x@beta,-35,35)))
        step=np.linalg.solve(x.T@((p*(1-p))[:,None]*x)+penalty,x.T@(p-y)+penalty@beta)
        beta-=step
        if np.max(np.abs(step))<1e-9:
            break
    else:
        raise ValueError('Hazard model did not converge')
    future=np.array([np.r_[1.,query,d[1:]] for d in np.eye(4)])
    conditional=1/(1+np.exp(-future@beta))
    return 1-np.cumprod(1-conditional)


def main():
    with (HERE/'dual_task_scores.csv').open() as f:
        refs=list(csv.DictReader(f))
    complete=load_complete()
    times=[]
    for r in refs:
        if r['source']=='stopped':
            first=stopped_time(r['case'])
        else:
            c=complete[r['case']]
            hits=c['t'][c['y'].min(axis=1)<LIMIT]
            first=hits[0] if len(hits) else np.inf
        assert np.isfinite(first)==bool(int(r['breach']))
        times.append(first)
    times=np.array(times)
    coords=np.array([design(r['case']) for r in refs])
    rows=[]
    for i,r in enumerate(refs):
        train=np.any(coords[:,:-1]!=coords[i,:-1],axis=1)
        risks=hazards(coords[train],times[train],coords[i])
        assert np.all(np.diff(risks)>=0)
        for h,risk in zip(HORIZONS,risks):
            rows.append(dict(case=r['case'],source=r['source'],horizon_s=h,
                             first_breach_s=times[i] if np.isfinite(times[i]) else '',
                             observed=int(times[i]<=h),risk=risk,
                             frequency=np.mean(times[train]<=h),binary120=r['with_stopped']))
    save(HERE/'first_breach_scores.csv',rows)
    for h in HORIZONS:
        s=[r for r in rows if r['horizon_s']==h]
        y=np.array([r['observed'] for r in s],bool)
        for key in ['frequency','risk']+(['binary120'] if h==120 else []):
            p=np.array([float(r[key]) for r in s])
            print(h,key,'events',sum(y),'missed',sum(y&(p<.5)),'false alarms',sum(~y&(p>=.5)),
                  'Brier',round(np.mean((p-y)**2),3))


if __name__=='__main__':
    main()
