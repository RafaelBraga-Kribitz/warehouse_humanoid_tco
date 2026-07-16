---
status: accepted
decision_date: 2026-07-16
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f221_fair_scenarios.py
linked_finding: F-221
---

# ADR-0014: Fair scenario sizing before technology comparison

- **Date:** 2026-07-16
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

The prior headline compared fixed, heterogeneous crew sizes: the baseline had
eight humans, while the AMR hybrid had six units. Its apparent advantage
therefore combined staffing reduction and technology choice.

## Decision

Size each non-legacy scenario with the deterministic F-220 optimizer. The
constraint is `rho <= 0.85` for every required policy class, and the objective
is minimum five-year present-value cost. Hybrid policies require every named
class; the human/humanoid hybrid additionally selects the closest feasible
integer 50/50 split. Future-2028 applies its configured humanoid throughput
multiplier while sizing and costing.

`S-baseline-human` remains an explicitly labelled historical eight-human,
legacy-overstaffed reference. `S-lean-human` is the optimizer-sized
human-only comparator.

## Consequences

### Old headline

“S-hybrid-amr is the cheapest option” conflated a smaller crew with the
technology mix and was not a technology-only recommendation.

### New headline

At modeled demand after pick-lines scaling (F-237), the optimizer-sized
three-human scenario is cheapest. Robot mixes are reported as feasible
technology alternatives, while the eight-human row remains only as a
historical reference for the cost of overstaffing.

## References

- `src/warehouse_humanoid_tco/analysis/crew_optimizer.py`
- `config/autostore_baseline.yaml`
- `tests/governance/test_f221_fair_scenarios.py`
- `governance/findings/F-221.yaml`
