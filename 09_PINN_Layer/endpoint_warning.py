"""Explore a separate descent-rate coefficient at the two end stations."""
import csv

import numpy as np

from margin_monitor import HERE, X, load_complete, save
from online_warning import estimate, evaluate, samples


def main():
    with (HERE/'neighbor_warning_scores.csv').open() as f:
        names = {r['case'] for r in csv.DictReader(f)}
    complete = load_complete(names)
    if set(complete) != names:
        raise ValueError('Incomplete warning cohort')
    cases = {}
    for name, raw in complete.items():
        case = samples(raw)
        local = case['features'][:, :, :4]
        end_rate = local[:, :, 1] * np.isin(X, [X[0], X[-1]])
        case['features'] = np.dstack((local, end_rate))
        cases[name] = case
    rows, differences, routed_rows = [], [], []
    for name, test in cases.items():
        train = [c for c in cases.values() if not np.array_equal(c['design'][:-1], test['design'][:-1])]
        baseline, candidate = {}, {}
        local_alarm = estimate(train, test, 4)
        end_alarm = estimate(train, test, 5)
        base = evaluate(test, local_alarm, baseline)
        result = evaluate(test, end_alarm, candidate)
        for station, event in sorted(baseline.keys() ^ candidate.keys()):
            key = station, event
            onset = test['events'][station][event][0]
            lead = candidate[key] if key in candidate else baseline[key]
            frame = np.argmin(abs(test['t']-(onset-lead)))
            np.testing.assert_allclose(test['t'][frame], onset-lead, atol=1e-8, rtol=0)
            differences.append(dict(case=name, station_m=X[station], onset_s=onset,
                                    change='recovered' if key in candidate else 'lost',
                                    lead_s=lead, height_m=complete[name]['y'][frame, station],
                                    recent_drop_m_s=test['features'][frame, station, 1],
                                    past_drop_m=test['features'][frame, station, 2]))
        routed = {}
        routed_metrics = evaluate(test, np.where(np.isin(X, [X[0], X[-1]]), end_alarm, local_alarm), routed)
        routed_rows.append(dict(case=name, recovered=len(routed.keys()-baseline.keys()),
                                lost=len(baseline.keys()-routed.keys()), **routed_metrics))
        rows.append(dict(case=name, events=result['events'], recovered=len(candidate.keys()-baseline.keys()),
                         lost=len(baseline.keys()-candidate.keys()), hits=result['hits'],
                         baseline_false=base['false_alarms'], false_alarms=result['false_alarms'],
                         lead_sum_s=result['lead_sum_s']))
    save(HERE/'endpoint_warning_scores.csv', rows)
    if differences:
        save(HERE/'endpoint_warning_changes.csv', differences)
    save(HERE/'endpoint_routed_scores.csv', routed_rows)
    print({key:sum(r[key] for r in rows) for key in rows[0] if key!='case'})


if __name__ == '__main__':
    main()
