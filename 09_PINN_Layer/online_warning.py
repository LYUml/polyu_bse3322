"""Two-second causal warnings. All parameters and alarm cutoffs use training designs."""
import numpy as np

from margin_monitor import HERE, H, LIMIT, X, load_complete, save
from run import intervals
from thermal import read_columns, layer_height

HORIZON = 2.


def samples(case):
    t, h = case['t'], case['y']
    ts, temp = read_columns(case['name'], case['directory'])
    # Most recent available slice, never the nearest future slice.
    latest = np.searchsorted(ts, t, side='right')-1
    if latest.min()<0:
        raise ValueError('Missing initial temperature')
    hz = layer_height(temp)[latest]
    top = temp[:,:,-1][latest]
    bottom = temp[:,:,0][latest]
    prev = np.maximum(0,np.arange(len(t))-1)
    step = (h-h[prev])/np.maximum((t-t[prev])[:,None],.01)
    past = np.maximum(0,np.searchsorted(t,t-2,side='right')-1)
    features = np.stack([H-h, -step, h[past]-h, np.broadcast_to(abs(X-3.3),h.shape),
                         H-hz, np.log1p(np.maximum(0,top-bottom))],axis=-1)
    events = [intervals(t,series) for series in h.T]
    label = np.zeros(h.shape,dtype=bool)
    for j,station in enumerate(events):
        for start,_ in station:
            label[:,j] |= (t<start)&(start<=t+HORIZON)
    eligible = (h>=LIMIT)&(t[:,None]<=t[-1]-HORIZON)
    return dict(t=t,features=features,eligible=eligible,label=label,events=events,
                design=case['design'],trend_score=LIMIT-h-HORIZON*step)


def estimate(train, test, nfeat):
    x=np.concatenate([c['features'][c['eligible']][:,:nfeat] for c in train])
    y=np.concatenate([c['label'][c['eligible']] for c in train])
    if not y.any() or y.all():
        return np.zeros_like(test['eligible'])
    mean=x.mean(axis=0)
    scale=np.maximum(x.std(axis=0),1e-6)
    z=(x-mean)/scale
    # Ridge linear discriminant for ranking alerts; the score is not a probability.
    w=np.linalg.solve(z.T@z+len(y)*.05*np.eye(nfeat),z.T@y.astype(float))
    cutoff=np.quantile((z@w)[~y],.999)
    return ((test['features'][:,:,:nfeat]-mean)/scale)@w > cutoff


def evaluate(case, alarms, event_leads=None):
    hits=short_hits=false=count=short=0
    leads=[]
    for j,events in enumerate(case['events']):
        count+=len(events)
        short+=sum(b-a<=2 for a,b in events)
        next_alarm=0.
        matched=set()
        for now in case['t'][case['eligible'][:,j]&alarms[:,j]]:
            if now<next_alarm:
                continue
            next_alarm=now+HORIZON
            hit=next((i for i,(a,b) in enumerate(events)
                      if i not in matched and now<a<=now+HORIZON),None)
            if hit is None:
                false+=1
            else:
                matched.add(hit)
                a,b=events[hit]
                leads.append(a-now)
                if event_leads is not None:
                    event_leads[j, hit] = a-now
                hits+=1
                short_hits+=int(b-a<=2)
    return dict(events=count,hits=hits,short_events=short,short_hits=short_hits,
                false_alarms=false,lead_sum_s=sum(leads))


def main():
    cases={name:samples(c) for name,c in load_complete().items()}
    rows=[]
    for name,test in cases.items():
        train=[c for c in cases.values() if not np.array_equal(c['design'][:-1],test['design'][:-1])]
        negatives=np.concatenate([c['trend_score'][c['eligible'] & ~c['label']] for c in train])
        methods={'persistence':np.zeros_like(test['eligible']),'trend':test['trend_score']>0,
                 'trend_calibrated':test['trend_score']>np.quantile(negatives,.999),
                 'height_features':estimate(train,test,4),'height_and_temperature':estimate(train,test,6)}
        for method,alarm in methods.items():
            rows.append(dict(case=name,method=method,**evaluate(test,alarm)))
    save(HERE/'online_warning_scores.csv',rows)
    for method in methods:
        subset=[r for r in rows if r['method']==method]
        print(method,{k:sum(r[k] for r in subset) for k in ['events','hits','short_events','short_hits','false_alarms','lead_sum_s']})


if __name__=='__main__':
    main()
