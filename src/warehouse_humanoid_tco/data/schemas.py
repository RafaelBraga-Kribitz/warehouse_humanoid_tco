"""Pandera schema contracts for all inter-module data.

These schemas are the API contracts between modules.
Module N is responsible for emitting valid data; Module N+1 may assume it.
See PROJECT_CHARTER.md §6.3 Schema Contracts.
"""

from __future__ import annotations

import pandera as pa
from pandera.typing import Series

from warehouse_humanoid_tco.data.enums import RobotPlatform, TaskCategory


class EpisodeMetadataSchema(pa.DataFrameModel):
    """Episode-level metadata extracted from UnifoLM-WBT.

    Producer: Module 1 Step 3
    Consumer: Module 1 Steps 4-7
    Path: data/interim/episode_metadata.parquet
    """

    episode_id: Series[str] = pa.Field(unique=True, nullable=False)
    task_description: Series[str] = pa.Field(nullable=True)
    robot_platform: Series[str] = pa.Field(
        isin=[p.value for p in RobotPlatform], nullable=False
    )
    n_frames: Series[int] = pa.Field(ge=1, nullable=False)
    duration_seconds: Series[float] = pa.Field(ge=0.1, le=3600, nullable=False)
    source_revision_sha: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = False


class HumanoidCapabilityPerEpisodeSchema(pa.DataFrameModel):
    """Per-episode humanoid capability features.

    Producer: Module 1 Steps 6-7
    Consumer: Module 2 (simulation sampling)
    Path: data/processed/humanoid_capabilities_per_episode.parquet
    """

    episode_id: Series[str] = pa.Field(unique=True, nullable=False)
    task_category: Series[str] = pa.Field(
        isin=[c.value for c in TaskCategory], nullable=False
    )
    robot_platform: Series[str] = pa.Field(
        isin=[p.value for p in RobotPlatform], nullable=False
    )
    cycle_time_seconds: Series[float] = pa.Field(ge=0.5, le=600, nullable=False)
    success_label: Series[bool] = pa.Field(nullable=True)
    payload_kg_estimate: Series[float] = pa.Field(ge=0.0, le=50.0, nullable=True)
    reach_meters_estimate: Series[float] = pa.Field(ge=0.0, le=5.0, nullable=True)
    energy_proxy_joint_integral: Series[float] = pa.Field(ge=0.0, nullable=True)
    pipeline_version: Series[str] = pa.Field(nullable=False)
    source_revision_sha: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = False


class HumanoidCapabilitySummarySchema(pa.DataFrameModel):
    """Aggregated capability statistics by task category.

    Producer: Module 1 Step 7
    Consumer: Module 2, Module 4
    Path: data/processed/humanoid_capabilities_summary.parquet
    """

    task_category: Series[str] = pa.Field(
        isin=[c.value for c in TaskCategory], nullable=False
    )
    n_episodes: Series[int] = pa.Field(ge=1, nullable=False)
    cycle_time_p50: Series[float] = pa.Field(ge=0.5, le=600, nullable=False)
    cycle_time_p95: Series[float] = pa.Field(ge=0.5, le=600, nullable=False)
    cycle_time_mean: Series[float] = pa.Field(ge=0.5, le=600, nullable=False)
    cycle_time_std: Series[float] = pa.Field(ge=0.0, nullable=False)
    success_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    insufficient_sample: Series[bool] = pa.Field(nullable=False)
    pipeline_version: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = False


class SimulationRunSchema(pa.DataFrameModel):
    """Per-scenario simulation outputs.

    Producer: Module 2
    Consumer: Module 3, Module 4
    Path: data/processed/simulation_runs.parquet
    """

    scenario_id: Series[str] = pa.Field(nullable=False)
    run_id: Series[int] = pa.Field(ge=0, nullable=False)
    throughput_orders_per_shift: Series[float] = pa.Field(ge=0.0, nullable=False)
    utilization_humanoid: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    utilization_human: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    utilization_amr: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    queue_length_mean: Series[float] = pa.Field(ge=0.0, nullable=False)
    pipeline_version: Series[str] = pa.Field(nullable=False)
    seed: Series[int] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = False


class TcoScenarioSchema(pa.DataFrameModel):
    """TCO financial model outputs per scenario.

    Producer: Module 3
    Consumer: Module 4
    Path: data/processed/tco_scenarios.parquet
    """

    scenario_id: Series[str] = pa.Field(nullable=False)
    npv_eur: Series[float] = pa.Field(nullable=False)
    irr: Series[float] = pa.Field(ge=-1.0, le=10.0, nullable=True)
    payback_years: Series[float] = pa.Field(ge=0.0, nullable=True)
    total_capex_eur: Series[float] = pa.Field(ge=0.0, nullable=False)
    total_opex_5yr_eur: Series[float] = pa.Field(ge=0.0, nullable=False)
    pipeline_version: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = False
