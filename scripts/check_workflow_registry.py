"""F-008 — every workflow must have a registry entry with non-empty gates.

Forward gate against orphaned workflows: each file under .github/workflows/ must
appear in governance/WORKFLOW_REGISTRY.yaml with at least one declared gate, and
the registry must not list workflows that no longer exist.
"""

from __future__ import annotations

import sys

import yaml
from _governance_check import REPO_ROOT, gate

WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
REGISTRY = REPO_ROOT / "governance" / "WORKFLOW_REGISTRY.yaml"


def main() -> int:
    on_disk = {p.name for p in WORKFLOWS_DIR.glob("*.yml")} | {
        p.name for p in WORKFLOWS_DIR.glob("*.yaml")
    }
    data = yaml.safe_load(REGISTRY.read_text()) or {}
    registered = data.get("workflows", {}) or {}
    problems: list[str] = []
    for name in sorted(on_disk):
        entry = registered.get(name)
        if entry is None:
            problems.append(f"{name}: no registry entry")
        elif not entry.get("gates"):
            problems.append(f"{name}: empty gates")
    for name in sorted(registered):
        if name not in on_disk:
            problems.append(f"{name}: registry entry has no workflow file")
    return gate(
        "check_workflow_registry.py",
        "F-008",
        ok=not problems,
        ok_msg=f"{len(on_disk)} workflow(s), each registered with gates",
        gap_msg="; ".join(problems),
    )


if __name__ == "__main__":
    sys.exit(main())
