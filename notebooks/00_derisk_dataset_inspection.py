# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: "1.3"
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
"""
# De-Risk Notebook: UnifoLM-WBT-Dataset Structure Inspection

## Purpose

This notebook is the FIRST thing you run for the project. Its only job is
to validate the assumptions in the Module 1 spec against the actual
dataset. Until this notebook produces a clean report, do not trust the
spec details.

## What this notebook validates

1. Is the dataset publicly downloadable without authentication?
2. What is the actual LeRobot V2.0+ schema for this release?
3. Are task descriptions present and how are they structured?
4. How many episodes exist and what are their durations?
5. Which task categories from the proposed taxonomy actually appear?
6. Is there a success / failure label or must we infer it?
7. Are payload, reach, and energy directly available or must we estimate?

## Outputs

Writes a JSON report to `reports/derisk_inspection_report.json` that the
Module 1 spec refactor will consume.

## Reproducibility

This notebook resolves and prints the dataset revision SHA. Copy that SHA
into the production code before any real pipeline run.
"""

# %%
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# %% [markdown]
"""
## Step 0: Environment check

Confirm the runtime environment has every required package before
downloading anything. Fail fast if missing.
"""

# %%
REQUIRED_PACKAGES = [
    "huggingface_hub",
    "pyarrow",
    "polars",
]

missing_packages: list[str] = []
for package_name in REQUIRED_PACKAGES:
    try:
        __import__(package_name)
    except ImportError:
        missing_packages.append(package_name)

if missing_packages:
    print(f"Missing packages: {missing_packages}")
    print("Install with:")
    print(f"  pip install {' '.join(missing_packages)}")
    sys.exit(1)

print("All required packages available.")
print(f"Python: {sys.version.split()[0]}")

# %% [markdown]
"""
## Step 1: Configuration

All configurable values live in this single cell. No magic numbers below.
"""

# %%
DATASET_REPO_ID = "unitreerobotics/UnifoLM-WBT-Dataset"
DATASET_REVISION = "main"  # Resolved to SHA below for reproducibility
LOCAL_CACHE_DIR = Path("../data/raw/unifolm_wbt")
SAMPLE_EPISODE_LIMIT = 5
INSPECTION_REPORT_PATH = Path("../reports/derisk_inspection_report.json")

LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
INSPECTION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Accumulator for the final report
inspection_report: dict[str, Any] = {
    "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "dataset_repo_id": DATASET_REPO_ID,
    "requested_revision": DATASET_REVISION,
}

# %% [markdown]
"""
## Step 2: Verify dataset accessibility

Inspect dataset metadata via the Hugging Face Hub API without downloading
the full payload. If this step fails, the dataset may be gated.

Troubleshooting if access fails:
- Visit https://huggingface.co/datasets/unitreerobotics/UnifoLM-WBT-Dataset
- Accept any license agreement on the dataset page
- Set the HF_TOKEN environment variable if authentication is required
"""

# %%
from huggingface_hub import HfApi, hf_hub_download

api = HfApi()

try:
    dataset_info = api.dataset_info(
        repo_id=DATASET_REPO_ID,
        revision=DATASET_REVISION,
    )
except Exception as exc:
    print(f"FAIL: Cannot access dataset. Error: {exc}")
    print("STOP. Resolve access before proceeding.")
    raise

pinned_revision_sha = dataset_info.sha
inspection_report["resolved_revision_sha"] = pinned_revision_sha
inspection_report["last_modified"] = (
    dataset_info.last_modified.isoformat()
    if dataset_info.last_modified
    else None
)

print(f"Dataset accessible.")
print(f"Last modified:     {dataset_info.last_modified}")
print(f"Resolved revision: {pinned_revision_sha}")
print(f"Total files:       {len(dataset_info.siblings)}")
print()
print(f"PIN THIS SHA in production code: {pinned_revision_sha}")

# %% [markdown]
"""
## Step 3: Catalog file structure

LeRobot V2.0+ datasets typically follow this layout:

```
dataset_root/
    meta/
        info.json         dataset-level metadata
        episodes.jsonl    per-episode metadata
        tasks.jsonl       task taxonomy
        stats.json        statistics
    data/
        chunk-000/
            episode_000000.parquet
            ...
    videos/
        chunk-000/
            observation.images.<camera>/
                episode_000000.mp4
                ...
```

This cell catalogs the actual file structure. Differences from the
expected layout become refactor items for the Module 1 spec.
"""

