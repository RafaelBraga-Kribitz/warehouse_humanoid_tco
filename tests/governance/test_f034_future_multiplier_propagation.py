"""F-034 — humanoid_throughput_multiplier must reach the TCO pipeline, or be removed."""

from __future__ import annotations

from _ratchet import REPO_ROOT, ratchet

BASELINE = REPO_ROOT / "config" / "autostore_baseline.yaml"
TCO_FILES = (
    REPO_ROOT / "src" / "warehouse_humanoid_tco" / "pipelines" / "module_03_tco.py",
    REPO_ROOT / "src" / "warehouse_humanoid_tco" / "models" / "tco.py",
)
KEY = "humanoid_throughput_multiplier"


def test_multiplier_reaches_tco_or_is_removed() -> None:
    declared = False
    if BASELINE.exists():
        declared = KEY in BASELINE.read_text()
    if not declared:
        ratchet("F-034", fixed=True, gap_msg="multiplier removed from baseline")
        return
    referenced = any(p.exists() and KEY in p.read_text() for p in TCO_FILES)
    ratchet(
        "F-034",
        fixed=referenced,
        gap_msg=f"{KEY} declared in baseline but not referenced by module_03_tco or models/tco",
    )
