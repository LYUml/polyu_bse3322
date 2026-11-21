"""Rebuild the six-case half-height Smoke3D footprint table on stdout."""
import csv
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def record(stream):
    marker = stream.read(4)
    if not marker:
        return None
    size, = struct.unpack("<I", marker)
    data = stream.read(size)
    if len(data) != size or stream.read(4) != marker:
        raise ValueError("Incomplete Fortran record")
    return data


def decompress(payload):
    decoded = bytearray()
    index = 0
    while index < len(payload):
        value = payload[index]
        index += 1
        if value == 255:
            value, repeats = payload[index:index + 2]
            index += 2
            decoded.extend(bytes([value]) * repeats)
        else:
            decoded.append(value)
    if len(decoded) != 20 * 29 * 133:
        raise ValueError("Unexpected Smoke3D frame dimensions")
    return np.frombuffer(decoded, dtype=np.uint8).reshape(20, 29, 133)


def footprint(case):
    directory = ROOT / "04_Results" / case
    name = f"{case}_1_1.s3d"
    metadata = (directory / f"{case}.smv").read_text().splitlines()
    position = [line.strip() for line in metadata].index(name)
    if metadata[position + 1].strip() != "SOOT DENSITY":
        raise ValueError(f"{name} does not contain soot density")
    occupied = np.zeros(131, dtype=bool)
    outer_count = max_count = 0
    times = []
    with (directory / name).open("rb") as stream:
        if struct.unpack("<8i", record(stream)) != (1, 0, 0, 132, 0, 28, 0, 19):
            raise ValueError("Expected the preset design grid")
        while (stamp := record(stream)) is not None:
            times.append(struct.unpack("<f", stamp)[0])
            size, packed = struct.unpack("<ii", record(stream))
            data = record(stream)
            if size != 77140 or len(data) != packed:
                raise ValueError("Invalid frame size")
            # Interior nodes only. Either level bracketing z=0.38 m can register smoke.
            signal = decompress(data)[9:11, 1:18, 1:132].any(axis=0)
            occupied |= signal.any(axis=0)
            outer_count += int(signal[:, :48].sum() + signal[:, 83:].sum())
            max_count = max(max_count, int(signal.sum()))
    if len(times) != 121 or not np.allclose(times, np.arange(121), atol=0.02, rtol=0):
        raise ValueError("Expected a complete 0-120 s time series")
    detected = np.flatnonzero(occupied)
    extent = ((detected[[0, -1]] + 1) / 20 if detected.size else ("", ""))
    return case, len(times), *extent, outer_count, max_count, 131 * 17


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["case", "frames", "first_x_ever_detected_m", "last_x_ever_detected_m",
                     "outer_positive_node_frames", "max_simultaneous_positive_nodes",
                     "interior_nodes_per_frame"])
    with (ROOT / "05_Calculations/door_preset_1p28_six_scenarios.csv").open() as source:
        for row in csv.DictReader(source):
            writer.writerow(footprint(row["case"]))