# %%
all_files = [sibling.rfilename for sibling in dataset_info.siblings]

meta_files = [f for f in all_files if f.startswith("meta/")]
data_files = [f for f in all_files if f.startswith("data/")]
video_files = [f for f in all_files if f.startswith("videos/")]
other_files = [
    f for f in all_files
    if not any(f.startswith(prefix) for prefix in ("meta/", "data/", "videos/"))
]

print(f"meta files:  {len(meta_files)}")
print(f"data files:  {len(data_files)}")
print(f"video files: {len(video_files)}")
print(f"other:       {len(other_files)}")

print("\nAll meta files:")
for meta_file in meta_files:
    print(f"  {meta_file}")

print("\nFirst 5 data files:")
for data_file in data_files[:5]:
    print(f"  {data_file}")

print("\nOther files (anything unexpected lands here):")
for other_file in other_files[:10]:
    print(f"  {other_file}")

inspection_report["file_counts"] = {
    "meta": len(meta_files),
    "data": len(data_files),
    "videos": len(video_files),
    "other": len(other_files),
}
inspection_report["meta_files"] = meta_files
inspection_report["other_files_sample"] = other_files[:20]

# %% [markdown]
"""
## Step 4: Download and inspect metadata files

The meta directory carries the global structure. If anything diverges
from LeRobot V2.0+ expectations, this is where we find out.
"""

# %%
meta_local_paths: dict[str, Path] = {}

for meta_file in meta_files:
    local_path = hf_hub_download(
        repo_id=DATASET_REPO_ID,
        filename=meta_file,
        repo_type="dataset",
        revision=pinned_revision_sha,
        local_dir=str(LOCAL_CACHE_DIR),
    )
    meta_local_paths[meta_file] = Path(local_path)
    size_kb = Path(local_path).stat().st_size / 1024
    print(f"Downloaded: {meta_file} ({size_kb:.1f} KB)")

# %% [markdown]
"""
### 4a: Inspect info.json

Authoritative source for dataset structure: episode count, frame count,
feature schemas, robot platform, video specs.
"""

# %%
info_path = meta_local_paths.get("meta/info.json")
info: dict[str, Any] = {}

if info_path and info_path.exists():
    with open(info_path) as file_handle:
        info = json.load(file_handle)

    print("Top-level keys in info.json:")
    for key in info.keys():
        print(f"  {key}")

    print("\nKey statistics:")
    print(f"  total_episodes: {info.get('total_episodes')}")
    print(f"  total_frames:   {info.get('total_frames')}")
    print(f"  total_tasks:    {info.get('total_tasks')}")
    print(f"  fps:            {info.get('fps')}")
    print(f"  robot_type:     {info.get('robot_type')}")
    print(f"  codebase_version: {info.get('codebase_version')}")

    print("\nFeature schema (columns in each episode parquet):")
    features = info.get("features", {})
    for feature_name, feature_def in features.items():
        dtype = feature_def.get("dtype", "?")
        shape = feature_def.get("shape", "?")
        print(f"  {feature_name}: dtype={dtype}, shape={shape}")

    inspection_report["info_summary"] = {
        "total_episodes": info.get("total_episodes"),
        "total_frames": info.get("total_frames"),
        "total_tasks": info.get("total_tasks"),
        "fps": info.get("fps"),
        "robot_type": info.get("robot_type"),
        "codebase_version": info.get("codebase_version"),
        "feature_names": list(features.keys()),
    }
else:
    print("WARN: meta/info.json not found. Dataset structure UNKNOWN.")
    print("STOP and reassess before any further work.")

# %% [markdown]
"""
### 4b: Inspect tasks.jsonl

The task taxonomy Unitree provides. If their labels are already
well-structured, the manual review step in Module 1 may shrink
dramatically.
"""

# %%
tasks_path = meta_local_paths.get("meta/tasks.jsonl")
tasks: list[dict] = []

if tasks_path and tasks_path.exists():
    with open(tasks_path) as file_handle:
        for line in file_handle:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))

    print(f"Total task definitions: {len(tasks)}")

    if tasks:
        print(f"\nTask record keys: {list(tasks[0].keys())}")
        print("\nFirst 10 task descriptions:")
        for task in tasks[:10]:
            print(f"  task_index={task.get('task_index')}: {task.get('task')!r}")

        unique_descriptions = sorted({t.get("task", "") for t in tasks})
        print(f"\nUnique task descriptions: {len(unique_descriptions)}")
        print("Sample of unique descriptions:")
        for description in unique_descriptions[:30]:
            print(f"  - {description}")

    inspection_report["tasks_summary"] = {
        "total_task_definitions": len(tasks),
        "unique_descriptions_count": len({t.get("task", "") for t in tasks}),
        "sample_descriptions": [t.get("task") for t in tasks[:20]],
    }
