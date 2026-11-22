"""One held-out physical design at a time. Early breaches label the binary task only."""
import csv
import json

import numpy as np

from margin_monitor import HERE, ROOT, LIMIT, PATTERN, X, design, load_complete, save
from minimum_risk import estimate


def verify_breach(name, report):
    stop = float(report['observed_to_s'])
    upper = float(report['observed_min_m'])
    if not (0 < stop < 120 and 0 <= upper < LIMIT):
        raise ValueError(name)
    for path in (ROOT/'04_Results').glob('*/'+name+'_devc.csv'):
        with path.open() as f:
            reader = csv.reader(f)
            units, header = next(reader), next(reader)
            cols = [header.index(f'layer{x:g}') for x in X]
            if units[0]!='s' or any(units[i]!='m' for i in cols):
                raise ValueError(name+' units')
            samples = [r for r in reader if r and float(r[0]) <= stop+.001]
        if samples and abs(float(samples[-1][0])-stop)<.001:
            observed = min(float(r[i]) for r in samples for i in cols)
            if abs(observed-upper)<1e-6:
                return upper
    raise ValueError('Cannot verify recorded breach: '+name)


def score(train_x, train_y, query):
    # Ridge logistic regression, unpenalized intercept, fixed feature scales from design().
    x = np.column_stack([np.ones(len(train_x)),train_x])
    penalty = np.diag([0., *np.ones(train_x.shape[1])])
    beta = np.zeros(x.shape[1])
    for _ in range(60):
        p = 1/(1+np.exp(-np.clip(x@beta,-35,35)))
        grad = x.T@(p-train_y)+penalty@beta
        hess = x.T@((p*(1-p))[:,None]*x)+penalty
        delta = np.linalg.solve(hess,grad)
        beta -= delta
        if np.max(abs(delta))<1e-9:
            break
    else:
        raise ValueError('Logistic fit failed to converge')
    return float(1/(1+np.exp(-np.r_[1,query]@beta)))


def main():
    complete=load_complete()
    upper={}
    for path in sorted((ROOT/'05_Calculations').glob('*_screen_failure.json')):
        r=json.loads(path.read_text(encoding='utf-8-sig'))
        n=r['chid']
        if PATTERN.fullmatch(n) and n not in complete and r['status']=='screen_failed':
            upper[n]=verify_breach(n,r)
    names=sorted(set(complete)|set(upper))
    coords=np.array([design(n) for n in names])
    full=np.array([n in complete for n in names])
    truth=np.array([complete[n]['y'].min()<LIMIT if n in complete else True for n in names])
    rows=[]
    for i,n in enumerate(names):
        mask=np.any(coords[:,:-1]!=coords[i,:-1],axis=1)
        train=[complete[m] for m,keep in zip(names,mask & full) if keep]
        height=estimate(train,n)[2]
        row=dict(case=n,source='complete' if full[i] else 'stopped',breach=int(truth[i]),
                 actual_min_m=complete[n]['y'].min() if full[i] else '',
                 observed_upper_m=upper.get(n,''),regression_m=height)
        for key,subset in [('complete_only',mask&full),('with_stopped',mask)]:
            row[key]=score(coords[subset],truth[subset],coords[i])
        rows.append(row)
    save(HERE/'dual_task_scores.csv',rows)
    def stats(pred):
        return [(int(sum(s&truth&~pred)),int(sum(s&~truth&pred))) for s in (full,~full)]
    print('height MAE cm',np.mean([abs(r['actual_min_m']-r['regression_m']) for r in rows if r['source']=='complete'])*100)
    print('regression',stats(np.array([r['regression_m']<LIMIT for r in rows])))
    for key in ('complete_only','with_stopped'):
        for cutoff in (.5,1/3):
            print(key,cutoff,stats(np.array([r[key]>=cutoff for r in rows])))


if __name__=='__main__':
    main()
