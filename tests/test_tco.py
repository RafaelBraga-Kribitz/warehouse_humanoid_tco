"""Unit tests for the TCO financial model."""

from __future__ import annotations

from warehouse_humanoid_tco.models.tco import (
    compute_annual_labor_cost,
    compute_irr,
    compute_npv,
    compute_payback_years,
)


def test_annual_labor_cost_basic() -> None:
    cost = compute_annual_labor_cost(
        n_humans=10,
        hourly_wage_eur=18.50,
        overhead_multiplier=1.35,
        operating_days=252,
        shift_hours=8.0,
    )
    expected = 10 * 18.50 * 1.35 * 252 * 8.0
    assert abs(cost - expected) < 0.01


def test_npv_simple() -> None:
    # Year 0: -100k capex, years 1-5: +30k savings
    cash_flows = [-100_000] + [30_000] * 5
    npv = compute_npv(cash_flows, discount_rate=0.08)
    assert npv > 0  # profitable


def test_npv_negative_case() -> None:
    # Bad investment: pay 100k, get 5k/year for 5 years
    cash_flows = [-100_000] + [5_000] * 5
    npv = compute_npv(cash_flows, discount_rate=0.08)
    assert npv < 0


def test_payback_years_found() -> None:
    cash_flows = [-100_000] + [50_000] * 5
    payback = compute_payback_years(cash_flows)
    assert payback is not None
    assert payback == 2.0


def test_payback_years_never() -> None:
    cash_flows = [-100_000] + [1_000] * 5
    payback = compute_payback_years(cash_flows)
    assert payback is None
