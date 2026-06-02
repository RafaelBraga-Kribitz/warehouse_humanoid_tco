"""Tests for Module 2 and Module 4 pipeline entry points (synthetic fixtures)."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest
import yaml

from warehouse_humanoid_tco.pipelines.module_02_simulation import module_02_main
from warehouse_humanoid_tco.pipelines.module_04_dashboards import (
    export_for_tableau,
    generate_executive_charts,
)

# ── Minimal config fixture ─────────────────────────────────────────────────────


def _make_minimal_config(config_path: Path, n_scenarios: int = 2) -> None:
    config = {
        "architecture": "autostore",
        "version": "test",
        "operations": {
            "shift_hours": 0.05,  # very short for test speed
            "order_arrival_rate_per_hour": 60.0,
        },
        "agents": {
            "human": {"cycle_time_mean_seconds": 25.0, "cycle_time_std_seconds": 5.0},
            "humanoid": {"cycle_time_mean_seconds": 30.0, "cycle_time_std_seconds": 8.0},
            "amr": {"cycle_time_mean_seconds": 35.0, "cycle_time_std_seconds": 5.0},
        },
        "scenarios": [
            {
                "id": "S-baseline-human",
                "human_fraction": 1.0,
                "humanoid_fraction": 0.0,
                "amr_fraction": 0.0,
            },
            {
                "id": "S-hybrid-amr",
                "human_fraction": 0.6,
                "humanoid_fraction": 0.2,
                "amr_fraction": 0.2,
            },
        ][:n_scenarios],
        "total_agents": 4,
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)


# ── module_02_simulation.py ───────────────────────────────────────────────────


@pytest.mark.integration
def test_module02_main_runs_to_completion(tmp_path: Path) -> None:
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)
    (tmp_path / "config").mkdir(parents=True)

    config_path = tmp_path / "config" / "autostore_baseline.yaml"
    _make_minimal_config(config_path, n_scenarios=2)

    result = module_02_main(tmp_path, config_path=config_path, n_runs=2, seed=42)

    assert "simulation_runs" in result
    assert "validation_report" in result
    assert result["validation_report"].exists()

    with open(result["validation_report"]) as f:
        report = json.load(f)
    assert report["total_runs"] == 4  # 2 scenarios × 2 runs
    assert report["scenarios_tested"] == 2


@pytest.mark.integration
def test_module02_main_output_parquet_schema(tmp_path: Path) -> None:
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)

    config_path = tmp_path / "config" / "autostore_baseline.yaml"
    (tmp_path / "config").mkdir(parents=True)
    _make_minimal_config(config_path, n_scenarios=1)

    result = module_02_main(tmp_path, config_path=config_path, n_runs=3, seed=7)
    df = pl.read_parquet(result["simulation_runs"])

    assert "scenario_id" in df.columns
    assert "throughput_orders_per_shift" in df.columns
    assert len(df) == 3


@pytest.mark.integration
def test_module02_main_with_capability_summary(tmp_path: Path) -> None:
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)

    # Create a minimal capability summary
    summary = pl.DataFrame(
        {
            "task_category": ["pick_small_object"],
            "cycle_time_mean": [35.0],
            "cycle_time_std": [10.0],
        }
    )
    cap_path = tmp_path / "data" / "processed" / "humanoid_capabilities_summary.parquet"
    summary.write_parquet(cap_path)

    config_path = tmp_path / "config" / "autostore_baseline.yaml"
    (tmp_path / "config").mkdir(parents=True)
    _make_minimal_config(config_path, n_scenarios=1)

    result = module_02_main(
        tmp_path, config_path=config_path, capability_summary_path=cap_path, n_runs=2
    )
    assert result["simulation_runs"] is not None


# ── module_04_dashboards.py ───────────────────────────────────────────────────


def _make_processed_data(processed_dir: Path) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        {
            "task_category": ["pick_small_object", "place_general"],
            "n_episodes": [15, 10],
            "cycle_time_mean": [25.0, 12.0],
            "cycle_time_std": [5.0, 3.0],
        }
    ).write_parquet(processed_dir / "humanoid_capabilities_summary.parquet")

    pl.DataFrame(
        {
            "scenario_id": ["S-baseline-human", "S-hybrid-amr"],
            "run_id": [0, 0],
            "throughput_orders_per_shift": [920.0, 880.0],
            "queue_length_mean": [0.5, 0.3],
            "pipeline_version": ["0.1.0", "0.1.0"],
            "seed": [42, 42],
        }
    ).write_parquet(processed_dir / "simulation_runs.parquet")

    pl.DataFrame(
        {
            "scenario_id": ["S-baseline-human", "S-hybrid-amr"],
            "npv_eur": [-1608300.0, -924125.0],
            "total_capex_eur": [0.0, 120000.0],
            "total_opex_5yr_eur_nominal": [2014000.0, 1007000.0],
            "total_opex_5yr_eur_pv": [1608300.0, 804125.0],
            "cost_reduction_vs_baseline_pct": [0.0, 50.0],
            "payback_years": [None, 2.4],
            "pipeline_version": ["0.1.0", "0.1.0"],
        }
    ).write_parquet(processed_dir / "tco_scenarios.parquet")

    # F-044: chart 03 + tableau export read the capacity-ceiling parquet.
    pl.DataFrame(
        {
            "scenario_id": ["S-baseline-human", "S-hybrid-amr"],
            "target_rho": [0.85, 0.85],
            "total_agents": [8, 6],
            "bottleneck_agent_type": ["human", "humanoid"],
            "bottleneck_cycle_time_seconds": [25.0, 78.7],
            "lambda_max_per_hour": [979.2, 233.0],
            "capacity_orders_per_shift": [7834.0, 1864.0],
            "observed_throughput_mean": [7780.0, 1850.0],
            "observed_throughput_std": [40.0, 25.0],
            "n_runs_at_ceiling": [5, 5],
        }
    ).write_parquet(processed_dir / "simulation_capacity_ceiling.parquet")


@pytest.mark.integration
def test_export_for_tableau_creates_csvs(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    _make_processed_data(processed)
    export_dir = tmp_path / "exports"

    export_for_tableau(processed, export_dir)

    assert (export_dir / "humanoid_capabilities_summary.csv").exists()
    assert (export_dir / "simulation_runs.csv").exists()
    assert (export_dir / "tco_scenarios.csv").exists()
    assert (export_dir / "simulation_capacity_ceiling.csv").exists()


@pytest.mark.integration
def test_generate_executive_charts_creates_pngs(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    _make_processed_data(processed)
    charts_dir = tmp_path / "charts"

    generate_executive_charts(processed, charts_dir)

    assert (charts_dir / "01_tco_npv_ranking.png").exists()
    assert (charts_dir / "02_cost_breakdown.png").exists()
    assert (charts_dir / "03_simulation_throughput.png").exists()
