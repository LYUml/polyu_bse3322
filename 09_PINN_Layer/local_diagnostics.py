"""Local-column diagnostic and design-only shrinkage with a stopped-run challenge."""
import csv
import json
import numpy as np

from minimum_risk import estimate
from three_zone import HERE, LIMIT, decode, design, load_complete, observed, save, signals
from margin_monitor import PATTERN
from thermal import layer_height, read_columns
from run import X, ROOT, H


def geometry_average(coords, name, targets):
    # Prefer matching end openings. Use all equally close geometries for ties.
    distances = ((coords[:,:2]-design(name)[:2])**2).sum(axis=1)
    return targets[np.isclose(distances, distances.min())].mean()


def diagnostic(x, summaries, target, mask, i):
    mu=summaries[mask].mean(axis=0)
    scale=np.maximum(summaries[mask].std(axis=0),1e-8)*np.sqrt(len(mu))
    return np.clip(decode(np.column_stack((x[mask],(summaries[mask]-mu)/scale)),
                          np.r_[x[i],(summaries[i]-mu)/scale],target[mask]),0,H).min()


def main():
    with (HERE/'minimum_risk_holdouts.csv').open() as f:
        ref=list(csv.DictReader(f))
    loaded=load_complete()
    cases=[loaded[r['case']] for r in ref]
    names=[c['name'] for c in cases]
    coords=np.array([c['design'] for c in cases])
    target=np.array([c['y'].min(axis=0) for c in cases])
    zones=np.array([signals(observed(c)[1]) for c in cases])
    local=[]
    for c in cases:
        t,temp=read_columns(c['name'],c['directory'])
        z=layer_height(temp)
        local.append(np.r_[z.min(axis=0),np.quantile(z,.05,axis=0)])
    local=np.array(local)
    rows=[]
    for i,name in enumerate(names):
        mask=np.any(coords[:,:-1]!=coords[i,:-1],axis=1)
        hybrid=float(ref[i]['hybrid_m'])
        geometry=geometry_average(coords[mask],name,target[mask].min(axis=1))
        rows.append(dict(case=name,actual_m=target[i].min(),hybrid_m=hybrid,
                         geometry_m=geometry,shrink_m=(geometry+hybrid)/2,
                         measured_zones_m=diagnostic(coords,zones,target,mask,i),
                         zones_columns_m=diagnostic(coords,np.column_stack((zones,local)),target,mask,i),
                         column_readout_m=local[i,:len(X)].min()))
    save(HERE/'local_diagnostics.csv',rows)
    for k in list(rows[0])[2:]:
        a,p=np.array([[r['actual_m'],r[k]] for r in rows]).T
        print(k,round(100*np.abs(a-p).mean(),2),sum((a<LIMIT)&(p>=LIMIT)),sum((a>=LIMIT)&(p<LIMIT)))
    stopped=[]
    for path in sorted((ROOT/'05_Calculations').glob('*_screen_failure.json')):
        r=json.loads(path.read_text(encoding='utf-8-sig'))
        name=r['chid']
        if not PATTERN.fullmatch(name) or name in loaded or r['status']!='screen_failed':
            continue
        if not (0<float(r['observed_to_s'])<120 and 0<=float(r['observed_min_m'])<LIMIT):
            continue
        mask=np.any(coords[:,:-1]!=design(name)[:-1],axis=1)
        train=[c for c,keep in zip(cases,mask) if keep]
        hybrid=estimate(train,name)[2]
        geom=geometry_average(coords[mask],name,target[mask].min(axis=1))
        stopped.append(dict(case=name,observed_upper_m=r['observed_min_m'],observed_to_s=r['observed_to_s'],
                            hybrid_m=hybrid,geometry_m=geom,shrink_m=(geom+hybrid)/2))
    if stopped:
        save(HERE/'stopped_diagnostics.csv',stopped)
        print('stopped',len(stopped),{k:sum(r[k]>=LIMIT for r in stopped) for k in ('hybrid_m','geometry_m','shrink_m')})


if __name__=='__main__':
    main()
