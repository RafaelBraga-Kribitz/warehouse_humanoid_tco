"""Shared stub helper for Phase 0 check_*.py scripts.

Phase 0 establishes the audit pipeline scaffolding: every check_*.py script
exists and is wired into `make audit`, but each one only logs "stub: not yet
implemented" and exits 0. Phase 1 replaces each stub with the real check.

This shared helper avoids 15 near-identical files and gives the Phase 1 author
a single place to see all the stubs to implement.

Phase 1 plan reference:
  /root/.claude/plans/system-reminder-you-re-running-in-glistening-frog.md
  governance/AUDIT_PROCEDURE.md
"""

from __future__ import annotations

import sys


def stub(script_name: str, finding_id: str | None, phase_due: str = "Phase 1") -> int:
    """Print stub marker and exit 0.

    Args:
        script_name: bare filename, e.g. "check_charter_size.py".
        finding_id: the F-NNN that drives this check, or None for cross-cutting.
        phase_due: which phase the real implementation arrives in.

    Returns:
        Always 0 in Phase 0. Phase 1 replaces this with real check logic that
        may return non-zero.
    """
    finding = f" (finding: {finding_id})" if finding_id else ""
    print(f"[stub] {script_name}: not yet implemented — due {phase_due}{finding}")
    return 0


def main_stub(script_name: str, finding_id: str | None = None) -> None:
    """Stub entry point — exits the process with the stub return code."""
    sys.exit(stub(script_name, finding_id))
