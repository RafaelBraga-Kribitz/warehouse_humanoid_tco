"""F-027 — simulation per-line service time must not be naive truncated-Normal."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

SIM = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "models" / "simulation.py"
NAIVE_PATTERN = re.compile(r"rng\.normal\(\s*profile\.cycle_time_mean")


def test_no_naive_normal_service_time() -> None:
    if not SIM.exists():
        ratchet("F-027", fixed=True, gap_msg="simulation.py absent — vacuously fixed")
        return
    text = SIM.read_text()
    hit = bool(NAIVE_PATTERN.search(text))
    ratchet(
        "F-027",
        fixed=not hit,
        gap_msg="simulation still uses rng.normal(cycle_time_mean, cycle_time_std)",
    )
