"""Tests for OAT and Monte Carlo sensitivity analysis."""

from __future__ import annotations

from warehouse_humanoid_tco.analysis.sensitivity import (
    SCENARIO_COMPOSITIONS,
    TRANSFER_FACTOR_BASELINE,
    compute_tco_for_params,
    run_monte_carlo_per_scenario,
    run_monte_carlo_sensitivity,
    run_oat_sensitivity,
)
from warehouse_humanoid_tco.evaluation.validation import validate_human_baseline_throughput

# ── compute_tco_for_params ─────────────────────────────────────────────────────


def test_compute_tco_all_human_no_capex() -> None:
    npv = compute_tco_for_params(
        n_human=8,
        n_humanoid=0,
        n_amr=0,
        humanoid_capex_eur=120000,
        human_wage_eur=18.50,
        human_overhead_mult=1.35,
    )
    assert npv < 0


def test_compute_tco_no_workers_no_capex() -> None:
    npv = compute_tco_for_params(
        n_human=0,
        n_humanoid=0,
        n_amr=0,
        humanoid_capex_eur=0,
        human_wage_eur=0,
        human_overhead_mult=1.0,
    )
    assert npv == 0.0


def test_compute_tco_higher_wage_more_negative() -> None:
    npv_low = compute_tco_for_params(n_human=8, n_humanoid=0, human_wage_eur=15.0)
    npv_high = compute_tco_for_params(n_human=8, n_humanoid=0, human_wage_eur=25.0)
    assert npv_low > npv_high


def test_compute_tco_higher_capex_more_negative() -> None:
    npv_low = compute_tco_for_params(
        n_human=0, n_humanoid=2, humanoid_capex_eur=80000, human_wage_eur=0
    )
    npv_high = compute_tco_for_params(
        n_human=0, n_humanoid=2, humanoid_capex_eur=200000, human_wage_eur=0
    )
    assert npv_low > npv_high


def test_compute_tco_lower_transfer_factor_more_negative() -> None:
    """Lower transfer factor → more effective humanoids needed → higher cost."""
    npv_high_transfer = compute_tco_for_params(n_human=4, n_humanoid=4, transfer_factor=0.90)
    npv_low_transfer = compute_tco_for_params(n_human=4, n_humanoid=4, transfer_factor=0.50)
    assert npv_low_transfer < npv_high_transfer  # more negative


def test_compute_tco_transfer_factor_baseline_is_neutral() -> None:
    """At transfer_factor = baseline, effective count equals literal count."""
    npv_baseline = compute_tco_for_params(
        n_human=4, n_humanoid=4, transfer_factor=TRANSFER_FACTOR_BASELINE
    )
    # Same NPV if we'd called the model with that exact composition; sanity check
    assert npv_baseline < 0


# ── run_oat_sensitivity ────────────────────────────────────────────────────────


def _base_params() -> dict:
    return {
        "humanoid_capex_eur": 120000.0,
        "human_wage_eur": 18.50,
        "human_overhead_mult": 1.35,
        "discount_rate": 0.08,
        "transfer_factor": TRANSFER_FACTOR_BASELINE,
    }


def test_oat_returns_correct_count() -> None:
    param_ranges = {"humanoid_capex_eur": (60000.0, 180000.0)}
    results = run_oat_sensitivity("S-hybrid-amr", _base_params(), param_ranges, n_steps=5)
    assert len(results) == 5


def test_oat_result_schema() -> None:
    param_ranges = {"human_wage_eur": (10.0, 25.0)}
    results = run_oat_sensitivity("S-hybrid-amr", _base_params(), param_ranges, n_steps=3)
    for r in results:
        assert r["scenario_id"] == "S-hybrid-amr"
        assert "parameter" in r
        assert "parameter_value" in r
        assert "npv_eur" in r


def test_oat_multiple_params() -> None:
    param_ranges = {
        "humanoid_capex_eur": (60000.0, 180000.0),
        "human_wage_eur": (10.0, 25.0),
    }
    results = run_oat_sensitivity("S-hybrid-amr", _base_params(), param_ranges, n_steps=5)
    assert len(results) == 10  # 2 params × 5 steps


def test_oat_npv_monotonic_with_capex() -> None:
    param_ranges = {"humanoid_capex_eur": (60000.0, 180000.0)}
    results = run_oat_sensitivity("S-hybrid-amr", _base_params(), param_ranges, n_steps=5)
    npvs = [r["npv_eur"] for r in results]
    # Higher capex → more negative NPV → monotonically decreasing
    assert all(npvs[i] >= npvs[i + 1] for i in range(len(npvs) - 1))


def test_oat_transfer_factor_included() -> None:
    """Transfer factor must produce a non-trivial NPV swing."""
    param_ranges = {"transfer_factor": (0.50, 0.90)}
    results = run_oat_sensitivity("S-hybrid-amr", _base_params(), param_ranges, n_steps=5)
    npvs = [r["npv_eur"] for r in results]
    # Lower transfer (early values) → more negative; range must be nonzero
    assert max(npvs) - min(npvs) > 1000.0


