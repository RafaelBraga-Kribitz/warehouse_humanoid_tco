# warehouse_humanoid_tco

![Hero Banner](./docs/assets/hero-banner.png)

[![CI](https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/actions/workflows/ci.yml/badge.svg)](https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/actions/workflows/ci.yml)
[![Reproducibility](https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/actions/workflows/reproducibility.yml/badge.svg)](https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco/actions/workflows/reproducibility.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Governance Audited](https://img.shields.io/badge/governance-audited-brightgreen)](governance/AUDIT_PROCEDURE.md)

A reproducible analytical framework for the Total Cost of Ownership of humanoid robots in Austrian intralogistics, built as a Data Analytics / Business Intelligence portfolio project.

> **All authoritative project information lives in [📋 PROJECT_CHARTER.md](./PROJECT_CHARTER.md).** This README intentionally does not duplicate it. If you want the goals, scope, requirements, design decisions, or anything else about the project, open the Charter.

## Demo

![60-second demo: clean history, Monte Carlo, scenario ranking, test suite](./docs/assets/demo.gif)

## What it does

Extracts humanoid robot task capabilities from the open Unitree UnifoLM-WBT dataset, simulates an AutoStore-style warehouse with configurable workforce mixes (human, humanoid, AMR), computes Total Cost of Ownership over 5 years using Austrian labor cost inputs, and publishes results to Tableau Public (CSV exports also import directly into Power BI). The entire pipeline is reproducible; the entire methodology is documented.

## Quick start

```bash
# Clone
git clone https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco.git
cd warehouse_humanoid_tco

# Fetch the raw datasets (Git-LFS-backed). Without this, data/raw/ holds only
# LFS pointer files and `make all` fails closed at Module 1 (0 episodes).
git lfs install && git lfs pull

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

**For users without `uv`:** A frozen `requirements.txt` is committed (regenerated from `uv.lock` via `uv export --format requirements-txt --no-hashes --no-emit-project`):
```bash
pip install -r requirements.txt
```

## Results Summary

**Pipeline Status:** ✓ All modules complete with real data (2026-05-21). Modules 1–3 executed on 2,359 real humanoid episodes from Unitree UnifoLM datasets.

### Data

- **2,359 episodes** extracted from 5 UnifoLM datasets (WBT + DiverseManip)
- **Capabilities profiled:** cycle time, reach, energy, success rate by task category
- **Multi-label taxonomy:** every episode is tagged with all applicable categories (avg 2.29 labels/episode; 1,750 / 2,359 = 74% multi-labeled). Coverage: `pick_medium_object` 2,359 · `place_general` 1,750 · `transport_short` 757 · `bimanual_handling` 525 episodes
- **What the capability profile does and does not differentiate:** cycle time varies meaningfully by task category and is the capability that feeds the simulation. `reach` and `energy_proxy` are computed only from the DiverseManip subset (the WBT subsets lack a usable state/action vector), so their per-category means are shared across categories rather than category-specific — treat them as dataset-level estimates, not task discriminators. `success_rate` is **1.0 for every category by construction**: the UnifoLM episodes are curated successful teleoperation demonstrations, so this is demonstration-completion, *not* a production reliability estimate. The simulation does not use `success_rate`.
- **Provenance:** every claim about dataset accessibility, episode counts, and SHA-pinned revisions traces to [`reports/derisk_inspection_report.json`](./reports/derisk_inspection_report.json) (the Module 0 de-risk audit, run before pipeline execution). This is the single authoritative source for "what data is real vs. synthetic" in this project.
- **Validation:** Full data profiling notebook in [📊 notebooks/01_data_profile_summary.ipynb](./notebooks/01_data_profile_summary.ipynb) (stakeholder transparency)

### Simulation

- **75 runs total** across 5 warehouse scenarios (15 replicas per scenario)
- **Scenarios:** baseline human, pure humanoid, hybrid (50/50), hybrid + AMR, future 2028
- **Metrics:** orders per shift, queue length, utilization (with 90% CI across runs)

### Financial Analysis (5-year horizon, 8% discount)


NPV is the discounted 5-year total cost. "Total cost reduction" is the NPV reduction vs. the human baseline (it accounts for capex). Note that the opex-only "cost reduction" shown in the Tableau CSV (`cost_reduction_vs_baseline_pct` / `opex_reduction_vs_baseline_pct`) is a different, larger number because it ignores capital expenditure — e.g. pure-humanoid is 70% lower on operating cost but only **3.9%** lower on total cost once its €1,064K capex is counted. Use total-cost reduction for ranking.

| Scenario         | NPV             | Capex      | Opex 5yr      | Cost/Order | Total cost ↓ vs baseline |
| ---------------- | --------------- | ---------- | ------------- | ---------- | ------------------------ |
| S-baseline-human | €-1,608,251     | €0         | €2,013,984    | €1.344     | 0.0%                     |
| S-hybrid-5050    | €-1,576,941     | €532K      | €1,308,562    | €1.324     | 1.9%                     |
| S-pure-humanoid  | €-1,545,632     | €1,064K    | €603,139      | €1.295     | 3.9%                     |
| S-future-2028    | €-1,398,599     | €409K      | €1,238,969    | €1.171     | 13.0%                    |
| **S-hybrid-amr** | **€-1,078,786** | **€198K**  | **€1,102,993**| **€0.904** | **32.9%**                |

![NPV Ranking — S-hybrid-amr lowest 5-year cost at €-1.08M](./reports/executive_charts/01_tco_npv_ranking.png)

> **Plain-language summary:** The leanest mix, S-hybrid-amr, fields a 6-unit crew (4 human + 1 humanoid + 1 AMR) and cuts 5-year warehouse costs from €1.6M to €1.08M — a ~33% total-cost saving, or €0.44/order cheaper than the 8-human baseline. Part of that advantage comes from fielding fewer total units, which the simulation confirms is feasible at the modeled 120 orders/hr demand (utilisation ρ < 1). At current humanoid capex (€120K/unit), pure-humanoid reaches cost parity with the human baseline with about €5.6K of headroom. Labor cost is the dominant uncertainty — its OAT elasticity (~0.76 for both wage and overhead) is roughly 5× that of humanoid capex (~0.15); the capital investment is the comparatively smaller risk.

**Under the modeled assumptions, S-hybrid-amr minimizes 5-year total cost by ~33% vs. the human baseline.** It does so with a leaner 6-unit crew (vs. 8 for the baseline); the agent counts per scenario are explicit in `config/autostore_baseline.yaml::scenarios.agent_counts`. Annual opex includes humanoid maintenance (8% of capex), energy, and a 0.10 FTE supervision overhead per humanoid; AMR scenarios also include AMR capex and opex. The advantage is sensitive to humanoid capex (see the sensitivity tornado below). Pure-humanoid reaches cost-parity with the human baseline at ≤€125,582/unit capex (current: €120K → €5.6K headroom; see `reports/module_03_tco_report.json::breakeven_thresholds`). The model applies the 70% WBT-to-production transfer factor to the simulated humanoid cycle time (production runs slower than the teleoperation demos); see PROJECT_CHARTER.md §3.7 for the rationale.

> **Real data execution:** Results computed from 2,359 episodes across 5 Unitree UnifoLM datasets (WBT + DiverseManip). Financial model uses 15 simulation replicas per scenario with Austrian labor cost inputs (€18.50/hr + 1.35× overhead).

### Sensitivity Analysis

- **Monte Carlo (10,000 runs × 5 scenarios = 50,000 samples, all persisted):** S-hybrid-amr NPV mean = €-1,089,021 ± €171,407 (1σ); median = €-1,079,103
  - 90% output interval (p5–p95): [€-1,386,257, €-830,291]
  - Per-scenario MC with **agent counts fixed**; samples only continuous params: humanoid capex, labor wage, labor overhead, discount rate, WBT→production transfer factor (5 parameters)
  - S-hybrid-amr is the only scenario whose worst case (p5 = €-1.39M) still beats the baseline mean (€-1.62M); its entire 90% interval [€-1.39M, €-830K] sits above the baseline expectation — it is robustly the cheapest under uncertainty
- **OAT Tornado (S-hybrid-amr):** ranked by normalised elasticity (range-independent, per F-030), labor dominates — overhead and wage each have elasticity ≈ 0.76, vs. WBT transfer factor 0.25, discount rate 0.19, and humanoid capex 0.15 (so labor is ~5× more elastic than capex). The corresponding peak NPV swings across each parameter's stress range are overhead ±€214K, wage ±€156K, discount rate ±€101K, capex ±€79K, transfer factor ±€77K. (OAT swings are *not* additive — labor's dominance is the elasticity result, not a sum of one-at-a-time deltas.) All figures are reproducible from [`reports/sensitivity_analysis_report.json`](./reports/sensitivity_analysis_report.json)`::oat_elasticity_ranking`.

#### Executive Charts

| Chart | View | Data |
|-------|------|------|
| **NPV Ranking** | ![](./reports/executive_charts/01_tco_npv_ranking.png) | [📥 01_tco_npv_ranking.png](./reports/executive_charts/01_tco_npv_ranking.png) |
| **Cost Breakdown** | ![](./reports/executive_charts/02_cost_breakdown.png) | [📥 02_cost_breakdown.png](./reports/executive_charts/02_cost_breakdown.png) |
| **Capacity Ceiling** | ![](./reports/executive_charts/03_simulation_throughput.png) | [📥 03_simulation_throughput.png](./reports/executive_charts/03_simulation_throughput.png) |
| **Sensitivity Tornado** | ![](./reports/executive_charts/04_sensitivity_tornado.png) | [📥 04_sensitivity_tornado.png](./reports/executive_charts/04_sensitivity_tornado.png) |
| **Cost per Order** | ![](./reports/executive_charts/05_cost_per_order.png) | [📥 05_cost_per_order.png](./reports/executive_charts/05_cost_per_order.png) |

**Full Report:** [📄 reports/sensitivity_analysis_report.json](./reports/sensitivity_analysis_report.json)

### Dashboards

- **[Tableau Public Dashboard](https://public.tableau.com/app/profile/rafael.braga.kribitz/viz/HumanoidRoboticsTCO/Dashboard1)** — Interactive TCO, simulation, and capabilities analysis
- The same CSV exports in [`exports/tableau_public/`](./exports/tableau_public/) import directly into Power BI Desktop. Tableau Public is the single published dashboard surface (see ADR-0008); no separate `.pbix` is shipped.

## For Recruiters

**Austrian hiring managers:** → **[Kurzfassung auf Deutsch](./reports/Executive_Summary_DE.qmd)** — Analyse unter österreichischen Kollektivvertragslöhnen und Betriebsratsanforderungen

**What this shows:**

1. ✓ Data pipeline rigor: end-to-end extraction, validation, profiling
2. ✓ Statistical modeling: SimPy discrete-event simulation with empirical cycle times from 2,359 UnifoLM episodes; throughput is demand-bound at the modeled 120 orders/hr arrival (ρ < 0.4 in every scenario), so the discriminating metric is the capacity ceiling sweep (max sustainable 209–979 orders/hr across scenarios at ρ=0.85), not operating throughput; see ADR-0007 for agent routing bug fix
3. ✓ Financial analysis: NPV, sensitivity, payback period for business decisions
4. ✓ Reproducibility: every result is version-controlled and auditable

**How to explore:**

1. Read [📋 PROJECT_CHARTER.md](./PROJECT_CHARTER.md) for methodology + assumptions
2. Review [📊 notebooks/01_data_profile_summary.ipynb](./notebooks/01_data_profile_summary.ipynb) for data validation
3. Check [📁 reports/](./reports/) for Module 0–4 validation reports
4. View [📈 executive_charts/](./reports/executive_charts/) (NPV, Cost, Throughput, Sensitivity, Cost/Order)
5. View the live dashboard: [📊 Tableau Public](https://public.tableau.com/app/profile/rafael.braga.kribitz/viz/HumanoidRoboticsTCO/Dashboard1) or browse [📊 exports/tableau_public/](./exports/tableau_public/) (CSVs for local BI import)

## Documentation Entry Points

| Document | Purpose |
|----------|---------|
| [📋 PROJECT_CHARTER.md](./PROJECT_CHARTER.md) | **SSOT.** Goals, scope, requirements, decisions, change log |
| [📝 CONTRIBUTING.md](./CONTRIBUTING.md) | Discipline rules: ADRs, Markdown allowlist, coding standards |
| [🏛️ docs/ADR/](./docs/ADR/) | Architecture Decision Records (append-only log) |
| [📊 reports/](./reports/) | Audit + validation reports + executive charts (all modules) |
| [📊 notebooks/01_data_profile_summary.ipynb](./notebooks/01_data_profile_summary.ipynb) | Data validation + stakeholder transparency |
| [📐 docs/data_lineage.md](./docs/data_lineage.md) | Pipeline data flow diagram (Mermaid) |
| [📈 reports/executive_charts/](./reports/executive_charts/) | 5 finalized business charts (ranking, cost, throughput, sensitivity, cost/order) |

## Why this project

I live 20 minutes from Knapp AG's headquarters and wanted to understand what operations analysts there are actually evaluating when they look at humanoid robot integration in 2026; not the hype cycle, but the unit economics. 

The biggest surprise was how much the sensitivity analysis depends on headcount assumptions rather than robot capex: if you have 8 workers and replace 1.6 of them with 1.6 humanoids, the labor savings math is almost entirely driven by how many human FTEs you actually need, not by whether the robot costs €100K or €180K. 

The second surprise was the 3× variance in cycle time across task categories in the real UnifoLM data — pick tasks are far noisier than place tasks, which makes the hybrid-AMR advantage fragile in some scenarios. With more time I would calibrate against actual Knapp throughput benchmarks rather than public estimates, and add a proper learning curve for humanoid performance over the first 12 months of deployment.

## License

[📄 MIT](./LICENSE)

## Author

Rafael Braga-Kribitz, Seiersberg-Pirka, Austria. Portfolio project, 2026.