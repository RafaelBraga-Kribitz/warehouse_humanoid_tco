---
status: accepted
decision_date: 2026-05-20
superseded_by: null
linked_invariant_test: tests/governance/test_f017_tableau_status.py
---

# ADR-0004: Dual-Publish Dashboards (Tableau Public + Power BI)

- **Date:** 2026-05-20
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

The portfolio's primary audiences (Austrian industrial recruiters) tend to work in Microsoft-heavy stacks. Power BI is the de facto BI tool at Knapp and TGW based on public job postings. However, Tableau Public offers superior portability: anyone with a browser can view a Tableau Public dashboard without installing Power BI Desktop.

The cost of producing both is modest: the analytical layer is in Python, with both BI tools consuming the same parquet outputs from Module 3.

## Decision

Module 4 ships two dashboard artifacts driven from the same data layer:

1. **Tableau Public** as the primary, browser-shareable link in the portfolio.
2. **Power BI `.pbix`** committed to `reports/` for download by recruiters in Microsoft-shop environments.

The Python data layer (`src/warehouse_humanoid_tco/visualization/exports.py`) emits CSV and parquet files consumable by both tools.

## Consequences

### Positive

- Maximum surface area: anyone clicking the portfolio link sees the dashboard immediately via Tableau Public; technical recruiters can also download the `.pbix`.
- Single Python data layer prevents drift between the two BI tools.
- Demonstrates breadth (knows multiple BI tools) without paying double the cost.

### Negative

- Two dashboards to maintain. Mitigation: the data layer is single-source, and dashboards are rebuilt rather than incrementally edited when data changes.
- Tableau Public requires every published dataset to be publicly visible. No private data, no embedded secrets. Acceptable since the project uses only public sources.

## References

- PROJECT_CHARTER.md §5.1 FR-07
- PROJECT_CHARTER.md §8.2 Technology Stack
