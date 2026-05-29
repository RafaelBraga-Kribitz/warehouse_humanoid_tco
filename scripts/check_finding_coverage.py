"""Structural invariant — every finding has a real, existing verification_script.

A finding without an executable verification contract is a narrative claim, which
is exactly the failure mode this governance system exists to prevent. Every
finding must declare a `verification_script` whose file exists on disk. The sole
exception is `closed_historical` findings (pure archival records, e.g. the
migrated CHARTER §11 changelog), which may carry a null script.
"""

from __future__ import annotations

import sys

import yaml
from _governance_check import REPO_ROOT, gate

FINDINGS = REPO_ROOT / "governance" / "findings"


def main() -> int:
    problems: list[str] = []
    count = 0
    for path in sorted(FINDINGS.glob("F-*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        count += 1
        status = data.get("status")
        script = data.get("verification_script")
        if status == "closed_historical":
            continue
        if not script:
            problems.append(f"{path.name}: null verification_script")
        elif not (REPO_ROOT / script).exists():
            problems.append(f"{path.name}: verification_script '{script}' not found")
    return gate(
        "check_finding_coverage.py",
        None,
        ok=not problems,
        ok_msg=f"{count} finding(s), each with an existing verification_script",
        gap_msg="; ".join(problems),
    )


if __name__ == "__main__":
    sys.exit(main())
