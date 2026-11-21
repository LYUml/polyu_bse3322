"""Summarize half-height soot continuity on the design grids. Pass case directories."""
import csv
import struct
import sys
from pathlib import Path

import numpy as np


def record(stream):
    size, = struct.unpack("<i", stream.read(4))
    if size < 0:
        raise ValueError("Negative record size")
    payload = stream.read(size)
    if len(payload) != size or stream.read(4) != struct.pack("<i", size):
        raise ValueError("Incomplete Fortran record")
    return payload


def intervals(mask):
    changes = np.diff(np.r_[False, mask, False].astype(int))
    return zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1) - 1)


def summarize(directory):
    name = directory.name
    smoke = directory / (name + "_1_1.s3d")
    metadata = (directory / (name + ".smv")).read_text().splitlines()
    index = [line.strip() for line in metadata].index(smoke.name)
    if metadata[index + 1].strip() != "SOOT DENSITY":
        raise ValueError("Expected soot density")
    times, frames = [], []
    with smoke.open("rb") as stream:
        header = struct.unpack("<8i", record(stream))
        if header[:7] != (1, 0, 0, 132, 0, 28, 0) or header[7] not in (19, 38):
            raise ValueError("Expected a supported design mesh")
        cells_z = header[7]
        # Keep the same two physical heights on both vertical grids.
        height_indices = [round(z * cells_z / 0.76) for z in (0.36, 0.40)]
        while stream.peek(1):
            time_s, = struct.unpack("<f", record(stream))
            count, compressed = struct.unpack("<2i", record(stream))
            payload = record(stream)
            if len(payload) != compressed or count != (cells_z + 1) * 29 * 133:
                raise ValueError("Unexpected frame dimensions")
            values = bytearray()
            i = 0
            while i < compressed:
                if payload[i] == 255:
                    values.extend(bytes([payload[i + 1]]) * payload[i + 2])
                    i += 3
                else:
                    values.append(payload[i])
                    i += 1
            field = np.frombuffer(values, dtype=np.uint8).reshape(cells_z + 1, 29, 133)
            # Check both sampled heights at interior x nodes.
            frames.append((field[height_indices, :, 1:-1] > 0).all(axis=0))
            times.append(time_s)
    if len(times) != 121 or times[0] != 0 or times[-1] != 120 or not np.allclose(np.diff(times), 1, atol=0.02):
        raise ValueError("Expected complete 120 s output with one frame per second")
    for y in (3, 9, 15):
        mask = np.asarray(frames)[:, y, :]
        # Resolve ties by latest frame, then rightmost position, as in the archive.
        space = max(((r-l, t, l, r) for t, row in enumerate(mask)
                     for l, r in intervals(row)), default=None)
        if space is None:
            yield [name, round(y*.05, 2), 0, "", "", "", 0, "", "", ""]
            continue
        span, t, l, r = space
        duration, x, start, end = max((times[e]-times[s], x, s, e)
                                      for x, row in enumerate(mask.T) for s, e in intervals(row))
        yield [name, round(y*.05, 2), round(span*.05, 3), round(times[t], 3),
               round((l+1)*.05, 2), round((r+1)*.05, 2), round(duration, 3),
               round((x+1)*.05, 2), round(times[start], 3), round(times[end], 3)]


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow("case y_m max_span_m span_time_s left_x_m right_x_m longest_same_point_span_s point_x_m first_sample_s last_sample_s".split())
    for argument in sys.argv[1:]:
        writer.writerows(summarize(Path(argument)))
