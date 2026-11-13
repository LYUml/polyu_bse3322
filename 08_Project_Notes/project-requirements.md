# Project requirements and open questions

Latest full reading: [Group 18 task and evidence review](01_Group18_任务与证据梳理.md). That review supersedes earlier unresolved source assumptions: Peng supports 0.63 m opening height and a 0.25 m square propane burner, and documents the measurement arrays. Teaching examples have several different inputs. Innovation is an extension after the required CFD work, as clarified by the user; see [PINN/MOOSAS options](02_创新方案_PINN_MOOSAS与开源复用.md).

Source: `01_Assignment_Brief/Project_Topic_1B_Smoke_Extraction.pdf` (3 pages). Text extracted; pages 1 and 2 visually reviewed on 2026-11-13. See `08_Project_Notes/project-start.md` for the current Group 18 plan and `08_Project_Notes/resources.md` for research sources.

User confirmed Group 18 on 2026-11-13. Working baseline: OP-1 plus OP-6 (R1 only), HRR 47.2 and 106.2 kW. The four configuration/HRR combinations are not a claim that only four total runs satisfy the assignment; mesh/SGS/constant studies add runs, and the brief's eight-case wording remains to be clarified.

## Confirmed brief requirements

- Mini-design project: 15% of course total; Topic B.
- Long compartment: 6.6 m long × 0.76 m high × 0.9 m wide.
- Four openings, left to right: L2, L1, R1, R2; each 0.43 m wide × 0.63 m high.
- Validation fire uses propane (C3H8).
- Study temperature, velocity, conduction, convection and radiation.
- Extend computational boundaries to capture doorway profiles.
- Conduct mesh sensitivity for OP-1, starting from characteristic-length-based mesh guidance.
- Validate ceiling temperature profiles against the experiment.
- Investigate SGS turbulence models and at least one modelling constant.
- Explain effects of doorway configurations on plume and ceiling jet.

## Case allocation requiring group number

All groups use OP-1: L1, L2, R1, R2 open.

| Group | Additional configuration | Openings |
| --- | --- | --- |
| 1–4 | OP-2 | L1, L2, R2 |
| 5–8 | OP-3 | R1, R2 |
| 9–12 | OP-4 | L1, R1 |
| 13–17 | OP-5 | L2, R2 |
| 18–22 | OP-6 | R1 |
| >22 | OP-7 | R2 |

Table 1 lists HRR 23.6 and 70.8 kW for odd groups, 47.2 and 106.2 kW for even groups. It also states “8 cases total based on group no.” Exact case counting and test-number mapping must be checked against the formatted table and experiment before generating the simulation matrix.

## Smoke extraction design

- Switch to propylene flame for design; smoke yield 0.02 and CO yield 0.01.
- Design smoke vents and curtains to keep the smoke layer from descending below half the compartment height (0.38 m above floor).
- If mechanical fans are required, evaluate required power.
- Evaluate more sooty conditions with smoke yields 0.05 and 0.1; explain design strategy and critical scenarios.
- Discuss CO generation and mitigation.

## Pending information / source ambiguities

- Report deadline, deliverable format, marking rubric and team allocation. Presentation schedule lists Group 18 on 2026-11-25, 08:30-09:00, Zone 4 (not a confirmed report deadline).
- Fig. 1 opening positions, burner dimensions/location, wall construction and measurement positions.
- Opening height has now been checked against Peng PDF page 3, both prose and high-resolution Fig. 1: 0.63 m. The earlier apparent 0.61 m was a low-resolution reading issue.
- Experimental time windows, ambient conditions and boundary/material properties.
- Brief mentions “nanofluid concentration,” apparently unrelated to this fire task: retain as a source ambiguity until clarified.
- Exact meaning of “inlet and outlet” temperature/velocity and smoke-layer acceptance measurement method.
- No model, solver installation or completed simulation is established by workspace initialization.

## Literature named in the brief

1. Peng et al. (2021), Experimental study on temperature profile in long-narrow compartment fire with multiple lateral openings. Tunnelling and Underground Space Technology, 117, 104018.
2. Yuen et al. (2015), LES and multi-step chemical reaction in compartment fires. Numerical Heat Transfer; Part A: Applications, 68, 711–736.

These papers have not yet been retrieved or reviewed in this workspace.
