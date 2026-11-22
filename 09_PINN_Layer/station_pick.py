"""One station per method, with the next first threshold crossing as the target."""
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
import sys

import numpy as np
from margin_monitor import HERE, ROOT, X, LIMIT, load_complete, design, save
from station_drop import predict, prefix

NAME='inlet48_6_0p02_0p24_1p12_z38_120'
PLAN=HERE/'station_watch_plan.json'


def pick(minima):
    # Stations are in ascending x; the smaller coordinate wins exact ties.
    return float(X[np.argmin(minima)])


def replay():
    grouped=defaultdict(list)
    with (HERE/'station_drop_holdouts.csv').open() as f:
        for r in csv.DictReader(f):
            grouped[r['case'],int(r['cutoff_s'])].append(r)
    out=[]
    for (name,cut),rows in grouped.items():
        rows.sort(key=lambda r:float(r['x_m']))
        obs=[float(r['observed_min_m']) for r in rows]
        if min(obs)<LIMIT:
            continue
        hits=[(float(r['first_breach_s']),float(r['x_m'])) for r in rows if r['first_breach_s']]
        if hits and min(hits)[0]<=cut:
            raise ValueError(name)
        first=min(hits)[0] if hits else None
        stations=[x for t,x in hits if t==first]
        out.append(dict(case=name,cutoff_s=cut,observed_pick_m=pick(obs),
                        model_pick_m=pick([float(r['predicted_min_m']) for r in rows]),
                        next_breach_s=first or '',next_stations_m='|'.join(map(str,stations)),
                        observed_hit=int(pick(obs) in stations) if hits else '',
                        model_hit=int(pick([float(r['predicted_min_m']) for r in rows]) in stations) if hits else ''))
    save(HERE/'station_pick_holdouts.csv',out)
    for cut in (30,60,90):
        rr=[r for r in out if r['cutoff_s']==cut and r['next_breach_s']]
        print(cut,len(rr),sum(r['observed_hit'] for r in rr),sum(r['model_hit'] for r in rr))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(path,data):
    # Single heartbeat/writer, exclusive creation; archived predictions never change.
    with path.open('x',encoding='utf-8') as f:
        json.dump(data,f,indent=2,allow_nan=False)
        f.write('\n')


def live():
    directory=ROOT/'04_Results'/NAME
    deck=directory/(NAME+'.fds')
    code={f:digest(HERE/f) for f in ('station_pick.py','station_drop.py','remaining_drop.py','margin_monitor.py','run.py')}
    if not PLAN.exists():
        known=load_complete()
        once(PLAN,dict(case=NAME,created_utc=datetime.now(timezone.utc).isoformat(),
                       prospective_cutoffs_s=[60,90],illustrative_cutoff_s=30,deck=digest(deck),
                       code=code,train={n:c['digest'] for n,c in known.items()
                                    if np.any(c['design'][:-1]!=design(NAME)[:-1])}))
    plan=json.loads(PLAN.read_text())
    if plan['code']!=code or plan['deck']!=digest(deck):
        raise ValueError('Registered code or inputs changed; inspect before using')
    train=load_complete(set(plan['train']))
    if {n:c['digest'] for n,c in train.items()}!=plan['train']:
        raise ValueError('Registered training set changed')
    for cut in [plan['illustrative_cutoff_s'],*plan['prospective_cutoffs_s']]:
        path=HERE/f'station_pick_live_{cut}.json'
        if path.exists():
            continue
        data=[]
        with (directory/(NAME+'_devc.csv')).open() as f:
            reader=csv.reader(f)
            units,header=next(reader),next(reader)
            cols=[header.index(f'layer{x:g}') for x in X]
            if units[0]!='s' or any(units[j]!='m' for j in cols):
                raise ValueError('Bad device units')
            for row in reader:
                if not row or len(row)!=len(header):
                    break
                t=float(row[0])
                if t>cut:
                    break
                data.append([t,*[float(row[j]) for j in cols]])
            else:
                break  # there has not yet been a sample beyond the landmark
            if not row or len(row)!=len(header) or t<=cut:
                break
        data=np.array(data)
        ts,h=data[:,0],data[:,1:]
        if ts[0]!=0 or cut-ts[-1]>.75 or not np.all((np.diff(ts)>0)&(np.diff(ts)<.75)) or not np.all((0<=h)&(h<=.76)):
            raise ValueError('Incomplete device prefix')
        c=dict(y=h,t=ts,design=design(NAME))
        obs=prefix(c,cut)
        pred=predict(list(train.values()),c,cut)
        result=dict(case=NAME,cutoff_s=cut,recorded_utc=datetime.now(timezone.utc).isoformat(),
                    already_breached=bool(min(obs)<LIMIT),observed_pick_m=pick(obs),
                    model_pick_m=pick(pred),observed_min_m=list(obs),predicted_min_m=list(pred))
        once(path,result)
        print(result['cutoff_s'],result['observed_pick_m'],result['model_pick_m'],result['already_breached'])


if __name__=='__main__':
    if '--live' in sys.argv:
        live()
    else:
        replay()