else:
    print("WARN: meta/tasks.jsonl not found.")
    inspection_report["tasks_summary"] = None

# %% [markdown]
"""
### 4c: Inspect episodes.jsonl

Episode-level metadata: which task each episode performs, length, any
extra annotations.
"""

# %%
episodes_path = meta_local_paths.get("meta/episodes.jsonl")
episodes: list[dict] = []

if episodes_path and episodes_path.exists():
    with open(episodes_path) as file_handle:
        for line in file_handle:
            line = line.strip()
            if line:
                episodes.append(json.loads(line))

    print(f"Total episodes in metadata: {len(episodes)}")

    if episodes:
        print(f"\nEpisode record keys: {list(episodes[0].keys())}")
        print(f"\nFirst episode sample:")
        print(json.dumps(episodes[0], indent=2)[:600])

        lengths = [ep.get("length", 0) for ep in episodes if ep.get("length")]
        if lengths:
            print(f"\nEpisode length stats (frames):")
            print(f"  min:    {min(lengths)}")
            print(f"  median: {statistics.median(lengths):.0f}")
            print(f"  mean:   {statistics.mean(lengths):.1f}")
            print(f"  max:    {max(lengths)}")

            fps = info.get("fps")
            if fps:
                print(f"\nAt {fps} fps, episode duration (seconds):")
                print(f"  min:    {min(lengths) / fps:.2f}")
                print(f"  median: {statistics.median(lengths) / fps:.2f}")
                print(f"  mean:   {statistics.mean(lengths) / fps:.2f}")
                print(f"  max:    {max(lengths) / fps:.2f}")

    inspection_report["episodes_summary"] = {
        "total_episodes_in_metadata": len(episodes),
        "first_episode_keys": list(episodes[0].keys()) if episodes else [],
        "length_stats_frames": (
            {
                "min": min(lengths),
                "median": statistics.median(lengths),
                "mean": statistics.mean(lengths),
                "max": max(lengths),
            }
            if episodes and lengths
            else None
        ),
    }
else:
    print("WARN: meta/episodes.jsonl not found.")
    inspection_report["episodes_summary"] = None

# %% [markdown]
"""
## Step 5: Download a sample of episode parquets

Download only `SAMPLE_EPISODE_LIMIT` episodes to inspect per-frame schema
and data quality. This is the moment of truth for the feature extraction
spec.
"""

# %%
sample_data_files = data_files[:SAMPLE_EPISODE_LIMIT]
sample_local_paths: list[Path] = []

for data_file in sample_data_files:
    local_path = hf_hub_download(
        repo_id=DATASET_REPO_ID,
        filename=data_file,
        repo_type="dataset",
        revision=pinned_revision_sha,
        local_dir=str(LOCAL_CACHE_DIR),
    )
    sample_local_paths.append(Path(local_path))
    size_mb = Path(local_path).stat().st_size / (1024 * 1024)
    print(f"Downloaded: {data_file} ({size_mb:.2f} MB)")

# %% [markdown]
"""
### 5a: Inspect first episode parquet

Load with polars for memory efficiency. Check actual columns, dtypes, and
sample values.
"""

# %%
import polars as pl

if sample_local_paths:
    first_episode_df = pl.read_parquet(sample_local_paths[0])

    print(f"Episode shape: {first_episode_df.shape}")
    print(f"Total columns: {len(first_episode_df.columns)}")
    print("\nAll columns with dtypes:")
    for column_name, dtype in zip(first_episode_df.columns, first_episode_df.dtypes):
        print(f"  {column_name:40s} {dtype}")

    print("\nFirst 3 rows (truncated):")
    with pl.Config(tbl_cols=8, tbl_width_chars=120, fmt_str_lengths=40):
        print(first_episode_df.head(3))

    inspection_report["episode_parquet_schema"] = {
        "shape": list(first_episode_df.shape),
        "columns": first_episode_df.columns,
        "dtypes": [str(d) for d in first_episode_df.dtypes],
    }
else:
    print("WARN: No episode parquets downloaded.")
    inspection_report["episode_parquet_schema"] = None

