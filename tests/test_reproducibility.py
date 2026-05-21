"""Reproducibility tests: same seed → same output."""

from __future__ import annotations

from warehouse_humanoid_tco.models.simulation import AgentProfile, WarehouseScenario, run_scenario


def _make_scenario(seed: int = 42) -> WarehouseScenario:
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
        shift_hours=1.0,  # short run for test speed
        seed=seed,
    )


def test_simulation_deterministic() -> None:
    scenario = _make_scenario(seed=42)
    result_a = run_scenario(scenario, run_id=0)
    result_b = run_scenario(scenario, run_id=0)
    assert result_a["throughput_orders_per_shift"] == result_b["throughput_orders_per_shift"]


def test_different_seeds_differ() -> None:
    result_42 = run_scenario(_make_scenario(seed=42), run_id=0)
    result_99 = run_scenario(_make_scenario(seed=99), run_id=0)
    assert (
        result_42["throughput_orders_per_shift"] != result_99["throughput_orders_per_shift"]
        or result_42["queue_length_mean"] != result_99["queue_length_mean"]
    )
