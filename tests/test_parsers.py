"""Tests for dataset parsers (WBT, DiverseManip) — file-system based fixtures."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import polars as pl
import pytest

from warehouse_humanoid_tco.features.parsers import (
    infer_dataset_type,
    load_diversemanip_episodes_jsonl,
    load_diversemanip_parquets,
    load_wbt_episodes_jsonl,
    load_wbt_parquets,
    resolve_nested_dataset,
)


# ── helpers to build fixture datasets ─────────────────────────────────────────

def _make_wbt_dataset(root: Path, n_episodes: int = 3) -> Path:
    """Create a minimal WBT (Unitree chunked) dataset structure."""
    meta = root / "meta"
    meta.mkdir(parents=True)
    data = root / "data"
    data.mkdir()

    info = {"total_episodes": n_episodes, "total_tasks": 1, "fps": 30}
    (meta / "info.json").write_text(json.dumps(info))

    # Single chunked parquet with episode_index column
    df = pl.DataFrame({
        "episode_index": [i for i in range(n_episodes) for _ in range(10)],
        "frame_index": list(range(10)) * n_episodes,
        "action": [[0.1, 0.2, 0.3]] * (n_episodes * 10),
    })
    df.write_parquet(data / "chunk-000.parquet")
    return root


def _make_diversemanip_dataset(root: Path, n_episodes: int = 3) -> Path:
    """Create a minimal DiverseManip (LeRobot V2.0+) dataset structure."""
    meta = root / "meta"
    meta.mkdir(parents=True)
    data = root / "data"
    data.mkdir()

    episodes_jsonl = meta / "episodes.jsonl"
    with open(episodes_jsonl, "w") as f:
        for i in range(n_episodes):
            f.write(json.dumps({"episode_index": i, "task_index": 0, "length": 10}) + "\n")

    for i in range(n_episodes):
        df = pl.DataFrame({
            "frame_index": list(range(10)),
            "action": [[0.1, 0.2, 0.3]] * 10,
        })
        df.write_parquet(data / f"episode_{i:06d}.parquet")

    return root


# ── resolve_nested_dataset ────────────────────────────────────────────────────

def test_resolve_nested_no_nesting(tmp_path: Path) -> None:
    (tmp_path / "meta").mkdir()
    result = resolve_nested_dataset(tmp_path)
    assert result == tmp_path


def test_resolve_nested_with_nesting(tmp_path: Path) -> None:
    nested = tmp_path / "inner_dataset"
    nested.mkdir()
    (nested / "meta").mkdir()
    result = resolve_nested_dataset(tmp_path)
    assert result == nested


# ── load_wbt_episodes_jsonl ───────────────────────────────────────────────────

def test_load_wbt_episodes_from_info_json(tmp_path: Path) -> None:
    _make_wbt_dataset(tmp_path, n_episodes=5)
    episodes = load_wbt_episodes_jsonl(tmp_path)
    assert len(episodes) == 5


def test_load_wbt_episodes_from_jsonl(tmp_path: Path) -> None:
    meta = tmp_path / "meta"
    meta.mkdir()
    jsonl = meta / "episodes.jsonl"
    with open(jsonl, "w") as f:
        for i in range(4):
            f.write(json.dumps({"episode_index": i, "task": "pick"}) + "\n")
    episodes = load_wbt_episodes_jsonl(tmp_path)
    assert len(episodes) == 4


def test_load_wbt_episodes_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_wbt_episodes_jsonl(tmp_path)


# ── load_wbt_parquets ─────────────────────────────────────────────────────────

def test_load_wbt_parquets_chunked(tmp_path: Path) -> None:
    _make_wbt_dataset(tmp_path, n_episodes=3)
    result = load_wbt_parquets(tmp_path)
    assert len(result) == 3
    assert all(isinstance(df, pl.DataFrame) for df in result.values())


def test_load_wbt_parquets_no_data_dir(tmp_path: Path) -> None:
    (tmp_path / "meta").mkdir()
    with pytest.raises(FileNotFoundError):
        load_wbt_parquets(tmp_path)


# ── load_diversemanip_episodes_jsonl ──────────────────────────────────────────

def test_load_diversemanip_episodes(tmp_path: Path) -> None:
    _make_diversemanip_dataset(tmp_path, n_episodes=6)
    episodes = load_diversemanip_episodes_jsonl(tmp_path)
    assert len(episodes) == 6


def test_load_diversemanip_episodes_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_diversemanip_episodes_jsonl(tmp_path)


# ── load_diversemanip_parquets ────────────────────────────────────────────────

def test_load_diversemanip_parquets(tmp_path: Path) -> None:
    _make_diversemanip_dataset(tmp_path, n_episodes=4)
    result = load_diversemanip_parquets(tmp_path)
    assert len(result) == 4


def test_load_diversemanip_no_data_dir(tmp_path: Path) -> None:
    (tmp_path / "meta").mkdir()
    with pytest.raises(FileNotFoundError):
        load_diversemanip_parquets(tmp_path)


# ── infer_dataset_type ────────────────────────────────────────────────────────

def test_infer_wbt(tmp_path: Path) -> None:
    meta = tmp_path / "meta"
    meta.mkdir()
    (meta / "info.json").write_text("{}")
    data = tmp_path / "data"
    data.mkdir()
    (data / "chunk-000.parquet").touch()
    result = infer_dataset_type(tmp_path)
    assert result == "wbt"


def test_infer_diversemanip(tmp_path: Path) -> None:
    meta = tmp_path / "meta"
    meta.mkdir()
    (meta / "episodes.jsonl").touch()
    result = infer_dataset_type(tmp_path)
    assert result == "diversemanip"


def test_infer_unknown(tmp_path: Path) -> None:
    result = infer_dataset_type(tmp_path)
    assert result == "unknown"