# %% [markdown]
"""
### 5b: Inspect vector-valued columns

LeRobot stores `action` and `observation.state` as float arrays (often
serialized as lists or fixed-shape arrays). Confirm dimensionality and
sanity-check value ranges.
"""

# %%
if sample_local_paths:
    candidate_vector_columns = [
        column_name for column_name in first_episode_df.columns
        if "action" in column_name.lower() or "state" in column_name.lower()
    ]

    print(f"Candidate vector columns: {candidate_vector_columns}")

    for column_name in candidate_vector_columns:
        first_value = first_episode_df[column_name][0]
        print(f"\nColumn: {column_name}")
        print(f"  Python type: {type(first_value).__name__}")

        if hasattr(first_value, "__len__"):
            print(f"  Length: {len(first_value)}")
            try:
                preview = list(first_value)[:6]
                print(f"  First 6 elements: {preview}")
            except Exception as exc:
                print(f"  Could not preview elements: {exc}")
        else:
            print(f"  Scalar value: {first_value}")

# %% [markdown]
"""
### 5c: Check for success / failure labels

Module 1 needs a success label per episode. Either Unitree provides one
(in episodes.jsonl or per-frame in the parquet) or we infer it. This
cell determines which case we are in.
"""

# %%
SUCCESS_KEY_CANDIDATES = ["success", "succeeded", "is_success", "task_success"]

success_in_episode_meta = False
if episodes:
    success_keys_found = [
        k for k in episodes[0].keys()
        if any(candidate in k.lower() for candidate in SUCCESS_KEY_CANDIDATES)
    ]
    if success_keys_found:
        success_in_episode_meta = True
        print(f"Success-related keys in episodes.jsonl: {success_keys_found}")

success_in_parquet = False
if sample_local_paths:
    success_columns_found = [
        c for c in first_episode_df.columns
        if any(candidate in c.lower() for candidate in SUCCESS_KEY_CANDIDATES)
    ]
    if success_columns_found:
        success_in_parquet = True
        print(f"Success-related columns in parquet: {success_columns_found}")

if not success_in_episode_meta and not success_in_parquet:
    print("NO explicit success label found.")
    print("Module 1 must INFER success from trajectory completion / teleop signals.")
    print("This is a known limitation to document in the README.")

inspection_report["success_label_availability"] = {
    "in_episodes_metadata": success_in_episode_meta,
    "in_episode_parquets": success_in_parquet,
}

# %% [markdown]
"""
### 5d: Check for payload, reach, and energy fields

Almost certainly NOT present as direct fields. If we are right, Module 1
must estimate these from trajectory geometry plus visual inspection.
"""

# %%
PHYSICAL_ATTRIBUTE_KEYWORDS = [
    "payload", "mass", "weight", "reach", "energy", "power", "force", "torque"
]

physical_attribute_columns: dict[str, list[str]] = {}
if sample_local_paths:
    for keyword in PHYSICAL_ATTRIBUTE_KEYWORDS:
        matches = [
            c for c in first_episode_df.columns if keyword in c.lower()
        ]
        if matches:
            physical_attribute_columns[keyword] = matches

if physical_attribute_columns:
    print("Physical attribute columns found:")
    for keyword, columns in physical_attribute_columns.items():
        print(f"  {keyword}: {columns}")
else:
    print("No direct payload / mass / reach / energy columns.")
    print("Module 1 must estimate these as documented in the spec.")

inspection_report["physical_attributes_direct"] = physical_attribute_columns

# %% [markdown]
"""
## Step 6: Map sample tasks to the proposed taxonomy

Run a dry-run of the rules-based taxonomy mapper against the actual task
descriptions. The coverage rate determines whether the manual review
step in Module 1 is small (good) or huge (bad, refactor needed).
"""

# %%
# Proposed v0.1 taxonomy rules. These ARE the draft mapper.
TAXONOMY_KEYWORD_RULES: dict[str, list[str]] = {
    "pick_small_object": ["pick up small", "grasp small", "pick the cup", "pick the bottle"],
    "pick_medium_object": ["pick up", "grasp", "lift", "take the"],
    "pick_large_object": ["lift large", "carry large", "two-handed", "bimanual lift"],
    "transport_short": ["move to", "place on", "transfer to", "hand over"],
    "transport_long": ["walk to", "carry to", "navigate", "deliver"],
    "place_precise": ["place precisely", "insert", "slot", "align"],
    "place_general": ["drop", "release", "place in"],
    "bimanual_handling": ["both hands", "two hands", "bimanual"],
}


