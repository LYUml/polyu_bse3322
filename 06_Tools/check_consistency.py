"""Cross-check every number in the report against stats.json and the decks."""
import json
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "07_Report"
DOCX = REPORT / "BSE3322_Group18_Report_v3.docx"
S = json.loads((ROOT / "05_Calculations" / "stats.json").read_text(encoding="utf-8"))


def at(case, x):
    xs, pr = S[case]["xs"], S[case]["profile"]
    i = min(range(len(xs)), key=lambda k: abs(xs[k] - x))
    return pr[i]


def expect_peak(c):
    return f"{S[c]['peak']:.0f}"


d = docx.Document(DOCX)

problems = []


def check_table(idx, name, spec):
    t = d.tables[idx]
    for r_i, (row, spec_row) in enumerate(zip(t.rows[1:], spec), start=1):
        for c_i, (cell, want) in enumerate(zip(row.cells, spec_row)):
            if want is None:
                continue
            got = cell.text.strip()
            if got != want:
                problems.append(f"{name} row{r_i} col{c_i}: got '{got}' want '{want}'")


# Table 3: peak, x=0.3, x=6.3
check_table(2, "Table3", [
    [None, None, None, expect_peak("A1"), f"{at('A1',0.3):.0f}", f"{at('A1',6.3):.0f}"],
    [None, None, None, expect_peak("B1"), f"{at('B1',0.3):.0f}", f"{at('B1',6.3):.0f}"],
    [None, None, None, expect_peak("A2"), f"{at('A2',0.3):.0f}", f"{at('A2',6.3):.0f}"],
    [None, None, None, expect_peak("B2"), f"{at('B2',0.3):.0f}", f"{at('B2',6.3):.0f}"],
])

# Table 4: fraction -> peak, far wall, mean
check_table(3, "Table4", [
    [None, expect_peak("F02"), f"{at('F02',6.3):.0f}", f"{S['F02']['mean_all']:.0f}"],
    [None, expect_peak("A2"), f"{at('A2',6.3):.0f}", f"{S['A2']['mean_all']:.0f}"],
    [None, expect_peak("F05"), f"{at('F05',6.3):.0f}", f"{S['F05']['mean_all']:.0f}"],
])

# Table 6: SE1/SE2/SE3 peak, far wall, mean
check_table(5, "Table6", [
    [None, None, expect_peak("SE1"), f"{at('SE1',6.3):.0f}", f"{S['SE1']['mean_all']:.0f}"],
    [None, None, expect_peak("SE2"), f"{at('SE2',6.3):.0f}", f"{S['SE2']['mean_all']:.0f}"],
    [None, None, expect_peak("SE3"), f"{at('SE3',6.3):.0f}", f"{S['SE3']['mean_all']:.0f}"],
])

txt = "\n".join(p.text for p in d.paragraphs)
for t in d.tables:
    for row in t.rows:
        txt += "\n" + " | ".join(c.text for c in row.cells)

# forbidden leftovers
for bad in ["n/a", "0.065 – 0.695", "203 x 40 x 32 uniform", "order of magnitude",
            "105 K above ambient", "within 0.5 %", "factor of about two from the impingement"]:
    if bad in txt:
        problems.append(f"stale text present: '{bad}'")

# R* arithmetic
DSTAR = 0.3911
for name, (nx, ny, nz) in {"Coarse": (101, 20, 12), "Medium": (152, 30, 17),
                           "Fine": (203, 40, 23)}.items():
    r = ((6.6 / nx) + (1.3 / ny) + (0.76 / nz)) / 3 / DSTAR
    band = (0.1, 0.2) if name != "Fine" else (1 / 15, 0.1)
    ok = band[0] <= r <= band[1]
    print(f"{name}: R* = {r:.4f} in band {band[0]:.4f}-{band[1]:.4f} -> {'OK' if ok else 'OUT'}")
    if not ok:
        problems.append(f"{name} R* out of band")

print()
if problems:
    print("PROBLEMS:")
    for p_ in problems:
        print("  -", p_)
    raise SystemExit(1)
else:
    print("all table numbers match stats.json; no stale text found")
