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
    rows = []
    for name, test in cases.items():
        train = [c for c in cases.values() if not np.array_equal(c['design'][:-1], test['design'][:-1])]
        baseline, candidate = {}, {}
        base = evaluate(test, estimate(train, test, 4), baseline)
        result = evaluate(test, estimate(train, test, 5), candidate)
        rows.append(dict(case=name, events=result['events'], recovered=len(candidate.keys()-baseline.keys()),
                         lost=len(baseline.keys()-candidate.keys()), hits=result['hits'],
                         baseline_false=base['false_alarms'], false_alarms=result['false_alarms'],
                         lead_sum_s=result['lead_sum_s']))
    save(HERE/'endpoint_warning_scores.csv', rows)
    print({key:sum(r[key] for r in rows) for key in rows[0] if key!='case'})


if __name__ == '__main__':
    main()
