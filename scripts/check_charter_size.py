"""F-001 / F-002 — PROJECT_CHARTER.md size budget + §11 Change Log absence.

Asserts the charter is <= 200 lines and that no §11 / "Change Log" section
remains (it duplicates CHANGELOG.md and is migrated to
governance/CHANGELOG_GENERATED.md in Phase 2).
"""

from __future__ import annotations

import re
import sys

from _governance_check import REPO_ROOT, gate

CHARTER = REPO_ROOT / "PROJECT_CHARTER.md"
LINE_BUDGET = 200

_HEADING_11 = re.compile(r"^#{1,6}\s*11[.\s]")
_CHANGELOG_HEADING = re.compile(r"^#{1,6}.*change\s*log", re.IGNORECASE)


def main() -> int:
    lines = CHARTER.read_text().splitlines()
    n = len(lines)
    has_changelog_section = any(
        _HEADING_11.search(line) or _CHANGELOG_HEADING.search(line) for line in lines
    )
    ok = n <= LINE_BUDGET and not has_changelog_section
    return gate(
        "check_charter_size.py",
        "F-001",
        ok=ok,
        ok_msg=f"{n} lines (<= {LINE_BUDGET}); no §11/Change Log section",
        gap_msg=(
            f"{n} lines (budget {LINE_BUDGET}); "
            f"changelog_section_present={has_changelog_section}"
        ),
    )


if __name__ == "__main__":
    sys.exit(main())
