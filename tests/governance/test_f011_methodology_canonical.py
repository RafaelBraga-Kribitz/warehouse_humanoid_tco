"""F-011 — a single canonical methodology document must exist.

governance/AUDIT_PROCEDURE.md is the one methodology reference (the antidote to
per-session framework reinvention). It must define the three durable roles.
F-011 closes in Phase 3 once CLAUDE.md routes agents to it.
"""

from __future__ import annotations

from _ratchet import REPO_ROOT

PROCEDURE = REPO_ROOT / "governance" / "AUDIT_PROCEDURE.md"


def test_audit_procedure_defines_three_roles() -> None:
    assert PROCEDURE.is_file(), "governance/AUDIT_PROCEDURE.md must exist"
    text = PROCEDURE.read_text()
    for role in ("Steward", "Remediator", "Adversary"):
        assert role in text, f"AUDIT_PROCEDURE.md must define the {role} role"
