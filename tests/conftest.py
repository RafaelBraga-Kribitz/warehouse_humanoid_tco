"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import polars as pl
import pytest

# Headless CI / broken Tcl installs must not pull the TkAgg backend.
matplotlib.use("Agg")


@pytest.fixture
def sample_task_descriptions() -> list[str]:
    return [
        "pick up small cup from table",
        "pick up the box and carry it to the shelf",
        "walk to the other side of the room and place the item",
        "bimanual coordination to fold the cloth",
        "place precisely into the drawer slot",
        "drop the object into the container",
        "some completely unrelated description without keywords",
    ]


@pytest.fixture(scope="session")
def real_sample_episodes() -> pl.DataFrame | None:
    """Load up to 10 real episodes from cached HuggingFace data for integration tests.

    Uses the WBT Pillow dataset (smallest, ~715 episodes).
    Returns None if dataset is not available locally (allows CI to skip gracefully).
    Mark tests using this as @pytest.mark.integration to skip in fast CI.
    """
    data_dir = Path(__file__).parent.parent / "data" / "raw"

    # Try to find WBT data (any dataset will do)
    wbt_dirs = list(data_dir.glob("G1_WBT_*"))
    if not wbt_dirs:
        return None

    wbt_path = wbt_dirs[0] / "data"
    if not wbt_path.exists():
        return None

    # Load first parquet file, limit to 10 rows
    parquet_files = list(wbt_path.glob("chunk-*.parquet"))
    if not parquet_files:
        return None

    df = pl.read_parquet(parquet_files[0])
    # Return first 10 unique episodes
    return df.unique(subset=["episode_index"], keep="first").head(10)
