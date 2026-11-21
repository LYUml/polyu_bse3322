"""Read a design centreplane profile: CASE X TIME [--half-height]."""
import csv
import struct
import sys
from pathlib import Path

case = Path(sys.argv[1])
position, requested = map(float, sys.argv[2:4])
half_height = sys.argv[4:] == ["--half-height"]
if sys.argv[4:] and not half_height:
    raise ValueError("Expected --half-height or no optional argument")

def record(stream):
    marker=stream.read(4)
    if not marker: return None
    n,=struct.unpack("<i", marker)
    if n<0: raise ValueError("Invalid record size")
    data=stream.read(n)
    if stream.read(4)!=marker: raise ValueError("Incomplete slice record")
    return data

def profile(index, quantity, unit):
    with (case/f"{case.name}_1_{index}.sf").open("rb") as stream:
        if record(stream).decode().strip()!=quantity: raise ValueError(quantity)
        record(stream)
        if record(stream).decode().strip()!=unit: raise ValueError(unit)
        bounds = struct.unpack("<6i", record(stream))
        if bounds[:5] != (0, 132, 9, 9, 0) or bounds[5] not in (19, 38):
            raise ValueError("Expected a supported design centreplane")
        nodes = bounds[5] + 1
        previous=None
        while (stamp:=record(stream)) is not None:
            t,=struct.unpack("<f",stamp)
            frame=record(stream)
            i=round(position/0.05)
            if not 0<=i<=132 or len(frame)!=133*nodes*4: raise ValueError("Invalid slice dimensions")
            values=[struct.unpack_from("<f",frame,4*(i+133*k))[0] for k in range(nodes)]
            current=t,values
            if t>=requested:
                return min((v for v in (previous,current) if v),key=lambda v:abs(v[0]-requested))
            previous=current
    raise ValueError("Requested time not yet covered")
t,temp=profile(1,"TEMPERATURE","C")
s,extinction=profile(5,"SOOT EXTINCTION COEFFICIENT","1/m")
if abs(t-s)>0.001 or len(temp)!=len(extinction): raise ValueError("Slices out of sync")
out=csv.writer(sys.stdout,lineterminator="\n")
out.writerow(["case","time_s","x_m","y_m","z_m","gas_temperature_C","soot_extinction_per_m"])
location = [case.name, round(t,4), round(round(position/0.05)*0.05,3), 0.45]
cells = len(temp) - 1
if half_height:
    # Odd cell counts bracket half height; even counts place a node there.
    lower, upper = cells // 2, (cells + 1) // 2
    out.writerow(location + [0.38, (temp[lower]+temp[upper])/2,
                             (extinction[lower]+extinction[upper])/2])
else:
    for k in range(1, cells):
        out.writerow(location + [round(k*0.76/cells, 2), round(temp[k], 3), round(extinction[k], 5)])
