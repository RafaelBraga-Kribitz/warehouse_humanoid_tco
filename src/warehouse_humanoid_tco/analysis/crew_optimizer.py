"""Deterministic integer crew optimizer constrained by predicted utilisation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from itertools import product
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import yaml

from warehouse_humanoid_tco.models.simulation import (
    AgentProfile,
    WarehouseScenario,
    predict_utilisation,
    scale_line_cycle_to_order,
)
from warehouse_humanoid_tco.pipelines.module_03_tco import (
    build_financial_params,
    compute_tco_scenario,
)

_AGENT_TYPES = ("human", "humanoid", "amr")
_MAX_CREW_PER_TYPE = 12
_HUMANOID_DEFAULT_CYCLE_MEAN_SECONDS = 30.0
_HUMANOID_DEFAULT_CYCLE_STD_SECONDS = 10.0


def _normalise_policy(policy: Iterable[str]) -> frozenset[str]:
    """Validate and normalize the allowed agent-type policy."""
    allowed = frozenset(policy)
    unknown = allowed.difference(_AGENT_TYPES)
    if unknown:
        raise ValueError(f"Unsupported agent types in policy: {sorted(unknown)}")
    if not allowed:
        raise ValueError("policy must allow at least one agent type")
    # ADR-0017 / F-237: AutoStore ports need fine-motor pick — pure AMR is invalid.
    if allowed == frozenset({"amr"}):
        raise ValueError(
            "pure-AMR policy is excluded: AutoStore ports require fine-motor pick " "(see ADR-0017)"
        )
    return allowed


def module_02_humanoid_cycle_overrides(
    sim_config: dict[str, Any],
    project_root: Path,
) -> dict[str, tuple[float, float]]:
    """Return per-order humanoid cycle times matching Module 2 (F-237).

    Loads the empirical demo mean/std, applies transfer + availability, then
    scales by ``operations.pick_lines_per_order``. Used by fair sizing and the
    demand frontier so optimizer service times match simulation.
    """
    import polars as pl

    from warehouse_humanoid_tco.models.simulation import compute_operational_availability

    summary_path = project_root / "data" / "processed" / "humanoid_capabilities_summary.parquet"
    if not summary_path.exists():
        return {}
    summary = pl.read_parquet(summary_path)
    reference_task = (
        sim_config.get("agents", {}).get("humanoid", {}).get("reference_task", "pick_medium_object")
    )
    match = summary.filter(pl.col("task_category") == reference_task)
    if match.height == 0:
        raise ValueError(f"reference_task {reference_task!r} missing from capability summary")
    row = match.row(0, named=True)
    ops = sim_config.get("humanoid_operational", {})
    availability = compute_operational_availability(
        float(ops.get("mtbf_hours", 40.0)),
        float(ops.get("mttr_hours", 0.5)),
        float(ops.get("battery_capacity_hours", 4.0)),
        float(ops.get("recharge_time_hours", 1.0)),
    )
    transfer_factor = (
        sim_config.get("capability_transfer", {})
        .get("wbt_to_production_factor", {})
        .get("point_estimate", 0.70)
    )
    if float(transfer_factor) <= 0:
        raise ValueError(f"wbt_to_production_factor must be > 0; got {transfer_factor}")
    pick_lines = float(sim_config.get("operations", {}).get("pick_lines_per_order", 1.0))
    line_mean = float(row["cycle_time_mean"]) / float(transfer_factor) / availability
    line_std = float(row["cycle_time_std"]) / float(transfer_factor) / availability
    return {"humanoid": scale_line_cycle_to_order(line_mean, line_std, pick_lines)}


def _agent_cycle_times(sim_config: dict[str, Any]) -> dict[str, tuple[float, float]]:
    """Extract per-order cycle times (line times × pick_lines_per_order, F-237)."""
    agents = sim_config.get("agents", {})
    pick_lines = float(sim_config.get("operations", {}).get("pick_lines_per_order", 1.0))
    cycle_times: dict[str, tuple[float, float]] = {}
    for agent_type in _AGENT_TYPES:
        config = agents.get(agent_type, {})
        mean = config.get("cycle_time_mean_seconds")
        std = config.get("cycle_time_std_seconds")
        if agent_type == "humanoid" and (mean is None or std is None):
            transfer_factor = (
                sim_config.get("capability_transfer", {})
                .get("wbt_to_production_factor", {})
                .get("point_estimate", 0.70)
            )
            if transfer_factor <= 0:
                raise ValueError(
                    "capability_transfer.wbt_to_production_factor.point_estimate "
                    f"must be positive; got {transfer_factor}"
                )
            line_mean = _HUMANOID_DEFAULT_CYCLE_MEAN_SECONDS / float(transfer_factor)
            line_std = _HUMANOID_DEFAULT_CYCLE_STD_SECONDS / float(transfer_factor)
            cycle_times[agent_type] = scale_line_cycle_to_order(line_mean, line_std, pick_lines)
        elif mean is None or std is None:
            raise ValueError(f"Missing cycle time for agent type {agent_type!r}")
        else:
            cycle_times[agent_type] = scale_line_cycle_to_order(float(mean), float(std), pick_lines)
    return cycle_times


# Policies that may appear in fair-scenario redesign and demand frontiers.
# Pure AMR is excluded: AutoStore ports need fine-motor pick (ADR-0017).
ALLOWED_FRONTIER_POLICIES: tuple[frozenset[str], ...] = (
    frozenset({"human"}),
    frozenset({"human", "amr"}),
    frozenset({"humanoid"}),
    frozenset({"human", "humanoid"}),
    frozenset({"human", "humanoid", "amr"}),
)


def _counts_key(counts: dict[str, int]) -> tuple[int, int, tuple[int, int, int]]:
    """Return the required deterministic tie-break order."""
    return (
        sum(counts.values()),
        counts["humanoid"],
        (counts["human"], counts["humanoid"], counts["amr"]),
    )


def optimize_crew(
    policy: frozenset[str] | set[str],
    sim_config: dict[str, Any],
    tco_assumptions: dict[str, Any],
    lambda_per_hour: float,
    target_rho: float = 0.85,
    require_each_policy_class: bool = False,
    balance_agent_types: tuple[str, str] | None = None,
    humanoid_throughput_multiplier: float = 1.0,
    cycle_time_overrides: dict[str, tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Find the lowest five-year NPV-cost integer crew allowed by ``policy``.

    Every allowed agent type is enumerated from 0 through 12; forbidden types
    are fixed at zero. The returned ``npv`` is a positive discounted *cost*
    (the TCO pipeline represents cash outflows as a negative financial NPV).
    ``frontier`` contains every feasible crew sorted by cost and the documented
    deterministic tie-break: total units, humanoid units, then type-count tuple.
    ``require_each_policy_class`` enforces at least one unit of every allowed
    class and evaluates its own rho against ``target_rho``. It is used for the
    F-221 fair-comparison scenario policies; the default preserves F-220's
    permissive "allowed technologies" frontier. ``balance_agent_types`` makes
    a hybrid select the closest integer split before comparing costs. The
    future humanoid multiplier changes both its effective service time and TCO.
    ``cycle_time_overrides`` lets the caller provide Module 2's empirical,
    availability-adjusted service times without mutating the baseline config.

    The humanoid cycle-time fallback mirrors Module 2 when its capability
    summary has not populated the baseline config yet.
    """
    allowed = _normalise_policy(policy)
    if lambda_per_hour < 0:
        raise ValueError("lambda_per_hour must be non-negative")
    if not 0 < target_rho <= 1:
        raise ValueError("target_rho must be in (0, 1]")
    if humanoid_throughput_multiplier <= 0:
        raise ValueError("humanoid_throughput_multiplier must be positive")
    if balance_agent_types is not None and not set(balance_agent_types).issubset(allowed):
        raise ValueError("balance_agent_types must be included in policy")

    cycle_times = _agent_cycle_times(sim_config)
    if cycle_time_overrides is not None:
        unknown_overrides = set(cycle_time_overrides).difference(_AGENT_TYPES)
        if unknown_overrides:
            raise ValueError(f"Unsupported cycle-time overrides: {sorted(unknown_overrides)}")
        cycle_times.update(cycle_time_overrides)
    cycle_times["humanoid"] = (
        cycle_times["humanoid"][0] / humanoid_throughput_multiplier,
        cycle_times["humanoid"][1] / humanoid_throughput_multiplier,
    )
    financial_params = build_financial_params(tco_assumptions, sim_config)
    operations = sim_config.get("operations", {})
    count_ranges = [
        range(_MAX_CREW_PER_TYPE + 1) if agent_type in allowed else range(1)
        for agent_type in _AGENT_TYPES
    ]
    feasible: list[dict[str, Any]] = []

    for count_values in product(*count_ranges):
        counts: dict[str, int] = dict(zip(_AGENT_TYPES, count_values, strict=True))
        total_units = sum(counts.values())
        if total_units == 0:
            continue
        # ADR-0017: reject pure-AMR crews even when amr is an allowed technology.
        if counts["amr"] > 0 and counts["human"] == 0 and counts["humanoid"] == 0:
            continue
        if require_each_policy_class and any(
            counts.get(agent_type, 0) == 0 for agent_type in allowed
        ):
            continue

        class_rho = {
            agent_type: (lambda_per_hour / 3600.0) * cycle_times[agent_type][0] / count
            for agent_type, count in counts.items()
            if count > 0
        }
        if require_each_policy_class and any(
            class_rho[agent_type] > target_rho for agent_type in allowed
        ):
            continue

        profiles = [
            AgentProfile(
                agent_type=agent_type,
                cycle_time_mean=cycle_times[agent_type][0],
                cycle_time_std=cycle_times[agent_type][1],
                count=counts[agent_type],
            )
            for agent_type in _AGENT_TYPES
            if counts[agent_type] > 0
        ]
        scenario = WarehouseScenario(
            scenario_id="crew-optimizer",
            architecture=str(sim_config.get("architecture", "autostore")),
            total_agents=total_units,
            agent_profiles=profiles,
            order_arrival_rate_per_hour=float(lambda_per_hour),
            shift_hours=float(operations.get("shift_hours", 8.0)),
        )
        rho = predict_utilisation(scenario)
        if rho > target_rho:
            continue

        result = compute_tco_scenario(
            "crew-optimizer",
            {"throughput_orders_per_shift": float(lambda_per_hour) * scenario.shift_hours},
            financial_params,
            years=int(tco_assumptions.get("financial", {}).get("horizon_years", 5)),
            discount_rate=float(financial_params["discount_rate"]),
            baseline_annual_opex=0.0,
            composition={
                "n_human": counts["human"],
                "n_humanoid": counts["humanoid"],
                "n_amr": counts["amr"],
                "throughput_multiplier": humanoid_throughput_multiplier,
            },
        )
        feasible.append(
            {
                "agent_counts": counts,
                "npv": -float(result["npv_eur"]),
                "rho": float(rho),
                "class_rho": class_rho,
            }
        )

    if not feasible:
        raise ValueError(
            f"No feasible crew for policy {sorted(allowed)} within 0–{_MAX_CREW_PER_TYPE} "
            f"units per type at lambda_per_hour={lambda_per_hour} and target_rho={target_rho}"
        )

    def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
        imbalance = (
            abs(
                row["agent_counts"][balance_agent_types[0]]
                - row["agent_counts"][balance_agent_types[1]]
            )
            if balance_agent_types is not None
            else 0
        )
        return (imbalance, row["npv"], *_counts_key(row["agent_counts"]))

    feasible.sort(key=sort_key)
    return {"best": feasible[0], "frontier": feasible}


