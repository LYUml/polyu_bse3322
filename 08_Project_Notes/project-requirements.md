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

The design brief specifies three soot yields. Group 18 tests each under both OP-1 (four open doorways) and OP-6 (only R1 open) to assess sensitivity to make-up air and identify the limiting scenario. Group 18 selected this six-case design matrix. The brief explicitly requests explanation of doorway effects in the propane investigation and asks the group to stipulate critical propylene scenarios.

## Pending information / source ambiguities

- Report deadline, deliverable format, marking rubric and team allocation. Presentation schedule lists Group 18 on 2026-11-25, 08:30-09:00, Zone 4 (not a confirmed report deadline).
- Peng Fig. 1 and the accompanying text support the 0.63 m opening height, 0.25 m square propane burner and measurement arrays. See the [source review](01_Group18_任务与证据梳理.md) for the geometry and coordinate mapping.
- Peng gives a 15 mm enclosure thickness. The wall sensitivity case uses proxy density, conductivity and specific heat. Experimental values for these three properties remain unverified. [Wall-case input and material provenance](../07_Report/Group18_review_draft.md#model-geometry-and-mesh)
- Experimental time windows, ambient conditions and boundary/material properties.
- Brief mentions “nanofluid concentration,” apparently unrelated to this fire task: retain as a source ambiguity until clarified.
- Exact meaning of “inlet and outlet” temperature/velocity and smoke-layer acceptance measurement method.
- [Validation and design records](03_Group18_验收记录.md) document completed simulations. The [seven full OP6 design results](../05_Calculations/tall_makeup_op6_completed_scenarios.csv) include the 0.32 m curtain. Each tested curtain depth has a negative margin in at least one scenario. Later door-dependent presets met the eight-station thermal target on the original design grid in all six scenarios at both tested flows (see the six-scenario evidence below). The [independent PINN check](../09_PINN_Layer/README.md) records a false pass for the deeper curtain.

## Literature named in the brief

1. Peng et al. (2021), Experimental study on temperature profile in long-narrow compartment fire with multiple lateral openings. Tunnelling and Underground Space Technology, 117, 104018.
2. Yuen et al. (2015), LES and multi-step chemical reaction in compartment fires. Numerical Heat Transfer; Part A: Applications, 68, 711–736.

Both full texts are archived. The [source review](01_Group18_任务与证据梳理.md) identifies the figures and sections used for temperature validation and numerical methodology.

### Experimental test numbers and the assignment count

Peng Table 1 gives eight HRRs per opening configuration. Both OP-1 (tests 1–8) and OP-6 (tests 41–48) list 11.8, 23.6, 35.4, 47.2, 59, 70.8, 88.5 and 106.2 kW. Reading each range in listed order implies tests 4 and 8 for OP-1, and 44 and 48 for OP-6, at the two Group 18 HRRs. This mapping is inferred from the table order. The methods paragraph prints 45.2 kW where the experimental table and assignment give 47.2 kW. The project uses 47.2 kW as specified in the brief. The experimental ranges explain the eight original tests per opening configuration. The brief's own eight-case counting rule remains unresolved. [Peng experimental matrix](../02_References/02_Papers/Peng_2021_Temperature_Profile_Multiple_Lateral_Openings.pdf) · [Assignment Table 1](../01_Assignment_Brief/Project_Topic_1B_Smoke_Extraction.pdf)

## Human review inventory (2026-11-22)

The [report figure directory](../07_Report/) contains the Peng ceiling temperature profiles, four coarse-grid propane validation plots (OP-1 and OP-6 at both HRRs), and one OP-6 curtain/soot minimum-height plot. Use the coarse-grid captions when reviewing those four figures. The OP-1 106.2 kW fine grid completed the 90–120 s comparison at 51 stations, with a mean error of −75.0 K and RMSE of 79.9 K. The corresponding 47.2 kW fine-grid RMSE is 176.2 K and mean error is −175.5 K. [Low-power metrics](../05_Calculations/op1_47_fine_90_120.json) [High-power fine-grid figure](../07_Report/op1_106_fine_validation.png) · [Formal metrics](../05_Calculations/op1_106_fine_90_120.json)

The submission directory currently contains only its placeholder. The formal report is deferred to human review. For the design conclusion, review the full-duration station minima for each required scenario, the fan power inputs and the CO discussion alongside the [module acceptance record](03_Group18_验收记录.md). Figure availability alone does not establish design acceptance.

The propylene design review now has a complete 120 s CFD result for each of the six fixed-door scenarios at 1.28 m³/s. The same two adjustable end openings use a 0.44 m preset for OP-1 and 0.48 m for OP-6. The smallest sampled thermal layer height was 0.4425 m in OP-1 at soot yield 0.02 kg/kg. The door state is assumed fixed during each fire. At 0.96 m³/s the six original-grid runs also completed. The limiting OP-6 case at soot yield 0.02 kg/kg reached 0.3957 m, leaving 0.0157 m above target. The [flow comparison](../05_Calculations/door_preset_flow_pair.csv) supports comparing these two flows under the same branch-loss assumptions. The [paired OP-6 refinement](../03_Models/inlet48_6_0p02_0p24_0p96_z38_120.fds) produced a [screening failure](../05_Calculations/inlet48_6_0p02_0p24_0p96_z38_120_screen_failure.json) at 98.001 s, with a height of 0.37169 m at x = 6.1 m. [Six-scenario evidence](../05_Calculations/door_preset_1p28_six_scenarios.csv) · [Design figure](../07_Report/door_preset_minimum_heights.png) · [Review draft](../07_Report/Group18_review_draft.md)

The [paired 0.44 m refinement input](../03_Models/inlet44_1_0p02_0p24_1p28_z38_120.fds) tests the limiting OP-1 preset at 0.02 m vertical resolution. The [completed 120 s comparison](../05_Calculations/z38_refinement_check.csv) gives a refined eight-station minimum of 0.5879 m for this preset. The separate 0.48 m OP-1 case reached 0.5457 m. The [actual heat-release comparison](../05_Calculations/door_preset_hrr_90_120.csv) gives the delivered fire power for the six original-grid scenarios. For the smoke-layer interpretation, inspect the [thermal minimum profile](../05_Calculations/inlet44_1_0p02_0p24_1p28_120_limiting_profile.csv), the [minimum-visibility profile](../05_Calculations/inlet48_6_0p05_0p24_1p28_120_visibility_event_profile.csv) and the [outer centreplane extinction maxima over 120 s](../05_Calculations/door_preset_outer_half_height_extinction.csv). These profiles distinguish the thermal interface from local smoke near the fire. Their spatial coverage is one longitudinal plane.
