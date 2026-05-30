"""F-039 — DASHBOARD_SETUP.md must not cite the stale Best NPV €-924,125 figure."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

DOC = REPO_ROOT / "docs" / "DASHBOARD_SETUP.md"
STALE_PATTERN = re.compile(r"924[,]?125|-924125")


def test_no_stale_best_npv() -> None:
    if not DOC.exists():
        ratchet("F-039", fixed=True, gap_msg="DASHBOARD_SETUP.md absent — vacuously fixed")
        return
    text = DOC.read_text()
    hit = bool(STALE_PATTERN.search(text))
    ratchet(
        "F-039",
        fixed=not hit,
        gap_msg='stale "Best NPV €-924,125" still cited',
    )
