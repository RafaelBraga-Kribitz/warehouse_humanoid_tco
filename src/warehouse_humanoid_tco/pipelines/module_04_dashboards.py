"""Module 4: Dashboard Generation

Produces stakeholder-facing artifacts:
1. Tableau Public dashboard data (CSV exports; the single published surface).
   The same CSVs import directly into Power BI Desktop — see ADR-0008, which
   deprecated a separate Power BI export path in favour of one CSV surface.
2. Executive summary charts (TCO, cost breakdown, capacity, sensitivity, cost/order).

See PROJECT_CHARTER.md §4 Module 4 and ADR-0008.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import polars as pl

from warehouse_humanoid_tco.analysis.crew_optimizer import generate_demand_frontier
from warehouse_humanoid_tco.utils.paths import repo_relative
from warehouse_humanoid_tco.visualization.chart_style import (
    ADVERSE,
    BASELINE,
    EURO_MILLIONS,
    OTHER,
    PLAIN_NUMBER,
    RECOMMENDED,
    apply_style,
)

SQL_DIR = Path(__file__).resolve().parents[3] / "analytics" / "sql"


def _duckdb_export(sql_path: Path, parquet_path: Path, csv_path: Path) -> None:
    """Apply a reviewed SQL projection to a Parquet input and write a Tableau CSV."""
    sql = sql_path.read_text().replace(
        "{{source}}", f"read_parquet('{parquet_path.resolve().as_posix()}')"
    )
    output = csv_path.resolve().as_posix().replace("'", "''")
    with duckdb.connect() as connection:
        connection.execute(f"COPY ({sql}) TO '{output}' (HEADER, DELIMITER ',')")


def export_for_tableau(processed_dir: Path, export_dir: Path) -> None:
    """Export reviewed DuckDB SQL projections as Tableau Public CSVs."""
    export_dir.mkdir(parents=True, exist_ok=True)

    projections = {
        "humanoid_capabilities_summary": "humanoid_capabilities_summary",
        "simulation_runs": "simulation_runs",
        "tco_scenarios": "tco_scenarios",
        "simulation_capacity_ceiling": "simulation_capacity_ceiling",
    }
    for artifact, sql_name in projections.items():
        _duckdb_export(
            SQL_DIR / f"{sql_name}.sql",
            processed_dir / f"{artifact}.parquet",
            export_dir / f"{artifact}.csv",
        )

    print(f"✓ Exported for Tableau: {export_dir}")


def generate_executive_charts(processed_dir: Path, charts_dir: Path) -> None:
    """Generate executive summary PNG charts for presentations."""
    charts_dir.mkdir(parents=True, exist_ok=True)
    sensitivity_path = charts_dir.parent / "sensitivity_analysis_report.json"
    sensitivity = (
        json.loads(sensitivity_path.read_text(encoding="utf-8"))
        if sensitivity_path.exists()
        else {}
    )
    mc_summary = sensitivity.get("mc_summary_per_scenario", {})
    source_note = f"Source: model outputs · {date.today().isoformat()}"
    tco = pl.read_parquet(processed_dir / "tco_scenarios.parquet")

    ranking = tco.with_columns((-pl.col("npv_eur") / 1_000_000).alias("total_cost_m_eur")).sort(
        "total_cost_m_eur"
    )
    scenarios = ranking["scenario_id"].to_list()
    costs = ranking["total_cost_m_eur"].to_list()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(
        scenarios,
        costs,
        color=[
            RECOMMENDED if s == "S-lean-human" else BASELINE if s == "S-baseline-human" else OTHER
            for s in scenarios
        ],
    )
    intervals = [
        (
            (
                max(0.0, cost - (-mc_summary[s]["npv_p95"] / 1_000_000)),
                max(0.0, (-mc_summary[s]["npv_p5"] / 1_000_000) - cost),
            )
            if s in mc_summary
            else (0.0, 0.0)
        )
        for s, cost in zip(scenarios, costs, strict=True)
    ]
    if any(low or high for low, high in intervals):
        ax.errorbar(
            costs,
            range(len(costs)),
            xerr=list(zip(*intervals, strict=True)),
            fmt="none",
            color=BASELINE,
            capsize=3,
            label="p5–p95 uncertainty interval",
        )
        ax.legend(loc="lower right", fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Positive 5-year total cost (€M, present value)")
    ax.set_title("Five-year total cost by scenario (lower is cheaper)")
    apply_style(ax)
    ax.grid(axis="x")
    for bar, value in zip(bars, costs, strict=True):
        ax.text(
            value, bar.get_y() + bar.get_height() / 2, f"  €{value:,.2f}M", va="center", fontsize=9
        )
    fig.text(0.01, 0.01, source_note, fontsize=7, color=BASELINE)
    plt.tight_layout()
    plt.savefig(charts_dir / "01_tco_npv_ranking.png", dpi=300, bbox_inches="tight")
    plt.close()

    scenarios_sorted = tco["scenario_id"].to_list()
    capex = tco["total_capex_eur"].to_list()
    opex = tco["total_opex_5yr_eur_pv"].to_list()
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(scenarios_sorted))
    capex_bars = ax.bar(x, capex, label="Capex (hardware, one-time)", color=OTHER)
    ax.bar(x, opex, bottom=capex, label="Operating cost (5-yr, present value)", color=RECOMMENDED)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios_sorted, rotation=45, ha="right")
    ax.set_ylabel("Cost (€)")
    ax.set_title("Five-year cost composition by scenario")
    ax.legend()
    apply_style(ax)
    ax.yaxis.set_major_formatter(EURO_MILLIONS)
    for bar, capex_value, opex_value in zip(capex_bars, capex, opex, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            capex_value + opex_value,
            f"€{(capex_value + opex_value) / 1_000_000:,.2f}M",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    fig.text(0.01, 0.01, source_note, fontsize=7, color=BASELINE)
    plt.tight_layout()
    plt.savefig(charts_dir / "02_cost_breakdown.png", dpi=300, bbox_inches="tight")
    plt.close()

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
        color=OTHER,
        label=f"Estimated sustainable capacity (ρ = {target_rho:.2f})",
    )
    ax.bar(
        [i + width / 2 for i in x],
        observed,
        width=width,
        yerr=observed_std,
        capsize=4,
        color=RECOMMENDED,
        label=f"Simulated capacity check ({n_validation_runs} runs, ±1 standard deviation)",
    )
    ax.axhline(
        960,
        color=BASELINE,
        linestyle="--",
        linewidth=1.2,
        label="Modeled demand: 960 orders per shift",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{s}\n(bottleneck: {b})" for s, b in zip(scenarios, bottlenecks, strict=True)],
        rotation=20,
        ha="right",
        fontsize=9,
    )
    ax.set_ylabel("Orders per 8-hour shift")
    ax.set_title("How much demand can each staffing mix sustain?")
    ax.legend(loc="upper left", fontsize=8)
    apply_style(ax)
    ax.yaxis.set_major_formatter(PLAIN_NUMBER)
    fig.text(
        0.5,
        0.005,
        "ρ (rho) is utilisation: workload divided by available service capacity. "
        "The capacity estimate uses λmax = ρ × c / max(cycle time). "
        "Baseline operation models 960 orders per 8-hour shift.",
        ha="center",
        fontsize=7,
        color=BASELINE,
        style="italic",
    )
    fig.text(0.01, 0.025, source_note, fontsize=7, color=BASELINE)
    plt.tight_layout(rect=(0, 0.04, 1, 1))
    plt.savefig(charts_dir / "03_simulation_throughput.png", dpi=300, bbox_inches="tight")
    plt.close()

    tco_cpo = tco.sort("cost_per_order_eur")
    scenarios_cpo = tco_cpo["scenario_id"].to_list()
    cpo = tco_cpo["cost_per_order_eur"].to_list()
    baseline_cpo = float(
        tco_cpo.filter(pl.col("scenario_id") == "S-baseline-human")["cost_per_order_eur"][0]
    )
    colors_cpo = [
        (
            RECOMMENDED
            if s == "S-lean-human"
            else (
                BASELINE
                if abs(v - baseline_cpo) / baseline_cpo <= 0.02
                else ADVERSE if v > baseline_cpo else OTHER
            )
        )
        for s, v in zip(scenarios_cpo, cpo, strict=True)
    ]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(scenarios_cpo, cpo, color=colors_cpo)
    ax.axvline(
        baseline_cpo,
        color=BASELINE,
        linestyle="--",
        linewidth=1.2,
        label=f"Baseline €{baseline_cpo:.3f}",
    )
    ax.set_xlabel("Cost per order (€; five-year horizon)")
    ax.set_title("Unit economics: cost per order by scenario")
    ax.legend(loc="lower right", fontsize=9)
    apply_style(ax)
    ax.grid(axis="x")
    for bar, value in zip(bars, cpo, strict=True):
        ax.text(
            value + 0.005,
            bar.get_y() + bar.get_height() / 2,
            f"€{value:.3f}",
            va="center",
            fontsize=9,
        )
    fig.text(0.01, 0.01, source_note, fontsize=7, color=BASELINE)
    plt.tight_layout()
    plt.savefig(charts_dir / "05_cost_per_order.png", dpi=300, bbox_inches="tight")
    plt.close()

    # F-221: separate the legacy eight-human staffing effect from the cost of
    # each technology mix. Positive values are savings relative to the legacy
    # baseline; a negative bar is a premium relative to optimized human sizing.
    baseline_cost = -float(tco.filter(pl.col("scenario_id") == "S-baseline-human")["npv_eur"][0])
    lean_rows = tco.filter(pl.col("scenario_id") == "S-lean-human")
    # Unit-test fixtures and legacy exports predate the fair comparator. In that
    # case, retain a neutral baseline reference rather than failing chart export.
    lean_cost = -float(lean_rows["npv_eur"][0]) if len(lean_rows) else baseline_cost
    robot_rows = tco.filter(
        pl.col("scenario_id").is_in(
            ["S-pure-humanoid", "S-hybrid-5050", "S-hybrid-amr", "S-future-2028"]
        )
    ).sort("scenario_id")
    effect_labels = ["Crew sizing\n(8→1 human)"] + robot_rows["scenario_id"].to_list()
    effect_values = [baseline_cost - lean_cost] + [
        lean_cost + float(npv) for npv in robot_rows["npv_eur"].to_list()
    ]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        effect_labels,
        [value / 1_000_000 for value in effect_values],
        color=[RECOMMENDED] + [ADVERSE if value < 0 else OTHER for value in effect_values[1:]],
    )
    ax.axhline(0, color=BASELINE, linewidth=1)
    ax.set_ylabel("Five-year cost effect (€M, present value)")
    ax.set_title("Effect decomposition: crew sizing versus technology mix")
    apply_style(ax)
    ax.yaxis.set_major_formatter(EURO_MILLIONS)
    for bar, value in zip(bars, effect_values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"€{value / 1_000_000:+.2f}M",
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=8,
        )
    fig.text(
        0.5,
        0.01,
        "First bar: savings from rightsizing the legacy human crew. Remaining bars: "
        "technology-mix cost relative to optimized human sizing; lower is better.",
        ha="center",
        fontsize=7,
        color=BASELINE,
    )
    fig.text(0.01, 0.03, source_note, fontsize=7, color=BASELINE)
    plt.tight_layout(rect=(0, 0.05, 1, 1))
    plt.savefig(charts_dir / "06_effect_decomposition.png", dpi=300, bbox_inches="tight")
    plt.close()

    plotted_values = {
        "01_tco_npv_ranking": {
            "scenario_id": ranking["scenario_id"].to_list(),
            "total_cost_m_eur": costs,
            "mc_summary": mc_summary,
        },
        "02_cost_breakdown": {
            "scenario_id": scenarios_sorted,
            "capex_eur": capex,
            "opex_pv_eur": opex,
        },
        "03_simulation_throughput": {
            "scenario_id": scenarios,
            "capacity_orders_per_shift": theoretical,
            "observed_throughput_mean": observed,
            "observed_throughput_std": observed_std,
            "demand_orders_per_shift": 960,
        },
        "05_cost_per_order": {
            "scenario_id": scenarios_cpo,
            "cost_per_order_eur": cpo,
            "baseline_eur": baseline_cpo,
        },
        "06_effect_decomposition": {
            "labels": effect_labels,
            "cost_effect_eur": effect_values,
        },
    }
    manifest = {
        "schema_version": 1,
        "hash_algorithm": "sha256",
        "charts": {
            name: hashlib.sha256(
                json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            for name, values in plotted_values.items()
        },
    }
    (charts_dir / "chart_data_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
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
    generate_demand_frontier(project_root)

    validation_report = {
        "module": "04_dashboards",
        "status": "complete",
        "tableau_exports": repo_relative(tableau_dir),
        "executive_charts": repo_relative(charts_dir),
        "next_steps": [
            "Upload tableau_public/ CSVs to Tableau Public",
            "Create dashboards in Tableau: TCO, Simulation, Capabilities",
            "Share public link in portfolio README",
            "Power BI users import the same CSVs directly (one surface, per ADR-0008)",
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
