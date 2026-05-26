"""Tests for OAT and Monte Carlo sensitivity analysis."""

from __future__ import annotations

from warehouse_humanoid_tco.analysis.sensitivity import (
    compute_tco_for_params,
    run_monte_carlo_sensitivity,
    run_oat_sensitivity,
)
from warehouse_humanoid_tco.evaluation.validation import validate_human_baseline_throughput

# ── compute_tco_for_params ─────────────────────────────────────────────────────


def test_compute_tco_all_human_no_capex() -> None:
    npv = compute_tco_for_params(
        humanoid_count=0,
        human_count=8,
        humanoid_capex=120000,
        human_wage=18.50,
        human_overhead=1.35,
    )
    assert npv < 0


def test_compute_tco_no_workers_no_capex() -> None:
    npv = compute_tco_for_params(
        humanoid_count=0,
        human_count=0,
        humanoid_capex=0,
        human_wage=0,
        human_overhead=1.0,
    )
    assert npv == 0.0


def test_compute_tco_higher_wage_more_negative() -> None:
    npv_low = compute_tco_for_params(0, 8, 0, human_wage=15.0, human_overhead=1.35)
    npv_high = compute_tco_for_params(0, 8, 0, human_wage=25.0, human_overhead=1.35)
    assert npv_low > npv_high


def test_compute_tco_higher_capex_more_negative() -> None:
    npv_low = compute_tco_for_params(2, 0, humanoid_capex=80000, human_wage=0, human_overhead=1.0)
    npv_high = compute_tco_for_params(2, 0, humanoid_capex=200000, human_wage=0, human_overhead=1.0)
    assert npv_low > npv_high


# ── run_oat_sensitivity ────────────────────────────────────────────────────────


def _base_params() -> dict:
    return {
        "humanoid_count": 2,
        "human_count": 6,
        "humanoid_capex_eur": 120000.0,
        "human_wage_eur": 18.50,
        "human_overhead_mult": 1.35,
    }


def test_oat_returns_correct_count() -> None:
    param_ranges = {"humanoid_capex_eur": (60000, 180000)}
    results = run_oat_sensitivity(_base_params(), param_ranges, n_steps=5)
    assert len(results) == 5


def test_oat_result_schema() -> None:
    param_ranges = {"human_wage_eur": (10.0, 25.0)}
    results = run_oat_sensitivity(_base_params(), param_ranges, n_steps=3)
    for r in results:
        assert "parameter" in r
        assert "parameter_value" in r
        assert "npv_eur" in r


def test_oat_multiple_params() -> None:
    param_ranges = {
        "humanoid_capex_eur": (60000, 180000),
        "human_wage_eur": (10.0, 25.0),
    }
    results = run_oat_sensitivity(_base_params(), param_ranges, n_steps=5)
    assert len(results) == 10  # 2 params × 5 steps


def test_oat_npv_monotonic_with_capex() -> None:
    param_ranges = {"humanoid_capex_eur": (60000, 180000)}
    results = run_oat_sensitivity(_base_params(), param_ranges, n_steps=5)
    npvs = [r["npv_eur"] for r in results]
    # Higher capex → more negative NPV → monotonically decreasing
    assert all(npvs[i] >= npvs[i + 1] for i in range(len(npvs) - 1))


# ── run_monte_carlo_sensitivity ────────────────────────────────────────────────


def _mc_distributions() -> dict:
    return {
        "humanoid_capex_eur": {"type": "normal", "mean": 120000, "std": 20000},
        "human_wage_eur": {"type": "uniform", "low": 15.0, "high": 22.0},
    }


def test_mc_returns_correct_sample_count() -> None:
    samples, summary = run_monte_carlo_sensitivity(
        _base_params(), _mc_distributions(), n_samples=50, seed=42
    )
    assert len(samples) == 50
    assert summary["n_samples"] == 50


def test_mc_summary_has_percentiles() -> None:
    _, summary = run_monte_carlo_sensitivity(
        _base_params(), _mc_distributions(), n_samples=50, seed=42
    )
    for key in ["npv_mean", "npv_std", "npv_p5", "npv_p50", "npv_p95"]:
        assert key in summary


def test_mc_npv_variance_nonzero() -> None:
    # Catches parameter collapse (e.g. if distributions stop varying → all NPVs identical)
    _, summary = run_monte_carlo_sensitivity(
        _base_params(), _mc_distributions(), n_samples=50, seed=42
    )
    assert summary["npv_std"] > 0, "MC collapsed: npv_std=0 means parameters are not varying"


def test_mc_deterministic_with_seed() -> None:
    _, s1 = run_monte_carlo_sensitivity(_base_params(), _mc_distributions(), n_samples=50, seed=7)
    _, s2 = run_monte_carlo_sensitivity(_base_params(), _mc_distributions(), n_samples=50, seed=7)
    assert abs(s1["npv_mean"] - s2["npv_mean"]) < 0.01


def test_mc_sample_schema() -> None:
    samples, _ = run_monte_carlo_sensitivity(
        _base_params(), _mc_distributions(), n_samples=10, seed=42
    )
    for s in samples:
        assert "sample_id" in s
        assert "npv_eur" in s
        assert s["npv_eur"] < 0  # cost model: all NPVs negative


def test_mc_p5_less_than_p95() -> None:
    _, summary = run_monte_carlo_sensitivity(
        _base_params(), _mc_distributions(), n_samples=200, seed=42
    )
    assert summary["npv_p5"] < summary["npv_p95"]


# ── validate_human_baseline_throughput ────────────────────────────────────────


def test_validation_pass_within_tolerance() -> None:
    result = validate_human_baseline_throughput(simulated_throughput=900.0)
    assert result["passed"] is True
    assert result["status"] == "PASS"


def test_validation_fail_outside_tolerance() -> None:
    result = validate_human_baseline_throughput(simulated_throughput=500.0)
    assert result["passed"] is False
    assert result["status"] == "FAIL"


def test_validation_exact_reference() -> None:
    result = validate_human_baseline_throughput(simulated_throughput=960.0)
    assert result["passed"] is True
    assert result["relative_error"] == 0.0


def test_validation_custom_reference() -> None:
    result = validate_human_baseline_throughput(
        simulated_throughput=200.0, reference_throughput=200.0
    )
    assert result["passed"] is True
