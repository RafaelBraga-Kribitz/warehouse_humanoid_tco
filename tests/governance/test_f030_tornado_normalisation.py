"""F-030 — OAT tornado must use elasticity / Sobol / Morris, not raw delta."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

SENS = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "analysis" / "sensitivity.py"
NORMALISATION_PATTERN = re.compile(r"sobol|morris|elasticit", re.IGNORECASE)


def test_tornado_uses_normalised_metric() -> None:
    if not SENS.exists():
        ratchet("F-030", fixed=True, gap_msg="analysis/sensitivity.py absent — vacuously fixed")
        return
    text = SENS.read_text()
    found = bool(NORMALISATION_PATTERN.search(text))
    ratchet(
        "F-030",
        fixed=found,
        gap_msg="no Sobol/Morris/elasticity reference in analysis/sensitivity.py",
    )
