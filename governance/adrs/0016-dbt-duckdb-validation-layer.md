---
status: accepted
decision_date: 2026-07-16
supersedes: null
superseded_by: null
linked_invariant_test: tests/governance/test_f229_dbt_parity.py
linked_finding: F-229
---

# ADR-0016: Validate published marts with dbt-duckdb

## Context

The reviewed DuckDB SQL projections in ADR-0013 define the published Tableau
CSVs, but they do not exercise an analytics-engineering build or data tests.

## Decision

Add an optional `analytics` dependency group containing `dbt-duckdb`. dbt reads
the four processed Parquet outputs, creates staging views and materialized
mart tables, and tests their key identifiers. The `F-229` pytest invokes
`dbt build` and compares mart column order, row count, and TCO NPV total with
the version-controlled Tableau CSVs.

The dbt project is a parallel validation layer. Module 4 and the reviewed SQL
projections remain the sole producers of published CSVs. dbt output is confined
to `analytics/dbt/target/` and is never committed.

The full workflow runs dbt only after Modules 1–4 have produced all Parquet
inputs. The per-PR pytest uses ignored Parquet fixtures generated from the
published CSVs only when real processed outputs are absent, so the build remains
executable in a clean checkout without weakening parity assertions.

## Consequences

### Positive

- Analytics marts, tests, and source lineage are reviewable dbt assets.
- dbt failures and CSV divergence block the F-229 recurrence test.
- The target database is isolated from production artifacts.

### Negative

- Contributors running `make dbt` must install `.[analytics]`.
- The full build requires all four processed Parquet outputs.

## References

- `analytics/dbt/`.
- `analytics/sql/`.
- `tests/governance/test_f229_dbt_parity.py`.
- `governance/findings/F-229.yaml`.
