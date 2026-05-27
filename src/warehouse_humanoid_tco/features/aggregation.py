"""Aggregate per-episode features to summary statistics by task category.

Multi-label aware: if per_episode_df has a list-typed `task_categories`
column, each episode contributes to every category it matches (one row per
category after explode). Falls back to single-label `task_category` for
synthetic test inputs.

See PROJECT_CHARTER.md §4 Module 1, Step 7.
"""

from __future__ import annotations

import polars as pl

MIN_EPISODES_PER_CATEGORY = 10


def aggregate_capabilities(per_episode_df: pl.DataFrame) -> pl.DataFrame:
    """Compute summary statistics per task category.

    Accepts either:
      - `task_categories` (list[str]): multi-label; episode contributes to
        each category in its list. Single source of truth from the
        multi-label classifier.
      - `task_category` (str): single-label fallback for synthetic / legacy
        inputs.

    Categories with fewer than MIN_EPISODES_PER_CATEGORY episodes are flagged
    as `insufficient_sample=True`. They are NOT silently dropped.
    """
    if "task_categories" in per_episode_df.columns:
        df = per_episode_df
        # Drop any pre-existing string column so the rename doesn't clash
        if "task_category" in df.columns:
            df = df.drop("task_category")
        df = df.explode("task_categories").rename({"task_categories": "task_category"})
    elif "task_category" in per_episode_df.columns:
        df = per_episode_df
    else:
        raise ValueError(
            "per_episode_df must contain either 'task_categories' (list) or "
            "'task_category' (str)"
        )

    summary = (
        df.group_by("task_category")
        .agg(
            pl.len().alias("n_episodes"),
            pl.col("cycle_time_seconds").quantile(0.50).alias("cycle_time_p50"),
            pl.col("cycle_time_seconds").quantile(0.95).alias("cycle_time_p95"),
            pl.col("cycle_time_seconds").mean().alias("cycle_time_mean"),
            pl.col("cycle_time_seconds").std().alias("cycle_time_std"),
            pl.col("reach_meters_estimate").mean().alias("reach_mean_meters"),
            pl.col("reach_meters_estimate").max().alias("reach_max_meters"),
            pl.col("energy_proxy_joint_integral").mean().alias("energy_proxy_mean"),
            pl.col("success_inferred").mean().alias("success_rate"),
        )
        .with_columns(
            (pl.col("n_episodes") < MIN_EPISODES_PER_CATEGORY).alias("insufficient_sample")
        )
        .sort("task_category")
    )
    return summary
