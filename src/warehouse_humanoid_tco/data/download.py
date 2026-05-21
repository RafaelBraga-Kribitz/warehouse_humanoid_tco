"""Dataset download utilities.

Downloads UnifoLM-WBT and DiverseManip datasets from Hugging Face Hub with reproducibility guarantees.
See PROJECT_CHARTER.md §6.1 for data source requirements and config/dataset_manifest.yaml for collection.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, snapshot_download


def resolve_revision_sha(repo_id: str, revision: str = "main") -> str:
    """Resolve a branch/tag to its commit SHA for reproducible pinning."""
    api = HfApi()
    info = api.dataset_info(repo_id=repo_id, revision=revision)
    sha = info.sha
    if sha is None:
        raise ValueError(f"Could not resolve SHA for revision {revision!r} in {repo_id}")
    return sha


def download_dataset(
    repo_id: str,
    revision_sha: str,
    local_dir: Path,
    *,
    token: str | None = None,
) -> Path:
    """Download a single dataset to local_dir.

    Always pin revision_sha — never pass 'main' here.
    """
    if revision_sha == "main" or not revision_sha.startswith(tuple("0123456789abcdef")):
        raise ValueError(
            f"revision_sha must be a pinned commit SHA, not {revision_sha!r}. "
            "Run resolve_revision_sha() first."
        )

    local_path = snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        revision=revision_sha,
        local_dir=str(local_dir),
        token=token,
    )
    return Path(local_path)


def download_dataset_collection(
    datasets: list[dict[str, Any]],
    base_dir: Path,
    *,
    token: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Download a collection of datasets, resolving SHAs and tracking provenance.

    Args:
        datasets: List of dicts with 'repo_id' and optional 'task_category', 'phase'
        base_dir: Root directory for all datasets
        token: HF token for auth

    Returns:
        Dict mapping repo_id → {sha, local_path, task_category, phase}
    """
    provenance = {}
    for entry in datasets:
        repo_id = entry["repo_id"]
        sha = resolve_revision_sha(repo_id, revision="main")
        dataset_dir = base_dir / repo_id.split("/")[1]  # Use dataset name as subdir
        dataset_dir.mkdir(parents=True, exist_ok=True)

        local_path = download_dataset(repo_id, sha, dataset_dir, token=token)
        provenance[repo_id] = {
            "sha": sha,
            "local_path": str(local_path),
            "task_category": entry.get("task_category"),
            "phase": entry.get("phase"),
        }
    return provenance


def sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file for manifest recording."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
