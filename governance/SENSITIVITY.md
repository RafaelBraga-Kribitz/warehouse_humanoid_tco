# Sensitivity Analysis Protocol v2

The source of ranges, base points, and distributions is
`config/tco_assumptions.yaml::sensitivity`. The current published ranking comes
from `exports/tableau_public/tco_scenarios.csv`: Lean Human + AMR Team is cheapest,
and Future 2028 Humanoid Team is the least-cost humanoid-inclusive option. After F-241,
Monte Carlo assigns Lean Human + AMR Team ~99.8% rank probability across the CRN
sample.

## One-at-a-time sweeps

| Parameter | Range | Base point |
|---|---:|---:|
| Humanoid capex | €60,000–€180,000 | €120,000 |
| Human wage | €15.13–€22.00/hour | €18.50/hour |
| Human overhead multiplier | 1.00–1.70 | 1.35 |
| Discount rate | 4%–12% | 8% |
| WBT-to-production transfer factor | 0.50–0.90 | 0.70 |

## Monte Carlo and common random numbers

The protocol draws 10,000 samples for each scenario: lognormal humanoid capex
(mean €120,000, standard deviation €30,000); normal human wage (mean €18.50,
standard deviation €2.00); and uniform distributions for overhead multiplier,
discount rate, and transfer factor over the ranges above. Results report output
quantiles rather than confidence intervals.

Every scenario receives the same sampled parameter row (common random numbers,
CRN). This removes parameter-noise from pairwise differences; rank probabilities
are therefore comparisons of paired costs, not independent simulations. After
F-241, the published MC report includes the frontier lean hybrid and is the
ranking evidence for H4.

## Pair matrix

| Pair | Base-case decision | Interpretation |
|---|---|---|
| Lean Human + AMR Team vs any humanoid option | Lean Human + AMR Team | Cheapest ρ-feasible crew at modeled demand |
| Lean Human + AMR Team vs Lean Human Team | Lean Human + AMR Team | Frontier mix beats human-only lean crew |
| Future 2028 Humanoid Team vs All-Humanoid Team | Future 2028 Humanoid Team | Better humanoid-inclusive cost due to lower effective unit need |
| Human + Humanoid + AMR Team vs Future 2028 Humanoid Team | Future 2028 Humanoid Team | AMR plus €200k integration cost is not recovered |
| Legacy Overstaffed Team vs Lean Human Team | Lean Human Team | The eight-human baseline is a legacy overstaffed reference |

## Sobol-style screening

`reports/sensitivity_analysis_report.json::sobol_indices` is a deterministic
coarse-grid variance proxy, not a full Saltelli/Sobol estimator. For each
parameter, 21 OAT grid values are evaluated with all other inputs at their base
point, then normalized output variance is reported as first- and total-order
screening importance. It cannot identify interactions and must not be described
as a full global Sobol decomposition. Pearson correlations over these same grids
are published as `correlation_sensitivity`.

## Two-way frontiers and decision flips

Charts `07_frontier_capex_wage.png` and `08_frontier_capex_transfer.png` map
Future 2028 Humanoid Team minus Lean Human + AMR Team five-year NPV cost across capex × wage and
capex × transfer-factor grids. The zero contour is a cost tie; positive values
mean the robot option remains costlier. `decision_flip_thresholds` records the
grid-bound result explicitly: no Future 2028 Humanoid Team tie with Lean Human + AMR Team occurs
inside the published €60k–€180k capex range when other parameters are fixed.

Chart 09 plots five-year frontier crew cost versus demand for 1/2/3 shifts
(F-241); robot count alone is invariant across shifts and is no longer the
y-axis.

Future extensions must update this document, the configuration, report JSON,
and the relevant reproducibility test together.

## Expected value of partial information

`reports/sensitivity_analysis_report.json::evpi_eur` estimates partial EVPI
from common-random-number samples as
`E[max scenario E(NPV | parameter)] - max scenario E(NPV)`. Parameter draws are
ranked into 20 equal-frequency bins; the best conditional mean NPV is averaged
over those bins. Values are floored at zero because negative values are
finite-sample artifacts, not economic information value. EVPI ranks uncertainty
worth measuring before a decision; it is not a realized-savings forecast.
