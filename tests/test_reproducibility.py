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


def test_different_run_ids_differ() -> None:
    # Different run_ids with the same scenario should produce independent results.
    # The simulation uses run_id to offset the random seed, so run_id=0 and run_id=1
    # should diverge for non-trivial scenarios.
    result_0 = run_scenario(_make_scenario(seed=42), run_id=0)
    result_1 = run_scenario(_make_scenario(seed=42), run_id=1)
    # At least one metric should differ across independent runs
    keys = ["throughput_orders_per_shift", "queue_length_mean", "utilization_human"]
    assert any(result_0[k] != result_1[k] for k in keys if result_0.get(k) is not None)
