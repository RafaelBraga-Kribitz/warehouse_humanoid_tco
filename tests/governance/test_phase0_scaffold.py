"""Smoke tests for Phase 0 governance scaffold.

Phase 0 contract:
  - governance/ scaffold is present and parseable
  - every check_*.py stub exits 0
  - write_audit_state.py emits a valid AUDIT_STATE.json
  - session_start.py renders a SESSION_HANDOUT.md without crashing
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GOV = REPO_ROOT / "governance"
FINDINGS_DIR = GOV / "findings"
SCRIPTS = REPO_ROOT / "scripts"


def test_governance_dir_present() -> None:
    assert GOV.is_dir(), "governance/ must exist after Phase 0"
    assert (GOV / "SSOT_REGISTRY.yaml").is_file()
    assert (GOV / "AUDIT_PROCEDURE.md").is_file()
    assert (GOV / "WORKFLOW_REGISTRY.yaml").is_file()
    assert (GOV / "DEPRECATIONS.yaml").is_file()
    assert (GOV / "ALLOWED_DEAD_CODE.yaml").is_file()


def test_findings_parse_and_have_required_fields() -> None:
    required = {"id", "title", "category", "kind", "status", "opened_at"}
    yaml_files = sorted(FINDINGS_DIR.glob("F-*.yaml"))
    assert yaml_files, "Phase 0 must seed at least one finding YAML"
    for path in yaml_files:
        data = yaml.safe_load(path.read_text())
        assert data, f"{path} parsed as empty"
        missing = required - data.keys()
        assert not missing, f"{path} missing fields: {missing}"
        assert data["id"] == path.stem, f"{path}: id {data['id']} does not match filename"


def test_migration_yaml_parses() -> None:
    migration_files = sorted((GOV / "migrations").glob("*.yaml"))
    assert migration_files, "Phase 0 seeds 01-sensitivity-merge migration"
    for path in migration_files:
        data = yaml.safe_load(path.read_text())
        assert data.get("name")
        assert data.get("status") in {"not_started", "in_progress", "complete", "abandoned"}
        assert "phases" in data


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        list(args),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_audit_state_writer_emits_valid_json() -> None:
    result = _run(sys.executable, str(SCRIPTS / "write_audit_state.py"))
    assert (
        result.returncode == 0
    ), f"writer failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    state_path = GOV / "AUDIT_STATE.json"
    assert state_path.is_file()
    state = json.loads(state_path.read_text())
    assert state["writer"] == "scripts/write_audit_state.py"
    assert "summary" in state
    assert state["summary"]["findings_total"] >= 1
    assert "validation_errors" in state


def test_all_audit_checks_exit_zero() -> None:
    # Phase 1 replaced the stubs with real checks built on _governance_check.
    # In the ratchet model every check exits 0 today (open findings measure;
    # structural invariants pass), so `make audit` stays green.
    checks = [p for p in sorted(SCRIPTS.glob("check_*.py")) if "_governance_check" in p.read_text()]
    assert checks, "Phase 1 must provide real check_*.py implementations"
    for check in checks:
        result = _run(sys.executable, str(check))
        assert (
            result.returncode == 0
        ), f"{check.name} returned {result.returncode}: {result.stdout}\n{result.stderr}"
        assert any(
            marker in result.stdout for marker in ("[PASS]", "[GAP]", "[INFO]")
        ), f"{check.name} should print a ratchet marker"


def test_session_start_renders_handout() -> None:
    _run(sys.executable, str(SCRIPTS / "write_audit_state.py"))
    result = _run(sys.executable, str(SCRIPTS / "session_start.py"))
    assert result.returncode == 0, f"session_start failed: {result.stderr}"
    handout = GOV / "SESSION_HANDOUT.md"
    assert handout.is_file()
    body = handout.read_text()
    assert "Session Handout" in body
    assert "Recommended next action" in body
