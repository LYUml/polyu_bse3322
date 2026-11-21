"""Summarize the six completed fixed-design scenarios as CSV on stdout."""
import argparse
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def summarize(case):
    directory = ROOT / "04_Results" / case
    if directory.is_dir():
        run = subprocess.run(
            ["node", str(ROOT / "06_Tools/summarize_design.cjs"), str(directory)],
            check=True, capture_output=True, text=True,
        )
        stations = list(csv.DictReader(io.StringIO(run.stdout)))
        duration = json.loads(run.stderr)["any_station_below_duration_s"]
    else:
        archive = ROOT / "05_Calculations"
        with (archive / f"{case}_stations.csv").open(encoding="utf-8-sig") as source:
            stations = list(csv.DictReader(source))
        with (archive / "design_excursion_durations.csv").open(encoding="utf-8-sig") as source:
            matches = [r for r in csv.DictReader(source) if r["case"] == case
                       and float(r["start_s"]) == 0 and float(r["end_s"]) == 120]
        if len(matches) != 1:
            raise ValueError(f"Expected one full-duration excursion record for {case}")
        duration = float(matches[0]["any_station_below_duration_s"])
    expected_positions = {0.5, 1.7, 2.4, 3.0, 3.6, 4.2, 4.9, 6.1}
    if {float(s["x_m"]) for s in stations} != expected_positions or len(stations) != 8:
        raise ValueError(f"Unexpected station positions in {case}")
    if any(s["case"] != case or float(s["end_s"]) != 120 or float(s["start_s"]) != 0 for s in stations):
        raise ValueError(f"Unexpected scenario or interval in {case}")
    height = min(stations, key=lambda s: float(s["min_height_m"]))
    visibility = min(stations, key=lambda s: float(s["min_visibility_m"]))
    co = max(stations, key=lambda s: float(s["max_co_ppm"]))
    return [case, height["min_height_m"], height["x_m"], height["time_at_min_s"], visibility["min_visibility_m"],
            visibility["x_m"], visibility["time_at_min_visibility_s"], co["max_co_ppm"], co["x_m"], co["time_at_max_co_s"],
            duration]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    designs = {
        "baseline": ("design", "0p16", "0p16"),
        "tall_makeup": ("tall_makeup", "0p16", "1p28"),
        "tall_makeup_deep": ("tall_makeup", "0p24", "1p28"),
        "inlet44": ("inlet44", "0p24", "1p28"),
    }
    parser.add_argument("--design", choices=designs, default="baseline")
    args = parser.parse_args()
    prefix, depth, flow = designs[args.design]
    rows = []
    for opening in (1, 6):
        for soot_yield in (0.02, 0.05, 0.1):
            yield_id = str(soot_yield).replace(".", "p")
            case = f"{prefix}_{opening}_{yield_id}_{depth}_{flow}_120"
            rows.append([f"OP-{opening}", soot_yield, *summarize(case)])
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["opening", "soot_yield_kg_per_kg", "case", "min_height_m", "height_station_x_m", "time_at_min_height_s", "min_visibility_m",
                     "visibility_station_x_m", "time_at_min_visibility_s", "max_co_ppm", "co_station_x_m", "time_at_max_co_s",
                     "any_station_below_duration_s"])
    writer.writerows(rows)
