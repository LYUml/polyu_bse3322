"""Replay a two-second linear extrapolation with a training-only alarm budget."""
import numpy as np

from margin_monitor import HERE, X, save
from online_warning import evaluate, fit_warning
from temperature_warning import holdout_features


def trend_cutoff(train, target):
    negatives = np.concatenate([
        case['trend_score'][case['eligible'] & ~case['label']] for case in train
    ])
    candidates = np.quantile(negatives, np.linspace(.998, .9998, 37))

    def budget_error(cut):
        false = sum(evaluate(c, c['trend_score'] > cut)['false_alarms'] for c in train)
        return abs(false - target), -cut

    return min(candidates, key=budget_error)


def main():
    scores, events = [], []
    for name, train, test in holdout_features():
        baseline, cut = fit_warning(train, 4)
        target = sum(evaluate(c, baseline(c) > cut)['false_alarms'] for c in train)
        limit = trend_cutoff(train, target)
        old, new = {}, {}
        for method, alarms, leads in [('station', baseline(test) > cut, old),
                                      ('trend', test['trend_score'] > limit, new)]:
            scores.append(dict(case=name, method=method, **evaluate(test, alarms, leads)))
        for j, series in enumerate(test['events']):
            for i, (start, end) in enumerate(series):
                events.append(dict(case=name, station_m=X[j], onset_s=start, end_s=end,
                                   station_lead_s=old.get((j, i), ''),
                                   trend_lead_s=new.get((j, i), '')))
    save(HERE / 'trend_budget_scores.csv', scores)
    save(HERE / 'trend_budget_events.csv', events)


if __name__ == '__main__':
    main()
