"""F-010 — machine-readable audit state must exist and be well-formed.

This contract is satisfied by Phase 0; the test guards it permanently. F-010
closes in Phase 3 once the session-start/end handoff loop is fully functional.
"""

from __future__ import annotations

import json

from _ratchet import REPO_ROOT

STATE = REPO_ROOT / "governance" / "AUDIT_STATE.json"


def test_audit_state_present_and_valid() -> None:
    assert STATE.is_file(), "governance/AUDIT_STATE.json must exist"
    state = json.loads(STATE.read_text())
    assert state.get("writer") == "scripts/write_audit_state.py"
    assert "summary" in state and state["summary"].get("findings_total", 0) >= 1
    assert isinstance(state.get("findings"), list) and state["findings"]
    assert "validation_errors" in state
