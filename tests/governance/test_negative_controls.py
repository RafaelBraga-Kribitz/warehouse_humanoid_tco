"""Negative controls for governance checkers and portable-report invariants."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_config_consumption import uncovered_keys  # noqa: E402
from check_internal_links import check_links_in_text  # noqa: E402
from check_no_abs_paths import absolute_path_matches  # noqa: E402


def test_link_checker_can_fail(tmp_path: Path) -> None:
    """A missing relative target is reported instead of silently ignored."""
    assert check_links_in_text("[missing](does-not-exist.md)", tmp_path) == ["does-not-exist.md"]


def test_unconsumed_config_leaf_is_reported(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("consumed: 1\ndecorative: 2\n", encoding="utf-8")
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / "consumer.py").write_text('value = config["consumed"]\n', encoding="utf-8")

    assert uncovered_keys([config], source_root) == {"decorative"}


def test_absolute_path_in_report_is_reported(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    report = reports / "report.json"
    report.write_text('{"path": "/home/example/artifact"}', encoding="utf-8")

    assert absolute_path_matches(tmp_path) == {report}


def test_report_writers_import_repo_relative() -> None:
    root = Path(__file__).resolve().parents[2]
    writers = [
        root / "src/warehouse_humanoid_tco/pipelines/module_01_capability_extraction.py",
        root / "src/warehouse_humanoid_tco/pipelines/module_02_simulation.py",
        root / "src/warehouse_humanoid_tco/pipelines/module_03_tco.py",
        root / "src/warehouse_humanoid_tco/pipelines/module_04_dashboards.py",
        root / "src/warehouse_humanoid_tco/analysis/sensitivity.py",
    ]

    assert all(
        "from warehouse_humanoid_tco.utils.paths import repo_relative" in path.read_text()
        for path in writers
    )
