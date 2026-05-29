"""F-003 — exactly one sensitivity module should exist.

models/sensitivity.py and analysis/sensitivity.py currently coexist (incomplete
migration 01-sensitivity-merge). Closure (Phase 5) deletes the deprecated one.
"""

from __future__ import annotations

from _ratchet import REPO_ROOT, ratchet

SRC = REPO_ROOT / "src" / "warehouse_humanoid_tco"


def test_single_sensitivity_module() -> None:
    models = SRC / "models" / "sensitivity.py"
    analysis = SRC / "analysis" / "sensitivity.py"
    present = [p.relative_to(REPO_ROOT) for p in (models, analysis) if p.exists()]
    ratchet(
        "F-003",
        fixed=len(present) <= 1,
        gap_msg=f"dual sensitivity modules present: {[str(p) for p in present]}",
    )
