---
status: accepted
decision_date: 2026-06-13
supersedes: null
superseded_by: null
linked_invariant_test: tests/test_config_wiring.py
linked_finding: null
---

# ADR-0011: Audit remediation — config wiring, explicit crews, and transfer-factor realism

- **Date:** 2026-06-13
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

A false-confidence audit found that several components *appeared* connected but
were not, while the governance suite verified provenance and wording rather than
wiring:

1. **`config/tco_assumptions.yaml` was inert.** `compute_tco_scenario` read flat
   keys (`human_hourly_wage_eur`, `humanoid_capex_eur`, …) that do not exist in
   the nested YAML (`labor.base_hourly_wage_eur`, `humanoid.unit_capex_eur`), so
   every `assumptions.get(key, default)` silently used a hardcoded default. NPV
   was byte-identical after multiplying the config wage ×5 and capex ×8.
2. **Crew sizes were silently truncated.** `int(total_agents * fraction)` floored
   S-hybrid-amr (60/20/20 of 8) to 4 + 1 + 1 = 6 units while docs implied 8.
3. **The 0.70 WBT→production transfer factor — the charter's "single largest
   methodological assumption" — never reached the simulation.** Capacity used raw
   teleoperation-demo cycle times. The humanoid cycle time was also selected as
   "first row with a valid std", which depended on alphabetical sort order and
   picked `bimanual_handling` rather than the modelled warehouse pick.
4. **The dashboard "cost reduction" was opex-only**, overstating the total-cost
   advantage (pure-humanoid: 70% opex vs 3.9% NPV).
5. **S-future-2028 was identical to S-hybrid-5050 in the Monte Carlo** (the
   throughput multiplier reached the deterministic TCO but not the sensitivity).

## Decision

- Map the nested config into the flat key space via
  `module_03_tco.build_financial_params`, and source the sensitivity
  ranges/distributions/base-point from `config/tco_assumptions.yaml::sensitivity`.
  The config is now the source of truth; the headline NPV table is unchanged
  because the defaults equalled the config values.
- Make crew sizes explicit integer `agent_counts` in
  `config/autostore_baseline.yaml::scenarios`, read by Modules 2 and 3. Where a
  scenario fields fewer than `total_agents` units (S-hybrid-amr = 6), it is a
  disclosed lean-crew design, not a hidden truncation.
- Apply the transfer factor to the simulated humanoid cycle time, and select that
  cycle time from an explicit `reference_task` (`pick_medium_object`), invariant
  to summary row order.
- Add an NPV-based `total_cost_reduction_vs_baseline_pct` and rank by it; retain
  the opex-only figure under an explicit alias.
- Apply the throughput multiplier in `analysis/sensitivity.py` so S-future-2028
  differs from S-hybrid-5050 in the MC.

## Consequences

### Positive

- Editing the config now changes the outputs; `tests/test_config_wiring.py`
  perturbs inputs and asserts the outputs move — the missing test class.
- The capacity ceiling reflects production speed (209–979 orders/hr across
  scenarios); the headline financial results are preserved.

### Negative

- The capacity ceiling, S-future-2028 MC, and break-even (€125,865 → €125,582)
  values changed from earlier reports; README/QMD/lineage were re-synced. The
  break-even change also fixed a pre-existing inconsistency between the report
  JSON and the cost-per-order artifact.

## References

- `tests/test_config_wiring.py` — input-perturbation regression suite.
- ADR-0008 (one dashboard surface) — Power BI orphan removed in the same change.
- CHANGELOG.md `[Unreleased]` — full per-item list.
