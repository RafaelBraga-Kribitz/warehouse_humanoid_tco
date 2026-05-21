"""Integration-level tests for pipeline module helpers (no real data needed).

These tests use temporary directories with synthetic fixtures.
Marked @pytest.mark.integration where they test full pipeline paths.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import polars as pl
import pytest

import json as _json

from warehouse_humanoid_tco.analysis.sensitivity import run_sensitivity_analysis
from warehouse_humanoid_tco.features.extraction import (
    compute_energy_proxy,
    compute_reach_estimate,
    extract_dataset_episodes,
    extract_episode_features,
)
from warehouse_humanoid_tco.pipelines.module_03_tco import module_03_main


# ── features/extraction.py ────────────────────────────────────────────────────

def test_compute_energy_proxy_valid() -> None:
    df = pl.DataFrame({"action": [[0.1, 0.2, 0.3], [-0.1, 0.2, 0.0], [0.5, 0.0, 0.1]]})
    result = compute_energy_proxy(df)
    assert result is not None
    assert result > 0.0


def test_compute_energy_proxy_1d_returns_none() -> None:
    df = pl.DataFrame({"action": [0.1, 0.2, 0.3]})
    result = compute_energy_proxy(df)
    assert result is None


def _make_wbt_dataset_for_extraction(root: Path, n_episodes: int = 3) -> Path:
    meta = root / "meta"
    meta.mkdir(parents=True)
    data = root / "data"
    data.mkdir()
    info = {"total_episodes": n_episodes, "fps": 30, "total_tasks": 1}
    (meta / "info.json").write_text(_json.dumps(info))
    df = pl.DataFrame({
        "episode_index": [i for i in range(n_episodes) for _ in range(10)],
        "action": [[0.1, 0.2, 0.3]] * (n_episodes * 10),
        "observation.state": [[0.0, 0.0, 0.0]] * (n_episodes * 10),
    })
    df.write_parquet(data / "chunk-000.parquet")
    return root


def _make_diversemanip_dataset_for_extraction(root: Path, n_episodes: int = 3) -> Path:
    meta = root / "meta"
    meta.mkdir(parents=True)
    data = root / "data"
    data.mkdir()
    with open(meta / "episodes.jsonl", "w") as f:
        for i in range(n_episodes):
            f.write(_json.dumps({"episode_index": i, "task_index": 0}) + "\n")
    for i in range(n_episodes):
        pl.DataFrame({
            "action": [[0.1, 0.2, 0.3]] * 10,
        }).write_parquet(data / f"episode_{i:06d}.parquet")
    return root


@pytest.mark.integration
def test_extract_dataset_episodes_wbt(tmp_path: Path) -> None:
    _make_wbt_dataset_for_extraction(tmp_path, n_episodes=3)
    result = extract_dataset_episodes(tmp_path, fps=30.0)
    assert isinstance(result, pl.DataFrame)
    assert len(result) == 3
    assert "cycle_time_seconds" in result.columns
    assert "n_frames" in result.columns


@pytest.mark.integration
def test_extract_dataset_episodes_diversemanip(tmp_path: Path) -> None:
    _make_diversemanip_dataset_for_extraction(tmp_path, n_episodes=4)
    result = extract_dataset_episodes(tmp_path, fps=10.0)
    assert isinstance(result, pl.DataFrame)
    assert len(result) == 4


@pytest.mark.integration
def test_extract_dataset_episodes_infers_fps(tmp_path: Path) -> None:
    _make_wbt_dataset_for_extraction(tmp_path, n_episodes=2)
    result = extract_dataset_episodes(tmp_path, fps=None)  # should infer from info.json
    assert isinstance(result, pl.DataFrame)
    assert len(result) == 2


def test_extract_episode_features(tmp_path: Path) -> None:
    df = pl.DataFrame({
        "observation.state": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]] * 10,
        "action": [[0.1, 0.2, 0.3]] * 20,
    })
    parquet_path = tmp_path / "ep.parquet"
    df.write_parquet(parquet_path)
    result = extract_episode_features(str(parquet_path), "ep_0", fps=30.0)
    assert result["cycle_time_seconds"] > 0
    assert result["n_frames"] == 20
    assert result["episode_id"] == "ep_0"


# ── analysis/sensitivity.py run_sensitivity_analysis ─────────────────────────

@pytest.mark.integration
def test_run_sensitivity_analysis_creates_outputs(tmp_path: Path) -> None:
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)

    paths = run_sensitivity_analysis(tmp_path, scenario_id="S-hybrid-amr", n_mc_samples=100)

    assert paths["oat_results"].exists()
    assert paths["mc_samples"].exists()
    assert paths["report"].exists()


@pytest.mark.integration
def test_run_sensitivity_analysis_report_content(tmp_path: Path) -> None:
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)

    paths = run_sensitivity_analysis(tmp_path, n_mc_samples=50)

    with open(paths["report"]) as f:
        report = json.load(f)

    assert report["mc_samples"] == 50
    assert "mc_summary" in report
    assert report["mc_summary"]["n_samples"] == 50
    assert report["mc_summary"]["npv_mean"] < 0


@pytest.mark.integration
def test_run_sensitivity_oat_parquet_schema(tmp_path: Path) -> None:
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)

    paths = run_sensitivity_analysis(tmp_path, n_mc_samples=20)
    df = pl.read_parquet(paths["oat_results"])
    assert "parameter" in df.columns
    assert "npv_eur" in df.columns


# ── pipelines/module_03_tco.py module_03_main ─────────────────────────────────

@pytest.mark.integration
def test_module03_main_empty_no_sim_data(tmp_path: Path) -> None:
    """module_03_main should handle missing simulation data gracefully."""
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)
    (tmp_path / "config").mkdir(parents=True)

    result = module_03_main(tmp_path)

    assert "validation_report" in result
    assert result["validation_report"].exists()

    with open(result["validation_report"]) as f:
        report = json.load(f)
    assert report["scenarios_analyzed"] == 0


@pytest.mark.integration
def test_module03_main_with_sim_data(tmp_path: Path) -> None:
    """module_03_main computes TCO from synthetic simulation runs."""
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)
    (tmp_path / "config").mkdir(parents=True)

    # Create synthetic simulation runs
    sim_df = pl.DataFrame({
        "scenario_id": (
            ["S-baseline-human"] * 5
            + ["S-hybrid-amr"] * 5
            + ["S-pure-humanoid"] * 5
        ),
        "run_id": list(range(5)) * 3,
        "throughput_orders_per_shift": [900.0 + i for i in range(15)],
        "queue_length_mean": [0.5] * 15,
        "pipeline_version": ["0.1.0"] * 15,
        "seed": [42] * 15,
    })
    sim_path = tmp_path / "data" / "processed" / "simulation_runs.parquet"
    sim_df.write_parquet(sim_path)

    result = module_03_main(tmp_path)

    with open(result["validation_report"]) as f:
        report = json.load(f)

    assert report["scenarios_analyzed"] == 3
    assert result["tco_scenarios"] is not None
    assert Path(result["tco_scenarios"]).exists()


@pytest.mark.integration
def test_module03_main_tco_parquet_has_npv(tmp_path: Path) -> None:
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)
    (tmp_path / "config").mkdir(parents=True)

    sim_df = pl.DataFrame({
        "scenario_id": ["S-hybrid-amr"] * 3,
        "run_id": [0, 1, 2],
        "throughput_orders_per_shift": [900.0, 950.0, 920.0],
        "queue_length_mean": [0.5, 0.4, 0.6],
        "pipeline_version": ["0.1.0"] * 3,
        "seed": [42, 43, 44],
    })
    sim_path = tmp_path / "data" / "processed" / "simulation_runs.parquet"
    sim_df.write_parquet(sim_path)

    result = module_03_main(tmp_path)
    tco_df = pl.read_parquet(result["tco_scenarios"])

    assert "npv_eur" in tco_df.columns
    assert all(tco_df["npv_eur"] < 0)


# ── Real Data Integration Tests ──────────────────────────────────────────────

@pytest.mark.integration
def test_extract_episode_features_on_real_data(
    tmp_path: Path, real_sample_episodes: pl.DataFrame | None
) -> None:
    """Integration test: extract features from real cached dataset episodes.

    Uses fixture that loads ~10 episodes from WBT dataset (if available locally).
    Verifies that feature extraction works end-to-end on real data.
    """
    if real_sample_episodes is None:
        pytest.skip("Real dataset not available locally")

    assert len(real_sample_episodes) > 0, "Fixture returned empty DataFrame"
    assert "episode_index" in real_sample_episodes.columns
    assert "action" in real_sample_episodes.columns

    # Write real data to temp parquet and extract features
    parquet_path = tmp_path / "real_episode.parquet"
    real_sample_episodes.head(1).write_parquet(parquet_path)

    result = extract_episode_features(parquet_path, "real_ep_0", fps=30.0)
    assert result["cycle_time_seconds"] > 0
    assert result["n_frames"] > 0
    assert result["episode_id"] == "real_ep_0"
