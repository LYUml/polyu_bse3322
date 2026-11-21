# Group 18 review draft

## Propane ceiling-jet validation

A ventilation design based on FDS depends on the model reproducing the temperature distribution in the experimental compartment. The validation compares the OP-1 and OP-6 ceiling measurements at 47.2 and 106.2 kW with the corresponding Peng profiles. The method pairs 51 thermocouple locations, subtracts the model ambient temperature and averages each device over 90–120 s using its actual output intervals. For the OP-6 high-power adiabatic door-flow case the signed mean error is +330.31 K and the RMSE is 361.45 K. The hottest model station lies 0.70 m farther to the left of the fire than the hottest experimental station. The paired wall heat-loss comparison and the OP-1 fine-grid results are pending. [Experimental profiles](../05_Calculations/peng_fig9.csv) · [OP-6 results](../05_Calculations/op6_106_doorflow_90_120.json)

The experimental reference consists of 204 points digitized from Peng et al., Fig. 9 (51 stations for each opening and heat-release-rate combination). The primary extraction reads native PDF marker paths with pdfplumber, calibrates the axes against the plot frame and major ticks, and uses the centroid of each triangular marker. A second extraction through Poppler SVG differed by a mean absolute 0.20 K and a maximum 0.6 K on the temperature axis. These differences measure agreement between digitization methods; experimental measurement uncertainty must be considered separately. [Primary extraction script](../06_Tools/extract_peng_pdf_objects.py) · [SVG cross-check](../06_Tools/extract_peng_fig9.cjs)

The four coarse-grid comparisons use the same 51-station scoring rule. Positive bias means FDS predicted a greater temperature rise than Peng measured.

| Opening | Fire power | Mean signed error | RMSE |
|---|---:|---:|---:|
| OP-1 | 47.2 kW | −191.8 K | 192.4 K |
| OP-1 | 106.2 kW | −76.6 K | 82.0 K |
| OP-6 | 47.2 kW | +6.0 K | 33.3 K |
| OP-6 | 106.2 kW | +302.5 K | 335.5 K |

The low-power OP-6 case has the smallest bias, but its RMSE shows substantial local discrepancies. Closing openings changes the sign of the mean error at both powers. Agreement in one configuration therefore gives limited support for predictions under a different opening condition. [OP-1 low power](op1_47_coarse_validation.png) · [OP-1 high power](op1_106_coarse_validation.png) · [OP-6 low power](op6_47_coarse_validation.png) · [OP-6 high power](op6_106_coarse_validation.png)

## Inflow and outflow at R1

The R1 doorway carries flow in both directions. At 106.2 kW, the 90–120 s mean velocity at 0.14 m above the floor pointed into the compartment in both cases. The four-open-door case (OP-1) gave 0.55 m/s inward at 29.65 °C, compared with 0.69 m/s inward at 39.21 °C for the single-open-door case (OP-6). At 0.38 m, the flow pointed outwards at 0.37 m/s and 109.61 °C for OP-1, and 0.74 m/s and 473.64 °C for OP-6. These are local model predictions at the same doorway. Experimental door profiles would be needed to validate the magnitudes. [OP-1 R1 profile](../05_Calculations/op1_106_doorfield_90_120.json) · [OP-6 R1 profile](../05_Calculations/op6_106_doorfield_90_120.json)

## Propylene smoke extraction

The design criterion is a smoke-layer height of at least 0.38 m. Each candidate is screened using the minimum reported thermal layer height across eight stations over the 120 s fire. Half-height visibility, CO and vertical slices provide independent indicators within the same simulation for interpreting a thermal-layer excursion. In OP-6, a 0.24 m curtain depth, 1.00 m curtain spacing and a total exhaust of 1.28 m³/s gave a minimum height of 0.3528 m at soot yield 0.05. Increasing the spacing to 1.10 m gave 0.2983 m at the same end station by 44.0 s and triggered an early stop. The end-station slice showed a vertical temperature range of only 1.85 K. The widened layout fails the thermal screen, while the local optical evidence gives little support for a continuous smoke interface there. The 0.90 m spacing is under evaluation. [Full-duration cases](../05_Calculations/tall_makeup_op6_completed_scenarios.csv) · [Early-stop record](../05_Calculations/spacing110_6_0p05_0p24_1p28_120_screen_failure.json) · [Vertical profile](../05_Calculations/spacing110_6_0p05_0p24_1p28_120_failure_profile.csv)

