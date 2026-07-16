# Repository Structure

| Top-level path | Purpose |
|---|---|
| `.github/` | CI workflows and repository automation. |
| `.cursor/` | Local Cursor configuration; plans are not project authority. |
| `config/` | Versioned simulation, financial, seed, and dataset configuration. |
| `data/` | Raw manifests plus interim and processed analytical data. |
| `docker/` | Container build and compose definitions. |
| `docs/` | Supporting user documentation, dashboard setup, and taxonomy rules. |
| `exports/` | Published Tableau-ready CSV outputs. |
| `governance/` | Findings, ADRs, registers, audit state, and operating procedure. |
| `notebooks/` | Exploratory and reproducible notebook sources. |
| `reports/` | Generated reports, executive charts, and presentation artifacts. |
| `scripts/` | Maintenance, governance, and pipeline helper scripts. |
| `src/` | Installable Python package and Modules 1–4 implementation. |
| `tests/` | Unit, integration, property, and governance verification tests. |
| `.gitignore` | Version-control exclusions. |
| `CLAUDE.md` | Agent operating protocol for the repository. |
| `CONTRIBUTING.md` | Contribution and documentation-discipline guidance. |
| `LICENSE` | MIT license text. |
| `Makefile` | Standard project entry points. |
| `PROJECT_CHARTER.md` | Project single source of truth. |
| `README.md` | Quick start and portfolio-facing overview. |
| `pyproject.toml` | Python package metadata, dependencies, and tool configuration. |
| `requirements.txt` | Exported dependency requirements for non-uv users. |
| `uv.lock` | Locked dependency resolution. |

Generated local environments and caches are intentionally excluded from this
map because they are not repository artifacts.
