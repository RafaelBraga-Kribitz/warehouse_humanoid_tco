# Tableau Public Dashboard Setup Guide

This guide walks through creating three interconnected dashboards for the humanoid robot TCO analysis on Tableau Public (free tier).

## Overview

**Data Source:** CSV files in `exports/tableau_public/`:
- `tco_scenarios.csv` — 5 scenarios, NPV results
- `simulation_runs.csv` — 75 simulation runs (15 per scenario)
- `humanoid_capabilities_summary.csv` — Task-level humanoid capabilities

**Target Dashboards:**
1. **Dashboard 1: TCO Summary** — NPV ranking, cost breakdown, payback periods
2. **Dashboard 2: Simulation Validation** — Throughput distribution, queue length, utilization
3. **Dashboard 3: Capabilities Explorer** — Task cycle times, reach, success rates

## Setup Instructions

### Step 1: Create Tableau Public Account

1. Go to https://public.tableau.com
2. Sign up with email (free account)
3. Note: Tableau Public is fully free but requires publishing dashboards publicly

### Step 2: Create a New Workbook

1. Click **Create** > **Workbook**
2. Or upload from Desktop (if using Tableau Desktop trial)

### Step 3: Connect to Data

**Option A: Upload CSVs directly (Recommended for Tableau Public Free)**

1. **Data** > **New Data Source** > **Text File**
2. Navigate to `exports/tableau_public/tco_scenarios.csv`
3. Click **Open**
4. Tableau will auto-detect columns and types
5. Verify:
   - `scenario_id` = String
   - `npv_eur`, `total_capex_eur`, `total_opex_5yr_eur_nominal`, `total_opex_5yr_eur_pv` = Number
   - `payback_years` = Number (null handling automatic)
6. Click **Create Sheet**

**Repeat for:** `simulation_runs.csv` and `humanoid_capabilities_summary.csv`

**Option B: Use Tableau Desktop (if available) + Publish to Public**

1. Open Tableau Desktop
2. Connect to each CSV as above
3. Create dashboards locally
4. **File** > **Publish to Tableau Public**
5. Sign in with Public account
6. Dashboards are now live and sharable

### Step 4: Build Dashboard 1 — TCO Summary

**Sheet 1a: NPV Ranking**
- Dimensions: `scenario_id`
- Measures: `npv_eur` (sum)
- Visualization: Horizontal Bar Chart
- Sort: By NPV ascending (worst to best)
- Highlight best scenario (S-hybrid-amr) in green
- Add annotations: "Winner: 43% cost reduction"

**Sheet 1b: Cost Composition**
- Dimensions: `scenario_id`
- Measures: `total_capex_eur`, `total_opex_5yr_eur_pv` (use the PV form so it stacks apples-to-apples with capex; `total_opex_5yr_eur_nominal` is for raw-cash-out reporting)
- Visualization: Stacked Horizontal Bar
- Color: Red for capex, orange for opex
- Interactive: Filter by scenario

**Sheet 1c: Payback Analysis**
- Dimensions: `scenario_id`
- Measures: `payback_years`
- Visualization: Text Table with conditional formatting
- Color code: Green < 2 years, yellow 2-3 years, red > 3 years (or null/infinite)
- Include cost_reduction_vs_baseline_pct column

**Dashboard 1 Assembly**
- Create new **Dashboard**
- Drag sheets 1a, 1b, 1c into layout
- Add title: "5-Year TCO by Scenario"
- Add filter object for `scenario_id` (optional, for detail views)
- Arrange visuals: 1a (top), 1b + 1c (bottom side-by-side)

### Step 5: Build Dashboard 2 — Simulation Validation

**Sheet 2a: Throughput Distribution**
- Data source: `simulation_runs.csv`
- Dimensions: `scenario_id`
- Measures: `throughput_orders_per_shift` (average + std dev if available)
- Visualization: Bar Chart with error bars
- Benchmark line: Add reference line at 960 (Knapp baseline)
- Title: "Warehouse Throughput by Scenario (3 runs, ±1 std)"

**Sheet 2b: Queue Dynamics**
- Dimensions: `scenario_id`
- Measures: `queue_length_mean` (average across 15 runs)
- Visualization: Line Chart or Bar
- Annotation: "All scenarios ~0.5 mean queue (statistically indistinguishable)"

