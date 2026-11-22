"""Replay two-second warnings on the original neighbor-warning cohort."""
import csv

import numpy as np

from margin_monitor import HERE, X, load_complete, save
from online_warning import evaluate, fit_warning, samples
from thermal import read_columns


def with_modes(case, center, axes):
    modes = (case['ceiling'] - center) @ axes.T
    station_modes = np.broadcast_to(modes[:, None, :], (*case['eligible'].shape, 2))
    features = np.concatenate((case['features'][:, :, :4], station_modes), axis=2)
    return dict(case, features=features)


def holdout_features():
    with (HERE/'neighbor_warning_scores.csv').open() as f:
        names = {r['case'] for r in csv.DictReader(f) if r['method'] == 'station'}
    complete = load_complete(names)
    if names != set(complete):
        raise ValueError('Missing completed reference case')
    cases = {}
    for name, raw in complete.items():
        case = samples(raw)
        ts, temp = read_columns(name, raw['directory'])
        latest = np.searchsorted(ts, case['t'], side='right') - 1
        if latest.min() < 0 or np.any(ts[latest] > case['t']):
            raise ValueError('Unavailable temperature frame')
        case['ceiling'] = temp[latest, :, -1]
        cases[name] = case

    for name, test in cases.items():
        train = [case for case in cases.values()
                 if not np.array_equal(case['design'][:-1], test['design'][:-1])]
        ceiling = np.concatenate([case['ceiling'] for case in train])
        center = ceiling.mean(axis=0)
        _, _, axes = np.linalg.svd(ceiling-center, full_matrices=False)
        training_features = [with_modes(case, center, axes[:2]) for case in train]
        test_features = with_modes(test, center, axes[:2])
        yield name, training_features, test_features


def main():
    scores, events = [], []
    for name, training_features, test_features in holdout_features():
        test = test_features
        leads = {}
        station_score, station_cut = fit_warning(training_features, 4)
        temp_score, temp_cut = fit_warning(training_features, 6)
        target = sum(evaluate(c, station_score(c)>station_cut)['false_alarms']
                     for c in training_features)
        ranked = [temp_score(c) for c in training_features]
        negatives = np.concatenate([s[c['eligible'] & ~c['label']]
                                    for c, s in zip(training_features, ranked)])
        def budget_error(cut):
            false = sum(evaluate(c, s>cut)['false_alarms']
                        for c, s in zip(training_features, ranked))
            return abs(false-target), abs(cut-temp_cut)
        thresholds = np.quantile(negatives, np.linspace(.998, .9998, 37))
        matched = min(thresholds, key=budget_error)
        for method, score, cutoff in [('station', station_score, station_cut),
                                      ('temperature', temp_score, temp_cut),
                                      ('budget', temp_score, matched)]:
            leads[method] = {}
            alarms = score(test_features) > cutoff
            metrics = evaluate(test, alarms, leads[method])
            scores.append(dict(case=name, method=method, **metrics))
        for j, station_events in enumerate(test['events']):
            for i, (start, end) in enumerate(station_events):
                events.append(dict(case=name, station_m=X[j], onset_s=start, duration_s=end-start,
                                   station_lead_s=leads['station'].get((j, i), ''),
                                   temperature_lead_s=leads['temperature'].get((j, i), ''),
                                   budget_lead_s=leads['budget'].get((j, i), '')))
    save(HERE/'temperature_warning_scores.csv', scores)
    save(HERE/'temperature_warning_events.csv', events)


if __name__ == '__main__':
    main()
