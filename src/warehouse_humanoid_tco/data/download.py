"""Dataset download utilities.

Downloads UnifoLM-WBT-Dataset from Hugging Face Hub with reproducibility guarantees.
See PROJECT_CHARTER.md §6.1 for data source requirements.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

DATASET_REPO_ID = "unitreerobotics/UnifoLM-WBT-Dataset"


def resolve_revision_sha(revision: str = "main") -> str:
    """Resolve a branch/tag to its commit SHA for reproducible pinning."""
    api = HfApi()
    info = api.dataset_info(repo_id=DATASET_REPO_ID, revision=revision)
    sha = info.sha
    if sha is None:
        raise ValueError(f"Could not resolve SHA for revision {revision!r}")
    return sha


def download_dataset(
    revision_sha: str,
    local_dir: Path,
    *,
    token: str | None = None,
) -> Path:
    """Download the full dataset shard to local_dir.

    Always pin revision_sha — never pass 'main' here.
    """
    if revision_sha == "main" or not revision_sha.startswith(tuple("0123456789abcdef")):
        raise ValueError(
            f"revision_sha must be a pinned commit SHA, not {revision_sha!r}. "
            "Run resolve_revision_sha() first."
        )

    local_path = snapshot_download(
        repo_id=DATASET_REPO_ID,
        repo_type="dataset",
        revision=revision_sha,
        local_dir=str(local_dir),
        token=token,
    )
    return Path(local_path)


def sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file for manifest recording."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
