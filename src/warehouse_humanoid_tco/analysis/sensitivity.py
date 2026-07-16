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
import yaml

from warehouse_humanoid_tco.models.tco import (
    compute_annual_humanoid_opex,
    compute_annual_labor_cost,
    compute_humanoid_capex,
    compute_npv,
)
from warehouse_humanoid_tco.utils.paths import repo_relative


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


def _load_sensitivity_config(project_root: Path) -> dict:
    """Load the `sensitivity` block from config/tco_assumptions.yaml.

    Returns {} if the file or block is absent (callers fall back to literals).
    """
    path = project_root / "config" / "tco_assumptions.yaml"
    if not path.exists():
        return {}
    try:
        cfg = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return {}
    sens = cfg.get("sensitivity")
    return sens if isinstance(sens, dict) else {}


def _load_monte_carlo_seed(project_root: Path, default: int = 42) -> int:
    """Load the canonical TCO sensitivity seed from ``config/seeds.yaml``."""
    path = project_root / "config" / "seeds.yaml"
    if not path.exists():
        return default
    try:
        config = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return default
    monte_carlo = config.get("monte_carlo")
    if not isinstance(monte_carlo, dict):
        return default
    seed = monte_carlo.get("tco_sensitivity_seed")
    return int(seed) if isinstance(seed, int) else default


# Fixed agent composition per scenario. Source: config/autostore_baseline.yaml
# (agent_counts). `throughput_multiplier` mirrors the TCO pipeline's F-034
# adjustment so S-future-2028 (next-gen humanoids 30% faster) is NOT identical
# to S-hybrid-5050 in the Monte-Carlo output (audit Risk #6).
# Counts re-derived under F-237 pick-lines scaling + F-221 fair optimizer.
SCENARIO_COMPOSITIONS: dict[str, dict[str, float]] = {
    "S-baseline-human": {"n_human": 8, "n_humanoid": 0, "n_amr": 0, "throughput_multiplier": 1.0},
    "S-lean-human": {"n_human": 3, "n_humanoid": 0, "n_amr": 0, "throughput_multiplier": 1.0},
    "S-pure-humanoid": {"n_human": 0, "n_humanoid": 11, "n_amr": 0, "throughput_multiplier": 1.0},
    "S-hybrid-5050": {"n_human": 11, "n_humanoid": 11, "n_amr": 0, "throughput_multiplier": 1.0},
    "S-hybrid-amr": {"n_human": 3, "n_humanoid": 11, "n_amr": 4, "throughput_multiplier": 1.0},
    "S-future-2028": {"n_human": 3, "n_humanoid": 9, "n_amr": 0, "throughput_multiplier": 1.30},
}


