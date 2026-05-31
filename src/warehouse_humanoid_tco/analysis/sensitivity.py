"""Sensitivity Analysis: OAT + Monte Carlo for TCO parameters.

Implements:
1. One-at-a-time (OAT) sensitivity for the S-hybrid-amr scenario.
2. Monte Carlo (10,000 runs) per scenario with agent counts fixed; samples only
   continuous parameters (wage, overhead, capex, discount rate, transfer factor).
3. Results export to parquet (all samples) + JSON report (per-scenario summary).

Per audit T0.2/T0.3/T0.5 (2026-05-27): MC must not vary agent counts (that
collapses scenario identity); the WBT→production transfer factor is the
single largest methodological assumption and must be sampled.

See PROJECT_CHARTER.md §7.4 and §7.6 for spec.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from warehouse_humanoid_tco.models.tco import (
    compute_annual_humanoid_opex,
    compute_annual_labor_cost,
    compute_humanoid_capex,
    compute_npv,
)


def one_at_a_time(
    base_params: dict[str, float],
    param_ranges: dict[str, tuple[float, float]],
    model_fn: Callable[..., float],
    *,
    n_steps: int = 20,
) -> pl.DataFrame:
    """OAT sensitivity: vary each parameter across its range, hold others at base.

    Returns a DataFrame with columns: parameter, value, output, delta_vs_base.
    Generic primitive — for TCO-specific OAT see `run_oat_sensitivity` below.
    """
    records: list[dict[str, Any]] = []
    base_output = model_fn(**base_params)

    for param_name, (low, high) in param_ranges.items():
        for value in np.linspace(low, high, n_steps):
            params = {**base_params, param_name: float(value)}
            output = model_fn(**params)
            records.append(
                {
                    "parameter": param_name,
                    "value": float(value),
                    "output": output,
                    "delta_vs_base": output - base_output,
                }
            )

    return pl.DataFrame(records)


def monte_carlo(
    base_params: dict[str, float],
    param_distributions: dict[str, tuple[float, float]],
    model_fn: Callable[..., float],
    n_runs: int = 10_000,
    seed: int = 200,
) -> pl.DataFrame:
    """Monte Carlo simulation: sample all parameters simultaneously.

    param_distributions: {param_name: (low, high)} — uniform sampling.
    Generic primitive — for TCO-specific MC see `run_monte_carlo_per_scenario`.
    """
    rng = np.random.default_rng(seed)
    records: list[dict[str, Any]] = []

    for run_id in range(n_runs):
        params = {**base_params}
        for param_name, (low, high) in param_distributions.items():
            params[param_name] = float(rng.uniform(low, high))
        output = model_fn(**params)
        records.append({"run_id": run_id, "output": output, **params})

    return pl.DataFrame(records)


TRANSFER_FACTOR_BASELINE = 0.70  # See config/autostore_baseline.yaml::capability_transfer

# Fixed agent composition per scenario (total_agents=8). Source: config/autostore_baseline.yaml
SCENARIO_COMPOSITIONS: dict[str, dict[str, int]] = {
    "S-baseline-human": {"n_human": 8, "n_humanoid": 0, "n_amr": 0},
    "S-pure-humanoid": {"n_human": 0, "n_humanoid": 8, "n_amr": 0},
    "S-hybrid-5050": {"n_human": 4, "n_humanoid": 4, "n_amr": 0},
    "S-hybrid-amr": {"n_human": 4, "n_humanoid": 1, "n_amr": 1},
    "S-future-2028": {"n_human": 4, "n_humanoid": 4, "n_amr": 0},
}


def compute_tco_for_params(
    n_human: int,
    n_humanoid: int,
    n_amr: int = 0,
    humanoid_capex_eur: float = 120000.0,
    human_wage_eur: float = 18.50,
    human_overhead_mult: float = 1.35,
    discount_rate: float = 0.08,
    transfer_factor: float = TRANSFER_FACTOR_BASELINE,
    years: int = 5,
    operating_days: int = 252,
    shift_hours: float = 8.0,
    humanoid_install_cost_eur: float = 8000.0,
    humanoid_training_cost_eur: float = 5000.0,
    humanoid_maint_fraction: float = 0.08,
    humanoid_energy_kwh_per_shift: float = 8.0,
    humanoid_supervision_ratio: float = 0.10,
    amr_capex_eur: float = 65000.0,
    amr_maint_fraction: float = 0.06,
    amr_energy_kwh_per_shift: float = 4.0,
    energy_cost_eur_per_kwh: float = 0.22,
) -> float:
    """5-year NPV for fixed agent composition + continuous parameters.

    Mirrors `pipelines.module_03_tco.compute_tco_scenario` but takes raw counts.
    The transfer factor models WBT-to-production capability shortfall: lower
    transfer means each humanoid does less productive work, so more effective
    units (capex + opex) are needed to match the demo-speed baseline.
    """
    # Effective humanoid count: at the baseline transfer factor, multiplier = 1.0
    transfer_multiplier = TRANSFER_FACTOR_BASELINE / max(transfer_factor, 0.05)
    eff_humanoid = n_humanoid * transfer_multiplier

    humanoid_capex_total = compute_humanoid_capex(
        eff_humanoid,  # type: ignore[arg-type]
        humanoid_capex_eur,
        humanoid_install_cost_eur,
        humanoid_training_cost_eur,
    )
    amr_capex_total = n_amr * amr_capex_eur
    capex_year0 = humanoid_capex_total + amr_capex_total

    supervision_ftes = humanoid_supervision_ratio * eff_humanoid
    annual_labor = compute_annual_labor_cost(
        n_human + supervision_ftes,  # type: ignore[arg-type]
        human_wage_eur,
        human_overhead_mult,
        operating_days,
        shift_hours,
    )
    annual_humanoid_opex = compute_annual_humanoid_opex(
        eff_humanoid,  # type: ignore[arg-type]
        humanoid_capex_eur,
        humanoid_maint_fraction,
        humanoid_energy_kwh_per_shift,
        energy_cost_eur_per_kwh,
        operating_days,
    )
    annual_amr_opex = compute_annual_humanoid_opex(
        n_amr,
        amr_capex_eur,
        amr_maint_fraction,
        amr_energy_kwh_per_shift,
        energy_cost_eur_per_kwh,
        operating_days,
    )
    annual_opex = annual_labor + annual_humanoid_opex + annual_amr_opex

    cash_flows = [-capex_year0] + [-annual_opex] * years
    return compute_npv(cash_flows, discount_rate)


def _call_with_params(
    composition: dict[str, int],
    params: dict[str, float],
) -> float:
    """Helper: dispatch a (composition, params) pair into compute_tco_for_params."""
    return compute_tco_for_params(
        n_human=composition["n_human"],
        n_humanoid=composition["n_humanoid"],
        n_amr=composition["n_amr"],
        humanoid_capex_eur=float(params.get("humanoid_capex_eur", 120000.0)),
        human_wage_eur=float(params.get("human_wage_eur", 18.50)),
        human_overhead_mult=float(params.get("human_overhead_mult", 1.35)),
        discount_rate=float(params.get("discount_rate", 0.08)),
        transfer_factor=float(params.get("transfer_factor", TRANSFER_FACTOR_BASELINE)),
    )


def run_oat_sensitivity(
    scenario_id: str,
    base_params: dict,
    param_ranges: dict[str, tuple[float, float]],
    n_steps: int = 11,
) -> list[dict]:
    """One-at-a-time sensitivity for a fixed-composition scenario.

    Varies each continuous parameter across `n_steps` values; agent counts are
    pinned to the scenario's composition. Each result row carries both the raw
    `delta_vs_base` (NPV - NPV_base) and a `normalised_elasticity`
    (= percent change in NPV divided by percent change in the parameter).
    Tornado rankings should be derived from elasticity, not raw delta, because
    raw delta is a pure function of the chosen parameter range (F-030).
    """
    composition = SCENARIO_COMPOSITIONS[scenario_id]
    base_npv = _call_with_params(composition, base_params)
    results: list[dict] = []

    for param_name, (min_val, max_val) in param_ranges.items():
        base_value = float(base_params[param_name])
        param_values = np.linspace(min_val, max_val, n_steps)
        for param_val in param_values:
            test_params = base_params.copy()
            test_params[param_name] = float(param_val)
            npv = _call_with_params(composition, test_params)
            results.append(
                {
                    "scenario_id": scenario_id,
                    "parameter": param_name,
                    "parameter_value": float(param_val),
                    "npv_eur": float(npv),
                    "delta_vs_base": float(npv - base_npv),
                    "normalised_elasticity": _elasticity(
                        npv, base_npv, float(param_val), base_value
                    ),
                }
            )

    return results


def _elasticity(output: float, base_output: float, param: float, base_param: float) -> float:
    """Compute normalised elasticity = (Δoutput / output) / (Δparam / param).

    Returns 0.0 at the base point (where Δparam = 0). NaN-safe: zero base
    output collapses the percent change in the denominator; in that case we
    fall back to absolute fractional change ``Δoutput / Δparam`` scaled by
    ``base_param`` so the magnitude still ranks parameters monotonically.
    """
    if param == base_param:
        return 0.0
    pct_param = (param - base_param) / base_param if base_param != 0 else 0.0
    if pct_param == 0.0:
        return 0.0
    if base_output == 0:
        return float((output - base_output) * base_param / (param - base_param))
    pct_output = (output - base_output) / abs(base_output)
    return float(pct_output / pct_param)


def compute_elasticity_ranking(oat_results: list[dict]) -> list[dict]:
    """Rank parameters by maximum |normalised_elasticity| across the OAT sweep.

    Returns a list sorted descending by `peak_elasticity`. Each row also reports
    `peak_delta_vs_base_eur` so consumers can render both the rank-driver
    (elasticity, range-independent) and the dollar magnitude (delta, range-
    dependent) — but the ranking is always driven by elasticity per F-030.
    """
    by_param: dict[str, list[dict]] = {}
    for row in oat_results:
        by_param.setdefault(row["parameter"], []).append(row)

    ranking: list[dict] = []
    for param_name, rows in by_param.items():
        peak_elasticity = max(abs(r["normalised_elasticity"]) for r in rows)
        peak_delta = max(abs(r["delta_vs_base"]) for r in rows)
        ranking.append(
            {
                "parameter": param_name,
                "peak_elasticity": float(peak_elasticity),
                "peak_delta_vs_base_eur": float(peak_delta),
            }
        )
    ranking.sort(key=lambda r: r["peak_elasticity"], reverse=True)
    return ranking


def _sample_params(
    rng: np.random.Generator,
    distributions: dict[str, dict],
    n_samples: int,
) -> dict[str, np.ndarray]:
    """Draw n_samples from each named distribution."""
    samples: dict[str, np.ndarray] = {}
    for name, cfg in distributions.items():
        dtype = cfg.get("type", "normal")
        if dtype == "normal":
            samples[name] = rng.normal(cfg["mean"], cfg["std"], n_samples)
        elif dtype == "uniform":
            samples[name] = rng.uniform(cfg["low"], cfg["high"], n_samples)
        else:
            raise ValueError(f"Unsupported distribution type: {dtype!r} for {name}")
    return samples


def _summarize(npv_array: np.ndarray, n_samples: int) -> dict[str, float]:
    return {
        "n_samples": n_samples,
        "npv_mean": float(np.mean(npv_array)),
        "npv_std": float(np.std(npv_array)),
        "npv_min": float(np.min(npv_array)),
        "npv_max": float(np.max(npv_array)),
        "npv_p5": float(np.percentile(npv_array, 5)),
        "npv_p25": float(np.percentile(npv_array, 25)),
        "npv_p50": float(np.percentile(npv_array, 50)),
        "npv_p75": float(np.percentile(npv_array, 75)),
        "npv_p95": float(np.percentile(npv_array, 95)),
    }


def run_monte_carlo_sensitivity(
    scenario_id: str,
    param_distributions: dict[str, dict],
    n_samples: int = 10000,
    seed: int = 42,
) -> tuple[list[dict], dict]:
    """Monte Carlo for a single scenario with agent counts fixed.

    Only continuous parameters are sampled (wage, overhead, capex, discount
    rate, transfer factor). Agent counts come from SCENARIO_COMPOSITIONS.
    """
    composition = SCENARIO_COMPOSITIONS[scenario_id]
    rng = np.random.default_rng(seed)
    drawn = _sample_params(rng, param_distributions, n_samples)

    samples: list[dict] = []
    npv_array = np.empty(n_samples)

    for i in range(n_samples):
        params = {name: float(drawn[name][i]) for name in drawn}
        npv = _call_with_params(composition, params)
        npv_array[i] = npv
        samples.append(
            {
                "sample_id": i,
                "scenario_id": scenario_id,
                "npv_eur": float(npv),
                **{f"{k}_sampled": float(drawn[k][i]) for k in drawn},
            }
        )

    summary = _summarize(npv_array, n_samples)
    return samples, summary


def run_monte_carlo_per_scenario(
    param_distributions: dict[str, dict],
    n_samples: int = 10000,
    seed: int = 42,
    scenario_ids: list[str] | None = None,
) -> tuple[list[dict], dict[str, dict]]:
    """Run Monte Carlo for every scenario, reusing the same parameter draws.

    Same continuous draws are applied to every scenario so cross-scenario
    NPV comparisons hold parameter noise constant — a standard variance-
    reduction trick.
    """
    if scenario_ids is None:
        scenario_ids = list(SCENARIO_COMPOSITIONS.keys())

    rng = np.random.default_rng(seed)
    drawn = _sample_params(rng, param_distributions, n_samples)

    all_samples: list[dict] = []
    per_scenario_summary: dict[str, dict] = {}

    for scenario_id in scenario_ids:
        composition = SCENARIO_COMPOSITIONS[scenario_id]
        npv_array = np.empty(n_samples)

        for i in range(n_samples):
            params = {name: float(drawn[name][i]) for name in drawn}
            npv = _call_with_params(composition, params)
            npv_array[i] = npv
            all_samples.append(
                {
                    "sample_id": i,
                    "scenario_id": scenario_id,
                    "npv_eur": float(npv),
                    **{f"{k}_sampled": float(drawn[k][i]) for k in drawn},
                }
            )

        per_scenario_summary[scenario_id] = _summarize(npv_array, n_samples)

    return all_samples, per_scenario_summary


def run_sensitivity_analysis(
    project_root: Path,
    scenario_id: str = "S-hybrid-amr",
    n_mc_samples: int = 10000,
) -> dict[str, Path]:
    """Run full sensitivity analysis.

    OAT runs against `scenario_id` (default S-hybrid-amr — the leading scenario).
    Monte Carlo runs per-scenario across all five scenarios.

    Returns dict mapping output paths.
    """
    data_processed = project_root / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)

    print("[Sensitivity] Running OAT + Monte Carlo analysis...")

    # Base parameter point estimates (used as OAT pivot)
    base_params = {
        "humanoid_capex_eur": 120000.0,
        "human_wage_eur": 18.50,
        "human_overhead_mult": 1.35,
        "discount_rate": 0.08,
        "transfer_factor": TRANSFER_FACTOR_BASELINE,
    }

    # OAT parameter ranges. Wage range is the actual WKO Spedition & Lagereibetriebe
    # collective agreement bracket (BG-III 2025/26) — see config/tco_assumptions.yaml.
    # Other ranges are documented stress-test bands around the point estimates.
    param_ranges: dict[str, tuple[float, float]] = {
        "humanoid_capex_eur": (60000, 180000),
        "human_wage_eur": (15.13, 22.00),
        "human_overhead_mult": (1.0, 1.7),
        "discount_rate": (0.04, 0.12),
        "transfer_factor": (0.50, 0.90),
    }

    # MC distributions — continuous parameters only (agent counts fixed per scenario)
    param_distributions: dict[str, dict] = {
        "humanoid_capex_eur": {"type": "normal", "mean": 120000, "std": 30000},
        "human_wage_eur": {"type": "normal", "mean": 18.50, "std": 2.0},
        "human_overhead_mult": {"type": "uniform", "low": 1.0, "high": 1.7},
        "discount_rate": {"type": "uniform", "low": 0.04, "high": 0.12},
        "transfer_factor": {"type": "uniform", "low": 0.50, "high": 0.90},
    }

    print(f"  OAT sensitivity ({scenario_id}, {len(param_ranges)} parameters)...")
    oat_results = run_oat_sensitivity(scenario_id, base_params, param_ranges, n_steps=11)
    elasticity_ranking = compute_elasticity_ranking(oat_results)

    print(f"  Monte Carlo: {n_mc_samples} samples × {len(SCENARIO_COMPOSITIONS)} scenarios...")
    mc_samples, mc_summary_per_scenario = run_monte_carlo_per_scenario(
        param_distributions, n_samples=n_mc_samples
    )

    # Persist OAT (small, full)
    oat_df = pl.DataFrame(oat_results)
    oat_path = data_processed / "sensitivity_oat_results.parquet"
    oat_df.write_parquet(oat_path)
    print(f"  ✓ OAT: {oat_path}")

    # Persist ALL MC samples (per audit T0.3 — no subsampling)
    mc_df = pl.DataFrame(mc_samples)
    mc_path = data_processed / "sensitivity_mc_samples.parquet"
    mc_df.write_parquet(mc_path)
    print(f"  ✓ MC samples (full {len(mc_samples)} rows): {mc_path}")

    # Leading scenario summary surfaces at top level for README/report consumers
    leading_summary = mc_summary_per_scenario.get(scenario_id, {})

    report = {
        "phase": "sensitivity_analysis",
        "scenario_id": scenario_id,
        "oat_parameters": list(param_ranges.keys()),
        "oat_parameter_ranges": {k: list(v) for k, v in param_ranges.items()},
        "oat_elasticity_ranking": elasticity_ranking,
        "mc_param_distributions": param_distributions,
        "mc_samples": n_mc_samples,
        "oat_results_path": str(oat_path),
        "mc_samples_path": str(mc_path),
        "mc_summary": leading_summary,
        "mc_summary_per_scenario": mc_summary_per_scenario,
    }

    report_path = project_root / "reports" / "sensitivity_analysis_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"  ✓ Report: {report_path}")
    if leading_summary:
        print(
            f"\n  MC Summary ({scenario_id}): "
            f"NPV = €{leading_summary['npv_mean']:.0f} ± €{leading_summary['npv_std']:.0f}"
        )
        print(
            f"    90% output interval (p5–p95): €{leading_summary['npv_p5']:.0f} "
            f"to €{leading_summary['npv_p95']:.0f}"
        )

    return {
        "oat_results": oat_path,
        "mc_samples": mc_path,
        "report": report_path,
    }


if __name__ == "__main__":
    import sys

    project_root = Path(__file__).parent.parent.parent.parent

    try:
        paths = run_sensitivity_analysis(project_root, n_mc_samples=10000)
        print(f"\n✓ Success. Outputs: {paths}")
    except Exception as e:
        print(f"\n✗ Failed: {e}", file=sys.stderr)
        sys.exit(1)
