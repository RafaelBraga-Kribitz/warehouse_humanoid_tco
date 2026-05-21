# Data Lineage

This diagram shows the end-to-end data flow for the warehouse_humanoid_tco pipeline.

```mermaid
flowchart LR
    A["UnifoLM HF Datasets\n(SHA-pinned)\n5 datasets · 2,359 episodes"] --> B["Module 1\nCapability Extraction\nsrc/pipelines/module_01_extraction.py"]
    B --> C["humanoid_capabilities_summary.parquet\ndata/processed/"]
    C --> D["Module 2\nSimPy Simulation\nsrc/pipelines/module_02_simulation.py"]
    D --> E["simulation_runs.parquet\ndata/processed/\n75 runs · 5 scenarios · 15 replicas"]
    E --> F["Module 3\nTCO Financial Model\nsrc/pipelines/module_03_tco.py"]
    F --> G["tco_scenarios.parquet\ndata/processed/"]
    G --> H["Module 4\nTableau Public + Power BI\nexports/tableau_public/"]
    G --> I["Executive Charts\nreports/executive_charts/\n4 PNGs"]
    G --> J["Sensitivity Analysis\nmodels/sensitivity.py\n10K Monte Carlo + OAT"]
    J --> K["sensitivity_analysis_report.json\nreports/"]
    J --> I
    L["config/autostore_baseline.yaml\nlayout · agents · scenarios\ncapability_transfer factor"] --> D
    M["config/tco_assumptions.yaml\nfinancial · labor · capex\nMonte Carlo parameters"] --> F
    N["config/seeds.yaml"] --> D
    N --> F
    O["config/dataset_manifest.yaml\nSHA pins for reproducibility"] --> A
```

## Key files

| Artifact | Path | Produced by |
|---|---|---|
| Raw episodes | `data/raw/*/` | HuggingFace download (`scripts/download_data.py`) |
| Capabilities summary | `data/processed/humanoid_capabilities_summary.parquet` | Module 1 |
| Simulation runs | `data/processed/simulation_runs.parquet` | Module 2 |
| TCO scenarios | `data/processed/tco_scenarios.parquet` | Module 3 |
| OAT sensitivity | `data/processed/sensitivity_oat_results.parquet` | Module 3 sensitivity |
| MC samples | `data/processed/sensitivity_mc_samples.parquet` | Module 3 sensitivity |
| Executive charts | `reports/executive_charts/*.png` | Module 3 + scripts |
| Tableau CSVs | `exports/tableau_public/*.csv` | Module 4 |

## Reproducibility

All outputs are deterministically reproducible given the same inputs and seed (`config/seeds.yaml`). The weekly reproducibility CI (`reproducibility.yml`) runs `make all` twice and compares output hashes.
