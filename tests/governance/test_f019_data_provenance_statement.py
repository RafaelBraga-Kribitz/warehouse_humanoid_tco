"""F-019 — README must state data provenance once, tied to the inspection report.

The README's synthetic-vs-real-data narrative must reference
reports/derisk_inspection_report.json so the current provenance is unambiguous
and traceable. Closure in Phase 5.
"""

from __future__ import annotations

from _ratchet import REPO_ROOT, ratchet

README = REPO_ROOT / "README.md"


def test_readme_references_inspection_report() -> None:
    text = README.read_text()
    references_report = "derisk_inspection_report.json" in text
    ratchet(
        "F-019",
        fixed=references_report,
        gap_msg="README does not reference reports/derisk_inspection_report.json",
    )
