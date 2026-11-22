"""Compare the 1.28 m3/s door-preset runs with their 0.96 m3/s counterparts.

Reads
-----
05_Calculations/door_preset_1p28_six_scenarios.csv   archived 1.28 m3/s minima
04_Results/<CHID>/stations.csv                       per-station output of
                                                    summarize_design.cjs

Writes
------
05_Calculations/door_preset_flow_pair.csv

The 0.96 m3/s runs are only compared where a matched 1.28 m3/s run with the
same opening state and soot yield exists. Missing runs are reported, not
guessed: a candidate without a completed 120 s result stays "pending".
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "05_Calculations/door_preset_1p28_six_scenarios.csv"
RESULTS = ROOT / "04_Results"
OUT = ROOT / "05_Calculations/door_preset_flow_pair.csv"
THRESHOLD = 0.38

# 0.96 m3/s case -> matched 1.28 m3/s case
PAIRS = {
    "inlet44_1_0p02_0p24_0p96_120": "inlet44_1_0p02_0p24_1p28_120",
    "inlet48_6_0p05_0p24_0p96_120": "inlet48_6_0p05_0p24_1p28_120",
    "inlet48_6_0p1_0p24_0p96_120": "inlet48_6_0p1_0p24_1p28_120",
    "inlet44_1_0p1_0p24_0p96_120": "inlet44_1_0p1_0p24_1p28_120",
}


def read_baseline() -> dict[str, dict[str, str]]:
    with BASELINE.open(newline="", encoding="utf-8-sig") as fh:
        return {row["case"]: row for row in csv.DictReader(fh)}


def read_stations(case: str) -> tuple[float, str, float] | None:
    path = RESULTS / case / "stations.csv"
    if not path.is_file():
        return None
    raw = path.read_bytes()
    if raw[:2] == b"\xff\xfe":
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        return None
    worst = min(rows, key=lambda r: float(r["min_height_m"]))
    return (
        float(worst["min_height_m"]),
        worst["x_m"],
        float(worst["time_at_min_s"]),
    )


def main() -> int:
    baseline = read_baseline()
    fields = [
        "case",
        "flow_m3_s",
        "inlet_height_m",
        "soot_yield",
        "min_height_m",
        "margin_m",
        "x_m",
        "time_s",
        "status",
    ]
    out_rows: list[dict[str, str]] = []
    missing: list[str] = []

    for low, high in PAIRS.items():
        base = baseline.get(high)
        if base is None:
            continue
        inlet = base["inlet_height_m"]
        soot = low.split("_")[2].replace("0p", "0.")
        if soot.endswith("1"):
            soot = "0.10"
        for case, flow in ((high, "1.28"), (low, "0.96")):
            if case == high:
                value = float(base["min_height_m"])
                x = float(base["x_m"])
                t = float(base["time_s"])
                status = "pass" if value >= THRESHOLD else "fail"
            else:
                got = read_stations(case)
                if got is None:
                    missing.append(case)
                    value, x, t, status = float("nan"), "", float("nan"), "pending"
                else:
                    value, x, t = got
                    status = "pass" if value >= THRESHOLD else "fail"
            out_rows.append(
                {
                    "case": case,
                    "flow_m3_s": flow,
                    "inlet_height_m": inlet,
                    "soot_yield": soot,
                    "min_height_m": "" if value != value else f"{value:.8f}",
                    "margin_m": "" if value != value else f"{value - THRESHOLD:.8f}",
                    "x_m": "" if x == "" else f"{float(x):g}",
                    "time_s": "" if t != t else f"{t:.6f}",
                    "status": status,
                }
            )

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"wrote {OUT.relative_to(ROOT)} with {len(out_rows)} rows")
    print(f"{'case':44s} {'flow':>5s} {'inlet':>6s} {'soot':>5s} {'min_m':>8s} {'status':>8s}")
    for row in out_rows:
        print(
            f"{row['case']:44s} {row['flow_m3_s']:>5s} {row['inlet_height_m']:>6s} "
            f"{row['soot_yield']:>5s} {row['min_height_m']:>8s} {row['status']:>8s}"
        )
    if missing:
        print("pending (no completed stations.csv yet):")
        for case in missing:
            print(f"  - {case}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
