---
status: accepted
decision_date: 2026-07-16
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f219_sql_parity.py
linked_finding: F-219
---

# ADR-0013: Publish Tableau exports through DuckDB SQL

- **Date:** 2026-07-16
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

Module 4 previously converted Parquet files to Tableau CSVs through opaque
Polars passthrough. This left no reviewable projection defining the published
analytical fields, despite DuckDB already being a declared dependency.

## Decision

Store one SQL projection per published dataset in `analytics/sql/`. Each query
enumerates its columns and uses a `{{source}}` placeholder. Module 4 replaces
that placeholder with a local `read_parquet(...)` relation and writes the
result to its Tableau CSV. The same SQL is tested over the published CSV when
processed Parquet is unavailable.

Polars remains the charting implementation; this decision applies only to the
published CSV export path.

## Consequences

### Positive

- Published fields and ordering are reviewable SQL artifacts.
- Parquet-to-CSV parity is checked when regenerated data is available.
- Existing CSVs remain testable in a data-constrained checkout.

### Negative

- Adding a published column requires updating both its SQL projection and its
  parity test.
- SQL files are templates, not independently executable without a source
  relation supplied by Module 4 or the test.

## References

- `src/warehouse_humanoid_tco/pipelines/module_04_dashboards.py`.
- `analytics/sql/`.
- `tests/governance/test_f219_sql_parity.py`.
- `governance/findings/F-219.yaml`.
