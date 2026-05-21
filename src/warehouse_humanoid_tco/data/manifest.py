"""Manifest utilities for recording data provenance.

Every artifact written by a module updates the processed/MANIFEST.yaml.
See PROJECT_CHARTER.md §6.2 Data Storage Layout.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import yaml


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def record_artifact(
    manifest_path: Path,
    artifact_path: Path,
    pipeline_version: str,
    source_revision_sha: str,
    produced_by: str,
) -> None:
    """Append an artifact entry to the processed MANIFEST.yaml."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = yaml.safe_load(f) or {}
    else:
        manifest = {}

    outputs: list[dict] = manifest.get("outputs", [])

    entry = {
        "artifact": artifact_path.name,
        "pipeline_version": pipeline_version,
        "source_revision_sha": source_revision_sha,
        "produced_by": produced_by,
        "run_timestamp_utc": datetime.now(UTC).isoformat(),
        "sha256": _sha256(artifact_path),
    }

    outputs = [o for o in outputs if o.get("artifact") != artifact_path.name]
    outputs.append(entry)
    manifest["outputs"] = outputs

    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
