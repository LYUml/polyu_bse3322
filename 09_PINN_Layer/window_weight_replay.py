"""Whole-design minimum replay with fourfold weights before training breaches."""
import csv

import numpy as np

from margin_monitor import H, HERE, LIMIT, load_complete, save
from minimum_risk import estimate


def weighted_case(case):
    times = case['t']
    mask = np.zeros(len(times), dtype=bool)
    for end in times[(case['y'] < LIMIT).any(axis=1)]:
        mask |= (times >= end - 2) & (times <= end)
    phi = case['phi'][mask]
    return dict(case, gram=case['gram'] + 3 * (phi.T @ phi),
                rhs=case['rhs'] + 3 * (phi.T @ (H - case['y'][mask])))


def main():
    with (HERE / 'minimum_risk_holdouts.csv').open() as source:
        archive = list(csv.DictReader(source))
    names = {row['case'] for row in archive}
    cases = load_complete(names)
    if set(cases) != names:
        raise ValueError('Incomplete FDS archive')
    weighted = {name: weighted_case(c) for name, c in cases.items()}
    results = []
    for row in archive:
        name = row['case']
        test = cases[name]
        train = [c for c in cases.values()
                 if not np.array_equal(c['design'][:-1], test['design'][:-1])]
        original = estimate(train, name)
        np.testing.assert_allclose(original, [float(row[k]) for k in
                                   ('pinn_m', 'direct_m', 'hybrid_m')], rtol=0, atol=1e-8)
        np.testing.assert_allclose(test['y'].min(), float(row['actual_m']))
        pinn, _, hybrid = estimate([weighted[c['name']] for c in train], name)
        results.append(dict(case=name, actual_m=row['actual_m'], original_pinn_m=original[0],
                            weighted_pinn_m=pinn, original_hybrid_m=original[2],
                            weighted_hybrid_m=hybrid))
    save(HERE / 'window_weight_holdouts.csv', results)


if __name__ == '__main__':
    main()
