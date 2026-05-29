"""Workflow registry coverage check (Phase 1 stub).

Will assert every .github/workflows/*.yml has a WORKFLOW_REGISTRY entry with
non-empty `gates:`.
"""

from _governance_stub import main_stub

if __name__ == "__main__":
    main_stub("check_workflow_registry.py", finding_id="F-008")
