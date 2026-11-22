"""Compare the vertical-grid refinement (z38, 0.02 m) against the 19-layer base runs.

Both refinement cases are 1.28 m3/s, soot yield 0.02, OP-1 with 0.24 m curtains.
The base runs live in 05_Calculations/<CHID>_stations.csv; the refined runs are written
to 04_Results/<CHID>/stations.csv by summarize_design.cjs.

Usage:
    python 06_Tools/compare_z38.py
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CALC = REPO / "05_Calculations"
RESULTS = REPO / "04_Results"

PAIRS = [
    ("inlet44_1_0p02_0p24_1p28_120", "inlet44_1_0p02_0p24_1p28_z38_120", "0.44"),
    ("inlet48_1_0p02_0p24_1p28_120", "inlet48_1_0p02_0p24_1p28_z38_120", "0.48"),
]

FIELDS = [
    "case",
    "inlet_height_m",
    "z19_min_height_m",
    "z38_min_height_m",
    "delta_m",
    "z19_x_m",
    "z38_x_m",
    "z19_time_at_min_s",
    "z38_time_at_min_s",
    "z19_below_duration_s",
    "z38_below_duration_s",
]


def read_stations(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {float(row["x_m"]): row for row in csv.DictReader(handle)}


def load_pair(base, refined):
    base_rows = read_stations(CALC / (base + "_stations.csv"))
    refined_rows = read_stations(RESULTS / refined / "stations.csv")
    return base_rows, refined_rows


def summarise(base_rows, refined_rows):
    """Pick the station carrying the lowest layer in either run."""
    worst = None
    for x, base_row in base_rows.items():
        ref_row = refined_rows.get(x)
        if ref_row is None:
            continue
        base_h = float(base_row["min_height_m"])
        ref_h = float(ref_row["min_height_m"])
        if worst is None or min(base_h, ref_h) < min(worst[1], worst[2]):
            worst = (x, base_h, ref_h, base_row, ref_row)
    return worst


def main():
    out_rows = []
    for base, refined, height in PAIRS:
        if not (RESULTS / refined / "stations.csv").exists():
            print("missing:", refined)
            continue
        base_rows, refined_rows = load_pair(base, refined)
        for x in sorted(base_rows):
            b = base_rows[x]
            r = refined_rows[x]
            out_rows.append(
                {
                    "case": refined,
                    "inlet_height_m": height,
                    "z19_min_height_m": b["min_height_m"],
                    "z38_min_height_m": r["min_height_m"],
                    "delta_m": f"{float(r['min_height_m']) - float(b['min_height_m']):.5f}",
                    "z19_x_m": x,
                    "z38_x_m": r["x_m"],
                    "z19_time_at_min_s": b["time_at_min_s"],
                    "z38_time_at_min_s": r["time_at_min_s"],
                    "z19_below_duration_s": b["below_duration_s"],
                    "z38_below_duration_s": r["below_duration_s"],
                }
            )
        worst = summarise(base_rows, refined_rows)
        print(
            f"{refined}: worst station x={worst[0]} "
            f"z19={worst[1]:.4f} m  z38={worst[2]:.4f} m  delta={worst[2] - worst[1]:+.4f} m"
        )

    target = CALC / "z38_refinement_check.csv"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)
    print("wrote", target, len(out_rows), "rows")


if __name__ == "__main__":
    main()
