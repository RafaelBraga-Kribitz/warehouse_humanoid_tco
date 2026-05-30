"""F-038 — DASHBOARD_SETUP.md must not contain 3-branch IF(...) DAX."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

DOC = REPO_ROOT / "docs" / "DASHBOARD_SETUP.md"
INVALID_IF = re.compile(r"IF\(\s*[^,()]+,\s*[^,()]+,\s*[^,()]+,\s*[^,()]+\)")


def test_no_invalid_dax_if() -> None:
    if not DOC.exists():
        ratchet("F-038", fixed=True, gap_msg="DASHBOARD_SETUP.md absent — vacuously fixed")
        return
    text = DOC.read_text()
    hits = INVALID_IF.findall(text)
    ratchet(
        "F-038",
        fixed=not hits,
        gap_msg=f"3-branch DAX IF still present: {hits[:2]}",
    )
