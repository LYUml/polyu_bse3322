"""Summarize the six completed fixed-design scenarios as CSV on stdout."""
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def summarize(case):
    run = subprocess.run(
        ["node", str(ROOT / "06_Tools/summarize_design.cjs"), str(ROOT / "04_Results" / case)],
        check=True, capture_output=True, text=True,
    )
    stations = list(csv.DictReader(io.StringIO(run.stdout)))
    if len({s["x_m"] for s in stations}) != 8 or len(stations) != 8:
        raise ValueError(f"Expected eight stations in {case}")
    if any(s["case"] != case or float(s["end_s"]) != 120 or float(s["start_s"]) != 0 for s in stations):
        raise ValueError(f"Unexpected scenario or interval in {case}")
    height = min(stations, key=lambda s: float(s["min_height_m"]))
    visibility = min(stations, key=lambda s: float(s["min_visibility_m"]))
    co = max(stations, key=lambda s: float(s["max_co_ppm"]))
    return [case, height["min_height_m"], height["x_m"], visibility["min_visibility_m"],
            visibility["x_m"], co["max_co_ppm"], co["x_m"],
            json.loads(run.stderr)["any_station_below_duration_s"]]


if __name__ == "__main__":
    cases = [f"design_{op}_{yield_id}_0p16_0p16_120"
             for op in (1, 6) for yield_id in ("0p02", "0p05", "0p1")]
    rows = [summarize(case) for case in cases]
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["case", "min_height_m", "height_station_x_m", "min_visibility_m",
                     "visibility_station_x_m", "max_co_ppm", "co_station_x_m",
                     "any_station_below_duration_s"])
    writer.writerows(rows)
