"""Forecast remaining height loss at each station; preserve censoring after an early stop."""
import csv

import numpy as np

from remaining_drop import HERE, X, LIMIT, load_complete, prefix, save, stop_series


def predict(train, test, cutoff):
    history = np.stack([prefix(c, cutoff) for c in train])
    observed = prefix(test, cutoff)
    losses = history - np.array([c['y'].min(axis=0) for c in train])
    # Compare the same station's previous low and its most recent 15 s minimum.
    def recent(c):
        return c['y'][(c['t'] > cutoff-15) & (c['t'] <= cutoff)].min(axis=0)
    design_distance = np.sum((np.array([c['design'] for c in train])-test['design'])**2, axis=1)
    distance = np.zeros_like(history)
    for x, q in [(history, observed), (np.array([recent(c) for c in train]), recent(test))]:
        distance += .5*((x-q)/np.maximum(x.std(axis=0),.01))**2
    distance += design_distance[:,None]
    w = np.exp(-.5*(distance-distance.min(axis=0)))
    return np.maximum(0, observed-(w*losses).sum(axis=0)/w.sum(axis=0))


def main():
    loaded=load_complete()
    with (HERE/'minimum_risk_holdouts.csv').open() as f:
        full={r['case']:loaded[r['case']] for r in csv.DictReader(f)}
    with (HERE/'stopped_diagnostics.csv').open() as f:
        stopped=[stop_series(r) for r in csv.DictReader(f)]
    with (HERE/'remaining_drop_holdouts.csv').open() as f:
        baseline={(r['case'],int(r['cutoff_s'])):float(r['local_loss_m']) for r in csv.DictReader(f)}
    stations,designs=[],[]
    for cutoff in (30,60,90):
        for c in [*full.values(),*stopped]:
            if c['t'][-1]<cutoff:
                continue
            name=c['name']
            train=[other for other in full.values() if np.any(other['design'][:-1]!=c['design'][:-1])]
            p=predict(train,c,cutoff)
            obs=prefix(c,cutoff)
            known=c['y'].min(axis=0)
            for j,x in enumerate(X):
                hits=np.flatnonzero(c['y'][:,j]<LIMIT)
                label=int(known[j]<LIMIT) if name in full or len(hits) else ''
                stations.append(dict(case=name,cutoff_s=cutoff,x_m=x,observed_min_m=obs[j],
                                     predicted_min_m=p[j],breach=label,
                                     first_breach_s=c['t'][hits[0]] if len(hits) else '',
                                     full_min_m=known[j] if name in full else ''))
            designs.append(dict(case=name,cutoff_s=cutoff,observed_min_m=obs.min(),actual_breach=int(known.min()<LIMIT),
                                previous_m=baseline[name,cutoff],station_model_m=p.min(),
                                full_min_m=known.min() if name in full else ''))
    save(HERE/'station_drop_holdouts.csv',stations)
    save(HERE/'station_drop_designs.csv',designs)
    for cutoff in (30,60,90):
        s=[r for r in designs if r['cutoff_s']==cutoff]
        future=[r for r in s if r['actual_breach'] and r['observed_min_m']>=LIMIT]
        for key in ('previous_m','station_model_m'):
            print(cutoff,key,'future hits',sum(r[key]<LIMIT for r in future),'/',len(future),
                  'false',sum(not r['actual_breach'] and r[key]<LIMIT for r in s),
                  'MAE cm',round(100*np.mean([abs(r[key]-r['full_min_m']) for r in s if r['full_min_m']!='']),2))
        for group in ('ends','interior'):
            s=[r for r in stations if r['cutoff_s']==cutoff and r['observed_min_m']>=LIMIT and
               ((r['x_m'] in (X[0],X[-1]))==(group=='ends'))]
            events=[r for r in s if r['breach']==1]
            print(group,'hits',sum(r['predicted_min_m']<LIMIT for r in events),'/',len(events),
                  'false',sum(r['breach']==0 and r['predicted_min_m']<LIMIT for r in s),
                  'unresolved alarms',sum(r['breach']=='' and r['predicted_min_m']<LIMIT for r in s))
            if cutoff==90:
                print([(r['case'],r['x_m'],round(r['predicted_min_m'],4)) for r in events])


if __name__=='__main__':
    main()
