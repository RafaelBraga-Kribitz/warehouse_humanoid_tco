"""Shared helpers for the Phase 1 governance check_*.py scripts.

Ratchet model
-------------
Every check evaluates the real condition now — there are no stubs left. The
*exit code* is gated by the linked finding's status so that `make audit` and
`make verify` stay green while Phases 1-5 are still in flight:

  finding closed / closed_historical  -> ENFORCE: a violation exits 1 (regression)
  finding open / in_progress          -> MEASURE: a violation exits 0 (known gap)
  no linked finding (finding_id=None)  -> ENFORCE: structural invariants of the
                                          governance system itself always hold

A check with no violation always prints PASS and exits 0. The moment a finding
flips to `closed` in its remediation phase, its gate begins blocking
regressions automatically, and scripts/check_closed_findings.py (the Adversary)
re-runs every closed finding's verification_script on each PR.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
FINDINGS_DIR = REPO_ROOT / "governance" / "findings"

ENFORCING_STATUSES = {"closed", "closed_historical"}


def finding_status(finding_id: str | None) -> str | None:
    """Return the status string for a finding, or None if unknown/absent."""
    if not finding_id:
        return None
    path = FINDINGS_DIR / f"{finding_id}.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("status")


def is_enforcing(finding_id: str | None) -> bool:
    """True when a violation should fail the build.

    Structural invariants (finding_id is None) always enforce. Finding-linked
    checks enforce only once the finding is closed.
    """
    if finding_id is None:
        return True
    return finding_status(finding_id) in ENFORCING_STATUSES


def gate(
    check_name: str,
    finding_id: str | None,
    *,
    ok: bool,
    ok_msg: str,
    gap_msg: str,
) -> int:
    """Print a PASS / FAIL / GAP line and return the process exit code."""
    if ok:
        print(f"[PASS] {check_name}: {ok_msg}")
        return 0
    if is_enforcing(finding_id):
        tag = finding_id or "structural"
        print(f"[FAIL] {check_name} ({tag} enforcing — regression): {gap_msg}")
        return 1
    print(f"[GAP]  {check_name} ({finding_id} open — tracked, due later phase): {gap_msg}")
    return 0
