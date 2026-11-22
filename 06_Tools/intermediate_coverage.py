"""Build the 1.12 m3/s report snapshot from the six native FDS device histories."""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIONS = ("0.5", "1.7", "2.4", "3", "3.6", "4.2", "4.9", "6.1")


def inspect(deck):
    case = deck.stem
    directory = ROOT / "04_Results" / case
    device = directory / (case + "_devc.csv")
    if not device.exists():
        return "Pending", None
    if (directory / deck.name).read_text(encoding="utf-8-sig") != deck.read_text(encoding="utf-8-sig"):
        raise ValueError(f"Input differs from reference: {case}")
    with device.open(encoding="utf-8-sig") as stream:
        next(stream)
        rows = []
        for row in csv.DictReader(stream, skipinitialspace=True):
            if any(row.get("layer" + x) in (None, "") for x in STATIONS):
                continue
            rows.append((float(row["Time"]), [float(row["layer" + x]) for x in STATIONS]))
    if not rows:
        return "Starting", None
    assert rows[0][0] == 0 and all(0 < b[0]-a[0] < .6 for a,b in zip(rows,rows[1:])), case
    assert all(math.isfinite(h) for _,heights in rows for h in heights), case
    h,t,x = min((h,t,float(x)) for t,heights in rows for x,h in zip(STATIONS,heights))
    end = rows[-1][0]
    tail = (directory / (case + ".out")).read_bytes()[-8192:]
    complete = end >= 119.999 and f"FDS completed successfully (CHID: {case})".encode() in tail
    status = "Breach" if h < .38 else "Pass" if complete else "Partial"
    return status,(end,h,t,x)


def main():
    rows = []
    verified = 0
    decks = sorted((ROOT / "03_Models").glob("*_1p12_z38_120.fds"))
    assert len(decks) == 6
    for deck in decks:
        _,door,soot,*_ = deck.stem.split("_")
        state, values = inspect(deck)
        verified += state in ("Pass", "Breach")
        fields = ["OP-" + door, f"{float(soot.replace('p','.')):.2f}", state]
        fields += [f"{values[0]:.1f}", f"{values[1]:.4f}"] if values else ["--","--"]
        rows.append(" & ".join(fields) + r" \\")
        print(deck.stem,state,values)
    target = ROOT / "07_Report/LaTeX/sections/intermediate-coverage.tex"
    count_file = target.with_name("intermediate-count.tex")
    count_file.write_text(str(verified) + "%\n", encoding="ascii")
    target.write_text("\n".join(rows)+"\n", encoding="ascii")


if __name__ == "__main__":
    main()
