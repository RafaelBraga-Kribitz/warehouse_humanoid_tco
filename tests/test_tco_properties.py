"""F-217 — property invariants for the TCO kernel and scenario adapter."""

from __future__ import annotations

import math

from hypothesis import given
from hypothesis import strategies as st

from warehouse_humanoid_tco.models.tco import (
    compute_annual_labor_cost,
    compute_humanoid_capex,
    compute_npv,
    compute_payback_years,
)
from warehouse_humanoid_tco.pipelines.module_03_tco import (
    compute_cost_per_order,
    compute_tco_scenario,
)

POSITIVE_FLOATS = st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False)


@given(st.lists(st.floats(min_value=-1_000_000, max_value=-0.01), min_size=1, max_size=10))
def test_npv_of_all_costs_is_negative(cash_flows: list[float]) -> None:
    assert compute_npv(cash_flows, 0.08) < 0


@given(st.lists(st.floats(min_value=-1_000_000, max_value=-0.01), min_size=1, max_size=10))
def test_npv_of_costs_increases_with_discount_rate(cash_flows: list[float]) -> None:
    assert compute_npv(cash_flows, 0.12) >= compute_npv(cash_flows, 0.04)


@given(
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100),
    POSITIVE_FLOATS,
    st.floats(min_value=1.0, max_value=3.0),
)
def test_labor_cost_is_linear_in_human_count(
    left: int, right: int, hourly_wage: float, overhead: float
) -> None:
    assert math.isclose(
        compute_annual_labor_cost(left + right, hourly_wage, overhead),
        compute_annual_labor_cost(left, hourly_wage, overhead)
        + compute_annual_labor_cost(right, hourly_wage, overhead),
    )


@given(
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100),
    POSITIVE_FLOATS,
    POSITIVE_FLOATS,
    POSITIVE_FLOATS,
)
def test_humanoid_capex_is_additive(
    left: int, right: int, unit_capex: float, installation: float, training: float
) -> None:
    assert math.isclose(
        compute_humanoid_capex(left + right, unit_capex, installation, training),
        compute_humanoid_capex(left, unit_capex, installation, training)
        + compute_humanoid_capex(right, unit_capex, installation, training),
    )


@given(st.floats(min_value=1.0, max_value=100.0), st.floats(min_value=1.0, max_value=100.0))
def test_higher_wage_makes_human_scenario_npv_more_negative(
    lower_wage: float, wage_increment: float
) -> None:
    composition = {"n_human": 2, "n_humanoid": 0, "n_amr": 0, "throughput_multiplier": 1}
    common = {"human_overhead_multiplier": 1.35, "operating_days": 252, "shift_hours": 8}
    low = compute_tco_scenario(
        "property-human",
        {"throughput_orders_per_shift": 100},
        {**common, "human_hourly_wage_eur": lower_wage},
        baseline_annual_opex=1_000_000.0,
        composition=composition,
    )
    high = compute_tco_scenario(
        "property-human",
        {"throughput_orders_per_shift": 100},
        {**common, "human_hourly_wage_eur": lower_wage + wage_increment},
        baseline_annual_opex=1_000_000.0,
        composition=composition,
    )
    assert high["npv_eur"] < low["npv_eur"]


@given(st.floats(max_value=0.0, allow_nan=False), POSITIVE_FLOATS, POSITIVE_FLOATS)
def test_cost_per_order_is_infinite_without_positive_throughput(
    throughput: float, capex: float, opex: float
) -> None:
    assert math.isinf(compute_cost_per_order(capex, opex, throughput))


@given(st.lists(st.floats(min_value=-1_000_000, max_value=-0.01), min_size=1, max_size=10))
def test_payback_is_none_when_cash_flows_never_create_savings(cash_flows: list[float]) -> None:
    assert compute_payback_years(cash_flows) is None
