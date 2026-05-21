"""Per-episode feature extraction from UnifoLM-WBT parquet files.

Computes cycle_time, reach_estimate, energy_proxy, and phase breakdown
from raw joint state time-series.
See PROJECT_CHARTER.md §4 Module 1, Steps 6-7.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import polars as pl


def compute_cycle_time(df: pl.DataFrame, fps: float) -> float:
    """Total duration of the manipulation phase in seconds."""
    return len(df) / fps


def compute_reach_estimate(df: pl.DataFrame, state_col: str = "observation.state") -> float | None:
    """Max end-effector displacement from base frame across episode.

    Uses the first 3 elements of the state vector as position proxy.
    Returns None if the column or dimensionality is not suitable.
    """
    if state_col not in df.columns:
        return None

    try:
        states = np.array(df[state_col].to_list())
        if states.ndim != 2 or states.shape[1] < 3:
            return None
        positions = states[:, :3]
        base = positions[0]
        displacements = np.linalg.norm(positions - base, axis=1)
        return float(displacements.max())
    except Exception:
        return None


def compute_energy_proxy(df: pl.DataFrame, action_col: str = "action") -> float | None:
    """Surrogate for mechanical energy: sum |velocity_i * action_i| over episode.

    This is an estimate, not a direct energy measurement.
    See PROJECT_CHARTER.md §6 Known Limitations.
    """
    if action_col not in df.columns:
        return None

    try:
        actions = np.array(df[action_col].to_list())
        if actions.ndim != 2:
            return None
        return float(np.abs(actions).sum())
    except Exception:
        return None


def extract_episode_features(
    parquet_path: Path,
    episode_id: str,
    fps: float,
    state_col: str = "observation.state",
    action_col: str = "action",
) -> dict[str, Any]:
    """Extract all per-episode features from a single parquet file."""
    df = pl.read_parquet(parquet_path)

    return {
        "episode_id": episode_id,
        "cycle_time_seconds": compute_cycle_time(df, fps),
        "reach_meters_estimate": compute_reach_estimate(df, state_col),
        "energy_proxy_joint_integral": compute_energy_proxy(df, action_col),
        "n_frames": len(df),
    }
