"""F-207 — reject absolute paths in published JSON and CSV artifacts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _governance_check import REPO_ROOT, gate

ABSOLUTE_PATH = re.compile(r"(/home/|/Users/|[A-Za-z]:\\\\|[A-Za-z]:/)")


def absolute_path_matches(root: Path) -> set[Path]:
    """Return JSON/CSV artifacts containing an absolute-path marker."""
    return {
        path
        for directory, suffix in ((root / "reports", "*.json"), (root / "exports", "*.csv"))
        for path in directory.rglob(suffix)
        if ABSOLUTE_PATH.search(path.read_text(encoding="utf-8"))
    }


def main() -> int:
    matches = absolute_path_matches(REPO_ROOT)
    matched_paths = ", ".join(str(path.relative_to(REPO_ROOT)) for path in sorted(matches))
    return gate(
        "check_no_abs_paths.py",
        "F-207",
        ok=not matches,
        ok_msg="no absolute paths in published JSON or CSV artifacts",
        gap_msg=f"absolute paths found in: {matched_paths}",
    )


if __name__ == "__main__":
    sys.exit(main())
