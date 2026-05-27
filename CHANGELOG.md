# Changelog

All notable changes to this project are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions are thematic milestones, not strict semver releases.

---

## [v0.6.0] — Portfolio Audit Remediation — 2026-05-27

### Added
- TCO sensitivity deep-dive notebook (`notebooks/04_tco_sensitivity_deep_dive.py`) showing labor variables drive ~5× more NPV swing than humanoid capex.
- Kruskal-Wallis non-parametric throughput-distribution test in `evaluation/validation.py` with three regression tests; SciPy added as an explicit dependency.
- German translation of ADR-0007 for Austrian readers.
- Mock-based tests for `data/download.py`, bringing that module from 0% to 100% coverage.
- Per-profile agent-utilization metric in the simulation (was previously hardcoded to `None`).

### Fixed
- **Sensitivity: `discount_rate` is now actually varied in the OAT sweep.** It was listed in `param_ranges` but the OAT loop called `compute_tco_for_params` without the `discount_rate` kwarg, so the sweep silently used the default 0.08. Re-running with the fix shifts MC mean to €-1,091,914 ± €418,038 and median to €-1,061,736; 90% CI [€-1.83M, €-460K]. README/Charter updated; the prior README labelled the mean as P50, which is a distinct statistic, and that label is now correct.
- Tornado chart's `PARAM_LABELS` realigned with the sensitivity-output schema; legacy `np.random.seed` migrated to `np.random.default_rng`.
- Removed an unused `numpy.random as npr` import left over from the `default_rng` migration.

### Changed
- NPV calculation unified across modules: `analysis/sensitivity.py` now delegates to `models.tco.compute_npv` instead of carrying a parallel manual-discounting implementation.
- `compute_payback_years` docstring clarifies that the metric is undiscounted; pointer added for discounted-payback users.
- CHANGELOG introduced (this file) to organize 80+ chronological commits into thematic milestones.

---

## [v0.5.0] — Reproducibility & Audit Hardening — 2026-05-26

### Added
- Committed `derisk_inspection_report.json` as a reproducibility artifact so pipeline outputs are traceable across runs.
- SHA256 manifest verification script (`config/dataset_manifest.yaml`) to catch silent data drift.
- Docker build CI job that exercises the actual `Dockerfile`, preventing it from diverging into documentation.
- `uv.lock` for fully deterministic dependency resolution; setup target migrated to `uv sync --frozen`.
- `npv_std > 0` regression guard in the sensitivity test suite to catch Monte Carlo parameter collapse.

### Fixed
- `tco_results` Parquet output now sorted by `scenario_id` for byte-for-byte deterministic output across runs.
- Makefile uses `?=` for `VENV`/`PYTHON` so CI environment variables take precedence over local defaults.
- VENV path corrected to `.venv`; `DASHBOARD_SETUP.md` reference fixed in Makefile.
- CI and Docker base image aligned to Python 3.11 across all workflow jobs.
- Reproducibility workflow CI job correctly overrides `VENV` for system-level installs.
- Internal audit response removed from the public tree; `audit_response` added to `.gitignore`.

### Changed
- `tco_scenarios` CSV extended to include simulation run counts and throughput metrics.
- Tornado chart migrated from legacy `np.random` to `np.random.default_rng` for reproducible seeding.
- `PARAM_LABELS` aligned with actual sensitivity output schema, fixing label mismatches in chart output.

---

## [v0.4.0] — Simulation Correctness & Statistical Rigor — 2026-05-22

### Added
- ADR-0007 documenting the agent routing bug discovery and the decision to correct rather than suppress it.
- Regression test asserting that orders are distributed across all agent profiles, not collapsed to a single profile.
- Real-data integration test fixture and `conftest.py` for end-to-end module testing.

### Fixed
- Critical simulation bug: orders were routed only to the first agent profile; corrected so all profiles receive distributed workload.
- Removed misleading `npv_std` and confidence interval fields from TCO output — throughput simulation does not scale fixed labor costs, so variance fields were statistically invalid.
- H1 hypothesis outcome corrected; German executive summary contained a math error; Python version standardized to 3.11 throughout docs.
- LinkedIn post updated to honestly describe the simulation bug discovery rather than elide it.

