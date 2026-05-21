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
from warehouse_humanoid_tco.features.extraction import extract_dataset_episodes
from warehouse_humanoid_tco.features.taxonomy import classify_task
from warehouse_humanoid_tco.features.aggregation import aggregate_capabilities


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
    if derisk_report_path:
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
        print(f"  Extracting features...")
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

        print(f"  Extracting features...")
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
    per_episode = pl.concat(all_episodes) if all_episodes else pl.DataFrame()

    if len(per_episode) > 0:
        per_episode = per_episode.with_columns(
            pl.col("task_description").map_elements(
                lambda desc: classify_task(desc).value, return_dtype=pl.Utf8
            ).alias("task_category")
        )

    # ========== Aggregate ==========
    print("[Aggregation] Computing summary statistics per task category...")
    if len(per_episode) > 0:
        summary = aggregate_capabilities(per_episode)
    else:
        summary = pl.DataFrame()

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
    validation_report = {
        "phase": "module_01_capability_extraction",
        "total_episodes_extracted": len(per_episode),
        "total_task_categories": len(summary) if len(summary) > 0 else 0,
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
