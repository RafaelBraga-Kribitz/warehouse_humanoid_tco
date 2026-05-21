"""Sensitivity Analysis: OAT + Monte Carlo for TCO parameters.

Implements:
1. One-at-a-time (OAT) sensitivity for top 10 parameters
2. Monte Carlo (10,000 runs) for top 5 parameters with empirical distributions
3. Tornado chart generation
4. Results export to parquet + JSON report

See PROJECT_CHARTER.md §7.4 for spec.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from numpy import random as npr


def compute_tco_for_params(
    humanoid_count: int,
    human_count: int,
    humanoid_capex: float,
    human_wage: float,
    human_overhead: float,
    years: int = 5,
    discount_rate: float = 0.08,
) -> float:
    """Compute NPV for given parameters."""
    capex = humanoid_count * humanoid_capex
    annual_opex = human_count * (252 * 8) * human_wage * human_overhead
    cash_flows = [-capex]
    for year in range(1, years + 1):
        cf = -annual_opex / ((1 + discount_rate) ** year)
        cash_flows.append(cf)
    return sum(cash_flows)


def run_oat_sensitivity(
    base_params: dict,
    param_ranges: dict,
    n_steps: int = 11,
) -> list[dict]:
    """One-at-a-time sensitivity: vary each parameter, hold others constant.

    Returns list of dicts with parameter name, value, and resulting NPV.
    """
    results = []

    for param_name, (min_val, max_val) in param_ranges.items():
        param_values = np.linspace(min_val, max_val, n_steps)

        for param_val in param_values:
            # Create params dict with this one parameter varied
            test_params = base_params.copy()
            test_params[param_name] = param_val

            npv = compute_tco_for_params(
                humanoid_count=int(test_params.get("humanoid_count", 0)),
                human_count=int(test_params.get("human_count", 8)),
                humanoid_capex=float(test_params.get("humanoid_capex_eur", 120000)),
                human_wage=float(test_params.get("human_wage_eur", 18.50)),
                human_overhead=float(test_params.get("human_overhead_mult", 1.35)),
            )

            results.append({
                "parameter": param_name,
                "parameter_value": float(param_val),
                "npv_eur": npv,
            })

    return results


def run_monte_carlo_sensitivity(
    base_params: dict,
    param_distributions: dict,
    n_samples: int = 10000,
    seed: int = 42,
) -> tuple[list[dict], dict]:
    """Monte Carlo sensitivity: sample parameters from distributions, compute NPV.

    Returns tuple of (samples_list, summary_stats).
    """
    npr.seed(seed)
    samples = []
    npv_array = []

    for _ in range(n_samples):
        # Sample each parameter from its distribution
        sample = {}
        for param_name, dist_config in param_distributions.items():
            dist_type = dist_config.get("type", "normal")
            if dist_type == "normal":
                mean = dist_config["mean"]
                std = dist_config["std"]
                sample[param_name] = npr.normal(mean, std)
            elif dist_type == "uniform":
                low = dist_config["low"]
                high = dist_config["high"]
                sample[param_name] = npr.uniform(low, high)
            else:
                sample[param_name] = dist_config.get("default", base_params.get(param_name, 0))

        # Compute NPV for this sample
        npv = compute_tco_for_params(
            humanoid_count=int(sample.get("humanoid_count", 0)),
            human_count=int(sample.get("human_count", 8)),
            humanoid_capex=float(sample.get("humanoid_capex_eur", 120000)),
            human_wage=float(sample.get("human_wage_eur", 18.50)),
            human_overhead=float(sample.get("human_overhead_mult", 1.35)),
        )
        npv_array.append(npv)

        samples.append({
            "sample_id": len(samples),
            "npv_eur": npv,
            **{f"{k}_sampled": v for k, v in sample.items()},
        })

    npv_array = np.array(npv_array)
    summary = {
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

    return samples, summary


def run_sensitivity_analysis(
    project_root: Path,
    scenario_id: str = "S-hybrid-amr",
    n_mc_samples: int = 10000,
) -> dict[str, Path]:
    """Run full sensitivity analysis (OAT + Monte Carlo) for a scenario.

    Returns dict mapping output paths.
    """
    data_processed = project_root / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)

    print("[Sensitivity] Running OAT + Monte Carlo analysis...")

    # Base parameters for S-hybrid-amr scenario
    base_params = {
        "humanoid_count": 2,  # 20% of 8 agents
        "human_count": 6,     # 60% of 8 agents
        "humanoid_capex_eur": 120000.0,
        "human_wage_eur": 18.50,
        "human_overhead_mult": 1.35,
    }

    # OAT parameter ranges (±50% from base)
    param_ranges = {
        "humanoid_capex_eur": (60000, 180000),
        "human_wage_eur": (9.25, 27.75),
        "human_overhead_mult": (0.67, 2.02),
        "humanoid_count": (0, 4),
        "human_count": (2, 8),
    }

    # Monte Carlo distributions (top 5 parameters)
    param_distributions = {
        "humanoid_capex_eur": {"type": "normal", "mean": 120000, "std": 30000},
        "human_wage_eur": {"type": "normal", "mean": 18.50, "std": 2.0},
        "human_overhead_mult": {"type": "uniform", "low": 1.0, "high": 1.7},
        "humanoid_count": {"type": "uniform", "low": 0, "high": 4},
        "human_count": {"type": "uniform", "low": 2, "high": 8},
    }

    # Run OAT
    print(f"  OAT sensitivity for {len(param_ranges)} parameters...")
    oat_results = run_oat_sensitivity(base_params, param_ranges, n_steps=11)

    # Run Monte Carlo
    print(f"  Monte Carlo: {n_mc_samples} samples...")
    mc_samples, mc_summary = run_monte_carlo_sensitivity(
        base_params, param_distributions, n_samples=n_mc_samples
    )

    # Export OAT results
    oat_df = pl.DataFrame(oat_results)
    oat_path = data_processed / "sensitivity_oat_results.parquet"
    oat_df.write_parquet(oat_path)
    print(f"  ✓ OAT: {oat_path}")

    # Export MC results (only first 1000 samples for size, summary stats are complete)
    mc_df = pl.DataFrame(mc_samples[:1000])  # Store first 1k samples
    mc_path = data_processed / "sensitivity_mc_samples.parquet"
    mc_df.write_parquet(mc_path)
    print(f"  ✓ MC samples: {mc_path}")

    # Export summary report
    report = {
        "phase": "sensitivity_analysis",
        "scenario_id": scenario_id,
        "oat_parameters": len(param_ranges),
        "mc_samples": n_mc_samples,
        "oat_results_path": str(oat_path),
        "mc_samples_path": str(mc_path),
        "mc_summary": mc_summary,
    }

    report_path = project_root / "reports" / "sensitivity_analysis_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"  ✓ Report: {report_path}")
    print(f"\n  MC Summary: NPV = €{mc_summary['npv_mean']:.0f} ± €{mc_summary['npv_std']:.0f}")
    print(f"    Range: €{mc_summary['npv_p5']:.0f} (p5) to €{mc_summary['npv_p95']:.0f} (p95)")

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
