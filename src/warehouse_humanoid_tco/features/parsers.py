"""Dataset-specific parsers for WBT and DiverseManip collections.

WBT datasets: flat file structure (parquet/json directly in root or single subdir)
DiverseManip: standard LeRobot V2.0+ structure (meta/, data/, videos/)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl


def resolve_nested_dataset(dataset_path: Path) -> Path:
    """Resolve nested dataset directory if present (Unitree structure).

    Returns the actual dataset directory.
    """
    subdirs = [d for d in dataset_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    if len(subdirs) == 1 and (subdirs[0] / "meta").exists():
        return subdirs[0]
    return dataset_path


def load_wbt_episodes_jsonl(dataset_path: Path) -> list[dict[str, Any]]:
    """Parse WBT dataset episodes from jsonl or Unitree chunked format.

    Supports both:
    1. LeRobot V2.0+ format: meta/episodes.jsonl
    2. Unitree chunked format: meta/info.json with episode metadata
    """
    dataset_path = resolve_nested_dataset(dataset_path)
    episodes = []

    # Try Unitree chunked format (info.json)
    info_path = dataset_path / "meta" / "info.json"
    if info_path.exists():
        with open(info_path) as f:
            info = json.load(f)
        # Create synthetic episode metadata from info.json
        total_episodes = info.get("total_episodes", 0)
        for i in range(total_episodes):
            episodes.append({
                "episode_index": i,
                "task": info.get("total_tasks", 1) > 0 and "task" or "unknown",
                "success": True,
            })
        return episodes

    # Try LeRobot V2.0+ format (episodes.jsonl)
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
        f"No episodes metadata found in {dataset_path}. "
        "Expected meta/episodes.jsonl or meta/info.json."
    )


def load_wbt_parquets(dataset_path: Path) -> dict[int, pl.DataFrame]:
    """Load episode parquets from WBT dataset (chunked or flat format).

    Returns dict mapping episode_id → episode_df (frame-level data).
    Handles both LeRobot and Unitree chunked formats.
    - Unitree: One large parquet with episode_index column → split by episode
    - LeRobot: One parquet per episode → return as-is
    """
    dataset_path = resolve_nested_dataset(dataset_path)
    episode_dfs = {}

    data_dir = dataset_path / "data"
    if not data_dir.exists():
        raise FileNotFoundError(f"No data directory in {dataset_path}")

    # Collect all parquets
    all_parquets = list(data_dir.glob("**/*.parquet"))
    if not all_parquets:
        raise FileNotFoundError(f"No parquet files found in {dataset_path}")

    # Load all parquets and merge if multiple
    all_frames = []
    for parquet_file in all_parquets:
        try:
            df = pl.read_parquet(parquet_file)
            all_frames.append(df)
        except Exception:
            continue

    if not all_frames:
        raise FileNotFoundError(f"Could not read any parquet files in {dataset_path}")

    combined_df = pl.concat(all_frames) if len(all_frames) > 1 else all_frames[0]

    # Check if this is Unitree chunked format (has episode_index column)
    if "episode_index" in combined_df.columns:
        # Split by episode_index
        for episode_id in combined_df["episode_index"].unique().sort().to_list():
            episode_df = combined_df.filter(pl.col("episode_index") == episode_id)
            episode_dfs[episode_id] = episode_df
    else:
        # Flat structure: each file is one episode
        for idx, parquet_file in enumerate(all_parquets):
            try:
                df = pl.read_parquet(parquet_file)
                # Try to infer episode_id from filename
                try:
                    episode_id = int(parquet_file.stem.split("_")[-1])
                except (ValueError, IndexError):
                    episode_id = idx
                episode_dfs[episode_id] = df
            except Exception:
                continue

    if not episode_dfs:
        raise FileNotFoundError(f"No valid episodes found in {dataset_path}")

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
    """Infer dataset type based on structure.

    Returns 'wbt' (chunked), 'diversemanip' (LeRobot), or 'unknown'.
    """
    # Check for nested dataset directory (WBT structure)
    subdirs = [d for d in dataset_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    if len(subdirs) == 1:
        nested_dir = subdirs[0]
        # Check if nested dir has the actual dataset structure
        if (nested_dir / "meta").exists() and (nested_dir / "data").exists():
            dataset_path = nested_dir

    # Check for Unitree chunked format (info.json + chunked parquets)
    if (dataset_path / "meta" / "info.json").exists():
        chunked_data = dataset_path / "data"
        if chunked_data.exists() and any(chunked_data.glob("chunk-*")):
            return "wbt"  # Unitree WBT format (chunked)

    # Check for LeRobot V2.0+ format (episodes.jsonl)
    if (dataset_path / "meta" / "episodes.jsonl").exists():
        return "diversemanip"

    return "unknown"
