"""Tests for warehouse simulation model."""

from __future__ import annotations

import numpy as np

from warehouse_humanoid_tco.evaluation.validation import compare_throughput_distributions
from warehouse_humanoid_tco.models.simulation import (
    AgentProfile,
    WarehouseScenario,
    run_scenario,
)


def _human_scenario(shift_hours: float = 1.0, seed: int = 42) -> WarehouseScenario:
    return WarehouseScenario(
        scenario_id="S-baseline-human",
        architecture="autostore",
        total_agents=8,
        agent_profiles=[
            AgentProfile(
                agent_type="human",
                cycle_time_mean=25.0,
                cycle_time_std=8.0,
                count=8,
                seed=seed,
            )
        ],
        order_arrival_rate_per_hour=120.0,
        shift_hours=shift_hours,
        seed=seed,
    )


def test_simulation_runs_to_completion() -> None:
    result = run_scenario(_human_scenario(), run_id=0)
    assert result is not None
    assert "throughput_orders_per_shift" in result
    assert result["throughput_orders_per_shift"] >= 0


def test_simulation_throughput_positive() -> None:
    result = run_scenario(_human_scenario(shift_hours=8.0), run_id=0)
    assert result["throughput_orders_per_shift"] > 0


def test_simulation_result_schema() -> None:
    result = run_scenario(_human_scenario(), run_id=0)
    required = {
        "scenario_id",
        "run_id",
        "throughput_orders_per_shift",
        "queue_length_mean",
        "pipeline_version",
        "seed",
    }
    assert required.issubset(result.keys())


def test_simulation_scenario_id_propagated() -> None:
    result = run_scenario(_human_scenario(), run_id=3)
    assert result["scenario_id"] == "S-baseline-human"
    assert result["run_id"] == 3


def test_simulation_deterministic() -> None:
    scenario = _human_scenario(seed=7)
    r1 = run_scenario(scenario, run_id=0)
    r2 = run_scenario(scenario, run_id=0)
    assert r1["throughput_orders_per_shift"] == r2["throughput_orders_per_shift"]
    assert r1["queue_length_mean"] == r2["queue_length_mean"]


def test_simulation_multi_agent_type() -> None:
    scenario = WarehouseScenario(
        scenario_id="S-hybrid-amr",
        architecture="autostore",
        total_agents=8,
        agent_profiles=[
            AgentProfile("human", 25.0, 8.0, count=5, seed=42),
            AgentProfile("humanoid", 35.0, 10.0, count=2, seed=42),
            AgentProfile("amr", 35.0, 5.0, count=1, seed=42),
        ],
        order_arrival_rate_per_hour=120.0,
        shift_hours=1.0,
        seed=42,
    )
    result = run_scenario(scenario, run_id=0)
    assert result["throughput_orders_per_shift"] >= 0
    assert "utilization_human" in result
    assert "utilization_humanoid" in result
    assert "utilization_amr" in result


def test_simulation_queue_length_nonnegative() -> None:
    result = run_scenario(_human_scenario(shift_hours=8.0), run_id=0)
    assert result["queue_length_mean"] >= 0.0


def test_scenarios_with_different_agent_mixes_produce_different_throughput() -> None:
    """Regression test for the agent routing bug.

    A hybrid scenario with very slow humanoids should produce lower throughput
    than a human-only scenario, because some orders are handled by slow humanoids.
    If this test fails, simulation.pick_order() is routing all orders to the
    first profile (the original v0.1.0 bug).
    """
    human_only = WarehouseScenario(
        scenario_id="S-baseline-human",
        architecture="autostore",
        total_agents=8,
        agent_profiles=[
            AgentProfile("human", 25.0, 8.0, count=8, seed=42),
        ],
        order_arrival_rate_per_hour=120.0,
        shift_hours=1.0,
        seed=42,
    )
    hybrid_slow = WarehouseScenario(
        scenario_id="S-test-hybrid",
        architecture="autostore",
        total_agents=8,
        agent_profiles=[
            AgentProfile("human", 25.0, 8.0, count=4, seed=42),
            AgentProfile("very_slow_humanoid", 250.0, 80.0, count=4, seed=42),
        ],
        order_arrival_rate_per_hour=120.0,
        shift_hours=1.0,
        seed=42,
    )
    h_thru = run_scenario(human_only, run_id=0)["throughput_orders_per_shift"]
    x_thru = run_scenario(hybrid_slow, run_id=0)["throughput_orders_per_shift"]
    assert h_thru > x_thru, (
        f"Hybrid scenario with very slow humanoids ({x_thru:.0f}) should produce "
        f"lower throughput than human-only ({h_thru:.0f}). "
        f"Equal throughput = agent routing bug."
    )


# ---------------------------------------------------------------------------
# Kruskal-Wallis cross-scenario throughput comparison tests
# ---------------------------------------------------------------------------


def test_kruskal_detects_identical_scenarios() -> None:
    """3 scenarios sampled from the same distribution should not be rejected."""
    rng = np.random.default_rng(seed=0)
    scenario_runs = {
        "S-A": rng.normal(loc=120.0, scale=10.0, size=20).tolist(),
        "S-B": rng.normal(loc=120.0, scale=10.0, size=20).tolist(),
        "S-C": rng.normal(loc=120.0, scale=10.0, size=20).tolist(),
    }
    result = compare_throughput_distributions(scenario_runs, alpha=0.05)
    assert result["rejected"] is False
    assert result["p_value"] > 0.05
    assert result["n_scenarios"] == 3
    assert "homogeneous" in result["note"]


def test_kruskal_detects_different_scenarios() -> None:
    """2 scenarios from very different distributions should be rejected."""
    rng = np.random.default_rng(seed=1)
    scenario_runs = {
        "S-high": rng.normal(loc=200.0, scale=5.0, size=20).tolist(),
        "S-low": rng.normal(loc=50.0, scale=5.0, size=20).tolist(),
    }
    result = compare_throughput_distributions(scenario_runs, alpha=0.05)
    assert result["rejected"] is True
    assert result["p_value"] < 0.05
    assert result["n_scenarios"] == 2
    assert "routing divergence" in result["note"]


def test_kruskal_raises_on_single_scenario() -> None:
    """ValueError must be raised when fewer than 2 scenarios are provided."""
    import pytest

    with pytest.raises(ValueError, match="At least 2 scenarios"):
        compare_throughput_distributions({"S-only": [100.0, 110.0, 105.0]})
