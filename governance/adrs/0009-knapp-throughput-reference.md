---
status: accepted
decision_date: 2026-05-31
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f035_knapp_citation.py
linked_finding: F-035
---

# ADR-0009: Knapp AutoStore throughput reference (960 orders/shift) — honest derivation and tautology disclosure

- **Date:** 2026-05-31
- **Status:** Accepted (revised v2 — replaces the v1 draft dropped under PR #27)
- **Deciders:** Rafael Braga

## Context

`src/warehouse_humanoid_tco/evaluation/validation.py` carries

```python
KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE = 960.0  # orders per 8-hour shift
```

used by `validate_human_baseline_throughput` as the pass/fail gate for the human-baseline simulation. The constant originally shipped with the bare comment "(public benchmark)" — no URL, no white paper, no Knapp product version. F-035 flagged this as a `governance_gaps` finding.

The first attempt at this ADR (PR #27, dropped) tried to justify 960 by computing `2 ports × 250 orders/h/port × 8 h × 25 % utilisation ≈ 1000`. Codex correctly flagged two errors in that derivation:

1. **Self-contradictory utilisation.** The narrative text stated "80 % port utilisation" but the formula multiplied by `0.25` (i.e., 25 %). With 80 % the result would be 3,072, not 960.
2. **Wrong configuration claim.** The v1 ADR asserted that `config/autostore_baseline.yaml` modelled 4 ports × 250 orders/h ≈ 8,000/shift and therefore the 960 reference described "a different installation". Inspecting `pipelines/module_02_simulation.py:145` shows the simulation passes `config["operations"]["order_arrival_rate_per_hour"]` (= 120/h) into `WarehouseScenario` as the Poisson arrival rate. `layout.ports` is documented in the config but is **not** wired into any throughput cap. The simulated throughput is therefore ~120/h × 8 h = ~960/shift — **the same** as the reference. The asymmetry the v1 ADR documented does not exist.

This v2 ADR replaces that derivation with an honest one and explicitly discloses the resulting limitation of the validation gate.

## Decision

Keep `KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE = 960.0` as a **conservative sanity-gate**, while disclosing in this ADR that the gate is **structurally tautological** under the current configuration: the simulation consumes the same arrival rate (120/h) that the gate compares against (120/h × 8h = 960/shift). The gate cannot fail under steady-state queueing with utilisation ρ ≈ 0.10 (per F-028) and lognormal service-time draws (per F-027), because every order that arrives is served well within the shift.

### Derivation (the honest one)

The 960 figure is **exactly** the product of two configured inputs:

```
order_arrival_rate_per_hour × shift_hours
  = 120 orders/h × 8 h
  = 960 orders/shift
```

with `order_arrival_rate_per_hour: 120` documented in `config/autostore_baseline.yaml` as "Poisson lambda; from Knapp public benchmarks". The Knapp public envelope for AutoStore picking spans roughly 100–250+ orders/hour/port depending on grid density, robot count, port hardware, and SKU mix; the 120/h baseline sits at the conservative low end of that envelope, defensible for a small-medium AutoStore install with mixed-task SKUs.

### Why keep the gate at all

It still has value as a **regression** check: a future code change that breaks order-dispatch routing (such that orders are dropped or starved) would push simulated throughput well below 960/shift even with the same arrival rate, and the gate would fire. The gate cannot detect over-capacity or speedup regressions — it can only detect catastrophic loss of work-in-flight.

## Consequences

### Positive

- The constant now carries a defensible, falsifiable derivation pinned to the actual configured inputs.
- The previous ADR's two factual errors (utilisation math, port-cap asymmetry) are removed; no future contributor will read the v1 prose and build a wrong calibration on top.
- The reference's tautology is disclosed in the code comment + this ADR, so a reader knows exactly what the gate proves (no work-dropping regressions) and what it does not prove (independent throughput validation).

### Negative

- The gate is genuinely weak — it does not validate the simulation against any external benchmark. Anyone reading the code now sees that explicitly; the previous comment "(public benchmark)" implied otherwise.
- A "real" validation gate would need an arrival-rate-independent metric (e.g., throughput per port-hour at saturation, or a comparison against a published Knapp case study with its own arrival rate). That work is deferred — see "Open follow-ups".

## Alternatives considered

- **Manufacture a URL citation.** Rejected: no specific Knapp case study with verified figures was located, and a fake URL is strictly worse than honest disclosure.
- **Remove the validation function entirely.** Rejected: even a weak regression check has value, and removing it would lose the only sanity gate on the human-baseline scenario.
- **Compute reference dynamically from arrival rate.** Rejected for v1.0: makes the tautology even more explicit but doesn't fix the underlying weakness, and `KNAPP_*_REFERENCE` is the type of name that should be a static benchmark, not a derived computed value.

## Open follow-ups (not closed by this ADR)

1. **Arrival-rate-independent validation.** Author a `validate_per_port_throughput_at_saturation` function or similar that compares the saturation throughput (driven by the ρ ≥ 1 gate from F-028) against an external published Knapp envelope. Requires either: (a) raising the arrival rate to saturation in a calibration run, or (b) computing the theoretical saturation throughput closed-form from agent count × 1/E[S].
2. **Pin a real Knapp case study.** If a future contributor locates a specific Knapp white paper or case study with verifiable throughput numbers, supersede this ADR with one citing that document and tighten the gate.

## References

- `src/warehouse_humanoid_tco/evaluation/validation.py` — the constant and the validation function.
- `src/warehouse_humanoid_tco/pipelines/module_02_simulation.py:145` — the arrival-rate plumbing that creates the tautology.
- `config/autostore_baseline.yaml::operations::order_arrival_rate_per_hour` — the 120/h Poisson rate that drives both the simulation and the reference.
- `governance/findings/F-035.yaml` — finding closed by this ADR.
- F-027 (lognormal service time), F-028 (utilisation gate), F-030 (elasticity-based tornado) — recent methodology fixes that the simulation now also passes through.
- Knapp public product page: https://www.knapp.com/en/solutions/products/autostore/ — general performance envelope context, no specific case study cited.
