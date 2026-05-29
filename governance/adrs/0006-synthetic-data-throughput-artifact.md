---
status: superseded
decision_date: 2026-05-21
superseded_by: "0007-simulation-agent-routing-bug.md"
linked_invariant_test: null
---

# ADR-0006: Synthetic Data Cycle Time Artifact in Simulation

**Date:** 2026-05-21
**Status:** Superseded
**Superseded by:** ADR-0007 (root cause was simulation routing bug, not synthetic data)
**Decider:** Rafael Braga

## Context

The first simulation run on the synthetic fixture (5 episodes) produced throughput of **930–980 orders/shift across ALL five scenarios**, including S-pure-humanoid. Scenarios with completely different workforce mixes — 100% human vs. 100% humanoid — showed statistically identical throughput. This was a red flag.

## Investigation

The synthetic fixture drew cycle times from a narrow uniform distribution (`U[20, 30]` seconds) to ensure the pipeline had valid numeric inputs during development. This uniform distribution had no meaningful difference between "human" and "humanoid" service times. Because the SimPy simulation uses service time distributions as the primary differentiator between agent types, identical distributions produce identical throughput.

The system was working correctly — it was the test inputs that masked scenario differences.

## Decision

1. Kept the synthetic fixture for pipeline smoke tests (`tests/test_simulation.py`) — it validates that the simulation runs to completion without exception, not that results are substantively different.
2. Added a `@pytest.mark.integration` marker for tests that validate scenario differentiation; these require real data and are skipped in fast CI.
3. Ran Modules 1–3 on the full real UnifoLM dataset (2,359 episodes). Real WBT cycle times show a **3× spread across task categories**: pick tasks average ~45s with σ≈18s; place tasks average ~15s with σ≈6s. This variance drives meaningful scenario differentiation in simulation.

## Outcome

After switching to real empirical inputs, throughput variance across scenarios increased substantially, and the sensitivity analysis became meaningful. The S-hybrid-amr advantage over S-pure-humanoid became explainable by task mix assignment, not cycle time noise.

## Consequences

- Synthetic fixtures are kept for smoke tests only; integration tests require real data.
- `@pytest.mark.integration` marker added to all scenario-differentiation tests.
- **Superseded by ADR-0007**: the actual cause of p=1.0 was a simulation routing bug, not synthetic data.

## Lesson

Synthetic test fixtures are useful for structural validation (does the pipeline run?) but should never be used to validate analytical results (do the numbers make sense?). The distinction is `@pytest.mark.unit` vs. `@pytest.mark.integration`. Document this boundary explicitly in `tests/conftest.py`.
