# Power BI Dashboard Setup Guide

> **Status (ADR-0008):** Power BI is an **optional, user-side** path. The single
> *published* dashboard surface for v1.0 is Tableau Public; no `.pbix` is built
> or committed to this repository. This guide is a convenience for users who
> prefer to import the same CSVs into Power BI.

This guide explains how to create a Power BI dashboard from the exported CSV data.

## Data Files

The following CSV files are ready for Power BI import (located in `exports/tableau_public/`):

1. **tco_scenarios.csv** — TCO results by scenario (NPV, capex, opex, payback)
2. **simulation_runs.csv** — Simulation raw results (15 runs × 6 scenarios)
3. **humanoid_capabilities_summary.csv** — Task-level humanoid capabilities

## Steps to Create .pbix File

### 1. Open Power BI Desktop

Download from https://powerbi.microsoft.com/en-us/downloads/ if not already installed.

### 2. Import Data

In Power BI Desktop:
- **Home > Get Data > CSV**
- Navigate to `exports/tableau_public/tco_scenarios.csv`
- Click **Load**
- Repeat for `simulation_runs.csv` and `humanoid_capabilities_summary.csv`

**Note:** Power BI will auto-detect column types. Verify:
- `npv_eur`, `total_capex_eur`, `total_opex_5yr_eur_nominal`, `total_opex_5yr_eur_pv` are detected as numbers
- `scenario_id` is text
- `payback_years` is number (handles nulls)

### 3. Create Relationships (Optional but Recommended)

In **Model** view, create a relationship:
- Table: `simulation_runs`
- To: `tco_scenarios`
- Matching column: `scenario_id`

This allows cross-filtering between simulation runs and TCO results.

### 4. Build Visualizations

Create the following pages in your report:

#### Page 1: TCO Summary

**Visual 1: NPV Ranking (Horizontal Bar Chart)**
- Category: `scenario_id` (from `tco_scenarios`)
- Values: `npv_eur`
- Sort by `npv_eur` ascending
- Color: Highlight winning scenario (S-hybrid-amr) in green

**Visual 2: Capex vs Opex Breakdown (Stacked Bar)**
- Category: `scenario_id`
- Values: `total_capex_eur`, `total_opex_5yr_eur_pv` (use the PV form so it stacks apples-to-apples with capex)
- Title: "Cost Composition by Scenario"

**Visual 3: Key Metrics (Card Visuals)**
- Winning scenario (S-hybrid-amr)
- Best NPV: €-924,125
- Cost reduction vs baseline: 50%
- Payback period: 0.6 years

#### Page 2: Simulation Results

**Visual 1: Throughput Distribution (Box Plot or Column Chart)**
- Category: `scenario_id`
- Values: `throughput_orders_per_shift`
- Add standard deviation error bars if available

**Visual 2: Queue Length Comparison**
- Category: `scenario_id`
- Values: `queue_length_mean`

**Visual 3: Run Count**
- Filter: Shows number of simulation replicas per scenario (should be 15 each)

#### Page 3: Capabilities

**Visual 1: Task Categories (Table)**
- Columns: `task_category`, `n_episodes`, `cycle_time_mean`, `cycle_time_std`
- Allows users to drill into cycle time variance by task

### 5. Add Filters

On each page, add a slicer for:
- `scenario_id` (to filter all visuals by scenario)
- `pipeline_version` (optional, for versioning transparency)

### 6. Format and Polish

- Set color scheme: Use consistent blue (#3498db for primary, #2c3e50 for accents)
- Add title page with methodology summary
- Include footer with data source: "Generated from `warehouse_humanoid_tco` pipeline, 2026-05-21"

### 7. Save as .pbix

- **File > Save**
- Save the `.pbix` locally for your own use
- **Do not commit the `.pbix` to this repository** — per ADR-0008 the repo ships
  one dashboard surface (Tableau Public + the CSV exports), not a `.pbix`.

## Alternative: Use Power BI Template File

If you have Power BI template expertise, you can also:
1. Export this file as a `.pbit` (Power BI template)
2. Users can download, connect to their own data, and generate reports

For now, the `.pbix` approach is simpler and more concrete.

## Tableau Public Alternative

If Power BI is not available:
- CSV files are also exported to `exports/tableau_public/`
- Upload these directly to Tableau Public (free tier available)
- **Published workbook:** [Humanoid Robotics TCO on Tableau Public](https://public.tableau.com/app/profile/rafael.braga.kribitz/viz/HumanoidRoboticsTCO/Dashboard1)
- Share the public link in README.md

## Reproducibility Note

Every time the pipeline runs (`make all`), the CSV files are regenerated with the latest data. The .pbix file will need to be refreshed manually by:
1. Opening the .pbix in Power BI Desktop
2. **Home > Refresh** to reload from the CSV sources
3. Save and re-publish

For automated refreshes, configure a Power BI scheduled refresh on PowerBI.com (requires Pro license).
