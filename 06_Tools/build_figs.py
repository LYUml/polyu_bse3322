"""Build the report figures from the students' own FDS output files.

Data live in  _tmp/bse_data/<case>__BSE3322_Fire_CFD_Model_devc.csv
Each file has one row of units, one row of column names (the ceiling
thermocouple positions in metres) and then 1 s samples.
(numpy + matplotlib only - the venv has no pandas.)
"""
from __future__ import annotations

import csv
import json
import re
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = r"C:\Users\Lenovo\Documents\deepseek-harness\default-workspace\BSE3322_Group18\Report"
DATA = r"C:\Users\Lenovo\Documents\deepseek-harness\default-workspace\_tmp\bse_data"
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

CASES = {
    "A1": ("All, 47.2, Fine", "four openings"),
    "A2": ("All, 106.2, Fine", "four openings"),
    "B1": ("R2, 47.2, Fine", "one opening"),
    "B2": ("R2, 106.2, Fine", "one opening"),
    "F02": ("All, 106.2, Fine, but fraction=0.2", "chi_r = 0.20"),
    "F05": ("All, 106.2 Fine, but fraction=0.5", "chi_r = 0.50"),
    "SE1": ("Smoke Extraction 1", "soot 0.02"),
    "SE2": ("Smoke Extraction 1 but soot=0.1", "soot 0.10"),
    "SE3": ("Smoke Extraction 1 but Fire curtain", "curtain only"),
}

T0, T1 = 50.0, 100.0


def deck_positions(case: str) -> dict:
    folder = CASES.get(case, (case, ""))[0]
    path = os.path.join(DATA, f"{folder}__BSE3322_Fire_CFD_Model.fds")
    txt = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for line in re.findall(r"&DEVC[^\n]*", txt):
        m = re.search(r"ID='([^']+)'", line)
        c = re.search(r"XYZ=\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)", line)
        if m and c:
            out[m.group(1)] = (float(c.group(1)), float(c.group(2)), float(c.group(3)))
    return out


def load(case: str):
    folder = CASES.get(case, (case, ""))[0]
    path = os.path.join(DATA, f"{folder}__BSE3322_Fire_CFD_Model_devc.csv")
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        rows = list(csv.reader(fh))
    names = rows[1]
    pos = deck_positions(case)
    xs = np.array([pos.get(n, (float(i - 1) * 0.1, 0, 0))[0] for i, n in enumerate(names)
                   if i > 0])
    body = []
    for r in rows[2:]:
        if not r:
            continue
        try:
            body.append([float(v) for v in r])
        except ValueError:
            continue
    data = np.array(body)
    return names[0], xs, data


def stats(case: str) -> dict:
    _, xs, data = load(case)
    t = data[:, 0]
    win = data[(t >= T0) & (t <= T1)][:, 1:]
    prof = win.mean(axis=0)
    return {
        "xs": xs.tolist(),
        "profile": prof.tolist(),
        "peak": float(prof.max()),
        "peak_x": float(xs[int(np.argmax(prof))]),
        "peak_max": float(win.max()),
        "end_left": float(prof[2]),
        "end_right": float(prof[-3]),
        "mean_all": float(prof.mean()),
        "t_full": float(t.max()),
    }


def fig_geometry() -> None:
    open_x = [(0.610, 1.040), (2.260, 2.690), (3.910, 4.340), (5.560, 5.990)]
    labels = ["OP-A", "OP-B", "OP-C", "OP-D"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.4, 5.6))

    ax1.add_patch(plt.Rectangle((0, 0), 6.6, 0.9, fill=False, lw=1.6, ec="k"))
    ax1.add_patch(plt.Rectangle((0, 0.9), 6.6, 0.05, fc="0.35", ec="k", lw=0.8))
    ax1.add_patch(plt.Rectangle((0, 0.95), 6.6, 0.35, fc="#d9eaf7", ec="0.6", lw=0.8))
    for (a, b), lab in zip(open_x, labels):
        ax1.add_patch(plt.Rectangle((a, 0.9), b - a, 0.05, fc="white", ec="#1f77b4",
                                    lw=1.4, hatch="//"))
        ax1.annotate(lab, ((a + b) / 2, 1.05), ha="center", fontsize=8, color="#1f77b4")
    ax1.add_patch(plt.Rectangle((3.2, 0.35), 0.2, 0.2, fc="#d62728", ec="k", lw=0.6))
    ax1.annotate("0.2 x 0.2 m burner", (3.3, 0.30), ha="center", va="top", fontsize=7.5)
    ax1.annotate("ambient zone (open on XMIN, XMAX, YMAX, ZMAX)", (6.55, 1.14),
                 ha="right", fontsize=7, color="0.35")
    ax1.set_xlim(-0.15, 6.75)
    ax1.set_ylim(-0.12, 1.38)
    ax1.set_aspect("equal")
    ax1.set_xlabel("X (m)")
    ax1.set_ylabel("Y (m)")
    ax1.set_title("(a) Plan view: 6.6 x 0.9 x 0.76 m compartment with four openings")

    ax2.add_patch(plt.Rectangle((0, 0), 6.6, 0.76, fill=False, lw=1.6, ec="k"))
    for (a, b), lab in zip(open_x, labels):
        ax2.add_patch(plt.Rectangle((a, 0), b - a, 0.63, fc="white", ec="#1f77b4",
                                    lw=1.4, hatch="//"))
        ax2.annotate(lab, ((a + b) / 2, 0.665), ha="center", fontsize=8, color="#1f77b4")
    ax2.plot([0, 6.6], [0.38, 0.38], ls=":", c="0.4", lw=1)
    ax2.annotate("half height 0.38 m", (0.15, 0.40), fontsize=7.5, color="0.35")
    ax2.add_patch(plt.Rectangle((3.2, 0), 0.2, 0.01, fc="#d62728", ec="k", lw=0.6))
    ax2.set_xlim(-0.15, 6.75)
    ax2.set_ylim(-0.08, 0.92)
    ax2.set_xlabel("X (m)")
    ax2.set_ylabel("Z (m)")
    ax2.set_title("(b) Section at mid-width: floor-mounted openings, 0.43 x 0.63 m")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_geometry.png"), dpi=200)
    plt.close(fig)


