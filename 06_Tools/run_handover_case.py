"""Start one Group 18 handover case on Windows, from scratch or a copied checkpoint."""
import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path

from monitor_screening import inspect

ROOT = Path(__file__).resolve().parents[1]
PRESETS = [
    f"inlet{height}_{op}_{soot}_0p24_0p96_120"
    for height, op in [(44, 1), (48, 6)]
    for soot in ("0p02", "0p05", "0p1")
]
REFINEMENTS = [
    f"inlet{height}_1_0p02_0p24_1p28_z38_120" for height in (44, 48)
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=PRESETS + REFINEMENTS)
    parser.add_argument("--fds", default=shutil.which("fds") or
                        r"C:\Program Files\PyroSim 2026\fds\fds.exe")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--check", action="store_true", help="Check inputs without starting FDS")
    args = parser.parse_args()
    case = args.case
    source = ROOT / "03_Models" / (case + ".fds")
    dest = ROOT / "04_Results" / case
    solver = Path(args.fds).resolve(strict=True)
    deck = source.read_text(encoding="utf-8-sig")
    if f"CHID='{case}'" not in deck or "T_END=120" not in deck:
        parser.error("Unexpected case ID or end time in source deck")
    if args.resume:
        required = [case + s for s in (".fds", "_1.restart", ".out", "_devc.csv", "_hrr.csv")]
        if not all((dest / f).is_file() and (dest / f).stat().st_size for f in required):
            parser.error("Checkpoint incomplete. Extract the handover archive into a clean clone.")
        if (dest / (case + ".fds")).read_text(encoding="utf-8-sig") != deck:
            parser.error("Checkpoint and source input differ")
        tail = (dest / (case + ".out")).read_bytes()[-4096:]
        if b"FDS stopped by user" not in tail or (dest / "screen_failure.json").exists():
            parser.error("Only user-paused checkpoints can be resumed")
        if (dest / (case + ".stop")).exists():
            parser.error("Stop marker present. Use a clean extraction of the checkpoint archive.")
        if deck.count("&MISC ") != 1:
            parser.error("Unexpected MISC record")
        name = "resume_" + case + ".fds"
    else:
        if dest.exists():
            parser.error("Result directory exists. Use --resume for a checkpoint or a fresh clone.")
        name = case + ".fds"
    if args.check:
        print("OK:", solver, case, "resume" if args.resume else "fresh")
        return
    if args.resume:
        (dest / name).write_text(deck.replace("&MISC ", "&MISC RESTART=.TRUE., "), encoding="ascii")
    else:
        dest.mkdir(parents=True, exist_ok=False)
        shutil.copy2(source, dest / name)
    marker = dest / "screening.enabled"
    if case in PRESETS:
        marker.write_text(case, encoding="ascii")
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join((str(solver.parent), str(solver.parent / "mpi"), env["PATH"]))
    env["OMP_NUM_THREADS"] = "1"
    proc = subprocess.Popen([str(solver), name], cwd=dest, env=env)
    while proc.poll() is None:
        if case in PRESETS:
            inspect(marker)
        time.sleep(5)
    if case in PRESETS:
        inspect(marker)
    out = dest / (case + ".out")
    tail = out.read_bytes()[-4096:] if out.exists() else b""
    if (dest / "screen_failure.json").is_file():
        print("Screen failed. Evidence:", dest / "screen_failure.json")
    elif proc.returncode or b"FDS completed successfully" not in tail:
        raise SystemExit(f"FDS did not finish successfully. Inspect {out}")
    else:
        print("FDS finished. Verify the complete time series in", dest)


if __name__ == "__main__":
    main()
