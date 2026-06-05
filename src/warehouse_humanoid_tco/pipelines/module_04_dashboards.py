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
    capabilities_summary = pl.read_parquet(processed_dir / "humanoid_capabilities_summary.parquet")
    simulation_runs = pl.read_parquet(processed_dir / "simulation_runs.parquet")
    tco_scenarios = pl.read_parquet(processed_dir / "tco_scenarios.parquet")
    capacity_ceiling = pl.read_parquet(processed_dir / "simulation_capacity_ceiling.parquet")

    # Export as CSV for Tableau
    capabilities_summary.write_csv(export_dir / "humanoid_capabilities_summary.csv")
    simulation_runs.write_csv(export_dir / "simulation_runs.csv")
    tco_scenarios.write_csv(export_dir / "tco_scenarios.csv")
    capacity_ceiling.write_csv(export_dir / "simulation_capacity_ceiling.csv")

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
    # F-033: use the PV-discounted opex stream so the stacked bar is in the same
    # units as capex (both flows discounted to year 0). Pre-rename this column
    # was the undiscounted nominal total, which over-stated the opex bar by ~22%.
    opex = tco["total_opex_5yr_eur_pv"].to_list()
    x = range(len(scenarios_sorted))
    ax.bar(x, capex, label="Capex (Hardware)", color="#e74c3c")
    ax.bar(x, opex, bottom=capex, label="Opex 5yr PV (Labor)", color="#f39c12")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios_sorted, rotation=45, ha="right")
    ax.set_ylabel("Cost (€)")
    ax.set_title("Cost Composition by Scenario")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(charts_dir / "02_cost_breakdown.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Chart 3: Capacity Ceiling by Scenario (F-044)
    # Before F-044 this plotted mean throughput from simulation_runs.parquet, but
    # the baseline arrival rate (120/hr, Poisson) puts every scenario in a deeply
    # demand-bound regime (rho in [0.10, 0.34]); observed throughputs collapse to
    # Poisson(960) noise regardless of capacity. Now reads the F-044 capacity-
    # ceiling sweep which stresses each scenario to lambda_max(target_rho=0.85)
    # under the per-agent-type stability constraint — the resulting bars compare
    # scenario *capacity*, which is what the chart claimed to show all along.
    capacity = pl.read_parquet(processed_dir / "simulation_capacity_ceiling.parquet").sort(
        "capacity_orders_per_shift"
    )
    scenarios = capacity["scenario_id"].to_list()
    theoretical = capacity["capacity_orders_per_shift"].to_list()
    observed = capacity["observed_throughput_mean"].to_list()
    observed_std = capacity["observed_throughput_std"].to_list()
    bottlenecks = capacity["bottleneck_agent_type"].to_list()
    target_rho = float(capacity["target_rho"][0])
    n_validation_runs = int(capacity["n_runs_at_ceiling"][0])

    fig, ax = plt.subplots(figsize=(10, 6))
    x = list(range(len(scenarios)))
    width = 0.4
    ax.bar(
        [i - width / 2 for i in x],
        theoretical,
        width=width,
        color="#9b59b6",
        alpha=0.85,
        label=f"Closed-form ceiling (rho={target_rho:.2f})",
    )
    ax.bar(
        [i + width / 2 for i in x],
        observed,
        width=width,
        yerr=observed_std,
        capsize=4,
        color="#27ae60",
        alpha=0.85,
        label=f"Simulated mean at lambda_max ({n_validation_runs} runs, ±1 std)",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{s}\n(bottleneck: {b})" for s, b in zip(scenarios, bottlenecks, strict=True)],
        rotation=20,
        ha="right",
        fontsize=9,
    )
    ax.set_ylabel("Max Sustainable Orders per 8-hour Shift")
    ax.set_title("Warehouse Capacity Ceiling by Scenario")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.text(
        0.5,
        0.005,
        "Per-agent-type stability bound: lambda_max = rho * c / max(cycle_time_t). "
        "Baseline runs at 120 orders/hr are deeply demand-bound (rho < 0.35) and "
        "do not discriminate scenarios.",
        ha="center",
        fontsize=7,
        color="gray",
        style="italic",
    )
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    plt.savefig(charts_dir / "03_simulation_throughput.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Chart 5: Cost per Order by Scenario (F-046)
    # cost_per_order_eur = (capex + opex_pv) / (throughput × years × shifts_per_year)
    # Added to tco_scenarios.parquet by F-045.  Reference line at baseline cost
    # makes the S-hybrid-amr advantage visible without mental arithmetic.
    tco_cpo = tco.sort("cost_per_order_eur")
    scenarios_cpo = tco_cpo["scenario_id"].to_list()
    cpo = tco_cpo["cost_per_order_eur"].to_list()
    baseline_cpo = float(
        tco_cpo.filter(pl.col("scenario_id") == "S-baseline-human")["cost_per_order_eur"][0]
    )
    colors_cpo = ["#2ecc71" if v < baseline_cpo else "#e74c3c" for v in cpo]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(scenarios_cpo, cpo, color=colors_cpo)
    ax.axvline(
        baseline_cpo,
        color="#555555",
        linestyle="--",
        linewidth=1.2,
        label=f"Baseline €{baseline_cpo:.3f}",
    )
    ax.set_xlabel("Cost per Order (€, 5-year horizon)")
    ax.set_title("Unit Economics: Cost per Order by Scenario")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    for bar, v in zip(bars, cpo, strict=True):
        ax.text(v + 0.005, bar.get_y() + bar.get_height() / 2, f"€{v:.3f}", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(charts_dir / "05_cost_per_order.png", dpi=300, bbox_inches="tight")
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
        "tableau_exports": str(tableau_dir.relative_to(project_root)),
        "executive_charts": str(charts_dir.relative_to(project_root)),
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
    print("\n✓ Module 4 complete.")
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