def fig_time(cases=("A1", "A2", "B1", "B2")) -> None:
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    styles = {"A1": ("#1f77b4", "-"), "A2": ("#d62728", "-"),
              "B1": ("#1f77b4", "--"), "B2": ("#d62728", "--")}
    for c in cases:
        _, xs, data = load(c)
        col = 1 + int(np.argmin(np.abs(xs - 3.3)))
        q = {1: 47.2, 2: 106.2}.get(int(c[1]), 106.2)
        ax.plot(data[:, 0], data[:, col], lw=1.2, color=styles[c][0], ls=styles[c][1],
                label=f"{q:.1f} kW, {CASES[c][1]}")
    ax.axvline(50, ls=":", c="0.5", lw=1)
    ax.annotate("averaging window starts at 50 s", (50.5, 120), fontsize=7.5, color="0.4")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Gas temperature above the fire (degC)")
    ax.set_title("Ceiling temperature at X = 3.3 m")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_time.png"), dpi=200)
    plt.close(fig)


def fig_profile() -> None:
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    styles = {"A1": ("#1f77b4", "-", "47.2 kW, four openings"),
              "A2": ("#d62728", "-", "106.2 kW, four openings"),
              "B1": ("#1f77b4", "--", "47.2 kW, one opening"),
              "B2": ("#d62728", "--", "106.2 kW, one opening")}
    for c, (col, ls, lab) in styles.items():
        s = stats(c)
        ax.plot(s["xs"], s["profile"], color=col, ls=ls, lw=1.5, label=lab)
    ax.set_xlabel("Distance from the left wall, X (m)")
    ax.set_ylabel("Mean ceiling temperature (degC)")
    ax.set_title("Ceiling-jet temperature profile, 50-100 s mean")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_profile.png"), dpi=200)
    plt.close(fig)


def fig_fraction() -> None:
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    for c, lab, col in (("F02", "chi_r = 0.20", "#2ca02c"),
                        ("A2", "chi_r = 0.35 (default)", "#d62728"),
                        ("F05", "chi_r = 0.50", "#9467bd")):
        s = stats(c)
        ax.plot(s["xs"], s["profile"], lw=1.5, color=col, label=lab)
    ax.set_xlabel("Distance from the left wall, X (m)")
    ax.set_ylabel("Mean ceiling temperature (degC)")
    ax.set_title("Sensitivity to the radiative fraction, 106.2 kW, four openings")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_fraction.png"), dpi=200)
    plt.close(fig)


def fig_design() -> None:
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    for c, lab, col, ls in (("SE1", "extraction, soot yield 0.02", "#1f77b4", "-"),
                            ("SE2", "extraction, soot yield 0.10", "#d62728", "-"),
                            ("SE3", "curtain only, no extraction", "#2ca02c", "--")):
        s = stats(c)
        ax.plot(s["xs"], s["profile"], lw=1.5, color=col, ls=ls, label=lab)
    ax.set_xlabel("Distance from the left wall, X (m)")
    ax.set_ylabel("Mean ceiling temperature (degC)")
    ax.set_title("Smoke-extraction cases, 106.2 kW propylene")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_design.png"), dpi=200)
    plt.close(fig)


def fig_alpert() -> None:
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    s = stats("A2")
    ax.plot(s["xs"], s["profile"], lw=1.6, color="#d62728", label="FDS, 106.2 kW")
    Q, H = 106.2, 0.76
    xs = np.array(s["xs"])
    r = np.maximum(np.abs(xs - 3.3), 1e-6)
    dT = np.where(r / H <= 0.18,
                  16.9 * Q ** (2 / 3) / H ** (5 / 3),
                  5.38 * (Q / r) ** (2 / 3) / H)
    ax.plot(xs, dT + 20, lw=1.4, color="0.35", ls="--",
            label="Alpert correlation (unconfined)")
    ax.set_xlabel("Distance from the left wall, X (m)")
    ax.set_ylabel("Ceiling temperature (degC)")
    ax.set_title("Ceiling-jet profile against the classical correlation")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_alpert.png"), dpi=200)
    plt.close(fig)


def main() -> None:
    fig_geometry()
    fig_time()
    fig_profile()
    fig_fraction()
    fig_design()
    fig_alpert()
    out = {c: stats(c) for c in CASES}
    with open(os.path.join(BASE, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    for c, s in out.items():
        print(f"{c:4s} peak={s['peak']:7.1f} at x={s['peak_x']:4.1f}  "
              f"ends={s['end_left']:6.1f}/{s['end_right']:6.1f}  mean={s['mean_all']:6.1f}  t={s['t_full']:.0f}")
    print("figures ->", FIG)


if __name__ == "__main__":
    main()
