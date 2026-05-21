"""Schema tests: every schema has a positive (valid) and negative (invalid) case."""

from __future__ import annotations

import pandas as pd
import pandera as pa
import pytest

from warehouse_humanoid_tco.data.schemas import HumanoidCapabilitySummarySchema


def make_valid_summary() -> pd.DataFrame:
    return pd.DataFrame({
        "task_category": ["pick_small_object"],
        "n_episodes": [15],
        "cycle_time_p50": [12.5],
        "cycle_time_p95": [28.0],
        "cycle_time_mean": [14.0],
        "cycle_time_std": [3.5],
        "success_rate": [0.87],
        "insufficient_sample": [False],
        "pipeline_version": ["0.1.0"],
    })


def test_summary_schema_valid() -> None:
    df = make_valid_summary()
    HumanoidCapabilitySummarySchema.validate(df)


def test_summary_schema_invalid_cycle_time() -> None:
    df = make_valid_summary()
    df["cycle_time_p50"] = -1.0  # violates ge=0.5
    with pytest.raises(pa.errors.SchemaError):
        HumanoidCapabilitySummarySchema.validate(df)


def test_summary_schema_invalid_success_rate() -> None:
    df = make_valid_summary()
    df["success_rate"] = 1.5  # violates le=1.0
    with pytest.raises(pa.errors.SchemaError):
        HumanoidCapabilitySummarySchema.validate(df)
