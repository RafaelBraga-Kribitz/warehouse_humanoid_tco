"""Unit tests for the TCO financial model and pipeline compute_tco_scenario."""

from __future__ import annotations

from warehouse_humanoid_tco.models.tco import (
    compute_annual_humanoid_opex,
    compute_annual_labor_cost,
    compute_humanoid_capex,
    compute_irr,
    compute_npv,
    compute_payback_years,
)
from warehouse_humanoid_tco.pipelines.module_03_tco import (
    _BASELINE_ANNUAL_OPEX,
    compute_tco_scenario,
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


def test_compute_humanoid_capex() -> None:
    result = compute_humanoid_capex(
        n_humanoids=2,
        unit_capex_eur=120000,
        installation_cost_per_unit_eur=8000,
        training_cost_per_unit_eur=5000,
    )
    assert result == 2 * (120000 + 8000 + 5000)


def test_compute_annual_humanoid_opex() -> None:
    result = compute_annual_humanoid_opex(
        n_humanoids=1,
        unit_capex_eur=120000,
        annual_maintenance_fraction=0.08,
        energy_kwh_per_shift=8.0,
        energy_cost_eur_per_kwh=0.22,
        operating_days=252,
    )
    maintenance = 120000 * 0.08
    energy = 8.0 * 0.22 * 252
    assert abs(result - (maintenance + energy)) < 0.01


def test_irr_no_positive_flows_returns_none_or_negative() -> None:
    cash_flows = [-100_000.0, -50_000.0, -50_000.0]
    irr = compute_irr(cash_flows)
    assert irr is None or irr < 0


# ── pipelines/module_03_tco.py ──────────────────────────────────────────────


def test_baseline_annual_opex_constant() -> None:
    expected = 8 * (252 * 8) * 18.50 * 1.35
    assert abs(_BASELINE_ANNUAL_OPEX - expected) < 1.0


def test_tco_scenario_baseline_human() -> None:
    result = compute_tco_scenario("S-baseline-human", {}, {})
    assert result["npv_eur"] < 0
    assert result["total_capex_eur"] == 0.0
    assert result["total_opex_5yr_eur"] > 0
    assert result["cost_reduction_vs_baseline_pct"] == 0.0
    assert result["payback_years"] == 0.0  # no capex to recover


def test_tco_scenario_pure_humanoid_no_opex() -> None:
    result = compute_tco_scenario("S-pure-humanoid", {}, {})
    assert result["total_opex_5yr_eur"] == 0.0
    assert result["total_capex_eur"] > 0
    assert result["cost_reduction_vs_baseline_pct"] == 100.0
    assert result["payback_years"] is not None and result["payback_years"] > 0


def test_tco_scenario_hybrid_amr_lowest_npv() -> None:
    baseline = compute_tco_scenario("S-baseline-human", {}, {})
    hybrid_amr = compute_tco_scenario("S-hybrid-amr", {}, {})
    pure_humanoid = compute_tco_scenario("S-pure-humanoid", {}, {})
    assert hybrid_amr["npv_eur"] > baseline["npv_eur"]
    assert hybrid_amr["npv_eur"] > pure_humanoid["npv_eur"]


def test_tco_scenario_no_irr_field() -> None:
    result = compute_tco_scenario("S-hybrid-amr", {}, {})
    assert "irr" not in result


def test_tco_scenario_required_keys() -> None:
    result = compute_tco_scenario("S-hybrid-amr", {}, {})
    required = {
        "scenario_id",
        "npv_eur",
        "cost_reduction_vs_baseline_pct",
        "payback_years",
        "total_capex_eur",
        "total_opex_5yr_eur",
        "pipeline_version",
    }
    assert required.issubset(result.keys())


def test_tco_scenario_all_five_scenarios() -> None:
    scenarios = [
        "S-baseline-human",
        "S-pure-humanoid",
        "S-hybrid-5050",
        "S-hybrid-amr",
        "S-future-2028",
    ]
    results = [compute_tco_scenario(s, {}, {}) for s in scenarios]
    for r in results:
        assert r["npv_eur"] < 0  # all are cost models — NPV must be negative
