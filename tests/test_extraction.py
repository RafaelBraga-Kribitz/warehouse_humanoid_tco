"""Unit tests for per-episode feature extraction."""

from __future__ import annotations

import polars as pl

from warehouse_humanoid_tco.features.extraction import (
    compute_cycle_time,
    compute_energy_proxy,
    compute_reach_estimate,
)


def make_mock_episode(n_frames: int = 100, n_joints: int = 37) -> pl.DataFrame:
    import numpy as np

    rng = np.random.default_rng(42)
    return pl.DataFrame(
        {
            "observation.state": [rng.uniform(-1, 1, n_joints).tolist() for _ in range(n_frames)],
            "action": [rng.uniform(-0.1, 0.1, n_joints).tolist() for _ in range(n_frames)],
        }
    )


def test_cycle_time_basic() -> None:
    df = make_mock_episode(n_frames=300)
    result = compute_cycle_time(df, fps=30.0)
    assert abs(result - 10.0) < 1e-6


def test_reach_estimate_returns_positive() -> None:
    df = make_mock_episode()
    result = compute_reach_estimate(df)
    assert result is not None
    assert result >= 0.0


def test_energy_proxy_returns_positive() -> None:
    df = make_mock_episode()
    result = compute_energy_proxy(df)
    assert result is not None
    assert result > 0.0


def test_reach_estimate_missing_column() -> None:
    df = pl.DataFrame({"some_other_col": [1, 2, 3]})
    result = compute_reach_estimate(df)
    assert result is None
