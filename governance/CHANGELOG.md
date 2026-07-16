# CHANGELOG — warehouse_humanoid_tco

**Generated from git history + governance/findings/ closures. This is the authoritative version history.**

> **Note:** This file is auto-generated from `git log` and `governance/findings/` on each Phase completion. **Do not edit manually.** Instead, document changes in the relevant ADR (if architecture-changing) or in finding closure notes (if fix-closing-finding). The next generation will incorporate your change.

## Version History (Semantic Versioning)

### [Unreleased — Quality Transformation Program]

- **F-200** (2026-07-16): Filed Quality Transformation Program — `governance/QUALITY_BLUEPRINT.md` + findings F-201–F-236.
- **Phase 0** (2026-07-16): F-202–F-207 closed (Charter link-truth, ADR unify, taxonomy honesty, decorative-config triage, DE metric align, path scrub). F-201 remains open (BLOCKED-ON-USER Figma banner; typo'd AI banner removed from README).
- **Phase 1** (2026-07-16): F-210–F-219 closed (decision statement, hypotheses, lean-human, validity, charts, README, PDF, property tests, license, DuckDB SQL).
- **Phase 2** (2026-07-16): F-220–F-230, F-236 closed (optimizer, fair scenarios, realism, cost taxonomy, CRN, frontiers, register, memos/FAQ, deck, dbt, repro log, claims ledger).
- **Phase 3** (2026-07-16): F-231–F-235 closed (EVPI, demand frontier, publication pack, packaging, pyright strict).

(See `governance/findings/` and `QUALITY_BLUEPRINT.md` for acceptance criteria.)

### [Phase 1] — 2026-05-29: Real Check Implementations + Adversary CI Job

**Commit:** `2948e11` — feat(governance): Phase 1 — real check_*.py + Adversary CI job

Replace 18 `check_*.py` stubs with real invariant implementations.

- Every check evaluates the real condition now
- Ratchet gates: closed findings auto-enforce; open findings stay green
- Fix `verify_data_integrity.py` silent no-op (manifest key bug)
- Adversary CI job re-verifies closed findings on every PR
- F-013 (pre-commit bootstrap) marked closed + verified
- 20 findings total: 16 open, 2 in_progress, 1 closed, 1 historical
- All CI checks pass; ratchet model proven end-to-end

### [Phase 0] — 2026-05-29: Bootstrap Machine-Readable Audit State

**Commit:** `983515f` — feat(governance): bootstrap machine-readable audit state (Phase 0)

Create governance scaffold enabling cross-session memory + Adversary regression detection.

- `governance/findings/` YAML directory (20 findings, full metadata)
- `governance/AUDIT_STATE.json` (machine-generated on every `make audit`)
- Makefile `audit` / `verify` / `session-start` / `session-end` targets
- CI `governance-audit` job wired into `.github/workflows/ci.yml`
- Pre-commit hooks: `make bootstrap` installs hooks + runs `pre-commit run --all-files`
- Test framework `tests/governance/_ratchet.py` + 9 finding verification tests

### [v0.6.0] — 2026-05-21: Portfolio Audit Remediation

**Commit:** `2738eb3` — v0.6.0: Portfolio audit remediation

Full audit remediation: linting (33 errors fixed), sensititvity analysis parametrization, hypothesis status updates.

- Linting: ruff + black compliance across all modules
- Sensitivity: OAT 5-parameter sweep + Monte Carlo 10K samples
- Hypothesis status: H1–H4 with confirmed/inconclusive/rejected outcomes
- ADR-0005 & ADR-0006 authored (see `governance/adrs/`)
- Data lineage diagram + Docker CI job
- README badges + reproducibility statement

### [v0.5.0] — 2026-05-21: Reproducibility and Audit Hardening

**Commit:** `431a975` — v0.5.0: Reproducibility and audit hardening

- Kruskal-Wallis validation test (scenarios statistically indistinguishable)
- Knapp AutoStore benchmark validation (959.4 ± 43.4 orders/shift, -0.06% error)
- Weekly reproducibility workflow (`make all` run twice, hash comparison)
- Test coverage 70.5% across 108 tests

### [v0.4.0] — 2026-05-21: Simulation Correctness Milestone

**Commit:** `fb5b1c7` — v0.4.0: Simulation correctness milestone

- SimPy warehouse simulation (Module 2) validated against Knapp benchmarks
- 15 simulation replicas per scenario (75 total runs)
- Throughput metrics within 20% of published baseline

### [v0.3.0] — 2026-05-21: TCO Model + Sensitivity Analysis + German Summary

**Commit:** `cfd18a1` — v0.3.0: TCO model, sensitivity analysis, German summary

- Module 3 TCO model (5-year NPV, payback, scenarios)
- Sensitivity analysis: OAT + Monte Carlo (€1.25M labor sensitivity vs €158K capex)
- One-page German executive summary (PDF)
- All hypothesis decision rules in place

### [v0.2.0] — 2026-05-21: Pipeline Modules + Test Suite + CI/CD

**Commit:** `01da055` — v0.2.0: Pipeline modules, test suite, CI/CD

- Modules 0–3 scaffolded (data download, extraction, simulation, TCO)
- Full pytest suite (70%+ coverage target)
- `.github/workflows/` jobs: lint, test, docker-build, ssot-check
- Makefile targets for each module + linting + testing

### [v0.1.0] — 2026-05-20: Initial Scaffold + Project Charter

**Commit:** `49c852f` — v0.1.0: Initial scaffold and project charter

- Repository initialized (Python 3.11 + uv)
- PROJECT_CHARTER.md (SSOT)
- `governance/adrs/` (0001–0004)
- Basic repo structure (`src/`, `data/`, `tests/`, `config/`)
- pyproject.toml (dependencies, Black, Ruff, pytest config)

---

## Finding Closures (F-NNN Status Changes)

Each finding closure is tracked by `verification_script` passing. The Adversary CI job re-verifies on every PR.

### Closed Findings

| ID | Title | Closed | Verification Script | Status |
|---|---|---|---|---|
| F-013 | Pre-commit hooks installed locally | 2026-05-29 | `tests/governance/test_f013_bootstrap_documented.py` | ✅ PASS (re-verified Phase 1) |

### Open Findings (16)

| ID | Title | Category | Phase Due | Gap Message |
|---|---|---|---|---|
| F-001 | PROJECT_CHARTER.md oversized | Structural | 2 | 779 lines (budget 200); change_log_section_present=True |
| F-002 | Charter §11 Change Log not migrated | Structural | 2 | Changelog section present; migration to `governance/CHANGELOG.md` pending |
| F-003 | Duplicate sensitivity modules | Code | 5 | `src/warehouse_humanoid_tco/models/sensitivity.py` and `src/.../analysis/sensitivity.py` coexist |
| F-004 | Deprecated symbols not removed (export_for_powerbi) | Code | 5 | `export_for_powerbi` past sunset (2026-06-30), still present |
| F-005 | Report data stale or missing (`date: today`) | Code | 4 | 4 QMD files use `date: today`; PNG prefixes may collide |
| F-006 | CONTRIBUTING.md claims "pyright strict" but config says "basic" | Structural | 5 | typeCheckingMode='basic' vs claim 'pyright strict' |
| F-007 | Escape hatches in CI (pipeline.yml `2>/dev/null`) | Structural | 4 | Escape hatch at pipeline.yml:25; manifest missing SHA256 on 5/5 datasets |
| F-008 | Workflows not registered with gates | Structural | 1 | 4 workflows registered with gates (PASS) |
| F-009 | SSOT scope mismatch (.pre-commit ssot-check files) | Structural | 4 | 15 canonical paths not covered by `files:` pattern |
| F-010 | AUDIT_STATE.json missing or invalid | Structural | 0 | File exists, valid JSON, summary present (PASS) |
| F-011 | AUDIT_PROCEDURE.md undefined (Steward/Remediator/Adversary roles) | Structural | 3 | File exists, three roles defined (PASS, Phase 3 only) |
| F-012 | docs/todo/ accumulation (anti-pattern) | Structural | 1 | Directory absent or empty (PASS) |
| F-014 | Makefile numeric literal drift (`"15 runs"` vs `n_runs`) | Structural | 1 | "15 runs" == n_runs default 15 (PASS) |
| F-015 | CLAUDE.md missing or banned (Phase 3 only) | Structural | 3 | Created Phase 3; bans graphify claims |
| F-016 | Notebook sequence gaps or collisions | Code | 2 | Notebooks [01] form clean sequence (PASS) |
| F-017 | README Tableau "publication pending" claim | Structural | 5 | Need Tableau Public link or remove claim |
| F-018 | Config MTBF inconsistency (two humanoid values 50x apart) | Code | 5 | One consistent humanoid MTBF in autostore_baseline.yaml |
| F-019 | README missing data provenance statement | Structural | 5 | README should reference derisk_inspection_report.json |

### Historical Findings (1)

| ID | Title | Status | Note |
|---|---|---|---|
| F-000 | Placeholder | `closed_historical` | Never used; reserved for pre-Phase-0 legacy |

---

## Phase Timeline

| Phase | Start | Duration | Status | Deliverable |
|---|---|---|---|---|
| Phase 0 | 2026-05-27 | 2 days | ✅ MERGED | Governance scaffold + machine-readable audit state |
| Phase 1 | 2026-05-28 | 1 day | ✅ MERGED | Real check_*.py + Adversary + F-013 closed |
| Phase 2 | 2026-05-29 | in progress | 📝 OPEN | Charter decomposition, ADR migration |
| Phase 3 | TBD | — | ⏳ PENDING | Agent contracts (CLAUDE.md, .claude/settings.json) |
| Phase 4 | TBD | — | ⏳ PENDING | CI hardening (pipeline.yml escape hatch, ssot-check scope) |
| Phase 5 | TBD | — | ⏳ PENDING | Code cleanup (sensitivity merge, deprecation, configs) |

---

## Notes for Recruiters / Evaluators

This changelog reflects the project's **governance maturity journey** — from a traditional portfolio project (Phases 0–1) to a self-verifying, meta-audited system (Phases 2–5).

**Key milestones:**
- **Phases 0–1** establish the audit infrastructure: machine-readable state, verification contracts, Adversary regression detection.
- **Phase 2** decomposes the monolithic charter into specification modules, enabling parallel work on Phases 3–5.
- **Phases 3–5** close the actual code-level findings while keeping the audit system green — proving that the ratchet works end-to-end.

By project completion, every claim in the charter and README is **verified by an automated test** that runs on every PR. This is the distinction between a retrospectively documented portfolio project and a **durably audited analytical framework**.

