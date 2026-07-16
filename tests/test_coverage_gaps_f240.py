"""F-240 — non-vacuous coverage for previously under-tested modules."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest
import yaml

from warehouse_humanoid_tco.analysis.crew_optimizer import (
    generate_demand_frontier,
    module_02_humanoid_cycle_overrides,
    optimize_crew,
)
from warehouse_humanoid_tco.analysis.profile_outputs import generate_profile_notebook
from warehouse_humanoid_tco.data.manifest import record_artifact
from warehouse_humanoid_tco.features.parsers import load_wbt_episodes_jsonl
from warehouse_humanoid_tco.models.simulation import (
    compute_operational_availability,
    scale_line_cycle_to_order,
)
from warehouse_humanoid_tco.pipelines.module_01_capability_extraction import (
    module_01_main,
    require_episodes_extracted,
)


def test_manifest_records_and_replaces_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "out.parquet"
    artifact.write_bytes(b"abc123")
    manifest = tmp_path / "MANIFEST.yaml"

    record_artifact(manifest, artifact, "1.0.0", "deadbeef", "module_test")
    first = yaml.safe_load(manifest.read_text())
    assert len(first["outputs"]) == 1
    assert first["outputs"][0]["artifact"] == "out.parquet"
    assert first["outputs"][0]["sha256"]
    assert first["outputs"][0]["produced_by"] == "module_test"

    artifact.write_bytes(b"xyz999")
    record_artifact(manifest, artifact, "1.0.1", "cafebabe", "module_test")
    second = yaml.safe_load(manifest.read_text())
    assert len(second["outputs"]) == 1
    assert second["outputs"][0]["pipeline_version"] == "1.0.1"
    assert second["outputs"][0]["sha256"] != first["outputs"][0]["sha256"]


def test_profile_notebook_includes_summary_and_derisk(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    summary = pl.DataFrame(
        {
            "task_category": ["pick_medium_object"],
            "n_episodes": [5],
            "cycle_time_mean": [61.4],
            "cycle_time_std": [10.0],
            "insufficient_sample": [False],
        }
    )
    summary.write_parquet(processed / "humanoid_capabilities_summary.parquet")
    per_ep = pl.DataFrame(
        {
            "episode_id": ["e1"],
            "cycle_time_seconds": [12.0],
            "task_category": ["pick_medium_object"],
        }
    )
    per_ep.write_parquet(processed / "humanoid_capabilities_per_episode.parquet")

    derisk = tmp_path / "derisk.json"
    derisk.write_text(json.dumps({"datasets": {}, "status": "ok"}), encoding="utf-8")
    out_nb = tmp_path / "notebooks" / "profile.ipynb"

    generate_profile_notebook(processed, derisk, out_nb)
    assert out_nb.exists()
    notebook = json.loads(out_nb.read_text(encoding="utf-8"))
    assert len(notebook["cells"]) >= 5
    sources = " ".join(
        "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else cell.get("source", "")
        for cell in notebook["cells"]
    )
    assert "humanoid_capabilities_summary" in sources or "Module 1" in sources


def test_require_episodes_extracted_passes_and_fails() -> None:
    require_episodes_extracted(3, 1)
    with pytest.raises(RuntimeError, match="0 episodes"):
        require_episodes_extracted(0, 2)


def test_module_01_main_with_mocked_extraction(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "dataset_manifest.yaml").write_text(
        yaml.dump(
            {
                "wbt_datasets": [
                    {
                        "repo_id": "org/FakeWBT",
                        "phase": 1,
                        "task_category": "pick_medium_object",
                    }
                ],
                "diversemanip_datasets": [
                    {
                        "repo_id": "org/FakeDM",
                        "phase": 2,
                        "task_category": "place_general",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "data" / "raw" / "FakeWBT").mkdir(parents=True)
    (tmp_path / "data" / "raw" / "FakeDM").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)

    derisk = tmp_path / "derisk.json"
    derisk.write_text(
        json.dumps(
            {
                "datasets": {
                    "org/FakeWBT": {"sha": "abc123"},
                    "org/FakeDM": {"sha": "def456"},
                    "org/NoSha": {},
                }
            }
        ),
        encoding="utf-8",
    )

    fake_episodes = pl.DataFrame(
        {
            "episode_id": ["e0", "e1"],
            "task_description": ["pick a can", "pick a bottle"],
            "cycle_time_seconds": [12.0, 14.0],
            "reach_meters_estimate": [0.5, 0.6],
            "energy_proxy_joint_integral": [1.0, 1.1],
            "n_frames": [100, 110],
            "success_inferred": [True, True],
        }
    )

    with patch(
        "warehouse_humanoid_tco.pipelines.module_01_capability_extraction.extract_dataset_episodes",
        return_value=fake_episodes,
    ):
        result = module_01_main(tmp_path, derisk_report_path=derisk, skip_download=True)

    assert result["per_episode"].exists()
    assert result["summary"].exists()
    report = json.loads(result["validation_report"].read_text(encoding="utf-8"))
    assert report["total_episodes_extracted"] == 4  # 2 datasets × 2 episodes
    assert report["datasets_processed"] == 2


def test_module_01_skips_missing_sha_and_failed_extract(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "dataset_manifest.yaml").write_text(
        yaml.dump(
            {
                "wbt_datasets": [
                    {"repo_id": "org/NoSha", "phase": 1, "task_category": "pick_medium_object"},
                    {"repo_id": "org/BadExtract", "phase": 1, "task_category": "pick_medium_object"},
                ],
                "diversemanip_datasets": [
                    {"repo_id": "org/NoShaDM", "phase": 2, "task_category": "place_general"},
                ],
            }
        ),
        encoding="utf-8",
    )
    for name in ("NoSha", "BadExtract", "NoShaDM"):
        (tmp_path / "data" / "raw" / name).mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)
    derisk = tmp_path / "derisk.json"
    derisk.write_text(
        json.dumps({"datasets": {"org/BadExtract": {"sha": "deadbeef"}}}),
        encoding="utf-8",
    )

    with patch(
        "warehouse_humanoid_tco.pipelines.module_01_capability_extraction.extract_dataset_episodes",
        side_effect=RuntimeError("corrupt parquet"),
    ):
        with pytest.raises(RuntimeError, match="0 episodes"):
            module_01_main(tmp_path, derisk_report_path=derisk, skip_download=True)


def test_scale_line_and_availability_reject_nonpositive() -> None:
    with pytest.raises(ValueError):
        scale_line_cycle_to_order(25.0, 8.0, 0.0)
    with pytest.raises(ValueError):
        scale_line_cycle_to_order(25.0, 8.0, -1.0)
    with pytest.raises(ValueError):
        compute_operational_availability(40.0, 0.0, 4.0, 1.0)


def test_optimize_crew_rejects_pure_amr_policy() -> None:
    sim = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "config" / "autostore_baseline.yaml").read_text()
    )
    assumptions = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "config" / "tco_assumptions.yaml").read_text()
    )
    with pytest.raises(ValueError, match="pure-AMR"):
        optimize_crew({"amr"}, sim, assumptions, lambda_per_hour=120.0)


def test_module_02_humanoid_overrides_scaled(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    sim = yaml.safe_load((root / "config" / "autostore_baseline.yaml").read_text())
    overrides = module_02_humanoid_cycle_overrides(sim, root)
    assert "humanoid" in overrides
    mean, std = overrides["humanoid"]
    assert mean > 100.0  # transfer + availability + pick_lines
    assert std > 0.0


def test_generate_demand_frontier_writes_report_and_chart(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    # Use real repo so capability parquet + configs exist; write outputs under tmp via chdir? 
    # generate_demand_frontier writes to project_root/reports — use real root but assert keys.
    paths = generate_demand_frontier(root)
    assert paths["report"].exists()
    assert paths["chart"].exists()
    report = json.loads(paths["report"].read_text(encoding="utf-8"))
    assert len(report["results"]) == 12
    assert all(row["human_count"] > 0 or row["humanoid_count"] > 0 for row in report["results"])
    assert not any(
        row["human_count"] == 0 and row["humanoid_count"] == 0 and row["amr_count"] > 0
        for row in report["results"]
    )


def test_load_wbt_episodes_missing_metadata_raises(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    with pytest.raises(FileNotFoundError, match="No episodes metadata"):
        load_wbt_episodes_jsonl(tmp_path / "empty")


def test_load_wbt_episodes_from_jsonl_fallback(tmp_path: Path) -> None:
    ds = tmp_path / "ds"
    ds.mkdir()
    (ds / "episodes_meta.jsonl").write_text(
        json.dumps({"episode_index": 0, "task": "pick"}) + "\n",
        encoding="utf-8",
    )
    episodes = load_wbt_episodes_jsonl(ds)
    assert len(episodes) == 1
    assert episodes[0]["episode_index"] == 0


def test_parser_error_paths_and_flat_wbt(tmp_path: Path) -> None:
    from warehouse_humanoid_tco.features.parsers import (
        infer_dataset_type,
        load_diversemanip_episodes_jsonl,
        load_diversemanip_parquets,
        load_wbt_parquets,
    )

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match="No data directory"):
        load_wbt_parquets(empty)
    with pytest.raises(FileNotFoundError, match="Expected"):
        load_diversemanip_episodes_jsonl(empty)
    with pytest.raises(FileNotFoundError, match="Expected"):
        load_diversemanip_parquets(empty)
    assert infer_dataset_type(empty) == "unknown"

    flat = tmp_path / "flat"
    (flat / "data").mkdir(parents=True)
    pl.DataFrame({"frame_index": [0, 1], "action": [[0.1], [0.2]]}).write_parquet(
        flat / "data" / "episode_000007.parquet"
    )
    episodes = load_wbt_parquets(flat)
    assert 7 in episodes


def test_sensitivity_config_loaders_missing_and_corrupt(tmp_path: Path) -> None:
    from warehouse_humanoid_tco.analysis.sensitivity import (
        _load_monte_carlo_seed,
        _load_sensitivity_config,
    )

    assert _load_sensitivity_config(tmp_path) == {}
    assert _load_monte_carlo_seed(tmp_path, default=99) == 99

    bad = tmp_path / "config"
    bad.mkdir()
    (bad / "tco_assumptions.yaml").write_text(": not: yaml: [[[", encoding="utf-8")
    (bad / "seeds.yaml").write_text(": bad: [[[", encoding="utf-8")
    assert _load_sensitivity_config(tmp_path) == {}
    assert _load_monte_carlo_seed(tmp_path, default=7) == 7

    (bad / "seeds.yaml").write_text("monte_carlo:\n  tco_sensitivity_seed: 123\n", encoding="utf-8")
    assert _load_monte_carlo_seed(tmp_path) == 123


def test_module_01_calls_download_when_not_skipped(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "dataset_manifest.yaml").write_text(
        yaml.dump(
            {
                "wbt_datasets": [
                    {"repo_id": "org/DL", "phase": 1, "task_category": "pick_medium_object"}
                ],
                "diversemanip_datasets": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "data" / "raw" / "DL").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)
    derisk = tmp_path / "derisk.json"
    derisk.write_text(json.dumps({"datasets": {"org/DL": {"sha": "sha1"}}}), encoding="utf-8")
    fake = pl.DataFrame(
        {
            "episode_id": ["e0"],
            "task_description": ["pick"],
            "cycle_time_seconds": [10.0],
            "reach_meters_estimate": [0.4],
            "energy_proxy_joint_integral": [1.0],
            "n_frames": [50],
            "success_inferred": [True],
        }
    )
    with (
        patch(
            "warehouse_humanoid_tco.pipelines.module_01_capability_extraction.download_dataset"
        ) as mock_dl,
        patch(
            "warehouse_humanoid_tco.pipelines.module_01_capability_extraction.extract_dataset_episodes",
            return_value=fake,
        ),
    ):
        module_01_main(tmp_path, derisk_report_path=derisk, skip_download=False)
        mock_dl.assert_called_once()
