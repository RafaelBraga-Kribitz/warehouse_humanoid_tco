---
status: accepted
decision_date: 2026-05-30
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f027_service_time_distribution.py
linked_finding: F-027
---

# ADR-0010: Lognormal per-line service time in the warehouse simulation

- **Date:** 2026-05-30
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

`src/warehouse_humanoid_tco/models/simulation.py` previously drew per-line service time as

```python
cycle_time = float(rng.normal(profile.cycle_time_mean, profile.cycle_time_std))
cycle_time = max(cycle_time, 1.0)
```

For the calibrated `Normal(25, 8)` baseline this means roughly 0.13 % of draws fall below 1 second and get folded into a point mass at 1.0. The fold is asymmetric: the right tail is unbounded but the left tail is clipped. The empirical mean of the kept samples is therefore strictly below 25 seconds, which inflates simulated throughput vs. the parameterised configuration. F-027 flagged the bias.

## Decision

Sample service time from a **lognormal** parameterised to preserve the target mean and standard deviation exactly:

```python
cv2 = (std / mean) ** 2
sigma2 = log(1 + cv2)
mu = log(mean) - sigma2 / 2
cycle_time = rng.lognormal(mu, sqrt(sigma2))
```

This is the industrial-IE standard for pick-time distributions:

- **Right-skewed**, matching empirical pick-time data (a few long picks, many short ones).
- **Strictly positive**, so no `max(., 1.0)` clip is needed and no point mass forms.
- **Two-parameter**, so it can be calibrated directly against the same mean/std the config supplies — no new parameters in `config/autostore_baseline.yaml`.

Algebraically: for `X ~ Lognormal(mu, sigma^2)`, `E[X] = exp(mu + sigma^2/2)` and `Var[X] = (exp(sigma^2) - 1) * E[X]^2`. Setting `E[X] = M` and `Var[X] = S^2` gives the formulas above.

## Consequences

### Positive

- The empirical mean of the simulated service time equals the configured mean (no left-tail folding bias).
- Service-time draws are strictly positive by construction, removing the silent `max(., 1.0)` clip.
- Right-skew matches the standard industrial-IE pick-time model, so calibration against external benchmarks (and any future fit to real WBT episode data) becomes meaningful instead of being absorbed by the truncation artefact.

### Negative

- Simulated throughput shifts vs. the prior runs (the bias is removed, not added). The Executive Summary's "~959 orders/shift" claim is allowed up to ±50 orders by F-021's tolerance gate, but if a single lognormal switch pushes throughput outside that band the QMD claim must be updated in the same PR. Downstream artefacts (`exports/tableau_public/tco_scenarios.csv`, `reports/sensitivity_analysis_report.json`) regenerate from `make all`.
- The TCO model in `pipelines/module_03_tco.py` is fixed-cost (`_ = simulation_data.get("throughput_orders_per_shift", 0)`), so NPV does not move with the throughput change.

## Alternatives considered

- **`scipy.stats.truncnorm`** — preserves Normal shape with a hard lower bound, but introduces a SciPy dependency in the hot inner loop for an effect that lognormal already achieves at zero cost. Rejected.
- **Weibull (shape, scale)** — also right-skewed and strictly positive. Equivalent for the v1.0 calibration, but its `(shape, scale)` parameters do not map directly to `(mean, std)`; the config would need new keys or an inversion helper. Deferred until empirical WBT cycle-time data justifies a richer distribution choice.
- **Keep `Normal` + clip, document the bias** — rejected because the verification script (F-027) explicitly bans the naive `rng.normal(profile.cycle_time_mean, ...)` pattern; "documenting the bug" doesn't close the finding.

## References

- `src/warehouse_humanoid_tco/models/simulation.py::_sample_service_time` — the implementation.
- `governance/findings/F-027.yaml` — finding closed by this ADR.
- `tests/governance/test_f027_service_time_distribution.py` — Adversary contract: the naive pattern must not return.
