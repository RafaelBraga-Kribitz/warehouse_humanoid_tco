"""F-005 — report QMDs must not use `date: today` in frontmatter.

`date: today` makes every render stamp a different date, so a committed report
PDF/HTML can never be reconciled with its source. Phase 5 replaces these with ISO
dates emitted by scripts/render_reports.py at render time.
"""

from __future__ import annotations

import re
import sys

from _governance_check import REPO_ROOT, gate

REPORTS = REPO_ROOT / "reports"
_DATE_TODAY = re.compile(r"^\s*date:\s*today\s*$")


def main() -> int:
    offenders: list[str] = []
    for qmd in sorted(REPORTS.glob("*.qmd")):
        if any(_DATE_TODAY.match(line) for line in qmd.read_text().splitlines()):
            offenders.append(qmd.name)
    return gate(
        "check_qmd_dates.py",
        "F-005",
        ok=not offenders,
        ok_msg="no QMD uses 'date: today'",
        gap_msg=f"{len(offenders)} QMD(s) use 'date: today': {', '.join(offenders)}",
    )


if __name__ == "__main__":
    sys.exit(main())
