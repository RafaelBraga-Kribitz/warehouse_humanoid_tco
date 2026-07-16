"""F-217 — content-addressed golden masters for available processed parquets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import polars as pl
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDENS = json.loads((REPO_ROOT / "tests" / "golden" / "golden_masters.json").read_text())


def _content_sha256(path: Path) -> str:
    """Hash logical row content so pins survive cross-platform Parquet encodings."""
    frame = pl.read_parquet(path)
    payload = json.dumps(
        frame.to_dicts(),
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("relative_path,expected", GOLDENS.items())
def test_processed_parquet_matches_golden_master(
    relative_path: str, expected: dict[str, object]
) -> None:
    """Skip absent generated data; validate every pinned artifact that is present."""
    path = REPO_ROOT / relative_path
    if not path.exists():
        pytest.xfail(f"Generated data unavailable: {relative_path}")

    frame = pl.read_parquet(path)
    assert frame.height == expected["rows"]
    assert frame.columns == expected["columns"]
    assert _content_sha256(path) == expected["sha256"]


@pytest.mark.parametrize(
    "relative_path",
    [
        "data/processed/humanoid_capabilities_summary.parquet",
        "data/processed/simulation_runs.parquet",
        "data/processed/tco_scenarios.parquet",
        "data/processed/simulation_capacity_ceiling.parquet",
    ],
)
def test_expected_pipeline_parquet_has_a_golden_entry_when_present(relative_path: str) -> None:
    """Require a pin when pipeline data is available; clearly xfail when absent."""
    if not (REPO_ROOT / relative_path).exists():
        pytest.xfail(f"Generated data unavailable: {relative_path}")
    assert relative_path in GOLDENS
