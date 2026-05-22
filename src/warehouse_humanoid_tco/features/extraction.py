"""Per-episode feature extraction from UnifoLM dataset collections.

Computes cycle_time, reach_estimate, energy_proxy from joint state time-series.
Handles both WBT and DiverseManip dataset structures.
See PROJECT_CHARTER.md §4 Module 1, Steps 6-7.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from warehouse_humanoid_tco.features.parsers import (
    infer_dataset_type,
    load_diversemanip_episodes_jsonl,
    load_diversemanip_parquets,
    load_wbt_episodes_jsonl,
    load_wbt_parquets,
    resolve_nested_dataset,
)

logger = logging.getLogger(__name__)


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


def extract_dataset_episodes(
    dataset_path: Path,
    fps: float | None = None,
) -> pl.DataFrame:
    """Extract features from all episodes in a dataset.

    Returns polars DataFrame with episode_id, cycle_time, reach, energy, n_frames, success_inferred.
    If fps is None, attempts to infer from dataset metadata (default 10.0 if not found).
    """
    dataset_path = resolve_nested_dataset(dataset_path)

    # Try to infer FPS from info.json if not provided
    if fps is None:
        fps = 10.0  # default
        info_path = dataset_path / "meta" / "info.json"
        if info_path.exists():
            import json

            with open(info_path) as f:
                info = json.load(f)
            fps = info.get("fps", 10.0)

    dataset_type = infer_dataset_type(dataset_path)

    if dataset_type == "wbt":
        episodes_meta = load_wbt_episodes_jsonl(dataset_path)
        episode_dfs = load_wbt_parquets(dataset_path)
    else:
        episodes_meta = load_diversemanip_episodes_jsonl(dataset_path)
        episode_dfs = load_diversemanip_parquets(dataset_path)

    # Create metadata lookup
    meta_by_id = {ep.get("episode_index", i): ep for i, ep in enumerate(episodes_meta)}

    features = []
    for episode_id, df in episode_dfs.items():
        try:
            feature_row = {
                "episode_id": episode_id,
                "cycle_time_seconds": compute_cycle_time(df, fps),
                "reach_meters_estimate": compute_reach_estimate(df),
                "energy_proxy_joint_integral": compute_energy_proxy(df),
                "n_frames": len(df),
            }

            # Add metadata from episodes.jsonl if available
            meta = meta_by_id.get(episode_id, {})
            feature_row["success_inferred"] = meta.get("success", None)
            feature_row["task_description"] = meta.get("task", "")

            features.append(feature_row)
        except Exception as e:
            logger.warning(f"Failed to extract features for episode {episode_id}: {e}")
            continue

    return pl.DataFrame(features)
