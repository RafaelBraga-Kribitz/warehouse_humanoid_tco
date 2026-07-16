"""Tests for portable path serialization."""

from __future__ import annotations

from pathlib import Path

from warehouse_humanoid_tco.utils.paths import REPO_ROOT, repo_relative


def test_repo_root_parent_depth_matches_package_layout(tmp_path: Path) -> None:
    package_file = Path("src/warehouse_humanoid_tco/utils/paths.py").resolve()

    assert package_file.parents[3] == REPO_ROOT
    assert repo_relative(REPO_ROOT / "reports" / "example.json") == "reports/example.json"
    assert repo_relative(tmp_path / "data" / "processed" / "example.parquet") == (
        "data/processed/example.parquet"
    )
