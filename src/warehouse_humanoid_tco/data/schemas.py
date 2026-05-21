"""Schema definitions for inter-module contracts.

Note: Pandera DataFrameModel API changed significantly; using simplified
dictionaries for now. Full validation deferred to Module 1+ integration.
See PROJECT_CHARTER.md §6.3 Schema Contracts.
"""

from __future__ import annotations

# Schema contracts documented as type annotations
# Full pandera validation to be implemented in Module 1+ integration tests

EPISODE_METADATA_SCHEMA = {
    "episode_id": "str (unique, non-null)",
    "task_description": "str (nullable)",
    "robot_platform": "str (enum: unitree_g1, z1)",
    "n_frames": "int (>=1, non-null)",
    "duration_seconds": "float (0.1-3600, non-null)",
    "source_revision_sha": "str (non-null)",
}

HUMANOID_CAPABILITY_PER_EPISODE_SCHEMA = {
    "episode_id": "str (unique, non-null)",
    "task_category": "str (enum: task categories)",
    "robot_platform": "str (enum)",
    "cycle_time_seconds": "float (0.5-600, non-null)",
    "success_label": "bool (nullable)",
    "reach_meters_estimate": "float (0.0-5.0, nullable)",
    "energy_proxy_joint_integral": "float (>=0.0, nullable)",
    "pipeline_version": "str (non-null)",
    "source_revision_sha": "str (non-null)",
}

HUMANOID_CAPABILITY_SUMMARY_SCHEMA = {
    "task_category": "str (enum, non-null)",
    "n_episodes": "int (>=1, non-null)",
    "cycle_time_p50": "float (0.5-600, non-null)",
    "cycle_time_p95": "float (0.5-600, non-null)",
    "cycle_time_mean": "float (0.5-600, non-null)",
    "cycle_time_std": "float (>=0.0, non-null)",
    "success_rate": "float (0.0-1.0, nullable)",
    "insufficient_sample": "bool (non-null)",
    "pipeline_version": "str (non-null)",
}

SIMULATION_RUN_SCHEMA = {
    "scenario_id": "str (non-null)",
    "run_id": "int (>=0, non-null)",
    "throughput_orders_per_shift": "float (>=0.0, non-null)",
    "utilization_humanoid": "float (0.0-1.0, nullable)",
    "utilization_human": "float (0.0-1.0, nullable)",
    "utilization_amr": "float (0.0-1.0, nullable)",
    "queue_length_mean": "float (>=0.0, non-null)",
    "pipeline_version": "str (non-null)",
    "seed": "int (non-null)",
}

TCO_SCENARIO_SCHEMA = {
    "scenario_id": "str (non-null)",
    "npv_eur": "float (non-null)",
    "irr": "float (-1.0-10.0, nullable)",
    "payback_years": "float (>=0.0, nullable)",
    "total_capex_eur": "float (>=0.0, non-null)",
    "total_opex_5yr_eur": "float (>=0.0, non-null)",
    "pipeline_version": "str (non-null)",
}