### Changed
- ADR-0006 marked superseded; ADR-0007 records the corrected approach.
- Module 2 report corrected to reflect 75 simulation runs (15 per scenario), not the previously stated 3.

---

## [v0.3.0] — TCO Model & Sensitivity Analysis — 2026-05-21

### Added
- Monte Carlo sensitivity analysis with 10,000 samples; results surface labor headcount as the dominant NPV driver.
- One-at-a-time (OAT) sensitivity tornado chart showing ranked parameter influence.
- `capability_transfer` factor and operational realism parameters added to config for scenario tuning.
- German-language executive summary populated with real TCO results and rendered to HTML via Quarto.
- Kruskal-Wallis non-parametric test added to README to support H2 hypothesis reporting.
- Assumptions catalog fully documented with source references.
- Data lineage Mermaid diagram showing end-to-end pipeline flow from raw datasets to outputs.
- ADR-0005 and ADR-0006 documenting real development dead-ends, including the simulation exploration notebook.

### Fixed
- IRR metric removed from TCO output — undefined for a cost-only model; payback calculation corrected to undiscounted form with rationale documented.
- `AUDIT_RESPONSE.md` relocated from repo root to `docs/` to comply with charter §2.4 SSOT file placement rules.
- Charter §3.7 updated with a limitations table; H1–H4 hypothesis statuses resolved to confirmed / rejected / inconclusive.

### Changed
- Hypothesis H1 status updated to reflect actual NPV direction from corrected simulation data.
- README extended with CI badge, decision-language results summary, and "why this project" section.

---

## [v0.2.0] — Simulation Engine & Pipeline Modules — 2026-05-21

### Added
- Module 0 (de-risk): dataset collection and validation against a curated set of humanoid capability sources.
- Module 1: capability extraction pipeline processing 2,359 episodes from 5 source datasets.
- Module 2–3: simulation outputs and TCO computation using real capability data.
- Module 4: Tableau-compatible exports and executive summary charts.
- Comprehensive test suite at 70.5% coverage (108 tests, 0 failures).
- Taxonomy classifier with first-match-wins logic and Polars-native schemas.
- GitHub Actions CI/CD pipeline with lint, type-check (Pyright basic mode), Black, and markdown allowlist checks.
- Makefile automation for full pipeline execution and environment setup.
- Tableau Public and Power BI setup guides for dashboard creation from pipeline outputs.

### Fixed
- Ruff linting compliance across all source modules.
- Pyright type errors resolved (7 fixes); `upload-artifact` action pinned to v4.
- CI failures resolved: lint, Black formatting, SSOT ADR presence check, markdown allowlist, Dockerfile `LICENSE` copy.
- Docker editable install corrected; Pipeline workflow scoped to `workflow_dispatch` only.

### Changed
- P0 audit fixes applied for credibility consistency and SSOT compliance.
- P1 statistical rigor improvements: simulation run count increased, environment consistency hardened.

---

## [v0.1.0] — Initial Scaffold & Project Charter — 2026-05-21

### Added
- Full project directory structure: `src/`, `tests/`, `config/`, `docs/`, `notebooks/`, `outputs/`.
- SSOT project charter (`PROJECT_CHARTER.md`) with functional requirements FR-01 through FR-11.
- Initial ADR set (ADR-0001 through ADR-0004) covering toolchain, data format, and model scope decisions.
- `config/` YAML files for scenario parameters, dataset manifest, and cost assumptions.
- Source module stubs with typed interfaces for all four pipeline modules.
- Minimal test scaffolding with placeholder assertions.
- `Dockerfile` and `.github/workflows/` skeletons for CI/CD.
- `.gitignore` configured for large files, virtual environments, and internal working documents.

---

[v0.6.0]: https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/compare/v0.5.0...HEAD
[v0.5.0]: https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/compare/v0.4.0...v0.5.0
[v0.4.0]: https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/compare/v0.3.0...v0.4.0
[v0.3.0]: https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/compare/v0.2.0...v0.3.0
[v0.2.0]: https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/compare/v0.1.0...v0.2.0
[v0.1.0]: https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/releases/tag/v0.1.0
