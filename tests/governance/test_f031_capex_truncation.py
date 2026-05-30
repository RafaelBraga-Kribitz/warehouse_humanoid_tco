"""F-031 — humanoid_capex_eur distribution must be truncated or lognormal."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

SENS = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "analysis" / "sensitivity.py"
_SAFE = r'humanoid_capex_eur[^\n]*"(truncnorm|truncated_normal|lognormal)"'
SAFE_PATTERN = re.compile(_SAFE, re.IGNORECASE)
NAIVE_PATTERN = re.compile(r'humanoid_capex_eur[^\n]*"type":\s*"normal"', re.IGNORECASE)


def test_capex_not_naive_normal() -> None:
    if not SENS.exists():
        ratchet("F-031", fixed=True, gap_msg="analysis/sensitivity.py absent — vacuously fixed")
        return
    text = SENS.read_text()
    is_safe = bool(SAFE_PATTERN.search(text))
    is_naive = bool(NAIVE_PATTERN.search(text))
    ratchet(
        "F-031",
        fixed=is_safe or not is_naive,
        gap_msg="humanoid_capex_eur still naive Normal without truncation/lognormal",
    )
