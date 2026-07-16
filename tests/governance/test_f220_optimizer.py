"""F-220 — integer crew optimizer verification."""

from __future__ import annotations

from itertools import product
from pathlib import Path

import pytest
import yaml
from _ratchet import ratchet

from warehouse_humanoid_tco.analysis.crew_optimizer import optimize_crew
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

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_TYPES = ("human", "humanoid", "amr")


@pytest.fixture
def configs() -> tuple[dict, dict]:
    """Load the two configuration inputs consumed by the optimizer."""
    sim_config = yaml.safe_load((REPO_ROOT / "config" / "autostore_baseline.yaml").read_text())
    tco_assumptions = yaml.safe_load((REPO_ROOT / "config" / "tco_assumptions.yaml").read_text())
    return sim_config, tco_assumptions


def _cycle_means(sim_config: dict) -> dict[str, float]:
    """Mirror optimizer per-order service times (line × pick_lines, F-237)."""
    factor = sim_config["capability_transfer"]["wbt_to_production_factor"]["point_estimate"]
    pick_lines = float(sim_config["operations"]["pick_lines_per_order"])
    human_mean, _ = scale_line_cycle_to_order(
        float(sim_config["agents"]["human"]["cycle_time_mean_seconds"]),
        0.0,
        pick_lines,
    )
    amr_mean, _ = scale_line_cycle_to_order(
        float(sim_config["agents"]["amr"]["cycle_time_mean_seconds"]),
        0.0,
        pick_lines,
    )
    humanoid_mean, _ = scale_line_cycle_to_order(30.0 / factor, 0.0, pick_lines)
    return {
        "human": human_mean,
        "humanoid": humanoid_mean,
        "amr": amr_mean,
    }


def _crew_cost_and_rho(
    counts: dict[str, int],
    sim_config: dict,
    tco_assumptions: dict,
    lambda_per_hour: float,
) -> tuple[float, float]:
    means = _cycle_means(sim_config)
    profiles = [
        AgentProfile(
            agent_type=agent_type,
            cycle_time_mean=means[agent_type],
            cycle_time_std=0.0,
            count=count,
        )
        for agent_type, count in counts.items()
        if count > 0
    ]
    scenario = WarehouseScenario(
        scenario_id="f220-brute-force",
        architecture=sim_config["architecture"],
        total_agents=sum(counts.values()),
        agent_profiles=profiles,
        order_arrival_rate_per_hour=lambda_per_hour,
        shift_hours=sim_config["operations"]["shift_hours"],
    )
    rho = predict_utilisation(scenario)
    params = build_financial_params(tco_assumptions, sim_config)
    result = compute_tco_scenario(
        "f220-brute-force",
        {"throughput_orders_per_shift": lambda_per_hour * scenario.shift_hours},
        params,
        baseline_annual_opex=0.0,
        years=tco_assumptions["financial"]["horizon_years"],
        discount_rate=params["discount_rate"],
        composition={
            "n_human": counts["human"],
            "n_humanoid": counts["humanoid"],
            "n_amr": counts["amr"],
        },
    )
    return -result["npv_eur"], rho


@pytest.mark.parametrize(
    "policy",
    ({"human"}, {"human", "amr"}, {"human", "humanoid", "amr"}),
)
def test_reported_optimum_has_no_cheaper_feasible_neighbour(
    configs: tuple[dict, dict], policy: set[str]
) -> None:
    """Brute-force the ±2 neighborhood around each policy's reported optimum."""
    sim_config, tco_assumptions = configs
    lambda_per_hour = sim_config["operations"]["order_arrival_rate_per_hour"]
    result = optimize_crew(policy, sim_config, tco_assumptions, lambda_per_hour)
    best = result["best"]
    best_counts = best["agent_counts"]

    ranges = [
        (
            range(max(0, best_counts[agent_type] - 2), min(12, best_counts[agent_type] + 2) + 1)
            if agent_type in policy
            else range(1)
        )
        for agent_type in AGENT_TYPES
    ]
    for values in product(*ranges):
        counts = dict(zip(AGENT_TYPES, values, strict=True))
        if sum(counts.values()) == 0:
            continue
        # ADR-0017: pure-AMR crews are excluded from the optimizer search.
        if counts["amr"] > 0 and counts["human"] == 0 and counts["humanoid"] == 0:
            continue
        cost, rho = _crew_cost_and_rho(counts, sim_config, tco_assumptions, lambda_per_hour)
        if rho <= 0.85:
            assert cost >= best["npv"]


def test_infeasible_policy_raises(configs: tuple[dict, dict]) -> None:
    sim_config, tco_assumptions = configs
    with pytest.raises(ValueError, match="No feasible crew"):
        optimize_crew({"human"}, sim_config, tco_assumptions, lambda_per_hour=1_000_000)


def test_crew_optimization_is_deterministic(configs: tuple[dict, dict]) -> None:
    sim_config, tco_assumptions = configs
    policy = frozenset({"human", "humanoid", "amr"})
    first = optimize_crew(policy, sim_config, tco_assumptions, lambda_per_hour=120.0)
    second = optimize_crew(policy, sim_config, tco_assumptions, lambda_per_hour=120.0)
    assert first == second
    ratchet("F-220", fixed=True, gap_msg="crew optimizer unavailable")
