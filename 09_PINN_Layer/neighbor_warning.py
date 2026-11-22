"""Paired two-second warning replay with left/right station histories."""
import numpy as np

from margin_monitor import HERE, X, load_complete, save
from online_warning import samples, estimate, evaluate


def features(case):
    t, h = case['t'], case['y']
    result = samples(case)
    columns = [result['features'][:, :, :4]]
    for lag in (1., 2.):
        # Interpolate the past level at the exact lag on the irregular device clock.
        past = np.column_stack([np.interp(t-lag, t, column) for column in h.T])
        drop = past-h
        left, right = np.zeros_like(drop), np.zeros_like(drop)
        left[:, 1:] = drop[:, :-1]
        right[:, :-1] = drop[:, 1:]
        columns.extend([left[:, :, None], right[:, :, None]])
    result['features'] = np.concatenate(columns, axis=2)
    return result


def main():
    cases = {name: features(case) for name, case in load_complete().items()}
    scores, events = [], []
    for name, test in cases.items():
        train = [case for case in cases.values()
                 if not np.array_equal(case['design'][:-1], test['design'][:-1])]
        by_method = {}
        for method, count in [('station', 4), ('neighbors', 8)]:
            leads = {}
            summary = evaluate(test, estimate(train, test, count), leads)
            scores.append(dict(case=name, method=method, **summary))
            by_method[method] = leads
        for j, station_events in enumerate(test['events']):
            for i, (start, end) in enumerate(station_events):
                events.append(dict(case=name, station_m=X[j], onset_s=start, duration_s=end-start,
                                   station_lead_s=by_method['station'].get((j, i), ''),
                                   neighbors_lead_s=by_method['neighbors'].get((j, i), '')))
    save(HERE/'neighbor_warning_scores.csv', scores)
    if events:
        save(HERE/'neighbor_warning_events.csv', events)


if __name__ == '__main__':
    main()
