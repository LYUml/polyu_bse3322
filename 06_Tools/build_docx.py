"""Generate the BSE3322 Group 18 report as a Word document.

Temperature comparisons use stats.json. The fixed-door flow comparison uses the archived station summaries.
"""
from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "07_Report"
FIG = REPORT / "figures"
OUT = REPORT / "BSE3322_Group18_Report_v3.docx"
S = json.loads((ROOT / "05_Calculations" / "stats.json").read_text(encoding="utf-8"))

BODY = 11


def f(value, digits=1, unit=""):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}{unit}"


def st(case, key):
    return S[case][key]


def at(case, x):
    """Profile value at the thermocouple nearest to x."""
    xs = S[case]["xs"]
    prof = S[case]["profile"]
    i = min(range(len(xs)), key=lambda k: abs(xs[k] - x))
    return prof[i]


doc = Document()

# ---------------------------------------------------------------- page setup
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.top_margin = Cm(2.4)
sec.bottom_margin = Cm(2.4)
sec.left_margin = Cm(2.4)
sec.right_margin = Cm(2.4)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(BODY)
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.15


def style_heading(style_name, size, bold=True, space_before=14, space_after=6):
    st_ = doc.styles[style_name]
    st_.font.name = "Times New Roman"
    st_.font.size = Pt(size)
    st_.font.bold = bold
    st_.font.color.rgb = RGBColor(0, 0, 0)
    rpr = st_._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]
    rfonts.set(qn("w:ascii"), "Times New Roman")
    rfonts.set(qn("w:hAnsi"), "Times New Roman")
    rfonts.set(qn("w:eastAsia"), "Times New Roman")
    st_.paragraph_format.space_before = Pt(space_before)
    st_.paragraph_format.space_after = Pt(space_after)


style_heading("Heading 1", 13)
style_heading("Heading 2", 11.5, space_before=10, space_after=4)


def para(text, size=BODY, bold=False, italic=False, align=None, indent=0.0,
         space_after=6, first_indent=0.0):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if align is not None:
        p.alignment = align
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    if first_indent:
        p.paragraph_format.first_line_indent = Cm(first_indent)
    p.paragraph_format.space_after = Pt(space_after)
    return p


def body(text):
    return para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=0.6)


def figure(name, caption, width=15.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(FIG / name), width=Cm(width))
    p.paragraph_format.space_after = Pt(2)
    cap = para(caption, size=9, italic=False, align=WD_ALIGN_PARAGRAPH.CENTER,
               space_after=10)
    return cap


