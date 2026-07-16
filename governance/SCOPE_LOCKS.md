# Scope Locks

The locks below define the v1.0 analytical boundary.

| Lock | Rule |
|---|---|
| L1 | Model AutoStore-style warehouse operations only; Stingray and Magna configurations remain uncalibrated stubs. |
| L2 | Do not add human activity sensing, RuView, CSI, or employee monitoring. |
| L3 | Derive humanoid capabilities from the pinned empirical datasets, not vendor marketing or predictive ML. |

## Anti-creep checklist

Before accepting a new feature or dataset, answer all five questions:

1. Does it directly support the AutoStore TCO decision?
2. Does it preserve the no-human-sensing boundary?
3. Is its capability evidence empirical and reproducible?
4. Can its assumptions, inputs, and outputs be versioned in this repository?
5. Does it require a Charter update and an ADR because it changes scope or architecture?

If any answer is no or unknown, record it as future work rather than adding it
to the v1.0 implementation.
