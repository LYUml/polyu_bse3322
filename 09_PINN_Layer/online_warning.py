"""Two-second causal warnings. All parameters and alarm cutoffs use training designs."""
import numpy as np

from margin_monitor import HERE, H, LIMIT, X, load_complete, save
from minimum_risk import nearest_designs
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


def fit_warning(train, nfeat, quantile=.999):
    x=np.concatenate([c['features'][c['eligible']][:,:nfeat] for c in train])
    y=np.concatenate([c['label'][c['eligible']] for c in train])
    if not y.any() or y.all():
        return lambda case: np.zeros_like(case['eligible'], dtype=float), np.inf
    mean=x.mean(axis=0)
    scale=np.maximum(x.std(axis=0),1e-6)
    z=(x-mean)/scale
    # Ridge linear discriminant for ranking alerts; the score is not a probability.
    w=np.linalg.solve(z.T@z+len(y)*.05*np.eye(nfeat),z.T@y.astype(float))
    cutoff=np.quantile((z@w)[~y],quantile)
    def score(case):
        return ((case['features'][:,:,:nfeat]-mean)/scale)@w
    return score, cutoff


def estimate(train, test, nfeat):
    score, cutoff = fit_warning(train, nfeat)
    return score(test) > cutoff


def evaluate(case, alarms, event_leads=None, *, rearm_on_recovery=False):
    hits=short_hits=false=count=short=0
    leads=[]
    lead_lower_bounds = []
    for j,events in enumerate(case['events']):
        count+=len(events)
        short+=sum(b-a<=2 for a,b in events)
        next_alarm=0.
        matched=set()
        candidates = case['eligible'][:,j] & alarms[:,j]
        if rearm_on_recovery:
            below = case['features'][:,j,0] > H-LIMIT
            recovered = np.r_[False, below[:-1] & ~below[1:]]
        else:
            recovered = np.zeros_like(candidates)
        for index in np.flatnonzero(candidates | recovered):
            now = case['t'][index]
            if recovered[index]:
                next_alarm = now
            if not candidates[index]:
                continue
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
                # Bound the crossing by its last at-or-above-limit sample.
                before = np.searchsorted(case['t'], a, side='right') - 1
                lead_lower_bounds.append(case['t'][before] - now)
                if event_leads is not None:
                    event_leads[j, hit] = a-now
                hits+=1
                short_hits+=int(b-a<=2)
    return dict(events=count,hits=hits,short_events=short,short_hits=short_hits,
                false_alarms=false,lead_sum_s=sum(leads),
                hits_at_least_half_second=sum(lead >= .5 for lead in leads),
                hits_at_least_one_second=sum(lead >= 1 for lead in leads),
                confirmed_half_second_hits=sum(lead >= .5 for lead in lead_lower_bounds),
                confirmed_one_second_hits=sum(lead >= 1 for lead in lead_lower_bounds))


def first_event_training(case):
    events = [(start, station) for station, intervals in enumerate(case['events'])
              for start, _ in intervals]
    start, station = min(events, default=(np.inf, 0))
    times = case['t']
    label = np.zeros_like(case['label'])
    label[:, station] = (times < start) & (times + HORIZON >= start)
    return dict(case, eligible=case['eligible'] & (times[:, None] < start), label=label)


def main():
    complete = load_complete()
    minima = {}
    for case in complete.values():
        minima.setdefault(tuple(case['design'][:-1]), []).append(case['y'].min())
    cases={name:samples(c) for name,c in complete.items()}
    rows=[]
    for name,test in cases.items():
        train=[c for c in cases.values() if not np.array_equal(c['design'][:-1],test['design'][:-1])]
        negatives=np.concatenate([c['trend_score'][c['eligible'] & ~c['label']] for c in train])
        methods={'persistence':np.zeros_like(test['eligible']),'trend':test['trend_score']>0,
                 'trend_calibrated':test['trend_score']>np.quantile(negatives,.999),
                 'height_features':estimate(train,test,4),'height_and_temperature':estimate(train,test,6)}
        for method,alarm in methods.items():
            rows.append(dict(case=name,method=method,**evaluate(test,alarm)))
        rows.append(dict(case=name, method='temperature_rearm_on_recovery',
                         **evaluate(test, methods['height_and_temperature'], rearm_on_recovery=True)))
        neighbors = nearest_designs(minima, tuple(test['design'][:-1]))
        alarms = np.zeros_like(test['eligible'])
        screen_positive = np.mean([np.mean(minima[g]) for g in neighbors]) < LIMIT
        if screen_positive:
            score, cutoff = fit_warning(train, 6, quantile=.9985)
            alarms = score(test) > cutoff
        rows.append(dict(case=name, method='nearest_temperature_rearm',
                         **evaluate(test, alarms, rearm_on_recovery=True)))
        times = test['t']
        heights = complete[name]['y']
        lowest_station = np.zeros_like(alarms)
        for end, start in enumerate(np.searchsorted(times, times - HORIZON)):
            # Ties go to the first station in the existing station order.
            station = np.argmin(heights[start:end + 1].min(axis=0))
            lowest_station[end, station] = True
        first_station_alarms = lowest_station & alarms
        rows.append(dict(case=name, method='nearest_temperature_rearm_lowest_station',
                         **evaluate(test, first_station_alarms, rearm_on_recovery=True)))
        fallback_alarms = first_station_alarms
        if not screen_positive:
            dt = np.r_[0, np.diff(times)][:, None]
            speed = test['features'][:, :, 1]
            prior_speed = np.vstack([np.zeros_like(speed[:1]), speed[:-1]])
            fallback_alarms = (lowest_station & (heights <= .50) & (prior_speed > 0)
                               & (heights - dt * speed < LIMIT))
        rows.append(dict(case=name, method='lowest_station_descent_fallback',
                         **evaluate(test, fallback_alarms, rearm_on_recovery=True)))
        staged = fallback_alarms.copy()
        if screen_positive:
            first_score, _ = fit_warning([first_event_training(c) for c in train], 6)
            negative_scores = np.concatenate([
                first_score(c)[c['eligible'] & ~c['label']] for c in train])
            # Fixed after retrospective comparison on the original 27 runs.
            first_cutoff = np.quantile(negative_scores, .99915)
            before_breach = ~np.logical_or.accumulate((heights < LIMIT).any(axis=1))
            staged[before_breach] = (lowest_station & (first_score(test) > first_cutoff))[before_breach]
        rows.append(dict(case=name, method='staged_first_breach',
                         **evaluate(test, staged, rearm_on_recovery=True)))
        agree = staged & fallback_alarms
        either = staged | fallback_alarms
        projected_breach = test['trend_score'] > 0
        confirmed = agree | (either & projected_breach)
        rows.append(dict(case=name, method='staged_union_trend_confirmation',
                         **evaluate(test, confirmed, rearm_on_recovery=True)))
        # Retrospective candidate for the 6.1 m station, using its 4.9 m neighbor.
        neighbor_at_ceiling = heights[:, -2] == H
        filtered = confirmed.copy()
        filtered[1:, -1] &= ~(neighbor_at_ceiling[:-1] & neighbor_at_ceiling[1:])
        rows.append(dict(case=name, method='downstream_neighbor_ceiling',
                         **evaluate(test, filtered, rearm_on_recovery=True)))
    save(HERE/'online_warning_scores.csv',rows)
    for method in dict.fromkeys(r['method'] for r in rows):
        subset=[r for r in rows if r['method']==method]
        print(method,{k:sum(r[k] for r in subset) for k in ['events','hits','short_events','short_hits','false_alarms','lead_sum_s']})


if __name__=='__main__':
    main()
