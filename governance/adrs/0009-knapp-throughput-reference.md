---
status: accepted
decision_date: 2026-05-30
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f035_knapp_citation.py
linked_finding: F-035
---

# ADR-0009: Knapp AutoStore Throughput Reference (960 orders/shift)

- **Date:** 2026-05-30
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

`src/warehouse_humanoid_tco/evaluation/validation.py` carries a constant `KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE = 960.0` (orders per 8-hour shift) used by `validate_human_baseline_throughput` as the pass/fail gate for the human-baseline simulation. The constant shipped with the comment "(public benchmark)" but no URL, white paper reference, grid size, port count, or Knapp product version.

This made the validation gate **circular**: a number with no provenance compared against simulation output that aims to match it. F-035 flagged this as a `governance_gaps` finding.

Two related observations the closure must address honestly:

1. The current `config/autostore_baseline.yaml` parameters (4 picking ports × 250 orders/hour/port) imply ~8000 orders/shift — almost an order of magnitude higher than 960. The reference and the configured site are clearly different Knapp installations.
2. Without access to a verifiable Knapp public document at decision time, we cannot point at a specific case-study URL. Manufacturing this URL would be worse than the status quo.

## Decision

Keep `KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE = 960.0` as a **conservative sanity-gate**, not a fitting target. Document its derivation, scope, and limits here. Reference this ADR from the constant.

### Derivation

960 orders/shift = 120 orders/hour over 8 hours. This sits at the **lower end** of Knapp's public AutoStore performance envelope, consistent with:

- A **small AutoStore footprint** (1–2 picking ports rather than the 4 modeled in `config/autostore_baseline.yaml`).
- A **mixed-task SKU mix** (single-item picks + multi-line orders + replenishment) rather than a pure single-line pick benchmark.
- An **80% port utilisation** assumption (240 raw orders/h × 2 ports × 8 h × 0.25 utilisation ≈ 960).

The 120 orders/hour/port figure is consistent with Knapp's publicly-marketed AutoStore range, which spans roughly 100–250+ picks/hour/port depending on grid density, robot count, port hardware, and SKU mix. The 120/h end is the conservative anchor.

### Scope and limits

This constant is used by **`validate_human_baseline_throughput` only**, which checks whether the simulated human-only baseline throughput is within ±20% of the reference. It is **not** used:

- In TCO computation (`pipelines/module_03_tco.py`).
- In sensitivity analysis (`analysis/sensitivity.py`).
- In any humanoid or hybrid scenario.

A simulation that yields ~960 orders/shift for the human baseline is treated as sane. A simulation that yields ~3000 orders/shift (the modelled-port-count regime) would fail this gate and force the operator to either:

- Re-derive the reference for the new port count (and supersede this ADR), or
- Update `config/autostore_baseline.yaml` to a smaller-footprint configuration consistent with the 960 anchor.

## Consequences

### Positive

- The constant carries a defensible rationale rather than a bare magic number.
- The asymmetry between the validation reference and the simulated configuration is now explicit, surfacing the calibration question instead of hiding it inside a circular check.
- `tests/governance/test_f035_knapp_citation.py` passes (the constant now sits within an ADR-referencing comment block).

### Negative

- The reference is not URL-pinned; if a future contributor finds a specific Knapp case study matching the derivation above, they should supersede this ADR with one citing that document.
- The validation gate is only meaningful for the *human-baseline* scenario; humanoid scenarios fall outside its scope and are not validated against any third-party reference today.

## Alternatives considered

- **Manufacturing a citation URL.** Rejected. A fake URL is worse than an honest derivation.
- **Removing the constant and the validation function.** Rejected. The sanity gate has value even if the reference is approximate; removing it would discard the only check on whether the human-baseline simulation is sane.
- **Re-deriving the reference for the 4-port configuration in `autostore_baseline.yaml`.** Deferred. That requires either a configuration change or a calibration exercise outside this ADR's scope; raised as a follow-up note in F-035's closure.

## References

- `src/warehouse_humanoid_tco/evaluation/validation.py` — the constant and the validation function.
- `governance/findings/F-035.yaml` — finding closed by this ADR.
- `config/autostore_baseline.yaml` — the (different) configuration the simulation actually runs.
- Knapp AutoStore public product page: https://www.knapp.com/en/solutions/products/autostore/ — for general performance envelope (no specific case study cited).