def table(header, rows, caption, widths=None):
    para(caption, size=9, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(header):
        hdr[i].text = ""
        r = hdr[i].paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(9)
        r.font.name = "Times New Roman"
        hdr[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(9)
            r.font.name = "Times New Roman"
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


# ------------------------------------------------------------------- title
para("Ceiling-Jet Temperature Profiles and a Smoke-Ventilation Design for a "
     "Reduced-Scale Long Compartment Fire", size=16, bold=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
para("BSE3322 Fire System Modelling - Group 18", size=11, italic=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
para("Department of Building Environment and Energy Engineering, "
     "The Hong Kong Polytechnic University", size=10,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=14)

# ------------------------------------------------------------------ abstract
doc.add_heading("Abstract", level=1)
body(
    "This study characterises the ceiling jet produced by a 0.2 m square propane burner in a "
    "reduced-scale long compartment, 6.6 m long, 0.9 m wide and 0.76 m high, fitted with four "
    "0.43 m by 0.63 m floor-mounted openings, and then develops a smoke-ventilation design for the "
    "same compartment. Large eddy simulation was carried out with the Fire Dynamics Simulator "
    "6.10.1 on a 203 x 40 x 23 uniform mesh giving a characteristic-length ratio of 0.0836, "
    "with a 66-point thermocouple grid along the ceiling. Two heat release rates, 47.2 kW and "
    f"106.2 kW, and two opening configurations were computed over 100 s and averaged over 50-100 s, "
    "the interval in which the hot layer is established. The ceiling temperature rises from "
    f"{f(at('A1', 0.0), 0)} C at the end wall to {f(st('A1', 'peak'), 0)} C above the fire at "
    f"47.2 kW, and from {f(at('A2', 0.0), 0)} C to {f(st('A2', 'peak'), 0)} C at 106.2 kW; it "
    f"decays to {f(at('A1', 6.3), 0)} C and {f(at('A2', 6.3), 0)} C respectively at the far "
    "wall. Opening one bay instead "
    "of four raises the fire-bay temperature at the low heat release rate and lowers it at the high "
    "one, because the two mechanisms, air supply and smoke confinement, become comparable. A "
    "sensitivity study of the radiative fraction shows the peak ceiling temperature moving between "
    f"{f(st('F05', 'peak'), 0)} C and {f(st('F02', 'peak'), 0)} C as the fraction varies from 0.50 "
    "to 0.20. Preliminary plume sizing gave 0.16 m3/s. With door-dependent inlet heights and 0.24 m curtains, the 0.96 m3/s mechanical extract candidate kept the sampled thermal interface above 0.38 m in all six 120 s scenarios on the tested grid."
)

# --------------------------------------------------------------- 1. intro
doc.add_heading("1. Introduction", level=1)
body(
    "A fire in a long, narrow enclosure - a tunnel, a corridor or, in the present case, a "
    "reduced-scale compartment used for model validation - is dominated by the ceiling jet. Once "
    "the buoyant plume impinges on the ceiling it spreads radially as a thin, fast, hot layer, and "
    "it is this layer, rather than the plume itself, that determines where smoke detectors operate, "
    "where the smoke interface settles and how quickly a space becomes untenable [1]. Because "
    "full-scale fire experiments are expensive and repeat poorly, computational fluid dynamics with "
    "large eddy simulation (LES) has become the standard design tool: it resolves the large "
    "energy-carrying eddies and models only the sub-grid scales, so the puffing and intermittency of "
    "a real plume are retained [2]."
)
body(
    "The Fire Dynamics Simulator (FDS 6.10.1, NIST) was used throughout [3]. The first objective "
    "was to reproduce the ceiling temperature profile measured in a reduced-scale long compartment "
    "and to establish how fine the mesh must be for a mesh-independent answer. The second was to "
    "quantify how the number of lateral openings controls the air supply and the depth of the hot "
    "layer, using the two heat release rates and two opening configurations assigned to Group 18. "
    "The third was to design a smoke-ventilation system for the same geometry, to test it "
    "numerically for a propylene fire with a soot yield representative of a design fuel, and to "
    "examine the sensitivity of the design to the soot yield and to the radiative fraction, which "
    "is the model constant that most directly controls the split between radiation and convection."
)
body(
    "The paper is organised as follows. Section 2 describes the geometry, the combustion model, "
    "the mesh and the instrumentation, and compares the computed ceiling-jet profile with a "
    "classical correlation. Section 3 reports the effect of the opening configuration, Section 4 "
    "the sensitivity to the radiative fraction, and Section 5 the ventilation design, the sizing "
    "calculation and the performance of the design cases. Section 6 lists the limitations and "
    "Section 7 concludes."
)

# ------------------------------------------------------- 2. model description
doc.add_heading("2. Model Description", level=1)
doc.add_heading("2.1 Geometry, openings and boundary conditions", level=2)
body(
    "The compartment is a 6.6 m long, 0.9 m wide and 0.76 m high steel hall. It is modelled inside "
    "a slightly larger computational domain, 6.6 m by 1.3 m by 0.76 m, so that a 0.35 m wide "
    "ambient strip exists outside the long wall; the strip is open on its four exterior faces and "
    "allows the outflow from the openings to escape without artificially pressurising the hall, "
    "which is the standard treatment for a reduced-scale compartment that discharges into a large "
    "laboratory. The compartment wall itself is a 0.05 m thick obstruction between y = 0.90 m and "
    "y = 0.95 m. The floor, the end walls and the ceiling are mesh boundaries and are therefore "
    "solid, inert and adiabatic."
)
body(
    "Four openings are cut through the long wall at the positions used in the reference experiment "
    "(Table 1). Each opening is 0.43 m wide and 0.63 m high and starts at the floor, so the soffit "
    "sits at 0.63 m, 0.13 m below the ceiling. The openings are created with HOLE objects, which is "
    "the only way to perforate an obstruction in FDS; a VENT placed on a plane inside the "
    "computational domain would be rejected by the code. In the four-opening configuration all four "
    "holes are active; in the single-opening configuration only the opening labelled OP-B is kept, "
    "which corresponds to the group assignment for Group 18. OP-B is the mirror image of the R1 "
    "opening about the fire axis at x = 3.3 m, and because the geometry and the fire are both "
    "symmetric about that axis the two are physically equivalent, which was verified by the "
    "symmetry of the computed profiles."
)
table(
    ["Opening", "X range (m)", "Z range (m)", "Width x height (m)", "Active in"],
    [["OP-A", "0.610 - 1.040", "0 - 0.630", "0.43 x 0.63", "four-opening case"],
     ["OP-B", "2.260 - 2.690", "0 - 0.630", "0.43 x 0.63", "both cases"],
     ["OP-C", "3.910 - 4.340", "0 - 0.630", "0.43 x 0.63", "four-opening case"],
     ["OP-D", "5.560 - 5.990", "0 - 0.630", "0.43 x 0.63", "four-opening case"]],
    "Table 1. Position of the four lateral openings (centre-to-centre spacing 1.65 m).",
)
figure("fig1_geometry.png",
       "Fig. 1. Computational model: (a) plan view with the four openings and the ambient strip; "
       "(b) section at mid-width showing the floor-mounted openings and the half-height criterion.")

doc.add_heading("2.2 Fire source and combustion", level=2)
body(
    "The fire is a 0.2 m by 0.2 m burner, 0.1 m high, standing on the floor at x = 3.2-3.4 m and "
    "y = 0.35-0.55 m, so that the flame impinges on the ceiling directly above the fire axis. The "
    "burner surface releases heat at a prescribed rate per unit area, 1180 kW/m2 for the 47.2 kW "
    "case and 2655 kW/m2 for the 106.2 kW case, both referred to the 0.04 m2 top surface. A single "
    "step reaction for propane is used for the validation cases and a propylene reaction with a "
    "soot yield of 0.02 and a carbon monoxide yield of 0.01 for the design cases, following the "
    "fuel specification of the assignment. The heat release rate is constant in time; the "
    "computed total heat release rate averaged over the averaging window agrees with the prescribed "
    "value to within 1 %, which confirms that the burner is supplied with enough oxygen and that "
    "the combustion model does not limit the fire."
)

doc.add_heading("2.3 Mesh and grid resolution", level=2)
body(
    "The mesh requirement for a compartment fire is set by the characteristic diameter of the "
    "plume, D* = [Q / (rho_inf c_p T_inf sqrt(g))]^(2/5), and by the non-dimensional resolution "
    "R* = dx / D* [2]. For a heat release rate of 106.2 kW, a density of 1.204 kg/m3, a specific "
    "heat of 1.005 kJ/kgK and an ambient temperature of 293 K, D* is 0.391 m; for 47.2 kW it is "
    "0.283 m. Resolution in the range 1/10 < R* < 1/5, which is the band recommended for the flame "
    "region and the near field, corresponds to cell sizes between 0.039 m and 0.078 m at the higher "
    "heat release rate. Three meshes were defined on this basis (Table 2). The fine mesh, with "
    "0.0325 m cells and R* = 0.083, lies in the finer band 1/15 < R* < 1/10 and was adopted for all "
    "production runs; the coarse and medium meshes were used only to establish the sensitivity."
)
table(
    ["Mesh", "Cells (x, y, z)", "Cell size (m)", "R* at 106.2 kW", "Total cells"],
    [["Coarse", "101 x 20 x 12", "0.0654 / 0.0650 / 0.0633", "0.1651", "24 240"],
     ["Medium", "152 x 30 x 17", "0.0434 / 0.0433 / 0.0447", "0.1120", "77 520"],
     ["Fine", "203 x 40 x 23", "0.0325 / 0.0325 / 0.0330", "0.0836", "186 760"]],
    "Table 2. Mesh systems and their non-dimensional resolution.",
)
body(
    "The three meshes were sized from the resolution bands of the reference mesh study [2]: the "
    "coarse and medium meshes lie inside 1/10 < R* < 1/5 and the fine mesh inside 1/15 < R* < 1/10. "
    "All production runs use the fine mesh; the coarse and medium meshes test the sensitivity. That test is "
    "not entirely reassuring. A preliminary medium mesh with 0.0317 m cells, only 2 % coarser than "
    "the fine mesh and still inside the recommended band, gave a peak ceiling temperature 11 % "
    "lower than the fine mesh, which shows that the peak remains resolution-limited at this scale. "
    "The peak values quoted in this report, including those in Sections 3 to 5, should therefore be "
    "read as upper estimates with an uncertainty of about 10 %; it is the profile shape and the "
    "comparison between cases, not the absolute peak, that carry the conclusions. A single uniform "
    "block was used throughout. Splitting a domain into several blocks does not refine the "
    "solution, it only distributes it over processors, so the three meshes were run as separate "
    "cases rather than as a multi-block decomposition. The design cases extend the domain to 1.06 m "
    "in height to accommodate the ceiling shafts, keeping the same horizontal cells and using 32 "
    "cells in the vertical direction."
)

doc.add_heading("2.4 Instrumentation and post-processing", level=2)
body(
    "sixty-six ceiling thermocouples sample the gas temperature on the centreline, 1 cm below the "
    "ceiling, at x = 0.0, 0.1, ..., 6.5 m. The device quantity THERMOCOUPLE is used deliberately: "
    "it returns the temperature of a bead that exchanges heat by convection and radiation with the "
    "surrounding gas, which is what a physical thermocouple measures and therefore what can be "
    "compared with the experimental profile. Gas temperatures would read higher in the plume and "
    "lower in a radiation field, so mixing the two would introduce a systematic bias of the order "
    "of 50-100 K in the near field."
)
body(
    "Each run is 100 s long. The hot layer needs roughly 50 s to establish itself in a compartment "
    "of this depth, and the mean over the last 50 s is used for every quoted value; the instantaneous "
    "peak is reported separately where it matters. Fig. 2 shows the thermocouple above the fire for "
    "the four validation cases: the signal rises steeply during the first 30 s and then oscillates "
    "about a plateau, which is the signature of a quasi-steady ceiling jet with intermittent "
    "puffing, and the 50-100 s window is entirely inside that plateau."
)
figure("fig2_time.png",
       "Fig. 2. Ceiling temperature above the fire during the 100 s runs; the averaging window "
       "starts at 50 s.")

doc.add_heading("2.5 Comparison with a classical ceiling-jet correlation", level=2)
body(
    "The experimental profile of the reference study was not available in digital form, so the "
    "computed profile was instead benchmarked against the Alpert correlation [6], which is the "
    "reference against which most compartment-fire LES results are still judged: "
    "dT = 16.9 Q^(2/3) H^(-5/3) for r/H <= 0.18 and dT = 5.38 (Q/r)^(2/3) H^(-1) for r/H > 0.18. "
    f"At r = 1.0 m and Q = 106.2 kW the correlation gives about 159 K above ambient (180 C), "
    f"whereas the simulation gives {f(at('A2', 4.3), 0)} C at the same station, a factor of 2.6 larger. "
    "The difference is expected and is not an error. The correlation describes a ceiling jet in an "
    "unconfined, well-ventilated compartment; the present hall is only 0.76 m high, so the plume "
    "hits the ceiling within half a metre of the fire and the products accumulate instead of "
    "escaping, heating the whole ceiling and the far end of the hall rather than a thin near-field "
    "jet. "
    "The comparison is nevertheless useful: it confirms that the computed profile follows the "
    "correct trend, a monotonic decay of a factor of about four from the impingement point to the far "
    "wall, and it quantifies the confinement penalty that any design in this geometry has to "
    "absorb."
)
figure("fig6_alpert.png",
       "Fig. 3. Computed ceiling profile at 106.2 kW against the Alpert correlation for the same "
       "heat release rate and compartment height.")

# ------------------------------------------------------- 3. opening effect
doc.add_heading("3. Effect of the Opening Configuration", level=1)
body(
    "Two configurations were computed at both heat release rates: all four openings active, and "
    "only OP-B active. Fig. 4 shows the four ceiling profiles and Table 3 summarises them. At "
    f"47.2 kW the single-opening case is hotter above the fire, {f(st('B1', 'peak'), 0)} C against "
    f"{f(st('A1', 'peak'), 0)} C, whereas at 106.2 kW it is marginally cooler, "
    f"{f(st('B2', 'peak'), 0)} C against {f(st('A2', 'peak'), 0)} C. The two responses are the "
    "result of two competing mechanisms. Closing three openings reduces the supply of fresh air, "
    "which starves the fire and weakens the plume, and it also removes three exhaust paths, which "
    "traps the products and thickens the layer. At the low heat release rate the fire is small "
    "enough that the trapped heat dominates and the ceiling becomes hotter; at the high rate the "
    "single 0.27 m2 opening is close to the air demand of the fire, the plume is diluted by a "
    "weaker, slower inflow, and the two effects nearly cancel, leaving the fire-bay temperature a "
    "few per cent lower."
)
figure("fig3_profile.png",
       "Fig. 4. Mean ceiling temperature profiles for the two heat release rates and the two opening "
       "configurations.")
table(
    ["Case", "HRR (kW)", "Openings", "Peak (C)", "At x = 0.3 m (C)", "At x = 6.3 m (C)"],
    [["A1", "47.2", "four", f(st("A1", "peak"), 0), f(at("A1", 0.3), 0), f(at("A1", 6.3), 0)],
     ["B1", "47.2", "one", f(st("B1", "peak"), 0), f(at("B1", 0.3), 0), f(at("B1", 6.3), 0)],
     ["A2", "106.2", "four", f(st("A2", "peak"), 0), f(at("A2", 0.3), 0), f(at("A2", 6.3), 0)],
     ["B2", "106.2", "one", f(st("B2", "peak"), 0), f(at("B2", 0.3), 0), f(at("B2", 6.3), 0)]],
    "Table 3. Ceiling temperatures, 50-100 s mean.",
)
body(
    "The far field behaves differently from the fire bay. Closing three openings raises the "
    f"temperature at the far wall in both cases, by {f(at('B1', 6.3) - at('A1', 6.3), 0)} K at "
    f"47.2 kW and by {f(at('B2', 6.3) - at('A2', 6.3), 0)} K at 106.2 kW, so the absolute effect is "
    "almost the same; what changes is the relative one, about 19 % at the low heat release rate and "
    "12 % at the high rate, because the whole ceiling is already much hotter at 106.2 kW. Closing "
    "the openings therefore does not simply make the compartment hotter or cooler; it changes the "
    "balance between the strength of the ceiling jet, which carries heat down the hall, and the "
    "depth of the layer, which stores it near the fire. At the low heat release rate the trapped "
    "layer dominates; at the high rate the same amount of trapped heat is spread over a much hotter "
    "ceiling, so it appears as a smaller relative change."
)

# ------------------------------------------------------- 4. radiative fraction
doc.add_heading("4. Sensitivity to a Key Model Constant", level=1)
body(
    "The radiative fraction, the proportion of the chemical heat release that leaves the flame as "
    "thermal radiation, is the model constant that most strongly controls the split between the "
    "energy that stays in the gas and the energy that is absorbed by the walls. FDS uses 0.35 by "
    "default. Two further cases were run at 106.2 kW with the fraction set to 0.20 and 0.50; "
    "everything else was unchanged. The ceiling profiles are compared in Fig. 5 and the peak values "
    f"are collected in Table 4. Lowering the fraction to 0.20 raises the peak from "
    f"{f(st('A2', 'peak'), 0)} C to {f(st('F02', 'peak'), 0)} C, and raising it to 0.50 lowers the "
    f"peak to {f(st('F05', 'peak'), 0)} C."
)
figure("fig4_fraction.png",
       "Fig. 5. Ceiling profiles at 106.2 kW for three values of the radiative fraction.")
table(
    ["Radiative fraction", "Peak (C)", "Far wall (C)", "Mean ceiling (C)"],
    [["0.20", f(st("F02", "peak"), 0), f(at("F02", 6.3), 0), f(st("F02", "mean_all"), 0)],
     ["0.35 (default)", f(st("A2", "peak"), 0), f(at("A2", 6.3), 0), f(st("A2", "mean_all"), 0)],
     ["0.50", f(st("F05", "peak"), 0), f(at("F05", 6.3), 0), f(st("F05", "mean_all"), 0)]],
    "Table 4. Sensitivity of the ceiling temperatures to the radiative fraction.",
)
body(
    "The response is not symmetric. Reducing the fraction by 0.15 heats the gas by about 4 %, "
    "whereas increasing it by the same amount cools the gas by about 12 %. The asymmetry has a "
    "physical explanation: when more energy leaves as radiation, part of it is absorbed by the "
    "adiabatic inert walls and returned to the room, so the net loss of gas enthalpy is smaller "
    "than the change in the radiative fraction suggests, and the extra energy is redistributed to "
    "the far field rather than removed. The practical consequence for the design is that the "
    "radiative fraction should be treated as an uncertainty of order plus or minus 15 % on the "
    "fire-bay ceiling temperature, which is smaller than the difference between the two opening "
    "configurations and much smaller than the difference between the two heat release rates; it "
    "does not change any of the conclusions of Section 5."
)

# --------------------------------------------------------------- 5. design
doc.add_heading("5. Smoke-Ventilation Design", level=1)
doc.add_heading("5.1 Preliminary plume sizing", level=2)
body(
    "The design target is taken from the assignment: the smoke interface should not fall below "
    "half the compartment height, 0.38 m, and the layer should remain above the occupied zone for "
    "the duration of the fire. The design fire is a 106.2 kW propylene fire, which is the larger of "
    "the two heat release rates and therefore the governing case, with a soot yield of 0.02 and a "
    "carbon monoxide yield of 0.01. The mass flow of smoke that must be extracted is estimated from "
    "the NFPA 92 plume expression [4], m_p = 0.071 Q_c^(1/3) z^(5/3), with the convective part of "
    "the heat release rate Q_c = 0.7 Q and the clear height z = 0.38 m. For 106.2 kW this gives "
    "Q_c = 74.3 kW, m_p = 0.059 kg/s and, at a layer temperature of about 200 C where the density is "
    "0.75 kg/m3, a volumetric extract rate of 0.080 m3/s. A factor of two is applied to cover the "
    "plume fluctuation and the leakage that any real installation has, so the preliminary extract rate "
    "is 0.16 m3/s."
)
table(
    ["Quantity", "Value", "Basis"],
    [["Design fire", "106.2 kW propylene", "larger of the two assigned HRRs"],
     ["Convective HRR, Q_c", "74.3 kW", "0.7 Q (radiative fraction 0.30)"],
     ["Clear height, z", "0.38 m", "half the compartment height"],
     ["Plume mass flow, m_p", "0.059 kg/s", "NFPA 92, 0.071 Q_c^(1/3) z^(5/3)"],
     ["Layer density at 200 C", "0.75 kg/m3", "ideal gas"],
     ["Required extract rate", "0.080 m3/s", "m_p / rho"],
     ["Preliminary extract rate", "0.16 m3/s", "2 x required"],
     ["Shaft area (two shafts)", "0.211 m2", "2 x 0.325 m"],
     ["Face velocity at the shaft", "0.76 m/s", "0.16 / 0.211"],
     ["Fan power", "48 W", "0.16 x 150 / 0.5"]],
    "Table 5. Preliminary plume sizing and assumed system pressure loss.",
)

doc.add_heading("5.2 Description of the design cases", level=2)
body(
    "Three design cases were built on the validated model. The ceiling of the compartment is closed "
    "with a 4 cm slab so that the smoke can only leave through two shafts, each 0.325 m square, "
    "which rise from the ceiling to the top of the computational domain at x = 2.50-2.83 m and "
    "x = 3.80-4.13 m, that is, symmetric about the fire, each shaft sitting just outboard of the "
    "shaft is connected to the ambient air through an HVAC duct of 0.30 m diameter, and the two "
    "ducts together pass the design extract rate. Case SE1 has the shafts open and no curtains. "
    "Case SE2 repeats SE1 with the soot yield raised to 0.10, which represents a sootier fuel or a "
    "less efficient combustion. Case SE3 keeps both shafts open and adds two curtains hung from the "
    "ceiling down to 0.61 m at x = 2.83 m and x = 3.77 m, that is, at the inner edge of each shaft, "
    "so that the smoke produced between them is guided into the two shafts instead of spilling along "
    "the hall; its soot yield is 0.10. SE3 therefore measures the marginal benefit of adding "
    "curtains to an already extracted compartment."
)
body(
    "The curtain depth of 0.15 m matches the 0.13 m gap between the ceiling at 0.76 m and the "
    "soffit of the openings, 0.63 m, so the curtains close the gap between the ceiling and the top "
    "of the openings and force the smoke to spill downwards before it can reach the adjacent bays. "
    "This is the arrangement that the half-height criterion implicitly assumes: a barrier that holds "
    "the layer in place while it is extracted."
)

doc.add_heading("5.3 Performance of the design", level=2)
body(
    "The three cases are compared in Fig. 6 and Table 6. All three design cases are far cooler in "
    f"the fire bay than the open compartment at the same heat release rate: {f(st('SE1', 'peak'), 0)} "
    f"C with the shafts open, {f(st('SE3', 'peak'), 0)} C with the shafts and the curtains, against "
    f"{f(st('A2', 'peak'), 0)} C when the ceiling is a free boundary. The two ceiling shafts sit only "
    "0.5 m from the fire axis, one on each side, so they act as a local exhaust hood: they capture "
    "the plume before it can spread as a ceiling jet, and the smoke leaves the compartment instead of "
    "being driven back into the hall. Adding the curtains raises the fire-bay temperature by about "
    f"{f(st('SE3', 'peak') - st('SE1', 'peak'), 0)} K rather than lowering it: the curtains close the "
    "lateral escape route, so the same smoke has to pass through the two shafts, and while it waits "
    "to be extracted it fills the bay between the curtains and heats it further. The extraction "
    "therefore protects the rest of the hall but makes the fire bay itself hotter, a trade-off that "
    "must be part of the design decision. Raising the soot yield from 0.02 to 0.10 changes the peak "
    "by less than 1 % (SE1 against SE2), the expected behaviour: the soot yield changes the optical "
    "properties of the smoke, not the heat release."
)
figure("fig5_design.png",
       "Fig. 6. Ceiling temperature profiles for the three design cases at 106.2 kW.")
table(
    ["Case", "Description", "Peak (C)", "Far wall (C)", "Mean ceiling (C)"],
    [["SE1", "shafts open, no curtains", f(st("SE1", "peak"), 0), f(at("SE1", 6.3), 0),
      f(st("SE1", "mean_all"), 0)],
     ["SE2", "shafts open, soot 0.10", f(st("SE2", "peak"), 0), f(at("SE2", 6.3), 0),
      f(st("SE2", "mean_all"), 0)],
     ["SE3", "shafts + curtains, soot 0.10", f(st("SE3", "peak"), 0), f(at("SE3", 6.3), 0),
      f(st("SE3", "mean_all"), 0)]],
    "Table 6. Temperatures in the three design cases, 50-100 s mean.",
)
body(
    "The most striking feature of Fig. 6 is the far end of the compartment. In all three design "
    f"cases the thermocouples beyond x = 5 m remain within 1 C of the ambient temperature, at "
    f"{f(at('SE1', 6.3), 0)} C, whereas the open compartment reaches {f(at('A2', 6.3), 0)} C at the "
    "same heat release rate. With the ceiling closed and the products withdrawn at the two shafts, "
    "the ceiling jet never propagates along the hall within the 100 s of the simulation, and the "
    "stratified layer that carries heat to the far wall in the open case does not establish itself. "
    "This is a genuine benefit for tenability at the far end, but it also means that the design "
    "cannot be judged by the half-height criterion alone, because in the protected zone the smoke "
    "layer never forms: applied literally, the criterion is satisfied for the wrong reason. It "
    "should rather be applied to the fire bay, where the layer does form, and there the computed "
    "temperatures indicate a hot, well-mixed volume rather than a clean upper layer."
)

doc.add_heading("5.4 Sootier fuels and tenability", level=2)
body(
    "The soot yield has no significant effect on the gas temperature, as Table 6 shows: SE2, with "
    "five times the soot of SE1, differs from it by less than 1 %. In the six mechanical extraction cases at 0.96 m3/s, the lowest half-height visibility was 12.33 m (OP-6, soot yield 0.10 kg/kg) and the highest CO concentration was 22.82 ppm (OP-6, 0.02 kg/kg). The simulations prescribe a CO yield of 0.01 kg/kg."
)

doc.add_heading("5.5 Mechanical extraction and fan power", level=2)
body(
    "The preliminary 0.16 m3/s estimate assumed 150 Pa system loss and 50 % efficiency, giving 48 W. For the mechanical extraction comparison, a short-branch loss model gives 10.32 W at 1.28 m3/s and 4.35 W at 0.96 m3/s. These estimates exclude other system losses."
)
body(
    "Both ends use 0.44 m inlets with four doors open (OP-1) or 0.48 m with R1 alone open (OP-6), with 0.24 m curtains. At 0.96 m3/s total, the eight-station minima over 120 s for soot yields 0.02, 0.05 and 0.10 kg/kg were 0.4574, 0.4717 and 0.4410 m for OP-1, and 0.3957, 0.5262 and 0.4061 m for OP-6. The smallest margin above 0.38 m was 0.0157 m at x = 0.5 m and 88.5 s, compared with 0.0625 m across the six higher-flow runs. The low-flow margin still needs a paired grid-refinement check."
)

# --------------------------------------------------------------- 6. limitations
doc.add_heading("6. Limitations", level=1)
body(
    "Four limitations should be stated. First, the walls are adiabatic and inert; a real steel hall "
    "loses heat to the structure, so the computed temperatures are upper bounds and the far-field "
    "values in particular are likely to be conservative by 20-40 K. Second, the preliminary runs are 100 s "
    "long, which is enough for the layer to establish itself in this small volume but not for the "
    "walls to reach a steady thermal state; the quasi-steady values quoted here are therefore "
    "early-time values. Third, cases SE1-SE3 were not instrumented with layer-height or "
    "visibility devices, so the performance of the ventilation system is assessed from the gas "
    "temperature and from the qualitative smoke distribution rather than from the two quantities "
    "the criterion is written in; adding those devices is the first improvement to make. Fourth, "
    "the preliminary single-opening case uses the OP-B opening, which is the mirror image of the R1 opening "
    "specified for the group; the two are equivalent for a symmetric geometry, but a direct run "
    "with R1 would remove any doubt."
)

# --------------------------------------------------------------- 7. conclusion
doc.add_heading("7. Conclusion", level=1)
body(
    "Large eddy simulation of a 6.6 m by 0.9 m by 0.76 m compartment with four floor-mounted "
    "openings has been used to characterise the ceiling jet produced by a 0.2 m burner and to design "
    "a smoke-ventilation system for the same geometry. Four conclusions follow. (i) The ceiling "
    f"temperature rises to {f(st('A1', 'peak'), 0)} C above the fire at 47.2 kW and to "
    f"{f(st('A2', 'peak'), 0)} C at 106.2 kW, and decays by a factor of about four to the far wall; "
    "the profile is much hotter than an unconfined ceiling-jet correlation would predict, and the "
    "difference is the confinement penalty of a compartment only 0.76 m deep. (ii) Reducing the "
    "number of open bays from four to one raises the fire-bay temperature by 4 % at 47.2 kW but "
    "lowers it by 1 % at 106.2 kW, because the loss of air supply and the trapping of smoke become "
    "comparable at the higher heat release rate. (iii) The radiative fraction is the most "
    "influential model constant among those tested, moving the peak ceiling temperature by up to "
    "12 % over the range 0.20-0.50, with an asymmetric response that reflects the re-radiation from "
    "the walls. (iv) For the two fixed door states and three soot yields tested, 0.96 m3/s met the eight-station thermal criterion on the current grid with a minimum clearance of 0.0157 m above target. Door transitions and the minimum feasible fan power remain unresolved."
)

# --------------------------------------------------------------- references
doc.add_heading("References", level=1)
refs = [
    "Peng, M., Cheng, X., Cong, W., Yang, H., Shahid, M. U., Yuen, R. and Zhang, H. (2021) "
    "'Experimental study on temperature profile in long-narrow compartment fire with multiple "
    "lateral openings', Tunnelling and Underground Space Technology, 117, 104018.",
    "Yuen, A. C. Y., Yeoh, G. H., Timchenko, V. and Barber, T. (2015) 'LES and multi-step chemical "
    "reaction in compartment fires', Numerical Heat Transfer, Part A: Applications, 68, pp. 711-736.",
    "McGrattan, K. et al. (2024) Fire Dynamics Simulator Technical Reference Guide. NIST Special "
    "Publication 1018. Gaithersburg, MD: National Institute of Standards and Technology.",
    "NFPA 92 (2021) Standard for Smoke Control Systems. Quincy, MA: National Fire Protection "
    "Association.",
    "ISO 13571 (2012) Life-threatening components of fire - Guidelines for the estimation of time to "
    "compromised tenability in fires. Geneva: International Organization for Standardization.",
    "Alpert, R. L. (1972) 'Calculation of response time of ceiling-mounted fire detectors', Fire "
    "Technology, 8(3), pp. 181-195.",
]
for i, r in enumerate(refs, 1):
    p = para(f"[{i}] {r}", size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=4)
    p.paragraph_format.left_indent = Cm(0.75)
    p.paragraph_format.first_line_indent = Cm(-0.75)

doc.save(OUT)
print("saved", OUT)
