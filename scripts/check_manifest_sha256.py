"""F-007 — every dataset manifest entry must carry a non-empty sha256.

config/dataset_manifest.yaml keys datasets under `wbt_datasets` and
`diversemanip_datasets` (not `datasets:` — the bug that made
verify_data_integrity.py a no-op). Each entry must pin a sha256 so integrity is
verifiable. Phase 5 populates the real values.
"""

from __future__ import annotations

import sys

import yaml
from _governance_check import REPO_ROOT, gate

MANIFEST = REPO_ROOT / "config" / "dataset_manifest.yaml"
DATASET_KEYS = ("wbt_datasets", "diversemanip_datasets")


def main() -> int:
    data = yaml.safe_load(MANIFEST.read_text()) or {}
    missing: list[str] = []
    total = 0
    for key in DATASET_KEYS:
        for entry in data.get(key, []) or []:
            total += 1
            repo_id = entry.get("repo_id", "?")
            if not entry.get("sha256"):
                missing.append(repo_id)
    ok = total > 0 and not missing
    return gate(
        "check_manifest_sha256.py",
        "F-007",
        ok=ok,
        ok_msg=f"all {total} manifest entries carry a sha256",
        gap_msg=f"{len(missing)}/{total} entries missing sha256",
    )


if __name__ == "__main__":
    sys.exit(main())
