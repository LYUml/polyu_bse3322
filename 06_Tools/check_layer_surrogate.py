"""Whole-case smoke extraction surrogate benchmark. See the project note for units."""
import argparse
import csv
import sys

import numpy as np

from replay_search import ROOT, predict, read_fds


def datasets():
    # Use the same grid-step coordinates as the existing blind search replay.
    grid = {p: margin + 0.38 for p, margin in read_fds().items()}
    tall = {}
    path = ROOT / "05_Calculations/tall_makeup_op6_completed_scenarios.csv"
    with path.open(encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            depth, soot = float(row["curtain_depth_m"]), float(row["soot_yield"])
            expected = f"tall_makeup_6_{soot:g}_{depth:g}_1.28_120".replace(".", "p")
            if (row["case_id"] != expected or row["opening"] != "OP6"
                    or float(row["end_s"]) != 120 or float(row["total_flow_m3_s"]) != 1.28):
                raise ValueError(f"Unexpected tall makeup case: {row}")
            point = (depth / 0.08, soot / 0.04)
            if point in tall:
                raise ValueError(f"Duplicate tall makeup case: {expected}")
            tall[point] = float(row["min_layer_m"])
    if len(tall) != 6 or any(not 0 <= y <= 0.76 for y in [*grid.values(), *tall.values()]):
        raise ValueError("Invalid benchmark labels")
    return {"original": grid, "tall": tall}


def predictions(train, point):
    # All centering and coefficients use training cases only.
    x, y = np.array(list(train)), np.array(list(train.values()))
    linear = np.linalg.lstsq(np.column_stack((np.ones(len(x)), x)), y, rcond=None)[0]
    gp, _ = predict(train, [point])
    return {"mean": y.mean(), "linear": np.dot([1, *point], linear), "gp": gp[0]}


def benchmark(data):
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["layout", "depth_m", "flow_m3_s", "soot_yield", "fds_min_m",
                     "mean_pred_m", "linear_pred_m", "gp_pred_m"])
    for layout, cases in data.items():
        for point, actual in cases.items():
            train = cases.copy()
            del train[point]
            outputs = predictions(train, point)
            flow, soot = (point[1]*0.08, 0.02) if layout == "original" else (1.28, point[1]*0.04)
            writer.writerow([layout, round(point[0]*0.08, 4), round(flow, 4), round(soot, 4),
                             round(actual, 9), *(round(v, 9) for v in outputs.values())])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", nargs=2, type=float, metavar=("DEPTH_M", "FLOW_M3_S"))
    parser.add_argument("--tall", nargs=2, type=float, metavar=("DEPTH_M", "SOOT_YIELD"))
    args = parser.parse_args()
    if args.original and args.tall:
        parser.error("Select one layout")
    data = datasets()
    if args.original or args.tall:
        layout = "original" if args.original else "tall"
        d, v = args.original or args.tall
        point = (d / 0.08, v / (0.08 if args.original else 0.04))
        bounds = np.array(list(data[layout]))
        if not np.all((bounds.min(axis=0) <= point) & (point <= bounds.max(axis=0))):
            parser.error("Requested design outside sampled range")
        for name, value in predictions(data[layout], point).items():
            print(f"{name}: {value:.6f} m")
    else:
        benchmark(data)
