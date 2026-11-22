"""Score frozen station selections after the 1.12 m3/s FDS run terminates."""
import csv
import json
import subprocess
from datetime import datetime

import numpy as np

from station_pick import HERE, ROOT, NAME, X, LIMIT, PLAN, digest


def evaluate():
    directory=ROOT/'04_Results'/NAME
    plan=json.loads(PLAN.read_text())
    if digest(directory/(NAME+'.fds'))!=plan['deck']:
        raise ValueError('Deck differs from preregistered input')
    log=(directory/(NAME+'.out')).read_text(errors='replace')[-4096:]
    full=f'STOP: FDS completed successfully (CHID: {NAME})' in log
    stopped=f'STOP: FDS stopped by user (CHID: {NAME})' in log
    if not (full or stopped):
        raise ValueError('No confirmed terminal status')
    if full:
        subprocess.run(['node',str(ROOT/'06_Tools/summarize_design.cjs'),str(directory)],
                       check=True,capture_output=True)
    with (directory/(NAME+'_devc.csv')).open() as f:
        units=next(csv.reader(f))
        reader=csv.DictReader(f)
        names=[f'layer{x:g}' for x in X]
        if units[0]!='s' or any(units[reader.fieldnames.index(n)]!='m' for n in names):
            raise ValueError('Unexpected units')
        data=np.array([[float(r['Time']),*[float(r[n]) for n in names]] for r in reader])
    t,h=data[:,0],data[:,1:]
    if t[0]!=0 or not np.all((np.diff(t)>0)&(np.diff(t)<.75)) or not np.all((h>=0)&(h<=.76)):
        raise ValueError('Invalid time series')
    with (directory/(NAME+'_steps.csv')).open() as f:
        next(f)
        steps=[(float(r['Simulation Time']),datetime.fromisoformat(r['Wall Time'].strip()))
               for r in csv.DictReader(f)]
    hits=np.flatnonzero(h.min(axis=1)<LIMIT)
    first=int(hits[0]) if hits.size else None
    idx,j=np.unravel_index(h.argmin(),h.shape)
    out=dict(case=NAME,complete=full,observed_to_s=t[-1],observed_min_m=h[idx,j],
             min_time_s=t[idx],min_station_m=X[j],first_time_s=None if first is None else t[first],
             first_stations_m=[] if first is None else list(X[h[first]<LIMIT]),landmarks=[])
    for cut in plan['prospective_cutoffs_s']:
        p=HERE/f'station_pick_live_{cut}.json'
        if not p.exists():
            if t[-1]>cut:
                raise ValueError(f'Missing forecast for {cut} s')
            out['landmarks'].append(dict(cutoff_s=cut,status='not reached'))
            continue
        r=json.loads(p.read_text())
        obs=h[t<=cut].min(axis=0)
        np.testing.assert_allclose(obs,r['observed_min_m'],rtol=0,atol=1e-8)
        if r['already_breached']!=bool(obs.min()<LIMIT):
            raise ValueError('Inconsistent prefix status')
        stamp=datetime.fromisoformat(r['recorded_utc'])
        # A step timestamp before/after the first breach brackets its wall-clock time.
        before=None
        if first is not None:
            earlier=[w for s,w in steps if s<t[first]]
            later=[w for s,w in steps if s>=t[first]]
            if earlier and stamp<=max(earlier):
                before=True
            elif later and stamp>=min(later):
                before=False
        eligible=not r['already_breached'] and first is not None
        alarm=min(r['predicted_min_m'])<LIMIT
        out['landmarks'].append(dict(cutoff_s=cut,recorded_utc=r['recorded_utc'],
            already_breached=r['already_breached'],frozen_before_first_breach=before,
            observed_pick_m=r['observed_pick_m'],model_pick_m=r['model_pick_m'],
            predicted_min_m=min(r['predicted_min_m']),alarm=alarm,
            observed_pick_hit=r['observed_pick_m'] in out['first_stations_m'] if eligible else None,
            model_pick_hit=r['model_pick_m'] in out['first_stations_m'] if eligible else None,
            missed_breach=not alarm if eligible else None,
            false_alarm=alarm if full and first is None else None))
    return out


if __name__=='__main__':
    print(json.dumps(evaluate(),indent=2,allow_nan=False))