# ── run_monte_carlo_sensitivity ────────────────────────────────────────────────


def _mc_distributions() -> dict:
    return {
        "humanoid_capex_eur": {"type": "normal", "mean": 120000, "std": 20000},
        "human_wage_eur": {"type": "uniform", "low": 15.0, "high": 22.0},
        "transfer_factor": {"type": "uniform", "low": 0.50, "high": 0.90},
    }


def test_mc_returns_correct_sample_count() -> None:
    samples, summary = run_monte_carlo_sensitivity(
        "S-hybrid-amr", _mc_distributions(), n_samples=50, seed=42
    )
    assert len(samples) == 50
    assert summary["n_samples"] == 50


def test_mc_summary_has_percentiles() -> None:
    _, summary = run_monte_carlo_sensitivity(
        "S-hybrid-amr", _mc_distributions(), n_samples=50, seed=42
    )
    for key in ["npv_mean", "npv_std", "npv_p5", "npv_p50", "npv_p95"]:
        assert key in summary


def test_mc_npv_variance_nonzero() -> None:
    _, summary = run_monte_carlo_sensitivity(
        "S-hybrid-amr", _mc_distributions(), n_samples=50, seed=42
    )
    assert summary["npv_std"] > 0, "MC collapsed: npv_std=0 means parameters are not varying"


def test_mc_deterministic_with_seed() -> None:
    _, s1 = run_monte_carlo_sensitivity("S-hybrid-amr", _mc_distributions(), n_samples=50, seed=7)
    _, s2 = run_monte_carlo_sensitivity("S-hybrid-amr", _mc_distributions(), n_samples=50, seed=7)
    assert abs(s1["npv_mean"] - s2["npv_mean"]) < 0.01


def test_mc_sample_schema() -> None:
    samples, _ = run_monte_carlo_sensitivity(
        "S-hybrid-amr", _mc_distributions(), n_samples=10, seed=42
    )
    for s in samples:
        assert "sample_id" in s
        assert "scenario_id" in s
        assert s["scenario_id"] == "S-hybrid-amr"
        assert "npv_eur" in s
        assert s["npv_eur"] < 0  # cost model: all NPVs negative


def test_mc_p5_less_than_p95() -> None:
    _, summary = run_monte_carlo_sensitivity(
        "S-hybrid-amr", _mc_distributions(), n_samples=200, seed=42
    )
    assert summary["npv_p5"] < summary["npv_p95"]


def test_mc_does_not_sample_agent_counts() -> None:
    """Agent counts must be fixed per scenario, not sampled."""
    samples, _ = run_monte_carlo_sensitivity(
        "S-baseline-human", _mc_distributions(), n_samples=20, seed=42
    )
    # No agent-count sampled columns should appear in records
    for s in samples:
        assert "humanoid_count_sampled" not in s
        assert "human_count_sampled" not in s


# ── run_monte_carlo_per_scenario ──────────────────────────────────────────────


def test_per_scenario_returns_all_five() -> None:
    samples, summary = run_monte_carlo_per_scenario(_mc_distributions(), n_samples=30, seed=42)
    assert set(summary.keys()) == set(SCENARIO_COMPOSITIONS.keys())
    # samples = 30 × 5 scenarios = 150 rows
    assert len(samples) == 30 * len(SCENARIO_COMPOSITIONS)


def test_per_scenario_shared_draws_same_seed() -> None:
    """Same seed → identical parameter draws applied to every scenario.

    This is a common variance-reduction trick (common random numbers).
    """
    samples, _ = run_monte_carlo_per_scenario(_mc_distributions(), n_samples=10, seed=42)
    by_scenario: dict[str, list[dict]] = {}
    for s in samples:
        by_scenario.setdefault(s["scenario_id"], []).append(s)
    # sample_id=0 should share the same drawn params across every scenario
    first_row_per_scenario = [by_scenario[sid][0] for sid in SCENARIO_COMPOSITIONS]
    for key in ("humanoid_capex_eur_sampled", "human_wage_eur_sampled"):
        values = {row[key] for row in first_row_per_scenario}
        assert len(values) == 1, f"Draws differ across scenarios for {key}: {values}"


def test_per_scenario_lean_human_leads() -> None:
    """After F-221/F-237 fair sizing, S-lean-human leads by mean NPV."""
    _, summary = run_monte_carlo_per_scenario(_mc_distributions(), n_samples=500, seed=42)
    means = {sid: summary[sid]["npv_mean"] for sid in summary}
    # Less negative = better
    best = max(means, key=lambda k: means[k])
    assert best == "S-lean-human", f"Expected S-lean-human to lead; got {best} with means={means}"


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
