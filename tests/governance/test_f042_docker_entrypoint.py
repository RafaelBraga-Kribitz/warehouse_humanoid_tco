"""F-042 — ci.yml Docker smoke test must not override --entrypoint python."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PATTERN = re.compile(r"--entrypoint\s+python")


def test_no_entrypoint_override() -> None:
    if not CI.exists():
        ratchet("F-042", fixed=True, gap_msg="ci.yml absent — vacuously fixed")
        return
    text = CI.read_text()
    hit = bool(PATTERN.search(text))
    ratchet(
        "F-042",
        fixed=not hit,
        gap_msg="ci.yml still overrides --entrypoint python in Docker smoke test",
    )
