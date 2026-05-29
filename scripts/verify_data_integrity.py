"""Verify SHA256 integrity of cached HuggingFace dataset files.

Reads pinned SHAs from config/dataset_manifest.yaml and compares against
the actual files in data/raw/. Fails loudly on any mismatch.

Usage:
    python scripts/verify_data_integrity.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    project_root = Path(__file__).parent.parent
    manifest_path = project_root / "config" / "dataset_manifest.yaml"

    if not manifest_path.exists():
        print("WARNING: config/dataset_manifest.yaml not found — skipping integrity check")
        sys.exit(0)

    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    # Datasets live under wbt_datasets + diversemanip_datasets, not "datasets".
    # Reading the wrong key previously made this script a silent no-op (F-007).
    dataset_keys = ("wbt_datasets", "diversemanip_datasets")
    datasets = [ds for key in dataset_keys for ds in (manifest.get(key) or [])]
    if not datasets:
        print("No datasets listed in manifest — nothing to verify")
        sys.exit(0)

    failures: list[str] = []
    for ds in datasets:
        name = ds.get("repo_id", ds.get("name", "unknown"))
        pinned_sha = ds.get("sha256")
        rel_path = ds.get("local_path")

        if not pinned_sha or not rel_path:
            continue

        local = project_root / rel_path
        if not local.exists():
            print(f"  SKIP  {name}: not downloaded (expected at {rel_path})")
            continue

        actual = sha256_file(local)
        if actual != pinned_sha:
            failures.append(f"{name}: expected {pinned_sha[:12]}… got {actual[:12]}…")
            print(f"  FAIL  {name}: SHA mismatch")
        else:
            print(f"  OK    {name}")

    if failures:
        print("\nData integrity check FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("\nAll dataset checksums verified.")


if __name__ == "__main__":
    main()
