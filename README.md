# warehouse_humanoid_tco

[![Pipeline](https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/actions/workflows/pipeline.yml/badge.svg)](https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/actions/workflows/pipeline.yml)

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

## Results Summary

**Pipeline Status:** ✓ All modules complete with real data (2026-05-21). Modules 1–3 executed on 2,359 real humanoid episodes from Unitree UnifoLM datasets.

### Data
- **2,359 episodes** extracted from 5 UnifoLM datasets (WBT + DiverseManip)
- **Capabilities profiled:** cycle time, reach, energy, success rate by task category
- **Validation:** Full data profiling notebook in `[notebooks/01_data_profile_summary.ipynb](./notebooks/01_data_profile_summary.ipynb)` (stakeholder transparency)

### Simulation
- **75 runs total** across 5 warehouse scenarios (15 replicas per scenario)
- **Scenarios:** baseline human, pure humanoid, hybrid (50/50), hybrid + AMR, future 2028
- **Metrics:** orders per shift, queue length, utilization (with 90% CI across runs)

### Financial Analysis (5-year horizon, 8% discount)
| Scenario | NPV | Capex | Opex 5yr |
|----------|-----|-------|----------|
| S-baseline-human | €-1,608,300 | €0 | €2,014,000 |
| **S-hybrid-amr** | **€-924,125** | **€120K** | **€1,007K** |
| S-hybrid-5050 | €-1,284,100 | €480K | €1,007K |
| S-pure-humanoid | €-960,000 | €960K | €0 |
| S-future-2028 | €-1,284,100 | €480K | €1,007K |

**Winner:** S-hybrid-amr (20% humanoid + 20% AMR minimizes total cost).

> **Real data execution:** Results computed from 2,359 episodes across 5 Unitree UnifoLM datasets (WBT + DiverseManip). Financial model uses 15 simulation replicas per scenario with Austrian labor cost inputs (€18.50/hr + 1.35× overhead).

### Sensitivity Analysis
- **Monte Carlo (10,000 runs):** NPV = €-1,084,673 ± €414,024
  - 90% confidence interval: [€-1.8M, €-463k]
  - Varies humanoid capex, labor costs, overhead, and agent counts
- **One-at-a-time (OAT):** Identifies top parameter drivers
- **Report:** `[reports/sensitivity_analysis_report.json](./reports/sensitivity_analysis_report.json)`

### Executive Charts
- [TCO NPV Ranking](./reports/executive_charts/01_tco_npv_ranking.png)
- [Cost Breakdown](./reports/executive_charts/02_cost_breakdown.png)
- [Simulation Throughput](./reports/executive_charts/03_simulation_throughput.png)

### Dashboards (In Progress)
- **Tableau Public:** CSVs ready in `exports/tableau_public/` → [create public dashboard](#for-recruiters)
- **Power BI:** exported data ready for `.pbix` creation

## For Recruiters

**What this shows:**
1. ✓ Data pipeline rigor: end-to-end extraction, validation, profiling
2. ✓ Statistical modeling: SimPy discrete-event simulation with empirical inputs
3. ✓ Financial analysis: NPV, sensitivity, payback period for business decisions
4. ✓ Reproducibility: every result is version-controlled and auditable

**How to explore:**
1. Read `[PROJECT_CHARTER.md](./PROJECT_CHARTER.md)` for methodology + assumptions
2. Review `[notebooks/01_data_profile_summary.ipynb](./notebooks/01_data_profile_summary.ipynb)` for data validation
3. Check `[reports/](./reports/)` for Module 0–4 validation reports
4. View executive charts in `[reports/executive_charts/](./reports/executive_charts/)`
5. (Coming soon) Tableau Public dashboards + Power BI `.pbix` file

## Documentation entry points

- `[PROJECT_CHARTER.md](./PROJECT_CHARTER.md)`: the Single Source of Truth.
- `[CONTRIBUTING.md](./CONTRIBUTING.md)`: documentation discipline and ADR rules.
- `[docs/ADR/](./docs/ADR/)`: architecture decisions, append-only.
- `[reports/](./reports/)`: rendered audit reports + executive charts for each module.
- `[notebooks/01_data_profile_summary.ipynb](./notebooks/01_data_profile_summary.ipynb)`: data transparency + stakeholder briefing.

## License

MIT. See `LICENSE`.

## Author

Rafael Braga-Kribitz, Seiersberg-Pirka, Austria. Portfolio project, 2026.