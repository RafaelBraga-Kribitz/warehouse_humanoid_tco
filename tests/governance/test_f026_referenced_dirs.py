"""F-026 — every local_dir referenced in data/raw/MANIFEST.yaml must exist."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

MANIFEST = REPO_ROOT / "data" / "raw" / "MANIFEST.yaml"


def test_referenced_dirs_exist() -> None:
    if not MANIFEST.exists():
        ratchet("F-026", fixed=True, gap_msg="MANIFEST absent — vacuously fixed")
        return
    text = MANIFEST.read_text()
    refs = re.findall(r'local_dir:\s*"([^"]+)"', text)
    missing = [r for r in refs if not (REPO_ROOT / r).exists()]
    ratchet(
        "F-026",
        fixed=not missing,
        gap_msg=f"manifest references missing dirs: {missing}",
    )
