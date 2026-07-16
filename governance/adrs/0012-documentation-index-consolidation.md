---
status: accepted
decision_date: 2026-07-16
supersedes: null
superseded_by: null
linked_invariant_test: scripts/check_internal_links.py
linked_finding: F-202
---

# ADR-0012: Consolidate the documentation index

- **Date:** 2026-07-16
- **Status:** Accepted
- **Deciders:** Rafael Braga

## Context

The Charter indexed documents that did not exist. This made the project
documentation look more complete than the repository and left readers without a
reliable route to its sources, scope, limitations, or sensitivity protocol.

## Decision

Restore the load-bearing governance documents referenced by the Charter:
`DATA_SOURCES.md`, `EXPERIMENTS.md`, `LIMITATIONS.md`, `REFERENCES.md`,
`REPO_STRUCTURE.md`, `SCOPE_LOCKS.md`, and `SENSITIVITY.md`.

Do not recreate redundant documents. The Charter now points technology-stack
details to `pyproject.toml` and `CONTRIBUTING.md`, data-storage details to
`DATA_SOURCES.md`, module behaviour to pipeline docstrings, and requirements to
the Charter sections themselves. `scripts/check_internal_links.py` verifies
tracked Markdown links and Charter index path references.

## Consequences

### Positive

- Documentation references resolve to maintained repository artifacts.
- The Charter remains the single authoritative index without duplicate specs.
- A regression in a tracked internal link is detected automatically.

### Negative

- Contributors must update the linked source when moving or deleting a document.
- `EXPERIMENTS.md` remains intentionally minimal until F-211 restores its
  hypothesis content.

## References

- `PROJECT_CHARTER.md` §3.6, §3.7, and §4.
- `governance/findings/F-202.yaml`.
- `scripts/check_internal_links.py`.
