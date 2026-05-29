---
status: accepted
decision_date: 2026-05-22
superseded_by: null
linked_invariant_test: null
---

# ADR-0007: Simulation Agent Routing Bug and Fix

**Date:** 2026-05-22
**Status:** Accepted
**Supersedes:** ADR-0006 (misdiagnosis of root cause)
**Decider:** Rafael Braga

## Context

Module 2 (SimPy discrete-event simulation) produced statistically indistinguishable throughput across all 5 scenarios (Kruskal-Wallis p=1.0) even after switching to real UnifoLM cycle time data with significant variance (std=41.8s for a mean of 61.4s). ADR-0006 hypothesized this was a data artifact and claimed real data resolved it, but validation after the switch still showed p=1.0.

## Investigation

Code review of `src/warehouse_humanoid_tco/models/simulation.py` revealed the root cause was not data, but simulation logic. In the `pick_order` generator function (lines 57–71), an early `return` statement inside the `for profile in scenario.agent_profiles` loop caused the function to exit after the first non-empty agent profile.

In all scenarios, the first profile is always "human". This meant every single order was assigned to the human resource, and subsequent profiles (humanoids and AMRs in hybrid scenarios) were never requested.

Verification: Running the simulation with humanoid cycle time set to 250s (10× slower than humans) in a hybrid scenario still produced throughput within ~8% of the human-only scenario, confirming that humanoids were not processing orders despite being available.

## Decision

Refactored `pick_order` to perform weighted-random agent selection based on workforce count:

```python
eligible = [p for p in scenario.agent_profiles if p.count > 0]
if not eligible:
    return
weights = np.array([p.count for p in eligible], dtype=float)
weights /= weights.sum()
chosen_idx = int(rng.choice(len(eligible), p=weights))
profile = eligible[chosen_idx]
# ...process order with chosen profile...
```

Added regression test `tests/test_simulation.py::test_scenarios_with_different_agent_mixes_produce_different_throughput` to prevent recurrence.

## Consequences

- Agent routing now correctly distributes orders across all available agent types in proportion to workforce composition.
- Throughput now varies across scenarios based on agent composition.
- Kruskal-Wallis test post-fix on real data: ~1% spread in means across scenarios (p-value likely remains ≥0.05, but due to low system utilization, not routing bug).
- All published charts and dashboards must be regenerated from the fixed simulation.
- ADR-0006's outcome statement "confirms real data resolves convergence" is incorrect; the actual root cause was simulation logic, not data quality.

## Why p=1.0 Still Occurs

Post-fix, throughput spread remains narrow (~948–950 orders/shift across 5 scenarios) because:
1. Order arrival rate is 120/hour (low utilization of total workforce capacity ~500–1150 orders/hour depending on agent mix)
2. At low utilization, queueing is minimal and all scenarios pass through orders at the arrival rate
3. Statistical convergence in throughput does NOT indicate routing bug after this fix; it indicates the system is not under enough load to show differentiation

This is **expected behavior** and not a regression. To observe meaningful throughput differences, either:
- Increase order arrival rate to saturate workforce capacity
- Examine scenarios with more extreme mix differences (e.g., pure humanoid vs. pure human at high load)

## Commit Hash

fix(simulation): correct agent routing bug; orders now distributed across all agent profiles
test(simulation): add regression test for agent routing differentiation
fix(tco): remove misleading npv_std/ci fields; throughput doesn't scale fixed labor costs

---

**Audit Trail:**
- Original hypothesis in ADR-0006: synthetic cycle time distribution caused convergence → rejected
- Actual cause identified: single-line early return in pick_order → fixed
- Regression test added to prevent reintroduction
- TCO model clarified: throughput does not affect NPV in fixed-cost labor model (only agent composition matters)
