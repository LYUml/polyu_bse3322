"""Replay warnings whenever either device heights or thermal slices arrive."""
import csv

import numpy as np
from margin_monitor import LIMIT

from online_warning import H, HERE, HORIZON, evaluate, fit_warning, load_complete, samples, save
from thermal import layer_height, read_columns


def joint_samples(raw, device):
    times = device['t']
    frames, profile = read_columns(raw['name'], raw['directory'])
    clock = np.union1d(times, frames[(frames >= times[0]) & (frames <= times[-1])])
    i = np.searchsorted(times, clock, side='right') - 1
    j = np.searchsorted(frames, clock, side='right') - 1
    if min(i.min(), j.min()) < 0:
        raise ValueError('Missing initial sensor data')
    features = device['features'][i].copy()
    features[:, :, 4] = H - layer_height(profile)[j]
    features[:, :, 5] = np.log1p(np.maximum(0, profile[j, :, -1] - profile[j, :, 0]))
    eligible = device['eligible'][i] & (clock[:, None] <= times[-1] - HORIZON)
    labels = np.zeros_like(eligible)
    for station, events in enumerate(device['events']):
        for start, _ in events:
            labels[:, station] |= (clock < start) & (start <= clock + HORIZON)
    return dict(device, t=clock, features=features, eligible=eligible, label=labels)


def main():
    with (HERE / 'temperature_warning_scores.csv').open() as source:
        cohort = {r['case'] for r in csv.DictReader(source)}
    raw = load_complete()
    if not cohort <= raw.keys():
        raise ValueError('Missing original warning cohort')
    device = {n: samples(c) for n, c in raw.items()}
    joint = {n: joint_samples(c, device[n]) for n, c in raw.items()}
    contrast = {n: dict(c, features=c['features'][:, :, [0, 1, 2, 3, 5]])
                for n, c in joint.items()}
    rows = []
    for name, case in raw.items():
        train = [n for n in sorted(cohort)
                 if not np.array_equal(raw[n]['design'][:-1], case['design'][:-1])]
        hits = {}
        for method, data, size in [('station', device, 4), ('joint_descending', joint, 6),
                                   ('contrast_descending', contrast, 5),
                                   ('contrast_recovery', contrast, 5)]:
            score, cut = fit_warning([data[n] for n in train], size)
            test = data[name]
            alarms = score(test) > cut
            rearm = method == 'contrast_recovery'
            if method != 'station':
                gate = test['features'][:, :, 1] > 0
                if rearm:
                    below = test['features'][:, :, 0] > H - LIMIT
                    gate[1:] |= below[:-1] & ~below[1:]
                alarms &= gate
            leads = {}
            result = evaluate(test, alarms, leads, rearm_on_recovery=rearm)
            hits[method] = set(leads)
            rows.append(dict(case=name, cohort='original' if name in cohort else 'additional',
                             method=method, events=result['events'], hits=result['hits'],
                             false_alarms=result['false_alarms'], lead_sum_s=result['lead_sum_s'],
                             gained=len(set(leads) - hits['station']),
                             lost=len(hits['station'] - set(leads))))
    save(HERE / 'joint_time_scores.csv', rows)


if __name__ == '__main__':
    main()
