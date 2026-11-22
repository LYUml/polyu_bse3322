"""Paired tests for opening geometry and the running-minimum consistency bound."""
import csv

import numpy as np

from margin_monitor import HERE, LIMIT, design, load_complete, save


def opening_ratio(d):
    left, right = .44+.08*d[:2]
    doors = 1 if d[2] else 4
    scale = .9*(left**1.5 + right**1.5) + doors*.43*.63**1.5
    return (1.28+.32*d[5])/(np.sqrt(9.81)*scale)


def main():
    with (HERE/'minimum_risk_holdouts.csv').open() as f:
        archived = list(csv.DictReader(f))
    cases = load_complete()
    cohort = [cases[r['case']] for r in archived]
    rows = []
    for r,c in zip(archived,cohort):
        train = [z for z in cohort if not np.array_equal(z['design'][:-1],c['design'][:-1])]
        coords = np.array([z['design'] for z in train])
        index = np.array([opening_ratio(d) for d in coords])
        scale = max(index.std(),1e-8)
        coords = np.column_stack((coords,(index-index.mean())/scale))
        query = np.r_[c['design'],(opening_ratio(c['design'])-index.mean())/scale]
        target = np.array([z['y'].min() for z in train])
        def kernel(x):
            return np.exp(-.5*((x[:,None]-coords[None,:])**2).sum(axis=2))
        coef = np.linalg.solve(kernel(coords)+.25*np.eye(len(train)),target-target.mean())
        direct = target.mean() + (kernel(query[None,:])@coef)[0]
        hybrid = float(r['hybrid_m'])
        actual = c['y'].min()
        np.testing.assert_allclose(actual,float(r['actual_m']))
        new = (direct+float(r['pinn_m']))/2
        rows.append(dict(case=c['name'],cutoff_s=0,actual_m=actual,
                         baseline_m=hybrid,opening_m=new,observed_m='',constrained_m=hybrid))
        for cutoff in (30,60,90):
            observed = c['y'][c['t']<=cutoff].min()
            rows.append(dict(case=c['name'],cutoff_s=cutoff,actual_m=actual,baseline_m=hybrid,
                             opening_m=new,observed_m=observed,constrained_m=min(hybrid,observed)))
    save(HERE/'physical_bounds_holdouts.csv',rows)
    for t in (0,30,60,90):
        sample = [r for r in rows if r['cutoff_s']==t]
        keys = ['baseline_m','opening_m'] if not t else ['observed_m','constrained_m']
        for key in keys:
            y,p = np.array([[r['actual_m'],r[key]] for r in sample]).T
            print(t,key,'MAE cm',round(np.abs(y-p).mean()*100,2),
                  'false pass',sum((y<LIMIT)&(p>=LIMIT)),'false fail',sum((y>=LIMIT)&(p<LIMIT)))


if __name__=='__main__':
    main()
