"""F-032 — transfer_factor floor must be reachable from its sampling range, or removed."""

from __future__ import annotations

import re

import yaml
from _ratchet import REPO_ROOT, ratchet

SENS = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "analysis" / "sensitivity.py"
ASSUMPTIONS = REPO_ROOT / "config" / "tco_assumptions.yaml"


def test_floor_reachable_or_removed() -> None:
    if not SENS.exists():
        ratchet("F-032", fixed=True, gap_msg="sensitivity.py absent — vacuously fixed")
        return
    text = SENS.read_text()
    has_floor = re.search(r"max\(\s*transfer_factor\s*,\s*0?\.05", text) is not None
    if not has_floor:
        ratchet("F-032", fixed=True, gap_msg="floor removed")
        return

    low = None
    if ASSUMPTIONS.exists():
        data = yaml.safe_load(ASSUMPTIONS.read_text()) or {}
        rng = data.get("sensitivity_oat_ranges", {}).get("transfer_factor")
        if isinstance(rng, list) and rng:
            low = float(rng[0])
    if low is None:
        m = re.search(r'transfer_factor[^\n]*"low":\s*([0-9.]+)', text)
        if m:
            low = float(m.group(1))
    if low is None:
        ratchet("F-032", fixed=False, gap_msg="cannot determine transfer_factor low bound")
        return
    ratchet(
        "F-032",
        fixed=low <= 0.05,
        gap_msg=f"floor 0.05 unreachable from low={low}",
    )
