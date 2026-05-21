"""Dataset-specific parsers for WBT and DiverseManip collections.

WBT datasets: flat file structure (parquet/json directly in root or single subdir)
DiverseManip: standard LeRobot V2.0+ structure (meta/, data/, videos/)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl


def load_wbt_episodes_jsonl(dataset_path: Path) -> list[dict[str, Any]]:
    """Parse WBT dataset episodes from jsonl or json files.

    WBT datasets store episode metadata as jsonl files (usually meta/episodes.jsonl
    or as a single json file). This function finds and loads them.
    """
    episodes = []

    # Try meta/episodes.jsonl (standard LeRobot location)
    meta_path = dataset_path / "meta" / "episodes.jsonl"
    if meta_path.exists():
        with open(meta_path) as f:
            for line in f:
                if line.strip():
                    episodes.append(json.loads(line))
        return episodes

    # Fallback: scan for any .jsonl file with episodes
    for jsonl_file in dataset_path.glob("**/*.jsonl"):
        if "episode" in jsonl_file.name.lower():
            with open(jsonl_file) as f:
                for line in f:
                    if line.strip():
                        episodes.append(json.loads(line))
            return episodes

    raise FileNotFoundError(
        f"No episodes.jsonl found in {dataset_path}. "
        "Expected meta/episodes.jsonl or similar."
    )


def load_wbt_parquets(dataset_path: Path) -> dict[int, pl.DataFrame]:
    """Load episode parquets from WBT dataset.

    Returns dict mapping episode_id → episode_df (frame-level data).
    """
    episode_dfs = {}

    # Standard LeRobot locations
    data_dir = dataset_path / "data"
    if data_dir.exists():
        for parquet_file in data_dir.glob("**/*.parquet"):
            try:
                df = pl.read_parquet(parquet_file)
                # Infer episode_id from filename (e.g., episode_000001.parquet)
                episode_id = int(parquet_file.stem.split("_")[-1])
                episode_dfs[episode_id] = df
            except Exception:
                continue

    if episode_dfs:
        return episode_dfs

    # Fallback: any parquet in root or subdir
    for parquet_file in dataset_path.glob("**/*.parquet"):
        try:
            df = pl.read_parquet(parquet_file)
            episode_id = int(parquet_file.stem.split("_")[-1])
            episode_dfs[episode_id] = df
        except Exception:
            continue

    if not episode_dfs:
        raise FileNotFoundError(f"No parquet files found in {dataset_path}")

    return episode_dfs


def load_diversemanip_episodes_jsonl(dataset_path: Path) -> list[dict[str, Any]]:
    """Parse DiverseManip episodes from meta/episodes.jsonl (LeRobot V2.0+)."""
    meta_path = dataset_path / "meta" / "episodes.jsonl"
    if not meta_path.exists():
        raise FileNotFoundError(f"Expected {meta_path} for DiverseManip dataset")

    episodes = []
    with open(meta_path) as f:
        for line in f:
            if line.strip():
                episodes.append(json.loads(line))

    return episodes


def load_diversemanip_parquets(dataset_path: Path) -> dict[int, pl.DataFrame]:
    """Load episode parquets from DiverseManip dataset (LeRobot V2.0+ layout)."""
    episode_dfs = {}
    data_dir = dataset_path / "data"

    if not data_dir.exists():
        raise FileNotFoundError(f"Expected {data_dir} for DiverseManip dataset")

    for parquet_file in data_dir.glob("**/*.parquet"):
        try:
            df = pl.read_parquet(parquet_file)
            episode_id = int(parquet_file.stem.split("_")[-1])
            episode_dfs[episode_id] = df
        except Exception:
            continue

    if not episode_dfs:
        raise FileNotFoundError(f"No parquets in {data_dir}")

    return episode_dfs


def infer_dataset_type(dataset_path: Path) -> str:
    """Infer whether dataset is WBT or DiverseManip based on structure.

    Returns 'wbt' or 'diversemanip'.
    """
    meta_path = dataset_path / "meta" / "episodes.jsonl"
    data_path = dataset_path / "data"

    if meta_path.exists() and data_path.exists():
        return "diversemanip"
    else:
        return "wbt"
