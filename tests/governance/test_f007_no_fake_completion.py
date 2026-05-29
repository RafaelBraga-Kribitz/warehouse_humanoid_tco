"""F-007 — no fake completion: no workflow escape hatches; manifest pins sha256.

(1) .github/workflows/ must not swallow test exit codes via `|| echo` / `2>/dev/null`.
(2) every dataset_manifest entry must carry a sha256.
Closure spans Phase 4 (remove escape hatch) and Phase 5 (populate sha256).
"""

from __future__ import annotations

import re

import yaml
from _ratchet import REPO_ROOT, ratchet

WORKFLOWS = REPO_ROOT / ".github" / "workflows"
MANIFEST = REPO_ROOT / "config" / "dataset_manifest.yaml"
_ESCAPES = re.compile(r"\|\|\s*echo|2>/dev/null")
DATASET_KEYS = ("wbt_datasets", "diversemanip_datasets")


def test_no_workflow_escape_hatches() -> None:
    hits = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if _ESCAPES.search(line):
                hits.append(f"{path.name}:{i}")
    ratchet("F-007", fixed=not hits, gap_msg=f"workflow escape hatches: {hits}")


def test_manifest_entries_have_sha256() -> None:
    data = yaml.safe_load(MANIFEST.read_text()) or {}
    missing = [
        entry.get("repo_id", "?")
        for key in DATASET_KEYS
        for entry in (data.get(key) or [])
        if not entry.get("sha256")
    ]
    ratchet("F-007", fixed=not missing, gap_msg=f"manifest entries missing sha256: {missing}")
