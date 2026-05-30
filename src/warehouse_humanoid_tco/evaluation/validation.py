"""Module 2 validation: compare human-only baseline simulation against Knapp benchmarks.

See PROJECT_CHARTER.md §7.5 Validation.
Passes if throughput is within 20% of published Knapp AutoStore benchmarks.
"""

from __future__ import annotations

from scipy import stats

# 960 orders per 8-hour shift = 120 orders/hour, the conservative lower-end anchor
# of Knapp's public AutoStore performance envelope (~100–250+ picks/h/port).
# Used by validate_human_baseline_throughput as a sanity gate, not a fitting target.
# See ADR-0009 (governance/adrs/0009-knapp-throughput-reference.md) for the full
# derivation, the asymmetry vs. config/autostore_baseline.yaml, and scope/limits.
# Knapp public product page: https://www.knapp.com/en/solutions/products/autostore/
KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE = 960.0  # orders per 8-hour shift (see ADR-0009)
TOLERANCE_FRACTION = 0.20


def validate_human_baseline_throughput(
    simulated_throughput: float,
    reference_throughput: float = KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE,
    tolerance: float = TOLERANCE_FRACTION,
) -> dict[str, float | bool | str]:
    """Check if simulation throughput is within tolerance of reference.

    Returns a dict with pass/fail status and diagnostics.
    """
    rel_error = abs(simulated_throughput - reference_throughput) / reference_throughput
    passed = rel_error <= tolerance

    return {
        "simulated_throughput": simulated_throughput,
        "reference_throughput": reference_throughput,
        "relative_error": rel_error,
        "tolerance": tolerance,
        "passed": passed,
        "status": "PASS" if passed else "FAIL",
        "note": (
            "Within tolerance."
            if passed
            else f"Relative error {rel_error:.1%} exceeds {tolerance:.0%} threshold. "
            "Recalibrate simulation parameters."
        ),
    }


def compare_throughput_distributions(
    scenario_runs: dict[str, list[float]],
    alpha: float = 0.05,
) -> dict[str, float | bool | str]:
    """Kruskal-Wallis H-test: are throughput distributions identical across scenarios?

    Args:
        scenario_runs: dict mapping scenario_id -> list of throughput values (one per run)
        alpha: significance level for rejection

    Returns dict with statistic, p_value, rejected (bool), and note.
    """
    if len(scenario_runs) < 2:
        raise ValueError(
            f"At least 2 scenarios required for Kruskal-Wallis test, got {len(scenario_runs)}."
        )

    groups = list(scenario_runs.values())
    result = stats.kruskal(*groups)
    h_stat: float = float(result.statistic)
    p_value: float = float(result.pvalue)
    rejected = p_value < alpha

    note = (
        "Distributions statistically different (routing divergence detected)."
        if rejected
        else "Distributions not statistically different (homogeneous throughput)."
    )

    return {
        "statistic": h_stat,
        "p_value": p_value,
        "rejected": rejected,
        "alpha": alpha,
        "n_scenarios": len(scenario_runs),
        "note": note,
    }
