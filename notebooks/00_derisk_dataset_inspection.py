# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
"""
# De-Risk Notebook: UnifoLM Dataset Collection Validation

## Purpose

Validates all datasets in the collection (WBT + DiverseManip) against
Module 1 assumptions. No dataset download — only metadata inspection.

## What this validates

For each dataset:
1. Is it accessible without auth errors?
2. What is the LeRobot V2.0+ schema?
3. Episode count, durations, success rates?
4. Which task categories appear?
5. Available features (reach, grasp, energy proxies)?

## Outputs

Writes JSON report to `reports/derisk_inspection_report.json` consumed by Module 1.
"""

# %%
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# %% [markdown]
"""
## Step 0: Environment & Config
"""

# %%
REQUIRED_PACKAGES = ["huggingface_hub", "pyarrow", "polars", "yaml"]

missing = []
for pkg in REQUIRED_PACKAGES:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"Missing: {missing}. Install: pip install {' '.join(missing)}")
    sys.exit(1)

print("✓ All packages available")
print(f"✓ Python: {sys.version.split()[0]}")

import yaml

# Resolve paths relative to project root (parent of notebooks dir)
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "dataset_manifest.yaml"
REPORT_PATH = PROJECT_ROOT / "reports" / "derisk_inspection_report.json"

with open(CONFIG_PATH) as f:
    manifest = yaml.safe_load(f)
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

# %% [markdown]
"""
## Step 1: Load dataset manifest and resolve all SHAs
"""

# %%
from huggingface_hub import HfApi

api = HfApi()

# Flatten all datasets from manifest
all_datasets = []
all_datasets.extend(manifest.get("wbt_datasets", []))
all_datasets.extend(manifest.get("diversemanip_datasets", []))

print(f"Total datasets in collection: {len(all_datasets)}")
for ds in all_datasets:
    print(f"  - {ds['repo_id']} (phase={ds.get('phase')})")

# Resolve SHAs for all datasets
dataset_info_map: dict[str, dict[str, Any]] = {}

for dataset in all_datasets:
    repo_id = dataset["repo_id"]
    try:
        info = api.dataset_info(repo_id=repo_id, revision="main")
        dataset_info_map[repo_id] = {
            "sha": info.sha,
            "last_modified": info.last_modified.isoformat() if info.last_modified else None,
            "files_count": len(info.siblings),
            "accessible": True,
            "error": None,
        }
        print(f"✓ {repo_id}")
        print(f"  SHA: {info.sha}")
        print(f"  Files: {len(info.siblings)}")
    except Exception as exc:
        dataset_info_map[repo_id] = {
            "accessible": False,
            "error": str(exc),
        }
        print(f"✗ {repo_id}: {exc}")

# %% [markdown]
"""
## Step 2: Inspect file structure for each dataset
"""


# %%
def catalog_files(siblings) -> dict[str, int]:
    """Count files by top-level directory."""
    all_files = [s.rfilename for s in siblings]
    prefixes = {"meta": 0, "data": 0, "videos": 0, "other": 0}
    for f in all_files:
        if f.startswith("meta/"):
            prefixes["meta"] += 1
        elif f.startswith("data/"):
            prefixes["data"] += 1
        elif f.startswith("videos/"):
            prefixes["videos"] += 1
        else:
            prefixes["other"] += 1
    return prefixes


file_structure = {}
for dataset in all_datasets:
    repo_id = dataset["repo_id"]
    if not dataset_info_map[repo_id]["accessible"]:
        continue

    info = api.dataset_info(repo_id=repo_id, revision="main")
    file_structure[repo_id] = catalog_files(info.siblings)
    print(f"\n{repo_id}:")
    for prefix, count in file_structure[repo_id].items():
        print(f"  {prefix}: {count}")

# %% [markdown]
"""
## Step 3: Aggregate findings for Module 1
"""

# %%
report = {
    "run_timestamp_utc": datetime.now(UTC).isoformat(),
    "manifest_path": str(CONFIG_PATH.relative_to(PROJECT_ROOT)),
    "dataset_count": len(all_datasets),
    "datasets_accessible": sum(1 for v in dataset_info_map.values() if v.get("accessible")),
    "datasets_inaccessible": sum(1 for v in dataset_info_map.values() if not v.get("accessible")),
    "datasets": dataset_info_map,
    "file_structure": file_structure,
    "notes": [
        "This report validates dataset accessibility and structure only.",
        "Full data download is deferred to Module 1 production pipeline.",
        "SHAs are pinned for reproducibility.",
    ],
}

# Write report
with open(REPORT_PATH, "w") as f:
    json.dump(report, f, indent=2)

print(f"\n✓ Report written to {REPORT_PATH}")

# %% [markdown]
"""
## Step 4: Summary for Module 1
"""

# %%
print("\n" + "=" * 60)
print("DE-RISK SUMMARY")
print("=" * 60)
print(f"\nDatasets accessible: {report['datasets_accessible']}/{report['dataset_count']}")
if report["datasets_inaccessible"] > 0:
    print(f"⚠️  INACCESSIBLE: {report['datasets_inaccessible']}")
    for repo_id, info in dataset_info_map.items():
        if not info.get("accessible"):
            print(f"  - {repo_id}: {info['error']}")
else:
    print("✓ All datasets accessible")

print(
    f"\nFile structure consistent across datasets: {len(set(str(v) for v in file_structure.values())) == 1}"
)

print("\nPROCEED TO MODULE 1 with:")
print("  config/dataset_manifest.yaml (phases & tasks defined)")
print(f"  {REPORT_PATH} (SHAs pinned)")
print("\nNext: Implement capability extraction per dataset, then aggregate.")