def compute_tco_for_params(
    n_human: float,
    n_humanoid: float,
    n_amr: float = 0,
    humanoid_capex_eur: float = 120000.0,
    human_wage_eur: float = 18.50,
    human_overhead_mult: float = 1.35,
    discount_rate: float = 0.08,
    transfer_factor: float = TRANSFER_FACTOR_BASELINE,
    throughput_multiplier: float = 1.0,
    years: int = 5,
    operating_days: int = 252,
    shift_hours: float = 8.0,
    humanoid_install_cost_eur: float = 8000.0,
    humanoid_training_cost_eur: float = 5000.0,
    humanoid_maint_fraction: float = 0.08,
    humanoid_energy_kwh_per_shift: float = 8.0,
    humanoid_supervision_ratio: float = 0.10,
    humanoid_availability: float = 40.0 / 40.5 * 4.0 / 5.0,
    annual_wage_growth_rate: float = 0.025,
    humanoid_useful_life_years: float = 7.0,
    humanoid_residual_value_fraction: float = 0.10,
    integration_cost_eur: float = 200000.0,
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
    # Effective humanoid count: at the baseline transfer factor, multiplier = 1.0.
    # transfer_factor must be positive — OAT and MC ranges are bounded at
    # [0.5, 0.9] (see config/autostore_baseline.yaml::capability_transfer), so
    # the previous max(.,0.05) floor was dead defensive code (F-032). Now
    # validated explicitly so a caller passing 0 fails fast with a clear
    # message instead of silently producing infinite leverage.
    if transfer_factor <= 0:
        raise ValueError(
            f"transfer_factor must be positive; got {transfer_factor}. "
            "OAT/MC ranges are [0.5, 0.9]; direct callers must supply > 0."
        )
    transfer_multiplier = TRANSFER_FACTOR_BASELINE / transfer_factor
    eff_humanoid = n_humanoid * transfer_multiplier
    # F-034 parity: a next-gen throughput multiplier means the same throughput
    # needs fewer effective humanoid units (less capex/opex). Mirrors the TCO
    # pipeline so S-future-2028 differs from S-hybrid-5050 under MC (Risk #6).
    if throughput_multiplier > 0:
        eff_humanoid = eff_humanoid / throughput_multiplier
    if humanoid_availability <= 0:
        raise ValueError(f"humanoid_availability must be positive; got {humanoid_availability}")
    eff_humanoid = eff_humanoid / humanoid_availability

    humanoid_capex_total = compute_humanoid_capex(
        eff_humanoid,  # type: ignore[arg-type]
        humanoid_capex_eur,
        humanoid_install_cost_eur,
        humanoid_training_cost_eur,
    )
    amr_capex_total = n_amr * amr_capex_eur
    capex_year0 = humanoid_capex_total + amr_capex_total
    if n_humanoid > 0:
        capex_year0 += integration_cost_eur

    supervision_ftes = humanoid_supervision_ratio * eff_humanoid
    annual_labor_base = compute_annual_labor_cost(
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
        n_amr,  # type: ignore[arg-type]
        amr_capex_eur,
        amr_maint_fraction,
        amr_energy_kwh_per_shift,
        energy_cost_eur_per_kwh,
        operating_days,
    )
    annual_non_labor_opex = annual_humanoid_opex + annual_amr_opex
    annual_opex_by_year = [
        annual_labor_base * (1 + annual_wage_growth_rate) ** year + annual_non_labor_opex
        for year in range(1, years + 1)
    ]
    residual_salvage = (
        eff_humanoid
        * humanoid_capex_eur
        * humanoid_residual_value_fraction
        * max(0.0, (humanoid_useful_life_years - years) / humanoid_useful_life_years)
    )

    cash_flows = [-capex_year0] + [-opex for opex in annual_opex_by_year]
    if years > 0:
        cash_flows[-1] += residual_salvage
    return compute_npv(cash_flows, discount_rate)


def _call_with_params(
    composition: dict[str, float],
    params: dict[str, float],
) -> float:
    """Helper: dispatch a (composition, params) pair into compute_tco_for_params."""
    return compute_tco_for_params(
        n_human=composition["n_human"],
        n_humanoid=composition["n_humanoid"],
        n_amr=composition["n_amr"],
        throughput_multiplier=float(composition.get("throughput_multiplier", 1.0)),
        humanoid_capex_eur=float(params.get("humanoid_capex_eur", 120000.0)),
        human_wage_eur=float(params.get("human_wage_eur", 18.50)),
        human_overhead_mult=float(params.get("human_overhead_mult", 1.35)),
        discount_rate=float(params.get("discount_rate", 0.08)),
        transfer_factor=float(params.get("transfer_factor", TRANSFER_FACTOR_BASELINE)),
        humanoid_supervision_ratio=float(params.get("humanoid_supervision_ratio", 0.10)),
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
    """Draw n_samples from each named distribution.

    Supports three distribution families:
      - ``normal``: rng.normal(mean, std). Allows negative draws — use only
        for parameters whose physical range admits both signs.
      - ``lognormal``: rng.lognormal parameterised to preserve the target
        ``mean`` and ``std`` exactly via sigma^2 = ln(1 + (std/mean)^2),
        mu = ln(mean) - sigma^2/2. Strictly positive — use for parameters
        like capex where negative draws are non-physical (F-031, F-027).
      - ``uniform``: rng.uniform(low, high).
    """
    samples: dict[str, np.ndarray] = {}
    for name, cfg in distributions.items():
        dtype = cfg.get("type", "normal")
        if dtype == "normal":
            samples[name] = rng.normal(cfg["mean"], cfg["std"], n_samples)
        elif dtype == "lognormal":
            mean = float(cfg["mean"])
            std = float(cfg["std"])
            if mean <= 0 or std <= 0:
                raise ValueError(
                    f"lognormal {name!r} requires positive mean and std; "
                    f"got mean={mean}, std={std}"
                )
            cv2 = (std / mean) ** 2
            sigma2 = float(np.log1p(cv2))
            mu = float(np.log(mean)) - 0.5 * sigma2
            samples[name] = rng.lognormal(mu, np.sqrt(sigma2), n_samples)
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


def _rank_probabilities(
    samples: list[dict],
    scenario_ids: list[str],
    n_samples: int,
) -> tuple[dict[str, float], int]:
    """Return P(rank 1) and the count of unusable paired CRN draws.

    A sample is feasible only when every scenario has one finite NPV. Ties use
    the supplied scenario order, making the winner deterministic and keeping
    the probabilities a proper distribution.
    """
    by_sample: dict[int, dict[str, float]] = {}
    for row in samples:
        sample_id = int(row["sample_id"])
        by_sample.setdefault(sample_id, {})[str(row["scenario_id"])] = float(row["npv_eur"])

    wins = dict.fromkeys(scenario_ids, 0)
    feasible_count = 0
    for sample_id in range(n_samples):
        npvs = by_sample.get(sample_id, {})
        if (
            len(npvs) != len(scenario_ids)
            or any(scenario_id not in npvs for scenario_id in scenario_ids)
            or any(not np.isfinite(npvs[scenario_id]) for scenario_id in scenario_ids)
        ):
            continue
        winner = max(scenario_ids, key=lambda scenario_id: npvs[scenario_id])
        wins[winner] += 1
        feasible_count += 1

    if feasible_count == 0:
        return {scenario_id: 0.0 for scenario_id in scenario_ids}, n_samples
    return (
        {scenario_id: wins[scenario_id] / feasible_count for scenario_id in scenario_ids},
        n_samples - feasible_count,
    )


def compute_evpi_per_parameter(
    samples: list[dict[str, Any]],
    scenario_ids: list[str],
    parameter_names: list[str],
    *,
    n_bins: int = 20,
) -> dict[str, float]:
    """Estimate partial EVPI from common-random-number Monte Carlo samples.

    For each input X, the estimator is ``E[max_s E(NPV_s | X)] - max_s E(NPV_s)``.
    It uses equal-frequency bins as a non-parametric conditional-mean estimator.
    Every scenario shares a parameter draw for a sample id, so differences are
    attributable to the parameter rather than independently sampled noise.
    """
    if n_bins < 2:
        raise ValueError("n_bins must be at least 2")

    rows_by_sample: dict[int, dict[str, dict[str, Any]]] = {}
    for row in samples:
        sample_id = int(row["sample_id"])
        rows_by_sample.setdefault(sample_id, {})[str(row["scenario_id"])] = row
    complete = [
        scenario_rows
        for scenario_rows in rows_by_sample.values()
        if all(scenario_id in scenario_rows for scenario_id in scenario_ids)
    ]
    if not complete:
        return {name: 0.0 for name in parameter_names}

    scenario_means = {
        scenario_id: float(np.mean([float(rows[scenario_id]["npv_eur"]) for rows in complete]))
        for scenario_id in scenario_ids
    }
    current_value = max(scenario_means.values())
    evpi: dict[str, float] = {}
    for parameter in parameter_names:
        sample_key = f"{parameter}_sampled"
        values = np.asarray([float(rows[scenario_ids[0]][sample_key]) for rows in complete])
        # Stable rank bins avoid distribution-specific assumptions and ensure
        # non-empty conditioning cells even for repeated uniform draws.
        ranks = np.argsort(np.argsort(values, kind="stable"), kind="stable")
        bins = np.minimum((ranks * n_bins) // len(complete), n_bins - 1)
        conditional_value = 0.0
        for bin_id in range(n_bins):
            indices = np.flatnonzero(bins == bin_id)
            if not len(indices):
                continue
            conditional_value += (
                len(indices)
                / len(complete)
                * max(
                    float(
                        np.mean(
                            [float(complete[index][scenario_id]["npv_eur"]) for index in indices]
                        )
                    )
                    for scenario_id in scenario_ids
                )
            )
        # Sampling noise can make an otherwise non-negative value infinitesimally
        # negative; zero is the economically meaningful lower bound.
        evpi[parameter] = float(max(0.0, conditional_value - current_value))
    return evpi


def _convergence_diagnostic(npv_array: np.ndarray) -> dict[str, float]:
    """Compare first- and second-half means for a lightweight MC stability check."""
    midpoint = len(npv_array) // 2
    if midpoint == 0 or midpoint == len(npv_array):
        raise ValueError("convergence diagnostic requires at least two samples")
    half1_mean = float(np.mean(npv_array[:midpoint]))
    half2_mean = float(np.mean(npv_array[midpoint:]))
    rel_delta = abs(half1_mean - half2_mean) / max(abs((half1_mean + half2_mean) / 2), 1.0)
    return {
        "half1_mean": half1_mean,
        "half2_mean": half2_mean,
        "rel_delta": float(rel_delta),
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
    """Run Monte Carlo for every scenario, reusing one parameter draw matrix.

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
    scenario_id: str = "S-lean-human",
    n_mc_samples: int = 10000,
) -> dict[str, Path]:
    """Run full sensitivity analysis.

    OAT runs against `scenario_id` (default S-lean-human — the recommended scenario).
    Monte Carlo runs per-scenario across all published scenarios.

    Returns dict mapping output paths.
    """
    data_processed = project_root / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)

    print("[Sensitivity] Running OAT + Monte Carlo analysis...")

    # Base point, OAT ranges, and MC distributions are read from
    # config/tco_assumptions.yaml::sensitivity (audit Risk #18 — the config is
    # now the source of truth, not decorative). The literals below are last-resort
    # fallbacks only, equal to the config values, for configs lacking the block.
    sens_cfg = _load_sensitivity_config(project_root)

    base_params = sens_cfg.get("base_point") or {
        "humanoid_capex_eur": 120000.0,
        "human_wage_eur": 18.50,
        "human_overhead_mult": 1.35,
        "discount_rate": 0.08,
        "transfer_factor": TRANSFER_FACTOR_BASELINE,
        "humanoid_supervision_ratio": 0.10,
    }

    oat_cfg = sens_cfg.get("oat") or {
        "humanoid_capex_eur": [60000, 180000],
        "human_wage_eur": [15.13, 22.00],
        "human_overhead_mult": [1.0, 1.7],
        "discount_rate": [0.04, 0.12],
        "transfer_factor": [0.50, 0.90],
        "humanoid_supervision_ratio": [0.05, 0.50],
    }
    param_ranges: dict[str, tuple[float, float]] = {
        k: (float(v[0]), float(v[1])) for k, v in oat_cfg.items()
    }

    # MC distributions — continuous parameters only (agent counts fixed per
    # scenario). humanoid_capex_eur uses lognormal (F-031): strictly positive,
    # right-skewed, preserving the target mean/std exactly. See _sample_params.
    param_distributions: dict[str, dict] = sens_cfg.get("monte_carlo") or {
        "humanoid_capex_eur": {"type": "lognormal", "mean": 120000, "std": 30000},
        "human_wage_eur": {"type": "normal", "mean": 18.50, "std": 2.0},
        "human_overhead_mult": {"type": "uniform", "low": 1.0, "high": 1.7},
        "discount_rate": {"type": "uniform", "low": 0.04, "high": 0.12},
        "transfer_factor": {"type": "uniform", "low": 0.50, "high": 0.90},
        "humanoid_supervision_ratio": {"type": "uniform", "low": 0.05, "high": 0.50},
    }

    print(f"  OAT sensitivity ({scenario_id}, {len(param_ranges)} parameters)...")
    oat_results = run_oat_sensitivity(scenario_id, base_params, param_ranges, n_steps=11)
    elasticity_ranking = compute_elasticity_ranking(oat_results)

    print(f"  Monte Carlo: {n_mc_samples} samples × {len(SCENARIO_COMPOSITIONS)} scenarios...")
    mc_samples, mc_summary_per_scenario = run_monte_carlo_per_scenario(
        param_distributions,
        n_samples=n_mc_samples,
        seed=_load_monte_carlo_seed(project_root),
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
    scenario_ids = list(SCENARIO_COMPOSITIONS)
    rank_probabilities, infeasible_sample_count = _rank_probabilities(
        mc_samples, scenario_ids, n_mc_samples
    )
    evpi_eur = compute_evpi_per_parameter(mc_samples, scenario_ids, list(param_distributions))
    leading_npvs = np.asarray(
        [sample["npv_eur"] for sample in mc_samples if sample["scenario_id"] == scenario_id],
        dtype=float,
    )

    report = {
        "phase": "sensitivity_analysis",
        "scenario_id": scenario_id,
        "oat_parameters": list(param_ranges.keys()),
        "oat_parameter_ranges": {k: list(v) for k, v in param_ranges.items()},
        "oat_elasticity_ranking": elasticity_ranking,
        "mc_param_distributions": param_distributions,
        "mc_samples": n_mc_samples,
        "oat_results_path": repo_relative(oat_path),
        "mc_samples_path": repo_relative(mc_path),
        "mc_summary": leading_summary,
        "mc_summary_per_scenario": mc_summary_per_scenario,
        "rank_probabilities": rank_probabilities,
        "evpi_eur": evpi_eur,
        "convergence": _convergence_diagnostic(leading_npvs),
        "infeasible_sample_count": infeasible_sample_count,
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
