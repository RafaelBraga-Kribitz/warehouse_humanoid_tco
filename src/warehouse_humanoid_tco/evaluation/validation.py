"""Module 2 validation: compare human-only baseline simulation against Knapp benchmarks.

See PROJECT_CHARTER.md §7.5 Validation.
Passes if throughput is within 20% of published Knapp AutoStore benchmarks.
"""

from __future__ import annotations

KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE = 960.0  # orders per 8-hour shift (public benchmark)
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
