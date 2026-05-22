"""Sensitivity analysis: OAT tornado chart + Monte Carlo.

See PROJECT_CHARTER.md §7.6 Sensitivity Analysis Protocol.
Top 10 parameters per tco_assumptions.yaml sensitivity_parameters.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import polars as pl


def one_at_a_time(
    base_params: dict[str, float],
    param_ranges: dict[str, tuple[float, float]],
    model_fn: Callable[..., float],
    *,
    n_steps: int = 20,
) -> pl.DataFrame:
    """OAT sensitivity: vary each parameter across its range, hold others at base.

    Returns a DataFrame with columns: parameter, value, output.
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
