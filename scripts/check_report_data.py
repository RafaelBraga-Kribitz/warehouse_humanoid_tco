"""F-005 — report QMDs must source their numbers from a declared data file.

Lightweight freshness contract: the canonical TCO results JSON must exist, and
every report QMD that presents computed figures must declare a `params:` block
(so numeric literals trace to a declared source rather than being hand-copied).
Phase 5 adds full numeric-literal cross-checking via scripts/render_reports.py.
"""

from __future__ import annotations

import re
import sys

from _governance_check import REPO_ROOT, gate

REPORTS = REPO_ROOT / "reports"
TCO_JSON = REPORTS / "module_03_tco_report.json"
_PARAMS_BLOCK = re.compile(r"^\s*params:\s*$", re.MULTILINE)


def main() -> int:
    problems: list[str] = []
    if not TCO_JSON.exists():
        problems.append("reports/module_03_tco_report.json missing")
    without_params = [
        qmd.name
        for qmd in sorted(REPORTS.glob("*.qmd"))
        if not _PARAMS_BLOCK.search(qmd.read_text())
    ]
    if without_params:
        problems.append(f"QMDs without params: block: {', '.join(without_params)}")
    return gate(
        "check_report_data.py",
        "F-005",
        ok=not problems,
        ok_msg="TCO results JSON present; every QMD declares a params: block",
        gap_msg="; ".join(problems),
    )


if __name__ == "__main__":
    sys.exit(main())
