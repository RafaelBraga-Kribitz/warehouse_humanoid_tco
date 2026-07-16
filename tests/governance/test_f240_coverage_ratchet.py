"""F-240 — coverage fail-under ratchet to ≥90%."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_f240_cov_fail_under_at_least_90() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"cov-fail-under=(\d+)", text)
    assert match is not None, "cov-fail-under missing from pyproject.toml"
    threshold = int(match.group(1))
    assert threshold >= 90, f"cov-fail-under={threshold} must be >= 90"

    assert 'omit = ["*/tests/*", "*/__main__.py"]' in text
    # No broad pipeline omits used to fake the threshold
    assert "module_01_capability_extraction" not in text.split("[tool.coverage.run]", 1)[1]

    f235 = (ROOT / "governance" / "findings" / "F-235.yaml").read_text(encoding="utf-8")
    assert "cov-fail-under=90" in f235 or "cov-fail-under>=90" in f235
    assert "FINAL THRESHOLD" in f235 or "FINAL:" in f235
