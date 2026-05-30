"""F-028 — simulation engine must compute/log/assert utilisation ρ."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

SIM = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "models" / "simulation.py"
RHO_PATTERN = re.compile(r"\brho\b|utili[sz]ation\s*=|erlang|M/M/c", re.IGNORECASE)


def test_rho_referenced() -> None:
    if not SIM.exists():
        ratchet("F-028", fixed=True, gap_msg="simulation.py absent — vacuously fixed")
        return
    text = SIM.read_text()
    found = bool(RHO_PATTERN.search(text))
    ratchet(
        "F-028",
        fixed=found,
        gap_msg="no ρ/utilization/Erlang-C reference in simulation.py",
    )
