"""F-025 — data/raw/MANIFEST.yaml entries must carry real revision_sha + access_date."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

MANIFEST = REPO_ROOT / "data" / "raw" / "MANIFEST.yaml"
NULL_FIELDS = ("revision_sha", "access_date", "snapshot_date")


def test_no_null_provenance_fields() -> None:
    if not MANIFEST.exists():
        ratchet("F-025", fixed=True, gap_msg="MANIFEST absent — vacuously fixed")
        return
    text = MANIFEST.read_text()
    hits = [f for f in NULL_FIELDS if re.search(rf"^\s*{f}:\s*null", text, re.MULTILINE)]
    ratchet(
        "F-025",
        fixed=not hits,
        gap_msg=f"null provenance fields in raw MANIFEST: {hits}",
    )
