"""F-222 — operational availability and realistic TCO cash-flow invariants."""

from __future__ import annotations

from pathlib import Path

import pytest

from warehouse_humanoid_tco.analysis.sensitivity import (
    _load_sensitivity_config,
    compute_tco_for_params,
)
from warehouse_humanoid_tco.models.simulation import (
    AgentProfile,
    WarehouseScenario,
    compute_capacity_ceiling,
    compute_operational_availability,
)
from warehouse_humanoid_tco.pipelines.module_03_tco import compute_tco_scenario


def _scenario_result(**assumptions: float) -> dict:
    return compute_tco_scenario(
        "S-pure-humanoid",
        {"throughput_orders_per_shift": 100.0},
        assumptions,
        baseline_annual_opex=1_000_000.0,
        years=5,
        discount_rate=0.08,
        composition={"n_human": 0.0, "n_humanoid": 1.0, "n_amr": 0.0},
    )


def test_availability_derates_capacity_by_reciprocal_cycle_time() -> None:
    availability = compute_operational_availability(40.0, 0.5, 4.0, 1.0)
    assert availability == pytest.approx(40.0 / 40.5 * 4.0 / 5.0)

    base = WarehouseScenario("base", "test", 1, [AgentProfile("humanoid", 10.0, 0.0, 1)], 100.0)
    derated = WarehouseScenario(
        "derated",
        "test",
        1,
        [AgentProfile("humanoid", 10.0 / availability, 0.0, 1)],
        100.0,
    )
    assert compute_capacity_ceiling(derated)["capacity_orders_per_shift"] == pytest.approx(
        compute_capacity_ceiling(base)["capacity_orders_per_shift"] * availability
    )


def test_integration_cost_is_once_per_humanoid_site_capex() -> None:
    without = _scenario_result(
        humanoid_availability=1.0,
        humanoid_capex_eur=120_000.0,
        integration_cost_eur=0.0,
    )
    with_integration = _scenario_result(
        humanoid_availability=1.0,
        humanoid_capex_eur=120_000.0,
        integration_cost_eur=200_000.0,
    )
    assert with_integration["total_capex_eur"] - without["total_capex_eur"] == pytest.approx(
        200_000.0
    )


def test_wage_growth_escalates_direct_and_supervision_labor() -> None:
    common = {
        "humanoid_availability": 1.0,
        "integration_cost_eur": 0.0,
        "humanoid_supervision_ratio": 0.25,
        "human_hourly_wage_eur": 20.0,
    }
    no_growth = compute_tco_scenario(
        "mixed",
        {},
        {**common, "annual_wage_growth_rate": 0.0},
        baseline_annual_opex=1_000_000.0,
        composition={"n_human": 1.0, "n_humanoid": 1.0, "n_amr": 0.0},
    )
    growth = compute_tco_scenario(
        "mixed",
        {},
        {**common, "annual_wage_growth_rate": 0.05},
        baseline_annual_opex=1_000_000.0,
        composition={"n_human": 1.0, "n_humanoid": 1.0, "n_amr": 0.0},
    )
    assert growth["total_opex_5yr_eur_nominal"] > no_growth["total_opex_5yr_eur_nominal"]


def test_supervision_ratio_is_in_oat_and_monte_carlo_config() -> None:
    root = Path(__file__).resolve().parents[2]
    sensitivity = _load_sensitivity_config(root)
    assert sensitivity["oat"]["humanoid_supervision_ratio"] == [0.05, 0.50]
    assert sensitivity["monte_carlo"]["humanoid_supervision_ratio"] == {
        "type": "uniform",
        "low": 0.05,
        "high": 0.50,
    }
    assert compute_tco_for_params(n_human=0, n_humanoid=1, humanoid_supervision_ratio=0.5) < (
        compute_tco_for_params(n_human=0, n_humanoid=1, humanoid_supervision_ratio=0.05)
    )


def test_residual_salvage_increases_npv_at_horizon() -> None:
    without = _scenario_result(
        humanoid_availability=1.0,
        integration_cost_eur=0.0,
        humanoid_residual_value_fraction=0.0,
    )
    with_salvage = _scenario_result(
        humanoid_availability=1.0,
        integration_cost_eur=0.0,
        humanoid_residual_value_fraction=0.10,
        humanoid_useful_life_years=7.0,
    )
    expected_salvage = 120_000.0 * 0.10 * (7.0 - 5.0) / 7.0 / 1.08**5
    assert with_salvage["npv_eur"] - without["npv_eur"] == pytest.approx(expected_salvage)
