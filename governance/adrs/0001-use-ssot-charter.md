---
status: accepted
decision_date: 2026-05-20
superseded_by: null
linked_invariant_test: tests/governance/test_f011_methodology_canonical.py
---

# ADR-0001: Use a Single Source of Truth Charter Instead of Separate Spec Documents

- **Date:** 2026-05-20
- **Status:** Accepted
- **Deciders:** Rafael Braga
- **Supersedes:** None
- **Superseded by:** None

## Context

The original request was to produce six separate documents: CRISP-DM, Business Case / Project Charter, Requirements Specification, Data Requirements, Experiment Design, and Software Requirements Specification.

Six standalone documents create the documentation sprawl anti-pattern. Each duplicates content (project goals, scope, stakeholders appear in at least three of the six). Each duplication is a future drift point. Within weeks, the documents disagree and tribal knowledge fills the gap.

The user explicitly stated they want to prevent fragmented documentation, tribal knowledge, and documentation sprawl. The user also explicitly stated they want a Single Source of Truth approach with automated enforcement.

These goals are incompatible with shipping six separate documents.

## Decision

Ship a single `PROJECT_CHARTER.md` at the repo root. It contains all six "documents" as numbered sections within a Table of Contents. It is the SSOT.

Supporting infrastructure:

1. `governance/adrs/` for append-only, immutable decision records.
2. `CONTRIBUTING.md` for the documentation discipline rules.
3. `.github/workflows/docs-ssot-check.yml` for CI-enforced staleness and sprawl checks.

The SSOT is enforced by three mechanisms:

- **Convention:** the Charter §2 explicitly forbids parallel documents.
- **CI:** the workflow fails the build if Markdown files appear outside the allowlist or if the SSOT is stale relative to code changes.
- **ADRs:** the only sanctioned way to evolve the SSOT is through dated, immutable ADRs.

## Consequences

### Positive

- One place to look for any project decision.
- No duplication, therefore no drift.
- Recruiters see a single, well-organized document instead of hunting through six.
- Future contributors (or future-self) have unambiguous rules for where new content goes.
- The ADR pattern preserves decision history, which is more valuable than the current state alone.

### Negative

- The Charter is long (~700 lines at v1.0). It is intentionally long and structured by Table of Contents, which is acceptable.
- Sections that grow too large will need ADR-driven extraction to sibling files under `docs/`. This is a known evolution path, not a flaw.
- Discipline is required to keep using ADRs instead of inline edits. The CI mitigates this but does not eliminate it.

### Neutral

- The user wanted six documents and was given one structured document plus supporting infrastructure. This was a Reviewer-mode pushback that was overridden in favor of the SSOT principle, which the user prioritized higher.

## References

- `PROJECT_CHARTER.md` §2 Documentation Discipline
- `.github/workflows/docs-ssot-check.yml`
- `CONTRIBUTING.md`
- User's master prompt: "enforcing a Single Source of Truth (SSOT) and enforcing constant and continuous update of documentation and SSOT as automatic workflow"
