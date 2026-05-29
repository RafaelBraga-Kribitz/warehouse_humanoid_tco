"""F-018 — humanoid MTBF must have one canonical value.

config/autostore_baseline.yaml currently carries two humanoid MTBF figures 50x
apart (agents.humanoid.mtbf_hours: 2000 vs humanoid_operational.mtbf_hours: 40).
Closure (Phase 5) removes the dead one or documents distinct semantics.
"""

from __future__ import annotations

import yaml
from _ratchet import REPO_ROOT, ratchet

BASELINE = REPO_ROOT / "config" / "autostore_baseline.yaml"


def _humanoid_mtbf_values(data: dict) -> list[float]:
    values: list[float] = []
    agents = data.get("agents", {})
    if isinstance(agents, dict):
        humanoid = agents.get("humanoid", {})
        if isinstance(humanoid, dict) and "mtbf_hours" in humanoid:
            values.append(float(humanoid["mtbf_hours"]))
    op = data.get("humanoid_operational", {})
    if isinstance(op, dict) and "mtbf_hours" in op:
        values.append(float(op["mtbf_hours"]))
    return values


def test_single_humanoid_mtbf() -> None:
    data = yaml.safe_load(BASELINE.read_text()) or {}
    values = _humanoid_mtbf_values(data)
    distinct = set(values)
    ratchet(
        "F-018",
        fixed=len(distinct) <= 1,
        gap_msg=f"contradictory humanoid mtbf_hours values: {sorted(distinct)}",
    )
