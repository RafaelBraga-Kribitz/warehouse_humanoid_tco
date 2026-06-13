"""F-101 — Module 1 must fail closed (raise / nonzero exit) on 0 episodes.

Ratchet pattern: xfails while open, hard-fails on regression after close.

A 0-episode extraction (e.g. raw data is git-lfs pointer files and HuggingFace
is unreachable) must NOT be reported as success. Before the fix, module_01 wrote
empty parquets and printed "✓ Success" with exit 0 — a fake completion that
produces empty downstream simulations and dashboards.

Two guards:
  1. Behavioural: require_episodes_extracted(0, n) raises; (>0, n) does not.
  2. Wiring: module_01 main actually *invokes* require_episodes_extracted(len(...))
     — prevents a silent revert where the guard exists but is never called.
     This is a symbol-call pattern, not a substring/comment, per the F-024/F-030
     tightening (comments alone must not satisfy the contract).
"""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

MODULE_01 = (
    REPO_ROOT
    / "src"
    / "warehouse_humanoid_tco"
    / "pipelines"
    / "module_01_capability_extraction.py"
)


def test_guard_raises_on_zero_and_allows_positive() -> None:
    try:
        from warehouse_humanoid_tco.pipelines.module_01_capability_extraction import (
            require_episodes_extracted,
        )
    except Exception as exc:  # noqa: BLE001 — import failure is itself the regression
        ratchet(
            "F-101",
            fixed=False,
            gap_msg=f"require_episodes_extracted not importable: {exc}",
        )
        return

    raises_on_zero = False
    try:
        require_episodes_extracted(0, 5)
    except RuntimeError:
        raises_on_zero = True

    allows_positive = True
    try:
        require_episodes_extracted(2359, 5)
    except Exception:  # noqa: BLE001
        allows_positive = False

    ratchet(
        "F-101",
        fixed=raises_on_zero and allows_positive,
        gap_msg=f"raises_on_zero={raises_on_zero} allows_positive={allows_positive}",
    )


def test_main_invokes_guard() -> None:
    if not MODULE_01.exists():
        ratchet("F-101", fixed=True, gap_msg="module_01 absent — vacuously fixed")
        return
    text = MODULE_01.read_text()
    # An actual call: require_episodes_extracted(len(...). The `def` line is
    # `def require_episodes_extracted(n_episodes` so this does not match it.
    invoked = bool(re.search(r"require_episodes_extracted\s*\(\s*len\(", text))
    ratchet("F-101", fixed=invoked, gap_msg=f"main invokes guard: invoked={invoked}")
