# warehouse_humanoid_tco

A reproducible analytical framework for the Total Cost of Ownership of humanoid robots in Austrian intralogistics, built as a Data Analytics / Business Intelligence portfolio project.

> **All authoritative project information lives in `[PROJECT_CHARTER.md](./PROJECT_CHARTER.md)`.** This README intentionally does not duplicate it. If you want the goals, scope, requirements, design decisions, or anything else about the project, open the Charter.

## What it does (one paragraph)

Extracts humanoid robot task capabilities from the open Unitree UnifoLM-WBT dataset, simulates an AutoStore-style warehouse with configurable workforce mixes (human, humanoid, AMR), computes Total Cost of Ownership over 5 years using Austrian labor cost inputs, and publishes results to Tableau Public and Power BI. The entire pipeline is reproducible; the entire methodology is documented.

## Quick start

```bash
# Clone
git clone <repo-url>
cd warehouse_humanoid_tco

# Install dependencies (one-time)
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run the de-risk notebook (Module 0)
jupytext --to ipynb notebooks/00_derisk_dataset_inspection.py
jupyter notebook notebooks/00_derisk_dataset_inspection.ipynb

# Run the full pipeline
make all
```

## Documentation entry points

- `[PROJECT_CHARTER.md](./PROJECT_CHARTER.md)`: the Single Source of Truth.
- `[CONTRIBUTING.md](./CONTRIBUTING.md)`: documentation discipline and ADR rules.
- `[docs/ADR/](./docs/ADR/)`: architecture decisions, append-only.
- `[reports/](./reports/)`: rendered audit reports for each module.

## License

MIT. See `LICENSE`.

## Author

Rafael Braga-Kribitz, Seiersberg-Pirka, Austria. Portfolio project, 2026.