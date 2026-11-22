"""Descriptive held-out operating curve; percentiles refer to training negatives."""
import numpy as np

from margin_monitor import HERE, X, save
from online_warning import evaluate, fit_warning
from temperature_warning import holdout_features


def main():
    percentiles = np.arange(99750, 99951) / 100000
    rows = [dict(quantile=q, false_alarms=0, retained=0, recovered=0, lost=0,
                 lead_sum_s=0.) for q in percentiles]
    events = [[] for _ in rows]
    baseline_false = 0
    for name, train, test in holdout_features():
        station, cutoff = fit_warning(train, 4)
        baseline = {}
        baseline_false += evaluate(test, station(test)>cutoff, baseline)['false_alarms']
        temperature, _ = fit_warning(train, 6)
        negatives = np.concatenate([temperature(c)[c['eligible'] & ~c['label']] for c in train])
        scores = temperature(test)
        for row, log, limit in zip(rows, events, np.quantile(negatives, percentiles)):
            leads = {}
            metrics = evaluate(test, scores>limit, leads)
            row['false_alarms'] += metrics['false_alarms']
            row['lead_sum_s'] += metrics['lead_sum_s']
            row['retained'] += len(baseline.keys() & leads.keys())
            row['lost'] += len(baseline.keys() - leads.keys())
            row['recovered'] += len(leads.keys() - baseline.keys())
            for j, station_events in enumerate(test['events']):
                for i, (start, _) in enumerate(station_events):
                    log.append(dict(quantile=row['quantile'], case=name, station_m=X[j],
                                    onset_s=start, baseline_lead_s=baseline.get((j,i),''),
                                    temperature_lead_s=leads.get((j,i),'')))
    save(HERE/'temperature_sweep_scores.csv', rows)
    # For tied false-alarm counts, archive every equally close quantile.
    distance = min(abs(r['false_alarms']-baseline_false) for r in rows)
    save(HERE/'temperature_sweep_events.csv',
         [e for r, log in zip(rows, events) if abs(r['false_alarms']-baseline_false)==distance
          for e in log])


if __name__ == '__main__':
    main()
