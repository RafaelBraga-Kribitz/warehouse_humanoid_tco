---
status: accepted
decision_date: 2026-07-16
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f232_demand_frontier.py
linked_finding: F-232
---

# ADR-0015: Demand and shift frontier uses optimized crews

- **Date:** 2026-07-16
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

A single demand point cannot show when robot capacity enters an economically
optimal crew. Labor cost also changes when operations require night shifts.

## Decision

Sweep demand at 120, 200, 300, and 400 orders per hour across one, two, and
three separately staffed shifts. Each point invokes the deterministic
`crew_optimizer` with `rho <= 0.85`. Later shifts receive the configurable
`night_shift_premium`, default 1.5, through the average staffing wage used in
the TCO comparison.

## Consequences

The frontier is a transparent planning screen, not a claim that a robot fleet
can operate continuously without additional reliability, maintenance, or
supervision modelling. The generated JSON records every grid point and the PNG
visualizes the robot count in the least-cost feasible crew.

## References

- `src/warehouse_humanoid_tco/analysis/crew_optimizer.py`
- `config/tco_assumptions.yaml`
- `reports/demand_frontier.json`
