"""Structural validation of governance/SSOT_REGISTRY.yaml.

Every fact must declare a `canonical` pointer and a `finding`, and that finding
file must exist. This is a structural invariant of the governance system, so it
always enforces (no linked finding gate).
"""

from __future__ import annotations

import sys

import yaml
from _governance_check import REPO_ROOT, gate

REGISTRY = REPO_ROOT / "governance" / "SSOT_REGISTRY.yaml"
FINDINGS = REPO_ROOT / "governance" / "findings"


def main() -> int:
    data = yaml.safe_load(REGISTRY.read_text()) or {}
    facts = data.get("facts", {})
    problems: list[str] = []
    for name, entry in facts.items():
        if not isinstance(entry, dict):
            problems.append(f"{name}: not a mapping")
            continue
        if not entry.get("canonical"):
            problems.append(f"{name}: missing canonical")
        fid = entry.get("finding")
        if not fid:
            problems.append(f"{name}: missing finding")
        elif not (FINDINGS / f"{fid}.yaml").exists():
            problems.append(f"{name}: finding {fid} not found")
    return gate(
        "check_ssot_registry.py",
        None,
        ok=not problems,
        ok_msg=f"{len(facts)} facts, each with canonical + existing finding",
        gap_msg="; ".join(problems),
    )


if __name__ == "__main__":
    sys.exit(main())
