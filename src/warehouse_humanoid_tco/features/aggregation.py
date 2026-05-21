"""Aggregate per-episode features to summary statistics by task category.

Produces the capability summary consumed by Module 2 simulation.
See PROJECT_CHARTER.md §4 Module 1, Step 7.
"""

from __future__ import annotations

import polars as pl

MIN_EPISODES_PER_CATEGORY = 10


def aggregate_capabilities(per_episode_df: pl.DataFrame) -> pl.DataFrame:
    """Compute summary statistics per task category.

    Categories with fewer than MIN_EPISODES_PER_CATEGORY episodes are flagged
    as insufficient_sample=True. They are NOT silently dropped.
    """
    summary = (
        per_episode_df.group_by("task_category")
        .agg(
            pl.len().alias("n_episodes"),
            # Cycle time percentiles
            pl.col("cycle_time_seconds").quantile(0.50).alias("cycle_time_p50"),
            pl.col("cycle_time_seconds").quantile(0.95).alias("cycle_time_p95"),
            pl.col("cycle_time_seconds").mean().alias("cycle_time_mean"),
            pl.col("cycle_time_seconds").std().alias("cycle_time_std"),
            # Reach
            pl.col("reach_meters_estimate").mean().alias("reach_mean_meters"),
            pl.col("reach_meters_estimate").max().alias("reach_max_meters"),
            # Energy proxy
            pl.col("energy_proxy_joint_integral").mean().alias("energy_proxy_mean"),
            # Success rate
            pl.col("success_inferred").mean().alias("success_rate"),
        )
        .with_columns(
            (pl.col("n_episodes") < MIN_EPISODES_PER_CATEGORY).alias("insufficient_sample")
        )
    )
    return summary
