"""F-029 — sensitivity.py must not call output quantiles a "90% CI"."""

from __future__ import annotations

from _ratchet import REPO_ROOT, ratchet

SENS = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "analysis" / "sensitivity.py"


def test_no_ci_mislabel() -> None:
    if not SENS.exists():
        ratchet("F-029", fixed=True, gap_msg="analysis/sensitivity.py absent — vacuously fixed")
        return
    text = SENS.read_text()
    hit = "90% CI:" in text
    ratchet(
        "F-029",
        fixed=not hit,
        gap_msg='sensitivity.py still prints "90% CI:" for empirical quantiles',
    )
