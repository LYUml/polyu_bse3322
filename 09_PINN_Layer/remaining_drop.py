"""Predict additional minimum-height loss after a fixed landmark using past frames only."""
import csv
import numpy as np
from margin_monitor import HERE, ROOT, X, LIMIT, load_complete, design, save


def stop_series(row):
    name=row['case']
    end=float(row['observed_to_s'])
    for path in (ROOT/'04_Results').glob('*/'+name+'_devc.csv'):
        with path.open() as f:
            units=next(csv.reader(f))
            reader=csv.DictReader(f)
            names=[f'layer{x:g}' for x in X]
            if units[0]!='s' or any(units[reader.fieldnames.index(n)]!='m' for n in names):
                raise ValueError(path)
            samples=np.array([[float(r['Time']),*(float(r[n]) for n in names)]
                              for r in reader if float(r['Time']) <= end+.001])
        if len(samples) and abs(samples[-1,0]-end)<.001 and abs(samples[:,1:].min()-float(row['observed_upper_m']))<1e-7:
            if samples[0,0]!=0 or not np.all((np.diff(samples[:,0])>0)&(np.diff(samples[:,0])<.75)):
                raise ValueError(path)
            return dict(t=samples[:,0],y=samples[:,1:],name=name,design=design(name))
    raise ValueError(name)


def prefix(case,cutoff):
    past=case['y'][case['t']<=cutoff]
    return past.min(axis=0)


def main():
    with (HERE/'minimum_risk_holdouts.csv').open() as f:
        ref=list(csv.DictReader(f))
    with (HERE/'stopped_diagnostics.csv').open() as f:
        stopped=[stop_series(r) for r in csv.DictReader(f)]
    loaded=load_complete()
    complete=[loaded[r['case']] for r in ref]
    hybrid={r['case']:float(r['hybrid_m']) for r in ref}
    with (HERE/'stopped_diagnostics.csv').open() as f:
        hybrid.update({r['case']:float(r['hybrid_m']) for r in csv.DictReader(f)})
    rows=[]
    for cutoff in (30,60,90):
        for c in complete+stopped:
            if c['t'][-1]<cutoff:
                continue
            train=[z for z in complete if np.any(z['design'][:-1]!=c['design'][:-1])]
            station=prefix(c,cutoff)
            history=np.stack([prefix(z,cutoff) for z in train])
            loss=history.min(axis=1)-np.array([z['y'].min() for z in train])
            scale=np.maximum(history.std(axis=0),.01)
            distance=np.mean(((history-station)/scale)**2,axis=1)
            distance+=np.sum((np.array([z['design'] for z in train])-c['design'])**2,axis=1)
            weight=np.exp(-.5*(distance-distance.min()))
            obs=station.min()
            is_full=c['name'] in {r['case'] for r in ref}
            rows.append(dict(case=c['name'],source='complete' if is_full else 'stopped',
                             cutoff_s=cutoff,breach=int(c['y'].min()<LIMIT),
                             final_m=c['y'].min() if is_full else '',observed_m=obs,
                             bounded_m=min(obs,hybrid[c['name']]),
                             mean_loss_m=max(0,obs-loss.mean()),
                             local_loss_m=max(0,obs-np.average(loss,weights=weight))))
    save(HERE/'remaining_drop_holdouts.csv',rows)
    for cutoff in (30,60,90):
        s=[r for r in rows if r['cutoff_s']==cutoff]
        for key in ['observed_m','bounded_m','mean_loss_m','local_loss_m']:
            full=[r for r in s if r['source']=='complete']
            future=[r for r in s if r['observed_m']>=LIMIT and r['breach']]
            print(cutoff,key,'MAE(cm)',round(np.mean([abs(r[key]-r['final_m']) for r in full])*100,2),
                  'future hits',sum(r[key]<LIMIT for r in future),'/',len(future),
                  'false alarms',sum(r[key]<LIMIT and not r['breach'] for r in s))


if __name__=='__main__':
    main()
