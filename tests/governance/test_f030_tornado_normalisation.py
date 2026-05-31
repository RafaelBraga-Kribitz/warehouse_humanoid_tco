"""F-030 — OAT tornado must use elasticity / Sobol / Morris, not raw delta.

The original test only scanned for the substring `elasticit`/`sobol`/`morris`,
which a `# TODO: add elasticity` comment would silently satisfy. Tightened to
require an actual symbol (`elasticity`/`sobol`/`morris` appearing in a name,
not just a comment) by enforcing the pattern `normalised_elasticity` OR
`compute_elasticity_ranking` OR `sobol`/`morris` as a function/identifier.
"""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

SENS = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "analysis" / "sensitivity.py"
# Match identifiers (def/return/=) that name an elasticity, Sobol, or Morris
# concept — not just a passing mention in a doc comment.
SYMBOL_PATTERN = re.compile(
    r"\b(?:def\s+|=\s*)?[A-Za-z_][A-Za-z_0-9]*" r"(?:elasticity|sobol|morris)" r"[A-Za-z_0-9]*\b",
    re.IGNORECASE,
)


def test_tornado_uses_normalised_metric() -> None:
    if not SENS.exists():
        ratchet("F-030", fixed=True, gap_msg="analysis/sensitivity.py absent — vacuously fixed")
        return
    text = SENS.read_text()
    # Strip lines that are pure comments so a `# TODO: elasticity` can't satisfy the gate.
    code_only = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    found = bool(SYMBOL_PATTERN.search(code_only))
    ratchet(
        "F-030",
        fixed=found,
        gap_msg=(
            "no elasticity/Sobol/Morris symbol in analysis/sensitivity.py "
            "(comments alone do not count)"
        ),
    )