def generate_demand_frontier(project_root: Path) -> dict[str, Path]:
    """Generate the demand-by-shift crew frontier and its entry chart.

    Each grid point uses the deterministic optimizer under the same utilization
    target. Shift counts represent separately staffed shifts; every shift after
    the first carries the configured night-shift wage premium. Robot hardware is
    costed once per shift crew, which makes this an explicit conservative
    staffing comparison rather than a claim that robots run unattended.
    """
    sim_config = (
        yaml.safe_load(
            (project_root / "config" / "autostore_baseline.yaml").read_text(encoding="utf-8")
        )
        or {}
    )
    tco_assumptions = (
        yaml.safe_load(
            (project_root / "config" / "tco_assumptions.yaml").read_text(encoding="utf-8")
        )
        or {}
    )
    frontier_config = tco_assumptions.get("demand_frontier", {})
    lambdas = [
        float(value) for value in frontier_config.get("lambda_per_hour", [120, 200, 300, 400])
    ]
    shifts = [int(value) for value in frontier_config.get("shifts", [1, 2, 3])]
    night_premium = float(frontier_config.get("night_shift_premium", 1.5))
    target_rho = float(frontier_config.get("target_rho", 0.85))

    rows: list[dict[str, Any]] = []
    for lambda_per_hour in lambdas:
        for shift_count in shifts:
            # Average cost multiplier across one day shift and N-1 premium shifts.
            wage_multiplier = (1.0 + (shift_count - 1) * night_premium) / shift_count
            shifted_assumptions = json.loads(json.dumps(tco_assumptions))
            labor = shifted_assumptions.setdefault("labor", {})
            labor["base_hourly_wage_eur"] = (
                float(labor.get("base_hourly_wage_eur", 18.5)) * wage_multiplier
            )
            overrides = module_02_humanoid_cycle_overrides(sim_config, project_root)
            result = optimize_crew(
                frozenset(_AGENT_TYPES),
                sim_config,
                shifted_assumptions,
                lambda_per_hour=lambda_per_hour,
                target_rho=target_rho,
                cycle_time_overrides=overrides or None,
            )
            best = result["best"]
            counts = best["agent_counts"]
            rows.append(
                {
                    "lambda_per_hour": lambda_per_hour,
                    "shifts": shift_count,
                    "night_shift_premium": night_premium,
                    "target_rho": target_rho,
                    "human_count": counts["human"],
                    "humanoid_count": counts["humanoid"],
                    "amr_count": counts["amr"],
                    "robot_count": counts["humanoid"] + counts["amr"],
                    "npv_eur": best["npv"],
                    "rho": best["rho"],
                }
            )

    reports_dir = project_root / "reports"
    charts_dir = reports_dir / "executive_charts"
    reports_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "demand_frontier.json"
    report_path.write_text(
        json.dumps(
            {
                "methodology": (
                    "Deterministic crew optimization over demand and separately staffed shifts."
                ),
                "lambda_per_hour": lambdas,
                "shifts": shifts,
                "night_shift_premium": night_premium,
                "target_rho": target_rho,
                "results": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    for shift_count in shifts:
        subset = [row for row in rows if row["shifts"] == shift_count]
        ax.plot(
            [row["lambda_per_hour"] for row in subset],
            [row["robot_count"] for row in subset],
            marker="o",
            label=f"{shift_count} shift{'s' if shift_count > 1 else ''}",
        )
    ax.set_xlabel("Demand (orders per hour)")
    ax.set_ylabel("Robots in optimized crew")
    ax.set_title("Robot entry frontier by demand and shift count")
    ax.set_xticks(lambdas)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title=f"Night premium ×{night_premium:g}")
    fig.tight_layout()
    chart_path = charts_dir / "09_robot_entry_frontier.png"
    fig.savefig(chart_path, dpi=300)
    plt.close(fig)
    return {"report": report_path, "chart": chart_path}
