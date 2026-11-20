"""Blind replay on the completed 4x4 OP-6 screening grid; CSV trace to stdout."""
import csv
import io
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GRID = [(d, q) for d in range(4) for q in range(1, 5)]
INITIAL = [(0, 1), (0, 4), (3, 1), (3, 4)]


def read_fds():
    margins = {}
    for d, q in GRID:
        depth, flow = (f"{i * 0.08:g}".replace(".", "p") for i in (d, q))
        directory = ROOT / "04_Results" / f"design_6_0p02_{depth}_{flow}_120"
        command = ["node", str(ROOT / "06_Tools/summarize_design.cjs"), str(directory)]
        data = subprocess.check_output(command, text=True)
        rows = list(csv.DictReader(io.StringIO(data)))
        if len(rows) != 8 or any(
            r["case"] != directory.name or float(r["start_s"]) != 0 or float(r["end_s"]) != 120
            for r in rows
        ):
            raise ValueError(f"Incomplete scenario: {directory}")
        margins[d, q] = min(float(r["min_height_m"]) for r in rows) - 0.38
    return margins


def predict(observed, candidates):
    # Fixed one-grid-step RBF length; normalize outputs using queried points only.
    x = np.asarray(list(observed))
    y = np.asarray(list(observed.values()))
    points = np.asarray(candidates)
    def kernel(a, b):
        return np.exp(-0.5 * ((a[:, None] - b[None, :]) ** 2).sum(axis=2))
    cross = kernel(x, points)
    chol = np.linalg.cholesky(kernel(x, x) + 1e-6 * np.eye(len(x)))
    weights = np.linalg.solve(chol.T, np.linalg.solve(chol, y - y.mean()))
    mean = y.mean() + cross.T @ weights
    spread = max(y.std(), 0.01) * np.sqrt(np.maximum(1e-9, 1 - (np.linalg.solve(chol, cross)**2).sum(axis=0)))
    return mean, spread


def log_feasibility(z):
    if z >= -10:
        return math.log(0.5 * math.erfc(-z / math.sqrt(2)))
    # Mills expansion for the lower normal tail, retaining scores below
    # floating-point probability range for strongly infeasible candidates.
    inv_sq = 1 / (z * z)
    return (-0.5 * z * z - math.log(-z) - 0.5 * math.log(2 * math.pi)
            + math.log1p(-inv_sq + 3 * inv_sq**2 - 15 * inv_sq**3))


def propose(method, observed, rng):
    unseen = [p for p in GRID if p not in observed]
    if method == "ordered":
        return min(unseen, key=lambda p: (p[1], p[0]))
    mean, spread = predict(observed, unseen)
    best = min((q for (d, q), m in observed.items() if m >= 0), default=5)
    if method == "BO":
        scores = [math.log(best-p[1]) + log_feasibility(m/s) if p[1] < best else -math.inf
                  for p, m, s in zip(unseen, mean, spread)]
        if max(scores) == -math.inf:
            scores = list(spread)
        return unseen[int(np.argmax(scores))]
    # Integer chromosomes (depth, flow); feasibility-first posterior mean fitness.
    scores = {p: (m >= 0, -p[1] if m >= 0 else m, m) for p, m in zip(unseen, mean)}
    population = rng.choices(unseen, k=8)
    for _ in range(5):
        parents = sorted(population, key=scores.get, reverse=True)[:4]
        population = parents.copy()
        while len(population) < 8:
            child = [rng.choice(parents)[0], rng.choice(parents)[1]]
            if rng.random() < 0.35:
                k = rng.randrange(2)
                child[k] = rng.choice(unseen)[k]
            p = tuple(child)
            population.append(p if p in scores else rng.choice(unseen))
    return max(population, key=scores.get)


def replay(margins, writer):
    for method in ("ordered", "BO", "GA"):
        for seed in (range(20) if method == "GA" else [0]):
            observed = {}
            rng = random.Random(seed)
            for step in range(len(GRID)):
                p = INITIAL[step] if step < len(INITIAL) else propose(method, observed, rng)
                assert p not in observed
                observed[p] = margins[p]
                best = min((q*0.08 for (_, q), m in observed.items() if m >= 0), default=None)
                best_margin = max(observed.values())
                writer.writerow([method, seed, step+1, p[0]*0.08, p[1]*0.08, observed[p], best, best_margin])


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    margins = read_fds()
    writer.writerow(["method","seed","queries","depth_m","flow_m3_s","observed_margin_m","best_feasible_flow_m3_s","best_observed_margin_m"])
    replay(margins, writer)
