"""F-025 — data/raw/MANIFEST.yaml entries must carry real revision_sha + access_date.

Per Codex feedback on the dropped PR #25: the bare null-ban contract let prose
("see config/dataset_manifest.yaml for per-subset commit SHAs") pass even
though the upstream lineage was still unpinned. This version enforces:
  1. No `null` on revision_sha / access_date / snapshot_date.
  2. revision_sha values must be 40-char hex (HF commit SHA format).
  3. access_date and snapshot_date values must be ISO-8601 dates (YYYY-MM-DD).
"""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

MANIFEST = REPO_ROOT / "data" / "raw" / "MANIFEST.yaml"
NULL_FIELDS = ("revision_sha", "access_date", "snapshot_date")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def test_provenance_fields_are_real() -> None:
    if not MANIFEST.exists():
        ratchet("F-025", fixed=True, gap_msg="MANIFEST absent — vacuously fixed")
        return
    text = MANIFEST.read_text()
    issues: list[str] = []

    for field in NULL_FIELDS:
        if re.search(rf"^\s*{field}:\s*null", text, re.MULTILINE):
            issues.append(f"{field}: null still present")

    for match in re.finditer(r'^\s*revision_sha:\s*"?([^"\s#]+)"?', text, re.MULTILINE):
        value = match.group(1)
        if value != "null" and not SHA_RE.match(value):
            issues.append(f'revision_sha "{value}" is not a 40-char hex commit SHA')

    for field in ("access_date", "snapshot_date"):
        for match in re.finditer(rf'^\s*{field}:\s*"?([^"\s#]+)"?', text, re.MULTILINE):
            value = match.group(1)
            if value != "null" and not DATE_RE.match(value):
                issues.append(f'{field} "{value}" is not ISO-8601 YYYY-MM-DD')

    ratchet(
        "F-025",
        fixed=not issues,
        gap_msg="; ".join(issues),
    )


# Keep the legacy test name as an alias for tooling/CI compatibility.
test_no_null_provenance_fields = test_provenance_fields_are_real
