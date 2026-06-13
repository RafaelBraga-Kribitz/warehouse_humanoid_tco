# Data Lineage

This diagram shows the end-to-end data flow for the warehouse_humanoid_tco
pipeline. Edges reflect *actual* data dependencies in the code; where a
component is computed but does not flow into a downstream result, the edge says
so explicitly (see the note on TCO below).

```mermaid
flowchart LR
    A["UnifoLM HF Datasets\n(SHA-pinned)\n5 datasets · 2,359 episodes"] --> B["Module 1\nCapability Extraction\nsrc/.../pipelines/module_01_capability_extraction.py"]
    B --> C["humanoid_capabilities_summary.parquet\ndata/processed/\n(per-category cycle time)"]
    C --> D["Module 2\nSimPy Simulation\nsrc/.../pipelines/module_02_simulation.py\nhumanoid cycle = reference_task / transfer_factor"]
    D --> E["simulation_runs.parquet\n75 runs · 5 scenarios · 15 replicas"]
    D --> P["simulation_capacity_ceiling.parquet\n(discriminating metric — chart 03)"]
    E -->|"throughput → cost_per_order only"| F["Module 3\nTCO Financial Model\nsrc/.../pipelines/module_03_tco.py"]
    F --> G["tco_scenarios.parquet\ndata/processed/"]
    G --> H["Module 4\nTableau Public (CSV)\nexports/tableau_public/"]
    P --> H
    G --> I["Executive Charts\nreports/executive_charts/\n5 PNGs"]
    P --> I
    F --> J["Sensitivity Analysis\nsrc/.../analysis/sensitivity.py\n10K Monte Carlo + OAT"]
    J --> K["sensitivity_analysis_report.json\nreports/"]
    J --> I
    L["config/autostore_baseline.yaml\nlayout · agents · agent_counts\ncapability_transfer factor"] --> D
    L --> F
    M["config/tco_assumptions.yaml\nfinancial · labor · capex\nsensitivity ranges/distributions"] --> F
    M --> J
    N["config/seeds.yaml"] --> D
    O["config/dataset_manifest.yaml\nSHA pins for reproducibility"] --> A
```

### How the TCO result is actually driven

The 5-year NPV per scenario is a function of the **agent composition**
(`config/autostore_baseline.yaml::scenarios.agent_counts`) and the **financial
assumptions** (`config/tco_assumptions.yaml`, wired in via
`module_03_tco.build_financial_params`). Simulation throughput does **not** drive
NPV/opex — at the modeled 120 orders/hr arrival every scenario is demand-bound
(ρ < 0.4), so throughput is ~constant. Throughput enters only the
`cost_per_order` denominator (hence the labeled `E → F` edge). The discriminating
operational metric is the capacity-ceiling sweep (`P`), not operating throughput.

## Key files

| Artifact | Path | Produced by |
|---|---|---|
| Raw episodes | `data/raw/*/` | HuggingFace download (`scripts/download_data.py`) |
| Capabilities summary | `data/processed/humanoid_capabilities_summary.parquet` | Module 1 |
| Simulation runs | `data/processed/simulation_runs.parquet` | Module 2 |
| Capacity ceiling | `data/processed/simulation_capacity_ceiling.parquet` | Module 2 |
| TCO scenarios | `data/processed/tco_scenarios.parquet` | Module 3 |
| OAT sensitivity | `data/processed/sensitivity_oat_results.parquet` | `analysis/sensitivity.py` |
| MC samples | `data/processed/sensitivity_mc_samples.parquet` | `analysis/sensitivity.py` |
| Executive charts | `reports/executive_charts/*.png` (5) | Module 4 + `scripts/generate_tornado_chart.py` |
| Tableau CSVs | `exports/tableau_public/*.csv` | Module 4 |

## Reproducibility

All outputs are deterministically reproducible given the same inputs and seed
(`config/seeds.yaml`). The weekly reproducibility CI (`reproducibility.yml`) runs
`make all` twice and compares output hashes.
