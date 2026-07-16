---
status: accepted
decision_date: 2026-07-16
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f237_pick_lines_service.py
linked_finding: F-237
---

# ADR-0017: Per-order service time = pick_lines × cycle_time_per_line

- **Date:** 2026-07-16
- **Status:** Accepted
- **Deciders:** Rafael Braga
- **Linked finding:** F-237

## Context

`config/autostore_baseline.yaml` stores human (and AMR) cycle times as **seconds
per pick line** (Knapp benchmark; ADR-0009) and separately declares
`operations.pick_lines_per_order: 2.5`. Until F-237 that factor was listed under
`unmodeled_parameters` and never applied. Simulation, utilisation prediction,
capacity ceilings, crew optimization, and the demand frontier therefore treated
25 s as **per-order** service — understating load by 2.5× and producing a
falsely feasible one-human lean crew.

## Decision

1. **Scaling site.** Apply once when constructing agent cycle times (Module 2
   profile build and `crew_optimizer._agent_cycle_times`), via
   `scale_line_cycle_to_order`. `predict_utilisation` and
   `compute_capacity_ceiling` continue to treat `AgentProfile.cycle_time_*` as
   **per-order** service after scaling.

2. **Variance model.** For independent line draws:
   `mean_order = mean_line × L`, `std_order = std_line × √L`.
   Alternative (fully correlated lines → std × L) rejected: pick-line times are
   closer to i.i.d. draws than a single scaled random variable.

3. **Pure-AMR exclusion.** Do not add `S-lean-amr`. Optimizer and demand-frontier
   policy sets exclude `{amr}`-only. AutoStore port work in this model requires
   fine-motor pick that AMRs alone cannot perform; AMR may only appear with humans
   and/or humanoids.

4. **`operations.pick_lines_per_order` is modeled** (removed from
   `unmodeled_parameters`).

## Consequences

- Lean-human crew at λ=120/h and ρ≤0.85 requires ≥3 humans (was 1).
- All headline TCO / capacity / sensitivity artifacts must be regenerated (F-237).
- Decision procurement trigger moves to
  `breakeven_thresholds.vs_lean_human.capex_eur_per_unit`.
