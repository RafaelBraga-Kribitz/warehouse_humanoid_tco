"""F-233 — stub/real check (ratchet while open)."""

from __future__ import annotations

import sys

from _governance_check import REPO_ROOT, gate


def main() -> int:
    required = (
        REPO_ROOT / "CITATION.cff",
        REPO_ROOT / "docs" / "case_study.qmd",
        REPO_ROOT / "governance" / "RELEASE_CHECKLIST.md",
        REPO_ROOT / "governance" / "EXTERNAL_REVIEW_RESPONSE.md",
    )
    ok = all(path.exists() and path.stat().st_size > 0 for path in required)
    return gate(
        "check_publication_pack.py",
        "F-233",
        ok=ok,
        ok_msg="case study, citation metadata, and release pack are present",
        gap_msg="publication pack is incomplete",
    )


if __name__ == "__main__":
    sys.exit(main())
