"""Module 3: Total Cost of Ownership (TCO) Financial Model Pipeline

Orchestrates:
1. Load simulation runs from Module 2
2. Load TCO assumptions (capex, opex, labor costs)
3. Compute 5-year NPV, cost reduction vs baseline, and payback period for each scenario
4. Run sensitivity analysis on key drivers
5. Export tco_scenarios parquet

Entry point: main()
See PROJECT_CHARTER.md §4 Module 3 for spec.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import yaml

from warehouse_humanoid_tco.models.tco import (
    compute_annual_humanoid_opex,
    compute_annual_labor_cost,
    compute_humanoid_capex,
)

_BASELINE_ANNUAL_OPEX = 8 * (252 * 8) * 18.50 * 1.35  # 8 humans, full shift, KV Spedition & Lagereibetriebe


def compute_tco_scenario(
    scenario_id: str,
    simulation_data: dict,
    assumptions: dict,
    years: int = 5,
    discount_rate: float = 0.08,
    baseline_annual_opex: float = _BASELINE_ANNUAL_OPEX,
) -> dict:
    """Compute TCO metrics for a single scenario.

    Annual opex = human labor + humanoid (maintenance + energy) + AMR (maintenance + energy)
                  + supervision labor (fraction of human FTE per humanoid).
    Returns dict with npv_eur, cost_reduction_vs_baseline_pct, payback_years.
    IRR is omitted: this is a pure-cost model with no revenue, making IRR undefined.
    payback_years = capex / annual_opex_savings_vs_baseline (inf if no savings).
    """
    # Throughput passed in but not yet wired to cost drivers (fixed-cost model)
    _ = simulation_data.get("throughput_orders_per_shift", 0)

    # Human labor assumptions
    human_hourly_wage = assumptions.get("human_hourly_wage_eur", 18.50)
    human_overhead = assumptions.get("human_overhead_multiplier", 1.35)
    operating_days = assumptions.get("operating_days", 252)
    shift_hours = assumptions.get("shift_hours", 8.0)

    # Humanoid capex + opex assumptions
    humanoid_capex_unit = assumptions.get("humanoid_capex_eur", 120000)
    humanoid_install_cost = assumptions.get("humanoid_installation_cost_eur", 8000)
    humanoid_training_cost = assumptions.get("humanoid_training_cost_eur", 5000)
    humanoid_maint_fraction = assumptions.get("humanoid_annual_maintenance_fraction", 0.08)
    humanoid_energy_kwh = assumptions.get("humanoid_energy_kwh_per_shift", 8.0)
    humanoid_supervision_ratio = assumptions.get("humanoid_supervision_ratio", 0.10)

    # AMR capex + opex assumptions
    amr_capex_unit = assumptions.get("amr_capex_eur", 65000)
    amr_maint_fraction = assumptions.get("amr_annual_maintenance_fraction", 0.06)
    amr_energy_kwh = assumptions.get("amr_energy_kwh_per_shift", 4.0)

    energy_cost_eur_per_kwh = assumptions.get("energy_cost_eur_per_kwh", 0.22)

    # Scenario composition
    human_fraction = 0.0
    humanoid_fraction = 0.0
    amr_fraction = 0.0

    if "baseline-human" in scenario_id:
        human_fraction = 1.0
    elif "pure-humanoid" in scenario_id:
        humanoid_fraction = 1.0
    elif "hybrid-5050" in scenario_id:
        human_fraction = 0.5
        humanoid_fraction = 0.5
    elif "hybrid-amr" in scenario_id:
        human_fraction = 0.6
        humanoid_fraction = 0.2
        amr_fraction = 0.2
    elif "future-2028" in scenario_id:
        human_fraction = 0.5
        humanoid_fraction = 0.5

    total_agents = assumptions.get("total_agents", 8)
    n_humanoid = max(0, int(total_agents * humanoid_fraction))
    n_human = max(0, int(total_agents * human_fraction))
    n_amr = max(0, int(total_agents * amr_fraction))

    # Supervision: each humanoid consumes supervision_ratio of a human FTE
    supervision_ftes = humanoid_supervision_ratio * n_humanoid

    # Year-0 capex: humanoid (unit + install + training) + AMR units
    humanoid_capex_total = compute_humanoid_capex(
        n_humanoid, humanoid_capex_unit, humanoid_install_cost, humanoid_training_cost
    )
    amr_capex_total = n_amr * amr_capex_unit
    capex_year0 = humanoid_capex_total + amr_capex_total

    # Annual operating costs
    annual_labor_cost = compute_annual_labor_cost(
        n_human + supervision_ftes,  # type: ignore[arg-type]
        human_hourly_wage,
        human_overhead,
        operating_days,
        shift_hours,
    )
    annual_humanoid_opex = compute_annual_humanoid_opex(
        n_humanoid,
        humanoid_capex_unit,
        humanoid_maint_fraction,
        humanoid_energy_kwh,
        energy_cost_eur_per_kwh,
        operating_days,
    )
    annual_amr_opex = compute_annual_humanoid_opex(
        n_amr,
        amr_capex_unit,
        amr_maint_fraction,
        amr_energy_kwh,
        energy_cost_eur_per_kwh,
        operating_days,
    )
    annual_opex = annual_labor_cost + annual_humanoid_opex + annual_amr_opex

    # 5-year discounted NPV (cost model: all flows negative)
    cash_flows = [-capex_year0]
    for year in range(1, years + 1):
        cash_flows.append(-annual_opex / ((1 + discount_rate) ** year))

    npv = sum(cash_flows)

    # Cost reduction vs all-human baseline (positive = cheaper than baseline)
    cost_reduction_pct = (
        (baseline_annual_opex - annual_opex) / baseline_annual_opex * 100
        if baseline_annual_opex > 0
        else 0.0
    )

    # Payback: years until cumulative opex savings offset capex
    annual_savings = max(0.0, baseline_annual_opex - annual_opex)
    if capex_year0 <= 0:
        payback_years = 0.0  # no capex to recover
    elif annual_savings <= 0:
        payback_years = float("inf")  # opex savings never offset capex
    else:
        payback_years = round(capex_year0 / annual_savings, 1)

    return {
        "scenario_id": scenario_id,
        "npv_eur": float(npv),
        "cost_reduction_vs_baseline_pct": round(cost_reduction_pct, 1),
        "payback_years": payback_years if payback_years != float("inf") else None,
        "total_capex_eur": float(capex_year0),
        "total_opex_5yr_eur": float(annual_opex * years),
        "pipeline_version": "0.2.0",
    }


def module_03_main(
    project_root: Path,
    simulation_runs_path: Path | None = None,
    assumptions_path: Path | None = None,
) -> dict[str, Path | None]:
    """Run Module 3 end-to-end.

    Returns dict mapping tco_scenarios, sensitivity_analysis, validation_report.
    """
    # Load simulation runs
    if simulation_runs_path is None:
        simulation_runs_path = project_root / "data" / "processed" / "simulation_runs.parquet"

    # Load assumptions
    if assumptions_path is None:
        assumptions_path = project_root / "config" / "tco_assumptions.yaml"

    data_processed = project_root / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)

    print(f"[Setup] Loading simulation runs from {simulation_runs_path}...")

    if simulation_runs_path.exists():
        sim_df = pl.read_parquet(simulation_runs_path)
        print(f"  ✓ Loaded {len(sim_df)} simulation runs")
    else:
        print("  ⚠ Simulation runs not found. Creating empty TCO.")
        sim_df = pl.DataFrame()

    print(f"[Setup] Loading TCO assumptions from {assumptions_path}...")
    if assumptions_path.exists():
        with open(assumptions_path) as f:
            assumptions = yaml.safe_load(f)
        print("  ✓ Loaded assumptions")
    else:
        print("  ⚠ Assumptions file not found. Using defaults.")
        assumptions = {
            "humanoid_capex_eur": 120000,
            "human_hourly_wage_eur": 18.50,
            "human_overhead_multiplier": 1.35,
            "annual_hours_per_worker": 252 * 8,
            "total_agents": 8,
        }

    # ========== Compute TCO ==========
    print("\n[TCO] Computing financial metrics per scenario...")

    tco_results = []
    if len(sim_df) > 0:
        # NPV deterministic per scenario (agent composition only, not throughput)
        for scenario_id in sim_df.select(pl.col("scenario_id").unique()).to_series():
            scenario_data = sim_df.filter(pl.col("scenario_id") == scenario_id)

            # Use mean throughput to compute a single NPV per scenario
            col = scenario_data["throughput_orders_per_shift"]
            throughput_mean: float = col.mean() or 0.0  # type: ignore[assignment]
            throughput_std: float = col.std() or 0.0  # type: ignore[assignment]
            result = compute_tco_scenario(
                scenario_id,
                {"throughput_orders_per_shift": throughput_mean},
                assumptions,
            )
            result["n_simulation_runs"] = len(scenario_data)
            result["throughput_mean_orders_per_shift"] = throughput_mean
            result["throughput_std_orders_per_shift"] = throughput_std

            tco_results.append(result)
            print(
                f"  {scenario_id}: NPV = €{result['npv_eur']:.0f} "
                f"(throughput: {throughput_mean:.0f} ± {throughput_std:.0f} orders/shift)"
            )

    # ========== Export ==========
    print("\n[Export] Writing parquets...")

    if tco_results:
        # Sort by scenario_id for deterministic output (pl.unique() order is not guaranteed)
        tco_df = pl.DataFrame(tco_results).sort("scenario_id")
        tco_path = data_processed / "tco_scenarios.parquet"
        tco_df.write_parquet(tco_path)
        print(f"  ✓ {tco_path}")
    else:
        tco_df = pl.DataFrame()
        tco_path = None

    # ========== Validation Report ==========
    validation_report = {
        "phase": "module_03_tco",
        "scenarios_analyzed": len(tco_results),
        "discount_rate": 0.08,
        "tco_scenarios_path": str(tco_path) if tco_path else None,
    }

    report_path = project_root / "reports" / "module_03_tco_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2)

    print(f"\n✓ Module 3 complete. {len(tco_results)} scenarios analyzed.")
    print(f"  Report: {report_path}")

    return {
        "tco_scenarios": tco_path,
        "validation_report": report_path,
    }


if __name__ == "__main__":
    import sys

    project_root = Path(__file__).parent.parent.parent.parent

    try:
        paths = module_03_main(project_root)
        print(f"\n✓ Success. Outputs: {paths}")
    except Exception as e:
        print(f"\n✗ Failed: {e}", file=sys.stderr)
        sys.exit(1)