Two passive roof-opening designs were tested for 120 s with OP-6, soot yield 0.02 kg/kg and 0.16 m curtains. Increasing total nominal opening area from 0.18 to 0.72 m² raised mean net upward flow through the sections below the openings from 0.292 to 0.437 m³/s. The eight-station minimum layer heights were 0.083 and 0.064 m, respectively. Both passive configurations failed the height criterion despite the increased upward flow, motivating the subsequent tests of mechanical extraction and make-up air. [Original roof openings](../05_Calculations/natural_6_0p02_0p16_0_120_stations.csv) · [Larger roof openings](../05_Calculations/natural_wide_6_0p02_0p16_0_120_stations.csv)

## Worst-case smoke yield

For OP-6 with 1.00 m curtain spacing and 1.28 m³/s total extraction, each table entry is the lowest thermal layer height recorded across eight stations during a complete 120 s run.

| Curtain depth (m) | Yield 0.02 kg/kg | Yield 0.05 kg/kg | Yield 0.10 kg/kg |
|---|---:|---:|---:|
| 0.16 | 0.263 m | 0.371 m | 0.245 m |
| 0.24 | 0.365 m | 0.353 m | 0.369 m |
| 0.32 | Untested here | Untested here | 0.267 m |

The lowest height occurred at yield 0.10 for the 0.16 m curtain and at yield 0.05 for the 0.24 m curtain. Increasing the curtain depth from 0.16 to 0.24 m improved the minimum across the three scenarios by 0.108 m, but the resulting minimum remained 0.027 m below the target. This comparison motivates testing the spacing change first at yield 0.05. The ranking applies to the stated opening and exhaust configuration. [Full-duration scenario minima](../05_Calculations/tall_makeup_op6_completed_scenarios.csv)

## Search and fan power

The first design objective is to find a nonnegative minimum layer-height margin in every agreed scenario. Only then can fan power be minimized among feasible layouts. A replay of the original 16 candidates found the largest available margin on query 7 with Bayesian optimization, query 9 for the median surrogate-GA trial and query 16 with ordered search. Even the largest margin was negative, so this experiment supports a comparison of search order only. For the wider exhaust openings, the two short branches together require an estimated 10.32 W at 1.28 m³/s under the assumed branch loss of 4.84 Pa and total efficiency of 0.60. Final fan selection requires the full system pressure rise. [Search results](../05_Calculations/search_summary.csv) · [Fan assumptions and CO comparisons](../08_Project_Notes/03_Group18_验收记录.md)

## Carbon monoxide generation and mitigation

The propylene model prescribes a CO yield of 0.01 kg per kg of fuel consumed. The half-height probes measure local concentration as smoke moves through the compartment. In the OP-6 comparison with soot yield 0.02 and curtain depth 0.16 m, increasing exhaust from 0.16 to 0.64 m³/s reduced the 120 s mean CO concentration at x = 6.1 m from 100.73 to 0.62 ppm. At this same station, minimum thermal layer height was 0.143 m and 0.097 m, respectively. Both fell below the 0.38 m target. This comparison supports higher extraction as a means of reducing local CO accumulation in this scenario. Estimating the fraction of CO removed through the ducts would also require exhaust CO mass flux. [Lower-flow station results](../05_Calculations/design_6_0p02_0p16_0p16_120_stations.csv) · [Higher-flow station results](../05_Calculations/design_6_0p02_0p16_0p64_120_stations.csv)

## Supplementary surrogate check

The physics-informed surrogate was trained on FDS output to predict eight station height histories. A held-out design tested extrapolation from curtain depths of 0.16 and 0.24 m to 0.32 m at OP-6, soot yield 0.10 and total flow 1.28 m³/s. Its predicted minimum of 0.619 m exceeded the full-run FDS minimum of 0.267 m by 0.352 m and would have classified the design as passing. The independent reference here is a held-out CFD case; experimental validation is a separate propane comparison. This false pass is why the design decision uses full-duration FDS output or an observed early failure. [Surrogate methodology and event audit](../09_PINN_Layer/README.md)

## Remaining decisions

After the paired propane runs finish, quantify the residual validation error and its sensitivity to enclosure heat transfer and mesh size. A propylene design recommendation requires a full-duration candidate with satisfactory margins across the specified door and soot scenarios. Retain all early-stop cases as failed, truncated observations. The formal report and submission remain subject to group review.
