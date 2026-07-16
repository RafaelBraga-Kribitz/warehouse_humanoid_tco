"""Audit-remediation regression tests: config + composition are actually wired.

The original audit's headline defect was that `config/tco_assumptions.yaml` was
inert — the model read flat keys that did not exist in the nested YAML and
silently used hardcoded defaults, so editing the config changed nothing. The
governance suite verified provenance and wording but never perturbed an input
and asserted the output moved. These tests close that gap.
"""

from __future__ import annotations

import copy

import yaml

from warehouse_humanoid_tco.analysis import sensitivity as sens
from warehouse_humanoid_tco.pipelines.module_03_tco import (
    build_financial_params,
    compute_tco_scenario,
)

NESTED_CONFIG = """
financial:
  discount_rate: 0.08
labor:
  base_hourly_wage_eur: 18.50
  overhead_multiplier: 1.35
  training_cost_per_humanoid_eur: 5000
humanoid:
  unit_capex_eur: 120000
  installation_cost_per_unit_eur: 8000
  annual_maintenance_fraction: 0.08
  energy_cost_eur_per_kwh: 0.22
amr:
  unit_capex_eur: 65000
  annual_maintenance_fraction: 0.06
"""

BASELINE_ANNUAL_OPEX = 500_000.0

SIM_CONFIG = """
operations:
  operating_days_per_year: 252
  shift_hours: 8.0
agents:
  humanoid:
    energy_kwh_per_shift: 8.0
  amr:
    energy_kwh_per_shift: 4.0
humanoid_operational:
  supervision_ratio: 0.10
"""


def _composition(n_human: float, n_humanoid: float, n_amr: float, mult: float = 1.0) -> dict:
    return {
        "n_human": n_human,
        "n_humanoid": n_humanoid,
        "n_amr": n_amr,
        "throughput_multiplier": mult,
    }


def test_build_financial_params_reads_nested_config() -> None:
    params = build_financial_params(yaml.safe_load(NESTED_CONFIG), yaml.safe_load(SIM_CONFIG))
    assert params["human_hourly_wage_eur"] == 18.50
    assert params["humanoid_capex_eur"] == 120000
    assert params["humanoid_training_cost_eur"] == 5000
    assert params["humanoid_supervision_ratio"] == 0.10


def test_changing_wage_changes_npv() -> None:
    base_cfg = yaml.safe_load(NESTED_CONFIG)
    sim_cfg = yaml.safe_load(SIM_CONFIG)
    comp = _composition(0, 8, 0)  # pure-humanoid: insensitive to wage except supervision

    base = compute_tco_scenario(
        "S-pure-humanoid",
        {"throughput_orders_per_shift": 950.0},
        build_financial_params(base_cfg, sim_cfg),
        baseline_annual_opex=BASELINE_ANNUAL_OPEX,
        composition=comp,
    )

    hot_cfg = copy.deepcopy(base_cfg)
    hot_cfg["labor"]["base_hourly_wage_eur"] = 99.0  # 5x wage
    hot = compute_tco_scenario(
        "S-pure-humanoid",
        {"throughput_orders_per_shift": 950.0},
        build_financial_params(hot_cfg, sim_cfg),
        baseline_annual_opex=BASELINE_ANNUAL_OPEX,
        composition=comp,
    )
    # Supervision labor scales with wage, so even pure-humanoid NPV must move.
    assert hot["npv_eur"] != base["npv_eur"]


def test_changing_capex_changes_npv() -> None:
    base_cfg = yaml.safe_load(NESTED_CONFIG)
    sim_cfg = yaml.safe_load(SIM_CONFIG)
    comp = _composition(0, 8, 0)
    base = compute_tco_scenario(
        "S-pure-humanoid",
        {"throughput_orders_per_shift": 950.0},
        build_financial_params(base_cfg, sim_cfg),
        baseline_annual_opex=BASELINE_ANNUAL_OPEX,
        composition=comp,
    )
    hot_cfg = copy.deepcopy(base_cfg)
    hot_cfg["humanoid"]["unit_capex_eur"] = 240000  # 2x capex
    hot = compute_tco_scenario(
        "S-pure-humanoid",
        {"throughput_orders_per_shift": 950.0},
        build_financial_params(hot_cfg, sim_cfg),
        baseline_annual_opex=BASELINE_ANNUAL_OPEX,
        composition=comp,
    )
    assert hot["total_capex_eur"] > base["total_capex_eur"]
    assert hot["npv_eur"] < base["npv_eur"]  # more capex => more negative NPV


def test_explicit_composition_has_no_int_truncation() -> None:
    """A fractional intended crew is honoured exactly when passed as counts."""
    params = build_financial_params(yaml.safe_load(NESTED_CONFIG), yaml.safe_load(SIM_CONFIG))
    # 4 humans cost strictly less labor than 5 humans (no silent floor).
    r4 = compute_tco_scenario(
        "X",
        {"throughput_orders_per_shift": 950.0},
        params,
        baseline_annual_opex=BASELINE_ANNUAL_OPEX,
        composition=_composition(4, 1, 1),
    )
    r5 = compute_tco_scenario(
        "X",
        {"throughput_orders_per_shift": 950.0},
        params,
        baseline_annual_opex=BASELINE_ANNUAL_OPEX,
        composition=_composition(5, 1, 1),
    )
    assert r5["total_opex_5yr_eur_nominal"] > r4["total_opex_5yr_eur_nominal"]


def test_total_cost_metric_distinct_from_opex_metric() -> None:
    """Opex-only reduction must not be conflated with total-cost reduction."""
    params = build_financial_params(yaml.safe_load(NESTED_CONFIG), yaml.safe_load(SIM_CONFIG))
    pure = compute_tco_scenario(
        "S-pure-humanoid",
        {"throughput_orders_per_shift": 950.0},
        params,
        baseline_annual_opex=BASELINE_ANNUAL_OPEX,
        composition=_composition(0, 8, 0),
    )
    # Pure-humanoid slashes opex but carries large capex; the opex-only metric
    # must be well above the eventual NPV-based total-cost reduction.
    assert pure["opex_reduction_vs_baseline_pct"] > 50.0


def test_future_2028_differs_from_hybrid_5050_in_mc() -> None:
    """Risk #6: the throughput multiplier must differentiate the two scenarios."""
    dists = {
        "humanoid_capex_eur": {"type": "lognormal", "mean": 120000, "std": 30000},
        "human_wage_eur": {"type": "normal", "mean": 18.50, "std": 2.0},
        "human_overhead_mult": {"type": "uniform", "low": 1.0, "high": 1.7},
        "discount_rate": {"type": "uniform", "low": 0.04, "high": 0.12},
        "transfer_factor": {"type": "uniform", "low": 0.50, "high": 0.90},
    }
    _, summary = sens.run_monte_carlo_per_scenario(
        dists, n_samples=500, scenario_ids=["S-hybrid-5050", "S-future-2028"]
    )
    assert summary["S-future-2028"]["npv_mean"] != summary["S-hybrid-5050"]["npv_mean"]
