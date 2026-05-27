"""Module 1: Capability Extraction Pipeline

Orchestrates:
1. Download datasets from HF (with pinned SHAs from de-risk)
2. Extract per-episode features (reach, cycle_time, energy, success)
3. Classify episodes by task taxonomy
4. Aggregate to summary statistics per task category
5. Validate against schemas and benchmarks
6. Export parquets for Module 2

Entry point: main()
See PROJECT_CHARTER.md §4 Module 1 for spec.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import yaml

from warehouse_humanoid_tco.data.download import download_dataset
from warehouse_humanoid_tco.features.aggregation import aggregate_capabilities
from warehouse_humanoid_tco.features.extraction import extract_dataset_episodes
from warehouse_humanoid_tco.features.taxonomy import classify_task


def module_01_main(
    project_root: Path,
    derisk_report_path: Path | None = None,
    skip_download: bool = False,
) -> dict[str, Path]:
    """Run Module 1 end-to-end.

    Returns dict mapping {'per_episode': ..., 'summary': ..., 'validation_report': ...}
    """
    config_path = project_root / "config" / "dataset_manifest.yaml"
    with open(config_path) as f:
        manifest = yaml.safe_load(f)

    derisk_report = {}
    if derisk_report_path and derisk_report_path.exists():
        with open(derisk_report_path) as f:
            derisk_report = json.load(f)

    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)

    # ========== Phase 1: Download and Extract WBT Datasets ==========
    all_episodes = []

    wbt_datasets = manifest.get("wbt_datasets", [])
    for ds_config in wbt_datasets:
        repo_id = ds_config["repo_id"]
        phase = ds_config.get("phase", 1)
        task_category = ds_config.get("task_category")

        print(f"\n[Phase {phase}] Extracting {repo_id}...")

        # Resolve SHA from de-risk report
        sha = derisk_report.get("datasets", {}).get(repo_id, {}).get("sha")
        if not sha:
            print(f"  WARNING: No SHA found for {repo_id}. Skipping.")
            continue

        # Download dataset
        dataset_dir = data_raw / repo_id.split("/")[1]
        if not skip_download:
            print(f"  Downloading to {dataset_dir}...")
            download_dataset(repo_id, sha, dataset_dir)

        # Extract features
        print("  Extracting features...")
        try:
            episodes_df = extract_dataset_episodes(dataset_dir, fps=10.0)
            episodes_df = episodes_df.with_columns(
                pl.lit(repo_id).alias("dataset_repo_id"),
                pl.lit(phase).alias("phase"),
                pl.lit(task_category).alias("task_category_source"),
            )
            all_episodes.append(episodes_df)
            print(f"  ✓ {len(episodes_df)} episodes extracted")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue

    # ========== Phase 2: Extract DiverseManip Datasets ==========
    diversemanip_datasets = manifest.get("diversemanip_datasets", [])
    for ds_config in diversemanip_datasets:
        repo_id = ds_config["repo_id"]
        phase = ds_config.get("phase", 2)
        task_category = ds_config.get("task_category")

        print(f"\n[Phase {phase}] Extracting {repo_id}...")

        sha = derisk_report.get("datasets", {}).get(repo_id, {}).get("sha")
        if not sha:
            print(f"  WARNING: No SHA found for {repo_id}. Skipping.")
            continue

        dataset_dir = data_raw / repo_id.split("/")[1]
        if not skip_download:
            print(f"  Downloading to {dataset_dir}...")
            download_dataset(repo_id, sha, dataset_dir)

        print("  Extracting features...")
        try:
            episodes_df = extract_dataset_episodes(dataset_dir, fps=10.0)
            episodes_df = episodes_df.with_columns(
                pl.lit(repo_id).alias("dataset_repo_id"),
                pl.lit(phase).alias("phase"),
                pl.lit(task_category).alias("task_category_source"),
            )
            all_episodes.append(episodes_df)
            print(f"  ✓ {len(episodes_df)} episodes extracted")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue

    # ========== Combine and Classify ==========
    print("\n[Classification] Mapping task descriptions to taxonomy...")
    if all_episodes:
        # Ensure consistent types before concat (cast to nullable numeric types)
        normalized = []
        for df in all_episodes:
            df = df.with_columns(
                pl.col("cycle_time_seconds").cast(pl.Float64),
                pl.col("reach_meters_estimate").cast(pl.Float64),
                pl.col("energy_proxy_joint_integral").cast(pl.Float64),
                pl.col("n_frames").cast(pl.Int64),
                pl.col("success_inferred").cast(pl.Boolean),
            )
            normalized.append(df)
        per_episode = pl.concat(normalized, how="diagonal")
    else:
        per_episode = pl.DataFrame()

    if len(per_episode) > 0:
        per_episode = per_episode.with_columns(
            pl.struct(["task_description", "dataset_repo_id", "task_category_source"])
            .map_elements(
                lambda row: [
                    c.value
                    for c in classify_task(
                        row["task_description"],
                        row["dataset_repo_id"],
                        row["task_category_source"],
                    )
                ],
                return_dtype=pl.List(pl.Utf8),
            )
            .alias("task_categories")
        )
        # Primary category (first match) preserved for single-label consumers
        per_episode = per_episode.with_columns(
            pl.col("task_categories").list.first().alias("task_category")
        )

    # ========== Aggregate ==========
    print("[Aggregation] Computing summary statistics per task category...")
    summary = aggregate_capabilities(per_episode) if len(per_episode) > 0 else pl.DataFrame()

    # ========== Export ==========
    print("[Export] Writing parquets...")
    per_episode_path = data_processed / "humanoid_capabilities_per_episode.parquet"
    summary_path = data_processed / "humanoid_capabilities_summary.parquet"

    if len(per_episode) > 0:
        per_episode.write_parquet(per_episode_path)
        print(f"  ✓ {per_episode_path}")

    if len(summary) > 0:
        summary.write_parquet(summary_path)
        print(f"  ✓ {summary_path}")

    # ========== Validation Report ==========
    category_episode_counts: dict[str, int] = {}
    multi_label_episode_count = 0
    avg_labels_per_episode = 0.0
    if len(per_episode) > 0 and "task_categories" in per_episode.columns:
        # Count categories across multi-label list column
        exploded = per_episode.explode("task_categories")
        category_episode_counts = {
            row["task_categories"]: int(row["n"])
            for row in (
                exploded.group_by("task_categories")
                .agg(pl.len().alias("n"))
                .sort("n", descending=True)
                .iter_rows(named=True)
            )
        }
        label_counts = per_episode.with_columns(
            pl.col("task_categories").list.len().alias("n_labels")
        )["n_labels"]
        multi_label_episode_count = int((label_counts > 1).sum())
        avg_labels_per_episode = float(label_counts.mean() or 0.0)

    validation_report = {
        "phase": "module_01_capability_extraction",
        "total_episodes_extracted": len(per_episode),
        "total_task_categories": len(summary) if len(summary) > 0 else 0,
        "category_episode_counts": category_episode_counts,
        "multi_label_episode_count": multi_label_episode_count,
        "avg_labels_per_episode": round(avg_labels_per_episode, 3),
        "datasets_processed": len(all_episodes),
        "per_episode_path": str(per_episode_path),
        "summary_path": str(summary_path),
    }

    report_path = project_root / "reports" / "module_01_capability_extraction_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2)

    print(f"\n✓ Module 1 complete. {len(per_episode)} episodes, {len(summary)} task categories.")
    print(f"  Report: {report_path}")

    return {
        "per_episode": per_episode_path,
        "summary": summary_path,
        "validation_report": report_path,
    }


if __name__ == "__main__":
    import sys

    project_root = Path(__file__).parent.parent.parent.parent
    derisk_report = project_root / "reports" / "derisk_inspection_report.json"

    try:
        paths = module_01_main(
            project_root,
            derisk_report_path=derisk_report,
            skip_download=False,
        )
        print(f"\n✓ Success. Outputs: {paths}")
    except Exception as e:
        print(f"\n✗ Failed: {e}", file=sys.stderr)
        sys.exit(1)
