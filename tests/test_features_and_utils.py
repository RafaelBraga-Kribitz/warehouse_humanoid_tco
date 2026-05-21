"""Tests for features, utils, and visualization exports."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import polars as pl
import pytest

from warehouse_humanoid_tco.features.aggregation import aggregate_capabilities, MIN_EPISODES_PER_CATEGORY
from warehouse_humanoid_tco.features.extraction import (
    compute_cycle_time,
    compute_energy_proxy,
    compute_reach_estimate,
)
from warehouse_humanoid_tco.models.sensitivity import monte_carlo, one_at_a_time
from warehouse_humanoid_tco.utils.logging import get_logger, JsonFormatter
from warehouse_humanoid_tco.utils.reproducibility import seed_all
from warehouse_humanoid_tco.visualization.exports import export_for_tableau, export_for_powerbi


# ── features/extraction.py ────────────────────────────────────────────────────

def test_compute_cycle_time_basic() -> None:
    df = pl.DataFrame({"col": range(30)})
    assert compute_cycle_time(df, fps=30.0) == 1.0


def test_compute_cycle_time_fps_10() -> None:
    df = pl.DataFrame({"col": range(100)})
    assert compute_cycle_time(df, fps=10.0) == 10.0


def test_compute_reach_estimate_missing_col() -> None:
    df = pl.DataFrame({"other": [1.0]})
    assert compute_reach_estimate(df) is None


def test_compute_reach_estimate_with_state() -> None:
    states = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    df = pl.DataFrame({"observation.state": states})
    result = compute_reach_estimate(df)
    assert result is not None
    assert result > 0.0


def test_compute_reach_estimate_1d_returns_none() -> None:
    df = pl.DataFrame({"observation.state": [[1.0], [2.0]]})
    result = compute_reach_estimate(df)
    assert result is None


def test_compute_energy_proxy_missing_col() -> None:
    df = pl.DataFrame({"other": [1.0]})
    assert compute_energy_proxy(df) is None


# ── features/aggregation.py ───────────────────────────────────────────────────

def _make_episodes(n: int, category: str = "pick_small_object") -> pl.DataFrame:
    return pl.DataFrame({
        "task_category": [category] * n,
        "cycle_time_seconds": [float(i + 10) for i in range(n)],
        "reach_meters_estimate": [0.5] * n,
        "energy_proxy_joint_integral": [1.0] * n,
        "success_inferred": [True] * n,
    })


def test_aggregate_capabilities_basic() -> None:
    df = _make_episodes(20)
    result = aggregate_capabilities(df)
    assert "task_category" in result.columns
    assert "n_episodes" in result.columns
    assert result["n_episodes"][0] == 20


def test_aggregate_capabilities_insufficient_flag() -> None:
    df = _make_episodes(MIN_EPISODES_PER_CATEGORY - 1)
    result = aggregate_capabilities(df)
    assert result["insufficient_sample"][0] is True


def test_aggregate_capabilities_sufficient_flag() -> None:
    df = _make_episodes(MIN_EPISODES_PER_CATEGORY + 5)
    result = aggregate_capabilities(df)
    assert result["insufficient_sample"][0] is False


def test_aggregate_capabilities_multiple_categories() -> None:
    df = pl.concat([_make_episodes(15, "pick_small_object"), _make_episodes(15, "place_general")])
    result = aggregate_capabilities(df)
    assert len(result) == 2


# ── models/sensitivity.py ─────────────────────────────────────────────────────

def _simple_model(x: float, y: float = 1.0) -> float:
    return x * y


def test_oat_output_schema() -> None:
    df = one_at_a_time(
        base_params={"x": 5.0, "y": 1.0},
        param_ranges={"x": (1.0, 10.0)},
        model_fn=_simple_model,
        n_steps=5,
    )
    assert "parameter" in df.columns
    assert "value" in df.columns
    assert "output" in df.columns
    assert "delta_vs_base" in df.columns


def test_oat_correct_count() -> None:
    df = one_at_a_time(
        base_params={"x": 5.0, "y": 1.0},
        param_ranges={"x": (1.0, 10.0), "y": (0.5, 2.0)},
        model_fn=_simple_model,
        n_steps=4,
    )
    assert len(df) == 8  # 2 params × 4 steps


def test_monte_carlo_output_count() -> None:
    df = monte_carlo(
        base_params={"x": 5.0, "y": 1.0},
        param_distributions={"x": (1.0, 10.0)},
        model_fn=_simple_model,
        n_runs=50,
        seed=42,
    )
    assert len(df) == 50


def test_monte_carlo_deterministic() -> None:
    df1 = monte_carlo(
        base_params={"x": 5.0, "y": 1.0},
        param_distributions={"x": (1.0, 10.0)},
        model_fn=_simple_model,
        n_runs=20,
        seed=99,
    )
    df2 = monte_carlo(
        base_params={"x": 5.0, "y": 1.0},
        param_distributions={"x": (1.0, 10.0)},
        model_fn=_simple_model,
        n_runs=20,
        seed=99,
    )
    assert df1["output"].to_list() == df2["output"].to_list()


# ── utils/reproducibility.py ──────────────────────────────────────────────────

def test_seed_all_runs_without_error() -> None:
    seed_all(42)
    seed_all(0)


def test_seed_all_deterministic() -> None:
    import numpy as np
    seed_all(123)
    a = np.random.uniform()
    seed_all(123)
    b = np.random.uniform()
    assert a == b


# ── utils/logging.py ──────────────────────────────────────────────────────────

def test_get_logger_returns_logger() -> None:
    import logging
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)


def test_get_logger_idempotent() -> None:
    l1 = get_logger("test_idempotent")
    l2 = get_logger("test_idempotent")
    assert l1 is l2


def test_json_formatter_output() -> None:
    import logging
    fmt = JsonFormatter()
    record = logging.LogRecord("test", logging.INFO, "", 0, "hello world", None, None)
    output = fmt.format(record)
    parsed = json.loads(output)
    assert parsed["event"] == "hello world"
    assert parsed["level"] == "INFO"
    assert "timestamp" in parsed


# ── visualization/exports.py ──────────────────────────────────────────────────

def test_export_for_tableau_creates_csv(tmp_path: Path) -> None:
    df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    out = export_for_tableau(df, tmp_path, "test.csv")
    assert out.exists()
    assert out.suffix == ".csv"


def test_export_for_powerbi_creates_parquet(tmp_path: Path) -> None:
    df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    out = export_for_powerbi(df, tmp_path, "test.parquet")
    assert out.exists()
    assert out.suffix == ".parquet"
    loaded = pl.read_parquet(out)
    assert loaded.shape == df.shape


def test_export_creates_dir_if_missing(tmp_path: Path) -> None:
    df = pl.DataFrame({"x": [1]})
    subdir = tmp_path / "new" / "subdir"
    export_for_tableau(df, subdir, "out.csv")
    assert subdir.exists()
