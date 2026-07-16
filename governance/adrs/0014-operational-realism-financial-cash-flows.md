---
status: accepted
decision_date: 2026-07-16
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f222_realism.py
linked_finding: F-222
---

# ADR-0014: Operational availability and realistic TCO cash flows

- **Date:** 2026-07-16
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

The model exposed reliability, battery, integration, wage-growth, residual, and
supervision assumptions but did not consistently apply them to capacity or TCO.
This understated the operational and financial cost of early humanoid deployments.

## Decision

1. **Availability:** Derate each humanoid service rate by
   `MTBF / (MTBF + MTTR) × battery_capacity / (battery_capacity + recharge)`.
   Capacity uses the reciprocal as a cycle-time multiplier; TCO uses the same
   reciprocal for required effective humanoid service capacity. AMRs receive the
   treatment only when their operational block supplies all four inputs.
2. **Integration:** Charge `infrastructure.integration_cost_eur` exactly once
   in year 0 for every scenario fielding at least one humanoid.
3. **Escalating labour and supervision uncertainty:** Escalate direct and
   supervision labour in operational year `t` by `(1 + wage_growth)^t`.
   Treat humanoid supervision ratio as a continuous OAT and Monte Carlo input
   over `[0.05, 0.50]`, sampled uniformly in Monte Carlo.
4. **Residual value:** Credit year-horizon salvage as a positive discounted
   cash flow: `n_units × unit_capex × residual_fraction ×
   max(0, (useful_life − horizon) / useful_life)`.

## Consequences

- Capacity ceilings decline for less-than-perfect availability.
- Humanoid scenarios include a site-level integration charge, escalating labour,
  and a terminal residual credit; all are visible in the cost-line breakdown.
- Sensitivity results now expose supervision uncertainty instead of treating it
  as a fixed, hidden operating assumption.

## References

- `config/autostore_baseline.yaml`
- `config/tco_assumptions.yaml`
- `tests/governance/test_f222_realism.py`
