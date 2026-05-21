"""Module 4: Dashboard Generation

Produces interactive visualizations for stakeholders:
1. Tableau Public dashboard (shareable link)
2. Power BI .pbix export (recruiters)
3. Executive summary charts (TCO, simulation, capability)

See PROJECT_CHARTER.md §4 Module 4.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


def export_for_tableau(processed_dir: Path, export_dir: Path) -> None:
    """Export all module outputs as CSV + metadata for Tableau Public."""
    export_dir.mkdir(parents=True, exist_ok=True)

    # Load all outputs
    capabilities_summary = pl.read_parquet(
        processed_dir / "humanoid_capabilities_summary.parquet"
    )
    simulation_runs = pl.read_parquet(processed_dir / "simulation_runs.parquet")
    tco_scenarios = pl.read_parquet(processed_dir / "tco_scenarios.parquet")

    # Export as CSV for Tableau
    capabilities_summary.write_csv(export_dir / "humanoid_capabilities_summary.csv")
    simulation_runs.write_csv(export_dir / "simulation_runs.csv")
    tco_scenarios.write_csv(export_dir / "tco_scenarios.csv")

    print(f"✓ Exported for Tableau: {export_dir}")


def generate_executive_charts(processed_dir: Path, charts_dir: Path) -> None:
    """Generate executive summary PNG charts for presentations."""
    charts_dir.mkdir(parents=True, exist_ok=True)

    tco = pl.read_parquet(processed_dir / "tco_scenarios.parquet").sort("npv_eur")

    # Chart 1: TCO NPV Ranking
    fig, ax = plt.subplots(figsize=(10, 6))
    scenarios = tco["scenario_id"].to_list()
    npv = tco["npv_eur"].to_list()
    colors = ["#2ecc71" if npv[i] == min(npv) else "#3498db" for i in range(len(npv))]
    ax.barh(scenarios, npv, color=colors)
    ax.set_xlabel("NPV (€)")
    ax.set_title("5-Year Total Cost of Ownership by Scenario")
    ax.grid(axis="x", alpha=0.3)
    for i, v in enumerate(npv):
        ax.text(v, i, f"  €{v:,.0f}", va="center")
    plt.tight_layout()
    plt.savefig(charts_dir / "01_tco_npv_ranking.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Chart 2: Capex vs Opex Breakdown
    fig, ax = plt.subplots(figsize=(10, 6))
    scenarios_sorted = tco["scenario_id"].to_list()
    capex = tco["total_capex_eur"].to_list()
    opex = tco["total_opex_5yr_eur"].to_list()
    x = range(len(scenarios_sorted))
    ax.bar(x, capex, label="Capex (Hardware)", color="#e74c3c")
    ax.bar(x, opex, bottom=capex, label="Opex 5yr (Labor)", color="#f39c12")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios_sorted, rotation=45, ha="right")
    ax.set_ylabel("Cost (€)")
    ax.set_title("Cost Composition by Scenario")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(charts_dir / "02_cost_breakdown.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Chart 3: Simulation Throughput by Scenario
    sim = pl.read_parquet(processed_dir / "simulation_runs.parquet")
    sim_summary = sim.group_by("scenario_id").agg(
        pl.col("throughput_orders_per_shift").mean().alias("mean_throughput"),
        pl.col("throughput_orders_per_shift").std().alias("std_throughput"),
    ).sort("mean_throughput")

    fig, ax = plt.subplots(figsize=(10, 6))
    scenarios = sim_summary["scenario_id"].to_list()
    means = sim_summary["mean_throughput"].to_list()
    # Replace None std (single-run scenarios) with 0.0 to avoid matplotlib error
    stds = [s if s is not None else 0.0 for s in sim_summary["std_throughput"].to_list()]
    x = range(len(scenarios))
    ax.bar(x, means, yerr=stds if any(s > 0 for s in stds) else None, capsize=5, color="#9b59b6", alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=45, ha="right")
    ax.set_ylabel("Orders per 8-hour Shift")
    ax.set_title("Warehouse Throughput by Scenario (3 runs, ±1 std)")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(charts_dir / "03_simulation_throughput.png", dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✓ Generated executive charts: {charts_dir}")


def module_04_main(
    project_root: Path,
) -> dict[str, Path]:
    """Run Module 4 end-to-end.

    Returns dict mapping {'tableau_exports': ..., 'charts': ...}
    """
    processed_dir = project_root / "data" / "processed"
    tableau_dir = project_root / "exports" / "tableau_public"
    charts_dir = project_root / "reports" / "executive_charts"

    print("[Export] Preparing data for Tableau Public...")
    export_for_tableau(processed_dir, tableau_dir)

    print("[Charts] Generating executive summary visualizations...")
    generate_executive_charts(processed_dir, charts_dir)

    validation_report = {
        "module": "04_dashboards",
        "status": "complete",
        "tableau_exports": str(tableau_dir),
        "executive_charts": str(charts_dir),
        "next_steps": [
            "Upload tableau_public/ CSVs to Tableau Public",
            "Create dashboards in Tableau: TCO, Simulation, Capabilities",
            "Share public link in portfolio README",
            "Create Power BI .pbix from module outputs for Austrian recruiters",
        ],
    }

    report_path = project_root / "reports" / "module_04_dashboard_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2)

    print(f"[Validation] Report: {report_path}")
    print(f"\n✓ Module 4 complete.")
    print(f"  Tableau exports: {tableau_dir}")
    print(f"  Executive charts: {charts_dir}")

    return {
        "tableau_exports": tableau_dir,
        "executive_charts": charts_dir,
        "validation_report": report_path,
    }


if __name__ == "__main__":
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    module_04_main(project_root)
