# Experiments

## Purpose

These hypotheses turn the capability, TCO, and uncertainty artifacts into
decision rules. Scenario definitions remain in
`config/autostore_baseline.yaml`.

## H1 — Task-category cycle times

**Statement:** Humanoid cycle times differ by task category.

**Decision rule:** The absolute difference between `pick_medium_object` and
`place_general` mean cycle time is at least 20% of the pick mean in
`exports/tableau_public/humanoid_capabilities_summary.csv`.

**VERDICT H1: SUPPORTED —** Pick mean cycle time is 61.40 seconds and place
mean is 73.80 seconds, a 20.2% difference [exports/tableau_public/humanoid_capabilities_summary.csv::cycle_time_mean].

## H2 — Robot-inclusive value

**Statement:** At least one robot-inclusive workforce mix beats the human
baseline on five-year NPV.

**Decision rule:** At least one non-baseline, non-lean-human row has
`total_cost_reduction_vs_baseline_pct > 0`.

**VERDICT H2: SUPPORTED —** After F-241, S-lean-hybrid-amr (1 human + 3 AMRs)
beats the eight-human baseline by 73.8% total-cost reduction; humanoid-inclusive
crews remain costlier than the baseline
[exports/tableau_public/tco_scenarios.csv::total_cost_reduction_vs_baseline_pct].

## H3 — Current-capex pure-humanoid parity

**Statement:** A pure-humanoid mix reaches cost parity at current capex.

**Decision rule:** `breakeven_thresholds.capex_eur_per_unit` is at least
the current unit capex (€120,000), leaving non-negative headroom.

**VERDICT H3: REJECTED —** The €56,446 breakeven versus the legacy baseline is
below €120,000 current capex, and versus S-lean-hybrid-amr no breakeven exists
anywhere in the searched €10K–€500K capex range
(`vs_lean_human.no_breakeven_in_search_range: true` — capex is not the binding
constraint) [reports/module_03_tco_report.json::breakeven_thresholds].

## H4 — Uncertainty-robust ranking

**Statement:** The winning scenario remains better than the baseline under
uncertainty after F-237 service-time scaling.

**Decision rule:** The MC-winning scenario's p5 NPV is greater than the
baseline mean NPV.

**VERDICT H4: SUPPORTED —** S-lean-hybrid-amr wins 99.8% of Monte Carlo samples;
its p5 NPV (€−537,549) is better than the baseline mean (€−1.74M)
[reports/sensitivity_analysis_report.json::mc_summary_per_scenario].
