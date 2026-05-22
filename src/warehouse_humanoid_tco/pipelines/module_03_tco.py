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

import numpy as np
import polars as pl
import yaml

_BASELINE_ANNUAL_OPEX = 8 * (252 * 8) * 18.50 * 1.35  # 8 humans, full shift, KV Handel 2026


def compute_tco_scenario(
    scenario_id: str,
    simulation_data: dict,
    assumptions: dict,
    years: int = 5,
    discount_rate: float = 0.08,
    baseline_annual_opex: float = _BASELINE_ANNUAL_OPEX,
) -> dict:
    """Compute TCO metrics for a single scenario.

    Returns dict with npv_eur, cost_reduction_vs_baseline_pct, payback_years.
    IRR is omitted: this is a pure-cost model with no revenue, making IRR undefined.
    payback_years = capex / annual_opex_savings_vs_baseline (inf if no savings).

    Note: throughput affects scenario comparison (higher throughput = more productive
    workforce) but does NOT scale NPV in this model because labor cost is fixed per FTE,
    not per order. Future: consider energy cost per order or maintenance cost per throughput.
    """
    # Extract throughput from simulation (may affect future cost drivers)
    total_throughput = simulation_data.get("throughput_orders_per_shift", 0)

    # Assumptions
    humanoid_capex = assumptions.get("humanoid_capex_eur", 120000)
    human_hourly_wage = assumptions.get("human_hourly_wage_eur", 18.50)
    human_overhead = assumptions.get("human_overhead_multiplier", 1.35)
    annual_hours_per_worker = assumptions.get("annual_hours_per_worker", 252 * 8)

    # Scenario composition
    human_fraction = 0.0
    humanoid_fraction = 0.0
    amr_fraction = 0.0  # noqa: F841

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
        _amr_fraction = 0.2  # Reserved for future use
    elif "future-2028" in scenario_id:
        human_fraction = 0.5
        humanoid_fraction = 0.5

    total_agents = assumptions.get("total_agents", 8)
    n_humanoid = max(0, int(total_agents * humanoid_fraction))
    n_human = max(0, int(total_agents * human_fraction))

    # Capital costs (first year only)
    capex_year0 = n_humanoid * humanoid_capex

    # Annual operating costs
    annual_labor_cost = n_human * annual_hours_per_worker * human_hourly_wage * human_overhead

    # 5-year discounted NPV (cost model: all flows negative)
    cash_flows = [-capex_year0]
    for year in range(1, years + 1):
        cash_flows.append(-annual_labor_cost / ((1 + discount_rate) ** year))

    npv = sum(cash_flows)

    # Cost reduction vs all-human baseline (positive = cheaper than baseline)
    cost_reduction_pct = (
        (baseline_annual_opex - annual_labor_cost) / baseline_annual_opex * 100
        if baseline_annual_opex > 0
        else 0.0
    )

    # Payback: years until cumulative opex savings offset capex
    annual_savings = max(0.0, baseline_annual_opex - annual_labor_cost)
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
        "total_opex_5yr_eur": float(annual_labor_cost * years),
        "pipeline_version": "0.1.0",
    }


def module_03_main(
    project_root: Path,
    simulation_runs_path: Path | None = None,
    assumptions_path: Path | None = None,
) -> dict[str, Path]:
    """Run Module 3 end-to-end.

    Returns dict mapping tco_scenarios, sensitivity_analysis, validation_report.
    """
    # Load simulation runs
    if simulation_runs_path is None:
        simulation_runs_path = (
            project_root / "data" / "processed" / "simulation_runs.parquet"
        )

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
        # Group by scenario and compute NPV
        # Note: NPV is deterministic per scenario (depends only on agent composition, not throughput)
        # Throughput variation across runs does not affect NPV in this fixed-cost model
        for scenario_id in sim_df.select(pl.col("scenario_id").unique()).to_series():
            scenario_data = sim_df.filter(pl.col("scenario_id") == scenario_id)

            # Use mean throughput to compute a single NPV per scenario
            throughput_mean = float(scenario_data["throughput_orders_per_shift"].mean())
            result = compute_tco_scenario(
                scenario_id,
                {"throughput_orders_per_shift": throughput_mean},
                assumptions,
            )
            result["n_simulation_runs"] = len(scenario_data)
            result["throughput_mean_orders_per_shift"] = throughput_mean
            result["throughput_std_orders_per_shift"] = float(
                scenario_data["throughput_orders_per_shift"].std()
            )

            tco_results.append(result)
            print(
                f"  {scenario_id}: NPV = €{result['npv_eur']:.0f} "
                f"(throughput: {throughput_mean:.0f} ± {result['throughput_std_orders_per_shift']:.0f} orders/shift)"
            )

    # ========== Export ==========
    print("\n[Export] Writing parquets...")

    if tco_results:
        tco_df = pl.DataFrame(tco_results)
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