**Sheet 2c: Run Count Validation**
- Dimensions: `scenario_id`
- Measures: Count of `run_id`
- Visualization: Text Table or Indicator
- Expected: 15 runs per scenario (shows reproducibility)

**Dashboard 2 Assembly**
- Create new **Dashboard**: "Simulation Validation"
- Add sheets 2a (top), 2b + 2c (bottom)
- Add note: "Kruskal-Wallis p=1.0: scenarios statistically indistinguishable by throughput. Cost differentiation is from assumptions, not simulation variance."

### Step 6: Build Dashboard 3 — Capabilities Explorer

**Sheet 3a: Task Capability Table**
- Data source: `humanoid_capabilities_summary.csv`
- Dimensions: `task_category`
- Measures: `cycle_time_mean`, `cycle_time_std`, `n_episodes`
- Visualization: Interactive Table
- Sorting: By `cycle_time_mean` ascending
- Interactivity: Click to drill down (if detailed data available)

**Dashboard 3 Assembly**
- Single sheet dashboard
- Add title: "Humanoid Capabilities by Task Category"
- Add description: "Summary of 2,359 real episodes from Unitree UnifoLM datasets"
- Include column explanations as tooltips

### Step 7: Create Navigation & Branding

**Navigation Page (Optional)**
- Create a new sheet with Tableau Text Object
- Add links to the 3 dashboards (Tableau allows action filters to jump between dashboards)
- Add project overview text
- Link to GitHub repo: https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco

**Color Scheme**
- Primary: #3498db (Tableau Blue)
- Success: #27ae60 (Green, for best scenario)
- Caution: #f39c12 (Orange)
- Neutral: #2c3e50 (Dark Blue)

### Step 8: Publish to Tableau Public

1. **File** > **Save As**
2. Name: `warehouse_humanoid_tco`
3. Click **Publish**
4. Sign in with Tableau Public account
5. Confirm public sharing
6. Copy the public URL: `https://public.tableau.com/app/profile/[username]/viz/...`

### Step 9: Link Dashboard in README

Update `README.md` section "### Dashboards":

```markdown
### Dashboards

- **[TCO Summary Dashboard](https://public.tableau.com/...)** — Interactive NPV ranking and cost composition
- **[Simulation Validation](https://public.tableau.com/...)** — Throughput and queue analysis
- **[Capabilities Explorer](https://public.tableau.com/...)** — Task-level humanoid performance
- **[Direct Data Download](./exports/tableau_public/)** — Raw CSVs for use in your own BI tools
```

## Maintenance & Updates

Every time the pipeline runs (`make all`), the CSV files are regenerated. To update the Tableau Public dashboards:

1. Download fresh CSVs from `exports/tableau_public/`
2. In Tableau Public, open the workbook
3. **Data** > **Refresh** (if using live connection)
4. Or re-upload CSVs (if using uploaded source)
5. Republish

For automated refreshes: Tableau Public does not natively support scheduled data refresh. For production use, consider:
- Tableau Server (enterprise, paid)
- Power BI (alternative BI tool with scheduled refresh)
- Manually trigger refreshes weekly via GitHub Actions hook

## Troubleshooting

**Issue: "Unable to connect to data source"**
- Tableau Public cannot connect to local files. Always upload CSVs through the UI.
- Solution: Use the "Upload File" button in Tableau Public.

**Issue: "Null values appear as 0"**
- Tableau treats nulls differently by default.
- Solution: In **Data > Field** properties, set Null handling to "Show as empty".

**Issue: "Formatting lost after republish"**
- Tableau Public may reset some custom formatting.
- Solution: Use Tableau's built-in formatting (not CSS/HTML).

## Sharing & Engagement

Once published:
1. Share public URL in README
2. Post on LinkedIn (include dashboard URL + German executive summary PDF)
3. Tag @KnappAG, @TGW Logistics with dashboard link
4. Track views and interactions (Tableau Public shows analytics)

## Alternative: Google Data Studio

If Tableau Public is restrictive, Google Data Studio (Google's BI tool) offers:
- Free tier with 5 users
- Direct Google Sheets connector (simpler workflow)
- Embedded dashboards on websites

Process:
1. Upload CSVs to Google Sheets
2. Create Data Studio report
3. Link to sheets
4. Publish and share URL

This guide covers Tableau Public as the primary option per PROJECT_CHARTER.md, but Data Studio is a viable fallback.