def classify_task_draft(description: str) -> str:
    """Draft taxonomy mapper. Returns category name or 'unclassified'."""
    if not description:
        return "unclassified"
    description_lower = description.lower()
    matches: list[str] = []
    for category_name, keywords in TAXONOMY_KEYWORD_RULES.items():
        for keyword in keywords:
            if keyword in description_lower:
                matches.append(category_name)
                break
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return f"ambiguous:{','.join(matches)}"
    return "unclassified"


if tasks:
    classification_counts: dict[str, int] = {}
    sample_unclassified: list[str] = []
    sample_ambiguous: list[tuple[str, str]] = []

    for task_record in tasks:
        description = task_record.get("task", "")
        category = classify_task_draft(description)
        classification_counts[category] = classification_counts.get(category, 0) + 1

        if category == "unclassified" and len(sample_unclassified) < 15:
            sample_unclassified.append(description)
        elif category.startswith("ambiguous") and len(sample_ambiguous) < 10:
            sample_ambiguous.append((description, category))

    total_tasks = len(tasks)
    classified_count = sum(
        count for category, count in classification_counts.items()
        if category not in ("unclassified",) and not category.startswith("ambiguous")
    )

    print(f"Total tasks classified:           {total_tasks}")
    print(f"Cleanly classified:               {classified_count} ({100 * classified_count / total_tasks:.1f}%)")
    print(f"Unclassified:                     {classification_counts.get('unclassified', 0)}")
    print(f"Ambiguous (multiple categories):  {sum(c for k, c in classification_counts.items() if k.startswith('ambiguous'))}")

    print("\nBreakdown by category:")
    for category, count in sorted(classification_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {category:50s} {count:4d}")

    print("\nSample unclassified task descriptions:")
    for description in sample_unclassified:
        print(f"  - {description}")

    print("\nSample ambiguous classifications:")
    for description, category in sample_ambiguous:
        print(f"  - [{category}] {description}")

    inspection_report["taxonomy_dry_run"] = {
        "total_tasks": total_tasks,
        "cleanly_classified_count": classified_count,
        "coverage_pct": 100 * classified_count / total_tasks if total_tasks else 0,
        "category_counts": classification_counts,
        "sample_unclassified": sample_unclassified,
    }
else:
    print("No tasks loaded; skipping taxonomy dry-run.")
    inspection_report["taxonomy_dry_run"] = None

# %% [markdown]
"""
## Step 7: Write the inspection report

Persist findings to JSON. The Module 1 spec refactor consumes this file.
"""

# %%
with open(INSPECTION_REPORT_PATH, "w") as file_handle:
    json.dump(inspection_report, file_handle, indent=2, default=str)

print(f"Inspection report written: {INSPECTION_REPORT_PATH.resolve()}")
print(f"Report size: {INSPECTION_REPORT_PATH.stat().st_size / 1024:.1f} KB")

# %% [markdown]
"""
## Step 8: Decision checklist

After running this notebook, answer these questions before touching the
Module 1 spec or any production code.

1. **Dataset accessibility:** does it download without authentication?
   - If yes: proceed.
   - If no: document the auth step and add it to README installation.

2. **Episode count:** how many episodes does the dataset actually contain?
   - If < 50: the project is data-starved. Reconsider scope.
   - If 50 to 500: viable for v1.0.
   - If > 500: rich, but be selective about which subset you process.

3. **Task description quality:** are descriptions free-form or templated?
   - Templated (Unitree's task index has structure): taxonomy mapper is easy.
   - Free-form: expect heavy manual review.

4. **Taxonomy coverage:** what percent of tasks did the draft mapper classify cleanly?
   - >= 70%: keep the proposed taxonomy; refine rules.
   - 40 to 70%: rebuild taxonomy categories from actual descriptions.
   - < 40%: completely rework the taxonomy from observed data first.

5. **Success label:** is it provided directly?
   - Yes: simpler Module 1.
   - No: design and document the inference heuristic.

6. **Action and state dimensionality:** does it match a humanoid?
   - Unitree G1 has ~37 actuated DOF. The action vector should be in that range.
   - Mismatch means we are not looking at G1 data.

7. **Video presence:** do video files exist? Total size?
   - If yes and tractable: useful for manual review thumbnails.
   - If too large: skip video, work from parquet only.

## Next action

Update `module_01_capability_extraction.md` to reflect what this notebook
found. The spec is currently based on assumptions. After this notebook
runs, it is based on facts.
"""
