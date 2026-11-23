"""Compare fixed residual heads using whole-layout folds and archived FDS outputs."""
import numpy as np
from margin_monitor import HERE, LIMIT, H, TIMES, basis, direction, save
from vent_geometry_ablation import EXTENDED, load


def features(case):
    return np.r_[case['raw'], case['extra']]


def physical_fit(train):
    gram = .1 * np.eye(EXTENDED.shape[1] + 1)
    physics = np.zeros_like(gram)
    rhs = 0.
    for case in train:
        phi, der = basis(case['t'], features(case), EXTENDED)
        res = (der + case['flow'] / (6.6 * .9 * H) * phi)[case['t'] >= 10]
        res -= res.mean(axis=0)
        gram += phi.T @ phi
        physics += res.T @ res
        rhs += phi.T @ (H - case['y'])
    weights = np.linalg.solve(gram, rhs)
    avg = np.linalg.solve(gram + 25 * physics, rhs @ direction)
    return weights + np.outer(avg - weights @ direction, direction)


def min_height(case, weights):
    phi, _ = basis(TIMES, features(case), EXTENDED)
    return np.clip(H - phi @ weights, 0, H).min()


def resnet(x, residual, test):
    # One trainable tanh block with an identity skip. Fixed settings in all folds.
    rng = np.random.default_rng(3322)
    a = rng.normal(0, .2, (x.shape[1], 8))
    b = rng.normal(0, .2, (8, 8))
    v = np.zeros(8)
    bias = residual.mean()
    for _ in range(800):
        h = np.tanh(x @ a)
        nonlinear = np.tanh(h @ b)
        z = h + nonlinear
        error = (z @ v + bias - residual) / len(x)
        grad = error[:, None] * v
        block = grad * (1 - nonlinear**2)
        da = x.T @ ((grad + block @ b.T) * (1 - h**2))
        a -= .03 * (da + .001 * a)
        b -= .03 * (h.T @ block + .001 * b)
        v -= .03 * (z.T @ error + .001 * v)
        bias -= .03 * error.sum()
    h = np.tanh(test @ a)
    return (h + np.tanh(h @ b)) @ v + bias


def kernel(x, y):
    return np.exp(-.5 * ((x[:, None] - y[None, :])**2).sum(axis=2))


def run():
    cases = list(load().values())
    rows = []
    for key in sorted({c['key'] for c in cases}):
        train = [c for c in cases if c['complete'] and c['key'] != key]
        test = [c for c in cases if c['key'] == key]
        weights = physical_fit(train)
        x, xt = [np.array([features(c) for c in group]) for group in (train, test)]
        residual = np.array([c['observed'] - min_height(c, weights) for c in train])
        gp = residual.mean() + kernel(xt, x) @ np.linalg.solve(
            kernel(x, x) + .25 * np.eye(len(x)), residual - residual.mean())
        nn = resnet(x, residual, xt)
        for c, g, n in zip(test, gp, nn):
            base = min_height(c, weights)
            rows.append(dict(case=c['name'], complete=int(c['complete']), observed=c['observed'],
                             gp=np.clip(base+g, 0, H), resnet=np.clip(base+n, 0, H)))
    save(HERE/'layout_residual_trials.csv', rows)
    for model in ('gp','resnet'):
        print(model, np.mean([abs(r['observed']-r[model]) for r in rows if r['complete']]),
              sum(r['observed']<LIMIT<=r[model] for r in rows),
              sum(r[model]<LIMIT<=r['observed'] for r in rows))


if __name__ == '__main__':
    run()
