"""Paired replay of the descending-only gate on the archived warning cohort."""
import csv

import numpy as np

from online_warning import H, HERE, LIMIT, X, estimate, evaluate, load_complete, samples, save


def main():
    with (HERE / 'neighbor_warning_scores.csv').open() as source:
        baseline = {r['case']: r for r in csv.DictReader(source) if r['method'] == 'station'}
    cases = {name: samples(raw) for name, raw in load_complete(set(baseline)).items()}
    if cases.keys() != baseline.keys():
        raise ValueError('Missing archived warning cases')
    rows = []
    event_rows = []
    for name, case in sorted(cases.items()):
        train = [other for other in cases.values()
                 if not np.array_equal(other['design'][:-1], case['design'][:-1])]
        alarms = estimate(train, case, 4)
        original, gated = {}, {}
        ref = evaluate(case, alarms, original)
        for key in ('events', 'hits', 'false_alarms'):
            if ref[key] != int(baseline[name][key]):
                raise ValueError(f'Archived baseline mismatch: {name} {key}')
        descending = case['features'][:, :, 1] > 0
        result = evaluate(case, alarms & descending, gated)
        below = case['features'][:, :, 0] > H - LIMIT
        recovery = np.zeros_like(below)
        recovery[1:] = below[:-1] & ~below[1:]
        leads = {}
        candidate = evaluate(case, alarms & (descending | recovery), leads,
                             rearm_on_recovery=True)
        for j, events in enumerate(case['events']):
            for i, (start, end) in enumerate(events):
                event_rows.append(dict(case=name, station_m=X[j], onset_s=start, end_s=end,
                                       baseline_lead_s=original.get((j, i), ''),
                                       recovery_gate_lead_s=leads.get((j, i), '')))
        rows.append(dict(case=name, events=ref['events'], original_hits=ref['hits'],
                         retained=len(original.keys() & gated.keys()),
                         recovered=len(gated.keys() - original.keys()),
                         original_false=ref['false_alarms'], gated_false=result['false_alarms'],
                         gated_lead_sum_s=result['lead_sum_s'],
                         recovery_gate_hits=candidate['hits'],
                         recovery_gate_false=candidate['false_alarms']))
    save(HERE / 'descending_warning_scores.csv', rows)
    save(HERE / 'descending_warning_events.csv', event_rows)


if __name__ == '__main__':
    main()
