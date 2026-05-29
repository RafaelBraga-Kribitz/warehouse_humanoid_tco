---
status: accepted
decision_date: 2026-05-29
supersedes: "0004-dual-publish-dashboards.md"
superseded_by: null
linked_invariant_test: scripts/check_deprecations.py
linked_finding: F-004
---

# ADR-0008: Deprecate Power BI Export Path

- **Date:** 2026-05-29
- **Status:** Accepted
- **Deciders:** Rafael Braga
- **Supersedes:** ADR-0004 (the Power BI half of the dual-publish decision)

## Context

ADR-0004 committed v1.0 to dual-publish dashboards: Tableau Public as the primary, browser-shareable surface and a Power BI `.pbix` for Microsoft-shop recruiters. The Python data layer in `src/warehouse_humanoid_tco/visualization/exports.py` carried matching `export_for_tableau` and `export_for_powerbi` functions.

Reality through Phase 5:

1. No `.pbix` was ever authored. The "Power BI" surface in v1.0 was just a parquet file alongside the Tableau CSV.
2. `export_for_powerbi` has zero callers in `src/`. The pipeline never writes parquet for Power BI; only the Tableau CSV ships.
3. The only consumer is `tests/test_features_and_utils.py::test_export_for_powerbi_creates_parquet`, which exercises the function in isolation, not as part of any module.
4. Power BI Desktop happily ingests CSVs. The marginal cost of dropping the parquet export is zero for any recruiter who downloads the repo.

The F-017 closure (this PR cluster) already removed the "publication pending" language from the README. With Tableau Public itself unhosted, claiming a Power BI surface on top is honesty drift: the README would advertise two dashboards while shipping neither.

## Decision

Delete `export_for_powerbi` and its isolated test. The CSV exports under `exports/tableau_public/` are the single dashboard data surface for v1.0. Anyone who wants Power BI can import the CSV.

This **supersedes the Power BI portion of ADR-0004**. The Tableau side of ADR-0004 still stands: Tableau Public remains the named primary surface, with hosting deferred per F-017's closure.

## Consequences

### Positive

- `src/.../visualization/exports.py` shrinks to the one exporter actually used.
- README, ADR-0008, and shipping reality agree: there is one dashboard surface.
- Removes a Phase 5 deprecation that would otherwise sunset on 2026-06-30 unenforced.

### Negative

- A future contributor who wants a native `.pbix` surface must author a new ADR superseding this one. Acceptable; that conversation should be triggered by a concrete recruiter request, not by inherited intent.

## Migration

- Delete `export_for_powerbi` from `src/warehouse_humanoid_tco/visualization/exports.py`.
- Delete `test_export_for_powerbi_creates_parquet` from `tests/test_features_and_utils.py` (and the unused import).
- Remove the `export_for_powerbi` entry from `governance/DEPRECATIONS.yaml`.
- Regenerate `governance/CODE_INVENTORY.yaml`.
- Close finding F-004; the `check_deprecations.py` Adversary script now reports zero overdue deprecations.

## References

- ADR-0004 (Dual-Publish Dashboards) — supersedes the Power BI portion only.
- `governance/findings/F-004.yaml` — dead-artifact finding closed by this ADR.
- `governance/DEPRECATIONS.yaml` — entry removed in this PR.
- `governance/findings/F-017.yaml` — Tableau "publication pending" closure, same PR series.
