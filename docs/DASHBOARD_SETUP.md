# Dashboard Setup Guide

Complete guide for creating Tableau Public and Power BI dashboards from module outputs.

## Tableau Public (Recommended for Portfolio)

### 1. Create Public Account
- Go to https://public.tableau.com
- Sign up (free)
- Create workspace: "warehouse_humanoid_tco"

### 2. Upload Data
1. In Tableau Public, click "Create" → "Connect to Data"
2. Upload CSV files from `exports/tableau_public/`:
   - `humanoid_capabilities_summary.csv`
   - `simulation_runs.csv`
   - `tco_scenarios.csv`

### 3. Build Dashboards

**Dashboard 1: Humanoid Capabilities**
- Data: `humanoid_capabilities_summary.csv`
- Sheets:
  - Cycle Time Distribution (by task_category): histogram/box plot
  - Reach by Category: bar chart
  - Success Rate Heatmap: task_category × metric

**Dashboard 2: Warehouse Simulation**
- Data: `simulation_runs.csv`
- Sheets:
  - Throughput by Scenario: bar chart with error bars (mean ± std)
  - Queue Length Over Scenarios: line plot
  - Run-to-run Variability: box plot per scenario

**Dashboard 3: TCO Analysis (Executive)**
- Data: `tco_scenarios.csv`
- Sheets:
  - NPV Ranking: horizontal bar (winner in green)
  - Capex vs Opex Stacked Bar: composition per scenario
  - Sensitivity Table: payback period, IRR by scenario

### 4. Publish + Share
1. Publish each dashboard
2. Get shareable URL
3. Add URLs to GitHub README under "Dashboards" section

---

## Power BI (.pbix for Recruiters)

### Prerequisites
- Power BI Desktop (free download)
- Python with pandas + pyodbc (for data transformation, optional)

### 1. Load Data in Power BI
1. Open Power BI Desktop
2. Get Data → CSV
3. Load all 3 CSVs from `exports/tableau_public/`

### 2. Data Modeling
1. **Relationships:** tco_scenarios ← scenario_id → simulation_runs
2. **Calculated Columns:**
   - `NPV_Category`: IF(npv_eur > -1000000, "Expensive", "Moderate", "Optimal")
   - `Capex_Ratio`: capex / (capex + opex)

### 3. Create Report
- **Page 1:** TCO Overview
  - Card: Winner (S-hybrid-amr)
  - Card: Best NPV (€-924,125)
  - Clustered bar: NPV by scenario
  - Stacked bar: Cost breakdown

- **Page 2:** Simulation Insights
  - Scatter: throughput vs queue_length (colored by scenario)
  - Table: summary stats per scenario
  - Gauge: best-case throughput vs baseline

- **Page 3:** Capability Deep Dive
  - Slicer: task_category
  - KPI: cycle_time_mean, reach_mean, success_rate
  - Histogram: cycle_time_p95 distribution

### 4. Export & Share
1. File → Save as: `warehouse_humanoid_tco.pbix`
2. Upload to shared workspace (OneDrive, SharePoint)
3. Share link with Austrian recruiters + hiring team

---

## Quick Links

- **Data Files:** `exports/tableau_public/`
- **Executive Charts:** `reports/executive_charts/`
- **Module Reports:** `reports/module_*_report.json`
- **Data Profiling:** `notebooks/01_data_profile_summary.ipynb`
- **Charter (Methodology):** `PROJECT_CHARTER.md`
