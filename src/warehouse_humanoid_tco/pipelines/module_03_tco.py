"""Module 3: Total Cost of Ownership (TCO) Financial Model Pipeline

Orchestrates:
1. Load simulation runs from Module 2
2. Load TCO assumptions (capex, opex, labor costs) + architecture config
3. Compute 5-year NPV, cost reduction vs baseline, and payback period for each scenario
4. Compute break-even capex + cost-per-order
5. Export tco_scenarios parquet

Entry point: module_03_main()
See PROJECT_CHARTER.md §4 Module 3 for spec.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import yaml

from warehouse_humanoid_tco.models.simulation import compute_operational_availability
from warehouse_humanoid_tco.models.tco import (
    compute_annual_labor_cost,
    compute_humanoid_capex,
    compute_npv,
)
from warehouse_humanoid_tco.utils.paths import repo_relative


def build_financial_params(tco_assumptions: dict, sim_config: dict) -> dict:
    """Flatten the nested config files into the flat key space the cost model uses.

    Closes the wiring gap (audit Risk #1): ``compute_tco_scenario`` reads flat
    keys (``human_hourly_wage_eur`` etc.), but ``config/tco_assumptions.yaml`` is
    nested (``labor.base_hourly_wage_eur``). Before this function every
    ``assumptions.get(flat_key, default)`` missed and silently used the hardcoded
    default, so editing the config changed nothing. Here we map each flat key the
    model needs to its real location across both config files. Financial levers
    come from ``tco_assumptions.yaml``; operational levers (shift hours, energy
    per shift, supervision ratio, total agents) come from the architecture config.
    """
    labor = tco_assumptions.get("labor", {})
    humanoid = tco_assumptions.get("humanoid", {})
    amr = tco_assumptions.get("amr", {})
    financial = tco_assumptions.get("financial", {})
    ops = sim_config.get("operations", {})
    h_ops = sim_config.get("humanoid_operational", {})
    sim_agents = sim_config.get("agents", {})
    sim_humanoid = sim_agents.get("humanoid", {})
    sim_amr = sim_agents.get("amr", {})
    infrastructure = tco_assumptions.get("infrastructure", {})
    humanoid_availability = compute_operational_availability(
        float(h_ops.get("mtbf_hours", 40.0)),
        float(h_ops.get("mttr_hours", 0.5)),
        float(h_ops.get("battery_capacity_hours", 4.0)),
        float(h_ops.get("recharge_time_hours", 1.0)),
    )
    amr_ops = sim_config.get("amr_operational", {})
    amr_availability = 1.0
    if {"mtbf_hours", "mttr_hours", "battery_capacity_hours", "recharge_time_hours"} <= set(
        amr_ops
    ):
        amr_availability = compute_operational_availability(
            float(amr_ops["mtbf_hours"]),
            float(amr_ops["mttr_hours"]),
            float(amr_ops["battery_capacity_hours"]),
            float(amr_ops["recharge_time_hours"]),
        )
    return {
        "human_hourly_wage_eur": labor.get("base_hourly_wage_eur", 18.50),
        "human_overhead_multiplier": labor.get("overhead_multiplier", 1.35),
        "annual_wage_growth_rate": labor.get("annual_wage_growth_rate", 0.025),
        "operating_days": ops.get("operating_days_per_year", 252),
        "shift_hours": ops.get("shift_hours", 8.0),
        "humanoid_capex_eur": humanoid.get("unit_capex_eur", 120000),
        "humanoid_installation_cost_eur": humanoid.get("installation_cost_per_unit_eur", 8000),
        "humanoid_training_cost_eur": labor.get("training_cost_per_humanoid_eur", 5000),
        "humanoid_annual_maintenance_fraction": humanoid.get("annual_maintenance_fraction", 0.08),
        "humanoid_useful_life_years": humanoid.get("useful_life_years", 7),
        "humanoid_residual_value_fraction": humanoid.get("residual_value_fraction", 0.10),
        "humanoid_availability": humanoid_availability,
        "humanoid_energy_kwh_per_shift": sim_humanoid.get("energy_kwh_per_shift", 8.0),
        "humanoid_supervision_ratio": h_ops.get("supervision_ratio", 0.10),
        "amr_capex_eur": amr.get("unit_capex_eur", 65000),
        "amr_annual_maintenance_fraction": amr.get("annual_maintenance_fraction", 0.06),
        "amr_useful_life_years": amr.get("useful_life_years", 8),
        "amr_residual_value_fraction": amr.get("residual_value_fraction", 0.15),
        "amr_availability": amr_availability,
        "amr_energy_kwh_per_shift": sim_amr.get("energy_kwh_per_shift", 4.0),
        "energy_cost_eur_per_kwh": humanoid.get("energy_cost_eur_per_kwh", 0.22),
        "discount_rate": financial.get("discount_rate", 0.08),
        "horizon_years": financial.get("horizon_years", 5),
        "integration_cost_eur": infrastructure.get("integration_cost_eur", 200000),
    }


def _composition_from_config(scenario_config: dict, total_agents: int) -> dict:
    """Build an explicit-count composition dict from a config scenario entry.

    Reads the authoritative ``agent_counts`` block; falls back to rounded (not
    truncated) fractions only for legacy entries without explicit counts.
    """
    counts = scenario_config.get("agent_counts")
    if counts is None:
        counts = {
            "human": round(total_agents * scenario_config.get("human_fraction", 0.0)),
            "humanoid": round(total_agents * scenario_config.get("humanoid_fraction", 0.0)),
            "amr": round(total_agents * scenario_config.get("amr_fraction", 0.0)),
        }
    return {
        "n_human": float(counts.get("human", 0)),
        "n_humanoid": float(counts.get("humanoid", 0)),
        "n_amr": float(counts.get("amr", 0)),
        "throughput_multiplier": float(scenario_config.get("humanoid_throughput_multiplier", 1.0)),
    }


def compute_cost_per_order(
    capex_eur: float,
    opex_pv_eur: float,
    throughput_mean_orders_per_shift: float,
    years: int = 5,
    shifts_per_year: int = 252,
) -> float:
    """Cost per order: total discounted cost / total orders delivered.

    Returns € per order. Division by zero returns inf (infinite cost).
    """
    if throughput_mean_orders_per_shift <= 0 or years <= 0:
        return float("inf")
    total_orders = throughput_mean_orders_per_shift * shifts_per_year * years
    if total_orders <= 0:
        return float("inf")
    total_cost = capex_eur + opex_pv_eur
    return total_cost / total_orders


def compute_breakeven_thresholds(
    baseline_cost_per_order: float,
    pure_humanoid_result: dict,
    assumptions: dict,
    sim_df: pl.DataFrame,
    baseline_annual_opex: float,
    years: int = 5,
    discount_rate: float = 0.08,
    composition: dict | None = None,
    lean_cost_per_order: float | None = None,
    lean_annual_opex: float | None = None,
) -> dict:
    """Compute break-even capex for pure-humanoid vs baseline and vs lean-human.

    Binary search on capex to find the value at which pure-humanoid
    cost_per_order equals the comparator cost_per_order.
    """
    scenario_data = sim_df.filter(pl.col("scenario_id") == "S-pure-humanoid")
    if len(scenario_data) == 0:
        return {}

    throughput_mean_raw = scenario_data["throughput_orders_per_shift"].mean()
    if throughput_mean_raw is None or not isinstance(throughput_mean_raw, (int, float)):
        return {}
    throughput_mean: float = float(throughput_mean_raw)
    if throughput_mean <= 0:
        return {}

    original_capex = float(assumptions.get("humanoid_capex_eur", 120000))

    def _cost_per_order_at(capex_value: float, opex_baseline: float) -> float:
        modified_assumptions = assumptions.copy()
        modified_assumptions["humanoid_capex_eur"] = capex_value
        result = compute_tco_scenario(
            "S-pure-humanoid",
            {"throughput_orders_per_shift": throughput_mean},
            modified_assumptions,
            years=years,
            discount_rate=discount_rate,
            baseline_annual_opex=opex_baseline,
            composition=composition,
        )
        return result.get("cost_per_order_eur", float("inf"))

    def _search(target_cost_per_order: float, opex_baseline: float) -> float | None:
        capex_low = 10000.0
        capex_high = 500000.0
        tolerance = 100.0
        # cost_per_order is monotone increasing in capex, so a breakeven exists
        # in range only if the comparator cost is bracketed by the endpoint
        # costs. Without this guard the bisection silently converges to a
        # search bound and publishes it as if it were a real crossover (the
        # F-237 €10,030 "trigger" was exactly the €10K lower bound).
        if _cost_per_order_at(capex_low, opex_baseline) > target_cost_per_order:
            return None
        if _cost_per_order_at(capex_high, opex_baseline) < target_cost_per_order:
            return None
        for _ in range(50):
            capex_mid = (capex_low + capex_high) / 2
            cost_per_order_at_capex = _cost_per_order_at(capex_mid, opex_baseline)
            if abs(capex_high - capex_low) < tolerance:
                break
            if cost_per_order_at_capex > target_cost_per_order:
                capex_high = capex_mid
            else:
                capex_low = capex_mid
        return (capex_low + capex_high) / 2

    breakeven_vs_baseline = _search(baseline_cost_per_order, baseline_annual_opex)
    out: dict = {
        "capex_eur_per_unit": (
            round(breakeven_vs_baseline, 0) if breakeven_vs_baseline is not None else None
        ),
        "no_breakeven_in_search_range": breakeven_vs_baseline is None,
        "search_range_eur": [10000, 500000],
        "baseline_cost_per_order_eur": round(baseline_cost_per_order, 3),
        "pure_humanoid_current_cost_per_order_eur": round(
            pure_humanoid_result.get("cost_per_order_eur", 0.0), 3
        ),
        "current_capex_eur_per_unit": round(original_capex, 0),
        "methodology": (
            "Binary search on capex to find where pure-humanoid cost_per_order "
            "= baseline-human cost_per_order"
        ),
    }
    if lean_cost_per_order is not None and lean_cost_per_order > 0:
        lean_opex = lean_annual_opex if lean_annual_opex is not None else baseline_annual_opex
        breakeven_vs_lean = _search(lean_cost_per_order, lean_opex)
        out["vs_lean_human"] = {
            "capex_eur_per_unit": (
                round(breakeven_vs_lean, 0) if breakeven_vs_lean is not None else None
            ),
            "no_breakeven_in_search_range": breakeven_vs_lean is None,
            "search_range_eur": [10000, 500000],
            "lean_cost_per_order_eur": round(lean_cost_per_order, 3),
            "current_capex_eur_per_unit": round(original_capex, 0),
            "methodology": (
                "Binary search on capex to find where pure-humanoid cost_per_order "
                "= S-lean-human cost_per_order (F-237 decision trigger)"
            ),
        }
    return out


def compute_tco_scenario(
    scenario_id: str,
    simulation_data: dict,
    assumptions: dict,
    baseline_annual_opex: float,
    years: int = 5,
    discount_rate: float = 0.08,
    composition: dict | None = None,
) -> dict:
    """Compute TCO metrics for a single scenario.

    Annual opex = human labor + humanoid (maintenance + energy) + AMR (maintenance + energy)
                  + supervision labor (fraction of human FTE per humanoid).

    Composition: when ``composition`` is given (the pipeline path) the explicit
    integer crew counts are used directly. Otherwise the legacy scenario_id
    substring inference is used (synthetic/test path).

    NPV is computed from undiscounted cash flows via ``models.tco.compute_npv``
    (one canonical NPV implementation shared with the sensitivity analysis).

    Returns ``npv_eur``, the OPEX-only ``cost_reduction_vs_baseline_pct`` (the
    NPV-based total-cost reduction is added downstream in module_03_main where
    the baseline NPV is known), and ``payback_years``.

    payback_years = capex / annual_opex_savings_vs_baseline — a SIMPLE
    (undiscounted) payback by design; the NPV column is the discounted measure.
    IRR is omitted: a pure-cost model with no revenue has no meaningful IRR.
    """
    # Throughput is used only for the cost-per-order denominator below; it does
    # not drive NPV/opex (this is a composition-and-assumptions cost model).
    throughput_mean_in = simulation_data.get("throughput_orders_per_shift", 0.0)

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
    humanoid_availability = float(assumptions.get("humanoid_availability", 1.0))
    humanoid_useful_life = float(assumptions.get("humanoid_useful_life_years", 7))
    humanoid_residual_fraction = float(assumptions.get("humanoid_residual_value_fraction", 0.10))
    annual_wage_growth_rate = float(assumptions.get("annual_wage_growth_rate", 0.025))
    integration_cost = float(assumptions.get("integration_cost_eur", 200000))

    # AMR capex + opex assumptions
    amr_capex_unit = assumptions.get("amr_capex_eur", 65000)
    amr_maint_fraction = assumptions.get("amr_annual_maintenance_fraction", 0.06)
    amr_energy_kwh = assumptions.get("amr_energy_kwh_per_shift", 4.0)
    amr_availability = float(assumptions.get("amr_availability", 1.0))
    amr_useful_life = float(assumptions.get("amr_useful_life_years", 8))
    amr_residual_fraction = float(assumptions.get("amr_residual_value_fraction", 0.15))

    energy_cost_eur_per_kwh = assumptions.get("energy_cost_eur_per_kwh", 0.22)

    # ── Crew composition ──────────────────────────────────────────────────────
    if composition is not None:
        # Pipeline path: explicit integer counts (config agent_counts).
        n_human = float(composition.get("n_human", 0.0))
        n_humanoid_int = float(composition.get("n_humanoid", 0.0))
        n_amr = float(composition.get("n_amr", 0.0))
        humanoid_throughput_multiplier = float(composition.get("throughput_multiplier", 1.0))
    else:
        # Legacy substring inference (synthetic / test path). Retained so unit
        # Synthetic callers may use this path when no explicit composition exists.
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
        n_humanoid_int = float(max(0, int(total_agents * humanoid_fraction)))
        n_human = float(max(0, int(total_agents * human_fraction)))
        n_amr = float(max(0, int(total_agents * amr_fraction)))
        humanoid_throughput_multiplier = 1.0
        if "future-2028" in scenario_id:
            humanoid_throughput_multiplier = assumptions.get(
                "humanoid_throughput_multiplier_future_2028", 1.30
            )

    # F-034: a throughput multiplier (next-gen humanoids X% faster) means the
    # same throughput needs n_humanoid / multiplier effective units, reducing
    # capex/maintenance/energy/supervision. multiplier = 1.0 leaves counts as-is.
    if humanoid_availability <= 0 or amr_availability <= 0:
        raise ValueError("agent availability must be positive")
    if humanoid_throughput_multiplier > 0:
        n_humanoid: float = n_humanoid_int / humanoid_throughput_multiplier / humanoid_availability
    else:
        n_humanoid = 0.0
    # AMR operational availability is applied only when a complete operational
    # block supplies MTBF, MTTR, battery capacity, and recharge time.
    n_amr = n_amr / amr_availability

    # Supervision: each humanoid consumes supervision_ratio of a human FTE
    supervision_ftes = humanoid_supervision_ratio * n_humanoid

    # Year-0 capex (helpers are linear in count and accept fractional counts).
    humanoid_capex_total = compute_humanoid_capex(
        n_humanoid,  # type: ignore[arg-type]
        humanoid_capex_unit,
        humanoid_install_cost,
        humanoid_training_cost,
    )
    amr_capex_total = n_amr * amr_capex_unit
    integration_capex = integration_cost if n_humanoid_int > 0 else 0.0
    capex_year0 = humanoid_capex_total + amr_capex_total + integration_capex

    # Annual operating costs. Keep components separate so the report can
    # reconcile each discounted cost line directly to NPV.
    annual_human_labor_cost = compute_annual_labor_cost(
        n_human,  # type: ignore[arg-type]
        human_hourly_wage,
        human_overhead,
        operating_days,
        shift_hours,
    )
    annual_supervision_labor_cost = compute_annual_labor_cost(
        supervision_ftes,  # type: ignore[arg-type]
        human_hourly_wage,
        human_overhead,
        operating_days,
        shift_hours,
    )
    annual_humanoid_maintenance = n_humanoid * humanoid_capex_unit * humanoid_maint_fraction
    annual_humanoid_energy = (
        n_humanoid * humanoid_energy_kwh * energy_cost_eur_per_kwh * operating_days
    )
    annual_amr_maintenance = n_amr * amr_capex_unit * amr_maint_fraction
    annual_amr_energy = n_amr * amr_energy_kwh * energy_cost_eur_per_kwh * operating_days
    annual_non_labor_opex = (
        annual_humanoid_maintenance
        + annual_humanoid_energy
        + annual_amr_maintenance
        + annual_amr_energy
    )
    annual_opex_by_year = [
        (annual_human_labor_cost + annual_supervision_labor_cost)
        * (1 + annual_wage_growth_rate) ** year
        + annual_non_labor_opex
        for year in range(1, years + 1)
    ]
    annual_opex = annual_opex_by_year[0] if annual_opex_by_year else 0.0
    nominal_opex_total = sum(annual_opex_by_year)
    humanoid_salvage = (
        n_humanoid
        * humanoid_capex_unit
        * humanoid_residual_fraction
        * max(0.0, (humanoid_useful_life - years) / humanoid_useful_life)
    )
    amr_salvage = (
        n_amr
        * amr_capex_unit
        * amr_residual_fraction
        * max(0.0, (amr_useful_life - years) / amr_useful_life)
    )
    residual_salvage = humanoid_salvage + amr_salvage

    # 5-year NPV via the canonical compute_npv (undiscounted flows in; npf.npv
    # discounts year 0 by 1 and years 1..N by (1+r)^t). Same implementation the
    # sensitivity analysis uses (audit Risk #19 — one NPV function, not two).
    cash_flows = [-capex_year0] + [-opex for opex in annual_opex_by_year]
    if years > 0:
        cash_flows[-1] += residual_salvage
    npv = compute_npv(cash_flows, discount_rate)

    # PV of the opex stream (years 1..N), for the opex_pv column + cost_per_order.
    pv_opex_total = sum(
        opex / ((1 + discount_rate) ** year)
        for year, opex in enumerate(annual_opex_by_year, start=1)
    )
    pv_human_labor = sum(
        annual_human_labor_cost
        * (1 + annual_wage_growth_rate) ** year
        / ((1 + discount_rate) ** year)
        for year in range(1, years + 1)
    )
    pv_supervision_labor = sum(
        annual_supervision_labor_cost
        * (1 + annual_wage_growth_rate) ** year
        / ((1 + discount_rate) ** year)
        for year in range(1, years + 1)
    )
    opex_discount_factor = sum(1 / ((1 + discount_rate) ** year) for year in range(1, years + 1))
    cost_line_breakdown = [
        {"line": "humanoid_unit_capex", "npv_eur": -n_humanoid * humanoid_capex_unit},
        {
            "line": "humanoid_installation",
            "npv_eur": -n_humanoid * humanoid_install_cost,
        },
        {"line": "humanoid_training", "npv_eur": -n_humanoid * humanoid_training_cost},
        {"line": "amr_unit_capex", "npv_eur": -amr_capex_total},
        {"line": "system_integration", "npv_eur": -integration_capex},
        {"line": "human_labor", "npv_eur": -pv_human_labor},
        {
            "line": "humanoid_supervision_labor",
            "npv_eur": -pv_supervision_labor,
        },
        {
            "line": "humanoid_maintenance",
            "npv_eur": -annual_humanoid_maintenance * opex_discount_factor,
        },
        {
            "line": "humanoid_energy",
            "npv_eur": -annual_humanoid_energy * opex_discount_factor,
        },
        {"line": "amr_maintenance", "npv_eur": -annual_amr_maintenance * opex_discount_factor},
        {"line": "amr_energy", "npv_eur": -annual_amr_energy * opex_discount_factor},
        {"line": "residual_salvage", "npv_eur": residual_salvage / ((1 + discount_rate) ** years)},
    ]

    # Operating-cost reduction vs baseline (EXCLUDES capex — see the NPV-based
    # total_cost_reduction_vs_baseline_pct added in module_03_main, which is the
    # honest headline figure). Positive = lower operating cost than baseline.
    opex_reduction_pct = (
        (baseline_annual_opex - annual_opex) / baseline_annual_opex * 100
        if baseline_annual_opex > 0
        else 0.0
    )
    if scenario_id == "S-baseline-human":
        opex_reduction_pct = 0.0

    # Simple (undiscounted) payback of capex via annual opex savings.
    annual_savings = max(0.0, baseline_annual_opex - annual_opex)
    if scenario_id == "S-baseline-human":
        payback_years = None
    elif capex_year0 <= 0:
        payback_years = 0.0
    elif annual_savings <= 0:
        payback_years = float("inf")
    else:
        payback_years = round(capex_year0 / annual_savings, 1)

    # F-045: cost per order for break-even analysis
    cost_per_order = compute_cost_per_order(
        capex_year0,
        pv_opex_total - residual_salvage / ((1 + discount_rate) ** years),
        throughput_mean_in,
        years=years,
    )

    return {
        "scenario_id": scenario_id,
        "npv_eur": float(npv),
        # Retained name for backward compatibility; semantics = OPEX-only.
        "cost_reduction_vs_baseline_pct": round(opex_reduction_pct, 1),
        # Explicit alias documenting the opex-only basis.
        "opex_reduction_vs_baseline_pct": round(opex_reduction_pct, 1),
        "payback_years": payback_years if payback_years != float("inf") else None,
        "total_capex_eur": float(capex_year0),
        "total_opex_5yr_eur_nominal": float(nominal_opex_total),
        "total_opex_5yr_eur_pv": float(pv_opex_total),
        "residual_salvage_eur": float(residual_salvage),
        "cost_line_breakdown": cost_line_breakdown,
        "pipeline_version": "0.2.0",
        "cost_per_order_eur": cost_per_order,
    }


def module_03_main(
    project_root: Path,
    simulation_runs_path: Path | None = None,
    assumptions_path: Path | None = None,
    sim_config_path: Path | None = None,
) -> dict[str, Path | None]:
    """Run Module 3 end-to-end.

    Returns dict mapping tco_scenarios, validation_report.
    """
    if simulation_runs_path is None:
        simulation_runs_path = project_root / "data" / "processed" / "simulation_runs.parquet"
    if assumptions_path is None:
        assumptions_path = project_root / "config" / "tco_assumptions.yaml"
    if sim_config_path is None:
        sim_config_path = project_root / "config" / "autostore_baseline.yaml"

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
            tco_assumptions = yaml.safe_load(f)
        print("  ✓ Loaded assumptions")
    else:
        print("  ⚠ Assumptions file not found. Using defaults.")
        tco_assumptions = {}

    if sim_config_path.exists():
        with open(sim_config_path) as f:
            sim_config = yaml.safe_load(f)
    else:
        sim_config = {}

    # Wire the nested config into the flat key space the model consumes (Risk #1)
    params = build_financial_params(tco_assumptions, sim_config)
    discount_rate = float(params.get("discount_rate", 0.08))
    years = int(params.get("horizon_years", 5))

    total_agents = sim_config.get("total_agents", 8)
    compositions = {
        s["id"]: _composition_from_config(s, total_agents)
        for s in sim_config.get("scenarios", [])
        if "id" in s
    }

    print("\n[TCO] Computing financial metrics per scenario...")

    tco_results = []
    baseline_annual_opex: float | None = None
    baseline_npv: float | None = None

    if len(sim_df) > 0:
        # Compute the baseline first so cost-reduction/payback are measured
        # against the live configuration rather than a frozen fallback.
        baseline_id = "S-baseline-human"
        b_data = sim_df.filter(pl.col("scenario_id") == baseline_id)
        b_throughput: float = (
            b_data["throughput_orders_per_shift"].mean() if len(b_data) else 0.0
        ) or 0.0
        baseline_composition = compositions.get(
            baseline_id,
            {
                "n_human": float(sim_config.get("total_agents", 8)),
                "n_humanoid": 0.0,
                "n_amr": 0.0,
                "throughput_multiplier": 1.0,
            },
        )
        b_result = compute_tco_scenario(
            baseline_id,
            {"throughput_orders_per_shift": b_throughput},
            params,
            baseline_annual_opex=0.0,
            years=years,
            discount_rate=discount_rate,
            composition=baseline_composition,
        )
        baseline_annual_opex = b_result["total_opex_5yr_eur_nominal"] / years
        baseline_npv = b_result["npv_eur"]

        for scenario_id in sorted(sim_df.select(pl.col("scenario_id").unique()).to_series()):
            scenario_data = sim_df.filter(pl.col("scenario_id") == scenario_id)
            col = scenario_data["throughput_orders_per_shift"]
            throughput_mean: float = col.mean() or 0.0  # type: ignore[assignment]
            throughput_std: float = col.std() or 0.0  # type: ignore[assignment]
            result = compute_tco_scenario(
                scenario_id,
                {"throughput_orders_per_shift": throughput_mean},
                params,
                baseline_annual_opex=baseline_annual_opex,
                years=years,
                discount_rate=discount_rate,
                composition=compositions.get(scenario_id),
            )
            result["n_simulation_runs"] = len(scenario_data)
            result["throughput_mean_orders_per_shift"] = throughput_mean
            result["throughput_std_orders_per_shift"] = throughput_std
            tco_results.append(result)
            print(
                f"  {scenario_id}: NPV = €{result['npv_eur']:.0f} "
                f"(throughput: {throughput_mean:.0f} ± {throughput_std:.0f} orders/shift)"
            )

    # NPV-based total-cost reduction vs baseline (Risk #4): the honest headline
    # figure that accounts for capex, unlike the opex-only cost_reduction column.
    if baseline_npv is not None and baseline_npv != 0:
        for r in tco_results:
            r["total_cost_reduction_vs_baseline_pct"] = round(
                (baseline_npv - r["npv_eur"]) / baseline_npv * 100, 1
            )
    else:
        for r in tco_results:
            r["total_cost_reduction_vs_baseline_pct"] = 0.0

    print("\n[Export] Writing parquets...")
    if tco_results:
        tco_df = pl.DataFrame(tco_results).sort("scenario_id")
        tco_path = data_processed / "tco_scenarios.parquet"
        tco_df.write_parquet(tco_path)
        print(f"  ✓ {tco_path}")
    else:
        tco_df = pl.DataFrame()
        tco_path = None

    validation_report = {
        "phase": "module_03_tco",
        "scenarios_analyzed": len(tco_results),
        "discount_rate": discount_rate,
        "tco_scenarios_path": repo_relative(tco_path) if tco_path else None,
        "scenario_results": tco_results,
        "cost_line_breakdown": {
            result["scenario_id"]: result["cost_line_breakdown"] for result in tco_results
        },
    }

    # F-045: break-even thresholds
    if tco_results and len(sim_df) > 0:
        baseline_result = next(
            (r for r in tco_results if "baseline-human" in r["scenario_id"]), None
        )
        pure_humanoid_result = next(
            (r for r in tco_results if "pure-humanoid" in r["scenario_id"]), None
        )
        if baseline_result and pure_humanoid_result:
            baseline_cost_per_order = baseline_result.get("cost_per_order_eur", 0.0)
            lean_result = next(
                (r for r in tco_results if r["scenario_id"] == "S-lean-human"), None
            )
            if baseline_cost_per_order > 0:
                lean_cpo = lean_result.get("cost_per_order_eur") if lean_result else None
                # Approximate lean annual opex from nominal 5yr / years for payback helper.
                lean_opex = None
                if lean_result and years > 0:
                    lean_opex = float(lean_result.get("total_opex_5yr_eur_nominal", 0.0)) / years
                breakeven_data = compute_breakeven_thresholds(
                    baseline_cost_per_order,
                    pure_humanoid_result,
                    params,
                    sim_df,
                    baseline_annual_opex=baseline_annual_opex,
                    years=years,
                    discount_rate=discount_rate,
                    composition=compositions.get("S-pure-humanoid"),
                    lean_cost_per_order=lean_cpo,
                    lean_annual_opex=lean_opex,
                )
                if breakeven_data:
                    validation_report["breakeven_thresholds"] = breakeven_data

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
