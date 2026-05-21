"""Tests for warehouse simulation model."""

from __future__ import annotations

import pytest

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
    required = {"scenario_id", "run_id", "throughput_orders_per_shift",
                "queue_length_mean", "pipeline_version", "seed"}
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
