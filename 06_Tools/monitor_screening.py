"""Monitor explicitly marked local propylene screening runs on Windows."""
import csv
import json
import math
import msvcrt
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "04_Results"
STATIONS = ("0.5", "1.7", "2.4", "3", "3.6", "4.2", "4.9", "6.1")


def inspect(marker):
    directory = marker.parent
    chid = marker.read_text().strip()
    if not chid.replace("_", "").isalnum():
        return
    deck = (directory / (chid + ".fds")).read_text()
    if "PROPYLENE" not in deck.upper() or f"CHID='{chid}'" not in deck:
        return
    output = directory / (chid + "_devc.csv")
    event = directory / "screen_failure.json"
    if not output.exists() or event.exists():
        return
    lines = output.read_bytes().splitlines(keepends=True)
    if lines and not lines[-1].endswith(b"\n"):
        lines.pop()
    if len(lines) < 3:
        return
    units, names, *rows = csv.reader(line.decode().strip() for line in lines)
    expected = {"Time": "s", "flowL": "m3/s", "flowR": "m3/s"}
    for x in STATIONS:
        expected.update({"layer"+x: "m", "vis"+x: "m", "co"+x: "mol/mol"})
    if any(dict(zip(names, units)).get(k) != u for k, u in expected.items()):
        raise ValueError(f"{chid}: unexpected device schema")
    frames = []
    for row in rows:
        if len(row) != len(names):
            raise ValueError(f"{chid}: invalid device row")
        frame = dict(zip(names, map(float, row)))
        if not all(map(math.isfinite, frame.values())) or (frames and frame["Time"] <= frames[-1]["Time"]):
            raise ValueError(f"{chid}: invalid sample")
        frames.append(frame)
    for i, frame in enumerate(frames):
        failures = [dict(x_m=float(x), height_m=frame["layer"+x], visibility_m=frame["vis"+x],
                         co_ppm=1e6*frame["co"+x]) for x in STATIONS if frame["layer"+x] < 0.38]
        if failures:
            # Original device and slice files stay in the run directory.
            record = dict(chid=chid, status="screen_failed", first_time_s=frame["Time"],
                          failures=failures, flow_L_m3_s=frame["flowL"], flow_R_m3_s=frame["flowR"],
                          observed_to_s=frames[-1]["Time"], full_duration_statistics=None,
                          observed_min_m=min(f["layer"+x] for f in frames for x in STATIONS),
                          adjacent_frames=frames[max(0,i-1):i+2],
                          slices=[p.name for p in directory.glob("*.sf")])
            temp = event.with_suffix(".tmp")
            temp.write_text(json.dumps(record, indent=2))
            (directory / (chid+".stop")).touch()
            temp.replace(event)
            break


if __name__ == "__main__":
    with (ROOT / "screen_monitor.lock").open("a+b") as lock:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        while True:
            for marker in ROOT.glob("*/screening.enabled"):
                try:
                    inspect(marker)
                except (OSError, ValueError) as error:
                    print(error, flush=True)
            time.sleep(5)
