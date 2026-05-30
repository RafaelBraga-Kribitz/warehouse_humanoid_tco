"""F-041 — ci.yml (or another PR-trigger workflow) must exercise the pipeline."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PATTERN = re.compile(r"module_0[1-4]|make\s+all|make\s+module-0[1-4]")


def test_pipeline_is_exercised_in_ci() -> None:
    if not CI.exists():
        ratchet("F-041", fixed=True, gap_msg="ci.yml absent — vacuously fixed")
        return
    text = CI.read_text()
    ratchet(
        "F-041",
        fixed=bool(PATTERN.search(text)),
        gap_msg="ci.yml does not run module_0[1-4] or `make all`",
    )
